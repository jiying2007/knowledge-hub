"""Build a tamper-resistant security-critical PR change review verdict."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError

PROJECTION = "knowledge-hub-security-change-review-v1"
AUTOMATION_FILE_ALLOWLISTS = {
    "automation/hosting-private-": (
        "registry/durable-evidence-ledger.jsonl",
        "registry/knowledge-platform-p5-p10.json",
    ),
    "automation/evidence-bind-": (
        "registry/durable-evidence-ledger.jsonl",
        "registry/items.jsonl",
    ),
    "automation/external-gap-": (
        "registry/durable-evidence-ledger.jsonl",
        "registry/knowledge-platform-p5-p10.json",
    ),
}
AUTOMATION_PREFIXES = tuple(AUTOMATION_FILE_ALLOWLISTS)
BOT_LOGINS = {
    "github-actions[bot]",
    "github-actions",
}
TRUSTED_COMMENT_ASSOCIATIONS = {
    "OWNER",
    "MEMBER",
    "COLLABORATOR",
}


def _fingerprint(value: Mapping[str, Any]) -> str:
    raw = json.dumps(
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _review_class(
    path: str,
    policy: Mapping[str, Any],
) -> str:
    selected = str(policy.get("default_class", "ordinary"))
    rules = policy.get("rules", [])
    if not isinstance(rules, list):
        raise KnowledgeHubError("review risk rules must be a list")
    for rule in rules:
        if not isinstance(rule, Mapping):
            continue
        if str(rule.get("path", "")) == path and path:
            return str(rule.get("review_class", selected))
        prefix = str(rule.get("path_prefix", ""))
        if prefix and path.startswith(prefix):
            return str(rule.get("review_class", selected))
    return selected


def _security_files(
    files: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen = set()
    for value in files:
        path = str(value.get("filename", "")).strip()
        if not path or path in seen:
            continue
        seen.add(path)
        if _review_class(path, policy) != "security-critical":
            continue
        rows.append(
            {
                "path": path,
                "status": str(value.get("status", "")),
                "additions": int(value.get("additions", 0) or 0),
                "deletions": int(value.get("deletions", 0) or 0),
                "changes": int(value.get("changes", 0) or 0),
                "blob_url": str(value.get("blob_url", "")),
                "raw_url": str(value.get("raw_url", "")),
                "sha": str(value.get("sha", "")),
            }
        )
    rows.sort(key=lambda row: row["path"])
    return rows


def _latest_reviews(
    reviews: Iterable[Mapping[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for value in reviews:
        user = value.get("user") or {}
        if not isinstance(user, Mapping):
            continue
        login = str(user.get("login", "")).strip()
        if not login:
            continue
        row = {
            "login": login,
            "user_type": str(user.get("type", "")),
            "state": str(value.get("state", "")).upper(),
            "commit_id": str(value.get("commit_id", "")).lower(),
            "submitted_at": str(value.get("submitted_at", "")),
            "review_id": int(value.get("id", 0) or 0),
        }
        if row["state"] not in {
            "APPROVED",
            "CHANGES_REQUESTED",
            "DISMISSED",
        }:
            continue
        previous = latest.get(login)
        if previous is None or row["review_id"] >= previous["review_id"]:
            latest[login] = row
    return latest


def _exact_head_approvals(
    reviews: Iterable[Mapping[str, Any]],
    *,
    head_sha: str,
    author_login: str,
) -> List[Dict[str, Any]]:
    approvals: List[Dict[str, Any]] = []
    for row in _latest_reviews(reviews).values():
        login = str(row["login"])
        if (
            row["state"] != "APPROVED"
            or row["commit_id"] != head_sha
            or row["user_type"] == "Bot"
            or login in BOT_LOGINS
            or login == author_login
        ):
            continue
        approvals.append(row)
    approvals.sort(key=lambda row: row["login"])
    return approvals


def _comment_approvals(
    comments: Iterable[Mapping[str, Any]],
    *,
    change_fingerprint: str,
    head_sha: str,
) -> List[Dict[str, Any]]:
    expected = "SECURITY-CHANGE-APPROVE {} {}".format(
        change_fingerprint,
        head_sha,
    )
    approvals: List[Dict[str, Any]] = []
    for value in comments:
        user = value.get("user") or {}
        if not isinstance(user, Mapping):
            continue
        login = str(user.get("login", "")).strip()
        user_type = str(user.get("type", ""))
        association = str(value.get("author_association", "")).upper()
        if (
            not login
            or user_type == "Bot"
            or login in BOT_LOGINS
            or association not in TRUSTED_COMMENT_ASSOCIATIONS
            or str(value.get("body", "")).strip() != expected
        ):
            continue
        approvals.append(
            {
                "login": login,
                "user_type": user_type,
                "author_association": association,
                "comment_id": int(value.get("id", 0) or 0),
                "created_at": str(value.get("created_at", "")),
            }
        )
    approvals.sort(key=lambda row: (row["login"], row["comment_id"]))
    return approvals


def _autonomous_ratchet(
    *,
    head_ref: str,
    same_repository: bool,
    author_login: str,
    head_is_direct_child_of_base: bool,
    files: Sequence[Mapping[str, Any]],
) -> bool:
    if (
        not same_repository
        or author_login not in BOT_LOGINS
        or not head_is_direct_child_of_base
    ):
        return False
    matched = next(
        (
            prefix
            for prefix in AUTOMATION_PREFIXES
            if head_ref.startswith(prefix)
        ),
        "",
    )
    if not matched:
        return False
    observed = sorted(
        {
            str(row.get("filename", "")).strip()
            for row in files
            if str(row.get("filename", "")).strip()
        }
    )
    expected = sorted(AUTOMATION_FILE_ALLOWLISTS[matched])
    return observed == expected


def _change_basis(
    *,
    repository: str,
    pr_number: int,
    base_sha: str,
    head_sha: str,
    head_ref: str,
    author_login: str,
    same_repository: bool,
    security: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    return {
        "repository": repository,
        "pr_number": int(pr_number),
        "base_sha": base_sha,
        "head_sha": head_sha,
        "head_ref": head_ref,
        "author_login": author_login,
        "same_repository": bool(same_repository),
        "security_critical_files": list(security),
    }


def _review_verdict(
    *,
    security: Sequence[Mapping[str, Any]],
    autonomous: bool,
    approvals: Sequence[Mapping[str, Any]],
    comment_approvals: Sequence[Mapping[str, Any]],
) -> Tuple[str, bool, str]:
    if not security:
        return "pass", False, "no-security-critical-change"
    if autonomous:
        return "pass", False, "dedicated-machine-ratchet-verifier"
    if approvals:
        return "pass", True, "exact-head-human-approval"
    if comment_approvals:
        return "pass", True, "hash-bound-human-approval"
    return (
        "awaiting-human-review",
        True,
        "exact-head-human-approval-required",
    )


def _packet(
    *,
    repository: str,
    pr_number: int,
    base_sha: str,
    head_sha: str,
    head_ref: str,
    author_login: str,
    same_repository: bool,
    head_is_direct_child_of_base: bool,
    autonomous: bool,
    change_fingerprint: str,
    security: Sequence[Mapping[str, Any]],
    approvals: Sequence[Mapping[str, Any]],
    comment_approvals: Sequence[Mapping[str, Any]],
    status: str,
    review_required: bool,
    reason: str,
) -> Dict[str, Any]:
    packet: Dict[str, Any] = {
        "schema_version": 1,
        "projection": PROJECTION,
        "status": status,
        "gate_pass": status == "pass",
        "review_required": review_required,
        "review_reason": reason,
        "read_only": True,
        "canonical_write_performed": False,
        "repository": repository,
        "pr_number": int(pr_number),
        "base_sha": base_sha,
        "head_sha": head_sha,
        "head_ref": head_ref,
        "author_login": author_login,
        "same_repository": bool(same_repository),
        "head_is_direct_child_of_base": bool(head_is_direct_child_of_base),
        "autonomous_ratchet": autonomous,
        "change_fingerprint": change_fingerprint,
        "security_critical_file_count": len(security),
        "security_critical_files": list(security),
        "exact_head_approval_count": len(approvals),
        "exact_head_approvals": list(approvals),
        "hash_bound_comment_approval_count": len(comment_approvals),
        "hash_bound_comment_approvals": list(comment_approvals),
    }
    packet["packet_fingerprint"] = _fingerprint(packet)
    return packet


def build_security_change_review(
    *,
    repository: str,
    pr_number: int,
    base_sha: str,
    head_sha: str,
    head_ref: str,
    author_login: str,
    same_repository: bool,
    head_is_direct_child_of_base: bool,
    files: Sequence[Mapping[str, Any]],
    reviews: Sequence[Mapping[str, Any]],
    review_risk_policy: Mapping[str, Any],
    comments: Sequence[Mapping[str, Any]] = (),
) -> Dict[str, Any]:
    security = _security_files(files, review_risk_policy)
    change_basis = _change_basis(
        repository=repository,
        pr_number=pr_number,
        base_sha=base_sha,
        head_sha=head_sha,
        head_ref=head_ref,
        author_login=author_login,
        same_repository=same_repository,
        security=security,
    )
    change_fingerprint = _fingerprint(change_basis)
    approvals = _exact_head_approvals(
        reviews,
        head_sha=head_sha,
        author_login=author_login,
    )
    comment_approvals = _comment_approvals(
        comments,
        change_fingerprint=change_fingerprint,
        head_sha=head_sha,
    )
    autonomous = _autonomous_ratchet(
        head_ref=head_ref,
        same_repository=same_repository,
        author_login=author_login,
        head_is_direct_child_of_base=head_is_direct_child_of_base,
        files=files,
    )
    status, review_required, reason = _review_verdict(
        security=security,
        autonomous=autonomous,
        approvals=approvals,
        comment_approvals=comment_approvals,
    )

    return _packet(
        repository=repository,
        pr_number=pr_number,
        base_sha=base_sha,
        head_sha=head_sha,
        head_ref=head_ref,
        author_login=author_login,
        same_repository=same_repository,
        head_is_direct_child_of_base=head_is_direct_child_of_base,
        autonomous=autonomous,
        change_fingerprint=change_fingerprint,
        security=security,
        approvals=approvals,
        comment_approvals=comment_approvals,
        status=status,
        review_required=review_required,
        reason=reason,
    )
