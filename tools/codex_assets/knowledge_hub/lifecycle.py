"""Capture, promote and retire Knowledge Hub items."""

from __future__ import annotations

import datetime as dt
import pathlib
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .authorization import authorization_rows, load_review_form, require_authorization
from .common import (
    KnowledgeHubError,
    display_path,
    encode_jsonl,
    file_sha256,
    load_jsonl,
    load_markdown,
    normalize_relpath,
    registry_items,
    render_markdown,
    resolve_inside,
    slugify,
    utc_timestamp,
)
from .indexing import CORE_INDEXES, update_core_indexes, update_project_index, update_topic_index
from .model import assert_transition, frontmatter_mirror, require_valid_item
from .review_attestation import confirmation_token, suggested_output_path
from .store import RepositoryTransaction


LIFECYCLE_LEDGER = "registry/lifecycle-events.jsonl"


def _date_plus_days(today: dt.date, days: int = 90) -> str:
    return (today + dt.timedelta(days=days)).isoformat()


def _first_heading(body: str) -> str:
    for line in body.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1)
    return ""


def _first_summary(body: str, fallback: str) -> str:
    paragraphs = re.split(r"\n\s*\n", body)
    for paragraph in paragraphs:
        value = " ".join(line.strip() for line in paragraph.splitlines() if line.strip() and not line.startswith("#"))
        if value:
            return value[:300]
    return fallback


def _source_payload(root: pathlib.Path, source: pathlib.Path) -> Dict[str, Any]:
    resolved = source.expanduser().resolve()
    try:
        relative = resolved.relative_to(root)
        source_from = relative.as_posix()
        source_type = "hub-local-capture"
    except ValueError:
        source_from = display_path(resolved)
        source_type = "local-file-capture"
    return {"type": source_type, "from": source_from, "source_sha256": file_sha256(resolved)}


def _load_index_contents(root: pathlib.Path) -> Dict[str, str]:
    return {relative: (root / relative).read_text(encoding="utf-8") for relative in CORE_INDEXES}


def _add_transaction_text(transaction: RepositoryTransaction, root: pathlib.Path, relative: str, content: str) -> None:
    target = root / relative
    transaction.add_text(relative, content, expected_sha256=file_sha256(target) if target.exists() else "")


def _append_event(root: pathlib.Path, event: Mapping[str, Any]) -> str:
    rows = load_jsonl(root / LIFECYCLE_LEDGER)
    rows.append(dict(event))
    return encode_jsonl(rows)


def _project_name(root: pathlib.Path, domain: str) -> str:
    if not domain.startswith("projects/"):
        return ""
    project_id = domain.split("/", 1)[1]
    for row in (root / "registry" / "projects.json",):
        import json

        data = json.loads(row.read_text(encoding="utf-8"))
        for project in data.get("projects", []):
            if project.get("id") == project_id:
                return str(project.get("name", project_id))
    return project_id


