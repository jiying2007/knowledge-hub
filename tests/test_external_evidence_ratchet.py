import hashlib
import json
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.external_evidence import RECEIPT_SCHEMA
from tools.codex_assets.knowledge_hub.external_evidence_ratchet import (
    build_external_gap_ratchet_candidate,
)


GAP = "connector-provider-pilot"
SOURCE_SHA = "a" * 40
INTAKE_SHA = "b" * 40
PAYLOAD_SHA = "c" * 64


def _write(path: Path, value):
    path.write_text(json.dumps(value, separators=(",", ":")) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path):
    registry = {
        "schema_version": 2,
        "external_closure_gaps": [
            {
                "id": GAP,
                "owner": "integration-owner",
                "required": True,
                "status": "open",
                "reason": "real provider evidence required",
            },
            {
                "id": "mcp-official-conformance",
                "required": True,
                "status": "closed",
                "reason": "already closed",
                "evidence_refs": ["run://mcp"],
            },
        ],
    }
    closure = {
        "schema_version": RECEIPT_SCHEMA,
        "status": "pass",
        "closure_ready": True,
        "gap_id": GAP,
        "source_revision": SOURCE_SHA,
        "observed_at": "2026-09-14T14:00:00Z",
        "evidence_payload_sha256": PAYLOAD_SHA,
        "evidence_source_refs": ["run://provider/123", "artifact://provider/456"],
        "synthetic_evidence_accepted": False,
        "mock_evidence_accepted": False,
        "local_only_evidence_accepted": False,
        "canonical_write_performed": False,
    }
    registry_path = tmp_path / "registry.json"
    closure_path = tmp_path / "closure.json"
    intake_path = tmp_path / "intake.json"
    binding_path = tmp_path / "binding.json"
    _write(registry_path, registry)
    closure_sha = _write(closure_path, closure)
    intake = {
        "schema_version": 1,
        "projection": "knowledge-hub-external-evidence-intake-v1",
        "status": "pass",
        "closure_candidate_only": True,
        "canonical_write_performed": False,
        "gap_id": GAP,
        "source_revision": SOURCE_SHA,
        "evidence_payload_sha256": PAYLOAD_SHA,
        "receipt_sha256": closure_sha,
        "source_provenance": {
            "repository": "jiying2007/knowledge-hub",
            "source_run_id": 123,
            "source_run_head_sha": SOURCE_SHA,
            "artifact_id": 456,
            "artifact_name": "real-provider-evidence",
            "artifact_digest": "sha256:" + "d" * 64,
        },
        "intake_run_id": 789,
        "intake_run_attempt": 1,
        "intake_revision": INTAKE_SHA,
    }
    intake_sha = _write(intake_path, intake)
    binding = {
        "schema_version": 1,
        "projection": "knowledge-hub-external-evidence-intake-host-binding-v1",
        "status": "pass",
        "repository": "jiying2007/knowledge-hub",
        "workflow_path": ".github/workflows/external-evidence-intake.yml",
        "intake_run_id": 789,
        "intake_run_attempt": 1,
        "intake_run_head_sha": INTAKE_SHA,
        "artifact_id": 987,
        "artifact_name": "knowledge-hub-external-evidence-connector-provider-pilot-789-1",
        "artifact_digest": "sha256:" + "e" * 64,
        "intake_receipt_sha256": intake_sha,
    }
    _write(binding_path, binding)
    return registry_path, closure_path, intake_path, binding_path


def test_ratchet_builder_closes_only_requested_gap_as_machine_candidate(tmp_path: Path):
    paths = _fixture(tmp_path)
    candidate, proposal = build_external_gap_ratchet_candidate(
        registry_path=paths[0],
        closure_receipt_path=paths[1],
        intake_receipt_path=paths[2],
        host_binding_path=paths[3],
    )
    gaps = {item["id"]: item for item in candidate["external_closure_gaps"]}
    assert gaps[GAP]["status"] == "closed"
    assert gaps[GAP]["evidence"]["terminal_claimed"] is False
    assert gaps[GAP]["evidence"]["canonical_write_performed_by_evidence_chain"] is False
    assert gaps["mcp-official-conformance"]["status"] == "closed"
    assert proposal["projection"] == "knowledge-hub-external-evidence-ratchet-proposal-v2"
    assert proposal["status"] == "ready-for-machine-ratchet"
    assert proposal["authorization_class"] == "autonomous-low-risk-ratchet"
    assert proposal["review_required"] is False
    assert proposal["canonical_write_performed"] is False
    assert len(proposal["expected_registry_sha256"]) == 64
    assert len(proposal["candidate_registry_sha256"]) == 64
    assert proposal["generated_at"] == "2026-09-14T14:00:00Z"


