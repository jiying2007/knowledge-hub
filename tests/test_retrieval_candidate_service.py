"""Shared governed retrieval-eligibility contract regressions."""

import datetime as dt

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub import retrieval_v4 as rv4
from tools.codex_assets.knowledge_hub import runtime_v3 as rv3
from tools.codex_assets.knowledge_hub.retrieval_eligibility import (
    scope_matches, serviceable_item,
)

TODAY = dt.date(2026, 9, 25)


@pytest.mark.parametrize(
    "item, expected",
    [
        ({"path": "projects/a/current/x.md", "status": "active"}, True),
        ({"path": "projects/a/current/x.md", "status": "reviewing"}, True),
        ({"path": "projects/a/current/x.md", "status": "draft"}, True),
        ({"path": "projects/a/current/x.md", "status": "archived"}, False),
        ({"path": "projects/a/current/x.md", "status": "active", "searchable": False}, False),
        ({"path": "registry/schema.md", "status": "active"}, False),
        ({"path": "registry/schema.md", "status": "active", "searchable": True}, True),
        ({"path": "notes/personal/x.md", "status": "active", "visibility": "personal-local"}, False),
        ({"path": "projects/a/current/x.md", "status": "active", "valid_from": "2026-09-26"}, False),
        ({"path": "projects/a/current/x.md", "status": "active", "valid_to": "2026-09-24"}, False),
    ],
)
def test_serviceable_contract(item, expected):
    assert serviceable_item(item, TODAY) is expected
    assert rv4._temporal_eligible(item, TODAY) is expected
    assert rv3._eligible(item, TODAY, ()) is expected


def test_invalid_temporal_range_fails_every_surface():
    item = {
        "path": "projects/a/current/x.md", "status": "active",
        "valid_from": "2026-09-26", "valid_to": "2026-09-24",
    }
    with pytest.raises(KnowledgeHubError, match="valid_from"):
        serviceable_item(item, TODAY)
    with pytest.raises(KnowledgeHubError, match="valid_from"):
        rv4._temporal_eligible(item, TODAY)
    with pytest.raises(KnowledgeHubError, match="valid_from"):
        rv3._eligible(item, TODAY, ())


@pytest.mark.parametrize(
    "scopes, expected",
    [
        ((), True),
        (("projects",), True),
        (("projects/a",), True),
        (("projects/a/current",), True),
        (("projects/b",), False),
        (("", "projects/b"), False),
    ],
)
def test_scope_contract(scopes, expected):
    item = {"domain": "projects/a", "path": "projects/a/current/x.md"}
    assert scope_matches(item, scopes) is expected


def test_scope_never_overrides_nonsearchable_lifecycle():
    item = {
        "domain": "projects/a", "path": "projects/a/current/x.md",
        "status": "active", "searchable": False,
    }
    assert scope_matches(item, ("projects/a",)) is True
    assert rv3._eligible(item, TODAY, ("projects/a",)) is False


def test_acl_is_intentionally_not_part_of_shared_pre_acl_contract():
    item = {
        "domain": "projects/a", "path": "projects/a/current/x.md",
        "status": "active", "acl": ["bob"],
    }
    assert serviceable_item(item, TODAY) is True
    assert scope_matches(item, ("projects/a",)) is True


def test_global_fts_rebuild_is_not_called_from_v4_request_path(monkeypatch, tmp_path):
    # Regression for the rejected initial #117 approach: candidate discovery
    # must not rebuild a global body index after principal ACL filtering.
    class Forbidden:
        def __init__(self, *args, **kwargs):
            raise AssertionError("global FTS index must not be opened by v4")
    import tools.codex_assets.knowledge_hub.search_index as search_index
    monkeypatch.setattr(search_index, "SearchIndex", Forbidden)
    monkeypatch.setattr(rv4, "registry_items", lambda root: [])
    monkeypatch.setattr(rv4, "agent_profile", lambda root, agent: {"knowledge_scopes": []})
    result = rv4.retrieve_v4(
        tmp_path, "uart", {"principal_id": "alice", "groups": [], "organization_id": "eng"},
        cache_enabled=False, as_of="2026-09-25",
    )
    assert result["results"] == []
