import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub import (
    connector_runtime,
    mcp_http_server,
    memory_runtime,
    provider_context,
    temporal_graph,
)


def _record(root, *, scope="scope:a", summary="one"):
    event = memory_runtime.memory_event(
        agent_id="agent",
        principal_id="principal",
        level="working",
        summary=summary,
        scope_ref=scope,
        source_refs=(),
    )
    return memory_runtime.append_memory_event(root, event)["record"]


def test_pending_active_provider_item_is_provisional():
    item = provider_context.public_item(
        {
            "id": "pending-active",
            "title": "pending",
            "kind": "validation",
            "status": "active",
            "path": "projects/pending.md",
            "manual_validation_pending": True,
        }
    )
    lanes = provider_context.authority_lanes(
        [{"subject_ref": {"type": "project", "id": "p"}, "items": [item]}]
    )
    assert item["manual_validation_pending"] is True
    assert lanes["authoritative"] == []
    assert lanes["provisional"] == ["pending-active"]


def test_memory_append_rejects_event_overflow_without_corruption(tmp_path, monkeypatch):
    monkeypatch.setattr(memory_runtime, "MAX_EVENTS", 1)
    first = _record(tmp_path)
    with pytest.raises(KnowledgeHubError, match="full"):
        _record(tmp_path, summary="two")
    rows = memory_runtime.read_memory_ledger(tmp_path)
    assert len(rows) == 1
    assert rows[0]["memory_id"] == first["memory_id"]


def test_memory_rejects_incomplete_tail_without_corruption(tmp_path):
    _record(tmp_path)
    ledger = tmp_path / memory_runtime.DEFAULT_LEDGER
    ledger.write_bytes(ledger.read_bytes()[:-1])
    before = ledger.read_bytes()
    with pytest.raises(KnowledgeHubError, match="tail is incomplete"):
        _record(tmp_path, summary="two")
    assert ledger.read_bytes() == before


def test_memory_wrong_scope_forget_is_rejected(tmp_path):
    row = _record(tmp_path, scope="scope:b")
    with pytest.raises(KnowledgeHubError, match="requested scope"):
        memory_runtime.forget_memory(
            tmp_path,
            memory_id=row["memory_id"],
            principal_id="principal",
            agent_id="agent",
            scope_ref="scope:a",
        )
    active = memory_runtime.active_memories(
        tmp_path,
        principal_id="principal",
        agent_id="agent",
        scope_ref="scope:b",
    )
    assert [value["memory_id"] for value in active] == [row["memory_id"]]


class _OverDeliveringAdapter:
    connector_id = "test"

    def checkpoint(self):
        return "next"

    def list_changed(self, checkpoint, limit):
        return [
            {"object_id": "1", "version": "1", "body": "a", "tombstone": False},
            {"object_id": "2", "version": "1", "body": "b", "tombstone": False},
        ]


def test_connector_rejects_adapter_overdelivery(tmp_path):
    with pytest.raises(KnowledgeHubError, match="more rows than requested"):
        connector_runtime.sync_connector(
            tmp_path,
            _OverDeliveringAdapter(),
            {"principal_id": "principal"},
            limit=1,
        )
    assert connector_runtime.load_checkpoint(tmp_path, "test")["sequence"] == 0


def test_connector_checkpoint_rejects_stale_sequence(tmp_path):
    first = connector_runtime.save_checkpoint(
        tmp_path, "test", cursor="one", previous_sequence=0
    )
    assert first["sequence"] == 1
    with pytest.raises(KnowledgeHubError, match="sequence changed"):
        connector_runtime.save_checkpoint(
            tmp_path, "test", cursor="stale", previous_sequence=0
        )
    current = connector_runtime.load_checkpoint(tmp_path, "test")
    assert current["sequence"] == 1
    assert current["cursor"] == "one"


def test_connector_tombstone_requires_boolean():
    with pytest.raises(KnowledgeHubError, match="tombstone must be boolean"):
        connector_runtime.normalize_object(
            "test",
            {"object_id": "1", "version": "1", "body": "data", "tombstone": "false"},
        )


def test_invalid_origin_is_rejected():
    with pytest.raises(mcp_http_server.MCPProtocolError):
        mcp_http_server.validate_local_origin(
            {"Host": "127.0.0.1:3000", "Origin": "null"}
        )


