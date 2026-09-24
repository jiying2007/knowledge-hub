"""P6 versioned evaluation datasets and fail-closed baseline comparison."""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
from typing import Any, Dict, List, Mapping, Sequence

from .common import KnowledgeHubError

REQUIRED_CASE_FIELDS = {
    "id", "query", "query_class", "language", "criticality",
    "expected_ids", "forbidden_ids", "principal", "scope",
}
MAX_CASES = 5000
MAX_DATASET_BYTES = 32 * 1024 * 1024
MAX_LINE_BYTES = 1024 * 1024
CRITICALITIES = {"critical", "high", "normal", "low"}


def _case_digest(case: Mapping[str, Any]) -> str:
    payload = json.dumps(
        dict(case), ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _string_list(value: Any, label: str, *, nonempty: bool = False) -> List[str]:
    if not isinstance(value, list) or len(value) > MAX_CASES:
        raise KnowledgeHubError("{} must be a bounded list".format(label))
    if nonempty and not value:
        raise KnowledgeHubError("{} must be non-empty".format(label))
    if any(not isinstance(row, str) or not row.strip() or len(row) > 4096 for row in value):
        raise KnowledgeHubError("{} must contain non-empty bounded strings".format(label))
    if len(set(value)) != len(value):
        raise KnowledgeHubError("{} contains duplicate IDs".format(label))
    return list(value)


def validate_case(case: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    missing = sorted(field for field in REQUIRED_CASE_FIELDS if field not in case)
    errors.extend("missing {}".format(field) for field in missing)
    for field in ("id", "query", "query_class", "language", "criticality", "scope"):
        value = case.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 4096:
            errors.append("{} must be a non-empty bounded string".format(field))
    if not isinstance(case.get("criticality"), str) or case["criticality"] not in CRITICALITIES:
        errors.append("invalid criticality")
    for field in ("expected_ids", "forbidden_ids"):
        try:
            _string_list(case.get(field), field)
        except KnowledgeHubError as exc:
            errors.append(str(exc))
    if not isinstance(case.get("principal"), Mapping):
        errors.append("principal must be an object")
    if "expected_zero_hit" in case and type(case["expected_zero_hit"]) is not bool:
        errors.append("expected_zero_hit must be a boolean")
    return errors


def load_dataset(path: pathlib.Path, maximum_cases: int = MAX_CASES) -> Dict[str, Any]:
    if type(maximum_cases) is not int or not 1 <= maximum_cases <= MAX_CASES:
        raise KnowledgeHubError("invalid evaluation case budget")
    if not path.exists() or path.is_symlink() or not path.is_file():
        raise KnowledgeHubError("evaluation dataset is unavailable")
    rows: List[Dict[str, Any]] = []
    seen = set()
    total_bytes = 0
    with path.open("rb") as handle:
        while True:
            raw = handle.readline(MAX_LINE_BYTES + 1)
            if not raw:
                break
            total_bytes += len(raw)
            if len(raw) > MAX_LINE_BYTES or total_bytes > MAX_DATASET_BYTES:
                raise KnowledgeHubError("evaluation dataset exceeds byte budget")
            if not raw.strip():
                continue
            if len(rows) >= maximum_cases:
                raise KnowledgeHubError("evaluation dataset exceeds case budget")
            try:
                row = json.loads(raw.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise KnowledgeHubError("invalid eval JSONL") from exc
            if not isinstance(row, Mapping):
                raise KnowledgeHubError("evaluation case must be an object")
            errors = validate_case(row)
            if errors:
                raise KnowledgeHubError("invalid eval case: {}".format("; ".join(errors)))
            if row["id"] in seen:
                raise KnowledgeHubError("evaluation dataset contains duplicate case IDs")
            seen.add(row["id"])
            rows.append(dict(row))
    if not rows:
        raise KnowledgeHubError("evaluation dataset must be non-empty")
    try:
        digest = hashlib.sha256(
            "\n".join(_case_digest(row) for row in rows).encode("ascii")
        ).hexdigest()
    except (TypeError, ValueError) as exc:
        raise KnowledgeHubError("evaluation dataset contains non-JSON values") from exc
    return {
        "schema_version": "knowledge-hub.eval-dataset.v2",
        "case_count": len(rows), "dataset_sha256": digest, "cases": rows,
    }


def migrate_v1_cases(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    migrated: List[Dict[str, Any]] = []
    for row in payload.get("cases", []):
        if not isinstance(row, Mapping):
            raise KnowledgeHubError("evaluation case must be an object")
        zero_hit = row.get("expected_zero_hit", False)
        if type(zero_hit) is not bool:
            raise KnowledgeHubError("expected_zero_hit must be a boolean")
        query = str(row.get("query", ""))
        language = "mixed" if any("\u4e00" <= char <= "\u9fff" for char in query) else "en"
        migrated.append({
            "id": str(row.get("id", "")), "query": query,
            "query_class": "known-answer", "language": language,
            "criticality": "high" if row.get("forbidden_ids") else "normal",
            "expected_ids": list(row.get("expected_ids", [])),
            "forbidden_ids": list(row.get("forbidden_ids", [])),
            "expected_paths": list(row.get("expected_paths", [])),
            "forbidden_paths": list(row.get("forbidden_paths", [])),
            "principal": {
                "principal_id": "eval-user", "organization_id": "engineering",
                "groups": ["team:engineering"],
            },
            "scope": "team-general", "expected_zero_hit": zero_hit,
            "source_trace": "tests/fixtures/retrieval_cases.json",
        })
    return migrated


def _number(value: Any, label: str, maximum: float = math.inf) -> float:
    if type(value) not in (int, float):
        raise KnowledgeHubError("{} must be a finite non-negative number".format(label))
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise KnowledgeHubError("{} is out of range".format(label)) from exc
    if not math.isfinite(result) or result < 0 or result > maximum:
        raise KnowledgeHubError("{} is out of range".format(label))
    return result


def _coverage_digest(ids: Sequence[str]) -> str:
    return _case_digest({"case_ids": sorted(ids)})


def metric_summary(
    case_results: Sequence[Mapping[str, Any]],
    *,
    expected_case_ids: Sequence[str] = (),
) -> Dict[str, Any]:
    if not case_results or len(case_results) > MAX_CASES:
        raise KnowledgeHubError("evaluation results must be non-empty and bounded")
    ids: List[str] = []
    latencies: List[float] = []
    critical_failures: List[str] = []
    passed = 0
    for row in case_results:
        if not isinstance(row, Mapping):
            raise KnowledgeHubError("evaluation result must be an object")
        row_id = _string_list([row.get("id")], "case_ids", nonempty=True)[0]
        ids.append(row_id)
        if type(row.get("passed")) is not bool:
            raise KnowledgeHubError("evaluation passed must be a boolean")
        if row.get("execution_status", "completed") != "completed":
            raise KnowledgeHubError("evaluation result was not completed")
        criticality = row.get("criticality", "normal")
        if not isinstance(criticality, str) or criticality not in CRITICALITIES:
            raise KnowledgeHubError("invalid result criticality")
        passed += int(row["passed"])
        latencies.append(_number(row.get("latency_ms"), "latency_ms"))
        if criticality == "critical" and not row["passed"]:
            critical_failures.append(row_id)
    ids = _string_list(ids, "case_ids", nonempty=True)
    if expected_case_ids:
        expected = _string_list(list(expected_case_ids), "expected_case_ids", nonempty=True)
        if set(ids) != set(expected):
            raise KnowledgeHubError("evaluation case coverage mismatch")
    latencies.sort()
    p95 = latencies[int(round((len(latencies) - 1) * 0.95))]
    return {
        "case_count": len(ids), "case_ids": sorted(ids),
        "case_set_sha256": _coverage_digest(ids),
        "pass_rate": passed / len(ids),
        "critical_failure_ids": sorted(critical_failures), "p95_ms": round(p95, 2),
    }


def _validate_summary(summary: Mapping[str, Any]) -> None:
    if not isinstance(summary, Mapping):
        raise KnowledgeHubError("evaluation summary must be an object")
    ids = _string_list(summary.get("case_ids"), "case_ids", nonempty=True)
    count = summary.get("case_count")
    if type(count) is not int or count != len(ids):
        raise KnowledgeHubError("evaluation case count mismatch")
    if summary.get("case_set_sha256") != _coverage_digest(ids):
        raise KnowledgeHubError("evaluation case fingerprint mismatch")
    _number(summary.get("pass_rate"), "pass_rate", 1.0)
    _number(summary.get("p95_ms"), "p95_ms")
    failures = _string_list(summary.get("critical_failure_ids"), "critical_failure_ids")
    if not set(failures).issubset(ids):
        raise KnowledgeHubError("critical failures are outside evaluated cases")


def compare_baseline(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    maximum_pass_rate_drop: float = 0.0,
    maximum_p95_regression_ratio: float = 1.20,
) -> Dict[str, Any]:
    drop = _number(maximum_pass_rate_drop, "maximum_pass_rate_drop", 1.0)
    ratio = _number(maximum_p95_regression_ratio, "maximum_p95_regression_ratio")
    if ratio < 1.0:
        raise KnowledgeHubError("maximum_p95_regression_ratio must be at least 1")
    failures: List[str] = []
    try:
        _validate_summary(baseline)
        _validate_summary(candidate)
    except KnowledgeHubError:
        failures.append("invalid-or-incomplete-evaluation")
    if not failures:
        if baseline["case_set_sha256"] != candidate["case_set_sha256"]:
            failures.append("case-coverage-mismatch")
        # Dataset/evaluator identities must agree when supplied. Source revisions
        # intentionally may differ: comparing different implementations is normal.
        for key in ("dataset_sha256", "evaluator_revision"):
            if key in baseline or key in candidate:
                if not baseline.get(key) or baseline.get(key) != candidate.get(key):
                    failures.append("{}-mismatch".format(key))
        if candidate["pass_rate"] + drop < baseline["pass_rate"]:
            failures.append("pass-rate-regression")
        if candidate["p95_ms"] > baseline["p95_ms"] * ratio:
            failures.append("p95-regression")
        if candidate["critical_failure_ids"]:
            failures.append("critical-case-failure")
    return {
        "schema_version": "knowledge-hub.eval-comparison.v2",
        "status": "pass" if not failures else "fail", "failures": failures,
        "baseline": dict(baseline), "candidate": dict(candidate),
        "newly_failing_critical_ids": (
            sorted(set(candidate["critical_failure_ids"]) - set(baseline["critical_failure_ids"]))
            if "invalid-or-incomplete-evaluation" not in failures else []
        ),
    }
