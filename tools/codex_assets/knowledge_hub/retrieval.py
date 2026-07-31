"""Known-answer retrieval quality benchmark."""

from __future__ import annotations

import concurrent.futures
import contextlib
import fcntl
import json
import math
import os
import pathlib
import statistics
import tempfile
import time
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence

from .common import (
    ensure_private_directory,
    load_json,
    parse_json_output,
    registry_items,
    route_rows,
    run_rtk,
    utc_timestamp,
)
from .context import _query_route_selection
from .search import (
    DEFAULT_SEARCH_EXCLUDED_PATHS,
    DEFAULT_SEARCH_EXCLUDED_ROOTS,
    SearchFilters,
    SearchIndex,
    search,
)
from .search_ranking import PRIVATE_IPV4_PATTERN


DEFAULT_CASES = "tests/fixtures/retrieval_cases.json"
DEFAULT_COMPATIBILITY_PATTERNS = (
    "EMBEDDED_KNOWLEDGE_HOME",
    "~/embedded/knowledge",
)


@contextlib.contextmanager
def _retrieval_benchmark_lock() -> Iterator[None]:
    """Serialize timing probes across independent gate processes.

    Regression workers may launch several product gates concurrently. Their
    quality assertions are independent, but overlapping latency probes measure
    scheduler contention instead of retrieval performance and become flaky.
    """

    lock_root = (
        pathlib.Path(tempfile.gettempdir())
        / "knowledge-hub-runtime-{}".format(os.getuid())
        / "locks"
    )
    ensure_private_directory(lock_root)
    lock_path = lock_root / "retrieval-benchmark.lock"
    if lock_path.is_symlink():
        raise RuntimeError("retrieval benchmark lock must not be a symlink")
    with lock_path.open("a+") as handle:
        os.chmod(lock_path, 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _dcg(relevances: Sequence[int]) -> float:
    return sum(
        (2 ** int(relevance) - 1) / math.log2(index + 2)
        for index, relevance in enumerate(relevances)
    )


def _ndcg_at_10(
    ranked: Sequence[Mapping[str, Any]],
    relevance_by_id: Mapping[str, int],
    relevance_by_path: Mapping[str, int],
) -> float:
    actual = [
        max(
            int(relevance_by_id.get(str(row.get("item_id", "")), 0)),
            int(relevance_by_path.get(str(row.get("path", "")), 0)),
        )
        for row in ranked[:10]
    ]
    ideal = sorted(
        list(relevance_by_id.values()) + list(relevance_by_path.values()),
        reverse=True,
    )[:10]
    ideal_dcg = _dcg(ideal)
    return _dcg(actual) / ideal_dcg if ideal_dcg else 1.0


def _control_path(path: str) -> bool:
    normalized = path.lstrip("./")
    root_name = normalized.split("/", 1)[0]
    return normalized in DEFAULT_SEARCH_EXCLUDED_PATHS or root_name in DEFAULT_SEARCH_EXCLUDED_ROOTS


def _result_exposes_internal_endpoint(row: Mapping[str, Any]) -> bool:
    exposed_fields = {
        key: value
        for key, value in row.items()
        if key not in {"score", "line"}
    }
    return PRIVATE_IPV4_PATTERN.search(
        json.dumps(exposed_fields, ensure_ascii=False)
    ) is not None


def retrieval_benchmark_summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": "knowledge-retrieval-benchmark-summary-v1",
        "status": payload.get("status", ""),
        "case_file": payload.get("case_file", ""),
        "case_count": payload.get("case_count", 0),
        "search_case_count": payload.get("search_case_count", 0),
        "route_case_count": payload.get("route_case_count", 0),
        "hit_rate": payload.get("hit_rate", 0),
        "mrr": payload.get("mrr", 0),
        "ndcg_at_10": payload.get("ndcg_at_10", 0),
        "authority_recall_at_3": payload.get("authority_recall_at_3", 0),
        "route_accuracy": payload.get("route_accuracy", 0),
        "performance_thresholds_enforced": payload.get(
            "performance_thresholds_enforced", True
        ),
        "integrity": payload.get("integrity", {}),
        "latency_ms": payload.get("latency_ms", {}),
        "concurrency_probe": payload.get("concurrency_probe", {}),
        "scale_probe": payload.get("scale_probe", {}),
        "thresholds": payload.get("thresholds", {}),
        "failure_count": len(payload.get("failures", [])),
        "route_failure_count": len(payload.get("route_failures", [])),
        "failures": list(payload.get("failures", []))[:10],
        "route_failures": list(payload.get("route_failures", []))[:10],
    }


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


