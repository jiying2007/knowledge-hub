"""Build deterministic, non-canonical AI maintenance triage artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, Tuple

from .common import KnowledgeHubError

PROJECTION = "knowledge-hub-ai-maintenance-triage-v1"
PACKET_PROJECTION = "knowledge-hub-governance-review-packet-v1"

_ALLOWED_CLASSES = {"ordinary", "governance-critical", "security-critical"}
_ROW_FIELDS = (
    "item_id",
    "path",
    "owner",
    "status",
    "domain",
    "source_id",
    "review_after",
    "days_until_review",
    "review_class",
    "stale_severity",
    "ai_first_action",
    "selection_reason",
)


def _object(value: object, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return dict(value)


def _digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _bounded_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {field: row.get(field, "") for field in _ROW_FIELDS}


def _stale_rows(review: Mapping[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    rows = review.get("rows", [])
    if not isinstance(rows, list):
        raise KnowledgeHubError("review rows must be a list")
    grouped: Dict[str, List[Dict[str, Any]]] = {
        name: [] for name in sorted(_ALLOWED_CLASSES)
    }
    for raw in rows:
        if not isinstance(raw, Mapping) or raw.get("row_type") != "stale_item":
            continue
        review_class = str(raw.get("review_class", "ordinary"))
        if review_class not in _ALLOWED_CLASSES:
            raise KnowledgeHubError(
                "unsupported review class: {}".format(review_class)
            )
        grouped[review_class].append(_bounded_row(raw))
    for values in grouped.values():
        values.sort(
            key=lambda row: (
                str(row.get("review_after", "")),
                str(row.get("item_id", "")),
            )
        )
    return grouped


def build_maintenance_triage(
    review: Mapping[str, Any],
    growth: Mapping[str, Any],
    health: Mapping[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    review_obj = _object(review, "review report")
    growth_obj = _object(growth, "growth report")
    health_obj = _object(health, "health report")
    grouped = _stale_rows(review_obj)

    ordinary = grouped["ordinary"]
    governance = grouped["governance-critical"]
    security = grouped["security-critical"]
    input_digests = {
        "review": _digest(review_obj),
        "growth": _digest(growth_obj),
        "health": _digest(health_obj),
    }

    triage = {
        "schema_version": 1,
        "projection": PROJECTION,
        "status": "pass",
        "as_of": str(review_obj.get("today", "")),
        "read_only": True,
        "canonical_write_performed": False,
        "input_digests": input_digests,
        "ordinary": {
            "action": "machine-triaged-no-semantic-write",
            "count": len(ordinary),
            "rows": ordinary,
        },
        "governance": {
            "action": "machine-review-packet-generated",
            "count": len(governance),
            "rows": governance,
        },
        "security": {
            "action": "human-review-required",
            "count": len(security),
            "rows": security,
        },
        "health_status": str(health_obj.get("status", "unknown")),
        "data_growth_status": str(growth_obj.get("status", "unknown")),
    }
    packet = {
        "schema_version": 1,
        "projection": PACKET_PROJECTION,
        "status": "ready" if governance else "no-change",
        "as_of": str(review_obj.get("today", "")),
        "read_only": True,
        "canonical_write_performed": False,
        "selection_is_authorization": False,
        "final_semantic_decision_made": False,
        "input_digests": input_digests,
        "review_class": "governance-critical",
        "row_count": len(governance),
        "rows": governance,
        "next_boundary": (
            "machine-review"
            if governance
            else "none"
        ),
    }
    return triage, packet
