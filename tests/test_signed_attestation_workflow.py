from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/signed-quality-attestation.yml")


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_signed_attestation_runs_only_after_quality_or_manual_master_dispatch():
    payload = _workflow()
    triggers = payload.get("on")
    assert isinstance(triggers, dict)
    assert "push" not in triggers
    workflow_run = triggers.get("workflow_run")
    assert isinstance(workflow_run, dict)
    assert workflow_run.get("workflows") == ["quality"]
    assert workflow_run.get("types") == ["completed"]
    assert "workflow_dispatch" in triggers

    job = payload["jobs"]["sign-and-verify"]
    condition = job.get("if", "")
    assert "workflow_run.conclusion == 'success'" in condition
    assert "workflow_run.event == 'push'" in condition
    assert "workflow_run.head_branch == 'master'" in condition
    assert "github.ref == 'refs/heads/master'" in condition


def test_signed_attestation_reuses_exact_quality_evidence_instead_of_recomputing():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "quality_evidence_binding_cli" in text
    assert "gh run download" in text
    assert "--name knowledge-hub-quality-evidence" in text
    assert "--name knowledge-hub-mcp-conformance" in text
    assert "mcp-conformance/evidence.json" in text
    assert "quality-source-run.json" in text
    assert '"head_branch": "master"' in text
    assert '"event": "push"' in text
    assert '"conclusion": "success"' in text

    assert "Run full engineering gate" not in text
    assert "Capture deterministic compliance evidence" not in text
    assert "Verify remote checkout in an offsite runner" not in text
    assert "Assess product and operational maturity independently" not in text


def test_signed_attestation_rebinds_hosting_terminal_and_oidc_to_source_revision():
    payload = _workflow()
    job = payload["jobs"]["sign-and-verify"]
    assert job["permissions"]["actions"] == "read"
    assert job["permissions"]["id-token"] == "write"
    assert job["permissions"]["attestations"] == "write"
    assert job["permissions"]["artifact-metadata"] == "write"
    assert job["env"]["SOURCE_REF"] == "refs/heads/master"
    assert job["env"]["SIGNER_WORKFLOW_REVISION"] == "${{ github.workflow_sha }}"

    text = WORKFLOW.read_text(encoding="utf-8")
    assert '--source-revision "${SOURCE_REVISION}"' in text
    assert 'KNOWLEDGE_SOURCE_REVISION="${SOURCE_REVISION}"' in text
    assert '--signer-digest "${SIGNER_WORKFLOW_REVISION}"' in text
    assert '--source-digest "${SIGNER_WORKFLOW_REVISION}"' not in text
    assert '--signer-source-revision "${SIGNER_WORKFLOW_REVISION}"' in text
    assert '--source-ref "${SOURCE_REF}"' in text
    assert "--deny-self-hosted-runners" in text


def test_signed_attestation_manual_reverification_requires_existing_successful_quality():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "actions/workflows/quality.yml/runs?branch=master&status=success" in text
    assert "No successful master Quality run is bound to SOURCE_REVISION" in text


def test_signed_attestation_upload_retains_quality_binding_and_fresh_hosting_evidence():
    payload = _workflow()
    steps = payload["jobs"]["sign-and-verify"]["steps"]
    upload = next(step for step in steps if step.get("name") == "Upload signed quality evidence")
    paths = {
        line.strip()
        for line in upload["with"]["path"].splitlines()
        if line.strip()
    }
    assert ".cache/knowledge-hub/quality-evidence-binding.json" in paths
    assert ".cache/knowledge-hub/hosting-posture.json" in paths
    assert ".cache/knowledge-hub/terminal-closure.json" in paths
    assert ".cache/knowledge-hub/signed-attestation/" in paths
