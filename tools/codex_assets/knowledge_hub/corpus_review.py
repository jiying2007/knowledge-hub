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
from .corpus_optimization import build_corpus_optimization
from .corpus_supersession import annotate_supersession
from .template_integrity import is_registered_unfilled_template
from .delegated_content_review import (
    FIELD as AI_REVIEW_FIELD, expected_record, item_digest, load_ledger, review_state,
)
from .review_risk import classify_review_risk, load_review_risk_policy
from .security import scan_secret_text
from .text_integrity import has_persisted_tool_truncation

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


def _archive_directory(root: pathlib.Path, item: Mapping[str, Any]) -> Dict[str, Any]:
    """Recognize a narrowly declared retired archive *directory*, not its bodies."""
    source = item.get("source", {})
    tags = item.get("tags", [])
    if not (
        item.get("status") == "archived"
        and item.get("review_status") == "archive-corpus-materialized"
        and item.get("promotion") == "none"
        and isinstance(source, Mapping)
        and source.get("type") == "retired-source-provenance"
        and isinstance(tags, list)
        and "historical-corpus" in tags
    ):
        return {}
    try:
        path = resolve_inside(root, str(item.get("path", "")))
        if not path.is_dir() or path.is_symlink() or not any(path.iterdir()):
            return {}
    except (KnowledgeHubError, OSError, TypeError, ValueError):
        return {}
    return {
        "status": "archive-directory-observed",
        "bytes": 0, "sha256": "", "body_sha256": "",
        "body_empty": None, "frontmatter_matches_registry": None,
        "secret_pattern_count": 0, "contents_verified": False,
        "directory_identity_observed": True,
    }


def _local_refs(
    root: pathlib.Path, item: Mapping[str, Any], *, archive_directory: bool = False
) -> Dict[str, Any]:
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
        # An archived validation_ref can be a CLI invocation, not a file
        # named "<script>.sh --flags". Check only the script's existence;
        # never execute it or claim that its arguments were validated.
        command = re.match(r"^(tools/[^\s]+\.sh)\s+\S", value)
        reference_path = command.group(1) if command else value
        try:
            path = resolve_inside(root, reference_path)
            valid_file = path.is_file() and not path.is_symlink()
            valid_archive_dir = (
                archive_directory and value == item.get("path")
                and path.is_dir() and not path.is_symlink()
            )
            missing += not (valid_file or valid_archive_dir)
        except (KnowledgeHubError, OSError, ValueError):
            missing += 1
    return {"status": "checked", "missing": missing, "checked": checked}


def _archived_non_markdown_asset(item: Mapping[str, Any], path: str, data: bytes) -> bool:
    """Recognize historical code/config, not current metadata or syntax approval."""
    if (item.get("status") != "archived" or item.get("kind") != "audit"
            or data.startswith((b"---", b"\xef\xbb\xbf---"))):
        return False
    relative = pathlib.PurePosixPath(path)
    if (relative.is_absolute() or ".." in relative.parts or "\\" in path
            or relative.as_posix() != path or any(ord(char) < 32 for char in path)):
        return False
    if path.startswith("tools/") and path.endswith(".sh"):
        return data.startswith((b"#!/bin/bash\n", b"#!/usr/bin/env bash\n"))
    if path.startswith("registry/") and path.endswith(".json"):
        try:
            return isinstance(json.loads(data.decode("utf-8")), (dict, list))
        except (UnicodeError, ValueError):
            return False
    return False


