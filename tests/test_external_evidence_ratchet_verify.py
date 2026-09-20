import hashlib
import json
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub.external_evidence import RECEIPT_SCHEMA
from tools.codex_assets.knowledge_hub.external_evidence_ratchet import (
    build_external_gap_ratchet_candidate,
)
from tools.codex_assets.knowledge_hub.external_evidence_ratchet_verify import (
    verify_external_evidence_ratchet,
)
from tools.codex_assets.knowledge_hub.schemas import validate_instance


REPOSITORY = "jiying2007/knowledge-hub"
GAP = "connector-provider-pilot"
MASTER = "a" * 40
HEAD = "b" * 40
SOURCE = "c" * 40
INTAKE = "d" * 40
RUN_ID = 321
RUN_ATTEMPT = 1


def _write_json(path: Path, value) -> str:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_compact(path: Path, value) -> str:
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path):
    base_registry = tmp_path / "base-registry.json"
    head_registry = tmp_path / "head-registry.json"
    base_ledger = tmp_path / "base-ledger.jsonl"
    head_ledger = tmp_path / "head-ledger.jsonl"
    closure = tmp_path / "closure.json"
    intake = tmp_path / "intake.json"
    binding = tmp_path / "binding.json"
    proposal_path = tmp_path / "proposal.json"
    origin = tmp_path / "origin.json"

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
    _write_json(base_registry, registry)

    closure_value = {
        "schema_version": RECEIPT_SCHEMA,
        "status": "pass",
        "closure_ready": True,
        "gap_id": GAP,
        "source_revision": SOURCE,
        "observed_at": "2026-09-20T01:00:00Z",
        "evidence_payload_sha256": "e" * 64,
        "evidence_source_refs": ["run://provider/123"],
        "summary": {},
        "synthetic_evidence_accepted": False,
        "mock_evidence_accepted": False,
        "local_only_evidence_accepted": False,
        "canonical_write_performed": False,
        "generated_at": "2026-09-20T01:00:00Z",
    }
    closure_sha = _write_compact(closure, closure_value)

    intake_value = {
        "schema_version": 1,
        "projection": "knowledge-hub-external-evidence-intake-v1",
        "status": "pass",
        "closure_candidate_only": True,
        "canonical_write_performed": False,
        "gap_id": GAP,
        "source_revision": SOURCE,
        "evidence_payload_sha256": "e" * 64,
        "receipt_sha256": closure_sha,
        "source_provenance": {
            "repository": REPOSITORY,
            "source_run_id": 123,
            "source_run_attempt": 1,
            "source_run_head_sha": SOURCE,
            "source_run_head_branch": "master",
            "source_run_event": "workflow_dispatch",
            "source_workflow_path": ".github/workflows/real-observation-source.yml",
            "artifact_id": 456,
            "artifact_name": "strict-provider-evidence",
            "artifact_digest": "sha256:" + "f" * 64,
        },
        "root_observation_provenance": {
            "repository": REPOSITORY,
            "source_run_id": 123,
            "source_run_attempt": 1,
            "source_run_head_sha": SOURCE,
            "source_run_head_branch": "master",
            "source_run_event": "workflow_dispatch",
            "source_workflow_path": ".github/workflows/real-observation-source.yml",
            "artifact_id": 456,
            "artifact_name": "strict-provider-evidence",
            "artifact_digest": "sha256:" + "f" * 64,
        },
        "intake_run_id": 789,
        "intake_run_attempt": 1,
        "intake_revision": INTAKE,
    }
    intake_sha = _write_compact(intake, intake_value)

    binding_value = {
        "schema_version": 1,
        "projection": "knowledge-hub-external-evidence-intake-host-binding-v1",
        "status": "pass",
        "repository": REPOSITORY,
        "workflow_path": ".github/workflows/external-evidence-intake.yml",
        "intake_run_id": 789,
        "intake_run_attempt": 1,
        "intake_run_head_sha": INTAKE,
        "artifact_id": 987,
        "artifact_name": "knowledge-hub-external-evidence-connector-provider-pilot-789-1",
        "artifact_digest": "sha256:" + "1" * 64,
        "intake_receipt_sha256": intake_sha,
    }
    _write_compact(binding, binding_value)

    candidate, proposal = build_external_gap_ratchet_candidate(
        registry_path=base_registry,
        closure_receipt_path=closure,
        intake_receipt_path=intake,
        host_binding_path=binding,
    )
    _write_json(head_registry, candidate)
    _write_json(proposal_path, proposal)
    base_ledger.write_bytes(b"")

    gap = next(
        row
        for row in candidate["external_closure_gaps"]
        if row["id"] == GAP
    )
    record = {
        "schema_version": 1,
        "event_id": "external-evidence-{}-{}-{}".format(
            GAP, RUN_ID, RUN_ATTEMPT
        ),
        "event_type": "external-evidence-ratchet",
        "source_revision": MASTER,
        "observed_at": proposal["generated_at"],
        "evidence_refs": gap["evidence_refs"],
        "digests": {
            "candidate_registry": "sha256:"
            + hashlib.sha256(head_registry.read_bytes()).hexdigest(),
            "ratchet_proposal": "sha256:"
            + hashlib.sha256(proposal_path.read_bytes()).hexdigest(),
            "host_binding": "sha256:"
            + hashlib.sha256(binding.read_bytes()).hexdigest(),
            "closure_receipt": "sha256:"
            + hashlib.sha256(closure.read_bytes()).hexdigest(),
            "intake_receipt": "sha256:"
            + hashlib.sha256(intake.read_bytes()).hexdigest(),
        },
        "expires_at": None,
        "notes": "strict real external evidence ratchet",
    }
    _write_compact(head_ledger, record)
    _write_json(
        origin,
        {
            "id": RUN_ID,
            "run_attempt": RUN_ATTEMPT,
            "name": "external-evidence-ratchet-candidate",
            "path": ".github/workflows/external-evidence-ratchet-candidate.yml",
            "head_sha": MASTER,
            "head_branch": "master",
            "status": "completed",
            "conclusion": "success",
            "event": "workflow_run",
            "repository": {"full_name": REPOSITORY},
        },
    )
    return {
        "base_registry": base_registry,
        "head_registry": head_registry,
        "base_ledger": base_ledger,
        "head_ledger": head_ledger,
        "closure": closure,
        "intake": intake,
        "binding": binding,
        "proposal": proposal_path,
        "origin": origin,
    }


