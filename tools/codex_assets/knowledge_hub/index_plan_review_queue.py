"""Review-queue projection helpers for index-plan."""

import argparse
import collections
import pathlib
from typing import Counter

REVIEW_CONTENT_BOUND_DECISIONS = {"accept-as-review-record", "archive-only", "reject"}

root = pathlib.Path(".")
args = argparse.Namespace()

def _unconfigured_file_sha256(relative_path):
    return ""

repository_file_sha256 = _unconfigured_file_sha256

def configure_review_queue(root_value, args_value, file_sha256):
    global root, args, repository_file_sha256
    root = root_value
    args = args_value
    repository_file_sha256 = file_sha256

def first_present_field(row, fields):
    for field in fields:
        value = row.get(field)
        if isinstance(value, list):
            if value:
                return field, value
        elif value:
            return field, value
    return "missing", ""

def is_blank(value):
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return not value
    if isinstance(value, dict):
        return not value
    return False

def as_list(value):
    return value if isinstance(value, list) else []

def review_priority_for_item(item):
    status_value = str(item.get("status", ""))
    path_text = str(item.get("path", ""))
    tags = set(str(tag) for tag in as_list(item.get("tags", [])))
    promotion_like = (
        status_value == "active"
        or path_text == "AGENTS.md"
        or path_text.startswith("domains/embedded/standards/")
        or path_text.startswith("src/codex-home/vendor/skills/")
        or "promoted" in tags
        or "team-standard" in tags
    )
    if promotion_like:
        return "P0"
    if status_value == "reviewing":
        return "P1"
    if status_value in {"archived", "personal"}:
        return "P3"
    return "P2"

def source_looks_external(source):
    path_text = str(source.get("path", ""))
    return (
        path_text.startswith("http://")
        or path_text.startswith("https://")
        or any(not is_blank(source.get(field)) for field in ["retrieved_at", "read_status", "source_license", "source_url", "url"])
    )

def make_review_queue_item(item, queue_type, reasons, missing_fields):
    item_id = str(item.get("id", ""))
    source = item.get("source", {}) if isinstance(item.get("source", {}), dict) else {}
    content_sha256 = repository_file_sha256(item.get("path", ""))
    return {
        "queue_id": f"item:{item_id}:{queue_type}",
        "queue_type": queue_type,
        "object_type": "registry-item",
        "id": item_id,
        "title": str(item.get("title", "")),
        "kind": str(item.get("kind", "")),
        "domain": str(item.get("domain", "")),
        "path": str(item.get("path", "")),
        "content_hash_required": True,
        "content_hash_status": "bound" if content_sha256 else "unavailable",
        "content_sha256": content_sha256,
        "owner": str(item.get("owner", "")),
        "status": str(item.get("status", "")),
        "review_after": str(item.get("review_after", "")),
        "priority": review_priority_for_item(item),
        "reasons": reasons,
        "missing_fields": missing_fields,
        "source_id": str(source.get("source_id", "")),
        "evidence_refs": as_list(item.get("validation_refs", [])) + as_list(item.get("evidence_refs", [])),
        "generated_by_ai": bool(item.get("generated_by_ai", False)),
        "ai_role": str(item.get("ai_role", "")),
        "ai_model_or_tool": str(item.get("ai_model_or_tool", "")),
        "ai_generated_at": str(item.get("ai_generated_at", "")),
        "human_reviewed_by": str(item.get("human_reviewed_by", "")),
        "human_reviewed_at": str(item.get("human_reviewed_at", "")),
        "review_basis": str(item.get("review_basis", "")),
        "read_status": str(item.get("read_status", "")),
        "source_license": str(item.get("source_license", "")),
        "retrieved_at": str(item.get("retrieved_at", "")),
        "promotion_decision": str(item.get("promotion_decision", "none") or "none"),
        "read_only": True,
        "report_only": True,
        "owner_gate_mutation": False,
        "memory_write": False,
        "source_project_write": False,
        "next_commands": [
            f"rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --explain {item_id}"
        ],
        "must_not": [
            "不生成 owner decision",
            "不关闭 owner gate",
            "不写 memory",
            "不自动提升 active",
        ],
    }

