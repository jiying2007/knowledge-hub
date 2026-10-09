"""Provider-owned candidate capture and verified, content-bound receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import tempfile
import time
from typing import Any, Dict

from .common import (
    KnowledgeHubError, file_sha256, load_json, load_markdown, normalize_relpath,
    read_utf8_bounded, registry_items, repository_root, resolve_inside,
    resolve_today, route_rows,
)
from .lifecycle import capture
from .model import FRONTMATTER_MIRROR_FIELDS
from .security import scan_secret_text
from .schemas import validate_instance
from .candidate_duplicates import duplicate_hints, duplicate_inventory
from .archive_observability import attach_trace
from .store import WriteConflict


POLICY = "registry/provider-archive-policy.json"
LOW_RISK_KINDS = {
    "validation", "debug-record", "runbook", "audit", "codex-session",
    "project-archive", "external-source-note",
}
SAFE_METADATA = {
    "title", "summary_zh", "tags", "primary_language", "source_language",
    "translation_status", "terminology_status",
}


def _archive_context(root: pathlib.Path, args: argparse.Namespace):
    policy = load_json(root / POLICY)
    if validate_instance(root, "provider-archive-policy-v1", policy)["status"] != "pass":
        raise KnowledgeHubError("archive policy structure is invalid")
    if (not isinstance(policy, dict) or policy.get("schema_version") != 1
            or policy.get("mode") != "candidate-only" or policy.get("enabled") is not True):
        raise KnowledgeHubError("provider candidate archive policy is disabled or invalid")
    if args.kind not in LOW_RISK_KINDS or args.kind not in policy.get("allowed_kinds", []):
        raise KnowledgeHubError("archive kind requires manual review")
    if re.fullmatch(r"[a-z0-9][a-z0-9-]{0,80}", args.project) is None:
        raise KnowledgeHubError("archive project id is invalid")
    if not args.sanitized:
        raise KnowledgeHubError("archive requires a sanitized reusable conclusion")
    owners = load_json(root / "registry/owners.json", {}).get("owners", [])
    if not isinstance(owners, list) or any(not isinstance(row, dict) for row in owners):
        raise KnowledgeHubError("archive policy owners are invalid")
    owner = policy.get("owner_id")
    if not owner or owner not in {row.get("id") for row in owners}:
        raise KnowledgeHubError("archive policy owner is not registered")
    routes = [row for row in route_rows(root) if row.get("project_id") == args.project]
    if len(routes) != 1:
        raise KnowledgeHubError("archive requires one explicit registered project route")
    route = routes[0]
    maximum = policy.get("maximum_bytes")
    if not isinstance(maximum, int) or isinstance(maximum, bool) or not 1 <= maximum <= 131072:
        raise KnowledgeHubError("archive byte budget is invalid")
    # Read once; capture the same checked bytes, avoiding an input change between scan and write.
    raw = read_utf8_bounded(pathlib.Path(args.source).expanduser(), maximum, "archive source")
    if scan_secret_text(raw):
        raise KnowledgeHubError("archive source contains secret-like material")
    if re.search(r"/home/[^/\s]+/|/vsdata/|\b(?:\d{1,3}\.){3}\d{1,3}\b", raw):
        raise KnowledgeHubError("archive source contains private path or address material")
    if re.search(r'"type"\s*:\s*"(?:session_meta|response_item|event_msg|turn_context)"', raw):
        raise KnowledgeHubError("raw session content cannot be archived")
    return owner, route, raw


def archive(root: pathlib.Path, args: argparse.Namespace) -> Dict[str, Any]:
    owner, route, raw = _archive_context(root, args)
    with tempfile.TemporaryDirectory(prefix="kh-provider-archive-") as temporary:
        checked = pathlib.Path(temporary) / "conclusion.md"
        checked.write_text(raw, encoding="utf-8")
        metadata, body = load_markdown(checked)
        if set(metadata) - SAFE_METADATA:
            raise KnowledgeHubError("archive input metadata must not assert lifecycle or review authority")
        if not body.strip():
            raise KnowledgeHubError("archive conclusion is empty")
        title = args.title or str(metadata.get("title", ""))
        if not title:
            match = re.search(r"(?m)^#\s+(.+)$", body)
            title = match.group(1).strip() if match else ""
        if (not title or len(title) > 512 or scan_secret_text(title)
                or re.search(r"/home/[^/\s]+/|/vsdata/|\b(?:\d{1,3}\.){3}\d{1,3}\b", title)):
            raise KnowledgeHubError("archive requires a safe title")
        source_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        identity = json.dumps([args.project, args.kind, title, source_hash], ensure_ascii=False)
        operation_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        item_id = "provider-{}-{}".format(args.project, operation_id[:24])
        lane = "validation_path" if args.kind == "validation" else "archive_path"
        base = normalize_relpath(str(route.get(lane, "")))
        # Only host registry routes determine destinations, never proposal paths or natural-language guesses.
        if not base.startswith(("projects/", "governance/product/", "domains/codex/")):
            raise KnowledgeHubError("archive route is outside candidate storage")
        target = base + "/" + item_id + ".md"
        domain = ("projects/" + args.project if base.startswith("projects/")
                  else "codex" if base.startswith("domains/codex/") else "governance")
        rows = duplicate_inventory(root, registry_items(root))
        existing = next((row for row in rows if row.get("id") == item_id), None)
        if existing:
            if (existing.get("path") != target or existing.get("status") != "reviewing"
                    or existing.get("owner") != owner or existing.get("promotion") != "none"
                    or existing.get("source", {}).get("source_sha256") != source_hash):
                raise KnowledgeHubError("archive retry conflicts with existing item")
            persisted_metadata, persisted_body = load_markdown(resolve_inside(root, target))
            if (persisted_body != body or any(
                    field in existing and persisted_metadata.get(field) != existing[field]
                    for field in FRONTMATTER_MIRROR_FIELDS)):
                raise KnowledgeHubError("archive retry detected content drift")
            return _receipt(root, existing, operation_id, source_hash, "ALREADY_ARCHIVED", False)
        if resolve_inside(root, target).exists():
            raise KnowledgeHubError("archive target already exists without registry identity")
        today, _ = resolve_today(args.as_of)
        result = capture(
            root, checked, args.kind, target, today, args.apply,
            item_id=item_id, title=title, domain=domain, owner=owner,
            scope="project-specific" if base.startswith("projects/") else "team-general",
            status="reviewing", generated_by_ai=True,
            tags=_metadata_tags(metadata, args.kind),
            summary_zh=str(metadata.get("summary_zh", "")),
            source_type="provider-candidate-archive",
            source_from="provider-policy-sha256:{};operation:{}".format(file_sha256(root / POLICY), operation_id),
        )
    if not args.apply:
        return {
            "schema_version": "knowledge-provider.archive-receipt/v1",
            "status": "PLANNED", "persisted": False, "read_only": True,
            "write_performed": False, "source_sha256": source_hash,
            "content_sha256": next(row['after_sha256'] for row in result['transaction']['writes'] if row['path'] == target),
            "operation_id": operation_id, "item_id": item_id, "target": target,
            "changed_count": result["transaction"]["changed_count"],
            "related_candidates": duplicate_hints(rows, title, str(metadata.get("summary_zh", "")), domain,
                                                  body=body, scope="project-specific" if base.startswith("projects/") else "team-general"),
        }
    row = next((row for row in registry_items(root) if row.get("id") == item_id), None)
    if row is None or result.get("status") != "applied":
        raise KnowledgeHubError("archive persistence readback failed")
    persisted_metadata, persisted_body = load_markdown(resolve_inside(root, target))
    if persisted_body != body or persisted_metadata.get("id") != item_id:
        raise KnowledgeHubError("archive body readback failed")
    receipt = _receipt(root, row, operation_id, source_hash, "ARCHIVED", True)
    receipt.update(transaction_id=result["transaction"]["transaction_id"],
                   related_candidates=duplicate_hints(rows, title, str(metadata.get("summary_zh", "")), domain, exclude_id=item_id,
                                                       body=body, scope=row.get('scope', ''), version=row.get('version', '')))
    return receipt


def _receipt(root, item, operation_id, source_hash, status, wrote):
    return {
        "schema_version": "knowledge-provider.archive-receipt/v1",
        "status": status, "persisted": True, "write_performed": wrote,
        "operation_id": operation_id, "item_id": item["id"], "target": item["path"],
        "candidate_status": item["status"], "source_sha256": source_hash,
        "content_sha256": file_sha256(resolve_inside(root, item["path"])),
        "promotion": "none", "active_promoted": False, "owner_review_performed": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Archive sanitized conclusions as reviewing candidates; dry-run by default.")
    parser.add_argument("--root", default="")
    parser.add_argument("--project", required=True)
    parser.add_argument("--source", default='')
    parser.add_argument("--kind", default='validation')
    parser.add_argument('--reconcile-operation', default='')
    parser.add_argument('--expected-content-sha256', default='')
    parser.add_argument("--title", default="")
    parser.add_argument("--sanitized", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    return run(args)


def run(args):
    started = time.monotonic()
    try:
        if getattr(args, 'reconcile_operation', ''):
            if args.apply:
                raise KnowledgeHubError('reconciliation is read-only')
            from .provider_reconcile import reconcile_archive
            result = reconcile_archive(repository_root(args.root), args.project, args.reconcile_operation,
                                       getattr(args, 'expected_content_sha256', ''))
            print(json.dumps(result, ensure_ascii=False))
            return 0 if result['status'] in {'VERIFIED', 'PRESENT_UNVERIFIED', 'NOT_FOUND'} else 2
        if not args.source:
            raise KnowledgeHubError('archive requires source')
        if args.apply and args.dry_run:
            raise KnowledgeHubError("--apply conflicts with --dry-run")
        result = _archive_with_retry(repository_root(args.root), args)
    except (KnowledgeHubError, OSError, ValueError, TypeError, AttributeError) as exc:
        # Do not echo source paths, body or attacker-controlled metadata in public errors.
        result = {"schema_version": "knowledge-provider.archive-receipt/v1", "status": "BLOCKED",
                  "persisted": False, "reason_code": _reason_code(exc),
                  "reason": "archive validation or persistence failed; review inputs and host policy"}
        print(json.dumps(result, ensure_ascii=False))
        return 2
    result = attach_trace(repository_root(args.root), result, (time.monotonic() - started) * 1000)
    print(json.dumps(result, ensure_ascii=False))
    return 0


def _reason_code(exc):
    message = str(exc)
    if isinstance(exc, WriteConflict):
        return "conflict"
    if "policy" in message or "owner" in message:
        return "policy-invalid"
    if "route" in message or "project id" in message:
        return "route-invalid"
    if "conflict" in message or "drift" in message or "snapshot" in message or "target already" in message:
        return "conflict"
    return "persistence-failed" if isinstance(exc, OSError) or "readback" in message else "source-rejected"


def _metadata_tags(metadata, kind):
    tags = metadata.get("tags", [])
    if (not isinstance(tags, list) or len(tags) > 32
            or any(not isinstance(tag, str) or not tag.strip() or len(tag) > 128 for tag in tags)):
        raise KnowledgeHubError("archive metadata tags are invalid")
    summary = metadata.get("summary_zh", "")
    if not isinstance(summary, str) or len(summary) > 1000:
        raise KnowledgeHubError("archive metadata summary is invalid")
    return tuple(dict.fromkeys(["provider-archive", kind] + tags))


def _archive_with_retry(root, args):
    _, _, raw = _archive_context(root, args)
    with tempfile.TemporaryDirectory(prefix='kh-provider-retry-') as directory:
        source = pathlib.Path(directory) / 'checked.md'
        source.write_text(raw, encoding='utf-8')
        checked_args = argparse.Namespace(**vars(args))
        checked_args.source = str(source)
        for attempt in range(1, 4):
            try:
                result = archive(root, checked_args)
                result['attempt_count'] = attempt
                return result
            except WriteConflict:
                if attempt == 3:
                    raise
                time.sleep(.05 * attempt)
    raise KnowledgeHubError('archive retry exhausted')


if __name__ == "__main__":
    raise SystemExit(main())
