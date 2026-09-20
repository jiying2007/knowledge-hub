from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/ai-provider-discovery.yml")


def _workflow():
    payload = yaml.load(
        WORKFLOW.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    assert isinstance(payload, dict)
    return payload


def test_ai_provider_discovery_uses_only_trusted_triggers():
    payload = _workflow()
    triggers = payload["on"]
    assert set(triggers) == {
        "workflow_run",
        "schedule",
        "workflow_dispatch",
        "pull_request",
    }
    assert triggers["workflow_run"]["workflows"] == ["quality"]
    assert triggers["workflow_run"]["types"] == ["completed"]
    assert triggers["pull_request"]["types"] == ["closed"]
    assert "push" not in triggers
    assert "pull_request_target" not in triggers

    discover = payload["jobs"]["discover"]
    condition = discover["if"]
    assert "github.event_name == 'schedule'" in condition
    assert "github.event_name == 'workflow_dispatch'" in condition
    assert "github.ref == 'refs/heads/master'" in condition
    assert "github.event_name == 'workflow_run'" in condition
    assert "workflow_run.conclusion == 'success'" in condition
    assert "workflow_run.event == 'push'" in condition
    assert "workflow_run.head_branch == 'master'" in condition
    assert "github.workflow_sha == github.event.workflow_run.head_sha" in condition
    assert discover["env"]["SOURCE_REVISION"] == (
        "${{ github.event_name == 'workflow_run' && "
        "github.event.workflow_run.head_sha || github.sha }}"
    )


def test_ai_provider_discovery_write_permissions_are_job_scoped():
    payload = _workflow()
    assert payload["permissions"] == {"contents": "read"}

    discover = payload["jobs"]["discover"]
    assert discover["permissions"] == {
        "contents": "write",
        "pull-requests": "write",
        "issues": "write",
        "actions": "write",
    }
    gc = payload["jobs"]["automation-branch-gc"]
    assert gc["permissions"] == {"contents": "write"}


def test_ai_provider_discovery_revalidates_exact_successful_master_quality():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Verify exact successful master Quality" in text
    assert "actions/workflows/quality.yml/runs?branch=master&status=success" in text
    assert '"head_sha": os.environ["SOURCE_REVISION"]' in text
    assert '"head_branch": "master"' in text
    assert '"event": "push"' in text
    assert '"conclusion": "success"' in text
    assert '".github/workflows/quality.yml"' in text


def test_ai_provider_discovery_routes_machine_and_human_evidence_separately():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--auto-route-unique" in text
    assert "--machine-candidate-output" in text
    assert "machine-candidate-items.jsonl" in text
    assert "--machine-manifest-output" in text
    assert "machine-candidate-manifest.json" in text
    assert "ready-for-machine-ratchet" in text
    assert "needs-governed-authorization" in text
    assert "mixed-routing" in text
    assert (
        "steps.discover.outputs.human_status == "
        "'needs-governed-authorization'"
        in text
    )
    assert "steps.discover.outputs.machine != '0'" in text


def test_ai_provider_discovery_machine_pr_is_bounded_and_not_direct_master_write():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Create governed machine evidence ratchet PR" in text
    assert 'branch="automation/evidence-bind-' in text
    assert "registry/items.jsonl" in text
    assert "registry/durable-evidence-ledger.jsonl" in text
    assert "changed paths outside the bounded allowlist" in text
    assert "gh pr create" in text
    assert 'HEAD:refs/heads/${branch}' in text
    assert "HEAD:refs/heads/master" not in text
    assert "gh pr merge" not in text
    assert "operator_binding_governed_apply" not in text
    assert "knowledge-promote" not in text


def test_ai_provider_discovery_revalidates_machine_provenance_and_contracts():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Prepare trusted machine-ratchet provenance" in text
    assert (
        "actions/runs/${GITHUB_RUN_ID}/attempts/${GITHUB_RUN_ATTEMPT}"
        in text
    )
    assert '"name": "ai-provider-discovery"' in text
    assert '"path": ".github/workflows/ai-provider-discovery.yml"' in text
    assert 'run.get("event") not in {' in text
    assert "operator-auto-route-v1" in text
    assert "operator-machine-ratchet-candidate-v1" in text
    assert "durable-evidence-record-v1" in text
    assert '"event_type": "evidence-binding-ratchet"' in text
    assert "machine candidate byte digest mismatch" in text


def test_ai_provider_discovery_pr_creation_is_idempotent_and_cleans_failure():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "identical machine evidence ratchet PR already open" in text
    assert "PR creation failed; deleting unowned machine evidence branch" in text
    assert 'git push "${remote}" --delete "${branch}" || true' in text
    assert "Superseded by fresh machine evidence ratchet" in text


def test_ai_provider_discovery_routes_only_remaining_human_boundary_to_issue():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Route only semantic or release authorization to a human" in text
    assert (
        "steps.discover.outputs.human_status == "
        "'needs-governed-authorization'"
        in text
    )
    assert "AI evidence binding: governed authorization pending" in text
    assert "release/owner/device/production evidence was not fabricated" in text
    assert "Close stale authorization issue when no human route remains" in text
    assert (
        "steps.discover.outputs.human_status != "
        "'needs-governed-authorization'"
        in text
    )
    assert "gh issue close" in text


def test_ai_provider_discovery_retires_closed_machine_evidence_branches():
    payload = _workflow()
    gc = payload["jobs"]["automation-branch-gc"]
    condition = gc["if"]
    assert "github.event_name == 'pull_request'" in condition
    assert "github.event.pull_request.head.repo.full_name == github.repository" in condition
    assert "automation/evidence-bind-" in condition

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "^automation/evidence-bind-[0-9a-f]{12}-[0-9]+$" in text
    assert "--method DELETE" in text


def test_ai_provider_discovery_uses_runtime_dependency_surface():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "requirements-runtime.lock" in text
    assert "requirements-dev.lock" not in text


def test_ai_provider_discovery_uploads_origin_artifact_before_creating_pr():
    payload = _workflow()
    steps = payload["jobs"]["discover"]["steps"]
    upload_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Upload bounded discovery evidence"
    )
    pr_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Create governed machine evidence ratchet PR"
    )
    assert upload_index < pr_index
    assert steps[upload_index]["if"] == "always()"