def _run_concurrency_probe(
    root: pathlib.Path,
    cases: Sequence[Mapping[str, Any]],
    workers: int = 4,
    query_count: int = 8,
    maximum_p95_ms: float = 1000.0,
) -> Dict[str, Any]:
    selected = [
        row
        for row in cases
        if row.get("expected_ids") or row.get("expected_paths")
    ][:query_count]
    if not selected:
        return {
            "status": "skipped",
            "worker_count": workers,
            "query_count": 0,
            "p95_ms": 0.0,
            "maximum_p95_ms": maximum_p95_ms,
            "failures": [],
        }

    def run_case(case: Mapping[str, Any]) -> Dict[str, Any]:
        started = time.monotonic()
        try:
            result = run_rtk(
                root,
                (
                    "bash",
                    "tools/knowledge-search.sh",
                    str(case.get("query", "")),
                    "--json",
                    "--limit",
                    "3",
                    "--no-telemetry",
                ),
                timeout=30,
                accepted_exit_codes=(0, 1),
            )
            payload = parse_json_output(result)
            returned_ids = {
                str(row.get("id", "")) for row in payload.get("results", [])
            }
            returned_paths = {
                _relative_result_path(row.get("path", ""))
                for row in payload.get("results", [])
            }
            expected_ids = {str(value) for value in case.get("expected_ids", [])}
            expected_paths = {
                str(value) for value in case.get("expected_paths", [])
            }
            hit = bool(
                returned_ids.intersection(expected_ids)
                or returned_paths.intersection(expected_paths)
            )
            return {
                "id": str(case.get("id", "")),
                "hit": hit,
                "latency_ms": round((time.monotonic() - started) * 1000, 2),
                "error": "",
            }
        except Exception as exc:  # pragma: no cover - defensive probe boundary
            return {
                "id": str(case.get("id", "")),
                "hit": False,
                "latency_ms": round((time.monotonic() - started) * 1000, 2),
                "error": str(exc),
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        rows = list(executor.map(run_case, selected))
    latencies = [float(row["latency_ms"]) for row in rows]
    p95_ms = _percentile(latencies, 0.95)
    failures = [row for row in rows if not row["hit"]]
    return {
        "status": "pass" if not failures and p95_ms <= maximum_p95_ms else "fail",
        "worker_count": workers,
        "query_count": len(rows),
        "p95_ms": round(p95_ms, 2),
        "max_ms": round(max(latencies) if latencies else 0.0, 2),
        "maximum_p95_ms": maximum_p95_ms,
        "failures": failures,
    }


def _run_scale_probe(
    document_files: int,
    factor: int = 10,
    maximum_total_ms: float = 15000.0,
) -> Dict[str, Any]:
    target_count = max(1000, document_files * factor)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="knowledge-retrieval-scale-") as directory:
        root = pathlib.Path(directory)
        (root / "registry").mkdir()
        (root / "projects/noise/archive").mkdir(parents=True)
        (root / "README.md").write_text(
            "# Knowledge Hub authority scale root\n",
            encoding="utf-8",
        )
        items: List[Dict[str, Any]] = [
            {
                "id": "scale-authority-root",
                "title": "Knowledge Hub authority scale root",
                "kind": "architecture",
                "domain": "root",
                "path": "README.md",
                "status": "active",
                "owner": "scale-probe",
                "summary_zh": "10 倍语料权威候选保留探针。",
                "tags": ["knowledge", "hub", "authority", "scale"],
            }
        ]
        for index in range(target_count - 1):
            relative = "projects/noise/archive/noise-{:05d}.md".format(index)
            (root / relative).write_text(
                "# Historical projection {}\n\nKnowledge Hub authority scale boilerplate.\n".format(
                    index
                ),
                encoding="utf-8",
            )
            items.append(
                {
                    "id": "scale-noise-{:05d}".format(index),
                    "title": "Historical projection {:05d}".format(index),
                    "kind": "project-archive",
                    "domain": "projects/noise",
                    "path": relative,
                    "status": "archived",
                    "owner": "scale-probe",
                    "summary_zh": "模板化历史投影。",
                    "tags": ["knowledge", "hub", "projection"],
                }
            )
        (root / "registry/items.jsonl").write_text(
            "".join(
                json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                for row in items
            ),
            encoding="utf-8",
        )
        (root / "registry/sources.json").write_text(
            '{"sources":[]}\n', encoding="utf-8"
        )
        (root / "registry/retired-sources.jsonl").write_text("", encoding="utf-8")
        search_index = SearchIndex(root)
        preparation_started = time.monotonic()
        preparation = search_index.ensure()
        preparation_ms = round((time.monotonic() - preparation_started) * 1000, 2)
        result = search(
            root,
            "Knowledge Hub authority scale",
            limit=3,
            filters=SearchFilters(),
            search_index=search_index,
        )
        total_ms = round((time.monotonic() - started) * 1000, 2)
        rank = next(
            (
                index
                for index, row in enumerate(result.get("results", []), 1)
                if row.get("id") == "scale-authority-root"
            ),
            0,
        )
    return {
        "status": "pass"
        if rank == 1
        and int(preparation.get("document_files", 0)) == target_count
        and total_ms <= maximum_total_ms
        else "fail",
        "factor": factor,
        "document_count": target_count,
        "authority_rank": rank,
        "candidate_limit": SearchIndex.CANDIDATE_LIMIT,
        "authority_lane_required_at_scale": target_count > SearchIndex.CANDIDATE_LIMIT,
        "preparation_ms": preparation_ms,
        "query_ms": result.get("latency_ms", 0),
        "total_ms": total_ms,
        "maximum_total_ms": maximum_total_ms,
    }