def capture(
    root: pathlib.Path,
    source: pathlib.Path,
    kind: str,
    target: str,
    today: dt.date,
    apply: bool,
    item_id: str = "",
    title: str = "",
    domain: str = "",
    owner: str = "leiwenjun",
    scope: str = "",
    visibility: str = "team-internal",
    status: str = "reviewing",
    review_after: str = "",
    tags: Sequence[str] = (),
    summary_zh: str = "",
    generated_by_ai: bool = False,
    ai_role: str = "drafted",
    ai_model_or_tool: str = "Codex",
    source_type: str = "",
    source_from: str = "",
    registered_source_id: str = "",
    registered_source_path: str = "",
) -> Dict[str, Any]:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise KnowledgeHubError("capture source must be a readable file: {}".format(source))
    if source.suffix.lower() == ".md":
        original_metadata, body = load_markdown(source)
    else:
        original_metadata, body = {}, source.read_text(encoding="utf-8")
    inferred_title = title or str(original_metadata.get("title", "")) or _first_heading(body) or source.stem
    inferred_id = item_id or slugify(str(original_metadata.get("id", "")) or inferred_title) + "-" + today.strftime("%Y%m%d")
    if target == "inbox":
        target = "notes/inbox/{}-{}.md".format(today.isoformat(), slugify(inferred_id))
    target = normalize_relpath(target)
    if not target.endswith(".md"):
        raise KnowledgeHubError("capture target must be a Markdown path")
    companion_path = (
        target[:-3] + ".jsonl"
        if kind == "audit" and target.startswith("artifacts/manifests/")
        else ""
    )
    if not domain:
        if target.startswith("projects/"):
            domain = "/".join(target.split("/")[:2])
        elif target.startswith("domains/codex/"):
            domain = "codex"
        elif target.startswith("domains/embedded/"):
            domain = "embedded"
        elif target.startswith("domains/patents/"):
            domain = "patents"
        elif target.startswith("notes/"):
            domain = "notes"
        else:
            domain = "governance"
    if not scope:
        scope = "project-specific" if domain.startswith("projects/") else "team-general"
    if status not in {"draft", "reviewing", "personal"}:
        raise KnowledgeHubError("capture may only create draft, reviewing or personal items")
    if status == "personal":
        visibility = "personal-local"
    if bool(source_type) != bool(source_from):
        raise KnowledgeHubError("source_type and source_from must be provided together")
    if registered_source_path and not registered_source_id:
        raise KnowledgeHubError("registered_source_path requires registered_source_id")
    source_payload = _source_payload(root, source)
    if source_type and source_from:
        source_payload.update({"type": source_type, "from": source_from})
    if registered_source_id:
        import json

        source_registry = json.loads((root / "registry/sources.json").read_text(encoding="utf-8"))
        known_source_ids = {
            str(row.get("id", ""))
            for row in source_registry.get("sources", [])
            if isinstance(row, dict)
        }
        if registered_source_id not in known_source_ids:
            raise KnowledgeHubError("registered source id does not exist: {}".format(registered_source_id))
        source_payload.update({"type": "registered", "source_id": registered_source_id})
        if registered_source_path:
            source_payload["source_path"] = registered_source_path
    primary_language = str(original_metadata.get("primary_language", "zh-CN"))
    source_language = str(original_metadata.get("source_language", primary_language))
    validation_refs = [
        target,
        "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
    ]
    if companion_path:
        validation_refs.insert(1, companion_path)
    item: Dict[str, Any] = {
        "id": inferred_id,
        "title": inferred_title,
        "kind": kind,
        "domain": domain,
        "path": target,
        "scope": scope,
        "visibility": visibility,
        "status": status,
        "owner": owner,
        "source": source_payload,
        "validation_refs": validation_refs,
        "summary_zh": summary_zh or _first_summary(body, inferred_title),
        "primary_language": primary_language,
        "source_language": source_language,
        "translation_status": str(original_metadata.get("translation_status", "not-required")),
        "terminology_status": str(original_metadata.get("terminology_status", "pending-review")),
        "review_status": "manual-entry-pending-review" if status in {"draft", "reviewing"} else "personal-local",
        "promotion_decision": "none; capture does not authorize active promotion or owner decision",
        "generated_by_ai": generated_by_ai,
        "tags": list(tags) or [kind, "capture", "manual-validation-pending"],
        "review_after": review_after or _date_plus_days(today),
        "promotion": "none",
        "created_at": today.isoformat(),
        "updated_at": today.isoformat(),
        "manual_validation_pending": True,
    }
    if generated_by_ai:
        item.update(
            {
                "ai_role": ai_role,
                "ai_model_or_tool": ai_model_or_tool,
                "ai_generated_at": today.isoformat(),
            }
        )
    current_items = registry_items(root)
    existing = next((row for row in current_items if row.get("id") == inferred_id), None)
    if existing:
        if existing.get("path") == target and (root / target).exists():
            return {
                "action": "capture",
                "status": "no-change",
                "apply_supported": True,
                "id": inferred_id,
                "target": target,
                "message": "Item already exists at the requested target.",
            }
        raise KnowledgeHubError("registry item id already exists: {}".format(inferred_id))
    if any(row.get("path") == target for row in current_items):
        raise KnowledgeHubError("registry path already exists: {}".format(target))
    require_valid_item(item, existing_ids=[str(row.get("id")) for row in current_items])

    mirror = dict(original_metadata)
    mirror.update(frontmatter_mirror(item))
    rendered = render_markdown(mirror, body)
    next_items = list(current_items) + [item]
    core_updates = update_core_indexes(_load_index_contents(root), item)
    project_text = (root / "indexes/by-project.md").read_text(encoding="utf-8")
    topic_text = (root / "indexes/by-topic.md").read_text(encoding="utf-8")
    project_update = update_project_index(project_text, item, _project_name(root, domain))
    topic_update = update_topic_index(topic_text, item)
    event = {
        "event_id": "capture-{}-{}".format(today.strftime("%Y%m%d"), inferred_id),
        "event_type": "capture",
        "item_id": inferred_id,
        "before_status": "missing",
        "after_status": status,
        "authorization_id": "",
        "executed_by": "knowledge-capture",
        "executed_at": utc_timestamp(),
        "evidence_refs": validation_refs,
    }

    transaction = RepositoryTransaction(root)
    _add_transaction_text(transaction, root, target, rendered)
    if companion_path:
        companion = {
            "schema_version": 1,
            "id": inferred_id,
            "status": status,
            "summary_zh": item["summary_zh"],
            "source": source_payload,
            "evidence_refs": [target],
            "validation_refs": validation_refs,
            "review_status": item["review_status"],
            "review_after": item["review_after"],
            "promotion": "none",
            "manual_validation_pending": True,
            "generated_by_ai": generated_by_ai,
            "boundaries": [
                "no owner decision",
                "no active promotion",
                "no memory write",
                "no source project write",
                "no remote publish",
            ],
        }
        _add_transaction_text(transaction, root, companion_path, encode_jsonl([companion]))
    _add_transaction_text(transaction, root, "registry/items.jsonl", encode_jsonl(next_items))
    for relative, content in core_updates.items():
        _add_transaction_text(transaction, root, relative, content)
    _add_transaction_text(transaction, root, "indexes/by-project.md", project_update)
    _add_transaction_text(transaction, root, "indexes/by-topic.md", topic_update)
    _add_transaction_text(transaction, root, LIFECYCLE_LEDGER, _append_event(root, event))
    plan = transaction.plan()
    result: Dict[str, Any] = {
        "action": "capture",
        "status": "planned" if not apply else "applying",
        "apply_supported": True,
        "id": inferred_id,
        "target": target,
        "created_status": status,
        "active_promotion": False,
        "transaction": plan,
    }
    if apply:
        result["transaction"] = transaction.apply().to_dict()
        result["status"] = "applied"
    return result


