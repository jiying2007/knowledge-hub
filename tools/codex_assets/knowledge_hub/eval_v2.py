"""P6 versioned evaluation datasets and baseline comparison."""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any, Dict, List, Mapping, Sequence

from .common import KnowledgeHubError

REQUIRED_CASE_FIELDS = {
    "id",
    "query",
    "query_class",
    "language",
    "criticality",
    "expected_ids",
    "forbidden_ids",
    "principal",
    "scope",
}


def _case_digest(case: Mapping[str, Any]) -> str:
    payload = json.dumps(
        dict(case),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_case(case: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    missing = sorted(field for field in REQUIRED_CASE_FIELDS if field not in case)
    errors.extend("missing {}".format(field) for field in missing)
    for field in ("id", "query", "query_class", "language", "criticality"):
        if field in case and not str(case.get(field, "")).strip():
            errors.append("{} must be non-empty".format(field))
    if str(case.get("criticality", "")) not in {"critical", "high", "normal", "low"}:
        errors.append("invalid criticality")
    for field in ("expected_ids", "forbidden_ids"):
        value = case.get(field, [])
        if not isinstance(value, list) or any(not str(row).strip() for row in value):
            errors.append("{} must be a list of non-empty strings".format(field))
    if not isinstance(case.get("principal", {}), Mapping):
        errors.append("principal must be an object")
    if len(str(case.get("query", ""))) > 4096:
        errors.append("query exceeds budget")
    return errors


def load_dataset(path: pathlib.Path, maximum_cases: int = 5000) -> Dict[str, Any]:
    if not path.exists() or path.is_symlink() or not path.is_file():
        raise KnowledgeHubError("evaluation dataset is unavailable")
    rows: List[Dict[str, Any]] = []
    total_bytes = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            total_bytes += len(raw.encode("utf-8"))
            if total_bytes > 32 * 1024 * 1024:
                raise KnowledgeHubError("evaluation dataset exceeds byte budget")
            if not raw.strip():
                continue
            if len(rows) >= maximum_cases:
                raise KnowledgeHubError("evaluation dataset exceeds case budget")
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise KnowledgeHubError(
                    "invalid eval JSONL line {}".format(line_number)
                ) from exc
            if not isinstance(row, Mapping):
                raise KnowledgeHubError("evaluation case must be an object")
            errors = validate_case(row)
            if errors:
                raise KnowledgeHubError(
                    "invalid eval case {}: {}".format(
                        row.get("id", line_number), "; ".join(errors)
                    )
                )
            rows.append(dict(row))
    digest = hashlib.sha256(
        "\n".join(_case_digest(row) for row in rows).encode("ascii")
    ).hexdigest()
    return {
        "schema_version": "knowledge-hub.eval-dataset.v2",
        "case_count": len(rows),
        "dataset_sha256": digest,
        "cases": rows,
    }


def migrate_v1_cases(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    migrated: List[Dict[str, Any]] = []
    for row in payload.get("cases", []):
        if not isinstance(row, Mapping):
            continue
        query = str(row.get("query", ""))
        language = "mixed" if any("\u4e00" <= char <= "\u9fff" for char in query) else "en"
        migrated.append(
            {
                "id": str(row.get("id", "")),
                "query": query,
                "query_class": "known-answer",
                "language": language,
                "criticality": "high" if row.get("forbidden_ids") else "normal",
                "expected_ids": list(row.get("expected_ids", [])),
                "forbidden_ids": list(row.get("forbidden_ids", [])),
                "expected_paths": list(row.get("expected_paths", [])),
                "forbidden_paths": list(row.get("forbidden_paths", [])),
                "principal": {
                    "principal_id": "eval-user",
                    "organization_id": "engineering",
                    "groups": ["team:engineering"],
                },
                "scope": "team-general",
                "expected_zero_hit": bool(row.get("expected_zero_hit", False)),
                "source_trace": "tests/fixtures/retrieval_cases.json",
            }
        )
    return migrated


def metric_summary(
    case_results: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    total = len(case_results)
    passed = sum(bool(row.get("passed", False)) for row in case_results)
    critical = [
        row
        for row in case_results
        if str(row.get("criticality", "")) == "critical"
    ]
    critical_failures = [
        str(row.get("id", ""))
        for row in critical
        if not bool(row.get("passed", False))
    ]
    latencies = sorted(float(row.get("latency_ms", 0.0)) for row in case_results)
    p95 = latencies[int(round((len(latencies) - 1) * 0.95))] if latencies else 0.0
    return {
        "case_count": total,
        "pass_rate": passed / total if total else 1.0,
        "critical_failure_ids": critical_failures,
        "p95_ms": round(p95, 2),
    }


def compare_baseline(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    maximum_pass_rate_drop: float = 0.0,
    maximum_p95_regression_ratio: float = 1.20,
) -> Dict[str, Any]:
    base_rate = float(baseline.get("pass_rate", 0.0))
    candidate_rate = float(candidate.get("pass_rate", 0.0))
    base_p95 = float(baseline.get("p95_ms", 0.0))
    candidate_p95 = float(candidate.get("p95_ms", 0.0))
    failures: List[str] = []
    if candidate_rate + maximum_pass_rate_drop < base_rate:
        failures.append("pass-rate-regression")
    if base_p95 > 0 and candidate_p95 > base_p95 * maximum_p95_regression_ratio:
        failures.append("p95-regression")
    if candidate.get("critical_failure_ids"):
        failures.append("critical-case-failure")
    return {
        "schema_version": "knowledge-hub.eval-comparison.v2",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "baseline": dict(baseline),
        "candidate": dict(candidate),
        "newly_failing_critical_ids": list(candidate.get("critical_failure_ids", [])),
    }
