from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/ai-provider-discovery.yml")


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_ai_provider_discovery_has_no_untrusted_pr_trigger():
    payload = _workflow()
    assert set(payload["on"]) == {"schedule", "workflow_dispatch"}
    assert "pull_request" not in payload["on"]
    assert "pull_request_target" not in payload["on"]


def test_ai_provider_discovery_is_read_only_until_authorization_boundary():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--auto-route-unique --json" in text
    assert "selection is explicitly not authorization" in text.lower()
    assert "gh pr merge" not in text
    assert "git push" not in text
    assert "knowledge-promote" not in text
    assert "operator_binding_governed_apply" not in text


def test_ai_provider_discovery_only_requests_human_attention_for_human_route():
    payload = _workflow()
    assert payload["permissions"] == {"contents": "read", "issues": "write"}
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "ready-for-machine-ratchet" in text
    assert "mixed-routing" in text
    assert "steps.discover.outputs.human != '0'" in text
    assert "AI evidence binding: governed authorization pending" in text
    assert "append-only provider-verifiable" in text


def test_ai_provider_discovery_closes_stale_authorization_issue():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Close stale authorization issue when fresh state no longer needs it" in text
    assert "gh issue close" in text
    assert "the previous authorization packet is stale" in text


def test_ai_provider_discovery_keeps_machine_route_noncanonical():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "routing-bundle.json" in text
    assert "--machine-candidate-output" in text
    assert "machine-candidate-items.jsonl" in text
    assert "--machine-manifest-output" in text
    assert "machine-candidate-manifest.json" in text
    assert "materialized only under .cache as reviewable artifacts" in text
    assert "operator_binding_governed_apply" not in text
    assert "git push" not in text
    assert "gh pr create" not in text
    assert "gh pr merge" not in text


def test_ai_provider_discovery_closes_human_issue_when_only_machine_work_remains():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "steps.discover.outputs.human == '0'" in text
    assert "gh issue close" in text
