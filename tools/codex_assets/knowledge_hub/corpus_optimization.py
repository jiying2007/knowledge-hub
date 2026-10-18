"""Deterministic, read-only optimization routing for every governed corpus item.

This is a projection of canonical corpus-review observations, not a second
knowledge source, semantic review, or permission to edit any knowledge item.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from typing import Any, Dict, Mapping

from .common import KnowledgeHubError

PROJECTION = "knowledge-hub.corpus-optimization/v1"
MAX_ROWS = 5000
MAX_PLAN_BYTES = 2 * 1024 * 1024
PRIORITIES = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
INTEGRITY = {"body-unavailable-or-invalid", "frontmatter-drift",
             "review-date-invalid", "reference-budget-or-shape"}
AI_DRIFT = {"ai-review-authorization-record-drift", "ai-review-item-identity-drift",
            "ai-review-content-drift", "human-review-content-drift"}
TRUST = {"ai-review-proof-unverified", "ai-review-request-proof-unverified",
         "human-review-historical-unbound"}
KNOWN_SIGNALS = INTEGRITY | AI_DRIFT | TRUST | {
    "secret-pattern-requires-triage", "local-reference-missing",
    "active-review-overdue", "candidate-needs-independent-review",
    "candidate-review-overdue", "archive-directory-identity-only",
    "historical-review-overdue", "review-date-overdue", "body-empty",
}


def _fingerprint(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _route(row: Mapping[str, Any], signals: set, duplicate: bool) -> tuple:
    risk = row.get("risk_class", "ordinary")
    lane = row.get("lane", "")
    if not signals.issubset(KNOWN_SIGNALS):
        return "P0", "human-governance-review", "contract-meaning-review"
    if "secret-pattern-requires-triage" in signals:
        return "P0", "human-security-review", "verified-security-review"
    if signals & INTEGRITY:
        return "P0", "machine-diagnose-integrity", "governed-repair-review"
    if signals & AI_DRIFT:
        return "P0", "machine-replay-review-binding", "independent-human-review"
    if risk == "security-critical" and signals:
        return "P0", "human-security-review", "verified-security-review"
    if signals & TRUST:
        return "P1", "machine-prepare-proof-packet", "independent-human-review"
    if "local-reference-missing" in signals:
        return "P1", "machine-discover-references", "governed-evidence-review"
    if "active-review-overdue" in signals:
        return "P1", "machine-prepare-current-review", "owner-semantic-review"
    if "candidate-needs-independent-review" in signals:
        return "P2", "machine-prepare-candidate-review", "independent-human-review"
    if "candidate-review-overdue" in signals:
        return "P2", "machine-prepare-candidate-review", "independent-human-review"
    if lane == "P0-governance" and signals:
        return "P0", "human-governance-review", "owner-semantic-review"
    if duplicate:
        return "P2", "machine-compare-duplicates", "owner-equivalence-decision"
    if "archive-directory-identity-only" in signals:
        return "P3", "machine-audit-archive-provenance", "archive-owner-review"
    if "historical-review-overdue" in signals:
        return "P3", "machine-prepare-historical-review", "archive-owner-review"
    if signals:
        # New/unknown signals are not silently declared safe or auto-fixed.
        return "P0", "human-governance-review", "contract-meaning-review"
    return "", "", ""


def _duplicates(report: Mapping[str, Any], visible: set) -> set:
    groups = report.get("duplicates")
    if not isinstance(groups, Mapping) or groups.get("automatic_merge_allowed") is not False:
        raise KnowledgeHubError("corpus duplicates must remain non-mergeable")
    duplicate_ids = set()
    for field in ("same_domain_title", "same_canonical_body"):
        rows = groups.get(field)
        if not isinstance(rows, list):
            raise KnowledgeHubError("corpus duplicate groups are malformed")
        for group in rows:
            if not isinstance(group, list) or len(group) < 2 or any(
                not isinstance(value, str) or value not in visible for value in group
            ):
                raise KnowledgeHubError("corpus duplicate group has invalid identity")
            duplicate_ids.update(group)
    return duplicate_ids


def _action(row: Mapping[str, Any], duplicate: bool) -> Dict[str, Any]:
    signals = row.get("signals")
    if not isinstance(signals, list) or any(not isinstance(x, str) for x in signals):
        raise KnowledgeHubError("corpus signals are malformed")
    unique = set(signals)
    priority, route, next_boundary = _route(row, unique, duplicate)
    if not route:
        return {}
    identity = {
        "id": str(row["id"]), "path": str(row["path"]),
        "body_sha256": str(row.get("body", {}).get("sha256", "")),
        "signals": sorted(unique), "duplicate_candidate": duplicate,
        "priority": priority, "route": route,
    }
    return {
        "item_id": identity["id"], "path": identity["path"],
        "owner": str(row.get("owner", "")), "status": str(row.get("status", "")),
        "risk_class": str(row.get("risk_class", "")),
        "priority": priority, "machine_first": route.startswith("machine-"),
        "action": route, "next_boundary": next_boundary,
        "signal_codes": identity["signals"],
        "duplicate_candidate": duplicate,
        "snapshot_fingerprint": _fingerprint(identity),
        "proposal_only": True, "content_change_approved": False,
    }


def build_corpus_optimization(report: Mapping[str, Any]) -> Dict[str, Any]:
    """Route all visible corpus records without touching content or approvals."""
    from .corpus_review import CONTRACT

    rows = report.get("rows")
    n = report.get("item_count")
    excluded = report.get("private_excluded_count")
    if (report.get("schema_version") != CONTRACT
            or report.get("report_only") is not True
            or report.get("canonical_write_performed") is not False
            or report.get("semantic_review_performed") is not False
            or report.get("owner_approval_performed") is not False
            or not isinstance(rows, list) or type(n) is not int
            or not 0 <= n <= MAX_ROWS or n != len(rows)
            or report.get("accounted_for_count") != n
            or type(excluded) is not int or excluded < 0 or excluded > n):
        raise KnowledgeHubError("corpus optimization requires complete read-only evidence")
    visible = [r for r in rows if isinstance(r, Mapping)
               and r.get("lane") != "personal-excluded"]
    hidden_count = n - len(visible)
    if hidden_count != excluded or any(not isinstance(r, Mapping) for r in rows):
        raise KnowledgeHubError("private corpus accounting is inconsistent")
    if any(row.get("status") == "personal"
           or str(row.get("path", "")).startswith("notes/personal/")
           for row in visible):
        raise KnowledgeHubError("personal item is visible in corpus observations")
    ids = [r.get("id") for r in visible]
    if any(not isinstance(x, str) or not x or len(x) > 256 for x in ids) or len(set(ids)) != len(ids):
        raise KnowledgeHubError("corpus identity set is invalid")
    dup = _duplicates(report, set(ids))
    actions = [_action(row, row["id"] in dup) for row in visible]
    actions = [row for row in actions if row]
    actions.sort(key=lambda row: (PRIORITIES[row["priority"]], row["item_id"]))
    action_count = len(actions)
    classes = Counter(row["action"] for row in actions)
    priorities = Counter(row["priority"] for row in actions)
    fingerprint = _fingerprint({
        "revision": report.get("source_revision", ""),
        "as_of": report.get("as_of", ""), "actions": actions,
        "total": n, "private_excluded": excluded,
    })
    result = {
        "projection": PROJECTION,
        "source_revision": report.get("source_revision", ""),
        "as_of": report.get("as_of", ""),
        "status": "needs-attention" if actions else "no-change",
        "item_count": n, "visible_count": len(visible),
        "private_excluded_count": excluded,
        "action_count": action_count,
        "no_change_count": len(visible) - action_count,
        "accounted_for_count": action_count + len(visible) - action_count + excluded,
        "coverage_complete": True,
        "machine_first_count": sum(x["machine_first"] for x in actions),
        "by_action": dict(sorted(classes.items())),
        "by_priority": dict(sorted(priorities.items())),
        "fingerprint": fingerprint,
        "read_only": True, "candidate_only": True,
        "canonical_write_performed": False,
        "automatic_content_edits_enabled": False,
        "semantic_review_performed": False, "owner_approval_performed": False,
        "duplicate_auto_merge_enabled": False,
        "actions": actions,
    }
    size = len(json.dumps(result, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False).encode("utf-8"))
    if size > MAX_PLAN_BYTES:
        raise KnowledgeHubError("corpus optimization plan exceeds byte budget")
    return result
