"""Known-answer retrieval quality benchmark."""

from __future__ import annotations

import pathlib
import statistics
import time
from typing import Any, Dict, List, Mapping, Sequence

from .common import load_json, route_rows, utc_timestamp
from .context import _query_route_selection
from .search import SearchFilters, SearchIndex, search


DEFAULT_CASES = "tests/fixtures/retrieval_cases.json"


def _relative_result_path(value: Any) -> str:
    text = str(value or "")
    prefix = "~/knowledge-hub/"
    return text[len(prefix) :] if text.startswith(prefix) else text


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * fraction))
    return ordered[max(0, min(index, len(ordered) - 1))]


def run_retrieval_benchmark(
    root: pathlib.Path,
    cases_path: pathlib.Path = None,
    top_k: int = 3,
    minimum_hit_rate: float = 0.95,
    minimum_mrr: float = 0.85,
    maximum_p95_ms: float = 500.0,
) -> Dict[str, Any]:
    path = cases_path or root / DEFAULT_CASES
    payload = load_json(path, {}) or {}
    cases = list(payload.get("cases", []))
    routes = route_rows(root) if payload.get("generated_route_matrix") or payload.get("route_cases") else []
    rows: List[Dict[str, Any]] = []
    latencies: List[float] = []
    reciprocal_ranks: List[float] = []
    hit_count = 0
    started = time.monotonic()
    search_index = SearchIndex(root)
    for case in cases:
        result = search(
            root,
            str(case["query"]),
            limit=top_k,
            filters=SearchFilters(),
            search_index=search_index,
        )
        expected_ids = set(str(value) for value in case.get("expected_ids", []))
        expected_paths = set(str(value) for value in case.get("expected_paths", []))
        rank = 0
        ranked = []
        for index, item in enumerate(result.get("results", []), 1):
            item_id = str(item.get("item_id", ""))
            item_path = _relative_result_path(item.get("path", ""))
            ranked.append({"rank": index, "item_id": item_id, "path": item_path, "score": item.get("score", 0)})
            if not rank and (item_id in expected_ids or item_path in expected_paths):
                rank = index
        hit = rank > 0
        hit_count += int(hit)
        reciprocal_rank = 1.0 / rank if rank else 0.0
        reciprocal_ranks.append(reciprocal_rank)
        latency = float(result.get("latency_ms", 0))
        latencies.append(latency)
        rows.append(
            {
                "id": case.get("id", ""),
                "query": case["query"],
                "hit": hit,
                "rank": rank,
                "reciprocal_rank": round(reciprocal_rank, 4),
                "expected_ids": sorted(expected_ids),
                "expected_paths": sorted(expected_paths),
                "ranked": ranked,
                "latency_ms": latency,
            }
        )
    count = len(cases)
    hit_rate = hit_count / count if count else 0.0
    mrr = statistics.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    p95_ms = _percentile(latencies, 0.95)
    latency_target_met = bool(latencies) and p95_ms <= maximum_p95_ms
    route_case_rows: List[Dict[str, Any]] = []
    matrix = payload.get("generated_route_matrix", {})
    if isinstance(matrix, Mapping) and matrix.get("enabled"):
        task_types = [str(value) for value in matrix.get("task_types", [])]
        for route in routes:
            project_id = str(route.get("project_id", ""))
            for task_type in task_types:
                route_case_rows.append(
                    {
                        "id": "matrix:{}:{}".format(project_id, task_type),
                        "query": "{} {}".format(project_id, task_type),
                        "expected_status": "selected",
                        "expected_project_id": project_id,
                    }
                )
    route_case_rows.extend(
        dict(row) for row in payload.get("route_cases", []) if isinstance(row, Mapping)
    )
    route_results: List[Dict[str, Any]] = []
    route_hit_count = 0
    for case in route_case_rows:
        selection = _query_route_selection(str(case.get("query", "")), routes)
        selected_project_id = (
            str(selection["route"].get("project_id", ""))
            if selection.get("route")
            else ""
        )
        expected_status = str(case.get("expected_status", "selected"))
        expected_project_id = str(case.get("expected_project_id", ""))
        hit = selection["status"] == expected_status and (
            not expected_project_id or selected_project_id == expected_project_id
        )
        route_hit_count += int(hit)
        route_results.append(
            {
                "id": case.get("id", ""),
                "query": case.get("query", ""),
                "hit": hit,
                "expected_status": expected_status,
                "actual_status": selection["status"],
                "expected_project_id": expected_project_id,
                "selected_project_id": selected_project_id,
                "candidates": selection.get("candidates", []),
            }
        )
    route_case_count = len(route_case_rows)
    route_accuracy = route_hit_count / route_case_count if route_case_count else 1.0
    status = (
        "pass"
        if count
        and hit_rate >= minimum_hit_rate
        and mrr >= minimum_mrr
        and latency_target_met
        and route_accuracy == 1.0
        else "fail"
    )
    try:
        case_file = str(path.relative_to(root))
    except ValueError:
        case_file = str(path)
    return {
        "schema_version": 1,
        "read_only": True,
        "generated_at": utc_timestamp(),
        "status": status,
        "case_file": case_file,
        "case_count": count + route_case_count,
        "search_case_count": count,
        "route_case_count": route_case_count,
        "top_k": top_k,
        "hit_count": hit_count,
        "hit_rate": round(hit_rate, 4),
        "mrr": round(mrr, 4),
        "route_hit_count": route_hit_count,
        "route_accuracy": round(route_accuracy, 4),
        "thresholds": {
            "minimum_hit_rate": minimum_hit_rate,
            "minimum_mrr": minimum_mrr,
            "maximum_p95_ms": maximum_p95_ms,
        },
        "latency_target_met": latency_target_met,
        "latency_ms": {
            "p50": round(_percentile(latencies, 0.50), 2),
            "p95": round(p95_ms, 2),
            "max": round(max(latencies) if latencies else 0.0, 2),
            "total": round((time.monotonic() - started) * 1000, 2),
        },
        "failures": [row for row in rows if not row["hit"]],
        "route_failures": [row for row in route_results if not row["hit"]],
        "cases": rows,
        "route_cases": route_results,
    }