def test_ratchet_builder_rejects_receipt_substitution(tmp_path: Path):
    paths = _fixture(tmp_path)
    closure = json.loads(paths[1].read_text(encoding="utf-8"))
    closure["observed_at"] = "2026-09-14T15:00:00Z"
    _write(paths[1], closure)
    with pytest.raises(KnowledgeHubError, match="not bound to the supplied closure receipt"):
        build_external_gap_ratchet_candidate(
            registry_path=paths[0],
            closure_receipt_path=paths[1],
            intake_receipt_path=paths[2],
            host_binding_path=paths[3],
        )


def test_ratchet_builder_rejects_non_open_or_prepopulated_gap(tmp_path: Path):
    paths = _fixture(tmp_path)
    registry = json.loads(paths[0].read_text(encoding="utf-8"))
    registry["external_closure_gaps"][0]["status"] = "closed"
    _write(paths[0], registry)
    with pytest.raises(KnowledgeHubError, match="required and open"):
        build_external_gap_ratchet_candidate(
            registry_path=paths[0],
            closure_receipt_path=paths[1],
            intake_receipt_path=paths[2],
            host_binding_path=paths[3],
        )


def test_ratchet_workflow_is_manual_read_only_and_never_writes_canonical():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/external-evidence-ratchet-candidate.yml").read_text(
        encoding="utf-8"
    )
    cli = (
        root / "tools/codex_assets/knowledge_hub/external_evidence_ratchet_cli.py"
    ).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "github.ref == 'refs/heads/master'" in workflow
    assert "actions: read" in workflow and "contents: read" in workflow
    assert "contents: write" not in workflow and "pull-requests: write" not in workflow
    assert "source run must be the external-evidence-intake workflow" in workflow
    assert "intake workflow run must be completed/success" in workflow
    assert "git diff --exit-code -- registry/knowledge-platform-p5-p10.json" in workflow
    assert "if-no-files-found: error" in workflow
    assert "ratchet candidate CLI must never write the canonical registry" in cli


def test_external_ratchet_is_deterministic_for_same_hosted_evidence(tmp_path: Path):
    paths = _fixture(tmp_path)
    first = build_external_gap_ratchet_candidate(
        registry_path=paths[0],
        closure_receipt_path=paths[1],
        intake_receipt_path=paths[2],
        host_binding_path=paths[3],
    )
    second = build_external_gap_ratchet_candidate(
        registry_path=paths[0],
        closure_receipt_path=paths[1],
        intake_receipt_path=paths[2],
        host_binding_path=paths[3],
    )
    assert first == second


def test_external_ratchet_matches_ai_first_policy():
    root = Path(__file__).resolve().parents[1]
    policy = json.loads(
        (root / "registry/ai-operations-policy.json").read_text(encoding="utf-8")
    )
    boundary = policy["external_evidence"]
    assert boundary["observation_generation_class"] == "real-world-evidence"
    assert boundary["validated_closure_class"] == "autonomous-low-risk-ratchet"
    assert boundary["strict_validator_required"] is True
    assert boundary["same_repository_hosted_chain_required"] is True
    assert boundary["synthetic_evidence_allowed"] is False
    assert boundary["mock_evidence_allowed"] is False
    assert boundary["local_only_evidence_allowed"] is False
    assert boundary["machine_ratchet_may_create_pr"] is True
    assert boundary["machine_ratchet_direct_master_write"] is False
    assert boundary["machine_ratchet_auto_merge_requires_protected_branch"] is True
