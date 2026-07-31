"""Bounded projection for the large status dashboard."""

from __future__ import annotations

from typing import Any, Dict, Mapping


def status_summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    registry = payload.get("registry", {}) or {}
    sources = payload.get("sources", {}) or {}
    queues = payload.get("review_queues", {}) or {}
    queue_summary = queues.get("summary", {}) or {}
    owner = payload.get("owner_gates", {}) or {}
    blockers = payload.get("strict_blockers", []) or []
    return {
        "schema_version": 1,
        "projection": "knowledge-status-summary-v1",
        "status": payload.get("status", ""),
        "status_contract": payload.get("status_contract", {}),
        "read_only": True,
        "strict": payload.get("strict", False),
        "generated_at": payload.get("generated_at", ""),
        "today": payload.get("today", ""),
        "knowledge_check": payload.get("knowledge_check", {}),
        "registry": {
            "item_count": registry.get("item_count", 0),
            "by_status": registry.get("by_status", {}),
            "stale_review_after_count": registry.get(
                "stale_review_after_count", 0
            ),
        },
        "sources": {
            "registered_count": sources.get("registered_count", 0),
            "stale_review_after_count": sources.get(
                "stale_review_after_count", 0
            ),
            "source_runtime_status": (
                sources.get("source_runtime", {}) or {}
            ).get("status", ""),
        },
        "review_queues": {
            "status": queues.get("status", ""),
            "total_pending_count": queue_summary.get("total_pending_count", 0),
            "ai_generated_pending_count": queue_summary.get(
                "ai_generated_pending_count", 0
            ),
            "external_source_pending_count": queue_summary.get(
                "external_source_pending_count", 0
            ),
        },
        "owner_gates": {
            "open_count": owner.get("open_count", 0),
            "active_exposure_count": owner.get("active_exposure_count", 0),
            "owner_ready_package_coverage": owner.get(
                "owner_ready_package_coverage", ""
            ),
        },
        "strict_blocker_count": len(blockers),
        "strict_blockers": [
            {
                "id": row.get("id", ""),
                "severity": row.get("severity", ""),
                "count": row.get("count", 0),
                "summary_zh": row.get("summary_zh", ""),
            }
            for row in blockers[:20]
            if isinstance(row, Mapping)
        ],
        "next_actions_zh": list(payload.get("next_actions_zh", []))[:10],
        "final_gate_command": payload.get("final_gate_command", ""),
    }
