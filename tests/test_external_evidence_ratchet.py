import hashlib
import json
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.external_evidence import RECEIPT_SCHEMA
from tools.codex_assets.knowledge_hub.schemas import validate_instance
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
        "summary": {},
        "synthetic_evidence_accepted": False,
        "mock_evidence_accepted": False,
        "local_only_evidence_accepted": False,
        "canonical_write_performed": False,
        "generated_at": "2026-09-14T14:00:00Z",
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
            "schema_version": 1,
            "repository": "jiying2007/knowledge-hub",
            "source_run_id": 123,
            "source_run_attempt": 1,
            "source_run_head_sha": SOURCE_SHA,
            "source_run_head_branch": "master",
            "source_run_event": "workflow_dispatch",
            "source_workflow_path": ".github/workflows/real-observation-source.yml",
            "artifact_id": 456,
            "artifact_name": "real-provider-evidence",
            "artifact_digest": "sha256:" + "d" * 64,
        },
        "root_observation_provenance": {
            "schema_version": 1,
            "repository": "jiying2007/knowledge-hub",
            "source_run_id": 123,
            "source_run_attempt": 1,
            "source_run_head_sha": SOURCE_SHA,
            "source_run_head_branch": "master",
            "source_run_event": "workflow_dispatch",
            "source_workflow_path": ".github/workflows/real-observation-source.yml",
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
    assert gaps[GAP]["evidence"]["root_source_run_id"] == 123
    assert gaps[GAP]["evidence"]["root_source_run_attempt"] == 1
    assert gaps[GAP]["evidence"]["root_source_run_head_sha"] == SOURCE_SHA
    assert (
        gaps[GAP]["evidence"]["root_source_workflow_path"]
        == ".github/workflows/real-observation-source.yml"
    )
    evidence = gaps[GAP]["evidence"]
    assert evidence["source_run_attempt"] == 1
    assert evidence["source_run_event"] == "workflow_dispatch"
    assert (
        evidence["source_workflow_path"]
        == ".github/workflows/real-observation-source.yml"
    )
    assert evidence["source_artifact_name"] == "real-provider-evidence"
    assert evidence["root_source_run_event"] == "workflow_dispatch"
    assert evidence["root_source_artifact_name"] == "real-provider-evidence"
    assert evidence["intake_run_attempt"] == 1
    assert (
        evidence["intake_workflow_path"]
        == ".github/workflows/external-evidence-intake.yml"
    )
    assert (
        evidence["intake_artifact_name"]
        == "knowledge-hub-external-evidence-connector-provider-pilot-789-1"
    )
    assert "https://github.com/jiying2007/knowledge-hub/actions/runs/123" in (
        gaps[GAP]["evidence_refs"]
    )
    assert (
        "https://github.com/jiying2007/knowledge-hub/actions/runs/123/artifacts/456"
        in gaps[GAP]["evidence_refs"]
    )
    assert len(gaps[GAP]["evidence_refs"]) == len(
        set(gaps[GAP]["evidence_refs"])
    )
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


def test_ratchet_workflow_automates_candidate_pr_without_direct_master_write():
    root = Path(__file__).resolve().parents[1]
    workflow = (
        root / ".github/workflows/external-evidence-ratchet-candidate.yml"
    ).read_text(encoding="utf-8")
    cli = (
        root / "tools/codex_assets/knowledge_hub/external_evidence_ratchet_cli.py"
    ).read_text(encoding="utf-8")

    assert "workflow_run:" in workflow
    assert "external-evidence-intake" in workflow
    assert "workflow_dispatch:" in workflow
    assert "schedule:" not in workflow
    assert "pull_request:" in workflow
    assert "Create governed external evidence PR" in workflow
    assert "automation/external-gap-" in workflow
    assert "gh pr create" in workflow
    assert "gh workflow run quality.yml" in workflow
    assert "HEAD:refs/heads/master" not in workflow
    assert "registry/knowledge-platform-p5-p10.json" in workflow
    assert "registry/durable-evidence-ledger.jsonl" in workflow
    assert "external evidence ratchet changed paths outside allowlist" in workflow
    assert "Requalify external ratchets after protection recovery" not in workflow
    assert "Retire closed external ratchet branch" in workflow
    assert "requirements-runtime.lock" in workflow
    assert "requirements-dev.lock" not in workflow
    assert "ratchet candidate CLI must never write the canonical registry" in cli
    for contract_id in (
        "external-evidence-receipt-v1",
        "external-evidence-intake-receipt-v1",
        "external-evidence-intake-host-binding-v1",
        "external-evidence-ratchet-proposal-v2",
    ):
        assert contract_id in cli


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
    assert boundary["root_observation_provenance_required"] is True
    assert (
        boundary[
            "root_observation_revision_must_match_evidence_source_revision"
        ]
        is True
    )
    assert boundary["trust_artifact_contracts"] == {
        "source_provenance": "external-evidence-source-provenance-v1",
        "producer_receipt": "external-pilot-evidence-producer-receipt-v1",
        "closure_receipt": "external-evidence-receipt-v1",
        "intake_receipt": "external-evidence-intake-receipt-v1",
        "host_binding": "external-evidence-intake-host-binding-v1",
        "ratchet_proposal": "external-evidence-ratchet-proposal-v2",
        "ratchet_verification": "external-evidence-ratchet-verification-v1",
    }


def test_ratchet_workflow_uploads_origin_before_creating_pr():
    import yaml

    root = Path(__file__).resolve().parents[1]
    path = root / ".github/workflows/external-evidence-ratchet-candidate.yml"
    payload = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    steps = payload["jobs"]["candidate"]["steps"]
    upload_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Upload bounded ratchet origin"
    )
    pr_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("name") == "Create governed external evidence PR"
    )
    assert upload_index < pr_index


