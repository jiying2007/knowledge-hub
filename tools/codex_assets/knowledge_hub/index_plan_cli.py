import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import re
import sys
from typing import Any, Dict, List

if not __package__:
    repository_root = pathlib.Path(__file__).resolve().parents[3]
    if str(repository_root) not in sys.path:
        sys.path.insert(0, str(repository_root))

from tools.codex_assets.knowledge_hub.index_plan_linking import build_linking_audit
from tools.codex_assets.knowledge_hub.index_plan_manifest import classify_unpaired_manifest, manifest_profile_health
from tools.codex_assets.knowledge_hub.index_plan_review_forms import apply_review_queue_filters, configure_review_forms, validate_review_queue_forms
from tools.codex_assets.knowledge_hub.index_plan_review_queue import (
    build_review_queue_view,
    configure_review_queue,
    first_present_field,
    make_review_queue_form,
)
from tools.codex_assets.knowledge_hub.index_plan_support import (
    display_path,
    emit_json,
    is_local_manifest_draft,
    read_json_array,
    read_jsonl,
    repository_file_sha256,
    select_source_coverage_closeout,
)
INDEX_PLAN_FULL_JSON_MAX_BYTES = 2 * 1024 * 1024
INDEX_PLAN_SUMMARY_JSON_MAX_BYTES = 64 * 1024

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Print a read-only plan for core Knowledge Hub indexes from registry files.")
parser.add_argument("--section", choices=["all", "owner", "review-date", "status", "project", "source", "topic", "decision", "manifest", "linking", "review-queue"], default="all")
parser.add_argument("--json", action="store_true")
parser.add_argument("--summary-json", action="store_true", help="Print a compact count/health projection without index rows.")
parser.add_argument("--as-of", default=os.environ.get("KNOWLEDGE_TODAY", ""), help="Review SLA date in YYYY-MM-DD.")
parser.add_argument("--queue-type", help="Filter review queue rows by queue_type when --section review-queue is used.")
parser.add_argument("--queue-owner", help="Filter review queue rows by owner when --section review-queue is used.")
parser.add_argument("--queue-review-after", help="Filter review queue rows by review_after when --section review-queue is used.")
parser.add_argument("--queue-priority", help="Filter review queue rows by priority when --section review-queue is used.")
parser.add_argument("--queue-limit", type=int, default=50, help="Limit review queue rows after filters (default: 50); explicit 0 disables pagination.")
parser.add_argument("--queue-offset", type=int, default=0, help="Offset review queue rows after filters.")
parser.add_argument("--queue-forms-jsonl", action="store_true", help="Print read-only human review form skeleton rows for the filtered review queue.")
parser.add_argument("--validate-queue-forms", metavar="JSONL", help="Validate filled review queue JSONL forms in report-only mode.")
args = parser.parse_args(argv)
try:
    review_sla_date = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()
except ValueError:
    parser.error("--as-of must use YYYY-MM-DD")
if args.queue_limit < 0:
    parser.error("--queue-limit must be >= 0")
if args.queue_offset < 0:
    parser.error("--queue-offset must be >= 0")
if args.json and args.summary_json:
    parser.error("--json and --summary-json are mutually exclusive")
if args.queue_forms_jsonl and args.json:
    parser.error("--queue-forms-jsonl cannot be combined with --json")
if args.queue_forms_jsonl and args.summary_json:
    parser.error("--queue-forms-jsonl cannot be combined with --summary-json")
if args.queue_forms_jsonl and args.section != "review-queue":
    parser.error("--queue-forms-jsonl requires --section review-queue")
if args.validate_queue_forms and args.queue_forms_jsonl:
    parser.error("--validate-queue-forms cannot be combined with --queue-forms-jsonl")
if args.validate_queue_forms and args.section != "review-queue":
    parser.error("--validate-queue-forms requires --section review-queue")
if args.validate_queue_forms and not args.json:
    parser.error("--validate-queue-forms requires --json")

configure_review_queue(
    root,
    args,
    lambda relative_path: repository_file_sha256(root, relative_path),
)
configure_review_forms(root, args, review_sla_date)



items_path = root / "registry" / "items.jsonl"
sources_path = root / "registry" / "sources.json"
projects_path = root / "registry" / "projects.json"
topics_path = root / "registry" / "topics.json"
decisions_path = root / "registry" / "decisions.jsonl"
items = []
sources = []
projects = []
topics = []
decisions = []
errors = []
warnings = []






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



