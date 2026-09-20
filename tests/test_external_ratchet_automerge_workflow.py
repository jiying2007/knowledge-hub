from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/external-ratchet-automerge.yml")


def _workflow():
    payload = yaml.load(
        WORKFLOW.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    assert isinstance(payload, dict)
    return payload


def test_external_ratchet_automerge_runs_only_after_exact_quality():
    payload = _workflow()
    assert set(payload["on"]) == {"workflow_run"}
    trigger = payload["on"]["workflow_run"]
    assert trigger["workflows"] == ["quality"]
    assert trigger["types"] == ["completed"]

    job = payload["jobs"]["merge"]
    condition = job["if"]
    assert "workflow_run.conclusion == 'success'" in condition
    assert "workflow_run.event == 'pull_request'" in condition
    assert "workflow_run.event == 'workflow_dispatch'" in condition
    assert "workflow_run.head_repository.full_name == github.repository" in condition
    assert "automation/external-gap-" in condition


def test_external_ratchet_automerge_permissions_are_job_scoped():
    payload = _workflow()
    assert payload["permissions"] == {"contents": "read"}
    assert payload["jobs"]["merge"]["permissions"] == {
        "contents": "write",
        "pull-requests": "write",
        "actions": "read",
    }


def test_external_ratchet_automerge_executes_only_trusted_master_code():
    payload = _workflow()
    steps = payload["jobs"]["merge"]["steps"]
    checkout = [
        step
        for step in steps
        if str(step.get("uses", "")).startswith("actions/checkout@")
    ]
    assert len(checkout) == 1
    assert checkout[0]["with"]["ref"] == "${{ env.WORKFLOW_SHA }}"
    assert checkout[0]["with"]["persist-credentials"] == "false"

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "ref: ${{ env.HEAD_SHA }}" not in text
    assert "pull_request_target" not in text
    assert "verify_external_evidence_ratchet" in text


def test_external_ratchet_automerge_requires_private_protected_current_master():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "live repository must remain private" in text
    assert "master must be protected before external ratchet auto-merge" in text
    assert "trusted external auto-merge workflow is not current master" in text
    assert "external ratchet head must be direct child of current master" in text
    assert "external ratchet PR base SHA is stale" in text
    assert "external ratchet PR must change exactly two files" in text


def test_external_ratchet_automerge_allows_only_registry_and_durable_ledger():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "registry/knowledge-platform-p5-p10.json" in text
    assert "registry/durable-evidence-ledger.jsonl" in text
    assert "external ratchet PR changed paths outside allowlist" in text
    assert "external ratchet PR must append one durable record" in text
    assert "external branch does not match trusted origin run" in text


def test_external_ratchet_automerge_replays_exact_origin_artifact():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert (
        "actions/runs/${ORIGIN_RUN_ID}/attempts/${ORIGIN_RUN_ATTEMPT}"
        in text
    )
    assert (
        "knowledge-hub-external-ratchet-candidate-"
        "${ORIGIN_RUN_ID}-${ORIGIN_RUN_ATTEMPT}"
        in text
    )
    assert "closure-candidate-receipt.json" in text
    assert "intake-receipt.json" in text
    assert "host-binding.json" in text
    assert "ratchet-proposal.json" in text
    assert "external-evidence-ratchet-verification-v1" in text
    assert "external ratchet verification contract failed" in text


def test_external_ratchet_automerge_revalidates_title_head_and_base_before_merge():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert (
        'expected_title="chore(external): ratchet '
        '${GAP} ${CANDIDATE_SHA:0:12} @ ${MASTER_SHA:0:12}"'
        in text
    )
    assert "external ratchet PR moved after verification" in text
    assert "external ratchet PR title no longer matches verified candidate" in text
    assert 'pulls/${PR_NUMBER}/merge' in text
    assert '-f sha="${HEAD_SHA}"' in text
    assert '-f merge_method="squash"' in text


def test_external_ratchet_automerge_has_no_direct_master_write_and_cleans_branch():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "git push" not in text
    assert "HEAD:refs/heads/master" not in text
    assert "Retire merged external ratchet branch" in text
    assert "--method DELETE" in text


def test_external_ratchet_automerge_retains_bounded_verification_proof():
    payload = _workflow()
    upload = next(
        step
        for step in payload["jobs"]["merge"]["steps"]
        if step.get("name") == "Upload bounded external auto-merge proof"
    )
    assert upload["if"] == "always()"
    assert upload["with"]["retention-days"] == "90"
    assert (
        upload["with"]["path"]
        == ".cache/knowledge-hub/external-ratchet-automerge/*.json"
    )
    assert "origin-artifact" not in upload["with"]["path"]


def test_external_ratchet_automerge_matches_ai_first_policy():
    import json

    policy = json.loads(
        Path("registry/ai-operations-policy.json").read_text(encoding="utf-8")
    )
    boundary = policy["external_evidence"]
    assert boundary["strict_validator_required"] is True
    assert boundary["same_repository_hosted_chain_required"] is True
    assert boundary["machine_ratchet_auto_merge_requires_protected_branch"] is True
    assert boundary["machine_ratchet_auto_merge_requires_exact_head_quality"] is True
    assert boundary["machine_ratchet_auto_merge_executes_pr_code"] is False

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "master must be protected before external ratchet auto-merge" in text
    assert "trigger Quality head repository mismatch" in text
    assert "verify_external_evidence_ratchet" in text


def test_external_ratchet_automerge_uses_runtime_dependencies():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "requirements-runtime.lock" in text
    assert "requirements-dev.lock" not in text
