#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import collections
import datetime as dt
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Print a read-only plan for core Knowledge Hub indexes from registry files.")
parser.add_argument("--section", choices=["all", "owner", "review-date", "status", "project", "source", "topic", "decision", "manifest", "linking", "review-queue"], default="all")
parser.add_argument("--json", action="store_true")
parser.add_argument("--queue-type", help="Filter review queue rows by queue_type when --section review-queue is used.")
parser.add_argument("--queue-owner", help="Filter review queue rows by owner when --section review-queue is used.")
parser.add_argument("--queue-review-after", help="Filter review queue rows by review_after when --section review-queue is used.")
parser.add_argument("--queue-priority", help="Filter review queue rows by priority when --section review-queue is used.")
parser.add_argument("--queue-limit", type=int, default=0, help="Limit review queue rows after filters; 0 means no JSON limit.")
parser.add_argument("--queue-offset", type=int, default=0, help="Offset review queue rows after filters.")
parser.add_argument("--queue-forms-jsonl", action="store_true", help="Print read-only human review form skeleton rows for the filtered review queue.")
args = parser.parse_args(argv)
if args.queue_limit < 0:
    parser.error("--queue-limit must be >= 0")
if args.queue_offset < 0:
    parser.error("--queue-offset must be >= 0")
if args.queue_forms_jsonl and args.json:
    parser.error("--queue-forms-jsonl cannot be combined with --json")
if args.queue_forms_jsonl and args.section != "review-queue":
    parser.error("--queue-forms-jsonl requires --section review-queue")

items_path = root / "registry" / "items.jsonl"
sources_path = root / "registry" / "sources.json"
projects_path = root / "registry" / "projects.json"
topics_path = root / "registry" / "topics.json"
decisions_path = root / "registry" / "decisions.jsonl"
migrations_path = root / "registry" / "migrations.jsonl"
items = []
sources = []
projects = []
topics = []
decisions = []
migrations = []
errors = []
warnings = []
SOURCE_COVERAGE_RE = re.compile(r"^knowledge-hub-source-coverage-closeout-(\d{8})\.jsonl$")

def select_source_coverage_closeout(root):
    paths = sorted((root / "artifacts" / "manifests").glob("knowledge-hub-source-coverage-closeout-*.jsonl"))
    dated = []
    ignored = []
    for path in paths:
        relative = str(path.relative_to(root))
        match = SOURCE_COVERAGE_RE.match(path.name)
        if not match:
            ignored.append(relative)
            continue
        date_text = match.group(1)
        try:
            dt.datetime.strptime(date_text, "%Y%m%d").date()
        except Exception:
            ignored.append(relative)
            continue
        dated.append((date_text, relative, path))
    dated.sort(key=lambda row: (row[0], row[1]))
    selection = {
        "pattern": "artifacts/manifests/knowledge-hub-source-coverage-closeout-*.jsonl",
        "required_filename": "knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl",
        "strategy": "filename-yyyymmdd-sort-last",
        "candidate_count": len(paths),
        "candidates": [str(path.relative_to(root)) for path in paths],
        "dated_candidate_count": len(dated),
        "dated_candidates": [row[1] for row in dated],
        "ignored_non_date_candidates": ignored,
        "selected": dated[-1][1] if dated else "",
        "reason_zh": "只按 knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl 的日期字段选择最新 closeout；非日期候选会被忽略并作为 warning 暴露，避免 future/latest 等文件名被静默选中。",
    }
    return selection, dated[-1][2] if dated else None

try:
    for line_no, line in enumerate(items_path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"registry/items.jsonl:{line_no}: {exc}")
            continue
        items.append(item)
except Exception as exc:
    errors.append(f"cannot read registry/items.jsonl: {exc}")

def read_json_array(path, key):
    try:
        data = json.loads(path.read_text())
        value = data.get(key, [])
        if not isinstance(value, list):
            errors.append(f"{path.relative_to(root)} field {key} is not a list")
            return []
        return value
    except Exception as exc:
        errors.append(f"cannot read {path.relative_to(root)}: {exc}")
        return []

def read_jsonl(path, label):
    rows = []
    try:
        for line_no, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append(f"{label}:{line_no}: {exc}")
    except Exception as exc:
        errors.append(f"cannot read {label}: {exc}")
    return rows

sources = read_json_array(sources_path, "sources")
projects = read_json_array(projects_path, "projects")
topics = read_json_array(topics_path, "topics")
decisions = read_jsonl(decisions_path, "registry/decisions.jsonl")
migrations = read_jsonl(migrations_path, "registry/migrations.jsonl")

by_owner = collections.defaultdict(list)
by_review_date = collections.defaultdict(list)
by_status = collections.defaultdict(list)
by_project = {}
by_source = {}
by_topic = {}
by_decision = {
    "registry_decisions": [],
    "owner_worksheets": [],
    "migration_decisions": [],
}
by_manifest = {
    "summary": {},
    "latest": [],
    "unpaired": [],
    "rows": [],
}
by_review_queue = {
    "summary": {},
    "rows": [],
    "by_type": {},
    "by_owner": {},
    "by_review_date": {},
}

for item in items:
    item_id = str(item.get("id", ""))
    if not item_id:
        continue
    by_owner[str(item.get("owner", ""))].append(item_id)
    by_review_date[str(item.get("review_after", ""))].append(item_id)
    by_status[str(item.get("status", ""))].append(item_id)

