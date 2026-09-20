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
    assert "workflow_dispatch" not in payload["on"]
    assert "pull_request" not in payload["on"]


def test_security_change_review_is_read_only_and_never_executes_pr_code():
    payload = _workflow()
    assert payload["permissions"] == {
        "contents": "read",
        "pull-requests": "read",
    }
    job = payload["jobs"]["review"]
    steps = job["steps"]
    checkout = next(
        step
        for step in steps
        if str(step.get("uses", "")).startswith("actions/checkout@")
    )
    assert checkout["with"]["ref"] == "${{ env.BASE_SHA }}"
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
    assert "WORKFLOW_SHA: ${{ github.workflow_sha }}" in text
    assert 'if [[ "${WORKFLOW_SHA}" != "${BASE_SHA}" ]]' in text
    assert "security review workflow is not bound to the exact PR base" in text


def test_security_change_review_fetches_exact_files_and_reviews():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'pulls/${PR_NUMBER}/files?per_page=100' in text
    assert 'pulls/${PR_NUMBER}/reviews?per_page=100' in text
    assert "build_security_change_review" in text
    assert "security-change-review-v1" in text
    assert "security-critical exact-head human approval required" in text


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
