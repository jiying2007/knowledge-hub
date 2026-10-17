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
    assert all(t["annotations"]["readOnlyHint"] is True for t in tools)
    assert all(t["annotations"]["destructiveHint"] is False for t in tools)
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
    (tmp_path / ".serving-sha").write_text(SHA + "\n", encoding="utf-8")
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


def test_team_http_requires_bearer_and_keeps_resource_scope(tmp_path):
    """Live loopback HTTP request exercises the auth boundary, not a mocked router."""
    import http.client
    import threading
    from tools.codex_assets.knowledge_hub.mcp_http_server import (
        _BoundedTeamServer, _Handler,
    )

    server = _BoundedTeamServer(("127.0.0.1", 0), _Handler, max_connections=4)
    server.knowledge_root = tmp_path
    server.knowledge_agent_id = "knowledge-reader"
    server.knowledge_limiter = threading.BoundedSemaphore(2)
    server.knowledge_team_token = "t" * 40
    server.knowledge_serving_sha = SHA
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(token=None, origin=None):
        body = json.dumps(_request("tools/list"), separators=(",", ":"))
        headers = {
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2026-07-28",
            "Mcp-Method": "tools/list",
        }
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        if origin is not None:
            headers["Origin"] = origin
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            conn.request("POST", "/mcp", body=body.encode("utf-8"), headers=headers)
            response = conn.getresponse()
            return response.status, json.loads(response.read())
        finally:
            conn.close()

    try:
        assert request()[0] == 401
        assert request("wrong")[0] == 401
        assert request("t" * 40, origin="https://evil.example")[0] == 403
        status, payload = request("t" * 40)
        assert status == 200
        names = {row["name"] for row in payload["result"]["tools"]}
        assert names == {"knowledge_search", "knowledge_get", "knowledge_context"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_only_evidence_verified_active_is_advertised_as_authority():
    from tools.codex_assets.knowledge_hub.team_mcp import _kind
    good = item(status="active", manual_validation_pending=False,
                content_review_status="accepted", evidence_validation_status="verified")
    assert _kind(good) == "verified"
    for changes in (
        {"manual_validation_pending": True},
        {"content_review_status": "pending"},
        {"evidence_validation_status": "pending"},
        {"status": "reviewing"},
    ):
        assert _kind(dict(good, **changes)) == "provisional"


def test_team_listener_sets_timeout_before_request_headers():
    import socket
    from tools.codex_assets.knowledge_hub.mcp_http_server import (
        _BoundedTeamServer, _Handler, REQUEST_TIMEOUT_SECONDS,
    )
    server = _BoundedTeamServer(("127.0.0.1", 0), _Handler, max_connections=2)
    try:
        with socket.create_connection(("127.0.0.1", server.server_port), timeout=3):
            conn, addr = server.get_request()
            try:
                assert addr
                assert conn.gettimeout() == REQUEST_TIMEOUT_SECONDS
            finally:
                conn.close()
    finally:
        server.server_close()


def test_real_repository_http_search_get_context_smoke():
    """Smoke the actual governed corpus through HTTP; not only mocked dispatch."""
    import pathlib
    import threading
    from tools.codex_assets.knowledge_hub.mcp_http_server import _BoundedTeamServer, _Handler
    from tools.codex_assets.knowledge_hub.team_smoke import smoke

    root = pathlib.Path(__file__).resolve().parents[1]
    server = _BoundedTeamServer(("127.0.0.1", 0), _Handler, max_connections=6)
    server.knowledge_root = root
    server.knowledge_agent_id = "knowledge-reader"
    server.knowledge_limiter = threading.BoundedSemaphore(3)
    server.knowledge_team_token = "t" * 40
    server.knowledge_serving_sha = SHA
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        result = smoke(
            "http://127.0.0.1:{}/mcp".format(server.server_port),
            "t" * 40, SHA, root,
        )
        assert result["status"] == "pass"
        assert result["search_results"] >= 1
        assert result["probe_id"]
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def test_current_context_requires_exact_full_body_review_proof(tmp_path, monkeypatch):
    active = item(
        status="active", review_after="2099-01-01",
        content_review_status="accepted", evidence_validation_status="verified",
        manual_validation_pending=False,
    )
    raw = b"# current knowledge\n"
    source = tmp_path / active["path"]
    source.parent.mkdir(parents=True)
    source.write_bytes(raw)
    monkeypatch.setattr(team_mcp, "registry_items", lambda root: [active])
    monkeypatch.setattr(team_mcp, "retrieve_v4", lambda *a, **kw: {
        "results": [{"id": "team-example", "score": 1}],
        "status": "pass", "retrieval_coverage": {"complete": True},
    })
    unbound_search = team_mcp.team_search(tmp_path, "knowledge", SHA)
    assert unbound_search["results"][0]["review_required"] is True
    assert unbound_search["results"][0]["review_binding_state"] == "unbound"
    unbound_get = team_mcp.team_get(tmp_path, "team-example", SHA)
    assert unbound_get["authority"] == "verified"  # historical status is retained
    assert unbound_get["review_binding_state"] == "unbound"
    assert unbound_get["review_required"] is True
    unbound_context = team_mcp.team_context(tmp_path, "knowledge", SHA)
    assert unbound_context["current"] == []
    assert len(unbound_context["provisional"]) == 1

    # A registry claim alone is never enough for search: it has not read bytes.
    active["human_review_content_sha256"] = hashlib.sha256(raw).hexdigest()
    declared_search = team_mcp.team_search(tmp_path, "knowledge", SHA)
    assert declared_search["results"][0]["review_binding_state"] == "declared-unverified"
    assert declared_search["results"][0]["review_required"] is True
    matched_get = team_mcp.team_get(tmp_path, "team-example", SHA)
    assert matched_get["review_binding_state"] == "current-body-bound"
    assert matched_get["review_required"] is False
    current_context = team_mcp.team_context(tmp_path, "knowledge", SHA)
    assert len(current_context["current"]) == 1
    assert current_context["provisional"] == []
    assert current_context["current"][0]["review_required"] is False

    # Any body change invalidates the old current-body approval, even if
    # the status, owner and review_after metadata still appear unchanged.
    source.write_bytes(raw + b"revised")
    drifted_get = team_mcp.team_get(tmp_path, "team-example", SHA)
    assert drifted_get["review_binding_state"] == "content-drift"
    assert drifted_get["review_required"] is True
    drifted_context = team_mcp.team_context(tmp_path, "knowledge", SHA)
    assert drifted_context["current"] == []
    assert drifted_context["provisional"][0]["review_binding_state"] == "content-drift"


def test_overdue_active_remains_historical_authority_but_needs_current_review():
    import datetime
    from tools.codex_assets.knowledge_hub.team_mcp import _kind, _review_overdue
    today = datetime.date(2026, 10, 17)
    active = item(status="active", review_after="2026-09-01",
                  content_review_status="accepted", evidence_validation_status="verified",
                  manual_validation_pending=False)
    assert _kind(active) == "verified"
    assert _review_overdue(active, today) is True
    assert _review_overdue(dict(active, review_after="2026-10-17"), today) is False
    assert _review_overdue(dict(active, review_after="invalid"), today) is True


def test_overdue_active_routes_to_provisional_context(tmp_path, monkeypatch):
    active = item(status="active", review_after="2020-01-01",
                  content_review_status="accepted", evidence_validation_status="verified",
                  manual_validation_pending=False)
    monkeypatch.setattr(team_mcp, "registry_items", lambda root: [active])
    monkeypatch.setattr(team_mcp, "retrieve_v4", lambda *a, **kw: {
        "results": [{"id": "team-example", "score": 1}],
        "status": "pass", "retrieval_coverage": {"complete": True},
    })
    monkeypatch.setattr(team_mcp, "team_get", lambda *a, **kw: {
        "content": "# active knowledge", "content_sha256": "a" * 64,
    })
    value = team_mcp.team_context(tmp_path, "term", SHA, limit=2)
    assert value["current"] == []
    assert len(value["provisional"]) == 1
    result = value["provisional"][0]
    assert result["status"] == "active"
    assert result["authority"] == "verified"
    assert result["review_overdue"] is True
    assert result["review_required"] is True
