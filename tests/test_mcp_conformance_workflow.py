from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/mcp-conformance.yml")


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_mcp_conformance_runs_for_every_pr_and_master_push():
    payload = _workflow()
    triggers = payload.get("on")
    assert isinstance(triggers, dict)

    push = triggers.get("push")
    assert isinstance(push, dict)
    assert push.get("branches") == ["master"]
    assert "paths" not in push
    assert "paths-ignore" not in push

    assert "pull_request" in triggers
    pull_request = triggers.get("pull_request")
    if isinstance(pull_request, dict):
        assert "paths" not in pull_request
        assert "paths-ignore" not in pull_request


def test_mcp_conformance_preserves_master_revision_evidence():
    payload = _workflow()
    concurrency = payload.get("concurrency")
    assert isinstance(concurrency, dict)
    assert concurrency.get("cancel-in-progress") == "${{ github.event_name == 'pull_request' }}"


def test_mcp_conformance_keeps_manual_reverification_entrypoint():
    payload = _workflow()
    triggers = payload.get("on")
    assert isinstance(triggers, dict)
    assert "workflow_dispatch" in triggers