sources = read_json_array(root, errors, sources_path, "sources") + read_jsonl(root, errors, root / "registry" / "retired-sources.jsonl", "registry/retired-sources.jsonl")
projects = read_json_array(root, errors, projects_path, "projects")
topics = read_json_array(root, errors, topics_path, "topics")
decisions = read_jsonl(root, errors, decisions_path, "registry/decisions.jsonl")

by_owner = collections.defaultdict(list)
by_review_date = collections.defaultdict(list)
by_status = collections.defaultdict(list)
by_project: Dict[str, Dict[str, Any]] = {}
by_source: Dict[str, Dict[str, Any]] = {}
by_topic: Dict[str, Dict[str, Any]] = {}
by_decision: Dict[str, List[Dict[str, Any]]] = {
    "registry_decisions": [],
    "owner_worksheets": [],
}
by_manifest: Dict[str, Any] = {
    "summary": {},
    "latest": [],
    "unpaired": [],
    "rows": [],
}
by_review_queue: Dict[str, Any] = {
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
    path_prefix = f"projects/{project_id}/"
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
coverage_by_source: Dict[str, Dict[str, Any]] = {}
if latest_coverage:
    duplicate_source_ids = []
    duplicate_source_rows = collections.defaultdict(list)
    for row in read_jsonl(root, errors, latest_coverage, str(latest_coverage.relative_to(root))):
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
    by_source[source_id] = {
        "role": source.get("role", ""),
        "path": source.get("path", ""),
        "authority": source.get("authority", ""),
        "status": source.get("status", ""),
        "write_policy": source.get("write_policy", ""),
        "source_strategy": source.get("source_strategy", ""),
        "owner": source.get("owner", ""),
        "review_after": source.get("review_after", ""),
        "final_disposition": source.get("final_disposition", ""),
        "check": source.get("check", ""),
        "no_check_reason": source.get("no_check_reason", ""),
        "coverage": coverage_by_source.get(source_id, {}),
        "item_refs": item_refs,
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
    for row in read_jsonl(root, errors, worksheet_path, str(worksheet_path.relative_to(root))):
        worksheet_id = str(row.get("id") or row.get("worksheet_id") or "")
        if worksheet_id:
            owner_decision = str(row.get("owner_decision", "")).strip()
            by_decision["owner_worksheets"].append(
                {
                    "worksheet_id": worksheet_id,
                    "source_id": row.get("source_id", ""),
                    "source_path": row.get("source_path", ""),
                    "status": row.get("worksheet_status") or row.get("status") or row.get("default_state", ""),
                    "owner": row.get("owner_required") or row.get("owner_candidate") or row.get("owner", ""),
                    "review_after": row.get("review_after", ""),
                    "decision_state": f"owner_decision:{owner_decision}" if owner_decision else "no owner decision generated",
                }
            )

manifest_jsonl_paths = [
    path
    for path in sorted((root / "artifacts" / "manifests").glob("*.jsonl"))
    if not is_local_manifest_draft(path)
]
manifest_md_paths = sorted((root / "artifacts" / "manifests").glob("*.md"))
manifest_md_by_stem = {path.stem: path for path in manifest_md_paths}
manifest_jsonl_stems = {path.stem for path in manifest_jsonl_paths}
manifest_md_stems = {path.stem for path in manifest_md_paths}
manifest_rows = []
manifest_profile_health_counts: Dict[str, int] = {}


















for manifest_path in manifest_jsonl_paths:
    rows = read_jsonl(root, errors, manifest_path, str(manifest_path.relative_to(root)))
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
    classify_unpaired_manifest(root, stem, stem in manifest_jsonl_stems, stem in manifest_md_stems)
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
        "profile_health_zh": "只读恢复视图：pass 表示当前治理 manifest 满足中文摘要、证据和边界字段；历史证据与 reference-only 制品不按当前发布契约判定；advisory-* 仅提示人工补强方向，missing-summary/missing-evidence 才说明当前 profile 基础字段缺失。",
        "profile_health_next_actions_zh": {
            "advisory-missing-boundary": "不回填历史正文、不升为硬失败；如需人工复核，优先打开 paired Markdown、查看 evidence_refs/validation_refs，并只对后续新增治理 manifest 在新增时补 boundaries。",
            "historical-evidence-exempt": "历史制品维持原始证据形态；需要重新发布时创建满足当前 profile 的新制品，不回填或改写历史证据。",
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
all_review_queue_view = build_review_queue_view(items, sources)
by_review_queue = apply_review_queue_filters(all_review_queue_view)

if args.queue_forms_jsonl:
    form_output = "\n".join(
        json.dumps(make_review_queue_form(row), ensure_ascii=False, sort_keys=True)
        for row in by_review_queue.get("rows", [])
    )
    if len(form_output.encode("utf-8")) > INDEX_PLAN_FULL_JSON_MAX_BYTES:
        emit_json(
            {
                "status": "fail",
                "error": "output-budget-exceeded",
                "projected_bytes": len(form_output.encode("utf-8")),
                "budget_bytes": INDEX_PLAN_FULL_JSON_MAX_BYTES,
                "next_action": "use a smaller --queue-limit",
            },
            budget_bytes=INDEX_PLAN_SUMMARY_JSON_MAX_BYTES,
        )
        sys.exit(2)
    if form_output:
        print(form_output)
    sys.exit(1 if errors else 0)

if args.validate_queue_forms:
    form_validation = validate_review_queue_forms(by_review_queue, all_review_queue_view)
    validation_payload = {
        "status": "planned" if form_validation.get("status") == "pass" and not errors else "blocked",
        "root": display_path(root),
        "section": args.section,
        "read_only": True,
        "report_only": True,
        "errors": errors,
        "warnings": warnings,
        "form_validation": form_validation,
    }
    if not emit_json(
        validation_payload, budget_bytes=INDEX_PLAN_FULL_JSON_MAX_BYTES
    ):
        sys.exit(2)
    sys.exit(1 if errors or form_validation.get("status") != "pass" else 0)



linking_audit = build_linking_audit(root, warnings, by_project, by_source, by_topic, decisions, by_decision, items, sources, topics, projects)

status_order = ["active", "reviewing", "archived"]

all_indexes = {
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
}
section_index_keys = {
    "owner": ["by_owner"],
    "review-date": ["by_review_date"],
    "status": ["by_status"],
    "project": ["by_project"],
    "source": ["by_source"],
    "topic": ["by_topic"],
    "decision": ["by_decision"],
    "manifest": ["by_manifest"],
    "linking": ["linking_audit"],
    "review-queue": ["by_review_queue"],
}
selected_index_keys = list(all_indexes) if args.section == "all" else section_index_keys[args.section]

result = {
    "status": "planned" if not errors else "blocked",
    "root": display_path(root),
    "item_count": len(items),
    "source_count": len(sources),
    "project_count": len(projects),
    "topic_count": len(topics),
    "section": args.section,
    "read_only": True,
    "errors": errors,
    "warnings": warnings,
    "indexes": {key: all_indexes[key] for key in selected_index_keys},
}
if args.section in {"all", "source", "manifest"}:
    result["source_coverage_selection"] = source_coverage_selection
if args.section in {"all", "linking"}:
    result["linking_audit"] = linking_audit


def compact_index_summary(key, value):
    if key == "by_review_queue":
        return {
            "summary": value.get("summary", {}),
            "pagination": value.get("pagination", {}),
        }
    if key == "by_manifest":
        return {"summary": value.get("summary", {})}
    if key == "linking_audit":
        return {
            "status": value.get("status", ""),
            "cross_session": value.get("cross_session", {}).get("status", ""),
            "cross_project": value.get("cross_project", {}).get("status", ""),
            "markdown_index_recovery": value.get("markdown_index_recovery", {}).get("status", ""),
        }
    if isinstance(value, dict):
        reference_count = sum(
            len(row) if isinstance(row, list) else 1
            for row in value.values()
        )
        return {"bucket_count": len(value), "reference_count": reference_count}
    return {"entry_count": len(value) if isinstance(value, list) else 0}


summary_result = {
    "projection": "knowledge-index-plan-summary-v1",
    "status": result["status"],
    "root": result["root"],
    "section": args.section,
    "read_only": True,
    "counts": {
        "items": len(items),
        "sources": len(sources),
        "projects": len(projects),
        "topics": len(topics),
    },
    "errors": errors,
    "warnings": warnings,
    "indexes": {
        key: compact_index_summary(key, all_indexes[key])
        for key in selected_index_keys
    },
}

if args.summary_json:
    if not emit_json(
        summary_result, budget_bytes=INDEX_PLAN_SUMMARY_JSON_MAX_BYTES
    ):
        sys.exit(2)
    sys.exit(1 if errors else 0)

if args.json:
    if not emit_json(result, budget_bytes=INDEX_PLAN_FULL_JSON_MAX_BYTES):
        sys.exit(2)
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
        print(f"- source_strategy: `{info.get('source_strategy', '')}`")
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