def test_ai_provider_discovery_self_heals_pre_protection_open_pr():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "identical machine evidence ratchet PR already open while master remains unprotected" in text
    assert "master protection is active; retaining" in text
    assert "fresh trusted-origin PR" in text
    protected_index = text.index("identical machine evidence ratchet PR already open while master remains unprotected")
    create_index = text.index("gh pr create")
    assert protected_index < create_index


def test_ai_provider_discovery_closes_superseded_pr_only_after_fresh_pr_exists():
    text = WORKFLOW.read_text(encoding="utf-8")
    create_index = text.index("gh pr create")
    supersede_index = text.index("Superseded by fresh machine evidence ratchet")
    assert create_index < supersede_index


def test_ai_provider_discovery_does_not_escalate_blocked_human_route():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '"human_status={}\\n".format(' in text
    assert '"machine_status={}\\n".format(' in text
    assert (
        "steps.discover.outputs.human_status == "
        "'needs-governed-authorization'"
        in text
    )


def test_ai_provider_discovery_explicitly_dispatches_quality_for_token_created_pr():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "ensure_quality()" in text
    assert "actions/workflows/quality.yml/runs?branch=${quality_branch}" in text
    assert "gh workflow run quality.yml" in text
    assert '--ref "${quality_branch}"' in text
    assert "exact-head Quality already active/successful" in text
    assert 'ensure_quality "${branch}" "$(git rev-parse HEAD)"' in text


def test_ai_provider_discovery_requalifies_existing_unprotected_pr_without_churn():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "headRefName" in text
    assert "headRefOid" in text
    assert 'ensure_quality "${existing_branch}" "${existing_sha}"' in text
    assert (
        "identical machine evidence ratchet PR already open while master remains unprotected"
        in text
    )


def test_ai_provider_discovery_matches_machine_policy_quality_dispatch():
    import json

    policy = json.loads(
        Path("registry/ai-operations-policy.json").read_text(encoding="utf-8")
    )
    assert policy["guardrails"]["automation_pr_requires_explicit_quality_dispatch"] is True
    boundary = policy["evidence_binding"]
    assert boundary["machine_ratchet_may_create_pr"] is True
    assert boundary["machine_ratchet_direct_master_write"] is False

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "gh workflow run quality.yml" in text
    assert "HEAD:refs/heads/master" not in text
