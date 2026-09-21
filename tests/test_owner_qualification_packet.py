from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.owner_qualification_packet import (
    build_owner_qualification_packet_from_readiness,
)
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def _row(
    project_id,
    *,
    evidence_status="contract-evidence-pending",
    field_status="incomplete",
    owner_status="pending",
    decision_owner_status="pending",
    owner_ref_status="pending",
    source_mapping_ready=False,
    missing=None,
    invalid=None,
):
    return {
        "project_id": project_id,
        "name": project_id,
        "evidence_profile": "software-tool",
        "evidence_status": evidence_status,
        "evidence_field_status": field_status,
        "owner_boundary_status": owner_status,
        "decision_owner_status": decision_owner_status,
        "owner_ref_status": owner_ref_status,
        "source_mapping_ready": source_mapping_ready,
        "evidence_contract": {
            "missing_fields": list(missing or []),
            "invalid_fields": list(invalid or []),
        },
    }


def _readiness():
    return {
        "project_count": 3,
        "structural_ready_count": 3,
        "source_mapping_ready_count": 2,
        "owner_boundary_ready_count": 2,
        "evidence_field_complete_count": 2,
        "evidence_ready_count": 1,
        "route_matrix_failure_count": 0,
        "rows": [
            _row(
                "complete-project",
                field_status="complete-awaiting-declaration",
                owner_status="ready",
                decision_owner_status="ready",
                owner_ref_status="ready",
                source_mapping_ready=True,
            ),
            _row(
                "missing-real-evidence",
                missing=["owner_ref", "source_refs", "device_refs"],
                source_mapping_ready=False,
            ),
            _row(
                "ready-project",
                evidence_status="ready",
                field_status="complete-awaiting-declaration",
                owner_status="ready",
                decision_owner_status="ready",
                owner_ref_status="ready",
                source_mapping_ready=True,
            ),
        ],
    }


def test_owner_packet_classifies_only_real_remaining_boundaries():
    packet = build_owner_qualification_packet_from_readiness(_readiness())

    assert packet["status"] == "needs-review"
    assert packet["qualification_pass"] is False
    assert packet["owner_decision_generated"] is False
    assert packet["canonical_write_performed"] is False

    assert packet["owner_declaration_projects"] == ["complete-project"]
    assert packet["owner_boundary_projects"] == ["missing-real-evidence"]
    assert packet["real_evidence_projects"] == ["missing-real-evidence"]

    rows = {row["project_id"]: row for row in packet["rows"]}
    assert rows["complete-project"]["owner_declaration_pending"] is True
    assert rows["complete-project"]["real_evidence_pending"] is False
    assert rows["missing-real-evidence"]["owner_boundary_pending"] is True
    assert rows["missing-real-evidence"]["real_evidence_missing_fields"] == [
        "device_refs",
        "source_refs",
    ]
    assert rows["ready-project"]["owner_declaration_pending"] is False
    assert rows["ready-project"]["owner_boundary_pending"] is False


def test_owner_packet_is_deterministic_and_schema_valid():
    first = build_owner_qualification_packet_from_readiness(_readiness())
    second = build_owner_qualification_packet_from_readiness(_readiness())

    assert first == second
    assert first["packet_fingerprint"].startswith("sha256:")
    assert (
        validate_instance(
            repository_root(),
            "owner-qualification-packet-v1",
            first,
        )["status"]
        == "pass"
    )


def test_owner_packet_pass_requires_all_projects_fully_ready():
    readiness = {
        "project_count": 1,
        "structural_ready_count": 1,
        "source_mapping_ready_count": 1,
        "owner_boundary_ready_count": 1,
        "evidence_field_complete_count": 1,
        "evidence_ready_count": 1,
        "route_matrix_failure_count": 0,
        "rows": [
            _row(
                "ready",
                evidence_status="ready",
                field_status="complete-awaiting-declaration",
                owner_status="ready",
                decision_owner_status="ready",
                owner_ref_status="ready",
                source_mapping_ready=True,
            )
        ],
    }
    packet = build_owner_qualification_packet_from_readiness(readiness)

    assert packet["status"] == "pass"
    assert packet["qualification_pass"] is True
    assert packet["owner_declaration_pending_count"] == 0
    assert packet["owner_boundary_pending_count"] == 0
    assert packet["real_evidence_pending_project_count"] == 0
