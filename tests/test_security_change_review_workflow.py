from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/security-critical-change-review.yml")


def _workflow():
    payload = yaml.load(
        WORKFLOW.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    assert isinstance(payload, dict)
    return payload


def test_security_change_review_runs_from_trusted_pr_events_only():
    payload = _workflow()
    assert set(payload["on"]) == {
        "pull_request_target",
        "pull_request_review",
        "issue_comment",
    }
    assert payload["on"]["pull_request_target"]["types"] == [
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
    ]
    assert payload["on"]["pull_request_review"]["types"] == [
        "submitted",
        "edited",
        "dismissed",
    ]
    assert payload["on"]["issue_comment"]["types"] == [
        "created",
        "edited",
        "deleted",
    ]
    assert "workflow_dispatch" not in payload["on"]
    assert "pull_request" not in payload["on"]


def test_security_change_review_is_read_only_and_never_executes_pr_code():
    payload = _workflow()
    assert payload["permissions"] == {
        "contents": "read",
        "pull-requests": "read",
        "issues": "read",
    }
    job = payload["jobs"]["review"]
    steps = job["steps"]
    checkout = next(
        step
        for step in steps
        if str(step.get("uses", "")).startswith("actions/checkout@")
    )
    assert checkout["with"]["ref"] == "${{ steps.resolve.outputs.base_sha }}"
    assert checkout["with"]["persist-credentials"] == "false"

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Checkout exact trusted base" in text
    assert "ref: ${{ env.HEAD_SHA }}" not in text
    assert "git checkout" not in text
    assert "git push" not in text
    assert "gh pr create" not in text
    assert "gh pr merge" not in text
    assert "gh issue" not in text


def test_security_change_review_binds_workflow_to_exact_pr_base():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Resolve exact PR identity" in text
    assert "WORKFLOW_SHA: ${{ github.workflow_sha }}" in text
    assert 'if [[ "${WORKFLOW_SHA}" != "${BASE_SHA}" ]]' in text
    assert "security review workflow is not bound to the exact PR base" in text


def test_security_change_review_fetches_exact_files_reviews_and_comments():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'pulls/${PR_NUMBER}/files?per_page=100' in text
    assert 'pulls/${PR_NUMBER}/reviews?per_page=100' in text
    assert 'issues/${PR_NUMBER}/comments?per_page=100' in text
    assert "comments=comments" in text
    assert "build_security_change_review" in text
    assert "security-change-review-v1" in text
    assert "SECURITY-CHANGE-APPROVE" in text


def test_security_change_review_uses_runtime_dependency_surface():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "requirements-runtime.lock" in text
    assert "requirements-dev.lock" not in text


def test_security_change_review_retains_bounded_packet():
    payload = _workflow()
    upload = next(
        step
        for step in payload["jobs"]["review"]["steps"]
        if step.get("name") == "Upload bounded security review evidence"
    )
    assert upload["if"] == "always()"
    assert upload["with"]["retention-days"] == "90"
    assert (
        upload["with"]["path"]
        == ".cache/knowledge-hub/security-change-review/packet.json"
    )


def test_security_change_review_uses_compact_jsonl_from_github_api():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--jq '.[] | @json'" in text
    assert text.count("--jq '.[] | @json'") == 3


def test_security_change_review_issue_comment_is_pr_only():
    payload = _workflow()
    condition = payload["jobs"]["review"]["if"]
    assert "github.event_name != 'issue_comment'" in condition
    assert "github.event.issue.pull_request != null" in condition


def test_security_change_review_does_not_write_approval_comment():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "gh issue comment" not in text
    assert "gh pr review" not in text


def test_security_change_review_resolves_direct_child_from_github_commit():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'commits/${head_sha}' in text
    assert "head-commit.json" in text
    assert "head_is_direct_child_of_base" in text
    assert (
        'os.environ["HEAD_IS_DIRECT_CHILD_OF_BASE"] == "true"'
        in text
    )
