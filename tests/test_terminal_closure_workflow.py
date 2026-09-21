from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/terminal-closure.yml")


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_terminal_closure_is_manual_master_only_and_reads_actions():
    payload = _workflow()
    assert set(payload["on"]) == {"workflow_dispatch"}
    assert payload["permissions"] == {"contents": "read", "actions": "read"}
    job = payload["jobs"]["terminal"]
    assert job["if"] == "${{ github.ref == 'refs/heads/master' }}"
    assert job["env"]["SOURCE_REVISION"] == "${{ github.sha }}"


def test_terminal_closure_reuses_exact_quality_and_mcp_artifacts():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "actions/workflows/quality.yml/runs?branch=master&status=success" in text
    assert "--name knowledge-hub-quality-evidence" in text
    assert "--name knowledge-hub-mcp-conformance" in text
    assert "quality_evidence_binding_cli" in text
    assert "mcp-conformance/evidence.json" in text
    assert "Run full engineering gate" not in text
    assert "knowledge-restore-drill.sh --source-mode head" not in text
    assert "knowledge-final-gate.sh --final-profile product" not in text


def test_terminal_closure_avoids_pipefail_early_close_selector():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "{print $1; exit}" not in text
    assert "found=1" in text


def test_terminal_closure_refreshes_remote_hosting_before_enforcement():
    text = WORKFLOW.read_text(encoding="utf-8")
    remote_pos = text.index("remote_branch_inventory_cli")
    hosting_pos = text.index("hosting_posture_cli")
    terminal_pos = text.index("terminal_closure_cli")
    assert remote_pos < hosting_pos < terminal_pos
    assert 'KNOWLEDGE_SOURCE_REVISION="${SOURCE_REVISION}"' in text
    assert 'KNOWLEDGE_GITHUB_REPOSITORY="${GITHUB_REPOSITORY}"' in text
