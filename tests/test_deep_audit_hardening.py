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
