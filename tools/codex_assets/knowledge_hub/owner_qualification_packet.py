"""Deterministic owner/project qualification packet from canonical readiness."""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any, Dict, Mapping

from .product_gate_support import _project_readiness

PROJECTION = "knowledge-hub-owner-qualification-packet-v1"
_OWNER_ONLY_FIELDS = {"owner_ref", "member_project_ids"}


def _fingerprint(value: Mapping[str, Any]) -> str:
    raw = json.dumps(
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _row(value: Mapping[str, Any]) -> Dict[str, Any]:
    contract = value.get("evidence_contract", {})
    if not isinstance(contract, Mapping):
        contract = {}
    missing = sorted(
        str(item) for item in contract.get("missing_fields", []) if str(item)
    )
    invalid = sorted(
        str(item) for item in contract.get("invalid_fields", []) if str(item)
    )
    evidence_status = str(value.get("evidence_status", ""))
    field_status = str(value.get("evidence_field_status", ""))
    owner_status = str(value.get("owner_boundary_status", ""))
    real_missing = [
        field for field in missing if field not in _OWNER_ONLY_FIELDS
    ]
    real_invalid = [
        field for field in invalid if field not in _OWNER_ONLY_FIELDS
    ]
    return {
        "project_id": str(value.get("project_id", "")),
        "name": str(value.get("name", value.get("project_id", ""))),
        "evidence_profile": str(value.get("evidence_profile", "")),
        "evidence_status": evidence_status,
        "evidence_field_status": field_status,
        "owner_boundary_status": owner_status,
        "decision_owner_status": str(value.get("decision_owner_status", "")),
        "owner_ref_status": str(value.get("owner_ref_status", "")),
        "source_mapping_ready": bool(value.get("source_mapping_ready", False)),
        "missing_fields": missing,
        "invalid_fields": invalid,
        "owner_declaration_pending": (
            field_status == "complete-awaiting-declaration"
            and evidence_status != "ready"
        ),
        "owner_boundary_pending": owner_status != "ready",
        "real_evidence_missing_fields": real_missing,
        "real_evidence_invalid_fields": real_invalid,
        "real_evidence_pending": bool(real_missing or real_invalid),
    }


def build_owner_qualification_packet_from_readiness(
    readiness: Mapping[str, Any],
) -> Dict[str, Any]:
    rows = [
        _row(row)
        for row in readiness.get("rows", [])
        if isinstance(row, Mapping)
    ]
    rows.sort(key=lambda row: row["project_id"])
    project_count = int(readiness.get("project_count", len(rows)) or 0)
    structural = int(readiness.get("structural_ready_count", 0) or 0)
    source = int(readiness.get("source_mapping_ready_count", 0) or 0)
    owner = int(readiness.get("owner_boundary_ready_count", 0) or 0)
    field_complete = int(
        readiness.get("evidence_field_complete_count", 0) or 0
    )
    evidence = int(readiness.get("evidence_ready_count", 0) or 0)
    route_failures = int(readiness.get("route_matrix_failure_count", 0) or 0)

    owner_declaration = [
        row["project_id"] for row in rows if row["owner_declaration_pending"]
    ]
    owner_boundary = [
        row["project_id"] for row in rows if row["owner_boundary_pending"]
    ]
    real_evidence = [
        row["project_id"] for row in rows if row["real_evidence_pending"]
    ]
    qualification_pass = bool(
        project_count
        and structural == project_count
        and source == project_count
        and owner == project_count
        and field_complete == project_count
        and evidence == project_count
        and route_failures == 0
    )
    material: Dict[str, Any] = {
        "schema_version": 1,
        "projection": PROJECTION,
        "status": "pass" if qualification_pass else "needs-review",
        "read_only": True,
        "canonical_write_performed": False,
        "owner_decision_generated": False,
        "qualification_pass": qualification_pass,
        "summary": {
            "project_count": project_count,
            "structural_ready_count": structural,
            "source_mapping_ready_count": source,
            "owner_boundary_ready_count": owner,
            "evidence_field_complete_count": field_complete,
            "evidence_ready_count": evidence,
            "route_matrix_failure_count": route_failures,
        },
        "owner_declaration_pending_count": len(owner_declaration),
        "owner_declaration_projects": owner_declaration,
        "owner_boundary_pending_count": len(owner_boundary),
        "owner_boundary_projects": owner_boundary,
        "real_evidence_pending_project_count": len(real_evidence),
        "real_evidence_projects": real_evidence,
        "rows": rows,
    }
    material["packet_fingerprint"] = _fingerprint(material)
    return material


def build_owner_qualification_packet(root: pathlib.Path) -> Dict[str, Any]:
    return build_owner_qualification_packet_from_readiness(
        _project_readiness(pathlib.Path(root).resolve())
    )
