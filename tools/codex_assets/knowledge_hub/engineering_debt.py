"""P10 engineering debt burn-down and mutation contract helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

from .common import KnowledgeHubError

DEFAULT_REDUCTION_RATIO = 0.15


def debt_targets(
    legacy_caps: Mapping[str, Any],
    *,
    reduction_ratio: float = DEFAULT_REDUCTION_RATIO,
) -> Dict[str, int]:
    if not 0.0 < reduction_ratio < 1.0:
        raise KnowledgeHubError("reduction_ratio must be between 0 and 1")
    result: Dict[str, int] = {}
    for path, raw in legacy_caps.items():
        cap = int(raw)
        if cap <= 0:
            raise KnowledgeHubError("legacy cap must be positive")
        result[str(path)] = max(1, int(cap * (1.0 - reduction_ratio)))
    return result


def debt_report(
    legacy_caps: Mapping[str, Any],
    current_lines: Mapping[str, Any],
    *,
    reduction_ratio: float = DEFAULT_REDUCTION_RATIO,
) -> Dict[str, Any]:
    targets = debt_targets(legacy_caps, reduction_ratio=reduction_ratio)
    rows: List[Dict[str, Any]] = []
    failures: List[str] = []
    for path in sorted(targets):
        baseline = int(legacy_caps[path])
        current = int(current_lines.get(path, baseline))
        target = targets[path]
        progress = baseline - current
        rows.append(
            {
                "path": path,
                "baseline_lines": baseline,
                "current_lines": current,
                "target_lines": target,
                "burned_lines": max(0, progress),
                "target_met": current <= target,
                "new_regression": current > baseline,
            }
        )
        if current > baseline:
            failures.append(path)
    return {
        "schema_version": "knowledge-hub.engineering-debt.v2",
        "status": "pass" if not failures else "fail",
        "policy": "report-debt-fail-new-regression",
        "quarterly_reduction_target": reduction_ratio,
        "rows": rows,
        "new_regression_paths": failures,
    }


def mutation_contract(
    *,
    baseline_blocked: bool,
    mutated_blocked: bool,
    probe_name: str,
) -> Dict[str, Any]:
    if not probe_name or len(probe_name) > 256:
        raise KnowledgeHubError("mutation probe name must be non-empty and bounded")
    detected = baseline_blocked and not mutated_blocked
    return {
        "schema_version": "knowledge-hub.mutation-contract.v1",
        "status": "pass" if detected else "fail",
        "probe": probe_name,
        "baseline_blocked": bool(baseline_blocked),
        "mutated_blocked": bool(mutated_blocked),
        "mutation_detected": detected,
    }


def branch_coverage_contract(
    *,
    measured_percent: float,
    minimum_percent: float = 70.0,
) -> Dict[str, Any]:
    if not 0.0 <= measured_percent <= 100.0:
        raise KnowledgeHubError("branch coverage must be a percentage")
    if not 0.0 <= minimum_percent <= 100.0:
        raise KnowledgeHubError("minimum branch coverage must be a percentage")
    return {
        "schema_version": "knowledge-hub.branch-coverage-contract.v1",
        "status": "pass" if measured_percent >= minimum_percent else "fail",
        "measured_percent": round(float(measured_percent), 2),
        "minimum_percent": round(float(minimum_percent), 2),
    }
