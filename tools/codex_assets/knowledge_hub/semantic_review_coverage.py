"""Report-only coverage of *claimed* whole-body AI reviews against exact corpus hashes.

Issue discussion is a progress journal, not a reviewer signature or knowledge source.
Never read or serialize personal-local item IDs or content into the report.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Sequence

CORPUS_CONTRACT = "knowledge-hub.corpus-review/v1"
PROJECTION = "knowledge-hub.semantic-review-coverage/v1"
MAX_COMMENTS = 1000
MAX_COMMENT_BYTES = 65536
MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_QUEUE = 30
ID_PATTERN = r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}"
RECEIPT = re.compile(r"^\|\s*`(" + ID_PATTERN + r")`\s*\|\s*`([a-f0-9]{64})`\s*\|", re.M)
SEMANTIC_CLAIM = re.compile(r"(?<![\w])semantic_review_performed\s*=\s*true(?![\w])", re.I)
SHA = re.compile(r"[a-f0-9]{64}\Z")
HEAD = re.compile(r"[a-f0-9]{40}\Z")
STATUS_ORDER = {"active": 0, "reviewing": 1, "draft": 2, "archived": 3, "rejected": 4}


def _check_corpus(corpus: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    if corpus.get("schema_version") != CORPUS_CONTRACT:
        raise ValueError("unexpected corpus contract")
    if not isinstance(corpus.get("source_revision"), str) or not HEAD.fullmatch(corpus["source_revision"]):
        raise ValueError("corpus has no exact source revision")
    if not isinstance(corpus.get("report_sha256"), str) or not SHA.fullmatch(corpus["report_sha256"]):
        raise ValueError("corpus has no bounded report identity")
    rows = corpus.get("rows")
    if not isinstance(rows, list) or len(rows) > 5000 or len(rows) != corpus.get("item_count"):
        raise ValueError("corpus rows are missing or incomplete")
    if corpus.get("accounted_for_count") != len(rows) or corpus.get("canonical_write_performed") is not False:
        raise ValueError("corpus is not a complete read-only audit")
    return rows


def _tracked_text_inventory(rows: List[Mapping[str, Any]], paths: Optional[Sequence[str]]) -> Dict[str, Any]:
    """Aggregate only: unregistered filenames/bodies are never exported or read."""
    if paths is None:
        return {"state": "unavailable", "unregistered_total": None}
    if len(paths) > 50000 or len(set(paths)) != len(paths):
        raise ValueError("invalid or duplicate tracked path inventory")
    registered = set()
    archive_roots = []
    for row in rows:
        if row.get("lane") == "personal-excluded":
            continue  # private paths cannot appear in the redacted corpus
        name = row.get("path")
        if not isinstance(name, str) or not name:
            raise ValueError("non-private row path missing")
        registered.add(name)
        if (isinstance(row.get("body"), dict)
                and row["body"].get("status") == "archive-directory-observed"):
            archive_roots.append(name.rstrip("/") + "/")
    total = 0
    unregistered = 0
    under_archive = 0
    private_skipped = 0
    for path in paths:
        if not isinstance(path, str) or not path or len(path.encode("utf-8")) > 1024:
            raise ValueError("invalid tracked path")
        if path.startswith(("personal/", ".private/")) or "/../" in path or path.startswith("../"):
            private_skipped += 1
            continue
        if not path.lower().endswith((".md", ".mdx", ".txt")):
            continue
        total += 1
        if path not in registered:
            unregistered += 1
            if any(path.startswith(prefix) for prefix in archive_roots):
                under_archive += 1
    return {
        "state": "tracked-text-aggregate", "tracked_text_count": total,
        "unregistered_total": unregistered,
        "under_archive_directory_count": under_archive,
        "unregistered_elsewhere_count": unregistered - under_archive,
        "private_path_candidates_skipped": private_skipped,
        "paths_or_contents_exported": False,
    }


def build_coverage(corpus: Mapping[str, Any], comments: List[Mapping[str, Any]], *,
                   owner: str, tracked_paths: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Match owner-posted textual claims to current body hashes; never certify semantic truth."""
    rows = _check_corpus(corpus)
    if not isinstance(owner, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", owner):
        raise ValueError("invalid expected issue commenter")
    if not isinstance(comments, list) or len(comments) > MAX_COMMENTS:
        raise ValueError("issue comment budget exceeded")
    claimed = defaultdict(set)
    semantic_comments = 0
    untrusted_comments = 0
    receipt_rows = 0
    for comment in comments:
        if not isinstance(comment, dict):
            raise ValueError("invalid issue comment")
        body = comment.get("body")
        if not isinstance(body, str) or len(body.encode("utf-8")) > MAX_COMMENT_BYTES:
            raise ValueError("invalid or oversized issue comment")
        user = comment.get("user")
        login = user.get("login") if isinstance(user, dict) else None
        if login != owner:
            untrusted_comments += 1
            continue
        if SEMANTIC_CLAIM.search(body) is None:
            continue
        semantic_comments += 1
        for match in RECEIPT.finditer(body):
            claimed[match.group(1)].add(match.group(2))
            receipt_rows += 1

    by_status: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"total": 0, "current_claim": 0, "stale_claim": 0, "pending": 0}
    )
    seen = set()
    pending = []
    readable = 0
    current = 0
    stale = 0
    private = 0
    unreadable = 0
    archive_directories = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid corpus row")
        if row.get("lane") == "personal-excluded":
            private += 1
            continue  # Do not access the private identifier, title, or body.
        identity = row.get("id")
        if not isinstance(identity, str) or not re.fullmatch(ID_PATTERN, identity) or identity in seen:
            raise ValueError("corpus contains missing or duplicated non-private IDs")
        seen.add(identity)
        status = row.get("status", "")
        if status not in STATUS_ORDER:
            raise ValueError("unknown non-private status")
        by_status[status]["total"] += 1
        body = row.get("body")
        if isinstance(body, dict) and body.get("status") == "archive-directory-observed":
            if status != "archived" or body.get("directory_identity_observed") is not True:
                raise ValueError("unverified archive directory identity")
            archive_directories += 1
            continue  # A directory is not a readable document; audit separately.
        digest = body.get("sha256") if isinstance(body, dict) else None
        available = bool(
            isinstance(body, dict) and body.get("status") == "read"
            and isinstance(digest, str) and SHA.fullmatch(digest)
        )
        if available:
            readable += 1
        else:
            unreadable += 1
        exact = available and digest in claimed.get(identity, set())
        old = bool(claimed.get(identity)) and not exact
        if exact:
            by_status[status]["current_claim"] += 1
            current += 1
        else:
            by_status[status]["pending"] += 1
            if old:
                by_status[status]["stale_claim"] += 1
                stale += 1
            signals = row.get("signals") if isinstance(row.get("signals"), list) else []
            p0 = any(
                isinstance(s, str) and s.startswith(
                    ("registered-unfilled", "frontmatter-drift", "body-unavailable")
                ) for s in signals
            )
            pending.append((
                0 if p0 else 1, STATUS_ORDER[status], identity, status,
                "body-unavailable" if not available else "stale-claim" if old else "not-reviewed"
            ))
    if private != corpus.get("private_excluded_count"):
        raise ValueError("private exclusion count differs from corpus")
    pending.sort()
    non_private = len(rows) - private
    reviewable = non_private - archive_directories
    if corpus.get("archive_directory_observed_count", archive_directories) != archive_directories:
        raise ValueError("archive directory count differs from corpus")
    inventory = _tracked_text_inventory(rows, tracked_paths)
    all_registered_claimed = current == reviewable and unreadable == 0
    unregistered = inventory["unregistered_total"]
    if all_registered_claimed and unregistered == 0:
        state = "registered-text-claims-complete-unverified"
    elif all_registered_claimed:
        state = "registered-text-claims-complete-scope-incomplete"
    else:
        state = "needs-semantic-review"
    return {
        "schema_version": PROJECTION,
        "status": state,
        "source_revision": corpus["source_revision"],
        "corpus_report_sha256": corpus["report_sha256"],
        "journal_issue": 176,
        "journal_expected_author": owner,
        "self_reported_only": True,
        "machine_semantic_verification_performed": False,
        "owner_approval_performed": False,
        "canonical_write_performed": False,
        "private_content_exported": False,
        "registry_item_count": len(rows),
        "private_excluded_count": private,
        "non_private_count": non_private,
        "reviewable_blob_count": reviewable,
        "archive_directory_structural_count": archive_directories,
        "registered_text_claims_complete": all_registered_claimed,
        "all_knowledge_semantically_verified": False,
        "unregistered_tracked_text_inventory": inventory,
        "machine_readable_body_count": readable,
        "body_unavailable_count": unreadable,
        "current_body_claim_count": current,
        "stale_body_claim_count": stale,
        "pending_body_claim_count": reviewable - current,
        "matched_issue_comment_count": semantic_comments,
        "untrusted_issue_comment_count": untrusted_comments,
        "journal_receipt_rows": receipt_rows,
        "by_status": dict(sorted(by_status.items())),
        "next_review_queue": [
            {"id": id_, "status": state, "reason": reason}
            for _, __, id_, state, reason in pending[:MAX_QUEUE]
        ],
        "queue_total": len(pending),
        "queue_truncated": len(pending) > MAX_QUEUE,
    }


