"""Deterministic critical-maintenance notification identity."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, Tuple

from .common import KnowledgeHubError

MAX_SECURITY_ROWS = 5000
MAX_POLICY_ERRORS = 256
MAX_VALUE_CHARS = 1024


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return value


def _bounded_text(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) > MAX_VALUE_CHARS:
        raise KnowledgeHubError("{} must be a bounded string".format(label))
    return value


def _security_rows(triage: Mapping[str, Any]) -> List[Tuple[str, str, str]]:
    group = _mapping(triage.get("security"), "security group")
    rows = group.get("rows")
    if not isinstance(rows, list) or len(rows) > MAX_SECURITY_ROWS:
        raise KnowledgeHubError("security rows must be a bounded list")
    normalized = []
    for row in rows:
        item = _mapping(row, "security row")
        normalized.append((
            _bounded_text(item.get("item_id", ""), "security item_id"),
            _bounded_text(item.get("review_after", ""), "security review_after"),
            _bounded_text(item.get("selection_reason", ""), "security selection_reason"),
        ))
    if len(set(normalized)) != len(normalized):
        raise KnowledgeHubError("security rows must not contain exact duplicates")
    return sorted(normalized)


def _hard_caps(growth: Mapping[str, Any]) -> List[Tuple[str, str, str]]:
    regressions = growth.get("regressions")
    if not isinstance(regressions, list) or len(regressions) > MAX_SECURITY_ROWS:
        raise KnowledgeHubError("growth regressions must be a bounded list")
    rows = []
    for raw in regressions:
        row = _mapping(raw, "growth regression")
        if row.get("type") != "data-growth-hard-cap":
            continue
        rows.append((
            _bounded_text(row.get("type", ""), "regression type"),
            _bounded_text(row.get("path", ""), "regression path"),
            _bounded_text(row.get("reason", ""), "regression reason"),
        ))
    return sorted(set(rows))


def _policy_errors(review: Mapping[str, Any]) -> List[str]:
    errors = review.get("errors")
    if not isinstance(errors, list) or len(errors) > MAX_POLICY_ERRORS:
        raise KnowledgeHubError("review errors must be a bounded list")
    return sorted({_bounded_text(value, "review error") for value in errors})


def critical_notification_decision(
    triage: Mapping[str, Any],
    growth: Mapping[str, Any],
    review: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build an order-independent identity for human-required state only."""

    triage = _mapping(triage, "triage")
    growth = _mapping(growth, "growth")
    review = _mapping(review, "review")
    security = _security_rows(triage)
    hard_caps = _hard_caps(growth)
    policy_errors = _policy_errors(review)
    growth_failed = growth.get("status") == "fail"
    if not isinstance(growth.get("status"), str):
        raise KnowledgeHubError("growth status must be a string")
    payload = {
        "schema_version": 1,
        "security": security,
        "hard_caps": hard_caps,
        "policy_errors": policy_errors,
        "growth_failed": growth_failed,
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return {
        "schema_version": 1,
        "human_required": bool(security or hard_caps or policy_errors or growth_failed),
        "notification_fingerprint": "sha256:" + hashlib.sha256(encoded).hexdigest(),
        "security_critical_count": len(security),
        "hard_cap_count": len(hard_caps),
        "policy_error_count": len(policy_errors) + int(growth_failed),
    }