def _document(root: pathlib.Path, item: Mapping[str, Any]) -> Dict[str, Any]:
    path = str(item.get("path", ""))
    try:
        data = read_repository_bytes_bounded(root, path, MAX_ITEM_BYTES, "corpus body")
        metadata, body = split_frontmatter(data.decode("utf-8"))
        mirrored = all(str(metadata.get(key, "")) == str(item.get(key, ""))
                       for key in ("id", "path", "status", "owner", "kind"))
        if (not mirrored and item.get("status") == "archived"
                and "path" not in metadata):
            # Legacy archived YAML may omit path; Registry remains authoritative.
            # All other identity mirrors must be explicitly present and exact.
            mirrored = all(
                key in metadata
                and str(metadata[key]) == str(item.get(key, ""))
                for key in ("id", "status", "owner", "kind")
            )
        declared = metadata.get("supersedes_candidate")
        invalid_supersedes = declared is not None and (
            not isinstance(declared, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}", declared)
        )
        return {
            "status": "read",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "body_sha256": hashlib.sha256(body.strip().encode("utf-8")).hexdigest(),
            "body_empty": not bool(body.strip()),
            "frontmatter_matches_registry": mirrored,
            "persisted_tool_truncation": has_persisted_tool_truncation(data),
            "historical_non_markdown_asset": _archived_non_markdown_asset(item, path, data),
            # Plain Markdown archived before YAML adoption is preserved as
            # unbound provenance, never silently accepted as current metadata.
            "historical_plaintext_archive": (
                item.get("status") == "archived"
                and path.endswith(".md")
                and not data.startswith((b"---", b"\xef\xbb\xbf---"))
            ),
            "secret_pattern_count": len(scan_secret_text(body)),
            "supersedes_candidate": declared if declared and not invalid_supersedes else "",
            "supersedes_invalid": bool(invalid_supersedes),
        }
    except (KnowledgeHubError, OSError, UnicodeError, ValueError, TypeError):
        return {
            "status": "unavailable-or-invalid",
            "bytes": 0, "sha256": "", "body_sha256": "",
            "body_empty": True, "frontmatter_matches_registry": False,
            "secret_pattern_count": 0,
        }


def _ai_snapshot_binding(item: Mapping[str, Any], document: Mapping[str, Any],
                         ledger: Mapping[str, Any]) -> Dict[str, Any]:
    """Inspect historical review hashes without granting review authority."""
    empty = {"item_sha256_match": None, "content_sha256_match": None,
             "request_proof": "absent"}
    record = item.get(AI_REVIEW_FIELD)
    if record is None:
        return dict(empty, state="absent")
    if not isinstance(record, dict):
        return dict(empty, state="record-malformed")
    auth = ledger.get(record.get("authorization_id", ""))
    if not isinstance(auth, dict):
        return dict(empty, state="authorization-missing")
    proof = str(auth.get("request_proof", {}).get("state", "unverified"))
    entry = next((row for row in auth.get("entries", [])
                  if row.get("id") == item.get("id")), None)
    if entry is None or record != expected_record(auth, entry):
        return dict(empty, state="authorization-record-drift", request_proof=proof)
    item_match = item_digest(item) == entry["item_sha256"]
    body_match = (document.get("sha256") == entry["content_sha256"]
                  if document.get("status") == "read" else None)
    if item_match is False or body_match is False:
        state = "snapshot-drift"
    elif body_match is None:
        state = "body-unavailable"
    elif proof != "verified":
        state = "request-unverified"
    else:
        state = "snapshot-exact-not-semantic-approval"
    return {"state": state, "item_sha256_match": item_match,
            "content_sha256_match": body_match, "request_proof": proof}


def _review_evidence(root: pathlib.Path, item: Mapping[str, Any], document: Mapping[str, Any],
                     ledger: Mapping[str, Any], policy: Mapping[str, Any]) -> Dict[str, Any]:
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
        "ai_snapshot": _ai_snapshot_binding(item, document, ledger),
    }


def _signals(item: Mapping[str, Any], doc: Mapping[str, Any], refs: Mapping[str, Any],
             review: Mapping[str, Any], today: dt.date) -> List[str]:
    issues = ["persisted-tool-truncation-marker"] if doc.get("persisted_tool_truncation") is True else []
    status = item.get("status")
    if doc["status"] == "archive-directory-observed":
        issues.append("archive-directory-identity-only")
    elif doc["status"] != "read":
        issues.append("body-unavailable-or-invalid")
    else:
        if doc["body_empty"]:
            issues.append("body-empty")
        if is_registered_unfilled_template(
                item.get("kind"), status, doc.get("body_sha256")):
            issues.append("registered-unfilled-template")
        if not doc["frontmatter_matches_registry"]:
            if (doc.get("historical_plaintext_archive") is True
                    or doc.get("historical_non_markdown_asset") is True):
                issues.append("archive-plaintext-provenance-only")
            else:
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
    snapshot = review["ai_snapshot"]
    if snapshot["item_sha256_match"] is False:
        issues.append("ai-review-item-identity-drift")
    if snapshot["content_sha256_match"] is False:
        issues.append("ai-review-content-drift")
    if snapshot["request_proof"] == "unverified":
        issues.append("ai-review-request-proof-unverified")
    if snapshot["state"] in {"record-malformed", "authorization-missing",
                              "authorization-record-drift"}:
        issues.append("ai-review-authorization-record-drift")
    if status == "reviewing" and review["human"] != "current-body-bound" and review["ai_closed"] != "verified":
        issues.append("candidate-needs-independent-review")
    return sorted(set(issues))