def _replace_item(items: List[Dict[str, Any]], item: Mapping[str, Any]) -> List[Dict[str, Any]]:
    return [dict(item) if row.get("id") == item.get("id") else row for row in items]


def _mark_authorization_used(root: pathlib.Path, authorization_id: str, today: dt.date) -> str:
    rows = authorization_rows(root)
    for row in rows:
        if row.get("authorization_id") == authorization_id:
            row["status"] = "used"
            row["used_at"] = today.isoformat()
    return encode_jsonl(rows)


def transition(
    root: pathlib.Path,
    item_id: str,
    target_status: str,
    today: dt.date,
    apply: bool,
    authorization_id: str = "",
    review_form: Optional[pathlib.Path] = None,
    expected_item_sha256: str = "",
    reason: str = "",
    superseded_by: str = "",
) -> Dict[str, Any]:
    items = registry_items(root)
    matches = [row for row in items if row.get("id") == item_id]
    if len(matches) != 1:
        raise KnowledgeHubError("item id must resolve to exactly one registry row: {}".format(item_id))
    before = dict(matches[0])
    before_status = str(before.get("status", ""))
    assert_transition(before_status, target_status)
    item_path = resolve_inside(root, str(before["path"]))
    if not item_path.exists():
        raise KnowledgeHubError("item body is missing: {}".format(before["path"]))
    actual_item_sha = file_sha256(item_path)
    if apply and not expected_item_sha256:
        raise KnowledgeHubError("--apply requires --expected-item-sha256")
    if expected_item_sha256 and expected_item_sha256 != actual_item_sha:
        raise KnowledgeHubError("expected item SHA256 does not match current body")

    action_names = ("active-promotion",) if target_status == "active" else (
        "automation-apply-with-review",
        "owner-decision-landing",
        "delete-or-prune",
    )
    auth = None
    review = None
    authorization_errors: List[str] = []
    attestation_errors: List[str] = []
    if authorization_id:
        try:
            auth = require_authorization(root, authorization_id, action_names, today, (item_id, str(before["path"])))
        except KnowledgeHubError as exc:
            authorization_errors.append(str(exc))
    else:
        authorization_errors.append("authorization_id is required")
    if review_form:
        try:
            review = load_review_form(review_form.expanduser().resolve(), item_id)
            expected_token = confirmation_token(
                {
                    "item_id": item_id,
                    "item_path": str(before["path"]),
                    "before_status": before_status,
                    "target_status": target_status,
                    "content_sha256": actual_item_sha,
                }
            )
            if review.get("confirmation_token") != expected_token:
                attestation_errors.append("content review attestation confirmation token does not match")
            if review.get("content_sha256") != actual_item_sha:
                attestation_errors.append("content review attestation SHA256 does not match current body")
            if review.get("expected_before_status") != before_status:
                attestation_errors.append("content review attestation before status does not match")
            if review.get("target_status") != target_status:
                attestation_errors.append("content review attestation target status does not match")
        except KnowledgeHubError as exc:
            attestation_errors.append(str(exc))
    else:
        attestation_errors.append(
            "content review attestation form is required; manual JSON editing is not required"
        )
    expected_decisions = {"active": {"accept", "accept-active"}, "archived": {"retire"}, "superseded": {"supersede"}, "rejected": {"reject"}}
    if review and review.get("review_decision") not in expected_decisions.get(target_status, set()):
        attestation_errors.append("review decision does not confirm target status {}".format(target_status))

    gate_errors = authorization_errors + attestation_errors
    attestation_output = suggested_output_path(
        {
            "item_id": item_id,
            "target_status": target_status,
        },
        today,
    )
    packet_command = (
        "rtk bash ~/knowledge-hub/tools/knowledge-review-attest.sh packet "
        "--id {} --target {} --as-of {} --json"
    ).format(item_id, target_status, today.isoformat())

    plan_result: Dict[str, Any] = {
        "action": "promote" if target_status == "active" else "retire",
        "status": "blocked" if gate_errors else "ready",
        "apply_supported": True,
        "id": item_id,
        "before_status": before_status,
        "target_status": target_status,
        "current_item_sha256": actual_item_sha,
        "authorization_id": authorization_id,
        "review_form": display_path(review_form) if review_form else "",
        "gate_errors": gate_errors,
        "gates": {
            "execution_authorization": {
                "status": "pass" if not authorization_errors else "blocked",
                "required": True,
                "authorization_id": authorization_id,
                "errors": authorization_errors,
                "purpose": "permits the lifecycle write; does not assert content review",
            },
            "content_review_attestation": {
                "status": "pass" if not attestation_errors else "blocked",
                "required": True,
                "review_form": display_path(review_form) if review_form else "",
                "errors": attestation_errors,
                "human_decision_required": True,
                "manual_json_editing_required": False,
                "mechanical_generation_allowed_after_human_decision": True,
                "packet_command": packet_command,
                "suggested_local_form": attestation_output,
            },
        },
        "authorization_boundary": {
            "owner_decision_generated": False,
            "authorization_required": True,
            "human_form_required": True,
            "human_decision_required": True,
            "manual_json_editing_required": False,
            "execution_authorization_separate_from_content_attestation": True,
            "mechanical_form_generation_allowed_after_human_decision": True,
            "expected_body_sha256_required_for_apply": True,
            "memory_write": False,
            "source_project_write": False,
            "remote_publish": False,
        },
        "validation_commands": [
            "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
            "rtk bash ~/knowledge-hub/tools/knowledge-search.sh \"{}\" --json".format(item_id),
            "rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json",
        ],
    }
    if gate_errors:
        if apply:
            raise KnowledgeHubError("lifecycle gates are not satisfied: {}".format("; ".join(gate_errors)))
        return plan_result

    assert auth is not None and review is not None
    after = dict(before)
    after["status"] = target_status
    after["updated_at"] = today.isoformat()
    attestation_mode = str(review["attestation_mode"])
    if attestation_mode == "human-directed-delegation":
        after["review_status"] = "human-directed-delegated-retired"
    else:
        after["review_status"] = "human-reviewed-active" if target_status == "active" else "human-reviewed-retired"
    after["human_reviewed_by"] = review["reviewed_by"]
    after["human_reviewed_at"] = review["reviewed_at"]
    after["human_review_decision"] = review["review_decision"]
    after["review_basis"] = review["review_basis"]
    after["validation_refs"] = list(review["validation_refs"])
    after["promotion_decision"] = reason or str(review["review_basis"])
    after["manual_validation_pending"] = False
    after["review_attestation_id"] = review["attestation_id"]
    after["review_attestation_mode"] = attestation_mode
    after["review_attestation_source_ref"] = review["attestation_source_ref"]
    after["review_attestation_statement_sha256"] = review["attestation_statement_sha256"]
    after["review_confirmation_token"] = review["confirmation_token"]
    after["review_content_sha256"] = review["content_sha256"]
    if superseded_by:
        after["superseded_by"] = superseded_by
    require_valid_item(after)

    metadata, body = load_markdown(item_path)
    metadata.update(frontmatter_mirror(after))
    rendered = render_markdown(metadata, body)
    core_updates = update_core_indexes(_load_index_contents(root), after)
    event = {
        "event_id": "{}-{}-{}".format(target_status, today.strftime("%Y%m%d"), item_id),
        "event_type": "promote" if target_status == "active" else "retire",
        "item_id": item_id,
        "before_status": before_status,
        "after_status": target_status,
        "authorization_id": authorization_id,
        "reviewed_by": review["reviewed_by"],
        "review_attestation_id": str(review["attestation_id"]),
        "review_attestation_mode": attestation_mode,
        "review_attestation_statement_sha256": str(review["attestation_statement_sha256"]),
        "review_confirmation_token": str(review["confirmation_token"]),
        "executed_by": "knowledge-lifecycle",
        "executed_at": utc_timestamp(),
        "evidence_refs": list(review["validation_refs"]),
    }
    transaction = RepositoryTransaction(root)
    transaction.add_text(str(before["path"]), rendered, expected_sha256=actual_item_sha)
    _add_transaction_text(transaction, root, "registry/items.jsonl", encode_jsonl(_replace_item(items, after)))
    for relative, content in core_updates.items():
        _add_transaction_text(transaction, root, relative, content)
    _add_transaction_text(transaction, root, LIFECYCLE_LEDGER, _append_event(root, event))
    _add_transaction_text(transaction, root, "registry/authorizations.jsonl", _mark_authorization_used(root, authorization_id, today))
    if target_status == "active":
        promotions = load_jsonl(root / "registry/promotions.jsonl")
        promotions.append(
            {
                "id": "{}-active-promotion-{}".format(item_id, today.strftime("%Y%m%d")),
                "status": "applied",
                "source": str(review_form),
                "target": str(before["path"]),
                "target_item": item_id,
                "authorization_id": authorization_id,
                "reason": reason or str(review["review_basis"]),
                "created_at": today.isoformat(),
                "review_after": after["review_after"],
            }
        )
        _add_transaction_text(transaction, root, "registry/promotions.jsonl", encode_jsonl(promotions))
    plan_result["transaction"] = transaction.plan()
    if apply:
        plan_result["transaction"] = transaction.apply().to_dict()
        plan_result["status"] = "applied"
    return plan_result