def _verify(paths):
    return verify_external_evidence_ratchet(
        repository_root(),
        base_registry_path=paths["base_registry"],
        head_registry_path=paths["head_registry"],
        base_ledger_path=paths["base_ledger"],
        head_ledger_path=paths["head_ledger"],
        closure_receipt_path=paths["closure"],
        intake_receipt_path=paths["intake"],
        host_binding_path=paths["binding"],
        proposal_path=paths["proposal"],
        origin_run_path=paths["origin"],
        repository=REPOSITORY,
        master_sha=MASTER,
        head_sha=HEAD,
    )


def test_external_ratchet_verifier_accepts_exact_replayed_chain(tmp_path):
    paths = _fixture(tmp_path)
    result = _verify(paths)

    assert result["status"] == "pass"
    assert result["gap_id"] == GAP
    assert result["origin_run_id"] == RUN_ID
    assert result["origin_run_attempt"] == RUN_ATTEMPT
    assert result["root_source_repository"] == REPOSITORY
    assert result["root_source_run_id"] == 123
    assert result["root_source_run_attempt"] == 1
    assert result["root_source_run_head_sha"] == SOURCE
    assert (
        result["root_source_workflow_path"]
        == ".github/workflows/real-observation-source.yml"
    )
    assert result["root_source_artifact_id"] == 456
    assert result["root_source_artifact_digest"] == "sha256:" + "f" * 64
    assert (
        validate_instance(
            repository_root(),
            "external-evidence-ratchet-verification-v1",
            result,
        )["status"]
        == "pass"
    )


def test_external_ratchet_verifier_rejects_candidate_tamper(tmp_path):
    paths = _fixture(tmp_path)
    head = json.loads(paths["head_registry"].read_text(encoding="utf-8"))
    head["external_closure_gaps"][0]["reason"] = "tampered"
    _write_json(paths["head_registry"], head)

    with pytest.raises(KnowledgeHubError, match="replayed external candidate"):
        _verify(paths)


def test_external_ratchet_verifier_rejects_multiple_ledger_appends(tmp_path):
    paths = _fixture(tmp_path)
    row = paths["head_ledger"].read_text(encoding="utf-8")
    paths["head_ledger"].write_text(row + row, encoding="utf-8")

    with pytest.raises(KnowledgeHubError, match="exactly one durable record"):
        _verify(paths)


def test_external_ratchet_verifier_rejects_origin_run_drift(tmp_path):
    paths = _fixture(tmp_path)
    origin = json.loads(paths["origin"].read_text(encoding="utf-8"))
    origin["head_sha"] = "9" * 40
    _write_json(paths["origin"], origin)

    with pytest.raises(KnowledgeHubError, match="head_sha mismatch"):
        _verify(paths)


def test_external_ratchet_verifier_is_in_mypy_surface():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert (
        '"tools/codex_assets/knowledge_hub/external_evidence_ratchet_verify.py"'
        in text
    )


def test_external_ratchet_verifier_rejects_retained_source_trust_tamper(
    tmp_path,
):
    paths = _fixture(tmp_path)
    intake = json.loads(paths["intake"].read_text(encoding="utf-8"))
    intake["source_provenance"]["source_run_head_branch"] = "feature/untrusted"
    _write_compact(paths["intake"], intake)

    with pytest.raises(
        KnowledgeHubError,
        match="external-evidence-intake-receipt-v1 validation failed",
    ):
        _verify(paths)
