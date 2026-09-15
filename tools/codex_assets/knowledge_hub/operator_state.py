"""Read-only operator projection for the Knowledge Hub human control plane."""

from __future__ import annotations

import pathlib
from typing import Any, Dict, Mapping

from .common import KnowledgeHubError, parse_json_output, run_rtk, utc_timestamp
from .operator_actions import HUMAN_EXECUTION_CLASSES, build_action_queue, project_actions
from .product_gate_support import _project_readiness
from .terminal_closure import DEFAULT_POLICY, _external_gaps, _load_object, evaluate_terminal_closure


def _status_summary(root: pathlib.Path) -> Dict[str, Any]:
    result = run_rtk(
        root,
        ["bash", "tools/knowledge-status.sh", "--summary-json"],
        timeout=120,
        accepted_exit_codes=(0, 1, 2),
    )
    try:
        payload = parse_json_output(result)
    except Exception as exc:
        return {
            "status": "unavailable",
            "read_only": True,
            "error": str(exc),
            "exit_code": result.get("exit_code", -1),
        }
    return dict(payload)


def _external_state(root: pathlib.Path) -> Dict[str, Any]:
    try:
        policy = _load_object(root / DEFAULT_POLICY, "terminal closure policy")
        gaps = _external_gaps(root, policy)
    except KnowledgeHubError as exc:
        return {
            "status": "unavailable",
            "open_count": 0,
            "open_gaps": [],
            "error": str(exc),
        }
    return {
        "status": "pass" if not gaps else "needs-review",
        "open_count": len(gaps),
        "open_gaps": gaps,
    }


def _terminal_state(root: pathlib.Path) -> Dict[str, Any]:
    try:
        payload = evaluate_terminal_closure(root)
    except KnowledgeHubError as exc:
        return {
            "status": "not-evaluated",
            "terminal": False,
            "error": str(exc),
        }
    return {
        "status": str(payload.get("status", "")),
        "terminal": bool(payload.get("terminal", False)),
        "blockers": list(payload.get("blockers", [])),
        "branch_gc": payload.get("branch_gc", {}),
    }


def _project_projection(row: Mapping[str, Any]) -> Dict[str, Any]:
    contract = row.get("evidence_contract", {})
    if not isinstance(contract, Mapping):
        contract = {}
    missing = sorted(str(value) for value in contract.get("missing_fields", []) if str(value))
    invalid = sorted(str(value) for value in contract.get("invalid_fields", []) if str(value))
    attention = []
    if row.get("owner_boundary_status") != "ready":
        attention.append("owner-boundary")
    if row.get("evidence_field_status") == "complete-awaiting-declaration":
        attention.append("owner-declaration")
    attention.extend("missing:{}".format(value) for value in missing)
    attention.extend("invalid:{}".format(value) for value in invalid)
    projected = {
        "project_id": str(row.get("project_id", "")),
        "name": str(row.get("name", row.get("project_id", ""))),
        "evidence_profile": str(row.get("evidence_profile", "")),
        "evidence_status": str(row.get("evidence_status", "")),
        "evidence_field_status": str(row.get("evidence_field_status", "")),
        "owner_boundary_status": str(row.get("owner_boundary_status", "")),
        "source_mapping_ready": bool(row.get("source_mapping_ready", False)),
        "missing_fields": missing,
        "invalid_fields": invalid,
        "attention": attention,
    }
    actions = project_actions(projected)
    action_classes = sorted({str(value.get("execution_class", "")) for value in actions})
    projected["operator_actions"] = actions
    projected["action_classes"] = action_classes
    projected["machine_candidate"] = "machine-discovery" in action_classes
    projected["needs_human_attention"] = any(
        value in HUMAN_EXECUTION_CLASSES for value in action_classes
    )
    return projected


def _readiness_projection(readiness: Mapping[str, Any]) -> Dict[str, Any]:
    projects = [
        _project_projection(row)
        for row in readiness.get("rows", [])
        if isinstance(row, Mapping)
    ]
    projects.sort(
        key=lambda row: (
            not row["needs_human_attention"],
            not row["machine_candidate"],
            row["project_id"],
        )
    )
    return {
        "project_count": int(readiness.get("project_count", 0) or 0),
        "structural_ready_count": int(readiness.get("structural_ready_count", 0) or 0),
        "source_mapping_ready_count": int(readiness.get("source_mapping_ready_count", 0) or 0),
        "owner_boundary_ready_count": int(readiness.get("owner_boundary_ready_count", 0) or 0),
        "evidence_field_complete_count": int(readiness.get("evidence_field_complete_count", 0) or 0),
        "evidence_ready_count": int(readiness.get("evidence_ready_count", 0) or 0),
        "human_attention_count": sum(1 for row in projects if row["needs_human_attention"]),
        "machine_candidate_project_count": sum(1 for row in projects if row["machine_candidate"]),
        "projects": projects,
    }


def build_operator_state(root: pathlib.Path) -> Dict[str, Any]:
    readiness = _readiness_projection(_project_readiness(root))
    status = _status_summary(root)
    external = _external_state(root)
    terminal = _terminal_state(root)
    action_queue = build_action_queue(readiness["projects"], external)
    next_actions = list(status.get("next_actions_zh", []))[:20]
    return {
        "schema_version": 1,
        "projection": "knowledge-operator-state-v1",
        "generated_at": utc_timestamp(),
        "read_only": True,
        "status": str(status.get("status", "unavailable")),
        "status_summary": status,
        "readiness": readiness,
        "action_queue": action_queue,
        "external_closure": external,
        "terminal_closure": terminal,
        "next_actions_zh": next_actions,
    }
