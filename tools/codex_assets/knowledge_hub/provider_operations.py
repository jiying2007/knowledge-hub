"""Subject-aware candidate writes with stable operation lookup and recovery."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import re
import tempfile

from .common import (KnowledgeHubError, load_jsonl, registry_items, load_markdown, render_markdown,
                     encode_jsonl, resolve_inside, read_utf8_bounded, file_sha256, utc_timestamp)
from .provider_archive import SAFE_METADATA, LOW_RISK_KINDS, _metadata_tags, checked_archive_policy
from .security import scan_secret_text
from .provider_subjects import (OPERATIONS_PATH, digest, subject, authorize, route_subject,
                               item_subject, verify_item, read_guard)
from .store import RepositoryTransaction, snapshot_inputs, WriteConflict
from .lifecycle import capture


def safe_text(value):
    if (scan_secret_text(value) or re.search(r"/home/[^/\s]+/|/vsdata/|\b(?:\d{1,3}\.){3}\d{1,3}\b", value)
            or re.search(r'"type"\s*:\s*"(?:session_meta|response_item|event_msg|turn_context)"', value)):
        raise KnowledgeHubError("SOURCE_REJECTED")


def operations(root):
    rows = load_jsonl(root / OPERATIONS_PATH)
    from .schemas import validate_instance
    if any(validate_instance(root, "provider-operation-ledger-v1", row)["status"] != "pass" for row in rows):
        raise KnowledgeHubError("SCHEMA_INVALID")
    ids = [r.get("operation_id") for r in rows]
    if len(ids) != len(set(ids)) or any(re.fullmatch(r"[a-f0-9]{64}", str(i)) is None for i in ids):
        raise KnowledgeHubError("SCHEMA_INVALID")
    return rows


def response(status, operation_id=None, item=None, content_hash=None, wrote=False, transaction_id=None, reason=None):
    verified = status in {"ARCHIVED", "ALREADY_ARCHIVED", "ASSIGNED", "ALREADY_ASSIGNED", "VERIFIED"}
    uncertain = status in {"UNKNOWN", "CONFLICT", "NOT_FOUND", "PRESENT_UNVERIFIED"}
    target = item_subject(item) if item else None
    return {"schema_version": "knowledge-provider.operation-receipt/v2", "status": status,
            "persisted": True if verified else None if uncertain else False,
            "write_performed": None if status == "UNKNOWN" else wrote,
            "operation_id": operation_id, "item_id": item.get("id") if item else None,
            "subject_ref": target, "assignment_state": "unassigned" if target and target["type"] == "unassigned" else "assigned" if target else None,
            "project_archived": bool(verified and target and target["type"] == "project"),
            "candidate_status": item.get("status") if item else None,
            "content_sha256": content_hash, "source_sha256": item.get("source", {}).get("source_sha256") if item else None,
            "transaction_id": transaction_id, "promotion": "none", "active_promoted": False,
            "owner_review_performed": False, "reason_codes": [reason] if reason else []}


def frozen_source(args):
    raw = read_utf8_bounded(pathlib.Path(args.source).expanduser(), 131072, "archive source")
    safe_text(raw)
    if not args.sanitized:
        raise KnowledgeHubError("SOURCE_REJECTED")
    with tempfile.TemporaryDirectory(prefix="provider-v2-parse-") as directory:
        checked = pathlib.Path(directory) / "checked.md"
        checked.write_text(raw, encoding="utf-8")
        metadata, body = load_markdown(checked)
    if set(metadata) - SAFE_METADATA or not body.strip():
        raise KnowledgeHubError("SOURCE_REJECTED")
    if any(not isinstance(value, str) for key, value in metadata.items() if key != "tags"):
        raise KnowledgeHubError("SOURCE_REJECTED")
    title = args.title or str(metadata.get("title", ""))
    if not title:
        match = re.search(r"(?m)^#\s+(.+)$", body)
        title = match.group(1).strip() if match else ""
    if not title or len(title) > 512:
        raise KnowledgeHubError("SOURCE_REJECTED")
    safe_text(title)
    provenance = {"source_kind": "session-conclusion", "source_ref": "sanitized-conclusion", "verification_state": "declared"}
    if getattr(args, "provenance_file", ""):
        from .common import load_json
        provenance = load_json(pathlib.Path(args.provenance_file), maximum_bytes=65536)
        allowed = {"source_kind", "source_ref", "verification_state", "manifest_sha256"}
        if (not isinstance(provenance, dict) or set(provenance) - allowed
                or not {"source_kind", "source_ref", "verification_state"} <= set(provenance)
                or provenance["source_kind"] not in {"manual", "document", "session-conclusion", "file-manifest", "artifact-reference"}
                or provenance["verification_state"] not in {"declared", "observed", "partial", "unstable"}
                or any(not isinstance(v, str) or len(v) > 512 for v in provenance.values())):
            raise KnowledgeHubError("SCHEMA_INVALID")
        safe_text(str(provenance))
    return raw, metadata, body, title, provenance


def archive_v2(root, args):
    archive_policy = checked_archive_policy(root, args.kind)
    frozen = frozen_source(args)
    if len(frozen[0].encode("utf-8")) > archive_policy["maximum_bytes"]:
        raise KnowledgeHubError("POLICY_DENIED")
    for attempt in range(3):
        try:
            return _archive(root, args, frozen)
        except WriteConflict:
            if attempt == 2:
                raise


def _replay_operation(op_rows, operation_id, target, args, title, source_hash):
    existing = next((r for r in op_rows if r["operation_id"] == operation_id), None)
    if not existing and target["type"] == "project" and not args.provenance_file:
        legacy_id = hashlib.sha256(json.dumps([target["id"], args.kind, title, source_hash], ensure_ascii=False).encode()).hexdigest()
        existing = next((r for r in op_rows if r["operation_id"] == legacy_id and r["api_version"] == 1), None)
    return existing


def _archive(root, args, frozen):
    raw, metadata, body, title, provenance = frozen
    target = subject(args.subject)
    if args.kind not in LOW_RISK_KINDS:
        raise KnowledgeHubError("POLICY_DENIED")
    host, actor = authorize(root, "archive", target)
    archive_policy = checked_archive_policy(root, args.kind)
    if len(raw.encode("utf-8")) > archive_policy["maximum_bytes"]:
        raise KnowledgeHubError("POLICY_DENIED")
    if target["type"] == "domain" and getattr(args, "declared_scope", "") != "team-general":
        raise KnowledgeHubError("GENERALIZATION_REQUIRED")
    route = route_subject(root, target, args.kind)
    source_hash = hashlib.sha256(raw.encode()).hexdigest()
    operation_id = digest({"api": 2, "action": "archive", "subject_ref": target, "kind": args.kind,
                           "title": title, "source_sha256": source_hash, "provenance": provenance})
    args._operation_id = operation_id
    from .provider_onboarding import resolve_workspace
    origin = resolve_workspace(root, args.cwd)
    origin_subject = origin["subject_ref"]
    conflict = origin["state"] == "conflict" or bool(target["type"] == "project" and origin_subject and origin_subject != target)
    if conflict:
        if not args.apply and not args.authorization_id:
            result = response("PLANNED", operation_id, reason="ROUTE_CONFLICT")
            result["expected_hash"] = operation_id
            return result
        authorize(root, "archive", target, args.authorization_id, expected_hash=operation_id, require_exact=True)
    item_id = "provider-v2-" + operation_id
    with read_guard(root):
        op_rows = operations(root)
        op_hash = file_sha256(root / OPERATIONS_PATH) if (root / OPERATIONS_PATH).is_file() else ""
        existing = _replay_operation(op_rows, operation_id, target, args, title, source_hash)
        if existing:
            item = next((r for r in registry_items(root) if r.get("id") == existing["item_id"]), None)
            if not item:
                raise KnowledgeHubError("CONTENT_DRIFT")
            current_subject = item_subject(item) or subject(existing["current_subject_ref"])
            authorize(root, "read", current_subject)
            actual, _, _ = verify_item(root, item, existing["current_content_sha256"])
            return response("ALREADY_ARCHIVED", existing["operation_id"], dict(item, subject_ref=current_subject), actual)
        if any(r.get("id") == item_id for r in registry_items(root)):
            raise KnowledgeHubError("CONTENT_DRIFT")
    path = route["base"] + "/" + item_id + ".md"
    with tempfile.TemporaryDirectory(prefix="provider-v2-capture-") as directory:
        checked = pathlib.Path(directory) / "checked.md"
        checked.write_text(raw, encoding="utf-8")

        def prepare(transaction, item, rendered):
            row = {"operation_id": operation_id, "api_version": 2, "action": "archive", "item_id": item_id,
                   "created_subject_ref": target, "current_subject_ref": target,
                   "current_content_sha256": hashlib.sha256(transaction.writes[item["path"]].content).hexdigest(),
                   "transaction_id": transaction.transaction_id, "principal_id": actor}
            # Bind this ledger to the same snapshot used for the replay check.
            transaction.expected_inputs[OPERATIONS_PATH] = op_hash
            transaction.add_text(OPERATIONS_PATH, encode_jsonl(op_rows + [row]))
            authorize(root, "archive", target)
            if checked_archive_policy(root, args.kind) != archive_policy:
                raise WriteConflict("archive policy changed before commit")
            if resolve_workspace(root, args.cwd) != origin:
                raise WriteConflict("workspace changed before commit")
            if conflict:
                authorize(root, "archive", target, args.authorization_id, expected_hash=operation_id, require_exact=True)
            if route_subject(root, target, args.kind) != route:
                raise WriteConflict("route changed before commit")
            args._commit_started = args.apply

        result = capture(root, checked, args.kind, path, dt.date.today(), args.apply,
                         item_id=item_id, title=title, domain=route["domain"], owner=host["owner_id"],
                         scope=route["scope"], visibility=route["visibility"], status="reviewing",
                         generated_by_ai=True, tags=_metadata_tags(metadata, args.kind),
                         summary_zh=metadata.get("summary_zh", ""), source_type="provider-candidate-archive",
                         source_from="operation:" + operation_id,
                         provider_metadata={"subject_ref": target, "created_subject_ref": target, "principal_id": actor,
                                            "provider_operation_id": operation_id, "provenance": provenance}, prepare_hook=prepare)
    if not args.apply:
        return response("PLANNED", operation_id)
    with read_guard(root):
        row = next(r for r in registry_items(root) if r["id"] == item_id)
        op = next(r for r in operations(root) if r["operation_id"] == operation_id)
        actual, _, _ = verify_item(root, row, op["current_content_sha256"])
        return response("ARCHIVED", operation_id, row, actual, True, result["transaction"]["transaction_id"])


def _assignment_views(root, transaction, after, rendered, next_items, op_rows):
    from .indexing import update_core_indexes, update_project_index, update_topic_index, CORE_INDEXES
    texts = {p: (root / p).read_text() for p in CORE_INDEXES}
    for path, text in update_core_indexes(texts, after).items():
        transaction.add_text(path, text)
    transaction.add_text("indexes/by-project.md", update_project_index((root / "indexes/by-project.md").read_text(), after))
    transaction.add_text("indexes/by-topic.md", update_topic_index((root / "indexes/by-topic.md").read_text(), after))
    from .obsidian_view import stage_obsidian_views
    staged = stage_obsidian_views(root, transaction, items=next_items, document_overrides={after["path"]: rendered})
    if staged["missing_files"] or staged["content_drifts"]:
        raise KnowledgeHubError("CONTENT_DRIFT")
    new_hash = hashlib.sha256(transaction.writes[after["path"]].content).hexdigest()
    for op in op_rows:
        if op["item_id"] == after["id"]:
            op["current_content_sha256"] = new_hash
    transaction.add_text(OPERATIONS_PATH, encode_jsonl(op_rows))
    return new_hash


def assign(root, args):
    target = subject(args.subject)
    request_hash = digest({"action": "assign", "item_id": args.item_id, "subject_ref": target,
                           "expected_content_sha256": args.expected_content_sha256})
    args._operation_id = request_hash
    with read_guard(root):
        inputs = snapshot_inputs(root)
        rows = registry_items(root)
        item = next((r for r in rows if r.get("id") == args.item_id), None)
        if not item:
            raise KnowledgeHubError("ITEM_NOT_FOUND")
        old_subject = item_subject(item)
        if not old_subject:
            legacy = next((r for r in operations(root) if r["item_id"] == item["id"]), None)
            old_subject = legacy["current_subject_ref"] if legacy else None
        if not old_subject:
            raise KnowledgeHubError("UPGRADE_REQUIRED")
        authorize(root, "read", old_subject)
        op_rows = operations(root)
        previous = next((r for r in op_rows if r["operation_id"] == request_hash), None)
        if previous:
            actual, _, _ = verify_item(root, item, previous["current_content_sha256"])
            return response("ALREADY_ASSIGNED", request_hash, item, actual)
        if item.get("status") != "reviewing" or item.get("promotion") != "none":
            raise KnowledgeHubError("POLICY_DENIED")
        actual, metadata, body = verify_item(root, item, args.expected_content_sha256)
        route = route_subject(root, target, item["kind"])
        widening = item["visibility"] != route["visibility"]
        authorize(root, "assign", target, args.authorization_id, widening, request_hash)
        if target["type"] == "domain" and args.declared_scope != "team-general":
            raise KnowledgeHubError("GENERALIZATION_REQUIRED")
        new_path = route["base"] + "/" + item["id"] + ".md"
        if new_path != item["path"] and resolve_inside(root, new_path).exists():
            raise KnowledgeHubError("ROUTE_CONFLICT")
        after = dict(item, subject_ref=target, created_subject_ref=item.get("created_subject_ref", old_subject), domain=route["domain"], scope=route["scope"],
                     visibility=route["visibility"], path=new_path, updated_at=dt.date.today().isoformat())
        # Replace only exact self-references; unrelated provenance is retained.
        for key in ("validation_refs", "evidence_refs"):
            after[key] = [new_path if r == item["path"] else r for r in item.get(key, [])]
        from .model import require_valid_item, merge_frontmatter_mirror
        require_valid_item(after)
        mirror = merge_frontmatter_mirror(metadata, after)
        mirror["subject_ref"] = target
        mirror["created_subject_ref"] = after["created_subject_ref"]
        rendered = render_markdown(mirror, body)
        new_hash = hashlib.sha256(rendered.encode()).hexdigest()
        for op in op_rows:
            if op["item_id"] == item["id"]:
                op.update(current_subject_ref=target, current_content_sha256=new_hash)
        transaction = RepositoryTransaction(root, expected_inputs=inputs)
        transaction.add_text(new_path, rendered)
        if new_path != item["path"]:
            transaction.add_delete(item["path"], actual)
        op_rows.append({"operation_id": request_hash, "api_version": 2, "action": "assign", "item_id": item["id"],
                        "created_subject_ref": old_subject, "current_subject_ref": target, "current_content_sha256": new_hash,
                        "transaction_id": transaction.transaction_id, "principal_id": after.get("principal_id", ""),
                        "authorization_ref": args.authorization_id})
        next_items = [after if r["id"] == item["id"] else r for r in rows]
        transaction.add_text("registry/items.jsonl", encode_jsonl(next_items))
        transaction.add_text(OPERATIONS_PATH, encode_jsonl(op_rows))
        events = load_jsonl(root / "registry/lifecycle-events.jsonl")
        events.append({"event_id": "assign-" + request_hash, "event_type": "reassign", "item_id": item["id"],
                       "before_status": "reviewing", "after_status": "reviewing", "authorization_id": args.authorization_id,
                       "executed_by": "knowledge-provider", "executed_at": utc_timestamp(), "evidence_refs": [new_path]})
        transaction.add_text("registry/lifecycle-events.jsonl", encode_jsonl(events))
        new_hash = _assignment_views(root, transaction, after, rendered, next_items, op_rows)
    if not args.apply:
        result = response("PLANNED", request_hash)
        result["expected_hash"] = request_hash
        return result
    args._commit_started = True
    result = transaction.apply()
    with read_guard(root):
        actual, _, _ = verify_item(root, after, new_hash)
    return response("ASSIGNED", request_hash, after, actual, True, result.transaction_id)


def reconcile(root, operation_id, expected_hash=""):
    if re.fullmatch(r"[a-f0-9]{64}", operation_id) is None:
        raise KnowledgeHubError("SCHEMA_INVALID")
    with read_guard(root):
        op = next((r for r in operations(root) if r["operation_id"] == operation_id), None)
        if not op:
            return response("NOT_FOUND", operation_id)
        row = next((r for r in registry_items(root) if r["id"] == op["item_id"]), None)
        if not row:
            return response("CONFLICT", operation_id, reason="CONTENT_DRIFT")
        current_subject = item_subject(row) or subject(op["current_subject_ref"])
        authorize(root, "read", current_subject)
        try:
            actual, _, _ = verify_item(root, row, op["current_content_sha256"])
        except KnowledgeHubError:
            return response("CONFLICT", operation_id, reason="CONTENT_DRIFT")
        if expected_hash and actual != expected_hash:
            return response("CONFLICT", operation_id, reason="CONTENT_DRIFT")
        view = dict(row, subject_ref=current_subject)
        return response("VERIFIED" if expected_hash else "PRESENT_UNVERIFIED", operation_id, view, actual)


def import_legacy(root, apply=False):
    """Observe legacy identities without claiming their historical validation."""
    with read_guard(root):
        inputs = snapshot_inputs(root)
        rows = operations(root)
        from .common import route_rows
        routes = route_rows(root)
        ids = {r["operation_id"] for r in rows}
        for item in registry_items(root):
            match = re.search(r"operation:([a-f0-9]{64})", item.get("source", {}).get("from", ""))
            if not match or match.group(1) in ids or item.get("source", {}).get("type") != "provider-candidate-archive":
                continue
            targets = [r for r in routes if any(item["path"].startswith(r.get(k, "!") + "/") for k in ("archive_path", "validation_path"))]
            if len(targets) != 1:
                raise KnowledgeHubError("ROUTE_CONFLICT")
            target = subject("project:" + targets[0]["project_id"])
            actual, _, _ = verify_item(root, item)
            rows.append({"operation_id": match.group(1), "api_version": 1, "action": "archive", "item_id": item["id"],
                         "created_subject_ref": target, "current_subject_ref": target,
                         "current_content_sha256": actual, "transaction_id": None, "principal_id": None,
                         "historical_validation_verified": False})
            ids.add(match.group(1))
    transaction = RepositoryTransaction(root, expected_inputs=inputs)
    transaction.add_text(OPERATIONS_PATH, encode_jsonl(rows))
    result = transaction.apply().to_dict() if apply else transaction.plan()
    return {"status": "IMPORTED" if apply else "PLANNED", "persisted": apply, "operation_count": len(rows), "transaction": result}