def _git_tracked_paths(root: pathlib.Path) -> List[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=20,
    )
    if result.returncode != 0 or len(result.stdout) > 4 * 1024 * 1024:
        raise ValueError("tracked path inventory unavailable or over budget")
    return [value.decode("utf-8", errors="strict") for value in result.stdout.split(b"\x00") if value]


def _bounded_json(path: pathlib.Path) -> Any:
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("audit input exceeds budget")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=pathlib.Path, required=True)
    parser.add_argument("--comments-jsonl", type=pathlib.Path, required=True)
    parser.add_argument("--owner", default="jiying2007")
    parser.add_argument("--repo-root", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)
    try:
        corpus = _bounded_json(args.corpus)
        if args.comments_jsonl.stat().st_size > MAX_INPUT_BYTES:
            raise ValueError("issue comments exceed byte budget")
        comments = [
            json.loads(line) for line in args.comments_jsonl.read_text(encoding="utf-8").splitlines() if line
        ]
        tracked_paths = _git_tracked_paths(args.repo_root) if args.repo_root is not None else None
        result = build_coverage(corpus, comments, owner=args.owner, tracked_paths=tracked_paths)
        # Comments stay in ignored .tmp; the output has only bounded non-private IDs.
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({key: result[key] for key in (
            "status", "source_revision", "non_private_count", "reviewable_blob_count", "current_body_claim_count",
            "stale_body_claim_count", "pending_body_claim_count", "private_excluded_count",
        )}, sort_keys=True))
        return 0
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "invalid", "reason": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
