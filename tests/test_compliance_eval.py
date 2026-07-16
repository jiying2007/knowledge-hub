import json

from tools.codex_assets.knowledge_hub.compliance_eval import evaluate_compliance_cases
from tools.codex_assets.knowledge_hub.common import repository_root
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
    assert "git push" not in serialized
    assert validate_instance(repository_root(), "agent-compliance-eval-v1", payload)["status"] == "pass"
