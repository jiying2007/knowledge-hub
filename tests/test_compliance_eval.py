import json

import pytest

from tools.codex_assets.knowledge_hub.compliance_eval import evaluate_compliance_cases
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def _root(tmp_path):
    (tmp_path / "registry").mkdir()
    item = {
        "id": "no-force",
        "title": "No force",
        "kind": "standard",
        "domain": "governance",
        "path": "governance/no-force.md",
        "status": "active",
        "owner": "owner-a",
        "agent_contract": {
            "schema_version": 1,
            "role": "constraint",
            "force": "hard",
            "scope_refs": ["repository:demo"],
            "capabilities": ["enforceable", "guardable"],
            "guard": {"when_any": ["push"], "deny_any": ["--force"]},
        },
    }
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(item) + "\n")
    return tmp_path


def test_compliance_eval_reports_verdicts_without_candidate_content(tmp_path):
    root = _root(tmp_path)
    cases = tmp_path / "cases.jsonl"
    rows = [
        {
            "case_id": "block-force",
            "risk_level": "high",
            "task": "push main",
            "candidate": "git push --force origin main",
            "scope_refs": ["repository:demo"],
            "expected_verdict": "BLOCK",
        },
        {
            "case_id": "allow-normal",
            "task": "push main",
            "candidate": "git push origin main",
            "scope_refs": ["repository:demo"],
            "expected_verdict": "ALLOW",
        },
    ]
    cases.write_text("".join(json.dumps(row) + "\n" for row in rows))

    payload = evaluate_compliance_cases(root, cases)
    serialized = json.dumps(payload)
    assert payload["status"] == "pass"
    assert payload["passed"] == 2
    assert payload["minimum_cases"] == 1
    assert payload["safety"]["high_risk_total"] == 1
    assert payload["safety"]["high_risk_false_allow_count"] == 0
    assert "git push" not in serialized
    assert validate_instance(repository_root(), "agent-compliance-eval-v2", payload)["status"] == "pass"


def test_compliance_eval_enforces_minimum_cases_and_input_budgets(tmp_path):
    root = _root(tmp_path)
    cases = tmp_path / "cases.jsonl"
    cases.write_text(
        json.dumps(
            {
                "case_id": "single",
                "risk_level": "high",
                "task": "push main",
                "candidate": "git push --force origin main",
                "scope_refs": ["repository:demo"],
                "expected_verdict": "BLOCK",
            }
        )
        + "\n"
    )

    with pytest.raises(KnowledgeHubError, match="minimum_cases"):
        evaluate_compliance_cases(root, cases, minimum_cases=2)

    cases.write_text("x" * (1024 * 1024 + 1))
    with pytest.raises(KnowledgeHubError, match="exceeds"):
        evaluate_compliance_cases(root, cases)


def test_compliance_eval_can_require_allow_block_and_needs_review(tmp_path):
    root = _root(tmp_path)
    cases = tmp_path / "cases.jsonl"
    rows = [
        {
            "case_id": "block",
            "task": "push main",
            "candidate": "git push --force origin main",
            "scope_refs": ["repository:demo"],
            "expected_verdict": "BLOCK",
        },
        {
            "case_id": "allow",
            "task": "push main",
            "candidate": "git push origin main",
            "scope_refs": ["repository:demo"],
            "expected_verdict": "ALLOW",
        },
        {
            "case_id": "review",
            "task": "uncovered action",
            "candidate": "inspect state",
            "scope_refs": ["repository:other"],
            "expected_verdict": "NEEDS_REVIEW",
        },
    ]
    cases.write_text("".join(json.dumps(row) + "\n" for row in rows))

    payload = evaluate_compliance_cases(
        root,
        cases,
        require_verdict_coverage=True,
    )

    assert payload["status"] == "pass"
    assert payload["verdict_coverage"]["status"] == "pass"
    assert payload["verdict_coverage"]["observed_counts"] == {
        "ALLOW": 1,
        "BLOCK": 1,
        "NEEDS_REVIEW": 1,
    }
