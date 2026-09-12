import datetime as dt
import json

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.memory_runtime import (
    active_memories,
    append_memory_event,
    consolidation_candidates,
    forget_memory,
    memory_event,
    read_memory_ledger,
    supersede_memory,
)
from tools.codex_assets.knowledge_hub.temporal_graph import (
    temporal_context_graph,
    validate_temporal_fields,
)


def test_memory_runtime_is_private_scoped_ttl_and_forgettable(tmp_path):
    first = memory_event(
        agent_id="embedded-expert",
        principal_id="alice",
        level="semantic",
        summary="Power loss recovery requires filesystem validation.",
        scope_ref="projects/pcr02",
        source_refs=["evidence:1"],
        ttl_seconds=60,
    )
    second = memory_event(
        agent_id="embedded-expert",
        principal_id="alice",
        level="semantic",
        summary="Recovery must preserve the canonical registry boundary.",
        scope_ref="projects/pcr02",
        source_refs=["evidence:2"],
    )
    append_memory_event(tmp_path, first)
    append_memory_event(tmp_path, second)

    current = active_memories(
        tmp_path,
        principal_id="alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
    )
    denied = active_memories(
        tmp_path,
        principal_id="bob",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
    )
    future = active_memories(
        tmp_path,
        principal_id="alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
        now=dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=120),
    )

    assert len(current) == 2
    assert denied == []
    assert len(future) == 1
    assert all(row["canonical_write"] is False for row in current)

    candidates = consolidation_candidates(
        tmp_path,
        principal_id="alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
    )
    assert candidates["candidate_count"] == 1
    assert candidates["canonical_write_performed"] is False

    forget_memory(
        tmp_path,
        memory_id=second["memory_id"],
        principal_id="alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
    )
    assert active_memories(
        tmp_path,
        principal_id="alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
    )[0]["memory_id"] == first["memory_id"]


def test_memory_supersede_and_tamper_detection(tmp_path):
    event = memory_event(
        agent_id="debug-investigator",
        principal_id="alice",
        level="procedural",
        summary="Collect dump before applying recovery action.",
        scope_ref="projects/pcr02",
        source_refs=["evidence:dump"],
    )
    append_memory_event(tmp_path, event)
    supersede_memory(
        tmp_path,
        memory_id=event["memory_id"],
        principal_id="alice",
        agent_id="debug-investigator",
        scope_ref="projects/pcr02",
    )
    assert active_memories(
        tmp_path,
        principal_id="alice",
        agent_id="debug-investigator",
        scope_ref="projects/pcr02",
    ) == []

    ledger = tmp_path / ".cache/knowledge-hub/memory/events.jsonl"
    text = ledger.read_text(encoding="utf-8")
    ledger.write_text(text.replace("procedural", "semantic", 1), encoding="utf-8")
    with pytest.raises(KnowledgeHubError, match="digest mismatch"):
        read_memory_ledger(tmp_path)


def _temporal_root(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir(parents=True)
    items = [
        {
            "id": "old-decision",
            "title": "Old decision",
            "domain": "projects/pcr02",
            "path": "projects/pcr02/old.md",
            "status": "superseded",
            "created_at": "2026-01-01",
            "updated_at": "2026-06-01",
            "valid_from": "2026-01-01",
            "valid_to": "2026-06-30",
            "tags": ["decision"],
            "source": {"type": "manual"},
            "superseded_by": "new-decision",
            "agent_contract": {
                "relations": {"supersedes": []}
            },
        },
        {
            "id": "new-decision",
            "title": "New decision",
            "domain": "projects/pcr02",
            "path": "projects/pcr02/new.md",
            "status": "active",
            "created_at": "2026-07-01",
            "updated_at": "2026-09-01",
            "valid_from": "2026-07-01",
            "tags": ["decision"],
            "source": {"type": "manual"},
            "agent_contract": {
                "relations": {"conflicts_with": []}
            },
        },
    ]
    (registry / "items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in items),
        encoding="utf-8",
    )
    (registry / "sources.json").write_text('{"sources":[]}\n', encoding="utf-8")
    (registry / "retired-sources.jsonl").write_text("", encoding="utf-8")
    return tmp_path


def test_temporal_graph_respects_validity_window_and_supersession(tmp_path):
    root = _temporal_root(tmp_path)
    old = temporal_context_graph(root, as_of="2026-06-15")
    new = temporal_context_graph(root, as_of="2026-09-12")

    assert {row["id"] for row in old["nodes"]} == {"old-decision"}
    assert {row["id"] for row in new["nodes"]} == {"new-decision"}
    assert old["authoritative"] is False
    assert new["canonical_graph_mutated"] is False


def test_temporal_validation_is_fail_closed():
    assert validate_temporal_fields(
        {"valid_from": "2026-01-01", "valid_to": "2026-01-31"}
    ) == []
    assert "valid_from must use YYYY-MM-DD" in validate_temporal_fields(
        {"valid_from": "bad"}
    )
    assert "valid_from must not exceed valid_to" in validate_temporal_fields(
        {"valid_from": "2026-02-01", "valid_to": "2026-01-01"}
    )
    assert "superseded item requires superseded_by" in validate_temporal_fields(
        {"status": "superseded"}, require_superseded_link=True
    )
