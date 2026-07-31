"""Bounded projection for the product final gate."""

from __future__ import annotations

from typing import Any, Dict, Mapping


def _blockers(payload: Mapping[str, Any]) -> list[Dict[str, Any]]:
    allowed = (
        "id",
        "check",
        "severity",
        "gap_type",
        "codex_auto_can_complete",
        "requires_owner_decision",
        "source_id",
        "field",
    )
    return [
        {key: row.get(key) for key in allowed if key in row}
        for row in payload.get("blockers", [])
        if isinstance(row, Mapping)
    ]


def _adoption(payload: Mapping[str, Any]) -> Dict[str, Any]:
    adoption = payload.get("adoption", {}) or {}
    metrics = (payload.get("operational_readiness", {}) or {}).get(
        "local_metrics", {}
    ) or {}
    usage = metrics.get("usage", {}) or {}
    retrieval = metrics.get("retrieval", {}) or {}
    return {
        "ready": adoption.get("ready", False),
        "evaluable": adoption.get("evaluable", False),
        "invocation_count": usage.get("invocation_count", 0),
        "feedback_count": retrieval.get("feedback_count", 0),
        "observation_days": usage.get("observation_days", 0),
    }


def product_gate_summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Remove heavy evidence rows while preserving all maturity decisions."""

    blockers = _blockers(payload)
    content = payload.get("content_readiness", {}) or {}
    project = content.get("project_readiness", {}) or {}
    owner = payload.get("owner_and_real_evidence", {}) or {}
    delivery = payload.get("delivery_readiness", {}) or {}
    return {
        "schema_version": 4,
        "projection": "product-final-gate-summary-v4",
        **{
            key: payload.get(key, "")
            for key in (
                "generated_at",
                "as_of",
                "final_profile",
                "regression_suite",
            )
        },
        "status": payload.get("status", "blocked"),
        "terminal": payload.get("terminal", False),
        "maturity_axes": payload.get("maturity_axes", {}),
        "hard_checks": (payload.get("platform_status", {}) or {}).get(
            "hard_checks", {}
        ),
        "blocker_count": len(blockers),
        "blockers": blockers,
        "content": {
            "status": content.get("status", ""),
            **{
                key: project.get(key, 0)
                for key in (
                    "project_count",
                    "structural_ready_count",
                    "evidence_ready_count",
                    "evidence_field_complete_count",
                )
            },
        },
        "owner_and_real_evidence": {
            "status": owner.get("status", ""),
            "owner_gate_open_count": owner.get("owner_gate_open_count", 0),
            "review_queue_pending_count": owner.get(
                "review_queue_pending_count", 0
            ),
            "pending_project_count": len(owner.get("pending_project_ids", [])),
            "pending_specialized_owner_candidate_count": owner.get(
                "pending_specialized_owner_candidate_count", 0
            ),
        },
        "delivery": {
            key: delivery.get(key, False if key != "status" else "")
            for key in (
                "status",
                "local_delivery_complete",
                "remote_published",
                "offsite_restore_verified",
                "engineering_quality_ready",
                "full_regression_ready",
            )
        },
        "adoption": _adoption(payload),
        "snapshot": payload.get("snapshot", ""),
        "conclusion_zh": payload.get("conclusion_zh", ""),
        "next_actions_zh": list(payload.get("next_actions_zh", []))[:10],
        "duration_ms": payload.get("duration_ms", 0),
    }
