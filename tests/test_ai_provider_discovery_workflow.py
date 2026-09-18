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
    assert "--auto-review-unique --json" in text
    assert "selection is explicitly not authorization" in text.lower()
    assert "gh pr merge" not in text
    assert "git push" not in text
    assert "knowledge-promote" not in text
    assert "operator_binding_governed_apply" not in text


def test_ai_provider_discovery_only_requests_human_attention_after_review_bundle():
    payload = _workflow()
    assert payload["permissions"] == {"contents": "read", "issues": "write"}
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "needs-governed-authorization" in text
    assert "AI evidence binding: governed authorization pending" in text
