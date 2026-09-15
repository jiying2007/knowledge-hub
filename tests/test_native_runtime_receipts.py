import hashlib
import json

from tools.codex_assets.knowledge_hub.connector_runtime import (
    StaticConnectorAdapter,
    sync_connector,
)
from tools.codex_assets.knowledge_hub.memory_runtime import (
    active_memories,
    append_memory_event,
    consolidation_candidates,
    forget_scope,
    memory_event,
)
from tools.codex_assets.knowledge_hub.observability_runtime import (
    append_span,
    new_span_id,
    new_trace_id,
    span_receipt_sha256,
    span_record,
)
from tools.codex_assets.knowledge_hub.retrieval_telemetry import (
    append_optional_telemetry,
    telemetry_receipt_sha256,
)


def _principal():
    return {
        "principal_id": "alice",
        "organization_id": "engineering",
        "groups": ["team:embedded"],
    }


def test_retrieval_telemetry_returns_exact_persisted_receipt(tmp_path):
    row = {
        "schema_version": 3,
        "interaction_id": "interaction-1",
        "query_sha256": hashlib.sha256(b"private query").hexdigest(),
        "result_ids": ["item-a"],
        "raw_query_stored": False,
    }
    path = tmp_path / ".cache/knowledge-hub/search-telemetry.jsonl"

    result = append_optional_telemetry(path, row)

    assert result["recorded"] is True
    assert result["receipt_sha256"] == telemetry_receipt_sha256(row)
    stored = path.read_text(encoding="utf-8")
    assert "private query" not in stored
    assert json.loads(stored)["raw_query_stored"] is False


def test_observability_span_returns_exact_receipt(tmp_path):
    span = span_record(
        name="knowledge.search",
        trace_id=new_trace_id(),
        span_id=new_span_id(),
        attributes={"query": "private query", "result_count": 1},
    )

    result = append_span(tmp_path, span)

    assert result["receipt_sha256"] == span_receipt_sha256(span)
    ledger = tmp_path / ".cache/knowledge-hub/observability/spans.jsonl"
    stored = ledger.read_text(encoding="utf-8")
    assert "private query" not in stored
    assert "query_sha256" in stored


def test_connector_sync_records_non_production_observation_receipt(tmp_path):
    adapter = StaticConnectorAdapter(
        "github",
        [
            {
                "object_id": "repo:file-a",
                "version": "abc123",
                "body": "reference text",
                "acl": ["alice"],
            },
            {
                "object_id": "repo:file-b",
                "version": "def456",
                "body": "",
                "acl": ["alice"],
                "tombstone": True,
            },
        ],
        next_cursor="commit-2",
    )

    result = sync_connector(tmp_path, adapter, _principal())

    assert result["checkpoint_advanced"] is True
    observation = result["observation"]
    assert observation["recorded"] is True
    assert observation["observation_origin"] == "static-fixture"
    assert len(observation["receipt_sha256"]) == 64
    ledger = tmp_path / ".cache/knowledge-hub/observability/spans.jsonl"
    stored = ledger.read_text(encoding="utf-8")
    assert "alice" not in stored
    assert "commit-2" not in stored
    span = json.loads(stored)
    assert span["attributes"]["canonical_write_performed"] is False
    assert span["attributes"]["tombstone_count"] == 1


def test_memory_events_scope_delete_and_consolidation_are_receipted(tmp_path):
    first = memory_event(
        agent_id="embedded-expert",
        principal_id="alice",
        level="semantic",
        summary="First governed memory.",
        scope_ref="projects/pcr02",
        source_refs=["evidence:1"],
    )
    second = memory_event(
        agent_id="embedded-expert",
        principal_id="alice",
        level="semantic",
        summary="Second governed memory.",
        scope_ref="projects/pcr02",
        source_refs=["evidence:2"],
    )
    other = memory_event(
        agent_id="embedded-expert",
        principal_id="alice",
        level="semantic",
        summary="Other scope memory.",
        scope_ref="projects/other",
        source_refs=["evidence:3"],
    )
    first_write = append_memory_event(tmp_path, first)
    append_memory_event(tmp_path, second)
    append_memory_event(tmp_path, other)

    assert first_write["receipt_sha256"] == first_write["record"]["event_sha256"]
    consolidation = consolidation_candidates(
        tmp_path,
        principal_id="alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
    )
    assert consolidation["candidate_count"] == 1
    assert consolidation["candidates"][0]["promotion_status"] == "candidate-only"
    assert len(consolidation["receipt_sha256"]) == 64

    deletion = forget_scope(
        tmp_path,
        principal_id="alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
    )

    assert deletion["scope_deleted"] is True
    assert deletion["deleted_count"] == 2
    assert len(deletion["receipt_sha256"]) == 64
    assert deletion["canonical_write_performed"] is False
    assert active_memories(
        tmp_path,
        principal_id="alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
    ) == []
    assert len(
        active_memories(
            tmp_path,
            principal_id="alice",
            agent_id="embedded-expert",
            scope_ref="projects/other",
        )
    ) == 1