for project in projects:
    project_id = str(project.get("id", ""))
    if not project_id:
        warnings.append("registry/projects.json contains project without id")
        continue
    domain = f"projects/{project_id}"
    path_prefix = f"domains/projects/{project_id}/"
    project_items = []
    for item in items:
        item_domain = str(item.get("domain", ""))
        item_path = str(item.get("path", ""))
        item_source = item.get("source", {}) if isinstance(item.get("source", {}), dict) else {}
        source_id = str(item_source.get("source_id", ""))
        if item_domain == domain or item_path.startswith(path_prefix) or project_id in source_id:
            project_items.append(str(item.get("id", "")))
    by_project[project_id] = {
        "name": project.get("name", ""),
        "domain": project.get("domain", ""),
        "status": project.get("status", ""),
        "items": [item_id for item_id in project_items if item_id],
    }

source_coverage_selection, latest_coverage = select_source_coverage_closeout(root)
if source_coverage_selection.get("ignored_non_date_candidates"):
    warnings.append(
        "ignored non-date source coverage closeout candidates: "
        + ", ".join(source_coverage_selection.get("ignored_non_date_candidates", []))
    )
coverage_by_source = {}
if latest_coverage:
    duplicate_source_ids = []
    duplicate_source_rows = collections.defaultdict(list)
    for row in read_jsonl(latest_coverage, str(latest_coverage.relative_to(root))):
        source_id = str(row.get("source_id", ""))
        if source_id:
            coverage_row = {
                "status": row.get("status", ""),
                "classification": row.get("classification", ""),
                "decision": row.get("decision", ""),
                "risk": row.get("risk", ""),
                "owner": row.get("owner", ""),
                "checked_at": row.get("checked_at", ""),
            }
            if source_id in coverage_by_source:
                if source_id not in duplicate_source_ids:
                    duplicate_source_ids.append(source_id)
                    duplicate_source_rows[source_id].append(coverage_by_source[source_id])
                duplicate_source_rows[source_id].append(coverage_row)
                continue
            coverage_by_source[source_id] = coverage_row
    source_coverage_selection["duplicate_source_ids"] = sorted(duplicate_source_ids)
    source_coverage_selection["duplicate_policy"] = "first-row-kept-duplicates-warned"
    source_coverage_selection["duplicate_rows"] = {
        source_id: rows for source_id, rows in sorted(duplicate_source_rows.items())
    }
    if duplicate_source_ids:
        warnings.append(
            "duplicate source_id rows in latest source coverage closeout: "
            + ", ".join(sorted(duplicate_source_ids))
            + "; first row kept for recovery view"
        )
else:
    warnings.append("missing dated knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl")

for source in sources:
    source_id = str(source.get("id", ""))
    if not source_id:
        warnings.append("registry/sources.json contains source without id")
        continue
    item_refs = []
    for item in items:
        item_source = item.get("source", {}) if isinstance(item.get("source", {}), dict) else {}
        if str(item_source.get("source_id", "")) == source_id:
            item_refs.append(str(item.get("id", "")))
    migration_refs = [
        row.get("mode", "")
        for row in migrations
        if source_id in str(row.get("from", "")) or source_id in str(row.get("to", "")) or source_id in str(row.get("notes", ""))
    ]
    by_source[source_id] = {
        "role": source.get("role", ""),
        "path": source.get("path", ""),
        "authority": source.get("authority", ""),
        "status": source.get("status", ""),
        "write_policy": source.get("write_policy", ""),
        "migration_strategy": source.get("migration_strategy", ""),
        "owner": source.get("owner", ""),
        "review_after": source.get("review_after", ""),
        "final_disposition": source.get("final_disposition", ""),
        "check": source.get("check", ""),
        "no_check_reason": source.get("no_check_reason", ""),
        "coverage": coverage_by_source.get(source_id, {}),
        "item_refs": item_refs,
        "migration_refs": migration_refs[:10],
    }

for topic in topics:
    topic_id = str(topic.get("id", ""))
    if not topic_id:
        warnings.append("registry/topics.json contains topic without id")
        continue
    allowed_kinds = set(topic.get("allowed_kinds", []))
    domain = str(topic.get("domain", ""))
    topic_items = []
    for item in items:
        tags = item.get("tags", []) if isinstance(item.get("tags", []), list) else []
        item_path = str(item.get("path", ""))
        item_kind = str(item.get("kind", ""))
        if topic_id in tags or (domain and item_path.startswith(domain)) or (item_kind in allowed_kinds and domain in item_path):
            topic_items.append(str(item.get("id", "")))
    by_topic[topic_id] = {
        "domain": domain,
        "allowed_kinds": sorted(allowed_kinds),
        "items": [item_id for item_id in topic_items if item_id],
    }

for decision in decisions:
    by_decision["registry_decisions"].append(
        {
            "decision_id": decision.get("decision_id", ""),
            "status": decision.get("status", ""),
            "owner": decision.get("owner", ""),
            "updated_at": decision.get("updated_at", ""),
            "source": decision.get("source", ""),
        }
    )

