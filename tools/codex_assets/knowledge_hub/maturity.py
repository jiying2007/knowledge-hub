"""Independent product maturity axes."""

from __future__ import annotations

from typing import Any, Dict

from .output_contract import canonical_status


def evaluate_maturity_axes(
    *,
    platform_status: str,
    content_status: str,
    project_count: int,
    project_evidence_ready_count: int,
    owner_gate_open_count: int,
    review_queue_pending_count: int,
    adoption_ready: bool,
    local_delivery_complete: bool,
    remote_published: bool,
    offsite_restore_verified: bool,
) -> Dict[str, Any]:
    """Compute axes without allowing project evidence to rewrite platform health."""

    platform = canonical_status(platform_status)
    content = canonical_status(content_status)
    project_ready = (
        project_count > 0 and project_evidence_ready_count == project_count
    )
    project_status = "pass" if project_ready else "needs-review"
    if local_delivery_complete and remote_published and offsite_restore_verified:
        delivery_status = "pass"
    else:
        delivery_status = "needs-review"
    terminal = bool(
        platform == "pass"
        and content == "pass"
        and project_ready
        and owner_gate_open_count == 0
        and review_queue_pending_count == 0
        and adoption_ready
        and delivery_status == "pass"
    )
    if platform == "blocked":
        overall = "blocked"
    elif platform == "needs-fix" or content == "needs-fix":
        overall = "needs-fix"
    elif terminal:
        overall = "pass"
    else:
        overall = "needs-review"
    return {
        "schema_version": 2,
        "platform": {
            "status": platform,
            "independent_from_project_evidence": True,
        },
        "content": {
            "status": content,
            "owner_gate_open_count": owner_gate_open_count,
            "review_queue_pending_count": review_queue_pending_count,
        },
        "project_evidence": {
            "status": project_status,
            "project_count": project_count,
            "ready_count": project_evidence_ready_count,
            "coverage": round(
                project_evidence_ready_count / float(max(1, project_count)),
                4,
            ),
        },
        "delivery": {
            "status": delivery_status,
            "local_delivery_complete": local_delivery_complete,
            "remote_published": remote_published,
            "offsite_restore_verified": offsite_restore_verified,
        },
        "adoption": {
            "status": "pass" if adoption_ready else "needs-review",
            "ready": adoption_ready,
        },
        "status": overall,
        "terminal": terminal,
    }
