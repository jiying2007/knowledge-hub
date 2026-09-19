from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/hosting-posture-reconcile.yml")


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_hosting_reconcile_is_low_frequency_and_pr_close_only_for_gc():
    payload = _workflow()
    triggers = payload["on"]
    assert set(triggers) == {"schedule", "workflow_dispatch", "pull_request"}
    assert triggers["pull_request"]["types"] == ["closed"]
    assert "push" not in triggers
    assert "workflow_run" not in triggers
    assert "pull_request_target" not in triggers

    reconcile = payload["jobs"]["reconcile"]
    condition = reconcile["if"]
    assert "github.event_name == 'schedule'" in condition
    assert "github.event_name == 'workflow_dispatch'" in condition
    assert "github.ref == 'refs/heads/master'" in condition
    assert reconcile["env"]["SOURCE_REVISION"] == "${{ github.sha }}"


def test_hosting_reconcile_revalidates_current_master_aggregate_quality():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Verify source has successful aggregate Quality" in text
    assert "actions/workflows/quality.yml/runs?branch=master&status=success" in text
    assert '"head_sha": os.environ["SOURCE_REVISION"]' in text
    assert '"head_branch": "master"' in text
    assert '"event": "push"' in text
    assert '"conclusion": "success"' in text
    assert '".github/workflows/quality.yml"' in text


def test_hosting_reconcile_creates_governed_pr_not_direct_master_write():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "persist-credentials: false" in text
    assert "repository_private_ratchet_cli" in text
    assert "automation/hosting-private-" in text
    assert "gh pr create" in text
    assert 'HEAD:refs/heads/${branch}' in text
    assert "HEAD:refs/heads/master" not in text
    assert "gh pr merge" not in text
    assert "synthetic" not in text.lower()


def test_hosting_reconcile_permissions_are_job_scoped():
    payload = _workflow()
    assert payload["permissions"] == {"contents": "read"}
    reconcile = payload["jobs"]["reconcile"]
    assert reconcile["permissions"] == {
        "contents": "write",
        "actions": "write",
        "pull-requests": "write",
        "issues": "write",
    }
    gc = payload["jobs"]["automation-branch-gc"]
    assert gc["permissions"] == {"contents": "write"}


def test_hosting_reconcile_deduplicates_open_ratchet_pr_before_push():
    text = WORKFLOW.read_text(encoding="utf-8")
    existing_index = text.index(
        "existing governed ratchet PR already owns this canonical transition"
    )
    push_index = text.index('git push "${remote}" "HEAD:refs/heads/${branch}"')
    assert existing_index < push_index
    assert 'branch="automation/hosting-private-${short}-${GITHUB_RUN_ID}"' in text


def test_hosting_reconcile_cleans_unowned_branch_when_pr_creation_fails():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "deleting the unowned automation branch" in text
    assert 'git push "${remote}" --delete "${branch}" || true' in text


def test_hosting_reconcile_retires_closed_automation_pr_branches_only():
    payload = _workflow()
    gc = payload["jobs"]["automation-branch-gc"]
    condition = gc["if"]
    assert "github.event_name == 'pull_request'" in condition
    assert "github.event.pull_request.head.repo.full_name == github.repository" in condition
    assert "startsWith(github.event.pull_request.head.ref, 'automation/')" in condition
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "^automation/[A-Za-z0-9._/-]+$" in text
    assert "--method DELETE" in text


def test_hosting_reconcile_captures_fresh_posture_and_dispatches_one_signed_refresh():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "remote_branch_inventory_cli" in text
    assert "hosting_posture_cli" in text
    assert "default_branch_protected" in text
    assert "Request one fresh Signed verification after protection recovery" in text
    assert "steps.decide.outputs.protected == 'true'" in text
    assert "steps.decide.outputs.canonical_private_closed == 'true'" in text
    assert "signed-quality-attestation.yml/runs?branch=master&per_page=20" in text
    assert 'awk -v sha="${SOURCE_REVISION}"' in text
    assert "gh workflow run signed-quality-attestation.yml" in text
    assert "--ref master" in text


def test_hosting_reconcile_uses_runtime_not_dev_dependency_surface():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "requirements-runtime.lock" in text
    assert "requirements-dev.lock" not in text


def test_hosting_reconcile_reuses_existing_deterministic_branch_before_push():
    text = WORKFLOW.read_text(encoding="utf-8")
    lookup = 'gh api "repos/${GITHUB_REPOSITORY}/branches/${branch}"'
    push = 'git push "${remote}" "HEAD:refs/heads/${branch}"'
    assert lookup in text
    assert "reusing the existing deterministic candidate branch" in text
    assert text.index(lookup) < text.index(push)