def _lane(item: Mapping[str, Any], signals: List[str], risk_class: str) -> str:
    if item.get("status") == "personal" or item.get("visibility") == "personal-local":
        return "personal-excluded"
    if ({"body-unavailable-or-invalid", "frontmatter-drift",
         "registered-unfilled-template", "persisted-tool-truncation-marker"} & set(signals)):
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
    doc = _archive_directory(root, item) or _document(root, item)
    refs = _local_refs(
        root, item, archive_directory=doc["status"] == "archive-directory-observed"
    )
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
        "machine_checked": doc["status"] == "read",
        "archive_directory_observed": doc["status"] == "archive-directory-observed",
        "semantic_review_performed": False,
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


def _annotate_lineage(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    from .corpus_supersession import BLOCKING_SIGNALS

    audit = annotate_supersession(rows)
    # Conflicting historical declarations are P0 governance, not approvals.
    for row in rows:
        if row.get("lane") != "personal-excluded" and BLOCKING_SIGNALS.intersection(
            row.get("signals", [])
        ):
            row["lane"] = "P0-governance"
    return audit


def _historical_ai_audit(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Count historical hash observations only; never generate new approval.
    ai_snapshots = [
        row["review_proof"]["ai_snapshot"] for row in rows
        if row.get("review_proof", {}).get("ai_snapshot", {}).get("state") != "absent"
        and row.get("review_proof", {}).get("ai_snapshot") is not None
    ]
    ai_states = collections.Counter(s["state"] for s in ai_snapshots)
    return {
        "historical_record_count": len(ai_snapshots),
        "state_counts": dict(sorted(ai_states.items())),
        "request_unverified_count": sum(s["request_proof"] == "unverified"
                                        for s in ai_snapshots),
        "item_identity_drift_count": sum(s["item_sha256_match"] is False
                                         for s in ai_snapshots),
        "body_content_drift_count": sum(s["content_sha256_match"] is False
                                        for s in ai_snapshots),
        "exact_snapshot_count": sum(
            s["item_sha256_match"] is True and s["content_sha256_match"] is True
            for s in ai_snapshots
        ),
        "semantic_approval_performed": False,
        "historical_proof_promoted": False,
        "report_only": True,
    }


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
    supersession_audit = _annotate_lineage(rows)
    counts = collections.Counter(x.get("status", "") for x in rows)
    lanes = collections.Counter(x["lane"] for x in rows)
    # A successfully parsed body is not the same as an attempted machine audit.
    # Missing/corrupt bodies remain visible as P0 findings, never as PASS.
    private_count = sum(x["lane"] == "personal-excluded" for x in rows)
    attempted_count = len(rows) - private_count
    checked_count = sum(x.get("machine_checked") is True for x in rows)
    directory_count = sum(x.get("archive_directory_observed") is True for x in rows)
    failed_count = attempted_count - checked_count - directory_count
    issue_counts = collections.Counter(flag for x in rows for flag in x["signals"])
    duplicates = _duplicate_groups(rows)
    ai_audit = _historical_ai_audit(rows)
    result = {
        "schema_version": CONTRACT, "as_of": as_of.isoformat(),
        "source_revision": _source_revision(root), "report_only": True,
        "canonical_write_performed": False, "active_promoted": False,
        "semantic_review_performed": False, "owner_approval_performed": False,
        "authorization_not_conferred_by_scan": True,
        "item_count": len(items), "accounted_for_count": len(rows),
        "machine_attempted_count": attempted_count,
        "machine_checked_count": checked_count,
        "archive_directory_observed_count": directory_count,
        "machine_failed_count": failed_count,
        "private_excluded_count": private_count,
        "total_body_bytes": total_bytes, "status_counts": dict(sorted(counts.items())),
        "lane_counts": dict(sorted(lanes.items())), "signal_counts": dict(sorted(issue_counts.items())),
        "duplicates": duplicates, "ai_review_audit": ai_audit,
        "supersession_audit": supersession_audit, "rows": rows,
    }
    # Reuse this canonical observation set to prepare a bounded, non-authoritative
    # action queue for *every* non-personal item, not only the first review batch.
    optimization = build_corpus_optimization(result)
    result["optimization_queue"] = optimization
    result["optimization_summary"] = {
        key: value for key, value in optimization.items()
        if key != "actions"
    }
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(encoded.encode("utf-8")) > MAX_REPORT_BYTES:
        raise KnowledgeHubError("corpus review output exceeds report byte budget")
    result["report_sha256"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return result
