import copy

from tools.codex_assets.knowledge_hub.security_change_review import (
    build_security_change_review,
)


BASE = "a" * 40
HEAD = "b" * 40


def _policy():
    return {
        "default_class": "ordinary",
        "rules": [
            {
                "path": "registry/ai-operations-policy.json",
                "review_class": "security-critical",
            },
            {
                "path_prefix": "docs/",
                "review_class": "governance-critical",
            },
        ],
    }


def _file(path="registry/ai-operations-policy.json"):
    return {
        "filename": path,
        "status": "modified",
        "additions": 4,
        "deletions": 1,
        "changes": 5,
        "blob_url": "https://github.example/blob",
        "raw_url": "https://github.example/raw",
        "sha": "c" * 40,
    }


def _review(
    *,
    login="reviewer",
    state="APPROVED",
    commit_id=HEAD,
    review_id=10,
    user_type="User",
):
    return {
        "id": review_id,
        "state": state,
        "commit_id": commit_id,
        "submitted_at": "2026-09-20T10:00:00Z",
        "user": {"login": login, "type": user_type},
    }


def _build(files=None, reviews=None, **overrides):
    args = {
        "repository": "example/knowledge-hub",
        "pr_number": 99,
        "base_sha": BASE,
        "head_sha": HEAD,
        "head_ref": "feature/security-change",
        "author_login": "author",
        "same_repository": True,
        "files": files if files is not None else [_file()],
        "reviews": reviews if reviews is not None else [],
        "review_risk_policy": _policy(),
    }
    args.update(overrides)
    return build_security_change_review(**args)


def test_security_change_requires_exact_head_human_approval():
    packet = _build()

    assert packet["status"] == "awaiting-human-review"
    assert packet["gate_pass"] is False
    assert packet["review_required"] is True
    assert packet["security_critical_file_count"] == 1
    assert packet["exact_head_approval_count"] == 0


def test_exact_head_human_approval_passes_security_change_gate():
    packet = _build(reviews=[_review()])

    assert packet["status"] == "pass"
    assert packet["gate_pass"] is True
    assert packet["review_reason"] == "exact-head-human-approval"
    assert packet["exact_head_approval_count"] == 1
    assert packet["exact_head_approvals"][0]["login"] == "reviewer"


def test_old_head_bot_and_self_approvals_do_not_pass():
    packet = _build(
        reviews=[
            _review(login="old", commit_id="d" * 40, review_id=1),
            _review(
                login="github-actions[bot]",
                user_type="Bot",
                review_id=2,
            ),
            _review(login="author", review_id=3),
        ]
    )

    assert packet["status"] == "awaiting-human-review"
    assert packet["exact_head_approval_count"] == 0


def test_latest_review_state_invalidates_earlier_approval():
    packet = _build(
        reviews=[
            _review(login="reviewer", state="APPROVED", review_id=1),
            _review(
                login="reviewer",
                state="CHANGES_REQUESTED",
                review_id=2,
            ),
        ]
    )

    assert packet["status"] == "awaiting-human-review"
    assert packet["exact_head_approval_count"] == 0


def test_no_security_critical_change_needs_no_human_review():
    packet = _build(files=[_file("docs/guide.md")])

    assert packet["status"] == "pass"
    assert packet["review_required"] is False
    assert packet["review_reason"] == "no-security-critical-change"


def test_same_repo_github_actions_ratchet_uses_dedicated_verifier_boundary():
    packet = _build(
        head_ref="automation/external-gap-abc123def456-123",
        author_login="github-actions[bot]",
        reviews=[],
    )

    assert packet["status"] == "pass"
    assert packet["autonomous_ratchet"] is True
    assert packet["review_required"] is False
    assert packet["review_reason"] == "dedicated-machine-ratchet-verifier"


def test_user_cannot_spoof_machine_ratchet_with_branch_prefix():
    packet = _build(
        head_ref="automation/external-gap-abc123def456-123",
        author_login="author",
        reviews=[],
    )

    assert packet["status"] == "awaiting-human-review"
    assert packet["autonomous_ratchet"] is False


def test_cross_repository_bot_pr_cannot_use_machine_ratchet_exemption():
    packet = _build(
        head_ref="automation/evidence-bind-abc123def456-123",
        author_login="github-actions[bot]",
        same_repository=False,
    )

    assert packet["status"] == "awaiting-human-review"
    assert packet["autonomous_ratchet"] is False


def test_security_change_packet_is_deterministic_for_same_inputs():
    first = _build(reviews=[_review()])
    second = _build(
        files=[copy.deepcopy(_file())],
        reviews=[copy.deepcopy(_review())],
    )

    assert first == second
    assert first["packet_fingerprint"].startswith("sha256:")
