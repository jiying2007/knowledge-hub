"""Build deterministic, non-canonical AI maintenance triage artifacts."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any, Dict, List, Mapping, Tuple

from .common import KnowledgeHubError

PROJECTION = "knowledge-hub-ai-maintenance-triage-v1"
PACKET_PROJECTION = "knowledge-hub-governance-review-packet-v1"
MAX_REVIEW_ROWS = 5000
MAX_FIELD_CHARS = 4096
MAX_REPORT_BYTES = 8 * 1024 * 1024

_ALLOWED_CLASSES = {"ordinary", "governance-critical", "security-critical"}
_ROW_FIELDS = (
    "item_id", "path", "owner", "status", "domain", "source_id",
    "review_after", "days_until_review", "review_class", "stale_severity",
    "ai_first_action", "selection_reason",
)
_NON_STALE_TYPES = {"near_due_item", "stale_source", "near_due_source", "open_owner_gate"}


def _object(value: object, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return dict(value)


def _digest(value: Mapping[str, Any]) -> str:
    try:
        raw = json.dumps(
            dict(value), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise KnowledgeHubError("maintenance report must contain finite JSON values") from exc
    if len(raw) > MAX_REPORT_BYTES:
        raise KnowledgeHubError("maintenance report exceeds byte budget")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _date(value: Any, label: str) -> dt.date:
    if not isinstance(value, str):
        raise KnowledgeHubError("{} must use YYYY-MM-DD".format(label))
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise KnowledgeHubError("{} must use YYYY-MM-DD".format(label)) from exc
    if parsed.isoformat() != value:
        raise KnowledgeHubError("{} must use YYYY-MM-DD".format(label))
    return parsed


def _bounded_row(row: Mapping[str, Any], today: dt.date) -> Dict[str, Any]:
    result = {field: row.get(field, "") for field in _ROW_FIELDS}
    result["review_class"] = row.get("review_class", "ordinary")
    for field, value in result.items():
        if field == "days_until_review":
            if type(value) is not int:
                raise KnowledgeHubError("days_until_review must be a real integer")
        elif not isinstance(value, str) or len(value) > MAX_FIELD_CHARS:
            raise KnowledgeHubError("{} must be a bounded string".format(field))
    if not result["item_id"].strip() or not result["path"].strip():
        raise KnowledgeHubError("stale item requires item_id and path")
    review_date = _date(result["review_after"], "review_after")
    days = (review_date - today).days
    if days >= 0 or result["days_until_review"] != days:
        raise KnowledgeHubError("stale item date and days_until_review disagree")
    return result


def _stale_rows(review: Mapping[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    if review.get("status") not in ("pass", "report-only"):
        raise KnowledgeHubError("review report is incomplete or failed")
    errors = review.get("errors")
    if not isinstance(errors, list) or errors:
        raise KnowledgeHubError("review report contains errors")
    today = _date(review.get("today"), "review today")
    rows = review.get("rows")
    if not isinstance(rows, list) or len(rows) > MAX_REVIEW_ROWS:
        raise KnowledgeHubError("review rows must be a bounded list")
    grouped: Dict[str, List[Dict[str, Any]]] = {name: [] for name in sorted(_ALLOWED_CLASSES)}
    seen: Dict[str, Dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise KnowledgeHubError("review row must be an object")
        row_type = raw.get("row_type")
        if not isinstance(row_type, str):
            raise KnowledgeHubError("review row requires row_type")
        if row_type in _NON_STALE_TYPES:
            continue
        if row_type != "stale_item":
            raise KnowledgeHubError("unsupported review row_type")
        review_class = raw.get("review_class", "ordinary")
        if not isinstance(review_class, str) or review_class not in _ALLOWED_CLASSES:
            raise KnowledgeHubError("unsupported review class: {}".format(review_class))
        row = _bounded_row(raw, today)
        item_id = row["item_id"]
        if item_id in seen:
            if seen[item_id] != row:
                raise KnowledgeHubError("conflicting review rows for the same item_id")
            continue
        seen[item_id] = row
        grouped[review_class].append(row)
    for values in grouped.values():
        values.sort(key=lambda row: (row["review_after"], row["item_id"]))
    return grouped


def build_maintenance_triage(
    review: Mapping[str, Any], growth: Mapping[str, Any], health: Mapping[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    review_obj = _object(review, "review report")
    growth_obj = _object(growth, "growth report")
    health_obj = _object(health, "health report")
    grouped = _stale_rows(review_obj)
    ordinary = grouped["ordinary"]
    governance = grouped["governance-critical"]
    security = grouped["security-critical"]
    input_digests = {
        "review": _digest(review_obj), "growth": _digest(growth_obj), "health": _digest(health_obj),
    }
    # A failed health/growth finding is not a malformed review. Preserve it for
    # the existing human/dependency routing; do not erase legitimate alerts.
    triage = {
        "schema_version": 1, "projection": PROJECTION, "status": "pass",
        "as_of": str(review_obj["today"]), "read_only": True,
        "canonical_write_performed": False, "input_digests": input_digests,
        "ordinary": {"action": "machine-triaged-no-semantic-write", "count": len(ordinary), "rows": ordinary},
        "governance": {"action": "machine-review-packet-generated", "count": len(governance), "rows": governance},
        "security": {"action": "human-review-required", "count": len(security), "rows": security},
        "health_status": str(health_obj.get("status", "unknown")),
        "data_growth_status": str(growth_obj.get("status", "unknown")),
    }
    packet = {
        "schema_version": 1, "projection": PACKET_PROJECTION,
        "status": "ready" if governance else "no-change",
        "as_of": str(review_obj["today"]), "read_only": True,
        "canonical_write_performed": False, "selection_is_authorization": False,
        "final_semantic_decision_made": False, "input_digests": input_digests,
        "review_class": "governance-critical", "row_count": len(governance), "rows": governance,
        "next_boundary": "machine-review" if governance else "none",
    }
    return triage, packet
