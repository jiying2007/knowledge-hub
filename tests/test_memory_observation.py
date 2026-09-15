import json

from tools.codex_assets.knowledge_hub.memory_observation import observe_memory_state
from tools.codex_assets.knowledge_hub.memory_runtime import (
    append_memory_event,
    forget_memory,
    memory_event,
)
from tools.codex_assets.knowledge_hub.runtime_p5_p10_cli import _dispatch, _parser


def _record(root, *, principal="user:alice", agent="embedded-expert", scope="projects/pcr02"):
    return append_memory_event(
        root,
        memory_event(
            agent_id=agent,
            principal_id=principal,
            level="semantic",
            summary="Private memory body must never appear in observation output.",
            scope_ref=scope,
            source_refs=("receipt:source",),
        ),
    )


def test_memory_observation_is_privacy_safe_and_receipted(tmp_path):
    recorded = _record(tmp_path)
    memory_id = recorded["record"]["memory_id"]

    observation = observe_memory_state(
        tmp_path,
        principal_id="user:alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
        memory_id=memory_id,
        expected_state="present",
    )

    assert observation["status"] == "pass"
    assert observation["target_present"] is True
    assert observation["active_count"] == 1
    assert observation["event_count"] == 1
    assert len(observation["receipt_sha256"]) == 64
    assert len(observation["state_sha256"]) == 64
    assert observation["raw_summary_stored"] is False
    assert observation["raw_identity_stored"] is False
    assert observation["raw_memory_id_stored"] is False
    assert observation["canonical_write_performed"] is False

    serialized = json.dumps(observation, sort_keys=True)
    assert "Private memory body" not in serialized
    assert "user:alice" not in serialized
    assert "embedded-expert" not in serialized
    assert "projects/pcr02" not in serialized
    assert memory_id not in serialized


def test_memory_observation_proves_identity_and_scope_isolation(tmp_path):
    recorded = _record(tmp_path)
    memory_id = recorded["record"]["memory_id"]

    cases = (
        ("user:bob", "embedded-expert", "projects/pcr02"),
        ("user:alice", "other-agent", "projects/pcr02"),
        ("user:alice", "embedded-expert", "projects/other"),
    )
    for principal, agent, scope in cases:
        result = observe_memory_state(
            tmp_path,
            principal_id=principal,
            agent_id=agent,
            scope_ref=scope,
            memory_id=memory_id,
            expected_state="absent",
        )
        assert result["status"] == "pass"
        assert result["target_present"] is False
        assert result["event_count"] == 1
        assert len(result["receipt_sha256"]) == 64


def test_memory_observation_fails_when_expectation_is_wrong(tmp_path):
    recorded = _record(tmp_path)
    memory_id = recorded["record"]["memory_id"]

    result = observe_memory_state(
        tmp_path,
        principal_id="user:alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
        memory_id=memory_id,
        expected_state="absent",
    )

    assert result["status"] == "fail"
    assert result["target_present"] is True
    assert len(result["receipt_sha256"]) == 64


def test_memory_observation_verifies_forget_without_canonical_write(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir()
    canonical = registry / "knowledge-platform-p5-p10.json"
    canonical.write_text('{"sentinel":"unchanged"}\n', encoding="utf-8")
    before = canonical.read_bytes()

    recorded = _record(tmp_path)
    memory_id = recorded["record"]["memory_id"]
    forgotten = forget_memory(
        tmp_path,
        memory_id=memory_id,
        principal_id="user:alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
    )
    assert forgotten["status"] == "recorded"

    result = observe_memory_state(
        tmp_path,
        principal_id="user:alice",
        agent_id="embedded-expert",
        scope_ref="projects/pcr02",
        memory_id=memory_id,
        expected_state="absent",
    )
    assert result["status"] == "pass"
    assert result["target_present"] is False
    assert canonical.read_bytes() == before


def test_memory_observe_cli_uses_existing_runtime_surface(tmp_path):
    recorded = _record(tmp_path)
    memory_id = recorded["record"]["memory_id"]
    args = _parser().parse_args(
        [
            "memory-observe",
            "--principal-id",
            "user:alice",
            "--agent-id",
            "embedded-expert",
            "--scope-ref",
            "projects/pcr02",
            "--memory-id",
            memory_id,
            "--expect",
            "present",
        ]
    )

    result = _dispatch(tmp_path, args)
    assert result["status"] == "pass"
    assert result["target_present"] is True
    assert result["schema_version"] == "knowledge-hub.memory-observation.v1"
