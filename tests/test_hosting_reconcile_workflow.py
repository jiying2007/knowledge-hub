from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/hosting-posture-reconcile.yml")


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_hosting_reconcile_only_runs_from_trusted_master_or_schedule():
    payload = _workflow()
    triggers = payload["on"]
    assert set(triggers) == {"push", "schedule", "workflow_dispatch"}
    assert triggers["push"]["branches"] == ["master"]
    assert "pull_request" not in triggers
    assert "pull_request_target" not in triggers


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


def test_hosting_reconcile_permissions_are_bounded_to_required_control_plane():
    payload = _workflow()
    assert payload["permissions"] == {
        "contents": "write",
        "pull-requests": "write",
        "issues": "write",
    }


def test_hosting_reconcile_deduplicates_open_ratchet_pr_before_push():
    text = WORKFLOW.read_text(encoding="utf-8")
    existing_index = text.index("existing governed ratchet PR already owns this canonical transition")
    push_index = text.index('git push "${remote}" "HEAD:refs/heads/${branch}"')
    assert existing_index < push_index
    assert 'branch="automation/hosting-private-${short}-${GITHUB_RUN_ID}"' in text