def run_retrieval_benchmark(
    root: pathlib.Path,
    cases_path: Optional[pathlib.Path] = None,
    top_k: int = 3,
    minimum_hit_rate: float = 0.95,
    minimum_mrr: float = 0.85,
    minimum_ndcg_at_10: float = 0.90,
    minimum_authority_recall_at_3: float = 1.0,
    maximum_p95_ms: float = 500.0,
    maximum_index_preparation_ms: float = 5000.0,
    maximum_concurrent_p95_ms: float = 1000.0,
    enable_extended_probes: Optional[bool] = None,
    enforce_performance_thresholds: bool = True,
) -> Dict[str, Any]:
    path = cases_path or root / DEFAULT_CASES
    payload = load_json(path, {}) or {}
    cases = list(payload.get("cases", []))
    routes = route_rows(root) if payload.get("generated_route_matrix") or payload.get("route_cases") else []
    rows: List[Dict[str, Any]] = []
    latencies: List[float] = []
    reciprocal_ranks: List[float] = []
    ndcg_values: List[float] = []
    authority_case_count = 0
    authority_hit_count = 0
    result_count = 0
    unregistered_result_count = 0
    control_result_count = 0
    duplicate_result_count = 0
    compatibility_hit_count = 0
    internal_endpoint_exposure_count = 0
    governed_items = registry_items(root)
    registry_ids = {str(row.get("id", "")) for row in governed_items}
    registry_paths = {str(row.get("path", "")) for row in governed_items}
    compatibility_patterns = tuple(
        str(value)
        for value in payload.get(
            "forbidden_default_patterns",
            DEFAULT_COMPATIBILITY_PATTERNS,
        )
    )
    hit_count = 0
    overall_started = time.monotonic()
    search_index = SearchIndex(root)
    preparation_started = time.monotonic()
    preparation = search_index.ensure()
    preparation_duration_ms = round(
        (time.monotonic() - preparation_started) * 1000,
        2,
    )
    index_preparation_target_met = (
        preparation_duration_ms <= maximum_index_preparation_ms
    )
    measurement_started = time.monotonic()
    for case in cases:
        result = search(
            root,
            str(case["query"]),
            limit=max(top_k, 10),
            filters=SearchFilters(),
            search_index=search_index,
        )
        expected_ids = set(str(value) for value in case.get("expected_ids", []))
        expected_paths = set(str(value) for value in case.get("expected_paths", []))
        forbidden_ids = set(str(value) for value in case.get("forbidden_ids", []))
        forbidden_paths = set(str(value) for value in case.get("forbidden_paths", []))
        rank = 0
        ranked = []
        forbidden_hits = []
        seen_case_paths = set()
        for index, item in enumerate(result.get("results", []), 1):
            item_id = str(item.get("item_id", ""))
            item_path = _relative_result_path(item.get("path", ""))
            ranked.append({"rank": index, "item_id": item_id, "path": item_path, "score": item.get("score", 0)})
            result_count += 1
            if registry_ids or registry_paths:
                if item_id not in registry_ids or item_path not in registry_paths:
                    unregistered_result_count += 1
            if _control_path(item_path):
                control_result_count += 1
            if item_path in seen_case_paths:
                duplicate_result_count += 1
            seen_case_paths.add(item_path)
            serialized_result = json.dumps(item, ensure_ascii=False)
            if any(pattern and pattern in serialized_result for pattern in compatibility_patterns):
                compatibility_hit_count += 1
            if _result_exposes_internal_endpoint(item):
                internal_endpoint_exposure_count += 1
            if not rank and (item_id in expected_ids or item_path in expected_paths):
                rank = index
            if item_id in forbidden_ids or item_path in forbidden_paths:
                forbidden_hits.append(
                    {"rank": index, "item_id": item_id, "path": item_path}
                )
        expected_zero_hit = bool(case.get("expected_zero_hit", False))
        hit = (
            not result.get("results", [])
            if expected_zero_hit
            else 0 < rank <= top_k
        ) and not forbidden_hits
        hit_count += int(hit)
        reciprocal_rank = 1.0 / rank if rank and not expected_zero_hit else 0.0
        if expected_ids or expected_paths:
            reciprocal_ranks.append(reciprocal_rank)
            relevance_ids = {
                str(key): int(value)
                for key, value in (case.get("relevance_ids", {}) or {}).items()
            }
            relevance_paths = {
                str(key): int(value)
                for key, value in (case.get("relevance_paths", {}) or {}).items()
            }
            for value in expected_ids:
                relevance_ids.setdefault(value, 3)
            for value in expected_paths:
                relevance_paths.setdefault(value, 3)
            ndcg_values.append(
                _ndcg_at_10(ranked, relevance_ids, relevance_paths)
            )
            if case.get("authority_case", True):
                authority_case_count += 1
                authority_hit_count += int(0 < rank <= 3)
        latency = float(result.get("latency_ms", 0))
        latencies.append(latency)
        rows.append(
            {
                "id": case.get("id", ""),
                "query": case["query"],
                "hit": hit,
                "rank": rank,
                "expected_zero_hit": expected_zero_hit,
                "reciprocal_rank": round(reciprocal_rank, 4),
                "ndcg_at_10": round(ndcg_values[-1], 4)
                if expected_ids or expected_paths
                else 1.0,
                "expected_ids": sorted(expected_ids),
                "expected_paths": sorted(expected_paths),
                "forbidden_ids": sorted(forbidden_ids),
                "forbidden_paths": sorted(forbidden_paths),
                "forbidden_hits": forbidden_hits,
                "ranked": ranked,
                "latency_ms": latency,
            }
        )
    measured_queries_duration_ms = round(
        (time.monotonic() - measurement_started) * 1000,
        2,
    )
    count = len(cases)
    hit_rate = hit_count / count if count else 0.0
    mrr = statistics.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    ndcg_at_10 = statistics.mean(ndcg_values) if ndcg_values else 0.0
    authority_recall_at_3 = (
        authority_hit_count / authority_case_count
        if authority_case_count
        else 0.0
    )
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
    extended_probes = (
        cases_path is None
        if enable_extended_probes is None
        else enable_extended_probes
    )
    concurrency_probe = (
        _run_concurrency_probe(
            root,
            cases,
            maximum_p95_ms=maximum_concurrent_p95_ms,
        )
        if extended_probes
        else {"status": "skipped", "reason": "custom-case-or-explicitly-disabled"}
    )
    scale_probe = (
        _run_scale_probe(int(preparation.get("document_files", 0)))
        if extended_probes
        else {"status": "skipped", "reason": "custom-case-or-explicitly-disabled"}
    )
    integrity: Dict[str, Any] = {
        "result_count": result_count,
        "unregistered_result_count": unregistered_result_count,
        "unregistered_result_rate": round(
            unregistered_result_count / result_count if result_count else 0.0,
            4,
        ),
        "control_result_count": control_result_count,
        "control_result_rate": round(
            control_result_count / result_count if result_count else 0.0,
            4,
        ),
        "duplicate_result_count": duplicate_result_count,
        "duplicate_result_rate": round(
            duplicate_result_count / result_count if result_count else 0.0,
            4,
        ),
        "compatibility_hit_count": compatibility_hit_count,
        "internal_endpoint_exposure_count": internal_endpoint_exposure_count,
    }
    integrity["status"] = (
        "pass"
        if all(
            integrity[key] == 0
            for key in (
                "unregistered_result_count",
                "control_result_count",
                "duplicate_result_count",
                "compatibility_hit_count",
                "internal_endpoint_exposure_count",
            )
        )
        else "fail"
    )
    performance_target_met = bool(
        not enforce_performance_thresholds
        or (latency_target_met and index_preparation_target_met)
    )
    status = (
        "pass"
        if count
        and hit_rate >= minimum_hit_rate
        and mrr >= minimum_mrr
        and ndcg_at_10 >= minimum_ndcg_at_10
        and authority_recall_at_3 >= minimum_authority_recall_at_3
        and performance_target_met
        and route_accuracy == 1.0
        and integrity["status"] == "pass"
        and concurrency_probe.get("status") in {"pass", "skipped"}
        and scale_probe.get("status") in {"pass", "skipped"}
        else "fail"
    )
    try:
        case_file = str(path.relative_to(root))
    except ValueError:
        case_file = str(path)
    return {
        "schema_version": 3,
        "read_only": True,
        "generated_at": utc_timestamp(),
        "status": status,
        "measurement_profile": "warm-interactive",
        "performance_thresholds_enforced": enforce_performance_thresholds,
        "case_file": case_file,
        "case_count": count + route_case_count,
        "search_case_count": count,
        "route_case_count": route_case_count,
        "top_k": top_k,
        "hit_count": hit_count,
        "hit_rate": round(hit_rate, 4),
        "mrr": round(mrr, 4),
        "ndcg_at_10": round(ndcg_at_10, 4),
        "authority_case_count": authority_case_count,
        "authority_hit_count": authority_hit_count,
        "authority_recall_at_3": round(authority_recall_at_3, 4),
        "route_hit_count": route_hit_count,
        "route_accuracy": round(route_accuracy, 4),
        "integrity": integrity,
        "concurrency_probe": concurrency_probe,
        "scale_probe": scale_probe,
        "thresholds": {
            "minimum_hit_rate": minimum_hit_rate,
            "minimum_mrr": minimum_mrr,
            "minimum_ndcg_at_10": minimum_ndcg_at_10,
            "minimum_authority_recall_at_3": minimum_authority_recall_at_3,
            "maximum_p95_ms": maximum_p95_ms,
            "maximum_index_preparation_ms": maximum_index_preparation_ms,
            "maximum_concurrent_p95_ms": maximum_concurrent_p95_ms,
        },
        "latency_target_met": latency_target_met,
        "index_preparation_target_met": index_preparation_target_met,
        "performance_target_met": performance_target_met,
        "index_preparation": {
            "state": preparation.get("state", ""),
            "rebuilt": bool(preparation.get("rebuilt", False)),
            "updated": bool(preparation.get("updated", False)),
            "duration_ms": preparation_duration_ms,
            "document_files": int(preparation.get("document_files", 0)),
            "document_rows": int(preparation.get("document_rows", 0)),
            "hashed_files": int(preparation.get("hashed_files", 0)),
            "reused_content_hashes": int(
                preparation.get("reused_content_hashes", 0)
            ),
        },
        "latency_ms": {
            "p50": round(_percentile(latencies, 0.50), 2),
            "p95": round(p95_ms, 2),
            "max": round(max(latencies) if latencies else 0.0, 2),
            "index_preparation": preparation_duration_ms,
            "measured_queries": measured_queries_duration_ms,
            "total": round((time.monotonic() - overall_started) * 1000, 2),
        },
        "failures": [row for row in rows if not row["hit"]],
        "route_failures": [row for row in route_results if not row["hit"]],
        "cases": rows,
        "route_cases": route_results,
    }


