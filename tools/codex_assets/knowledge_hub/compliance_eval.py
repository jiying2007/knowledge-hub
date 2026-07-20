"""Reproducible batch evaluation for explicit Agent action contracts."""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List

from .agent_runtime import check_action
from .common import KnowledgeHubError, read_utf8_bounded


COMPLIANCE_EVAL_SCHEMA = "knowledge-hub.compliance-eval.v2"
VERDICTS = {"ALLOW", "BLOCK", "NEEDS_REVIEW"}
RISK_LEVELS = {"normal", "high"}
COMPLIANCE_MAX_FILE_BYTES = 1024 * 1024
COMPLIANCE_MAX_LINE_BYTES = 16 * 1024
COMPLIANCE_MAX_CASES = 1000


def _load_cases(path: pathlib.Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        raise KnowledgeHubError("compliance cases file does not exist: {}".format(path))
    text = read_utf8_bounded(
        path,
        COMPLIANCE_MAX_FILE_BYTES,
        "compliance cases file",
    )
    rows: List[Dict[str, Any]] = []
    seen = set()
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        if len(line.encode("utf-8")) > COMPLIANCE_MAX_LINE_BYTES:
            raise KnowledgeHubError(
                "compliance JSONL line {} exceeds {} bytes".format(
                    line_no, COMPLIANCE_MAX_LINE_BYTES
                )
            )
        if len(rows) >= COMPLIANCE_MAX_CASES:
            raise KnowledgeHubError(
                "compliance cases exceed {} rows".format(COMPLIANCE_MAX_CASES)
            )
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise KnowledgeHubError("invalid compliance JSONL line {}".format(line_no)) from exc
        if not isinstance(row, dict):
            raise KnowledgeHubError("compliance case line {} must be an object".format(line_no))
        case_id = str(row.get("case_id", ""))
        expected = str(row.get("expected_verdict", ""))
        risk_level = str(row.get("risk_level", "normal"))
        if not case_id or case_id in seen:
            raise KnowledgeHubError("compliance case_id must be non-empty and unique")
        if expected not in VERDICTS:
            raise KnowledgeHubError("invalid expected_verdict for {}".format(case_id))
        if risk_level not in RISK_LEVELS:
            raise KnowledgeHubError("invalid risk_level for {}".format(case_id))
        if not str(row.get("task", "")).strip() or not str(row.get("candidate", "")).strip():
            raise KnowledgeHubError("compliance case {} requires task and candidate".format(case_id))
        seen.add(case_id)
        row["risk_level"] = risk_level
        rows.append(row)
    if not rows:
        raise KnowledgeHubError("compliance cases file is empty")
    return rows


def evaluate_compliance_cases(
    root: pathlib.Path,
    cases_path: pathlib.Path,
    minimum_cases: int = 1,
    require_verdict_coverage: bool = False,
) -> Dict[str, Any]:
    if not isinstance(minimum_cases, int) or not 1 <= minimum_cases <= COMPLIANCE_MAX_CASES:
        raise KnowledgeHubError(
            "minimum_cases must be between 1 and {}".format(COMPLIANCE_MAX_CASES)
        )
    cases = _load_cases(cases_path)
    if len(cases) < minimum_cases:
        raise KnowledgeHubError(
            "compliance cases do not meet minimum_cases={}: got {}".format(
                minimum_cases, len(cases)
            )
        )
    results = []
    passed = 0
    high_risk_total = 0
    high_risk_allowed = 0
    high_risk_false_allow = 0
    verdict_distribution = {verdict: 0 for verdict in sorted(VERDICTS)}
    for case in cases:
        result = check_action(
            root,
            str(case["task"]),
            str(case["candidate"]),
            scope_refs=[str(value) for value in case.get("scope_refs", [])],
            asserted_exceptions=[str(value) for value in case.get("exceptions", [])],
        )
        expected = str(case["expected_verdict"])
        actual = str(result["verdict"])
        verdict_distribution[actual] = verdict_distribution.get(actual, 0) + 1
        case_passed = expected == actual
        high_risk = case.get("risk_level") == "high"
        high_risk_total += int(high_risk)
        high_risk_allowed += int(high_risk and actual == "ALLOW")
        high_risk_false_allow += int(
            high_risk and expected != "ALLOW" and actual == "ALLOW"
        )
        passed += int(case_passed)
        results.append(
            {
                "case_id": str(case["case_id"]),
                "expected_verdict": expected,
                "actual_verdict": actual,
                "passed": case_passed,
                "risk_level": case.get("risk_level", "normal"),
                "candidate_sha256": result["candidate_sha256"],
                "applicable_ids": [row["id"] for row in result["applicable_must"]],
                "violation_ids": [row["id"] for row in result["violations"]],
                "needs_review_ids": [row["id"] for row in result["needs_review"]],
            }
        )
    missing_verdicts = [
        verdict
        for verdict in sorted(VERDICTS)
        if verdict_distribution.get(verdict, 0) == 0
    ]
    coverage_ready = not require_verdict_coverage or not missing_verdicts
    return {
        "schema_version": COMPLIANCE_EVAL_SCHEMA,
        "read_only": True,
        "status": "pass" if passed == len(cases) and coverage_ready else "fail",
        "total": len(cases),
        "minimum_cases": minimum_cases,
        "passed": passed,
        "failed": len(cases) - passed,
        "results": results,
        "safety": {
            "high_risk_total": high_risk_total,
            "high_risk_allowed_count": high_risk_allowed,
            "high_risk_false_allow_count": high_risk_false_allow,
        },
        "verdict_coverage": {
            "required": require_verdict_coverage,
            "required_verdicts": sorted(VERDICTS),
            "observed_counts": verdict_distribution,
            "missing_verdicts": missing_verdicts,
            "status": "pass" if coverage_ready else "fail",
        },
        "content_echoed": False,
    }
