from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/ai-maintenance-sweep.yml")


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_ai_maintenance_has_only_trusted_scheduled_or_manual_triggers():
    payload = _workflow()
    assert set(payload["on"]) == {"schedule", "workflow_dispatch"}
    assert "pull_request" not in payload["on"]
    assert "pull_request_target" not in payload["on"]


def test_ai_maintenance_routes_only_critical_items_to_human():
    payload = _workflow()
    assert payload["permissions"] == {"contents": "read", "issues": "write"}
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "security-critical" in text
    assert "governance-critical" in text
    assert "ordinary_and_governance_routed_to_ai" in text
    assert "human_required" in text
    assert "git push" not in text
    assert "gh pr merge" not in text
    assert "knowledge-promote" not in text


def test_ai_maintenance_closes_stale_critical_issue_after_recovery():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Close stale critical maintenance issue when recovered" in text
    assert "gh issue close" in text
    assert "no longer requires a critical human decision" in text
