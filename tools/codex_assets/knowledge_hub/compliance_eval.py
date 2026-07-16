"""Reproducible batch evaluation for explicit Agent action contracts."""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Mapping

from .agent_runtime import check_action
from .common import KnowledgeHubError


COMPLIANCE_EVAL_SCHEMA = "knowledge-hub.compliance-eval.v1"
VERDICTS = {"ALLOW", "BLOCK", "NEEDS_REVIEW"}


def _load_cases(path: pathlib.Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        raise KnowledgeHubError("compliance cases file does not exist: {}".format(path))
    rows: List[Dict[str, Any]] = []
    seen = set()
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise KnowledgeHubError("invalid compliance JSONL line {}".format(line_no)) from exc
        if not isinstance(row, dict):
            raise KnowledgeHubError("compliance case line {} must be an object".format(line_no))
        case_id = str(row.get("case_id", ""))
        expected = str(row.get("expected_verdict", ""))
        if not case_id or case_id in seen:
            raise KnowledgeHubError("compliance case_id must be non-empty and unique")
        if expected not in VERDICTS:
            raise KnowledgeHubError("invalid expected_verdict for {}".format(case_id))
        if not str(row.get("task", "")).strip() or not str(row.get("candidate", "")).strip():
            raise KnowledgeHubError("compliance case {} requires task and candidate".format(case_id))
        seen.add(case_id)
        rows.append(row)
    if not rows:
        raise KnowledgeHubError("compliance cases file is empty")
    return rows


def evaluate_compliance_cases(root: pathlib.Path, cases_path: pathlib.Path) -> Dict[str, Any]:
    cases = _load_cases(cases_path)
    results = []
    passed = 0
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
        case_passed = expected == actual
        passed += int(case_passed)
        results.append(
            {
                "case_id": str(case["case_id"]),
                "expected_verdict": expected,
                "actual_verdict": actual,
                "passed": case_passed,
                "candidate_sha256": result["candidate_sha256"],
                "applicable_ids": [row["id"] for row in result["applicable_must"]],
                "violation_ids": [row["id"] for row in result["violations"]],
                "needs_review_ids": [row["id"] for row in result["needs_review"]],
            }
        )
    return {
        "schema_version": COMPLIANCE_EVAL_SCHEMA,
        "read_only": True,
        "status": "pass" if passed == len(cases) else "fail",
        "total": len(cases),
        "passed": passed,
        "failed": len(cases) - passed,
        "results": results,
        "content_echoed": False,
    }
