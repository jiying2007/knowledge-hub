import shutil

import pytest

from tools.codex_assets.knowledge_hub import runtime_v3 as rv3
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root


def _root(tmp_path):
    source = repository_root() / rv3.CONFIG_PATH
    target = tmp_path / rv3.CONFIG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    items = tmp_path / "registry/items.jsonl"
    items.parent.mkdir(parents=True, exist_ok=True)
    items.write_text("", encoding="utf-8")
    return tmp_path


def test_local_write_flag_does_not_bypass_agent_capability(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(KnowledgeHubError, match="not permitted"):
        rv3.api_dispatch(
            root,
            "feedback",
            {"query": "q", "outcome": "accepted"},
            agent_id="knowledge-reader",
            enable_local_write=True,
        )


def test_mcp_unknown_or_write_like_tools_fail_closed(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(KnowledgeHubError, match="unsupported MCP tool"):
        rv3.handle_mcp_request(
            root,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "knowledge_feedback",
                    "arguments": {"query": "q", "outcome": "accepted"},
                },
            },
        )

    with pytest.raises(KnowledgeHubError, match="unsupported MCP resource"):
        rv3.handle_mcp_request(
            root,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/read",
                "params": {"uri": "knowledge://canonical/write"},
            },
        )


def test_mcp_protocol_and_notifications_fail_closed(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(KnowledgeHubError, match="JSON-RPC 2.0"):
        rv3.handle_mcp_request(root, {"jsonrpc": "1.0", "id": 1, "method": "ping"})

    assert (
        rv3.handle_mcp_request(
            root,
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
        )
        is None
    )


def test_semantic_corpus_budget_fails_instead_of_truncating(tmp_path, monkeypatch):
    root = _root(tmp_path)
    rows = [
        {
            "id": "item-{}".format(index),
            "title": "row {}".format(index),
            "kind": "project-current",
            "domain": "projects/demo",
            "path": "projects/demo/current/{}.md".format(index),
            "visibility": "team-internal",
            "status": "active",
            "updated_at": "2026-09-01",
        }
        for index in range(rv3.MAX_SEMANTIC_ITEMS + 1)
    ]
    monkeypatch.setattr(rv3, "registry_items", lambda _root: rows)

    with pytest.raises(KnowledgeHubError, match="semantic candidate corpus exceeds"):
        rv3.hybrid_search(root, "uart", as_of="2026-09-11")


def test_context_graph_hop_budget_is_bounded(tmp_path):
    with pytest.raises(KnowledgeHubError, match="graph hops must be between"):
        rv3.context_graph(_root(tmp_path), ["active-fact"], hops=rv3.MAX_GRAPH_HOPS + 1)


def test_connector_envelope_rejects_unknown_source_and_invalid_digest(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(KnowledgeHubError, match="unknown connector"):
        rv3.connector_envelope(root, "unknown", "object-1")

    with pytest.raises(KnowledgeHubError, match="lowercase SHA256"):
        rv3.connector_envelope(
            root,
            "github",
            "object-1",
            content_sha256="NOT-A-SHA",
        )


def test_memory_and_feedback_enums_are_closed(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(KnowledgeHubError, match="invalid memory level"):
        rv3.memory_candidate("embedded-expert", "forever", "summary", ["item:a"])

    with pytest.raises(KnowledgeHubError, match="invalid feedback outcome"):
        rv3.record_feedback(
            root,
            "knowledge-steward",
            "query",
            "auto-promote",
        )


def test_a2a_safe_delegation_is_preflight_only(tmp_path):
    result = rv3.a2a_preflight(
        _root(tmp_path),
        "manager-agent",
        "embedded-expert",
        "inspect UART evidence",
        ["knowledge.search", "knowledge.context"],
    )

    assert result["status"] == "pass"
    assert result["unsupported_capabilities"] == []
    assert result["high_risk_capabilities"] == []
    assert result["delegation_executes_task"] is False
    assert result["human_review_required"] is False


def test_context_compiler_applies_same_agent_scopes_to_all_retrieval_lanes(
    tmp_path, monkeypatch
):
    root = _root(tmp_path)
    observed = {}

    def fake_hybrid(*args, **kwargs):
        observed["hybrid_scopes"] = tuple(kwargs["knowledge_scopes"])
        return {"results": []}

    def fake_evidence(*args, **kwargs):
        observed["evidence_domains"] = tuple(kwargs["filters"].domains)
        return {"must": [], "context": []}

    monkeypatch.setattr(rv3, "hybrid_search", fake_hybrid)
    monkeypatch.setattr(rv3, "build_evidence_pack", fake_evidence)

    rv3.compile_context(root, "UART", agent_id="embedded-expert")

    assert observed["hybrid_scopes"] == ("embedded", "projects")
    assert observed["evidence_domains"] == observed["hybrid_scopes"]


def test_direct_evidence_pack_api_inherits_agent_scopes(tmp_path, monkeypatch):
    root = _root(tmp_path)
    observed = {}

    def fake_evidence(*args, **kwargs):
        observed["domains"] = tuple(kwargs["filters"].domains)
        return {"status": "pass"}

    monkeypatch.setattr(rv3, "build_evidence_pack", fake_evidence)

    result = rv3.api_dispatch(
        root,
        "evidence-pack",
        {"query": "UART"},
        agent_id="embedded-expert",
    )

    assert result["status"] == "pass"
    assert observed["domains"] == ("embedded", "projects")
