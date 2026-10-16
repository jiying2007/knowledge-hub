"""Team MCP has one visibility rule for all tools and no write operations."""
import datetime as dt
import hashlib
import json

import pytest

from tools.codex_assets.knowledge_hub import team_mcp
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.protocol_conformance import MCPProtocolError


SHA = "a" * 40
NOW = dt.date.today()


def item(**overrides):
    row = {
        "id": "team-example", "title": "Test", "status": "reviewing",
        "visibility": "team-internal", "path": "projects/example/current/test.md",
        "summary_zh": "test summary",
    }
    row.update(overrides)
    return row


@pytest.mark.parametrize("changes", [
    {"status": "draft"}, {"status": "archived"}, {"status": "rejected"},
    {"status": "superseded"}, {"status": "personal"},
    {"visibility": "personal-local"}, {"visibility": "other"},
    {"searchable": False}, {"acl": ["alice"]},
    {"path": "projects/example/archive/test.md"},
    {"path": "notes/inbox/test.md"}, {"path": "notes/personal/alice/test.md"},
    {"path": "tools/config.md"}, {"path": "projects/../secret.md"},
    {"path": "/etc/secret.md"}, {"path": "projects/.private/test.md"},
    {"valid_from": "not-a-date"}, {"valid_to": "1999-01-01"},
    {"valid_from": "2025-02-30"}, {"valid_from": "2099-01-01"},
])
def test_team_visibility_negative(changes):
    assert team_mcp.team_publishable(item(**changes), NOW) is False


@pytest.mark.parametrize("status", ["active", "reviewing"])
def test_team_visibility_positive(status):
    assert team_mcp.team_publishable(item(status=status), NOW) is True


def test_team_get_requires_registered_id_bounded_utf8_and_exact_content(tmp_path):
    root = tmp_path
    (root / "registry").mkdir()
    doc = root / "projects/example/current/test.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("你好你好\n" * 200, encoding="utf-8")
    rows = [item(), item(id="hidden", status="draft", path="projects/example/current/hidden.md")]
    (root / "registry/items.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )
    first = team_mcp.team_get(root, "team-example", SHA, max_bytes=13)
    assert first["content"].encode("utf-8")
    assert len(first["content"].encode("utf-8")) <= 13
    assert first["next_offset"] > 0
    assert first["review_required"] is True
    second = team_mcp.team_get(root, "team-example", SHA, offset=first["next_offset"],
                               expected_sha256=first["content_sha256"], max_bytes=13)
    assert second["content"]
    with pytest.raises(KnowledgeHubError, match="not found"):
        team_mcp.team_get(root, "hidden", SHA)
    with pytest.raises(KnowledgeHubError):
        team_mcp.team_get(root, "team-example", SHA, expected_sha256="b" * 64)
    with pytest.raises(KnowledgeHubError):
        team_mcp.team_get(root, "../etc/passwd", SHA)
    with pytest.raises(KnowledgeHubError):
        team_mcp.team_get(root, "team-example", SHA, max_bytes=MAX_UNBOUNDED)
    assert first["content_sha256"] == hashlib.sha256(doc.read_bytes()).hexdigest()


MAX_UNBOUNDED = team_mcp.MAX_PAGE_BYTES + 1


def _request(method, params=None):
    from tools.codex_assets.knowledge_hub.protocol_conformance import (
        MCP_PROTOCOL_META_KEY, MCP_CLIENT_CAPABILITIES_META_KEY,
    )
    value = dict(params or {})
    value["_meta"] = {
        MCP_PROTOCOL_META_KEY: "2026-07-28",
        MCP_CLIENT_CAPABILITIES_META_KEY: {},
    }
    return {"jsonrpc": "2.0", "id": 2, "method": method, "params": value}


def test_team_advertises_exact_tools_and_only_health_resource(tmp_path):
    tools = team_mcp.handle_team_mcp(tmp_path, _request("tools/list"), SHA)["result"]["tools"]
    assert {t["name"] for t in tools} == {"knowledge_search", "knowledge_get", "knowledge_context"}
    resources = team_mcp.handle_team_mcp(tmp_path, _request("resources/list"), SHA)["result"]["resources"]
    assert [r["uri"] for r in resources] == ["knowledge://health"]
    with pytest.raises(MCPProtocolError):
        team_mcp.handle_team_mcp(tmp_path, _request("resources/read", {"uri": "knowledge://agents"}), SHA)
    with pytest.raises(MCPProtocolError):
        team_mcp.handle_team_mcp(tmp_path, _request("tools/call", {
            "name": "knowledge_action_check", "arguments": {"candidate": "x"}}), SHA)


def test_team_does_not_allow_time_travel_or_unadvertised_arguments(tmp_path):
    for params in [
        {"query": "test", "as_of": "2000-01-01"},
        {"query": "test", "limit": True},
        {"query": "test", "limit": 11},
        {"query": ""},
    ]:
        with pytest.raises(KnowledgeHubError):
            team_mcp.handle_team_mcp(tmp_path, _request("tools/call", {
                "name": "knowledge_search", "arguments": params}), SHA)
    with pytest.raises(KnowledgeHubError):
        team_mcp.handle_team_mcp(tmp_path, _request("tools/call", {
            "name": "knowledge_get", "arguments": {"item_id": "x", "path": "/secret"}}), SHA)


def test_team_search_filters_before_retrieval_ranking(tmp_path, monkeypatch):
    rows = [item(), item(id="secret", status="draft"),
            item(id="archive", status="reviewing", path="projects/x/archive/foo.md")]
    def fake_items(root):
        return rows
    def fake_search(root, query, principal, *, limit, candidate_filter):
        assert [r["id"] for r in rows if candidate_filter(r)] == ["team-example"]
        return {"results": [{"id": "team-example", "score": 0.8}],
                "status": "pass", "retrieval_coverage": {"complete": True}}
    monkeypatch.setattr(team_mcp, "registry_items", fake_items)
    monkeypatch.setattr(team_mcp, "retrieve_v4", fake_search)
    found = team_mcp.team_search(tmp_path, "foo", SHA)
    assert len(found["results"]) == 1
    assert found["results"][0]["authority"] == "provisional"


def test_no_hidden_item_content_is_returned_through_context(tmp_path, monkeypatch):
    rows = [item(), item(id="draft", status="draft")]
    monkeypatch.setattr(team_mcp, "registry_items", lambda root: rows)
    monkeypatch.setattr(team_mcp, "retrieve_v4", lambda *a, **kw: {
        "results": [{"id": "draft", "score": 1}],
        "status": "pass", "retrieval_coverage": {"complete": True},
    })
    with pytest.raises(KnowledgeHubError, match="eligibility"):
        team_mcp.team_context(tmp_path, "secret", SHA)


def test_team_http_rejects_missing_or_weak_token_file(tmp_path):
    from tools.codex_assets.knowledge_hub.mcp_http_server import serve
    with pytest.raises(KnowledgeHubError, match="token file"):
        serve(tmp_path, team=True, serving_sha=SHA)
    token = tmp_path / "token"
    token.write_text("short", encoding="utf-8")
    token.chmod(0o600)
    with pytest.raises(KnowledgeHubError, match="32-512"):
        serve(tmp_path, team=True, token_file=str(token), serving_sha=SHA)
    token.write_text("x" * 40, encoding="utf-8")
    token.chmod(0o644)
    with pytest.raises(KnowledgeHubError, match="private regular"):
        serve(tmp_path, team=True, token_file=str(token), serving_sha=SHA)
