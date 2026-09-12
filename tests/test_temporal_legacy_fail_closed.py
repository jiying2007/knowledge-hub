import datetime as dt

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.model import frontmatter_mirror, validate_item
from tools.codex_assets.knowledge_hub.runtime_p5_security import repository_posture
from tools.codex_assets.knowledge_hub.runtime_v3 import _eligible, _freshness


def _item():
    return {
        "id": "temporal-contract-test",
        "title": "Temporal contract test",
        "kind": "decision",
        "domain": "projects/test",
        "path": "projects/test/temporal.md",
        "scope": "team-general",
        "visibility": "team-internal",
        "status": "draft",
        "owner": "test-owner",
        "source": {},
        "review_after": "2026-12-31",
        "validation_refs": ["test:temporal"],
        "review_status": "draft",
        "created_at": "2026-01-01",
        "updated_at": "2026-09-01",
        "promotion": "none",
        "tags": ["temporal"],
    }


def test_canonical_model_rejects_invalid_temporal_dates_and_range():
    invalid = _item()
    invalid["valid_from"] = "not-a-date"
    invalid["valid_to"] = "2026-12-31"
    errors = validate_item(invalid)
    assert any("valid_from must use YYYY-MM-DD" in error for error in errors)

    reversed_range = _item()
    reversed_range["valid_from"] = "2027-01-01"
    reversed_range["valid_to"] = "2026-12-31"
    errors = validate_item(reversed_range)
    assert "valid_from must not exceed valid_to" in errors


def test_temporal_fields_are_registry_owned_frontmatter():
    item = _item()
    item.update(
        {
            "valid_from": "2026-09-01",
            "valid_to": "2026-12-31",
            "superseded_by": "next-decision",
        }
    )
    mirror = frontmatter_mirror(item)
    assert mirror["valid_from"] == "2026-09-01"
    assert mirror["valid_to"] == "2026-12-31"
    assert mirror["superseded_by"] == "next-decision"


def test_legacy_runtime_v3_temporal_parsing_is_fail_closed():
    item = {
        "status": "active",
        "visibility": "team-internal",
        "domain": "projects/test",
        "path": "projects/test/current.md",
        "valid_from": "bad-date",
    }
    with pytest.raises(KnowledgeHubError):
        _eligible(item, dt.date(2026, 9, 12), ())

    with pytest.raises(KnowledgeHubError):
        _freshness({"updated_at": "bad-date"}, dt.date(2026, 9, 12))


def test_repository_posture_enforces_full_declared_admin_target():
    target = {
        "private_required": True,
        "protected_default_branch_required": True,
        "required_status_checks": ["quality"],
        "block_force_push": True,
        "block_branch_deletion": True,
        "require_pull_request": True,
        "require_conversation_resolution": True,
    }
    blocked = repository_posture(
        {
            "private": False,
            "default_branch_protected": False,
            "required_status_checks": [],
            "force_push_blocked": False,
            "branch_deletion_blocked": False,
            "pull_request_required": False,
            "conversation_resolution_required": False,
        },
        target,
    )
    assert blocked["status"] == "blocked"
    assert set(blocked["failures"]) == {
        "repository-must-be-private",
        "default-branch-protection-required",
        "required-status-checks-missing",
        "force-push-must-be-blocked",
        "branch-deletion-must-be-blocked",
        "pull-request-must-be-required",
        "conversation-resolution-must-be-required",
    }

    passed = repository_posture(
        {
            "private": True,
            "default_branch_protected": True,
            "required_status_checks": ["quality"],
            "force_push_blocked": True,
            "branch_deletion_blocked": True,
            "pull_request_required": True,
            "conversation_resolution_required": True,
        },
        target,
    )
    assert passed["status"] == "pass"
    assert passed["failures"] == []