def run_retrieval_benchmark_serialized(
    root: pathlib.Path,
    cases_path: Optional[pathlib.Path] = None,
    top_k: int = 3,
    minimum_hit_rate: float = 0.95,
    minimum_mrr: float = 0.85,
    minimum_ndcg_at_10: float = 0.90,
    minimum_authority_recall_at_3: float = 1.0,
    maximum_p95_ms: float = 500.0,
    maximum_index_preparation_ms: float = 5000.0,
    maximum_concurrent_p95_ms: float = 1000.0,
    enable_extended_probes: Optional[bool] = None,
    enforce_performance_thresholds: bool = True,
) -> Dict[str, Any]:
    with _retrieval_benchmark_lock():
        return run_retrieval_benchmark(
            root,
            cases_path=cases_path,
            top_k=top_k,
            minimum_hit_rate=minimum_hit_rate,
            minimum_mrr=minimum_mrr,
            minimum_ndcg_at_10=minimum_ndcg_at_10,
            minimum_authority_recall_at_3=minimum_authority_recall_at_3,
            maximum_p95_ms=maximum_p95_ms,
            maximum_index_preparation_ms=maximum_index_preparation_ms,
            maximum_concurrent_p95_ms=maximum_concurrent_p95_ms,
            enable_extended_probes=enable_extended_probes,
            enforce_performance_thresholds=enforce_performance_thresholds,
        )