def test_temporal_graph_reports_truncation_without_dangling_edges(tmp_path, monkeypatch):
    rows = [
        {
            "id": "a",
            "title": "A",
            "status": "active",
            "domain": "d",
            "agent_contract": {"relations": {"related": ["b"]}},
        },
        {"id": "b", "title": "B", "status": "active", "domain": "d"},
    ]
    monkeypatch.setattr(temporal_graph, "registry_items", lambda root: rows)
    monkeypatch.setattr(
        temporal_graph, "_authorized", lambda item, principal, scopes: True
    )
    value = temporal_graph.temporal_context_graph(
        tmp_path, seed_ids=["a"], as_of="2026-10-14", maximum_nodes=1
    )
    assert value["status"] == "needs-review"
    assert value["truncated"] is True
    assert value["coverage_complete"] is False
    assert value["node_count"] == 1
    assert value["edges"] == []


@pytest.mark.parametrize("maximum", [0, -1, 10001])
def test_temporal_graph_rejects_invalid_node_budget(tmp_path, maximum):
    with pytest.raises(KnowledgeHubError, match="maximum_nodes"):
        temporal_graph.temporal_context_graph(
            tmp_path, as_of="2026-10-14", maximum_nodes=maximum
        )


def test_provider_corpus_signature_ignores_unrelated_domain_body(tmp_path, monkeypatch):
    relevant = tmp_path / "relevant.md"
    unrelated = tmp_path / "unrelated.md"
    relevant.write_text("alpha", encoding="utf-8")
    unrelated.write_text("before", encoding="utf-8")
    rows = [
        {"id": "a", "path": "relevant.md", "domain": "wanted", "visibility": "team-internal"},
        {"id": "b", "path": "unrelated.md", "domain": "other", "visibility": "team-internal"},
    ]
    monkeypatch.setattr(provider_context, "_execution", lambda root, args, resolution: (None, resolution))
    monkeypatch.setattr(
        provider_context,
        "scope_inputs",
        lambda root, args, execution: [{"type": "domain", "id": "wanted"}],
    )
    monkeypatch.setattr(provider_context, "authorize", lambda root, action, scope: None)
    monkeypatch.setattr(provider_context, "registry_items", lambda root: rows)
    args = type("Args", (), {})()
    first = provider_context.corpus_signature(tmp_path, args, {})
    unrelated.write_text("after", encoding="utf-8")
    second = provider_context.corpus_signature(tmp_path, args, {})
    assert second == first
    relevant.write_text("changed", encoding="utf-8")
    assert provider_context.corpus_signature(tmp_path, args, {}) != first


def test_memory_scope_delete_scans_ledger_constant_times(tmp_path, monkeypatch):
    for index in range(40):
        _record(tmp_path, scope="scope:bulk", summary="row-{}".format(index))
    original = memory_runtime._read_unlocked
    calls = {"count": 0}

    def counted(root):
        calls["count"] += 1
        return original(root)

    monkeypatch.setattr(memory_runtime, "_read_unlocked", counted)
    result = memory_runtime.forget_scope(
        tmp_path,
        principal_id="principal",
        agent_id="agent",
        scope_ref="scope:bulk",
    )
    assert result["scope_deleted"] is True
    assert result["deleted_count"] == 40
    assert calls["count"] <= 3


def test_structured_filter_is_applied_before_candidate_limit(tmp_path, monkeypatch):
    from tests.test_fifth_retrieval import _hub, _item
    from tools.codex_assets.knowledge_hub.search import SearchFilters, SearchIndex, search

    noisy = _item(
        "noise",
        "flash flash flash flash flash",
        "flash " * 40,
        project="other",
    )
    target = _item(
        "target",
        "flash target",
        "flash target answer",
        project="wanted",
    )
    root = _hub(tmp_path, [noisy, target])
    monkeypatch.setattr(SearchIndex, "CANDIDATE_LIMIT", 1)
    monkeypatch.setattr(SearchIndex, "STRUCTURED_CANDIDATE_LIMIT", 1)
    result = search(
        root,
        "flash",
        filters=SearchFilters(domains=["projects/wanted"]),
    )
    assert [row["item_id"] for row in result["results"]] == ["target"]


def test_static_connector_cannot_skip_unconsumed_page():
    adapter = connector_runtime.StaticConnectorAdapter(
        "static",
        [
            {"object_id": str(index), "version": "1", "body": "x"}
            for index in range(3)
        ],
    )
    with pytest.raises(KnowledgeHubError, match="exceeds batch limit"):
        adapter.list_changed("", limit=2)


def test_connector_acl_rejects_nonstring_subject():
    with pytest.raises(KnowledgeHubError, match="invalid subject"):
        connector_runtime.normalize_object(
            "static", {"object_id": "one", "version": "1", "acl": [17]},
        )


def test_provider_adapter_rejects_acl_truncation():
    from tools.codex_assets.knowledge_hub.connector_adapters import github_object

    with pytest.raises(KnowledgeHubError, match="excessive"):
        github_object(
            {
                "repository": "org/repo",
                "path": "README.md",
                "sha": "a" * 40,
                "acl": ["alice"] * 65,
            }
        )
