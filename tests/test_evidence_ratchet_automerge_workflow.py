from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/evidence-ratchet-automerge.yml")


def _workflow():
    payload = yaml.load(
        WORKFLOW.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    assert isinstance(payload, dict)
    return payload


def test_evidence_ratchet_automerge_triggers_only_after_quality():
    payload = _workflow()
    assert set(payload["on"]) == {"workflow_run"}
    trigger = payload["on"]["workflow_run"]
    assert trigger["workflows"] == ["quality"]
    assert trigger["types"] == ["completed"]
    assert "pull_request_target" not in payload["on"]

    job = payload["jobs"]["merge"]
    condition = job["if"]
    assert "workflow_run.conclusion == 'success'" in condition
    assert "workflow_run.event == 'pull_request'" in condition
    assert "workflow_run.event == 'workflow_dispatch'" in condition
    assert "workflow_run.head_repository.full_name == github.repository" in condition
    assert "automation/evidence-bind-" in condition


def test_evidence_ratchet_automerge_has_job_scoped_least_privilege():
    payload = _workflow()
    assert payload["permissions"] == {"contents": "read"}
    job = payload["jobs"]["merge"]
    assert job["permissions"] == {
        "contents": "write",
        "pull-requests": "write",
        "actions": "read",
    }


def test_evidence_ratchet_automerge_never_executes_pr_code():
    payload = _workflow()
    steps = payload["jobs"]["merge"]["steps"]
    checkout = [step for step in steps if str(step.get("uses", "")).startswith("actions/checkout@")]
    assert len(checkout) == 1
    assert checkout[0]["with"]["ref"] == "${{ env.WORKFLOW_SHA }}"
    assert checkout[0]["with"]["persist-credentials"] == "false"

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Checkout trusted workflow revision" in text
    assert "ref: ${{ env.HEAD_SHA }}" not in text
    assert "ref: ${{ github.event.workflow_run.head_sha }}" not in text
    assert "pull_request_target" not in text


def test_evidence_ratchet_automerge_requires_private_protected_current_master():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "live repository must remain private" in text
    assert "master must be protected before machine ratchet auto-merge" in text
    assert "trusted auto-merge workflow is not bound to current master" in text
    assert "machine evidence head must be a direct child of current master" in text
    assert "machine evidence PR base SHA is stale" in text
    assert "machine evidence PR must change exactly two files" in text


def test_evidence_ratchet_automerge_revalidates_exact_quality_identity():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '"name": "quality"' in text
    assert '"path": ".github/workflows/quality.yml"' in text
    assert 'run.get("event") not in {"pull_request", "workflow_dispatch"}' in text
    assert '"conclusion": "success"' in text
    assert '"head_sha": os.environ["HEAD_SHA"]' in text
    assert "trigger Quality head repository mismatch" in text


def test_evidence_ratchet_automerge_allows_only_two_canonical_paths():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "registry/items.jsonl" in text
    assert "registry/durable-evidence-ledger.jsonl" in text
    assert "machine evidence PR changed paths outside allowlist" in text
    assert "machine evidence PR must append one durable record" in text
    assert "^automation/evidence-bind-[0-9a-f]{12}-[0-9]+$" in text
    assert "machine evidence branch does not match trusted origin run" in text


def test_evidence_ratchet_automerge_replays_exact_origin_run_and_artifact():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert (
        "actions/runs/${ORIGIN_RUN_ID}/attempts/${ORIGIN_RUN_ATTEMPT}"
        in text
    )
    assert "knowledge-hub-ai-provider-discovery-${ORIGIN_RUN_ID}-${ORIGIN_RUN_ATTEMPT}" in text
    assert "gh run download" in text
    assert "routing-bundle.json" in text
    assert "machine-candidate-items.jsonl" in text
    assert "machine-candidate-manifest.json" in text
    assert "verify_machine_evidence_ratchet" in text
    assert "verification.json" in text


def test_evidence_ratchet_automerge_revalidates_expected_title_and_head_before_merge():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "candidate_sha256" in text
    assert (
        'expected_title="chore(evidence): ratchet machine refs '
        '${CANDIDATE_SHA256:0:12} @ ${MASTER_SHA:0:12}"'
        in text
    )
    assert "machine evidence PR moved after verification" in text
    assert "machine evidence PR title no longer matches verified candidate" in text
    assert 'pulls/${PR_NUMBER}/merge' in text
    assert '-f sha="${HEAD_SHA}"' in text
    assert '-f merge_method="squash"' in text


def test_evidence_ratchet_automerge_has_no_direct_master_write_and_cleans_branch():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "git push" not in text
    assert "HEAD:refs/heads/master" not in text
    assert "--method DELETE" in text
    assert "Retire merged machine evidence branch" in text


def test_evidence_ratchet_automerge_uses_runtime_dependency_surface():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "requirements-runtime.lock" in text
    assert "requirements-dev.lock" not in text


def test_evidence_ratchet_automerge_retains_bounded_verification_metadata():
    payload = _workflow()
    steps = payload["jobs"]["merge"]["steps"]
    upload = next(
        step
        for step in steps
        if step.get("name") == "Upload bounded auto-merge verification"
    )
    assert upload["if"] == "always()"
    assert upload["with"]["retention-days"] == "90"
    assert (
        upload["with"]["path"]
        == ".cache/knowledge-hub/evidence-ratchet-automerge/*.json"
    )
    assert "origin-artifact" not in upload["with"]["path"]


def test_evidence_ratchet_automerge_resolves_identity_after_trusted_checkout():
    payload = _workflow()
    steps = payload["jobs"]["merge"]["steps"]
    checkout_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Checkout trusted workflow revision"
    )
    resolve_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Resolve protected current master and exact PR"
    )
    fetch_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Fetch exact base and head canonical files"
    )
    assert checkout_index < resolve_index < fetch_index
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "trusted auto-merge workflow is not bound to current master" in text


def test_evidence_ratchet_automerge_validates_verification_contract():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "operator-machine-ratchet-verification-v1" in text
    assert "machine ratchet verification contract failed" in text
