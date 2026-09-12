import json
import shutil

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub.runtime_p4_cli import main as p4_cli_main
from tools.codex_assets.knowledge_hub.runtime_p4_interop import (
    consumer_handshake,
    correlate_execution_receipt,
    handoff_envelope,
    integration_contract,
    integration_readiness,
)
from tools.codex_assets.knowledge_hub.runtime_v3_governance import (
    record_execution_receipt,
)


def _root(tmp_path):
    source_root = repository_root()
    for relative in (
        "registry/knowledge-runtime-v3.json",
        "registry/integrations/digital-worker.json",
        "registry/knowledge-runtime-p4.json",
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


def _identity():
    return {
        "work_item_id": "dw-work-123",
        "run_id": "dw-run-456",
        "scope_ref": "projects/pcr02",
    }


def test_integration_readiness_preserves_ssot_and_surfaces(tmp_path):
    root = _root(tmp_path)
    contract = integration_contract(root, "digital-worker")
    result = integration_readiness(root, "digital-worker")

    assert result["status"] == "pass"
    assert result["missing_provider_capabilities"] == []
    assert result["missing_provider_surfaces"] == []
    assert result["direct_active_mutation"] is False
    assert contract["ssot"]["digital_worker"][0] == "work_item"
    assert contract["source_of_truth_policy"] == "stays-at-source"


def test_consumer_handshake_requires_identity_and_protocol_match(tmp_path):
    root = _root(tmp_path)
    ready = consumer_handshake(
        root,
        "digital-worker",
        "manager-agent",
        _identity(),
        ["knowledge.search"],
        mcp_version="2026-07-28",
        a2a_version="1.0.0",
    )
    blocked = consumer_handshake(
        root,
        "digital-worker",
        "manager-agent",
        {"work_item_id": "dw-work-123"},
        ["knowledge.search"],
        mcp_version="wrong",
        a2a_version="1.0.0",
    )

    assert ready["status"] == "ready"
    assert ready["task_execution_authorized"] is False
    assert ready["canonical_write_permitted"] is False
    assert blocked["status"] == "blocked"
    assert blocked["missing_identity_fields"] == ["run_id", "scope_ref"]
    assert blocked["protocol_mismatches"] == ["mcp"]


def test_handoff_is_report_only_and_does_not_echo_task(tmp_path):
    root = _root(tmp_path)
    task = "Inspect UART timestamp drift and return evidence-backed findings."
    result = handoff_envelope(
        root,
        "digital-worker",
        "manager-agent",
        "embedded-expert",
        task,
        _identity(),
        ["knowledge.search", "knowledge.evidence-pack"],
        evidence_ids=["evidence:uart-1"],
    )

    assert result["status"] == "ready"
    assert result["task_echoed"] is False
    assert task not in json.dumps(result, ensure_ascii=False)
    assert result["handoff_executes_task"] is False
    assert result["canonical_write_permitted"] is False
    assert result["consumer_work_item_ssot"] is True
    assert result["a2a_preflight"]["status"] == "pass"


def test_handoff_correlates_only_verified_local_receipt(tmp_path):
    root = _root(tmp_path)
    recorded = record_execution_receipt(
        root,
        "manager-agent",
        "prepare embedded expert handoff",
        "ALLOW",
        ["evidence:uart-1"],
    )
    digest = recorded["record"]["receipt_sha256"]

    correlated = correlate_execution_receipt(root, digest)
    result = handoff_envelope(
        root,
        "digital-worker",
        "manager-agent",
        "embedded-expert",
        "Inspect UART timestamp drift.",
        _identity(),
        ["knowledge.search"],
        execution_receipt_sha256=digest,
    )
    missing = handoff_envelope(
        root,
        "digital-worker",
        "manager-agent",
        "embedded-expert",
        "Inspect UART timestamp drift.",
        _identity(),
        ["knowledge.search"],
        execution_receipt_sha256="0" * 64,
    )

    assert correlated["verified"] is True
    assert result["status"] == "ready"
    assert result["execution_receipt"]["verified"] is True
    assert missing["status"] == "needs-review"
    assert missing["execution_receipt"]["status"] == "missing"


def test_handoff_keeps_high_risk_delegation_fail_closed(tmp_path):
    root = _root(tmp_path)
    result = handoff_envelope(
        root,
        "digital-worker",
        "manager-agent",
        "embedded-expert",
        "Promote this candidate directly.",
        _identity(),
        ["knowledge.canonical.write"],
    )

    assert result["status"] == "needs-review"
    assert result["human_review_required"] is True
    assert result["a2a_preflight"]["delegation_executes_task"] is False
    assert "knowledge.canonical.write" in result["a2a_preflight"][
        "high_risk_capabilities"
    ]


def test_unknown_consumer_and_invalid_receipt_fail_closed(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(KnowledgeHubError):
        integration_contract(root, "../escape")
    with pytest.raises(KnowledgeHubError):
        correlate_execution_receipt(root, "not-a-digest")


def test_p4_cli_readiness_is_machine_readable(tmp_path, capsys):
    root = _root(tmp_path)
    exit_code = p4_cli_main(
        ["--root", str(root), "readiness", "--consumer", "digital-worker"]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "pass"
    assert payload["schema_version"] == "knowledge-hub.integration-readiness.v1"