def test_ratchet_workflow_delegates_protection_requalification_to_hosting():
    root = Path(__file__).resolve().parents[1]
    text = (
        root / ".github/workflows/external-evidence-ratchet-candidate.yml"
    ).read_text(encoding="utf-8")
    hosting = (
        root / ".github/workflows/hosting-posture-reconcile.yml"
    ).read_text(encoding="utf-8")

    assert "schedule:" not in text
    assert "Requalify external ratchets after protection recovery" not in text
    assert 'requalify_prefix "automation/external-gap-"' in hosting
    assert "Requalify bounded automation PRs after protection recovery" in hosting


def test_ratchet_builder_rejects_untrusted_retained_source_provenance(tmp_path: Path):
    paths = _fixture(tmp_path)
    intake = json.loads(paths[2].read_text(encoding="utf-8"))
    intake["source_provenance"]["source_run_head_branch"] = "feature/untrusted"
    _write(paths[2], intake)
    binding = json.loads(paths[3].read_text(encoding="utf-8"))
    binding["intake_receipt_sha256"] = hashlib.sha256(
        paths[2].read_bytes()
    ).hexdigest()
    _write(paths[3], binding)

    with pytest.raises(KnowledgeHubError, match="originate from master"):
        build_external_gap_ratchet_candidate(
            registry_path=paths[0],
            closure_receipt_path=paths[1],
            intake_receipt_path=paths[2],
            host_binding_path=paths[3],
        )

    intake["source_provenance"]["source_run_head_branch"] = "master"
    intake["source_provenance"]["source_run_event"] = "pull_request"
    _write(paths[2], intake)
    binding["intake_receipt_sha256"] = hashlib.sha256(
        paths[2].read_bytes()
    ).hexdigest()
    _write(paths[3], binding)
    with pytest.raises(KnowledgeHubError, match="event is not trusted"):
        build_external_gap_ratchet_candidate(
            registry_path=paths[0],
            closure_receipt_path=paths[1],
            intake_receipt_path=paths[2],
            host_binding_path=paths[3],
        )


def test_ratchet_builder_requires_positive_source_run_attempt(tmp_path: Path):
    paths = _fixture(tmp_path)
    intake = json.loads(paths[2].read_text(encoding="utf-8"))
    intake["source_provenance"]["source_run_attempt"] = 0
    _write(paths[2], intake)
    binding = json.loads(paths[3].read_text(encoding="utf-8"))
    binding["intake_receipt_sha256"] = hashlib.sha256(
        paths[2].read_bytes()
    ).hexdigest()
    _write(paths[3], binding)

    with pytest.raises(KnowledgeHubError, match="source provenance run attempt"):
        build_external_gap_ratchet_candidate(
            registry_path=paths[0],
            closure_receipt_path=paths[1],
            intake_receipt_path=paths[2],
            host_binding_path=paths[3],
        )


