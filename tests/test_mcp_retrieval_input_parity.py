from tools.codex_assets.knowledge_hub import runtime_v3 as rv3


def _tool(name):
    return next(row for row in rv3.mcp_tools() if row["name"] == name)


def test_mcp_search_and_context_expose_as_of():
    for name in ("knowledge_search", "knowledge_context"):
        props = _tool(name)["inputSchema"]["properties"]
        assert props["as_of"]["pattern"] == r"^\d{4}-\d{2}-\d{2}$"


def test_mcp_evidence_pack_exposes_dispatch_supported_inputs():
    props = _tool("knowledge_evidence_pack")["inputSchema"]["properties"]
    assert set(props) == {"query", "limit", "scope_refs", "as_of"}
    assert props["limit"]["maximum"] == 100


def test_context_api_forwards_evidence_as_of(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(rv3, "require_capability", lambda *args: None)
    monkeypatch.setattr(rv3, "agent_profile", lambda *args: {"knowledge_scopes": []})

    def build(root, query, **kwargs):
        captured.update(kwargs)
        return {"schema_version": "x", "must": [], "context": []}

    monkeypatch.setattr(rv3, "build_evidence_pack", build)
    rv3.api_dispatch(
        tmp_path,
        "evidence-pack",
        {"query": "q", "as_of": "2026-09-25"},
        agent_id="knowledge-reader",
    )
    assert captured["as_of"] == "2026-09-25"
