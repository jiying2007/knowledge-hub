"""Read-only full-corpus integrity and review preparation.

This is a *machine audit*, not a semantic approval or lifecycle transition.
Every registry item is accounted for; personal content is never exported.
Canonical Markdown, registry, and existing review ledgers remain authoritative.
"""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess
import unicodedata
from typing import Any, Dict, List, Mapping

from .common import (
    KnowledgeHubError, read_repository_bytes_bounded, registry_items,
    resolve_inside, split_frontmatter,
)
from .delegated_content_review import (
    FIELD as AI_REVIEW_FIELD, load_ledger, review_state,
)
from .review_risk import classify_review_risk, load_review_risk_policy
from .security import scan_secret_text

CONTRACT = "knowledge-hub.corpus-review/v1"
MAX_ITEMS = 5000
MAX_ITEM_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_REPORT_BYTES = 4 * 1024 * 1024
MAX_REFS_PER_ITEM = 128
PATH_PREFIXES = (
    "projects/", "domains/", "governance/", "artifacts/", "sources/",
    "tools/", "schemas/", "registry/", "indexes/", "templates/", "docs/",
)


def _source_revision(root: pathlib.Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    value = result.stdout.strip() if result.returncode == 0 else ""
    return value if re.fullmatch(r"[a-f0-9]{40}", value) else ""


def _safe_date(value: Any) -> dt.date:
    if not isinstance(value, str):
        raise KnowledgeHubError("review_after is not a date")
    result = dt.date.fromisoformat(value)
    if result.isoformat() != value:
        raise KnowledgeHubError("review_after is not canonical")
    return result


def _local_refs(root: pathlib.Path, item: Mapping[str, Any]) -> Dict[str, Any]:
    values: List[Any] = []
    for field in ("evidence_refs", "validation_refs"):
        refs = item.get(field, [])
        if not isinstance(refs, list):
            return {"status": "invalid", "missing": 0, "checked": 0}
        values.extend(refs)
    if len(values) > MAX_REFS_PER_ITEM:
        return {"status": "budget-exceeded", "missing": 0, "checked": 0}
    checked, missing = 0, 0
    for value in dict.fromkeys(str(v) for v in values):
        if not value.startswith(PATH_PREFIXES) or "\n" in value or "#" in value:
            continue
        checked += 1
        try:
            path = resolve_inside(root, value)
            missing += not path.is_file() or path.is_symlink()
        except (KnowledgeHubError, OSError, ValueError):
            missing += 1
    return {"status": "checked", "missing": missing, "checked": checked}


def _document(root: pathlib.Path, item: Mapping[str, Any]) -> Dict[str, Any]:
    path = str(item.get("path", ""))
    try:
        data = read_repository_bytes_bounded(root, path, MAX_ITEM_BYTES, "corpus body")
        metadata, body = split_frontmatter(data.decode("utf-8"))
        mirrored = all(str(metadata.get(key, "")) == str(item.get(key, ""))
                       for key in ("id", "path", "status", "owner", "kind"))
        return {
            "status": "read",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "body_sha256": hashlib.sha256(body.strip().encode("utf-8")).hexdigest(),
            "body_empty": not bool(body.strip()),
            "frontmatter_matches_registry": mirrored,
            "secret_pattern_count": len(scan_secret_text(body)),
        }
    except (KnowledgeHubError, OSError, UnicodeError, ValueError, TypeError):
        return {
            "status": "unavailable-or-invalid",
            "bytes": 0, "sha256": "", "body_sha256": "",
            "body_empty": True, "frontmatter_matches_registry": False,
            "secret_pattern_count": 0,
        }


def _review_evidence(root: pathlib.Path, item: Mapping[str, Any], document: Mapping[str, Any],
                     ledger: Mapping[str, Any], policy: Mapping[str, Any]) -> Dict[str, str]:
    digest = str(document.get("sha256", ""))
    human = str(item.get("human_review_content_sha256") or "")
    if human:
        human_state = "current-body-bound" if human == digest else "content-drift"
    elif item.get("human_reviewed_by") or item.get("human_reviewed_at"):
        human_state = "historical-unbound"
    else:
        human_state = "absent"
    ai = review_state(root, item, ledger=ledger, policy=policy) if AI_REVIEW_FIELD in item else {
        "status": "absent", "closed": False,
    }
    return {
        "human": human_state,
        "ai": str(ai["status"]),
        "ai_decision": str(ai.get("decision", "")),
        "ai_closed": "verified" if ai.get("closed") is True else "not-verified",
    }


def _signals(item: Mapping[str, Any], doc: Mapping[str, Any], refs: Mapping[str, Any],
             review: Mapping[str, str], today: dt.date) -> List[str]:
    issues = []
    status = item.get("status")
    if doc["status"] != "read":
        issues.append("body-unavailable-or-invalid")
    elif doc["body_empty"]:
        issues.append("body-empty")
    if not doc["frontmatter_matches_registry"]:
        issues.append("frontmatter-drift")
    if doc["secret_pattern_count"]:
        issues.append("secret-pattern-requires-triage")
    if refs["status"] != "checked":
        issues.append("reference-budget-or-shape")
    elif refs["missing"]:
        issues.append("local-reference-missing")
    try:
        overdue = _safe_date(item.get("review_after")) < today
    except (KnowledgeHubError, TypeError, ValueError):
        overdue = True
        issues.append("review-date-invalid")
    if overdue:
        issues.append({
            "active": "active-review-overdue",
            "reviewing": "candidate-review-overdue",
            "archived": "historical-review-overdue",
        }.get(status, "review-date-overdue"))
    if review["human"] == "content-drift":
        issues.append("human-review-content-drift")
    elif review["human"] == "historical-unbound" and status in {"active", "reviewing"}:
        issues.append("human-review-historical-unbound")
    if review["ai"] in {"invalid", "needs-review"}:
        issues.append("ai-review-proof-unverified")
    if status == "reviewing" and review["human"] != "current-body-bound" and review["ai_closed"] != "verified":
        issues.append("candidate-needs-independent-review")
    return sorted(set(issues))


def _lane(item: Mapping[str, Any], signals: List[str], risk_class: str) -> str:
    if item.get("status") == "personal" or item.get("visibility") == "personal-local":
        return "personal-excluded"
    if "body-unavailable-or-invalid" in signals or "frontmatter-drift" in signals:
        return "P0-integrity"
    if risk_class == "security-critical" and item.get("status") in {"active", "reviewing"}:
        return "P0-governance"
    if item.get("status") == "active":
        return "P1-current-validity" if signals else "current-verified-metadata"
    if item.get("status") in {"reviewing", "draft"}:
        return "P2-candidate-review"
    return "P3-historical-integrity"


def _item_row(root: pathlib.Path, item: Mapping[str, Any], today: dt.date,
              ledger: Mapping[str, Any], policy: Mapping[str, Any]) -> Dict[str, Any]:
    if item.get("status") == "personal" or item.get("visibility") == "personal-local":
        identity = hashlib.sha256(str(item.get("id", "")).encode()).hexdigest()[:16]
        return {"id": "redacted-sha256:" + identity, "status": "personal",
                "lane": "personal-excluded", "machine_checked": False,
                "signals": ["personal-excluded"], "private_content_exported": False}
    doc = _document(root, item)
    refs = _local_refs(root, item)
    review = _review_evidence(root, item, doc, ledger, policy)
    risk = classify_review_risk(policy, item.get("path", ""))
    flags = _signals(item, doc, refs, review, today)
    return {
        "id": str(item.get("id", "")), "path": str(item.get("path", "")),
        "title": str(item.get("title", ""))[:512], "domain": str(item.get("domain", "")),
        "kind": str(item.get("kind", "")), "status": str(item.get("status", "")),
        "owner": str(item.get("owner", "")), "review_after": str(item.get("review_after", "")),
        "risk_class": risk["review_class"], "lane": _lane(item, flags, risk["review_class"]),
        "body": doc, "references": refs, "review_proof": review, "signals": flags,
        "machine_checked": doc["status"] == "read", "semantic_review_performed": False,
        "human_approval_performed": False, "lifecycle_changed": False,
    }


def _duplicate_groups(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    titles = collections.defaultdict(list)
    bodies = collections.defaultdict(list)
    for item in rows:
        if item["lane"] == "personal-excluded":
            continue
        name = unicodedata.normalize("NFKC", item["title"]).casefold().strip()
        if name:
            titles[(item["domain"], name)].append(item["id"])
        digest = item["body"].get("body_sha256", "")
        if digest and not item["body"].get("body_empty"):
            bodies[digest].append(item["id"])
    named = [sorted(group) for group in titles.values() if len(group) > 1]
    equal = [sorted(group) for group in bodies.values() if len(group) > 1]
    return {"same_domain_title": sorted(named), "same_canonical_body": sorted(equal),
            "automatic_merge_allowed": False, "duplicate_is_not_equivalent": True}


def build_corpus_review(root: pathlib.Path, as_of: dt.date) -> Dict[str, Any]:
    if type(as_of) is not dt.date:
        raise KnowledgeHubError("corpus review requires a concrete calendar date")
    items = registry_items(root)
    if len(items) > MAX_ITEMS or len({x.get("id") for x in items}) != len(items):
        raise KnowledgeHubError("corpus exceeds item budget or has duplicate IDs")
    ledger = load_ledger(root)
    policy = load_review_risk_policy(root)
    rows, total_bytes = [], 0
    for item in items:
        row = _item_row(root, item, as_of, ledger, policy)
        total_bytes += row.get("body", {}).get("bytes", 0)
        if total_bytes > MAX_TOTAL_BYTES:
            raise KnowledgeHubError("corpus review total body budget exceeded")
        rows.append(row)
    counts = collections.Counter(x.get("status", "") for x in rows)
    lanes = collections.Counter(x["lane"] for x in rows)
    # A successfully parsed body is not the same as an attempted machine audit.
    # Missing/corrupt bodies remain visible as P0 findings, never as PASS.
    private_count = sum(x["lane"] == "personal-excluded" for x in rows)
    attempted_count = len(rows) - private_count
    checked_count = sum(x.get("machine_checked") is True for x in rows)
    failed_count = attempted_count - checked_count
    issue_counts = collections.Counter(flag for x in rows for flag in x["signals"])
    duplicates = _duplicate_groups(rows)
    result = {
        "schema_version": CONTRACT, "as_of": as_of.isoformat(),
        "source_revision": _source_revision(root), "report_only": True,
        "canonical_write_performed": False, "active_promoted": False,
        "semantic_review_performed": False, "owner_approval_performed": False,
        "authorization_not_conferred_by_scan": True,
        "item_count": len(items), "accounted_for_count": len(rows),
        "machine_attempted_count": attempted_count,
        "machine_checked_count": checked_count,
        "machine_failed_count": failed_count,
        "private_excluded_count": private_count,
        "total_body_bytes": total_bytes, "status_counts": dict(sorted(counts.items())),
        "lane_counts": dict(sorted(lanes.items())), "signal_counts": dict(sorted(issue_counts.items())),
        "duplicates": duplicates, "rows": rows,
    }
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(encoded.encode("utf-8")) > MAX_REPORT_BYTES:
        raise KnowledgeHubError("corpus review output exceeds report byte budget")
    result["report_sha256"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return result
