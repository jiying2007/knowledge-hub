from pathlib import Path

import yaml


MANUAL_WORKFLOW = Path(".github/workflows/mcp-conformance.yml")
QUALITY_WORKFLOW = Path(".github/workflows/quality.yml")


def _workflow(path):
    payload = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_exact_head_mcp_is_part_of_quality_for_pr_and_master():
    payload = _workflow(QUALITY_WORKFLOW)
    triggers = payload["on"]
    assert triggers["push"]["branches"] == ["master"]
    assert "pull_request" in triggers
    job = payload["jobs"]["mcp-conformance"]
    assert job["name"] == "Official MCP 2026 native profile"
    assert job["runs-on"] == "ubuntu-latest"
    text = QUALITY_WORKFLOW.read_text(encoding="utf-8")
    assert "run-mcp-conformance.sh" in text
    assert "knowledge-hub-mcp-conformance" in text


def test_standalone_mcp_workflow_is_manual_only_to_avoid_duplicate_private_minutes():
    payload = _workflow(MANUAL_WORKFLOW)
    triggers = payload["on"]
    assert set(triggers) == {"workflow_dispatch"}
    assert payload["concurrency"]["cancel-in-progress"] == "false"


def test_manual_mcp_reverification_keeps_hosted_runner_and_evidence_upload():
    payload = _workflow(MANUAL_WORKFLOW)
    job = payload["jobs"]["native-profile"]
    assert job["runs-on"] == "ubuntu-latest"
    text = MANUAL_WORKFLOW.read_text(encoding="utf-8")
    assert "run-mcp-conformance.sh" in text
    assert "upload-artifact" in text