def test_external_ratchet_intermediate_artifacts_match_catalog_contracts(
    tmp_path: Path,
):
    paths = _fixture(tmp_path)
    root = Path(__file__).resolve().parents[1]

    closure = json.loads(paths[1].read_text(encoding="utf-8"))
    intake = json.loads(paths[2].read_text(encoding="utf-8"))
    binding = json.loads(paths[3].read_text(encoding="utf-8"))
    candidate, proposal = build_external_gap_ratchet_candidate(
        registry_path=paths[0],
        closure_receipt_path=paths[1],
        intake_receipt_path=paths[2],
        host_binding_path=paths[3],
    )

    cases = (
        (
            "external-evidence-source-provenance-v1",
            intake["source_provenance"],
        ),
        ("external-evidence-receipt-v1", closure),
        ("external-evidence-intake-receipt-v1", intake),
        ("external-evidence-intake-host-binding-v1", binding),
        ("external-evidence-ratchet-proposal-v2", proposal),
    )
    for contract_id, payload in cases:
        result = validate_instance(root, contract_id, payload)
        assert result["status"] == "pass", (
            contract_id,
            result["errors"],
        )
    assert candidate["external_closure_gaps"][0]["status"] == "closed"


def test_external_ratchet_workflow_validates_intermediate_contracts():
    root = Path(__file__).resolve().parents[1]
    intake_workflow = (
        root / ".github/workflows/external-evidence-intake.yml"
    ).read_text(encoding="utf-8")
    ratchet_workflow = (
        root / ".github/workflows/external-evidence-ratchet-candidate.yml"
    ).read_text(encoding="utf-8")
    cli = (
        root / "tools/codex_assets/knowledge_hub/external_evidence_cli.py"
    ).read_text(encoding="utf-8")

    assert "external-evidence-source-provenance-v1" in intake_workflow
    assert "external-evidence-intake-receipt-v1" in intake_workflow
    assert "external-evidence-receipt-v1" in cli
    assert "external-evidence-intake-host-binding-v1" in ratchet_workflow
    assert "external-evidence-ratchet-proposal-v2" in ratchet_workflow


def test_ratchet_builder_rejects_root_revision_drift(tmp_path: Path):
    paths = _fixture(tmp_path)
    intake = json.loads(paths[2].read_text(encoding="utf-8"))
    intake["root_observation_provenance"]["source_run_head_sha"] = "9" * 40
    _write(paths[2], intake)
    binding = json.loads(paths[3].read_text(encoding="utf-8"))
    binding["intake_receipt_sha256"] = hashlib.sha256(
        paths[2].read_bytes()
    ).hexdigest()
    _write(paths[3], binding)

    with pytest.raises(
        KnowledgeHubError,
        match="root observation revision does not match",
    ):
        build_external_gap_ratchet_candidate(
            registry_path=paths[0],
            closure_receipt_path=paths[1],
            intake_receipt_path=paths[2],
            host_binding_path=paths[3],
        )


def test_ratchet_builder_rejects_cross_repository_root_provenance(
    tmp_path: Path,
):
    paths = _fixture(tmp_path)
    intake = json.loads(paths[2].read_text(encoding="utf-8"))
    intake["root_observation_provenance"]["repository"] = "other/repository"
    _write(paths[2], intake)
    binding = json.loads(paths[3].read_text(encoding="utf-8"))
    binding["intake_receipt_sha256"] = hashlib.sha256(
        paths[2].read_bytes()
    ).hexdigest()
    _write(paths[3], binding)

    with pytest.raises(
        KnowledgeHubError,
        match="root observation repository differs",
    ):
        build_external_gap_ratchet_candidate(
            registry_path=paths[0],
            closure_receipt_path=paths[1],
            intake_receipt_path=paths[2],
            host_binding_path=paths[3],
        )


def test_external_ratchet_hosted_refs_dedupe_manual_root_and_source(
    tmp_path: Path,
):
    paths = _fixture(tmp_path)
    intake = json.loads(paths[2].read_text(encoding="utf-8"))
    intake["root_observation_provenance"] = dict(
        intake["source_provenance"]
    )
    _write(paths[2], intake)
    binding = json.loads(paths[3].read_text(encoding="utf-8"))
    binding["intake_receipt_sha256"] = hashlib.sha256(
        paths[2].read_bytes()
    ).hexdigest()
    _write(paths[3], binding)

    candidate, _ = build_external_gap_ratchet_candidate(
        registry_path=paths[0],
        closure_receipt_path=paths[1],
        intake_receipt_path=paths[2],
        host_binding_path=paths[3],
    )
    gap = next(
        row
        for row in candidate["external_closure_gaps"]
        if row["id"] == GAP
    )

    assert len(gap["evidence_refs"]) == len(set(gap["evidence_refs"]))