def make_external_source_queue_item(source):
    source_id = str(source.get("id", ""))
    missing_fields = [
        field for field in ["retrieved_at", "read_status", "source_license", "review_status"]
        if is_blank(source.get(field))
    ]
    return {
        "queue_id": f"source:{source_id}:external-source-review",
        "queue_type": "external-source-review",
        "object_type": "registered-source",
        "id": source_id,
        "title": str(source.get("name", source_id)),
        "kind": "registered-source",
        "domain": "",
        "path": str(source.get("path", "")),
        "content_hash_required": False,
        "content_hash_status": "not-applicable",
        "content_sha256": "",
        "owner": str(source.get("owner", "")),
        "status": str(source.get("status", "")),
        "review_after": str(source.get("review_after", "")),
        "priority": "P2" if missing_fields else "P3",
        "reasons": ["external-source-fields-incomplete"] if missing_fields else ["external-source-review-tracked"],
        "missing_fields": missing_fields,
        "source_id": source_id,
        "evidence_refs": [],
        "generated_by_ai": False,
        "read_status": str(source.get("read_status", "")),
        "source_license": str(source.get("source_license", "")),
        "retrieved_at": str(source.get("retrieved_at", "")),
        "promotion_decision": str(source.get("promotion_decision", "none") or "none"),
        "read_only": True,
        "report_only": True,
        "owner_gate_mutation": False,
        "memory_write": False,
        "source_project_write": False,
        "next_commands": [
            "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source --json"
        ],
        "must_not": [
            "不生成 owner decision",
            "不关闭 owner gate",
            "不写 memory",
            "不自动提升 active",
        ],
    }

def build_review_queue_view(items, sources):
    rows = []
    for item in items:
        if item.get("generated_by_ai") is True:
            missing_fields = [
                field for field in ["human_reviewed_by", "human_reviewed_at", "review_basis"]
                if is_blank(item.get(field))
            ]
            current_content_sha256 = repository_file_sha256(item.get("path", ""))
            stored_review_sha256 = str(item.get("human_review_content_sha256", ""))
            review_content_drifted = (
                str(item.get("human_review_decision", "")) in REVIEW_CONTENT_BOUND_DECISIONS
                and bool(stored_review_sha256)
                and stored_review_sha256 != current_content_sha256
            )
            if missing_fields:
                rows.append(
                    make_review_queue_item(
                        item,
                        "ai-human-review",
                        [f"missing-{field.replace('_', '-')}" for field in missing_fields],
                        missing_fields,
                    )
                )
            elif str(item.get("human_review_decision", "")) in {"needs-edits", "defer"}:
                review_decision = str(item.get("human_review_decision", ""))
                rows.append(
                    make_review_queue_item(
                        item,
                        "ai-human-review",
                        [f"human-review-{review_decision}"],
                        ["review_resolution"],
                    )
                )
            elif review_content_drifted:
                rows.append(
                    make_review_queue_item(
                        item,
                        "ai-human-review",
                        ["human-review-content-sha256-drift"],
                        ["review_resolution"],
                    )
                )
        external_item_fields = ["retrieved_at", "read_status", "source_license", "source_url", "url"]
        if str(item.get("kind", "")) == "external-source-note" or any(not is_blank(item.get(field)) for field in external_item_fields):
            missing_fields = [
                field for field in ["retrieved_at", "read_status", "source_license", "review_basis"]
                if is_blank(item.get(field))
            ]
            if missing_fields:
                rows.append(
                    make_review_queue_item(
                        item,
                        "external-source-review",
                        [f"missing-{field.replace('_', '-')}" for field in missing_fields],
                        missing_fields,
                    )
                )
    for source in sources:
        if source_looks_external(source):
            row = make_external_source_queue_item(source)
            if row.get("missing_fields"):
                rows.append(row)
    rows = sorted(
        rows,
        key=lambda row: (
            str(row.get("queue_type", "")),
            str(row.get("priority", "P9")),
            str(row.get("review_after", "") or "9999-12-31"),
            str(row.get("owner", "")),
            str(row.get("id", "")),
        ),
    )
    by_type = collections.defaultdict(list)
    by_owner = collections.defaultdict(list)
    by_review_date = collections.defaultdict(list)
    priority_counts: Counter[str] = collections.Counter()
    for row in rows:
        row_id = str(row.get("queue_id", ""))
        by_type[str(row.get("queue_type", ""))].append(row_id)
        by_owner[str(row.get("owner", "") or "<missing-owner>")].append(row_id)
        by_review_date[str(row.get("review_after", "") or "<missing-review_after>")].append(row_id)
        priority_counts[str(row.get("priority", ""))] += 1
    return {
        "summary": {
            "status": "needs-human-review" if rows else "clear",
            "row_count": len(rows),
            "ai_generated_pending_count": len([row for row in rows if row.get("queue_type") == "ai-human-review"]),
            "external_source_pending_count": len([row for row in rows if row.get("queue_type") == "external-source-review"]),
            "active_or_promotion_blocker_count": len([row for row in rows if row.get("priority") == "P0"]),
            "by_priority": dict(sorted(priority_counts.items())),
            "source": "registry/items.jsonl + registry/sources.json",
            "read_only": True,
            "report_only": True,
            "owner_gate_mutation": False,
            "memory_write": False,
        },
        "rows": rows,
        "by_type": dict(sorted(by_type.items())),
        "by_owner": dict(sorted(by_owner.items())),
        "by_review_date": dict(sorted(by_review_date.items())),
        "must_not": [
            "不生成 owner decision",
            "不关闭 owner gate",
            "不写 memory",
            "不自动提升 active",
        ],
    }

