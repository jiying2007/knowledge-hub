import json
import shutil

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.runtime_p4_policy import (
    governed_handoff_envelope,
)
from tools.codex_assets.knowledge_hub.runtime_v3_governance import (
    record_execution_receipt,
)


def _root(tmp_path):
    source_root = repository_root()
    for relative in (
        "registry/knowledge-runtime-v3.json",
        "registry/knowledge-runtime-p4.json",
        "registry/integrations/digital-worker.json",
    ):
        source = source_root / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    contract = json.loads(
        (tmp_path / "registry/integrations/digital-worker.json").read_text(
            encoding="utf-8"
        )
    )
    surfaces = {}
    surfaces.update(contract["read_surfaces"])
    surfaces.update(contract["write_surfaces"])
    surfaces["provider_entrypoint"] = contract["runtime_contract"][
        "provider_entrypoint"
    ]
    for relative in surfaces.values():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    return tmp_path


def _identity(scope_ref="projects/pcr02"):
    return {
        "work_item_id": "dw-work-123",
        "run_id": "dw-run-456",
        "scope_ref": scope_ref,
    }


def test_governed_handoff_allows_matching_target_scope(tmp_path):
    root = _root(tmp_path)
    result = governed_handoff_envelope(
        root,
        "digital-worker",
        "manager-agent",
        "embedded-expert",
        "Inspect UART timestamp drift.",
        _identity(),
        ["knowledge.search"],
    )

    assert result["status"] == "ready"
    assert result["policy_enforced"] is True
    assert result["scope_check"]["from_agent_allowed"] is True
    assert result["scope_check"]["to_agent_allowed"] is True


def test_governed_handoff_blocks_target_scope_escape(tmp_path):
    root = _root(tmp_path)
    result = governed_handoff_envelope(
        root,
        "digital-worker",
        "manager-agent",
        "embedded-expert",
        "Inspect a governance-only scope.",
        _identity("governance/policy"),
        ["knowledge.search"],
    )

    assert result["status"] == "blocked"
    assert result["scope_check"]["from_agent_allowed"] is True
    assert result["scope_check"]["to_agent_allowed"] is False
    assert result["policy_block_reasons"] == ["to-agent-scope"]
    assert result["handoff_executes_task"] is False


def test_governed_handoff_blocks_receipt_from_another_agent(tmp_path):
    root = _root(tmp_path)
    recorded = record_execution_receipt(
        root,
        "embedded-expert",
        "embedded-only preparation",
        "ALLOW",
        ["evidence:embedded"],
    )
    digest = recorded["record"]["receipt_sha256"]

    result = governed_handoff_envelope(
        root,
        "digital-worker",
        "manager-agent",
        "embedded-expert",
        "Inspect UART timestamp drift.",
        _identity(),
        ["knowledge.search"],
        execution_receipt_sha256=digest,
    )

    assert result["execution_receipt"]["verified"] is True
    assert result["execution_receipt_agent_match"] is False
    assert result["status"] == "blocked"
    assert result["policy_block_reasons"] == ["receipt-agent-mismatch"]