worksheet_paths = sorted((root / "artifacts" / "manifests").glob("*owner-decision-worksheets-*.jsonl"))
for worksheet_path in worksheet_paths:
    for row in read_jsonl(worksheet_path, str(worksheet_path.relative_to(root))):
        worksheet_id = str(row.get("id") or row.get("worksheet_id") or "")
        if worksheet_id:
            by_decision["owner_worksheets"].append(
                {
                    "worksheet_id": worksheet_id,
                    "source_id": row.get("source_id", ""),
                    "source_path": row.get("source_path", ""),
                    "status": row.get("worksheet_status") or row.get("status") or row.get("default_state", ""),
                    "owner": row.get("owner_required") or row.get("owner_candidate") or row.get("owner", ""),
                    "review_after": row.get("review_after", ""),
                    "decision_state": "no owner decision generated",
                }
            )

for row in migrations:
    mode = str(row.get("mode", ""))
    if any(token in mode for token in ["migration", "copy-first", "reference", "artifact", "coverage", "boundary"]):
        by_decision["migration_decisions"].append(
            {
                "mode": mode,
                "status": row.get("status", ""),
                "to": row.get("to", ""),
                "checked_at": row.get("checked_at", ""),
            }
        )

manifest_jsonl_paths = sorted((root / "artifacts" / "manifests").glob("*.jsonl"))
manifest_md_paths = sorted((root / "artifacts" / "manifests").glob("*.md"))
manifest_md_by_stem = {path.stem: path for path in manifest_md_paths}
manifest_jsonl_stems = {path.stem for path in manifest_jsonl_paths}
manifest_md_stems = {path.stem for path in manifest_md_paths}
manifest_rows = []
manifest_profile_health_counts = {}

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
    return {
        "queue_id": f"item:{item_id}:{queue_type}",
        "queue_type": queue_type,
        "object_type": "registry-item",
        "id": item_id,
        "title": str(item.get("title", "")),
        "kind": str(item.get("kind", "")),
        "domain": str(item.get("domain", "")),
        "path": str(item.get("path", "")),
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
            if missing_fields:
                rows.append(
                    make_review_queue_item(
                        item,
                        "ai-human-review",
                        [f"missing-{field.replace('_', '-')}" for field in missing_fields],
                        missing_fields,
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
    priority_counts = collections.Counter()
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

def build_review_queue_command(include_json=False, include_forms_jsonl=False, next_offset=None):
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
        "schema_version": 1,
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
        "source_id": str(row.get("source_id", "")),
        "review_after": str(row.get("review_after", "")),
        "priority": str(row.get("priority", "")),
        "reasons": as_list(row.get("reasons", [])),
        "missing_fields": as_list(row.get("missing_fields", [])),
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
        "notes_zh": "这是人工复核填写前的只读 JSONL 骨架；工具只负责按过滤条件列出待复核对象，不写 registry，不生成结论，不提升 active。",
    }
    return form

def apply_review_queue_filters(view):
    rows = list(view.get("rows", []))
    total_row_count = len(rows)
    filters = {
        "queue_type": args.queue_type or "",
        "owner": args.queue_owner or "",
        "review_after": args.queue_review_after or "",
        "priority": args.queue_priority or "",
    }
    for field, expected in filters.items():
        if expected:
            rows = [row for row in rows if str(row.get(field, "")) == expected]
    matched_count = len(rows)
    offset = args.queue_offset
    limit = args.queue_limit
    shown_rows = rows[offset:] if not limit else rows[offset:offset + limit]
    next_offset = offset + len(shown_rows)
    has_next = next_offset < matched_count
    current_batch_command = build_review_queue_command(include_json=True)
    next_page_command = build_review_queue_command(include_json=True, next_offset=next_offset) if has_next else ""
    current_forms_command = build_review_queue_command(include_forms_jsonl=True)

    filtered = dict(view)
    by_type = collections.defaultdict(list)
    by_owner = collections.defaultdict(list)
    by_review_date = collections.defaultdict(list)
    for row in rows:
        row_id = str(row.get("queue_id", ""))
        by_type[str(row.get("queue_type", ""))].append(row_id)
        by_owner[str(row.get("owner", "") or "<missing-owner>")].append(row_id)
        by_review_date[str(row.get("review_after", "") or "<missing-review_after>")].append(row_id)
    filtered_summary = dict(filtered.get("summary", {}))
    filtered_summary.update({
        "total_row_count": total_row_count,
        "matched_count": matched_count,
        "shown_count": len(shown_rows),
        "offset": offset,
        "limit": limit,
        "has_next": has_next,
        "next_offset": next_offset if has_next else None,
        "next_command": next_page_command,
        "review_batch_packet": {
            "packet_type": "review-queue-batch",
            "read_only": True,
            "report_only": True,
            "filter": filters,
            "offset": offset,
            "limit": limit,
            "matched_count": matched_count,
            "shown_count": len(shown_rows),
            "row_ids": [str(row.get("queue_id", "")) for row in shown_rows],
            "required_human_fields": ["human_reviewed_by", "human_reviewed_at", "review_basis"],
            "next_commands": [
                command
                for row in shown_rows
                for command in row.get("next_commands", [])
            ],
            "recommended_batch_json": current_batch_command,
            "recommended_forms_jsonl": current_forms_command,
            "forms_jsonl_command": current_forms_command,
            "next_page_command": next_page_command,
            "must_not": [
                "不生成 owner decision",
                "不关闭 owner gate",
                "不写 memory",
                "不自动提升 active",
                "不把 review queue 当 owner gate 签收结果",
            ],
            "notes_zh": "只读人工复核批次包；用于按当前过滤和分页领取一批 AI/外部资料待复核条目。它只给诊断命令和必填人工字段，不写 registry，不回填 human_reviewed_by，不提升 active。",
        },
    })
    filtered["summary"] = filtered_summary
    filtered["filter"] = filters
    filtered["by_type"] = dict(sorted(by_type.items()))
    filtered["by_owner"] = dict(sorted(by_owner.items()))
    filtered["by_review_date"] = dict(sorted(by_review_date.items()))
    filtered["pagination"] = {
        "offset": offset,
        "limit": limit,
        "matched_count": matched_count,
        "shown_count": len(shown_rows),
        "has_next": has_next,
        "next_offset": next_offset if has_next else None,
        "next_command": next_page_command,
        "forms_jsonl_command": current_forms_command,
        "notes_zh": "只过滤 registry 派生视图；不生成人工复核结论，不回填 human_reviewed_by，不改变 registry。",
    }
    filtered["review_batch_packet"] = filtered_summary["review_batch_packet"]
    filtered["rows"] = shown_rows
    return filtered

def manifest_profile_health(manifest_path, first, date_value, summary_source, evidence_source, evidence_count):
    path_name = manifest_path.name
    in_current_profile = path_name.startswith("knowledge-hub-") and date_value >= "2026-06-21"
    if not in_current_profile:
        mode = str(first.get("mode", "") or "")
        classification = str(first.get("classification", "") or "")
        review_status = str(first.get("review_status", "") or "")
        if "reference" in mode or "reference" in classification or "reference" in review_status:
            return "reference-only"
        return "legacy-missing-profile"
    if summary_source == "missing":
        return "missing-summary"
    if evidence_source == "missing" or evidence_count == 0:
        return "missing-evidence"
    if not isinstance(first.get("boundaries"), dict):
        return "advisory-missing-boundary"
    return "pass"

def classify_unpaired_manifest(stem, has_jsonl, has_md):
    reasons = []
    status = "needs_review"
    if "dry-run" in stem:
        status = "expected"
        reasons.append("dry-run 制品允许只保留执行明细或 Markdown 摘要之一")
    if "artifact-ref" in stem:
        status = "expected"
        reasons.append("artifact-ref 制品常以 JSONL 作为机器可读引用清单")
    if "source-inventory" in stem:
        status = "expected"
        reasons.append("source inventory 是历史盘点入口，允许 Markdown-only")
    if "classification" in stem:
        status = "expected"
        reasons.append("classification 是历史分类报告，允许 Markdown-only")
    if "copy-first-applied" in stem:
        status = "expected"
        reasons.append("早期 copy-first applied 记录允许 Markdown-only；后续新增治理 manifest 优先成对")
    if not reasons:
        reasons.append("未命中已知历史例外，建议人工确认是否缺少 Markdown 或 JSONL 配对文件")
    return {
        "stem": stem,
        "jsonl_path": str((root / "artifacts" / "manifests" / f"{stem}.jsonl").relative_to(root)) if has_jsonl else "",
        "markdown_path": str((root / "artifacts" / "manifests" / f"{stem}.md").relative_to(root)) if has_md else "",
        "pairing_status": "jsonl-only" if has_jsonl and not has_md else "markdown-only" if has_md and not has_jsonl else "unknown",
        "review_status": status,
        "reasons_zh": reasons,
        "notes_zh": "只读恢复分类；expected 不代表推荐新增同类单边文件，needs_review 不自动作为硬失败。",
    }

for manifest_path in manifest_jsonl_paths:
    rows = read_jsonl(manifest_path, str(manifest_path.relative_to(root)))
    first = rows[0] if rows else {}
    stem = manifest_path.stem
    md_path = manifest_md_by_stem.get(stem)
    filename_date_match = re.search(r"(20\d{2})(\d{2})(\d{2})", manifest_path.name)
    filename_date = ""
    if filename_date_match:
        filename_date = "-".join(filename_date_match.groups())
    row_date_value = first.get("checked_at") or first.get("created_at") or first.get("updated_at") or first.get("review_after") or ""
    date_value = filename_date
    summary_source, summary_value = first_present_field(first, ["summary_zh", "notes_zh", "notes"])
    evidence_source, evidence_value = first_present_field(
        first,
        ["evidence", "evidence_refs", "validation_refs", "verification_commands", "source_refs"],
    )
    if not isinstance(evidence_value, list):
        evidence_count = 1 if evidence_value else 0
    else:
        evidence_count = len(evidence_value)
    profile_health = manifest_profile_health(
        manifest_path,
        first,
        date_value,
        summary_source,
        evidence_source,
        evidence_count,
    )
    manifest_profile_health_counts[profile_health] = manifest_profile_health_counts.get(profile_health, 0) + 1
    manifest_rows.append(
        {
            "id": first.get("id", stem),
            "path": str(manifest_path.relative_to(root)),
            "markdown_path": str(md_path.relative_to(root)) if md_path else "",
            "paired": bool(md_path),
            "row_count": len(rows),
            "status": first.get("status", ""),
            "date": date_value,
            "date_source": "filename-YYYYMMDD" if filename_date else "missing-filename-date",
            "row_date": row_date_value,
            "source_id": first.get("source_id", ""),
            "owner": first.get("owner", ""),
            "classification": first.get("classification", ""),
            "mode": first.get("mode", ""),
            "decision": first.get("decision", ""),
            "summary_zh": summary_value,
            "derived_summary_zh": summary_value,
            "summary_source": summary_source,
            "evidence_count": evidence_count,
            "derived_evidence_count": evidence_count,
            "evidence_source": evidence_source,
            "profile_health": profile_health,
        }
    )
unpaired_stems = sorted(manifest_jsonl_stems ^ manifest_md_stems)
unpaired_classified = [
    classify_unpaired_manifest(stem, stem in manifest_jsonl_stems, stem in manifest_md_stems)
    for stem in unpaired_stems
]
unpaired_expected = [row for row in unpaired_classified if row["review_status"] == "expected"]
unpaired_needs_review = [row for row in unpaired_classified if row["review_status"] != "expected"]
by_manifest = {
    "summary": {
        "jsonl_count": len(manifest_jsonl_paths),
        "markdown_count": len(manifest_md_paths),
        "paired_count": len(manifest_jsonl_stems & manifest_md_stems),
        "unpaired_count": len(unpaired_stems),
        "unpaired_expected_count": len(unpaired_expected),
        "unpaired_needs_review_count": len(unpaired_needs_review),
        "latest_strategy": "filename-date-only",
        "latest_strategy_zh": "latest 只按 manifest 文件名中的 YYYYMMDD 排序；JSONL row 内 checked_at/created_at/updated_at/review_after 仅作为 row_date 辅助字段，不参与 latest 排序。",
        "profile_health": dict(sorted(manifest_profile_health_counts.items())),
        "profile_health_zh": "只读恢复视图：pass 表示当前治理 manifest 满足中文摘要、证据和边界字段；legacy/reference 类旧制品不作为硬失败；advisory-* 仅提示人工补强方向，missing-summary/missing-evidence 才说明当前 profile 基础字段缺失。",
        "profile_health_next_actions_zh": {
            "advisory-missing-boundary": "不回填历史正文、不升为硬失败；如需人工复核，优先打开 paired Markdown、查看 evidence_refs/validation_refs，并只对后续新增治理 manifest 在新增时补 boundaries。",
            "legacy-missing-profile": "历史制品保留 legacy 口径；只有迁移、重写或重新发布时才按当前 profile 补齐中文摘要、证据和边界字段。",
            "reference-only": "引用类制品只维护引用和边界，不复制 source 正文。",
            "missing-summary": "当前 profile 基础字段缺失；新增或近期治理 manifest 需要补中文摘要。",
            "missing-evidence": "当前 profile 基础字段缺失；新增或近期治理 manifest 需要补 validation_refs/evidence_refs。",
            "pass": "当前 profile 基础字段齐备，按 review_after 周期复核即可。",
        },
    },
    "latest": sorted(manifest_rows, key=lambda row: (str(row.get("date", "")), str(row.get("path", ""))), reverse=True)[:20],
    "unpaired": unpaired_classified,
    "unpaired_expected": unpaired_expected,
    "unpaired_needs_review": unpaired_needs_review,
    "rows": manifest_rows,
}
by_review_queue = apply_review_queue_filters(build_review_queue_view(items, sources))

if args.queue_forms_jsonl:
    for row in by_review_queue.get("rows", []):
        print(json.dumps(make_review_queue_form(row), ensure_ascii=False, sort_keys=True))
    sys.exit(1 if errors else 0)

def read_relative_text(relative_path):
    path = root / relative_path
    try:
        return path.read_text()
    except Exception as exc:
        warnings.append(f"cannot read {relative_path}: {exc}")
        return ""

def build_linking_audit():
    required_level2_sources = {
        "pcr02-project-tools",
        "pcr02-project-knowledge",
        "pcr02-product-test",
        "pcr02-project-scratch",
        "pcr02-project-root-artifacts",
        "pcr02-module-agent-rules",
        "pcr02-project-agent-config",
    }
    required_topics = {"project-current", "project-archive"}
    required_index_anchors = {
        "by_project": {
            "path": "indexes/by-project.md",
            "anchors": ["domains/projects/pcr02", "indexes/by-decision.md", "pcr02-owner-review-package-20260618.md"],
        },
        "by_source": {
            "path": "indexes/by-source.md",
            "anchors": ["pcr02-project-docs", "pcr02-project-tools", "pcr02-level2-source-check-execution-snapshot-20260621.md"],
        },
        "by_topic": {
            "path": "indexes/by-topic.md",
            "anchors": [
                "## 优先恢复主题速查",
                "## 历史治理台账",
                "PCR02",
                "Knowledge Hub final gate",
                "knowledge-hub-proof-search-runtime-hardening-20260622.md",
                "memory auto-curation",
                "Codex archive",
            ],
        },
        "by_decision": {
            "path": "indexes/by-decision.md",
            "anchors": ["pcr02-owner-decision-worksheet-001", "pcr02-owner-decision-worksheet-007", "该包不生成 owner decision"],
        },
    }

    missing_cross_session = []
    pcr02_project = by_project.get("pcr02", {})
    source_ids = set(by_source.keys())
    topic_ids = set(by_topic.keys())
    owner_worksheets = by_decision.get("owner_worksheets", [])
    registry_decisions = by_decision.get("registry_decisions", [])
    migration_decisions = by_decision.get("migration_decisions", [])

    cross_session_checks = {
        "project_recoverable": bool(pcr02_project) and pcr02_project.get("domain") == "domains/projects/pcr02",
        "source_recoverable": "pcr02-project-docs" in source_ids and required_level2_sources.issubset(source_ids),
        "topic_recoverable": required_topics.issubset(topic_ids),
        "decision_recoverable": len(owner_worksheets) >= 7 and bool(registry_decisions) and bool(migration_decisions),
        "handoff_recoverable": any("pcr02-governance-handoff" in item_id for item_id in pcr02_project.get("items", [])),
    }
    for check_id, passed in cross_session_checks.items():
        if not passed:
            missing_cross_session.append(check_id)

    missing_cross_project = []
    pcr02_sources = {source_id: by_source.get(source_id, {}) for source_id in {"pcr02-project-docs"} | required_level2_sources}
    pcr02_sources_with_provenance = []
    for source_id, source in pcr02_sources.items():
        has_check_or_reason = bool(str(source.get("check", "")).strip() or str(source.get("no_check_reason", "")).strip())
        has_provenance = all(str(source.get(field, "")).strip() for field in ["path", "owner", "review_after", "migration_strategy", "final_disposition"]) and has_check_or_reason
        if has_provenance:
            pcr02_sources_with_provenance.append(source_id)
        else:
            missing_cross_project.append(f"source-provenance:{source_id}")
    project_specific_not_team_promoted = not any(
        str(item.get("path", "")).startswith("domains/embedded/standards/")
        and str((item.get("source") or {}).get("source_id", "")) == "pcr02-project-docs"
        for item in items
        if isinstance(item.get("source", {}), dict)
    )
    if not project_specific_not_team_promoted:
        missing_cross_project.append("project-specific-promoted-to-team-standards")

    markdown_missing = []
    markdown_index_recovery = {}
    for index_id, spec in required_index_anchors.items():
        text = read_relative_text(spec["path"])
        missing_anchors = [anchor for anchor in spec["anchors"] if anchor not in text]
        markdown_index_recovery[index_id] = {
            "status": "pass" if not missing_anchors else "fail",
            "path": spec["path"],
            "required_anchors": spec["anchors"],
            "missing_anchors": missing_anchors,
        }
        for anchor in missing_anchors:
            markdown_missing.append({"index": index_id, "path": spec["path"], "anchor": anchor})

    cross_session_status = "pass" if not missing_cross_session else "fail"
    cross_project_status = "pass" if not missing_cross_project else "fail"
    markdown_status = "pass" if not markdown_missing else "fail"
    status = "pass" if cross_session_status == "pass" and cross_project_status == "pass" and markdown_status == "pass" else "fail"
    return {
        "contract_version": 1,
        "status": status,
        "read_only": True,
        "source_body_read": False,
        "owner_gate_mutation": False,
        "commands": {
            "index_plan": "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json",
            "status": "runtime:knowledge-status --strict payload",
            "search_contract": "runtime:knowledge-regression search result ids",
        },
        "cross_session": {
            "status": cross_session_status,
            **cross_session_checks,
            "missing": missing_cross_session,
        },
        "cross_project": {
            "status": cross_project_status,
            "pcr02_project_present": bool(pcr02_project),
            "registered_source_count": len(by_source),
            "pcr02_level2_source_ids_present": required_level2_sources.issubset(source_ids),
            "required_topic_ids_present": required_topics.issubset(topic_ids),
            "decision_refs_present": len(owner_worksheets) >= 7 and bool(registry_decisions) and bool(migration_decisions),
            "provenance_fields_present": len(pcr02_sources_with_provenance) == len(pcr02_sources),
            "project_specific_not_team_promoted": project_specific_not_team_promoted,
            "missing": missing_cross_project,
        },
        "markdown_index_recovery": {
            "status": markdown_status,
            "indexes": markdown_index_recovery,
            "missing_anchors": markdown_missing,
        },
        "evidence_refs": [
            "runtime:status.sources.source_recovery_rows",
            "runtime:index_plan.indexes.by_project",
            "runtime:index_plan.indexes.by_source",
            "runtime:index_plan.indexes.by_topic",
            "runtime:index_plan.indexes.by_decision",
            "runtime:checks.knowledge_regression",
        ],
        "limitations_zh": "只证明 registry/index/search 恢复链路；不证明 owner decision 已签收，不读取 PCR02 源项目正文。",
    }

linking_audit = build_linking_audit()

status_order = ["active", "reviewing", "archived"]

result = {
    "status": "planned" if not errors else "blocked",
    "root": str(root),
    "item_count": len(items),
    "source_count": len(sources),
    "project_count": len(projects),
    "topic_count": len(topics),
    "section": args.section,
    "read_only": True,
    "errors": errors,
    "warnings": warnings,
    "source_coverage_selection": source_coverage_selection,
    "indexes": {
        "by_owner": dict(sorted(by_owner.items())),
        "by_review_date": dict(sorted(by_review_date.items())),
        "by_status": {status: by_status.get(status, []) for status in status_order if status in by_status},
        "by_project": by_project,
        "by_source": by_source,
        "by_topic": by_topic,
        "by_decision": by_decision,
        "by_manifest": by_manifest,
        "by_review_queue": by_review_queue,
        "linking_audit": linking_audit,
    },
    "linking_audit": linking_audit,
}

if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1 if errors else 0)

print("# Knowledge Index Plan")
print()
print("本命令只读生成核心索引视图，不创建、不修改、不提交任何文件。")
print()
print(f"- items: {len(items)}")
print(f"- sources: {len(sources)}")
print(f"- projects: {len(projects)}")
print(f"- topics: {len(topics)}")
print(f"- section: {args.section}")
print(f"- status: {result['status']}")
for error in errors:
    print(f"- ERROR: {error}")
for warning in warnings:
    print(f"- WARNING: {warning}")

def print_owner():
    print()
    print("## By Owner")
    for owner, ids in sorted(by_owner.items()):
        owner_label = owner or "<missing-owner>"
        print()
        print(f"### {owner_label}")
        for item_id in ids:
            print(f"- `{item_id}`")

def print_review_date():
    print()
    print("## By Review Date")
    for review_after, ids in sorted(by_review_date.items()):
        date_label = review_after or "<missing-review_after>"
        for item_id in ids:
            print(f"- {date_label}: `{item_id}`")

def print_status():
    print()
    print("## By Status")
    for status in status_order:
        ids = by_status.get(status, [])
        if ids:
            for item_id in ids:
                print(f"- {status}: `{item_id}`")
    extra_statuses = sorted(status for status in by_status if status not in status_order)
    if extra_statuses:
        print()
        print("### Non-canonical Status Values")
        for status in extra_statuses:
            for item_id in by_status[status]:
                print(f"- {status or '<missing-status>'}: `{item_id}`")

def print_project():
    print()
    print("## By Project")
    for project_id, info in sorted(by_project.items()):
        print()
        print(f"### {project_id}")
        print(f"- domain: `{info.get('domain', '')}`")
        print(f"- status: `{info.get('status', '')}`")
        for item_id in info.get("items", []):
            print(f"- item: `{item_id}`")

def print_source():
    print()
    print("## By Source")
    for source_id, info in sorted(by_source.items()):
        print()
        print(f"### {source_id}")
        print(f"- role: `{info.get('role', '')}`")
        print(f"- authority: `{info.get('authority', '')}`")
        print(f"- status: `{info.get('status', '')}`")
        print(f"- owner: `{info.get('owner', '')}`")
        print(f"- review_after: `{info.get('review_after', '')}`")
        print(f"- write_policy: `{info.get('write_policy', '')}`")
        print(f"- migration_strategy: `{info.get('migration_strategy', '')}`")
        print(f"- final_disposition: `{info.get('final_disposition', '')}`")
        print(f"- check: `{info.get('check', '') or '<no-check-in-source-registry>'}`")
        if info.get("no_check_reason"):
            print(f"- no_check_reason: {info.get('no_check_reason')}")
        coverage = info.get("coverage", {})
        if coverage:
            print(f"- coverage: `{coverage.get('status', '')}` / `{coverage.get('classification', '')}` / checked_at `{coverage.get('checked_at', '')}`")
            print(f"- coverage decision: {coverage.get('decision', '')}")
            print(f"- coverage risk: {coverage.get('risk', '')}")
        else:
            print("- coverage: `<missing-latest-coverage-row>`")
        for item_id in info.get("item_refs", []):
            print(f"- item: `{item_id}`")
        for mode in info.get("migration_refs", []):
            print(f"- migration mode: `{mode}`")

def print_topic():
    print()
    print("## By Topic")
    for topic_id, info in sorted(by_topic.items()):
        print()
        print(f"### {topic_id}")
        print(f"- domain: `{info.get('domain', '')}`")
        print(f"- allowed_kinds: {', '.join(f'`{kind}`' for kind in info.get('allowed_kinds', []))}")
        for item_id in info.get("items", []):
            print(f"- item: `{item_id}`")

def print_decision():
    print()
    print("## By Decision")
    print()
    print("### Registry Decisions")
    for row in by_decision.get("registry_decisions", []):
        print(f"- `{row.get('decision_id', '')}`: {row.get('status', '')}; owner `{row.get('owner', '')}`; source `{row.get('source', '')}`")
    print()
    print("### Owner Worksheets")
    for row in by_decision.get("owner_worksheets", []):
        print(
            f"- `{row.get('worksheet_id', '')}`: {row.get('source_id', '')}/{row.get('source_path', '')}; "
            f"status `{row.get('status', '')}`; owner `{row.get('owner', '')}`; "
            f"review_after `{row.get('review_after', '')}`; {row.get('decision_state', '')}"
        )
    print()
    print("### Migration Decisions")
    for row in by_decision.get("migration_decisions", [])[:80]:
        print(f"- `{row.get('mode', '')}`: {row.get('status', '')}; checked_at `{row.get('checked_at', '')}`")

def print_manifest():
    print()
    print("## By Manifest")
    summary = by_manifest.get("summary", {})
    print(f"- jsonl_count: {summary.get('jsonl_count', 0)}")
    print(f"- markdown_count: {summary.get('markdown_count', 0)}")
    print(f"- paired_count: {summary.get('paired_count', 0)}")
    print(f"- unpaired_count: {summary.get('unpaired_count', 0)}")
    print(f"- unpaired_expected_count: {summary.get('unpaired_expected_count', 0)}")
    print(f"- unpaired_needs_review_count: {summary.get('unpaired_needs_review_count', 0)}")
    profile_health = summary.get("profile_health", {})
    if profile_health:
        print("- profile_health:")
        for status, count in sorted(profile_health.items()):
            print(f"  - {status}: {count}")
        if summary.get("profile_health_zh"):
            print(f"- profile_health_zh: {summary.get('profile_health_zh')}")
    unpaired = by_manifest.get("unpaired", [])
    if unpaired:
        print()
        print("### Unpaired")
        for row in unpaired:
            reasons = "; ".join(row.get("reasons_zh", []))
            print(
                f"- `{row.get('stem', '')}` review_status=`{row.get('review_status', '')}` "
                f"pairing=`{row.get('pairing_status', '')}` jsonl=`{row.get('jsonl_path', '')}` "
                f"markdown=`{row.get('markdown_path', '')}` reason={reasons}"
            )
    print()
    print("### Latest")
    for row in by_manifest.get("latest", []):
        print(
            f"- `{row.get('path', '')}` status=`{row.get('status', '')}` "
            f"date=`{row.get('date', '')}` rows={row.get('row_count', 0)} "
            f"paired={row.get('paired', False)} evidence={row.get('evidence_count', 0)} "
            f"profile_health=`{row.get('profile_health', '')}` "
            f"summary_source=`{row.get('summary_source', '')}` evidence_source=`{row.get('evidence_source', '')}`"
            )

def print_review_queue():
    print()
    print("## By Review Queue")
    summary = by_review_queue.get("summary", {})
    print(f"- status: `{summary.get('status', '')}`")
    print(f"- row_count: {summary.get('row_count', 0)}")
    print(f"- ai_generated_pending_count: {summary.get('ai_generated_pending_count', 0)}")
    print(f"- external_source_pending_count: {summary.get('external_source_pending_count', 0)}")
    print(f"- active_or_promotion_blocker_count: {summary.get('active_or_promotion_blocker_count', 0)}")
    print(f"- matched_count: {summary.get('matched_count', summary.get('row_count', 0))}")
    print(f"- shown_count: {summary.get('shown_count', len(by_review_queue.get('rows', [])))}")
    if summary.get("has_next"):
        print(f"- next_command: `{summary.get('next_command', '')}`")
    print(f"- source: `{summary.get('source', '')}`")
    print("- must_not:")
    for rule in by_review_queue.get("must_not", []):
        print(f"  - {rule}")
    print()
    print("### Queue Types")
    for queue_type, queue_ids in by_review_queue.get("by_type", {}).items():
        print(f"- `{queue_type}`: {len(queue_ids)}")
    print()
    print("### Review Dates")
    for review_after, queue_ids in by_review_queue.get("by_review_date", {}).items():
        print(f"- `{review_after}`: {len(queue_ids)}")
    print()
    print("### Rows")
    for row in by_review_queue.get("rows", [])[:80]:
        missing = ", ".join(row.get("missing_fields", []))
        print(
            f"- `{row.get('queue_id', '')}` priority=`{row.get('priority', '')}` "
            f"owner=`{row.get('owner', '')}` review_after=`{row.get('review_after', '')}` "
            f"status=`{row.get('status', '')}` kind=`{row.get('kind', '')}` "
            f"domain=`{row.get('domain', '')}` path=`{row.get('path', '')}` missing=`{missing}`"
        )
        if row.get("next_commands"):
            print(f"  - next: `{row.get('next_commands', [''])[0]}`")

def print_linking():
    print()
    print("## Linking Audit")
    print(f"- status: `{linking_audit.get('status', '')}`")
    print(f"- read_only: `{linking_audit.get('read_only', False)}`")
    print(f"- source_body_read: `{linking_audit.get('source_body_read', True)}`")
    print(f"- owner_gate_mutation: `{linking_audit.get('owner_gate_mutation', True)}`")
    cross_session = linking_audit.get("cross_session", {})
    cross_project = linking_audit.get("cross_project", {})
    markdown = linking_audit.get("markdown_index_recovery", {})
    print(f"- cross_session: `{cross_session.get('status', '')}` missing={cross_session.get('missing', [])}")
    print(f"- cross_project: `{cross_project.get('status', '')}` missing={cross_project.get('missing', [])}")
    print(f"- markdown_index_recovery: `{markdown.get('status', '')}`")
    missing_anchors = markdown.get("missing_anchors", [])
    if missing_anchors:
        print("- missing_anchors:")
        for row in missing_anchors:
            print(f"  - `{row.get('path', '')}` missing `{row.get('anchor', '')}`")

if args.section in {"all", "owner"}:
    print_owner()
if args.section in {"all", "review-date"}:
    print_review_date()
if args.section in {"all", "status"}:
    print_status()
if args.section in {"all", "project"}:
    print_project()
if args.section in {"all", "source"}:
    print_source()
if args.section in {"all", "topic"}:
    print_topic()
if args.section in {"all", "decision"}:
    print_decision()
if args.section in {"all", "manifest"}:
    print_manifest()
if args.section in {"all", "review-queue"}:
    print_review_queue()
if args.section in {"all", "linking"}:
    print_linking()

print()
print("## 验证")
print()
print("```bash")
print("rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics")
print("```")

sys.exit(1 if errors else 0)
PY