def build_review_queue_command(include_json=False, include_forms_jsonl=False, validate_queue_forms_path="", next_offset=None):
    command_parts = [
        "rtk",
        "bash",
        "~/knowledge-hub/tools/knowledge-index-plan.sh",
        "--section",
        "review-queue",
    ]
    if include_json:
        command_parts.append("--json")
    if include_forms_jsonl:
        command_parts.append("--queue-forms-jsonl")
    if validate_queue_forms_path:
        command_parts.extend(["--validate-queue-forms", validate_queue_forms_path])
    if args.queue_type:
        command_parts.extend(["--queue-type", args.queue_type])
    if args.queue_owner:
        command_parts.extend(["--queue-owner", args.queue_owner])
    if args.queue_review_after:
        command_parts.extend(["--queue-review-after", args.queue_review_after])
    if args.queue_priority:
        command_parts.extend(["--queue-priority", args.queue_priority])
    if args.queue_limit:
        command_parts.extend(["--queue-limit", str(args.queue_limit), "--queue-offset", str(next_offset if next_offset is not None else args.queue_offset)])
    elif args.queue_offset:
        command_parts.extend(["--queue-offset", str(next_offset if next_offset is not None else args.queue_offset)])
    return " ".join(command_parts)

def make_review_queue_form(row):
    form = {
        "form_type": "review-queue-human-review",
        "schema_version": 2,
        "status": "human-fill-required",
        "read_only": True,
        "report_only": True,
        "owner_gate_mutation": False,
        "memory_write": False,
        "source_project_write": False,
        "no_registry_write": True,
        "no_owner_decision_generated": True,
        "no_active_promotion": True,
        "queue_id": str(row.get("queue_id", "")),
        "queue_type": str(row.get("queue_type", "")),
        "object_type": str(row.get("object_type", "")),
        "id": str(row.get("id", "")),
        "title": str(row.get("title", "")),
        "kind": str(row.get("kind", "")),
        "domain": str(row.get("domain", "")),
        "path": str(row.get("path", "")),
        "content_hash_required": bool(row.get("content_hash_required", False)),
        "content_sha256": str(row.get("content_sha256", "")),
        "source_id": str(row.get("source_id", "")),
        "review_after": str(row.get("review_after", "")),
        "priority": str(row.get("priority", "")),
        "reasons": as_list(row.get("reasons", [])),
        "missing_fields": as_list(row.get("missing_fields", [])),
        "required_binding_fields": ["content_sha256"] if row.get("content_hash_required") else [],
        "required_human_fields": ["human_reviewed_by", "human_reviewed_at", "review_basis"],
        "human_reviewed_by": "",
        "human_reviewed_at": "",
        "review_basis": "",
        "review_decision": "",
        "review_decision_candidates": ["accept-as-review-record", "needs-edits", "archive-only", "reject", "defer"],
        "retrieved_at": str(row.get("retrieved_at", "")),
        "read_status": str(row.get("read_status", "")),
        "source_license": str(row.get("source_license", "")),
        "promotion_decision": str(row.get("promotion_decision", "none") or "none"),
        "evidence_refs": as_list(row.get("evidence_refs", [])),
        "next_commands": as_list(row.get("next_commands", [])),
        "read_only_context": {
            "registry_owner": str(row.get("owner", "")),
            "registry_status": str(row.get("status", "")),
            "ai_role": str(row.get("ai_role", "")),
            "ai_model_or_tool": str(row.get("ai_model_or_tool", "")),
            "ai_generated_at": str(row.get("ai_generated_at", "")),
        },
        "must_not": as_list(row.get("must_not", [])) + [
            "不写 registry",
            "不得把本表单当 owner decision",
            "不得由 Codex 自动回填 human_reviewed_by/human_reviewed_at/review_basis",
        ],
        "notes_zh": "这是人工复核填写前的只读 JSONL 骨架；registry item 的 content_sha256 绑定当前整文件，正文漂移后表单必须重新导出。工具不写 registry，不生成结论，不提升 active。",
    }
    return form

