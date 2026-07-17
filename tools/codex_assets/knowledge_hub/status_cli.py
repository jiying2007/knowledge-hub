import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Print a read-only Knowledge Hub status dashboard.")
parser.add_argument("--json", action="store_true")
parser.add_argument("--strict", action="store_true", help="Return non-zero unless the final status is ok.")
parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD", help="Use a fixed date for review_after checks.")
parser.add_argument("--review-queue-limit", type=int, default=20, help="Maximum rows per review queue sample in JSON/text output.")
args = parser.parse_args(argv)
args.final_profile = "product"
if args.review_queue_limit < 1:
    parser.error("--review-queue-limit must be a positive integer")

errors = []
DISPLAY_TOOL_ROOT = "~/knowledge-hub/tools"
SOURCE_CHECK_SNAPSHOT_ID = "pcr02-level2-source-check-execution-snapshot-20260621"
SOURCE_CHECK_SNAPSHOT_EXPECTED_SOURCE_IDS = [
    "pcr02-project-tools",
    "pcr02-project-knowledge",
    "pcr02-product-test",
    "pcr02-project-scratch",
    "pcr02-project-root-artifacts",
    "pcr02-module-agent-rules",
    "pcr02-project-agent-config",
]
OWNER_READY_ROW_STATUS_SOURCE = "knowledge-owner-gates.rows[].owner_ready_package_status"
PRODUCT_COPY_TARGET_PREFIXES = ("projects/", "domains/", "notes/")
PRODUCT_COPY_ALLOWED_OBJECT_TYPES = {"markdown"}
REVIEW_CONTENT_BOUND_DECISIONS = {"accept-as-review-record", "archive-only", "reject"}

def repository_file_sha256(relative_path):
    path_text = str(relative_path or "")
    if not path_text:
        return ""
    candidate = pathlib.Path(path_text)
    if candidate.is_absolute():
        return ""
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return ""
    if not resolved.is_file():
        return ""
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def resolve_today():
    if args.as_of:
        raw_value = args.as_of
        source = "arg:--as-of"
    else:
        raw_value = os.environ.get("KNOWLEDGE_TODAY", "")
        source = "env:KNOWLEDGE_TODAY" if raw_value else "system-date"
    if raw_value:
        try:
            return dt.date.fromisoformat(raw_value), source
        except Exception:
            parser.error(f"invalid date for {source}: {raw_value}")
    return dt.date.today(), source

today, today_source = resolve_today()
SOURCE_COVERAGE_RE = re.compile(r"^knowledge-hub-source-coverage-closeout-(\d{8})\.jsonl$")

def user_path_prefixes():
    prefixes = [str(pathlib.Path.home())]
    user_name = os.environ.get("USER", "")
    if user_name:
        prefixes.append("/" + "vsdata" + "/" + user_name)
    return [prefix for prefix in prefixes if prefix and prefix != "/"]

def display_path(value):
    text = str(value)
    for prefix in user_path_prefixes():
        if text == prefix:
            text = "~"
        elif text.startswith(prefix + "/"):
            text = "~" + text[len(prefix):]
        else:
            text = text.replace(prefix, "~")
    return text

def display_tool(script_name):
    return f"{DISPLAY_TOOL_ROOT}/{script_name}"

def shell_command(parts):
    quoted = []
    for part in parts:
        text = str(part)
        if text.startswith("~/"):
            quoted.append(text)
        else:
            quoted.append(shlex.quote(text))
    return " ".join(quoted)

def load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        errors.append(f"cannot load {path.relative_to(root)}: {exc}")
        return {}

def load_jsonl(path):
    rows = []
    try:
        lines = path.read_text().splitlines()
    except Exception as exc:
        errors.append(f"cannot read {path.relative_to(root)}: {exc}")
        return rows
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception as exc:
            errors.append(f"{path.relative_to(root)}:{line_no}: invalid jsonl: {exc}")
    return rows

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
        "reason_zh": "只按 knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl 的日期字段选择最新 closeout；非日期候选会被忽略，避免 future/latest 等文件名被静默选中。",
    }
    return selection, dated[-1][2] if dated else None

def run_json(command):
    completed = subprocess.run(
        command,
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload = {}
    parse_error = ""
    if completed.stdout.strip():
        try:
            payload = json.loads(completed.stdout)
        except Exception as exc:
            parse_error = str(exc)
            errors.append(f"cannot parse {' '.join(command)} output: {exc}")
    else:
        parse_error = "empty JSON output"
        errors.append(f"{' '.join(command)} returned no JSON output")
    return {
        "command": command,
        "exit_code": completed.returncode,
        "payload": payload,
        "parse_error": parse_error,
        "stderr": completed.stderr.strip(),
    }

def build_source_check_snapshot_summary():
    items_by_id = {
        str(row.get("id", "")): row
        for row in load_jsonl(root / "registry" / "items.jsonl")
        if row.get("id")
    }
    item = items_by_id.get(SOURCE_CHECK_SNAPSHOT_ID, {})
    md_relative = str(item.get("path", "")) if item else ""
    jsonl_relative = str(pathlib.Path(md_relative).with_suffix(".jsonl")) if md_relative else ""
    jsonl_path = root / jsonl_relative if jsonl_relative else root / "__missing__.jsonl"
    rows = load_jsonl(jsonl_path) if jsonl_relative and jsonl_path.is_file() else []
    row_source_ids = [
        str(row.get("source_id", ""))
        for row in rows
        if row.get("source_id")
    ]
    expected_set = set(SOURCE_CHECK_SNAPSHOT_EXPECTED_SOURCE_IDS)
    row_source_id_set = set(row_source_ids)
    failed_rows = [
        {
            "id": row.get("id", ""),
            "source_id": row.get("source_id", ""),
            "status": row.get("status", ""),
            "exit_code": row.get("exit_code", None),
            "executed": row.get("executed", None),
            "execution_mode": row.get("execution_mode", ""),
        }
        for row in rows
        if row.get("status") != "pass"
        or row.get("exit_code") != 0
        or row.get("executed") is not True
        or row.get("execution_mode") != "report-only-manual"
    ]
    status = (
        "pass"
        if item
        and bool(md_relative and (root / md_relative).is_file())
        and bool(jsonl_relative and jsonl_path.is_file())
        and len(rows) == len(SOURCE_CHECK_SNAPSHOT_EXPECTED_SOURCE_IDS)
        and not sorted(expected_set - row_source_id_set)
        and not sorted(row_source_id_set - expected_set)
        and not failed_rows
        else "fail"
    )
    return {
        "status": status,
        "artifact_id": SOURCE_CHECK_SNAPSHOT_ID,
        "scope": "pcr02-level2-only",
        "execution_mode": "report-only-manual-snapshot",
        "runtime_execution": False,
        "source_check_health_contract": "static-registry-only",
        "md_path": md_relative,
        "jsonl_path": jsonl_relative,
        "expected_source_ids": SOURCE_CHECK_SNAPSHOT_EXPECTED_SOURCE_IDS,
        "covered_source_ids": sorted(row_source_id_set),
        "expected_count": len(SOURCE_CHECK_SNAPSHOT_EXPECTED_SOURCE_IDS),
        "row_count": len(rows),
        "passed_count": len(rows) - len(failed_rows),
        "missing_source_ids": sorted(expected_set - row_source_id_set),
        "unexpected_source_ids": sorted(row_source_id_set - expected_set),
        "failed_rows": failed_rows,
        "all_executed": bool(rows) and all(row.get("executed") is True for row in rows),
        "all_exit_0": bool(rows) and all(row.get("exit_code") == 0 for row in rows),
        "checked_at": sorted({str(row.get("checked_at", "")) for row in rows if row.get("checked_at")}),
        "limitations_zh": "仅为 2026-06-21 report-only 手动快照，只证明 7 个 PCR02 Level 2 source 的路径或文件当时存在；不证明内容正确、语义可迁移、owner 签收或 active promotion。",
    }

def count_by(rows, field):
    counter = collections.Counter()
    for row in rows:
        value = str(row.get(field, "") or "<missing>")
        counter[value] += 1
    return dict(sorted(counter.items()))

def parse_date(value):
    try:
        return dt.date.fromisoformat(str(value))
    except Exception:
        return None

items = load_jsonl(root / "registry" / "items.jsonl")
sources_payload = load_json(root / "registry" / "sources.json")
current_sources = sources_payload.get("sources", [])
retired_sources = load_jsonl(root / "registry" / "retired-sources.jsonl")
sources = current_sources + retired_sources

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

def source_looks_external(source):
    path_text = str(source.get("path", ""))
    return (
        path_text.startswith("http://")
        or path_text.startswith("https://")
        or any(not is_blank(source.get(field)) for field in ["retrieved_at", "read_status", "source_license", "source_url", "url"])
    )

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

def build_review_queues(items, sources):
    ai_rows = []
    external_rows = []
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
                ai_rows.append(
                    make_review_queue_item(
                        item,
                        "ai-human-review",
                        [f"missing-{field.replace('_', '-')}" for field in missing_fields],
                        missing_fields,
                    )
                )
            elif str(item.get("human_review_decision", "")) in {"needs-edits", "defer"}:
                review_decision = str(item.get("human_review_decision", ""))
                ai_rows.append(
                    make_review_queue_item(
                        item,
                        "ai-human-review",
                        [f"unresolved-{review_decision}"],
                        ["review_resolution"],
                    )
                )
            elif review_content_drifted:
                ai_rows.append(
                    make_review_queue_item(
                        item,
                        "ai-human-review",
                        ["unresolved-content-sha256-drift"],
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
                external_rows.append(
                    make_review_queue_item(
                        item,
                        "external-source-review",
                        [f"missing-{field.replace('_', '-')}" for field in missing_fields],
                        missing_fields,
                    )
                )
    for source in sources:
        if source_looks_external(source):
            external_row = make_external_source_queue_item(source)
            if external_row.get("missing_fields"):
                external_rows.append(external_row)

    def sort_key(row):
        return (
            str(row.get("priority", "P9")),
            str(row.get("review_after", "") or "9999-12-31"),
            str(row.get("owner", "")),
            str(row.get("id", "")),
        )

    ai_rows = sorted(ai_rows, key=sort_key)
    external_rows = sorted(external_rows, key=sort_key)
    all_rows = ai_rows + external_rows
    priority_counts = collections.Counter(str(row.get("priority", "")) for row in all_rows)
    owner_counts = collections.Counter(str(row.get("owner", "") or "<missing-owner>") for row in all_rows)
    active_or_promotion_rows = [row for row in all_rows if row.get("priority") == "P0"]
    recommended_row = ai_rows[0] if ai_rows else (external_rows[0] if external_rows else {})
    active_blocking_final_gate = bool(active_or_promotion_rows)
    product_blocking_final_gate = bool(all_rows)

    def review_queue_command(json_mode=False, forms_jsonl=False, validate_queue_forms_path=""):
        parts = [
            "rtk",
            "bash",
            "~/knowledge-hub/tools/knowledge-index-plan.sh",
            "--section",
            "review-queue",
        ]
        if recommended_row.get("queue_type"):
            parts.extend(["--queue-type", str(recommended_row.get("queue_type", ""))])
        if recommended_row.get("owner"):
            parts.extend(["--queue-owner", str(recommended_row.get("owner", ""))])
        parts.extend(["--queue-limit", str(args.review_queue_limit)])
        if json_mode:
            parts.append("--json")
        if forms_jsonl:
            parts.append("--queue-forms-jsonl")
        if validate_queue_forms_path:
            parts.extend(["--validate-queue-forms", validate_queue_forms_path])
        return " ".join(parts)

    status_json_command = f"rtk bash ~/knowledge-hub/tools/knowledge-status.sh --as-of {today.isoformat()} --json"

    return {
        "status": "needs-human-review" if all_rows else "clear",
        "read_only": True,
        "report_only": True,
        "final_profile": args.final_profile,
        "active_blocking_final_gate": active_blocking_final_gate,
        "product_blocking_final_gate": product_blocking_final_gate,
        "blocking_final_gate": product_blocking_final_gate,
        "queue_source": "registry/items.jsonl + registry/sources.json",
        "sample_limit": args.review_queue_limit,
        "summary": {
            "total_pending_count": len(all_rows),
            "ai_generated_pending_count": len(ai_rows),
            "external_source_pending_count": len(external_rows),
            "active_or_promotion_blocker_count": len(active_or_promotion_rows),
            "by_priority": dict(sorted(priority_counts.items())),
            "by_owner": dict(sorted(owner_counts.items())),
        },
        "ai_generated_pending": ai_rows[:args.review_queue_limit],
        "external_source_pending": external_rows[:args.review_queue_limit],
        "commands": {
            "status_json": status_json_command,
            "index_plan": "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --json",
            "recommended_batch_json": review_queue_command(json_mode=True),
            "recommended_forms_jsonl": review_queue_command(forms_jsonl=True),
            "recommended_validate_queue_forms": review_queue_command(json_mode=True, validate_queue_forms_path="'<review-queue-forms.jsonl>'"),
        },
        "must_not": [
            "队列是 report-only 派生视图，不写 registry",
            "不得把 AI 草稿或外部资料队列当 owner decision",
            "不得自动提升 active 或关闭 owner gate",
            "不得写 ~/.codex/memories",
        ],
    }

review_queues = build_review_queues(items, sources)

knowledge_check = run_json(["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics", "--as-of", today.isoformat()])
owner_gates = run_json(["rtk", "bash", "tools/knowledge-owner-gates.sh", "--status", "all", "--json"])

stale_items = []
for item in items:
    review_after = parse_date(item.get("review_after", ""))
    if review_after and review_after < today and item.get("status") in {"active", "reviewing"}:
        stale_items.append({
            "id": item.get("id", ""),
            "status": item.get("status", ""),
            "review_after": item.get("review_after", ""),
            "owner": item.get("owner", ""),
        })

latest_source_coverage = ""
latest_source_coverage_selection, latest_source_coverage_path = select_source_coverage_closeout(root)
if latest_source_coverage_path:
    latest_source_coverage = str(latest_source_coverage_path.relative_to(root))

owner_payload = owner_gates["payload"]
check_payload = knowledge_check["payload"]
active_exposure_count = int(owner_payload.get("active_exposure_count", 0) or 0)
open_owner_gate_count = int(owner_payload.get("open_count", 0) or 0)
owner_ready_package_count = int(owner_payload.get("owner_ready_package_count", 0) or 0)
owner_ready_missing_count = int(owner_payload.get("owner_ready_missing_count", 0) or 0)
owner_ready_invalid_count = int(owner_payload.get("owner_ready_invalid_count", 0) or 0)
owner_ready_duplicate_count = int(owner_payload.get("owner_ready_duplicate_count", 0) or 0)
owner_ready_package_coverage = str(owner_payload.get("owner_ready_package_coverage", ""))
owner_rows = owner_payload.get("rows", [])
open_owner_rows = sorted(
    [row for row in owner_rows if row.get("status") == "open"],
    key=lambda row: (
        str(row.get("review_after", "") or "9999-12-31"),
        str(row.get("id", "")),
    ),
)
owner_ready_row_schema_errors = [
    {
        "worksheet_id": str(row.get("id", "")),
        "source_id": str(row.get("source_id", "")),
        "source_path": str(row.get("source_path", "")),
        "missing_field": "owner_ready_package_status",
        "expected_source": OWNER_READY_ROW_STATUS_SOURCE,
        "summary_zh": "open owner row 缺少 owner-ready 逐行强校验状态；status dashboard 不再从 registry_items 静默推断 covered。",
    }
    for row in open_owner_rows
    if "owner_ready_package_status" not in row
]
next_owner_gate = {}
next_open_queue = []
owner_dispatch = []
summary_commands = []
owner_summary_commands = []
owner_forms_jsonl_commands = []
owner_evidence_readiness_commands = []
owner_validate_forms_command_templates = []
owner_landing_plan_command_templates = []
owner_landing_audit_command_templates = []
forms_jsonl_commands = []
evidence_readiness_commands = []
validate_forms_command_templates = []
landing_plan_command_templates = []
landing_audit_command_templates = []
def safe_slug(value):
    text = str(value).strip().lower()
    chars = []
    for char in text:
        if char.isalnum() or char in {"-", "_"}:
            chars.append(char)
        else:
            chars.append("-")
    slug = "".join(chars).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "owner"

def make_status_owner_handoff_packet(owner, source_id, owner_rows, next_owner_row):
    local_path = (
        f"artifacts/manifests/{source_id}-{safe_slug(owner)}-owner-decisions-YYYYMMDD.local.jsonl"
        if source_id
        else "artifacts/manifests/<source-id>-<owner>-owner-decisions-YYYYMMDD.local.jsonl"
    )
    base = ["rtk", "bash", display_tool("knowledge-owner-gates.sh")]
    summary = shell_command(base + ["--source-id", source_id, "--owner", owner, "--summary"]) if source_id else ""
    owner_inbox = shell_command(base + ["--source-id", source_id, "--owner", owner, "--owner-inbox", "--json"]) if source_id else ""
    readiness = shell_command(base + ["--source-id", source_id, "--owner", owner, "--evidence-readiness", "--json"]) if source_id else ""
    forms = shell_command(base + ["--source-id", source_id, "--owner", owner, "--forms-jsonl"]) if source_id else ""
    validate = shell_command(base + ["--source-id", source_id, "--owner", owner, "--validate-forms", "<owner-decisions.jsonl>", "--json"]) if source_id else ""
    landing_plan = shell_command(base + ["--source-id", source_id, "--owner", owner, "--validate-forms", "<owner-decisions.jsonl>", "--landing-plan", "--json"]) if source_id else ""
    landing_audit = shell_command(base + ["--source-id", source_id, "--owner", owner, "--validate-forms", "<owner-decisions.jsonl>", "--landing-audit", "--json"]) if source_id else ""
    required_fields = []
    must_not = []
    for row in owner_rows:
        for field in row.get("required_owner_fields", []):
            if field not in required_fields:
                required_fields.append(field)
        for rule in row.get("must_not", []):
            if rule not in must_not:
                must_not.append(rule)
    return {
        "status": "ready-for-owner-review" if owner_rows else "empty",
        "read_only": True,
        "source_identity_read_policy": {
            "source_identity_read_mode": "read-bytes-for-hash",
            "source_body_read_for_hash": True,
            "source_body_copied": False,
            "source_project_written": False,
            "owner_gate_mutation": False,
            "notes_zh": "status 通过 knowledge-owner-gates 读取 source identity；为计算 hash 会只读读取 source 文件字节，但不复制正文、不写源项目、不生成 owner decision、不关闭 gate。",
        },
        "owner": owner,
        "source_id": source_id,
        "open_count": len(owner_rows),
        "worksheet_ids": [str(row.get("id", "")) for row in owner_rows],
        "next_worksheet_id": str(next_owner_row.get("id", "")) if next_owner_row else "",
        "suggested_local_owner_decisions_path": local_path,
        "manual_owner_fields": required_fields,
        "recommended_sequence": [
            {"step": "1-open-owner-inbox", "command": owner_inbox, "notes_zh": "单屏查看 owner 问题、字段分组、候选证据和后续命令；不生成 owner decision。"},
            {"step": "2-review-summary", "command": summary, "notes_zh": "确认 owner 角色、open worksheet、source path 和 owner_route；这一步不生成 owner decision。"},
            {"step": "3-check-evidence-readiness", "command": readiness, "notes_zh": "只读查看 source identity、owner-ready evidence ref 候选和仍需人工回答的字段；source identity 为 hash 会读取 source 字节但不复制正文。"},
            {"step": "4-export-forms", "command": forms, "output_path_hint": local_path, "notes_zh": "导出表单骨架到 stdout；owner 可另存为 .local.jsonl 后手工填写，工具不写该文件。"},
            {"step": "5-validate-filled-forms", "command_template": validate, "replace_placeholder_with": local_path, "notes_zh": "只读校验 owner 填写结果；不通过时不得进入 landing plan。"},
            {"step": "6-plan-manual-landing", "command_template": landing_plan, "replace_placeholder_with": local_path, "notes_zh": "生成 no-write 人工落地计划；仍不写 registry、worksheet、migration 或 index。"},
            {"step": "7-audit-manual-landing", "command_template": landing_audit, "replace_placeholder_with": local_path, "notes_zh": "人工落地后复核 worksheet、registry、source policy 和 index 是否同步；不能把 audit 当 owner approval。"},
        ],
        "must_not": [
            "不得把 routing_owner 当 reviewed_by",
            "不得由工具或 AI 代签 owner decision",
            "不得关闭未签收 owner gate",
            "不得把 owner-ready package 当作已批准决策",
        ] + [rule for rule in must_not if rule not in {
            "不得把 routing_owner 当 reviewed_by",
            "不得由工具或 AI 代签 owner decision",
            "不得关闭未签收 owner gate",
            "不得把 owner-ready package 当作已批准决策",
        }],
        "notes_zh": "只读 owner handoff 包；用于跨会话恢复人工领取顺序，不生成、不保存、不应用 owner decision。",
    }

def make_next_open_queue_entry(row):
    source_id = str(row.get("source_id", ""))
    worksheet_id = str(row.get("id", ""))
    base = [
        "rtk",
        "bash",
        display_tool("knowledge-owner-gates.sh"),
        "--source-id",
        source_id,
        "--worksheet-id",
        worksheet_id,
    ]
    owner_ready_packages = row.get("owner_ready_packages", []) if isinstance(row.get("owner_ready_packages", []), list) else []
    owner_ready_package_status = str(row.get("owner_ready_package_status", ""))
    if not owner_ready_package_status:
        owner_ready_package_status = "unknown-owner-ready-status"
    owner_ready_package_ids = [
        str(item.get("id", ""))
        for item in owner_ready_packages
        if isinstance(item, dict) and item.get("id")
    ]
    return {
        "worksheet_id": worksheet_id,
        "source_id": source_id,
        "source_path": str(row.get("source_path", "")),
        "owner": str(row.get("owner", "")),
        "owner_route": row.get("owner_route", {}),
        "review_after": str(row.get("review_after", "")),
        "owner_question_zh": str(row.get("owner_question_zh", "")),
        "owner_ready_package_status": owner_ready_package_status,
        "owner_ready_package_status_source": str(row.get("owner_ready_package_status_source", OWNER_READY_ROW_STATUS_SOURCE)),
        "owner_ready_source": OWNER_READY_ROW_STATUS_SOURCE,
        "owner_ready_package_ids": owner_ready_package_ids,
        "owner_ready_package_count": int(row.get("owner_ready_package_count", len(owner_ready_package_ids)) or 0),
        "selection_order": "review_after, worksheet_id",
        "focus_command": shell_command(base + ["--checklist", "--forms"]),
        "forms_jsonl_command": shell_command(base + ["--forms-jsonl"]),
        "evidence_readiness_command": shell_command(base + ["--evidence-readiness", "--json"]),
        "validate_forms_command_template": shell_command(base + ["--validate-forms", "<owner-decisions.jsonl>", "--json"]),
        "landing_plan_command_template": shell_command(base + ["--validate-forms", "<owner-decisions.jsonl>", "--landing-plan", "--json"]),
        "landing_audit_command_template": shell_command(base + ["--validate-forms", "<owner-decisions.jsonl>", "--landing-audit", "--json"]),
        "notes_zh": "只读下一批 owner gate 恢复队列；按 review_after 和 worksheet_id 排序，不生成 owner decision，不关闭 gate。",
    }

if open_owner_rows:
    next_open_queue = [make_next_open_queue_entry(row) for row in open_owner_rows]
    rows_by_scope = collections.defaultdict(list)
    for row in open_owner_rows:
        owner = str(row.get("owner", "") or "<missing-owner>")
        source_id = str(row.get("source_id", "") or "")
        rows_by_scope[(source_id, owner)].append(row)
    for (source_id, owner), owner_rows in sorted(rows_by_scope.items()):
        next_owner_row = sorted(
            owner_rows,
            key=lambda row: (
                str(row.get("review_after", "") or "9999-12-31"),
                str(row.get("id", "")),
            ),
        )[0]
        owner_routes = []
        seen_owner_routes = set()
        for row in owner_rows:
            route = row.get("owner_route", {})
            if not route:
                continue
            key = json.dumps(route, ensure_ascii=False, sort_keys=True)
            if key in seen_owner_routes:
                continue
            seen_owner_routes.add(key)
            owner_routes.append(route)
        owner_dispatch.append({
            "owner": owner,
            "source_id": source_id,
            "source_ids": [source_id] if source_id else [],
            "dispatch_scope_id": f"{source_id or '<missing-source>'}:{owner}",
            "mixed_source_owner": False,
            "owner_route": owner_routes[0] if len(owner_routes) == 1 else {},
            "owner_routes": owner_routes,
            "row_count": len(owner_rows),
            "open_count": len(owner_rows),
            "worksheet_ids": [str(row.get("id", "")) for row in owner_rows],
            "source_paths": [str(row.get("source_path", "")) for row in owner_rows],
            "owner_inbox_json_command": shell_command([
                "rtk",
                "bash",
                display_tool("knowledge-owner-gates.sh"),
                "--source-id",
                source_id,
                "--owner",
                owner,
                "--owner-inbox",
                "--json",
            ]) if source_id else "",
            "summary_command": shell_command([
                "rtk",
                "bash",
                display_tool("knowledge-owner-gates.sh"),
                "--source-id",
                source_id,
                "--owner",
                owner,
                "--summary",
            ]) if source_id else "",
            "forms_jsonl_command": shell_command([
                "rtk",
                "bash",
                display_tool("knowledge-owner-gates.sh"),
                "--source-id",
                source_id,
                "--owner",
                owner,
                "--forms-jsonl",
            ]) if source_id else "",
            "evidence_readiness_command": shell_command([
                "rtk",
                "bash",
                display_tool("knowledge-owner-gates.sh"),
                "--source-id",
                source_id,
                "--owner",
                owner,
                "--evidence-readiness",
                "--json",
            ]) if source_id else "",
            "handoff_packet_json_command": shell_command([
                "rtk",
                "bash",
                display_tool("knowledge-owner-gates.sh"),
                "--source-id",
                source_id,
                "--owner",
                owner,
                "--handoff-packet",
                "--json",
            ]) if source_id else "",
            "validate_forms_command_template": shell_command([
                "rtk",
                "bash",
                display_tool("knowledge-owner-gates.sh"),
                "--source-id",
                source_id,
                "--owner",
                owner,
                "--validate-forms",
                "<owner-decisions.jsonl>",
                "--json",
            ]) if source_id else "",
            "landing_plan_command_template": shell_command([
                "rtk",
                "bash",
                display_tool("knowledge-owner-gates.sh"),
                "--source-id",
                source_id,
                "--owner",
                owner,
                "--validate-forms",
                "<owner-decisions.jsonl>",
                "--landing-plan",
                "--json",
            ]) if source_id else "",
            "landing_audit_command_template": shell_command([
                "rtk",
                "bash",
                display_tool("knowledge-owner-gates.sh"),
                "--source-id",
                source_id,
                "--owner",
                owner,
                "--validate-forms",
                "<owner-decisions.jsonl>",
                "--landing-audit",
                "--json",
            ]) if source_id else "",
            "next_focus_command": shell_command([
                "rtk",
                "bash",
                display_tool("knowledge-owner-gates.sh"),
                "--source-id",
                str(next_owner_row.get("source_id", "")),
                "--owner",
                owner,
                "--worksheet-id",
                str(next_owner_row.get("id", "")),
                "--checklist",
                "--forms",
            ]),
            "suggested_owner_packet": make_status_owner_handoff_packet(owner, source_id, owner_rows, next_owner_row),
            "notes_zh": "status dashboard 只读 owner 分派摘要；按 source_id + owner 分派，避免同一 owner 跨 source 时丢失 source scope。用于跨会话恢复 owner 领取、表单导出、校验和 landing-plan 入口，不生成 owner decision，不关闭 gate。",
        })
    for source_id in sorted({str(row.get("source_id", "")) for row in open_owner_rows if row.get("source_id")}):
        summary_command = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--summary",
        ]
        summary_commands.append(shell_command(summary_command))
    for source_id, owner in sorted({
        (str(row.get("source_id", "")), str(row.get("owner", "")))
        for row in open_owner_rows
        if row.get("source_id") and row.get("owner")
    }):
        owner_summary_command = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--owner",
            owner,
            "--summary",
        ]
        owner_summary_commands.append(shell_command(owner_summary_command))
        owner_forms_jsonl_command = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--owner",
            owner,
            "--forms-jsonl",
        ]
        owner_forms_jsonl_commands.append(shell_command(owner_forms_jsonl_command))
        owner_evidence_readiness_command = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--owner",
            owner,
            "--evidence-readiness",
            "--json",
        ]
        owner_evidence_readiness_commands.append(shell_command(owner_evidence_readiness_command))
        owner_validate_forms_command_template = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--owner",
            owner,
            "--validate-forms",
            "<owner-decisions.jsonl>",
            "--json",
        ]
        owner_validate_forms_command_templates.append(shell_command(owner_validate_forms_command_template))
        owner_landing_plan_command_template = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--owner",
            owner,
            "--validate-forms",
            "<owner-decisions.jsonl>",
            "--landing-plan",
            "--json",
        ]
        owner_landing_plan_command_templates.append(shell_command(owner_landing_plan_command_template))
        owner_landing_audit_command_template = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--owner",
            owner,
            "--validate-forms",
            "<owner-decisions.jsonl>",
            "--landing-audit",
            "--json",
        ]
        owner_landing_audit_command_templates.append(shell_command(owner_landing_audit_command_template))
    for source_id in sorted({str(row.get("source_id", "")) for row in open_owner_rows if row.get("source_id")}):
        forms_jsonl_command = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--forms-jsonl",
        ]
        forms_jsonl_commands.append(shell_command(forms_jsonl_command))
        evidence_readiness_command = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--evidence-readiness",
            "--json",
        ]
        evidence_readiness_commands.append(shell_command(evidence_readiness_command))
        validation_command_template = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--validate-forms",
            "<owner-decisions.jsonl>",
            "--json",
        ]
        validate_forms_command_templates.append(shell_command(validation_command_template))
        landing_plan_command_template = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--validate-forms",
            "<owner-decisions.jsonl>",
            "--landing-plan",
            "--json",
        ]
        landing_plan_command_templates.append(shell_command(landing_plan_command_template))
        landing_audit_command_template = [
            "rtk",
            "bash",
            display_tool("knowledge-owner-gates.sh"),
            "--source-id",
            source_id,
            "--validate-forms",
            "<owner-decisions.jsonl>",
            "--landing-audit",
            "--json",
        ]
        landing_audit_command_templates.append(shell_command(landing_audit_command_template))
    first_open = open_owner_rows[0]
    next_open_command = [
        "rtk",
        "bash",
        display_tool("knowledge-owner-gates.sh"),
        "--source-id",
        first_open.get("source_id", ""),
        "--next-open",
        "--checklist",
        "--forms",
    ]
    next_open_forms_jsonl_command = [
        "rtk",
        "bash",
        display_tool("knowledge-owner-gates.sh"),
        "--source-id",
        first_open.get("source_id", ""),
        "--next-open",
        "--forms-jsonl",
    ]
    next_open_evidence_readiness_command = [
        "rtk",
        "bash",
        display_tool("knowledge-owner-gates.sh"),
        "--source-id",
        first_open.get("source_id", ""),
        "--next-open",
        "--evidence-readiness",
        "--json",
    ]
    focus_command = [
        "rtk",
        "bash",
        display_tool("knowledge-owner-gates.sh"),
        "--source-id",
        first_open.get("source_id", ""),
        "--worksheet-id",
        first_open.get("id", ""),
        "--checklist",
        "--forms",
    ]
    focus_forms_jsonl_command = [
        "rtk",
        "bash",
        display_tool("knowledge-owner-gates.sh"),
        "--source-id",
        first_open.get("source_id", ""),
        "--worksheet-id",
        first_open.get("id", ""),
        "--forms-jsonl",
    ]
    focus_evidence_readiness_command = [
        "rtk",
        "bash",
        display_tool("knowledge-owner-gates.sh"),
        "--source-id",
        first_open.get("source_id", ""),
        "--worksheet-id",
        first_open.get("id", ""),
        "--evidence-readiness",
        "--json",
    ]
    focus_validate_forms_command_template = [
        "rtk",
        "bash",
        display_tool("knowledge-owner-gates.sh"),
        "--source-id",
        first_open.get("source_id", ""),
        "--worksheet-id",
        first_open.get("id", ""),
        "--validate-forms",
        "<owner-decisions.jsonl>",
        "--json",
    ]
    focus_landing_plan_command_template = [
        "rtk",
        "bash",
        display_tool("knowledge-owner-gates.sh"),
        "--source-id",
        first_open.get("source_id", ""),
        "--worksheet-id",
        first_open.get("id", ""),
        "--validate-forms",
        "<owner-decisions.jsonl>",
        "--landing-plan",
        "--json",
    ]
    focus_landing_audit_command_template = [
        "rtk",
        "bash",
        display_tool("knowledge-owner-gates.sh"),
        "--source-id",
        first_open.get("source_id", ""),
        "--worksheet-id",
        first_open.get("id", ""),
        "--validate-forms",
        "<owner-decisions.jsonl>",
        "--landing-audit",
        "--json",
    ]
    next_owner_gate = {
        "worksheet_id": first_open.get("id", ""),
        "source_id": first_open.get("source_id", ""),
        "source_path": first_open.get("source_path", ""),
        "owner": first_open.get("owner", ""),
        "owner_route": first_open.get("owner_route", {}),
        "review_after": first_open.get("review_after", ""),
        "selection_order": "review_after, worksheet_id",
        "next_open_command": shell_command(next_open_command),
        "next_open_forms_jsonl_command": shell_command(next_open_forms_jsonl_command),
        "next_open_evidence_readiness_command": shell_command(next_open_evidence_readiness_command),
        "focus_command": shell_command(focus_command),
        "focus_forms_jsonl_command": shell_command(focus_forms_jsonl_command),
        "focus_evidence_readiness_command": shell_command(focus_evidence_readiness_command),
        "focus_validate_forms_command_template": shell_command(focus_validate_forms_command_template),
        "focus_landing_plan_command_template": shell_command(focus_landing_plan_command_template),
        "focus_landing_audit_command_template": shell_command(focus_landing_audit_command_template),
    }

def build_product_source_inventory_audit():
    rows = []
    blockers = []
    for source in sorted(sources, key=lambda row: str(row.get("id", ""))):
        source_id = str(source.get("id", ""))
        if not source_id:
            continue
        inventory_path = root / "sources" / source_id / "inventory.jsonl"
        if not inventory_path.exists():
            blockers.append({
                "source_id": source_id,
                "row_id": "",
                "reason": "missing-inventory",
                "summary_zh": "source 缺少 inventory.jsonl，不能证明正文最大迁移处置已覆盖。",
            })
            continue
        inventory_rows = load_jsonl(inventory_path)
        if not inventory_rows:
            blockers.append({
                "source_id": source_id,
                "row_id": "",
                "reason": "empty-inventory",
                "summary_zh": "source inventory 为空，不能证明正文最大迁移处置已覆盖。",
            })
        for line_no, row in enumerate(inventory_rows, 1):
            row_id = str(row.get("id", f"{source_id}:{line_no}"))
            object_type = str(row.get("object_type", ""))
            disposition = str(row.get("hub_disposition", ""))
            row_status = str(row.get("status", ""))
            target_path = str(row.get("target_path", "")).strip()
            row_blockers = []
            if row_status == "pending":
                row_blockers.append("pending-row")
            if disposition == "copy-body":
                if object_type not in PRODUCT_COPY_ALLOWED_OBJECT_TYPES:
                    row_blockers.append("copy-body-non-markdown")
                if not target_path:
                    row_blockers.append("copy-body-missing-target")
                elif not target_path.startswith(PRODUCT_COPY_TARGET_PREFIXES):
                    row_blockers.append("copy-body-noncanonical-target")
                elif not (root / target_path).exists():
                    row_blockers.append("copy-body-target-missing")
            rows.append({
                "source_id": source_id,
                "row_id": row_id,
                "line": line_no,
                "object_type": object_type,
                "hub_disposition": disposition,
                "target_path": target_path,
                "status": row_status,
                "blockers": row_blockers,
            })
            if row_blockers:
                blockers.append({
                    "source_id": source_id,
                    "row_id": row_id,
                    "line": line_no,
                    "reason": ",".join(row_blockers),
                    "object_type": object_type,
                    "hub_disposition": disposition,
                    "target_path": target_path,
                    "status": row_status,
                    "summary_zh": "product 要求正文复制仅限可维护 Markdown，并落到 projects/domains/notes；其他对象必须 summary/reference/artifact/archive/exclude。",
                })
    by_reason = collections.Counter()
    for blocker in blockers:
        for reason in str(blocker.get("reason", "")).split(","):
            if reason:
                by_reason[reason] += 1
    return {
        "status": "pass" if not blockers else "needs-fix",
        "profile": "product",
        "row_count": len(rows),
        "blocker_count": len(blockers),
        "by_reason": dict(sorted(by_reason.items())),
        "blockers": blockers,
        "rules": {
            "copy_body_allowed_object_types": sorted(PRODUCT_COPY_ALLOWED_OBJECT_TYPES),
            "copy_body_target_prefixes": list(PRODUCT_COPY_TARGET_PREFIXES),
            "pending_rows_block_final_gate": True,
        },
        "notes_zh": "product 终态要求可复制正文落到 canonical 正文层；raw/session/history/log/binary/source-code/tool/config/artifact 不得全文 copy-body。",
    }

product_source_inventory_audit = build_product_source_inventory_audit()

owner_gates_failed = owner_gates["exit_code"] != 0
review_queue_blocking_count = int(review_queues.get("summary", {}).get("active_or_promotion_blocker_count", 0) or 0)
review_queue_product_blocking_count = int(review_queues.get("summary", {}).get("total_pending_count", 0) or 0)
product_source_inventory_blocking_count = int(product_source_inventory_audit.get("blocker_count", 0) or 0)

PRODUCT_NONCANONICAL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bmigrated-",
        r"copy-?first",
        r"copyfirst",
        r"migration-baseline",
        r"migration-applied",
        r"migration-dry-run",
        r"source-docs",
    ]
]
PRODUCT_PROCESS_MANIFEST_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"copy-?first",
        r"source-inventory-\d{8}",
        r"project-docs-classification-\d{8}",
    ]
]
PRODUCT_ALLOWED_PROCESS_MANIFEST_NAMES = {
    "knowledge-hub-governance-regression-helper-20260619.md",
}
PRODUCT_REVIEWING_TARGET_RATIO = 0.10

def product_noncanonical_text_matches(*values):
    text_parts = []
    for value in values:
        if isinstance(value, list):
            text_parts.extend(str(item) for item in value)
        elif value is not None:
            text_parts.append(str(value))
    haystack = " ".join(text_parts)
    return any(pattern.search(haystack) for pattern in PRODUCT_NONCANONICAL_PATTERNS)

def product_sealed_historical_item(item):
    status_value = str(item.get("status", ""))
    path_value = str(item.get("path", ""))
    review_status = str(item.get("review_status", ""))
    tags = item.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    tag_set = {str(tag) for tag in tags}
    if status_value != "archived":
        return False
    if "/current/" in path_value or path_value.startswith("projects/") and "/archive/" not in path_value and not path_value.startswith("artifacts/manifests/"):
        return False
    if "owner-ready-no-decision" in review_status or "delete-blocked" in review_status or review_status.endswith("-open"):
        return False
    sealed_tags = {
        "archive-only",
        "deleted-tombstoned",
        "historical-session",
        "historical-release",
        "historical-policy",
        "historical-analysis",
        "historical-code-analysis",
        "historical-memory-curation",
        "no-active-promotion",
        "tombstone",
        "delete-execution",
        "coverage-audit",
    }
    return bool(tag_set & sealed_tags) or path_value.startswith("artifacts/manifests/")

def build_product_noncanonical_residue_audit():
    noncanonical_item_hits = []
    sealed_historical_hits = []
    long_lived_reviewing = []
    archived_noncanonical_hits = []
    for item in items:
        item_id = str(item.get("id", ""))
        status_value = str(item.get("status", ""))
        hit = product_noncanonical_text_matches(
            item_id,
            item.get("path", ""),
            item.get("tags", []),
            item.get("review_status", ""),
            item.get("summary_zh", ""),
        )
        if hit:
            item_ref = {
                "id": item_id,
                "status": status_value,
                "kind": item.get("kind", ""),
                "domain": item.get("domain", ""),
                "path": item.get("path", ""),
                "review_status": item.get("review_status", ""),
                "tags": item.get("tags", []),
            }
            if product_sealed_historical_item(item):
                sealed_historical_hits.append(item_ref)
                continue
            noncanonical_item_hits.append(item_ref)
            if status_value == "archived":
                archived_noncanonical_hits.append(item_id)
        if status_value == "reviewing":
            long_lived_reviewing.append({
                "id": item_id,
                "domain": item.get("domain", ""),
                "path": item.get("path", ""),
                "review_after": item.get("review_after", ""),
                "review_status": item.get("review_status", ""),
            })

    process_manifest_hits = []
    manifests_root = root / "artifacts" / "manifests"
    if manifests_root.exists():
        for path in sorted(manifests_root.iterdir()):
            if not path.is_file():
                continue
            name = path.name
            if name in PRODUCT_ALLOWED_PROCESS_MANIFEST_NAMES:
                continue
            if any(pattern.search(name) for pattern in PRODUCT_PROCESS_MANIFEST_PATTERNS):
                process_manifest_hits.append(display_path(path))

    copy_first_tools = [
        display_path(path)
        for path in sorted((root / "tools").glob("knowledge-copy-first*.sh"))
        if path.exists()
    ]
    source_current_closed = [
        {
            "id": str(source.get("id", "")),
            "status": source.get("status", ""),
            "final_disposition": source.get("final_disposition", ""),
            "canonical_target": source.get("canonical_target", ""),
        }
        for source in current_sources
        if str(source.get("status", "")) == "retired"
    ]

    reviewing_count = len(long_lived_reviewing)
    item_count = len(items)
    reviewing_ratio = round(reviewing_count / item_count, 4) if item_count else 0
    blockers = []
    if noncanonical_item_hits:
        blockers.append({
            "id": "product-noncanonical-items",
            "count": len(noncanonical_item_hits),
            "summary_zh": "product 运行模型不允许带有 copy-first、migrated、source-docs 等封存流程标记的条目留在当前 registry。",
            "sample": noncanonical_item_hits[:20],
        })
    if process_manifest_hits:
        blockers.append({
            "id": "product-process-manifests",
            "count": len(process_manifest_hits),
            "summary_zh": "product 运行模型不把 copy-first、classification 或 source-inventory 过程 manifest 保留为当前树资产。",
            "sample": process_manifest_hits[:20],
        })
    if copy_first_tools:
        blockers.append({
            "id": "product-copy-first-tools",
            "count": len(copy_first_tools),
            "summary_zh": "product 运行模型不暴露 copy-first 工具入口；外部资料吸收统一走 source/intake/review/promote。",
            "sample": copy_first_tools,
        })
    if source_current_closed:
        blockers.append({
            "id": "product-closed-sources-in-current-registry",
            "count": len(source_current_closed),
            "summary_zh": "product 运行模型不把已关闭来源保留在 registry/sources.json 当前 source 主列表。",
            "sample": source_current_closed[:20],
        })
    return {
        "status": "pass" if not blockers else "needs-fix",
        "profile": "product",
        "item_count": item_count,
        "noncanonical_item_count": len(noncanonical_item_hits),
        "archived_noncanonical_item_count": len(archived_noncanonical_hits),
        "sealed_historical_item_count": len(sealed_historical_hits),
        "sealed_historical_item_sample": sealed_historical_hits[:20],
        "process_manifest_count": len(process_manifest_hits),
        "copy_first_tool_count": len(copy_first_tools),
        "closed_source_count": len(source_current_closed),
        "reviewing_count": reviewing_count,
        "reviewing_ratio": reviewing_ratio,
        "reviewing_target_ratio": PRODUCT_REVIEWING_TARGET_RATIO,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "notes_zh": "product 运行模型只允许 canonical 资产进入当前入口；reviewing 比例只作采用度观测，不作为技术失败。已封存且不可误用的历史证据只作 provenance。",
    }

product_noncanonical_residue_audit = build_product_noncanonical_residue_audit()
product_noncanonical_blocking_count = int(product_noncanonical_residue_audit.get("blocker_count", 0) or 0)

fix_blocking = (
    knowledge_check["exit_code"] != 0
    or owner_gates_failed
    or active_exposure_count
    or owner_ready_row_schema_errors
    or review_queue_blocking_count
    or product_source_inventory_blocking_count
    or product_noncanonical_blocking_count
)
owner_review_blocking = open_owner_gate_count or review_queue_product_blocking_count

if errors:
    status = "blocked"
elif fix_blocking:
    status = "needs-fix"
elif owner_review_blocking:
    status = "needs-owner-review"
else:
    status = "ok"

exit_code = 1 if status in {"blocked", "needs-fix"} or (args.strict and status != "ok") else 0
if today_source == "system-date":
    final_gate_command = "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product"
else:
    final_gate_command = f"rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --as-of {today.isoformat()} --json --final-profile product"
review_after_command = "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date"
source_review_after_command = "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source"
review_after_near_due_command = f"rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of {today.isoformat()} --window-days 30 --json"
source_check_report_command = f"rtk bash ~/knowledge-hub/tools/knowledge-source-check.sh --scope pcr02-level2 --as-of {today.isoformat()} --json"
source_check_health = check_payload.get("source_check_health", {}) if isinstance(check_payload.get("source_check_health", {}), dict) else {}
source_check_execution_snapshot = build_source_check_snapshot_summary()
source_stale_review_after_ids = set(source_check_health.get("stale_review_after_ids", []) or [])
source_check_rows = {
    str(row.get("source_id", "")): row
    for row in source_check_health.get("rows", [])
    if isinstance(row, dict)
}
source_coverage_rows = load_jsonl(latest_source_coverage_path) if latest_source_coverage_path else []
source_coverage_by_id = {
    str(row.get("source_id", "")): row
    for row in source_coverage_rows
    if isinstance(row, dict)
}
source_recovery_rows = []
for source in sorted(sources, key=lambda row: str(row.get("id", ""))):
    source_id = str(source.get("id", ""))
    check_row = source_check_rows.get(source_id, {})
    coverage_row = source_coverage_by_id.get(source_id, {})
    source_recovery_rows.append({
        "source_id": source_id,
        "status": str(source.get("status", "")),
        "owner": str(source.get("owner", "")),
        "review_after": str(source.get("review_after", "")),
        "review_after_stale": bool(check_row.get("review_after_stale", source_id in source_stale_review_after_ids)),
        "final_disposition": str(source.get("final_disposition", "")),
        "source_strategy": str(source.get("source_strategy", "")),
        "check_contract_status": str(check_row.get("check_contract_status", "")),
        "has_check": bool(check_row.get("has_check", bool(source.get("check", "")))),
        "has_no_check_reason": bool(check_row.get("has_no_check_reason", bool(source.get("no_check_reason", "")))),
        "check": str(source.get("check", "")),
        "no_check_reason": str(source.get("no_check_reason", "")),
        "coverage_status": str(coverage_row.get("status", "")),
        "coverage_classification": str(coverage_row.get("classification", "")),
        "coverage_decision": str(coverage_row.get("decision", "")),
        "coverage_risk": str(coverage_row.get("risk", "")),
        "coverage_checked_at": str(coverage_row.get("checked_at", "")),
        "coverage_owner": str(coverage_row.get("owner", "")),
    })
stale_sources = sorted(
    [
        {
            "id": str(source.get("id", "")),
            "status": str(source.get("status", "")),
            "review_after": str(source.get("review_after", "")),
            "owner": str(source.get("owner", "")),
            "final_disposition": str(source.get("final_disposition", "")),
        }
        for source in sources
        if source.get("id") in source_stale_review_after_ids
    ],
    key=lambda row: (row["review_after"], row["id"]),
)

next_actions = []
if knowledge_check["exit_code"] != 0:
    next_actions.append("先按 knowledge-check diagnostics 的 action_zh 修复阻断错误。")
if owner_gates_failed:
    next_actions.append("先修复 knowledge-owner-gates 子命令失败；status dashboard 不能在 owner gate 工具失败时作为终态证据。")
if active_exposure_count:
    next_actions.append("立即移除 owner-gated active exposure，owner 决策闭环前不得 active。")
if open_owner_gate_count:
    next_actions.append(
        "需要确认是否只剩 owner 语义门禁时，运行最终门禁："
        f"{final_gate_command}。"
    )
    if owner_ready_missing_count or owner_ready_invalid_count or owner_ready_duplicate_count:
        next_actions.append(
            "先补齐 owner-ready package 强校验覆盖，再分派 owner 决策；"
            f"当前缺失 {owner_ready_missing_count} 条、无效 {owner_ready_invalid_count} 条、重复 {owner_ready_duplicate_count} 条。"
        )
    if summary_commands:
        next_actions.append(
            "先查看 owner gate 总览以分派全部 open gate；运行："
            f"{summary_commands[0]}。"
        )
    if owner_summary_commands:
        next_actions.append(
            "需要按责任人分派 owner gate 时，先读取 JSON 中的 `owner_gates.owner_dispatch[]`；默认先打开 owner-inbox 单屏入口，再看 owner 过滤总览，例如："
            f"{owner_dispatch[0].get('owner_inbox_json_command', '') if owner_dispatch else ''}；{owner_summary_commands[0]}。"
        )
    if owner_forms_jsonl_commands:
        next_actions.append(
            "需要按责任人导出纯 JSONL owner 表单时，运行："
            f"{owner_forms_jsonl_commands[0]}。"
        )
    if owner_evidence_readiness_commands:
        next_actions.append(
            "需要按责任人查看只读证据准备度和候选值时，运行："
            f"{owner_evidence_readiness_commands[0]}。"
        )
    if owner_validate_forms_command_templates:
        next_actions.append(
            "责任人填完 JSONL 后，按 owner 范围先只读校验："
            f"{owner_validate_forms_command_templates[0]}。"
        )
    if owner_landing_plan_command_templates:
        next_actions.append(
            "责任人表单校验通过后，按 owner 范围生成无写入 landing plan："
            f"{owner_landing_plan_command_templates[0]}。"
        )
    if owner_landing_audit_command_templates:
        next_actions.append(
            "责任人表单校验通过后，按 owner 范围审计 worksheet、registry、source policy 和 index 人工落点："
            f"{owner_landing_audit_command_templates[0]}。"
        )
    if next_owner_gate:
        next_actions.append(
            "继续处理 owner decision worksheet；下一条是 "
            f"{next_owner_gate['worksheet_id']} ({next_owner_gate['source_path']})；运行："
            f"{next_owner_gate['next_open_command']}。"
        )
        if next_owner_gate.get("next_open_forms_jsonl_command"):
            next_actions.append(
                "需要保存或交给脚本处理纯 JSONL owner 表单时，运行："
                f"{next_owner_gate['next_open_forms_jsonl_command']}。"
            )
        if next_owner_gate.get("next_open_evidence_readiness_command"):
            next_actions.append(
                "需要先查看下一条 owner gate 的证据准备度时，运行："
                f"{next_owner_gate['next_open_evidence_readiness_command']}。"
            )
        if validate_forms_command_templates:
            next_actions.append(
                "owner 填完 JSONL 后，先只读校验："
                f"{validate_forms_command_templates[0]}。"
            )
        if landing_plan_command_templates:
            next_actions.append(
                "owner 表单校验通过后，生成无写入人工 landing plan："
                f"{landing_plan_command_templates[0]}。"
            )
        if landing_audit_command_templates:
            next_actions.append(
                "owner 表单校验通过后，运行人工落点审计，确认 worksheet 不会继续 open："
                f"{landing_audit_command_templates[0]}。"
            )
    else:
        next_actions.append("继续处理 owner decision worksheet；本状态表示语义决策未闭环，不是工具失败。")
if stale_items:
    next_actions.append(
        "复核 review_after 已过期的 active/reviewing 条目；先运行："
        f"{review_after_command}。"
    )
if stale_sources:
    next_actions.append(
        "复核 review_after 已过期的 registered source；先运行："
        f"{source_review_after_command}。"
    )
if review_queues.get("summary", {}).get("total_pending_count", 0):
    next_actions.append(
        "复核 AI 生成和外部资料的人工复核队列；先运行："
        f"{review_queues.get('commands', {}).get('index_plan', '')}。"
    )
if review_queue_product_blocking_count:
    next_actions.append(
        "product 终态要求 AI/外部资料复核队列清零；这是人工复核阻断，不是工具失败。先导出表单、人工填写、校验，再用 review queue apply 工具落地。"
    )
if product_source_inventory_blocking_count:
    next_actions.append(
        "product 终态要求 source inventory 无 pending，且 copy-body 仅限 canonical Markdown 正文；先查看 `product_source_inventory_audit.blockers`。"
    )
if product_noncanonical_blocking_count:
    next_actions.append(
        "product 终态要求当前 registry、manifest、source 主列表和工具入口只包含 canonical 资产；先查看 `product_noncanonical_residue_audit.blockers`。"
    )
if not next_actions:
    next_actions.append("控制面无阻断；新增内容仍按 README 人工最短路径登记、索引和验证。")

strict_blockers = []
owner_blocker_source = {
    "status_source": "knowledge-status --strict",
    "strict_blocker_ids": ["owner-gates-open"] if open_owner_gate_count else [],
    "owner_gate_open_count_field": "owner_gates.open_count",
    "owner_ready_package_coverage_field": "owner_gates.owner_ready_package_coverage",
    "active_exposure_count_field": "owner_gates.active_exposure_count",
    "open_count": open_owner_gate_count,
    "owner_ready_package_coverage": owner_ready_package_coverage,
    "active_exposure_count": active_exposure_count,
    "owner_ready_row_status_source": OWNER_READY_ROW_STATUS_SOURCE,
    "owner_ready_row_schema_error_count": len(owner_ready_row_schema_errors),
    "notes_zh": "owner gate 数量、owner-ready 覆盖和 active exposure 均来自本 status 输出的 owner_gates；next_open_queue 的逐行 owner-ready 状态只消费 knowledge-owner-gates 的强校验字段，不从 registry_items 推断 covered；本结构只解释 blocker 来源，不生成 owner decision，不关闭 gate。",
}
if errors:
    strict_blockers.append({
        "id": "status-dashboard-errors",
        "severity": "blocker",
        "count": len(errors),
        "summary_zh": "status dashboard 自身读取或解析失败，不能作为终态证据。",
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json"],
    })
if knowledge_check["exit_code"] != 0:
    strict_blockers.append({
        "id": "knowledge-check-failed",
        "severity": "blocker",
        "count": len(check_payload.get("errors", [])),
        "summary_zh": "knowledge-check 存在阻断错误，必须先按 diagnostics 修复。",
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"],
    })
if owner_gates_failed:
    strict_blockers.append({
        "id": "owner-gates-command-failed",
        "severity": "blocker",
        "count": 1,
        "summary_zh": "knowledge-owner-gates 子命令返回非零，不能把 owner gate 状态当作可信终态证据。",
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json"],
        "command": shell_command(owner_gates["command"]),
        "exit_code": owner_gates["exit_code"],
        "stderr_sample": owner_gates["stderr"][:1000],
        "parse_error": owner_gates.get("parse_error", ""),
    })
if active_exposure_count:
    strict_blockers.append({
        "id": "owner-gated-active-exposure",
        "severity": "blocker",
        "count": active_exposure_count,
        "summary_zh": "存在 unresolved owner-gated 内容暴露为 active，必须先移除 active exposure。",
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json"],
    })
if owner_ready_row_schema_errors:
    strict_blockers.append({
        "id": "owner-ready-row-schema-missing",
        "severity": "blocker",
        "count": len(owner_ready_row_schema_errors),
        "summary_zh": "owner-gates open rows 缺少逐行 owner-ready 强校验字段；不能用 registry_items presence 代替 covered。",
        "errors": owner_ready_row_schema_errors,
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json"],
    })
if review_queue_blocking_count:
    strict_blockers.append({
        "id": "review-queue-active-or-promotion-without-human-review",
        "severity": "blocker",
        "count": review_queue_blocking_count,
        "summary_zh": "存在 active 或 promotion 类条目缺少人工复核闭环；必须先补 human_reviewed_by/human_reviewed_at/review_basis，或降级为 reviewing/report-only。",
        "commands": [review_queues.get("commands", {}).get("index_plan", "")],
    })
if review_queue_product_blocking_count:
    strict_blockers.append({
        "id": "review-queue-pending-product",
        "severity": "owner-review",
        "count": review_queue_product_blocking_count,
        "summary_zh": "product 终态要求 AI/外部资料人工复核队列清零；普通待复核项属于 owner-review 阻断，不能由工具代签或自动清零。",
        "commands": [
            review_queues.get("commands", {}).get("recommended_batch_json", ""),
            review_queues.get("commands", {}).get("recommended_forms_jsonl", ""),
            review_queues.get("commands", {}).get("recommended_validate_queue_forms", ""),
            "rtk bash ~/knowledge-hub/tools/knowledge-review-queue-apply.sh --forms '<review-queue-forms.jsonl>' --dry-run",
        ],
    })
if product_source_inventory_blocking_count:
    strict_blockers.append({
        "id": "source-inventory-product-blockers",
        "severity": "blocker",
        "count": product_source_inventory_blocking_count,
        "summary_zh": "product source inventory 仍有 pending、非法 copy-body 或缺失 canonical target。",
        "blockers": product_source_inventory_audit.get("blockers", []),
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json"],
    })
if product_noncanonical_blocking_count:
    strict_blockers.append({
        "id": "product-noncanonical-residue-blockers",
        "severity": "blocker",
        "count": product_noncanonical_blocking_count,
        "summary_zh": "product 运行模型仍发现非规范 registry、manifest、source 或工具入口残留。",
        "blockers": product_noncanonical_residue_audit.get("blockers", []),
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json"],
    })
if open_owner_gate_count:
    owner_commands = list(summary_commands)
    owner_commands.extend(owner_summary_commands)
    owner_commands.extend(owner_forms_jsonl_commands)
    owner_commands.extend(owner_evidence_readiness_commands)
    if next_owner_gate.get("next_open_command"):
        owner_commands.append(next_owner_gate["next_open_command"])
    if next_owner_gate.get("next_open_forms_jsonl_command"):
        owner_commands.append(next_owner_gate["next_open_forms_jsonl_command"])
    if next_owner_gate.get("next_open_evidence_readiness_command"):
        owner_commands.append(next_owner_gate["next_open_evidence_readiness_command"])
    owner_command_templates = []
    owner_command_templates.extend(owner_validate_forms_command_templates)
    owner_command_templates.extend(owner_landing_plan_command_templates)
    owner_command_templates.extend(owner_landing_audit_command_templates)
    owner_command_templates.extend(validate_forms_command_templates)
    owner_command_templates.extend(landing_plan_command_templates)
    owner_command_templates.extend(landing_audit_command_templates)
    strict_blockers.append({
        "id": "owner-gates-open",
        "severity": "owner-review",
        "count": open_owner_gate_count,
        "summary_zh": "仍有 owner decision worksheet 未签收；这是语义门禁，不是工具失败。",
        "owner_blocker_source": owner_blocker_source,
        "commands": owner_commands,
        "command_templates": owner_command_templates,
    })

owner_review_strict_blocker_ids = [
    str(blocker.get("id", ""))
    for blocker in strict_blockers
    if isinstance(blocker, dict)
    and blocker.get("severity") == "owner-review"
    and blocker.get("id")
]
owner_blocker_source["strict_blocker_ids"] = owner_review_strict_blocker_ids
owner_blocker_source["review_queue_pending_count_field"] = "review_queues.summary.total_pending_count"
owner_blocker_source["review_queue_blocking_final_gate_field"] = "review_queues.blocking_final_gate"
owner_blocker_source["review_queue_profile_field"] = "review_queues.final_profile"
owner_blocker_source["notes_zh"] = "owner-review blocker 来源于本 status 输出的 owner_gates 与 review_queues；owner gate 数量、owner-ready 覆盖和 active exposure 来自 owner_gates，review queue 按唯一 product 终态语义判定。本结构只解释 blocker 来源，不生成 owner decision，不关闭 gate，不代签人工复核。"

result = {
    "schema_version": 1,
    "root": display_path(root),
    "read_only": True,
    "strict": args.strict,
    "final_profile": args.final_profile,
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "status": status,
    "today": today.isoformat(),
    "as_of_source": today_source,
    "owner_blocker_source": owner_blocker_source,
    "knowledge_check": {
        "exit_code": knowledge_check["exit_code"],
        "status": check_payload.get("status", "<missing>"),
        "error_count": len(check_payload.get("errors", [])),
        "warning_count": len(check_payload.get("warnings", [])),
        "diagnostic_categories": [
            category.get("id", "")
            for category in check_payload.get("diagnostics", {}).get("categories", [])
        ],
    },
    "registry": {
        "item_count": len(items),
        "by_status": count_by(items, "status"),
        "by_domain": count_by(items, "domain"),
        "stale_review_after_count": len(stale_items),
        "stale_review_after_sample": stale_items[:10],
        "review_after_command": review_after_command,
        "review_after_near_due_command": review_after_near_due_command,
    },
    "sources": {
        "registered_count": len(sources),
        "latest_coverage_manifest": latest_source_coverage,
        "latest_coverage_selection": latest_source_coverage_selection,
        "source_coverage_health": check_payload.get("source_coverage_health", {}),
        "source_check_health": source_check_health,
        "source_check_execution_snapshot": source_check_execution_snapshot,
        "source_recovery_rows": source_recovery_rows,
        "stale_review_after_count": len(stale_sources),
        "stale_review_after_sample": stale_sources[:10],
        "review_after_command": source_review_after_command,
        "source_check_report_command": source_check_report_command,
        "boundary_health": check_payload.get("boundary_health", {}),
        "product_source_inventory_audit": product_source_inventory_audit,
        "product_noncanonical_residue_audit": product_noncanonical_residue_audit,
    },
    "review_queues": review_queues,
    "owner_gates": {
        "command": shell_command(owner_gates["command"]),
        "exit_code": owner_gates["exit_code"],
        "stderr_sample": owner_gates["stderr"][:1000],
        "parse_error": owner_gates.get("parse_error", ""),
        "worksheet_count": owner_payload.get("worksheet_count", 0),
        "row_count": owner_payload.get("row_count", 0),
        "open_count": open_owner_gate_count,
        "resolved_count": owner_payload.get("resolved_count", 0),
        "active_exposure_count": active_exposure_count,
        "owner_ready_package_count": owner_ready_package_count,
        "owner_ready_missing_count": owner_ready_missing_count,
        "owner_ready_invalid_count": owner_ready_invalid_count,
        "owner_ready_duplicate_count": owner_ready_duplicate_count,
        "owner_ready_package_coverage": owner_ready_package_coverage,
        "owner_ready_missing": owner_payload.get("owner_ready_missing", []),
        "owner_ready_invalid": owner_payload.get("owner_ready_invalid", []),
        "owner_ready_duplicate": owner_payload.get("owner_ready_duplicate", []),
        "owner_ready_row_status_source": OWNER_READY_ROW_STATUS_SOURCE,
        "owner_ready_row_schema_errors": owner_ready_row_schema_errors,
        "source_identity_read_policy": owner_payload.get("source_identity_read_policy", {
            "source_identity_read_mode": "read-bytes-for-hash",
            "source_body_read_for_hash": True,
            "source_body_copied": False,
            "source_project_written": False,
            "owner_gate_mutation": False,
            "notes_zh": "status 通过 knowledge-owner-gates 获取 owner gate source identity；不复制正文、不写源项目、不生成 owner decision、不关闭 gate。",
        }),
        "owner_dispatch": owner_dispatch,
        "summary_commands": summary_commands,
        "owner_summary_commands": owner_summary_commands,
        "owner_forms_jsonl_commands": owner_forms_jsonl_commands,
        "owner_evidence_readiness_commands": owner_evidence_readiness_commands,
        "owner_validate_forms_command_templates": owner_validate_forms_command_templates,
        "owner_landing_plan_command_templates": owner_landing_plan_command_templates,
        "owner_landing_audit_command_templates": owner_landing_audit_command_templates,
        "forms_jsonl_commands": forms_jsonl_commands,
        "evidence_readiness_commands": evidence_readiness_commands,
        "validate_forms_command_templates": validate_forms_command_templates,
        "landing_plan_command_templates": landing_plan_command_templates,
        "landing_audit_command_templates": landing_audit_command_templates,
        "next_open": next_owner_gate,
        "next_open_queue": next_open_queue,
        "next_open_queue_count": len(next_open_queue),
        "next_open_queue_selection_order": "review_after, worksheet_id",
    },
    "errors": errors,
    "strict_blockers": strict_blockers,
    "final_gate_command": final_gate_command,
    "next_actions_zh": next_actions,
}

if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(exit_code)

print("# Knowledge Hub Status")
print()
print("本命令只读汇总 Knowledge Hub 当前控制面状态，不创建、不修改、不提交、不提升任何文件。")
print()
print(f"- status: {status}")
print(f"- strict: {str(args.strict).lower()}")
print(f"- final_profile: {args.final_profile}")
print(f"- today: {today.isoformat()}")
print(f"- knowledge-check: {result['knowledge_check']['status']} (exit={knowledge_check['exit_code']}, errors={result['knowledge_check']['error_count']}, warnings={result['knowledge_check']['warning_count']})")
print(f"- registry items: {len(items)}")
print(f"- registered sources: {len(sources)}")
print(f"- review queues: pending={review_queues['summary']['total_pending_count']}, ai={review_queues['summary']['ai_generated_pending_count']}, external={review_queues['summary']['external_source_pending_count']}, active_or_promotion={review_queue_blocking_count}, product_blocking={review_queue_product_blocking_count}")
print(f"- product source inventory: {product_source_inventory_audit['status']} blockers={product_source_inventory_audit['blocker_count']}")
print(f"- owner gates: open={open_owner_gate_count}, resolved={owner_payload.get('resolved_count', 0)}, active_exposure={active_exposure_count}")
print(
    f"- owner-ready packages: {owner_ready_package_coverage or str(owner_ready_package_count) + '/' + str(owner_payload.get('row_count', 0))}, "
    f"missing={owner_ready_missing_count}, invalid={owner_ready_invalid_count}, duplicate={owner_ready_duplicate_count}"
)
if latest_source_coverage:
    print(f"- source coverage: `{latest_source_coverage}`")
print()
print("## Registry")
print()
for key, value in result["registry"]["by_status"].items():
    print(f"- status `{key}`: {value}")
print(f"- stale review_after: {len(stale_items)}")
print(f"- review_after command: `{review_after_command}`")
print(f"- review_after near-due command: `{review_after_near_due_command}`")
if stale_items:
    for item in stale_items[:10]:
        print(f"  - `{item['id']}` status={item['status']} review_after={item['review_after']} owner={item['owner']}")
print()
print("## Sources")
print()
print(f"- stale source review_after: {len(stale_sources)}")
print(f"- source review_after command: `{source_review_after_command}`")
print(f"- source check report command: `{source_check_report_command}`")
if stale_sources:
    for source in stale_sources[:10]:
        print(
            f"  - `{source['id']}` status={source['status']} "
            f"review_after={source['review_after']} owner={source['owner']}"
        )
print()
print("## Review Queues")
print()
print(f"- status: {review_queues['status']}")
print(f"- pending: {review_queues['summary']['total_pending_count']}")
print(f"- ai generated pending: {review_queues['summary']['ai_generated_pending_count']}")
print(f"- external source pending: {review_queues['summary']['external_source_pending_count']}")
print(f"- active or promotion blockers: {review_queue_blocking_count}")
print(f"- index plan command: `{review_queues['commands']['index_plan']}`")
for row in review_queues.get("ai_generated_pending", [])[:5]:
    print(f"- ai: `{row['id']}` priority={row['priority']} owner={row['owner']} review_after={row['review_after']}")
for row in review_queues.get("external_source_pending", [])[:5]:
    print(f"- external: `{row['id']}` priority={row['priority']} owner={row['owner']} review_after={row['review_after']}")
print()
print("## Owner Gates")
print()
print(f"- worksheets: {result['owner_gates']['worksheet_count']}")
print(f"- rows: {result['owner_gates']['row_count']}")
print(f"- open: {open_owner_gate_count}")
print(f"- resolved: {owner_payload.get('resolved_count', 0)}")
print(f"- active exposure: {active_exposure_count}")
print(f"- owner-ready packages: {owner_ready_package_coverage or str(owner_ready_package_count) + '/' + str(result['owner_gates']['row_count'])}")
print(f"- owner-ready missing: {owner_ready_missing_count}")
print(f"- owner-ready invalid: {owner_ready_invalid_count}")
print(f"- owner-ready duplicate: {owner_ready_duplicate_count}")
if summary_commands:
    print("- summary commands:")
    for command in summary_commands:
        print(f"  - `{command}`")
if owner_summary_commands:
    print("- owner summary commands:")
    for command in owner_summary_commands:
        print(f"  - `{command}`")
if forms_jsonl_commands:
    print("- forms-jsonl commands:")
    for command in forms_jsonl_commands:
        print(f"  - `{command}`")
if owner_forms_jsonl_commands:
    print("- owner forms-jsonl commands:")
    for command in owner_forms_jsonl_commands:
        print(f"  - `{command}`")
if owner_validate_forms_command_templates:
    print("- owner validate-forms command templates:")
    for command in owner_validate_forms_command_templates:
        print(f"  - `{command}`")
if owner_landing_plan_command_templates:
    print("- owner landing plan command templates:")
    for command in owner_landing_plan_command_templates:
        print(f"  - `{command}`")
if owner_landing_audit_command_templates:
    print("- owner landing audit command templates:")
    for command in owner_landing_audit_command_templates:
        print(f"  - `{command}`")
if validate_forms_command_templates:
    print("- validate-forms command templates:")
    for command in validate_forms_command_templates:
        print(f"  - `{command}`")
if landing_plan_command_templates:
    print("- landing plan command templates:")
    for command in landing_plan_command_templates:
        print(f"  - `{command}`")
if landing_audit_command_templates:
    print("- landing audit command templates:")
    for command in landing_audit_command_templates:
        print(f"  - `{command}`")
if next_owner_gate:
    print(f"- next open: `{next_owner_gate['worksheet_id']}` ({next_owner_gate['source_path']})")
    print(f"- next-open command: `{next_owner_gate['next_open_command']}`")
    print(f"- next-open forms-jsonl command: `{next_owner_gate['next_open_forms_jsonl_command']}`")
    print(f"- focus command: `{next_owner_gate['focus_command']}`")
    print(f"- focus forms-jsonl command: `{next_owner_gate['focus_forms_jsonl_command']}`")
    print(f"- focus validate-forms command template: `{next_owner_gate['focus_validate_forms_command_template']}`")
    print(f"- focus landing-plan command template: `{next_owner_gate['focus_landing_plan_command_template']}`")
    print(f"- focus landing-audit command template: `{next_owner_gate['focus_landing_audit_command_template']}`")
if next_open_queue:
    print(f"- next open queue: {len(next_open_queue)} item(s), order=`review_after, worksheet_id`")
    for row in next_open_queue:
        print(f"  - `{row['worksheet_id']}` ({row['source_path']}) owner=`{row['owner']}` ready=`{row['owner_ready_package_status']}`")
        print(f"    - focus: `{row['focus_command']}`")
        print(f"    - forms-jsonl: `{row['forms_jsonl_command']}`")
        print(f"    - evidence-readiness: `{row['evidence_readiness_command']}`")
print()
if strict_blockers:
    print("## Strict Blockers")
    print()
    for blocker in strict_blockers:
        print(f"- `{blocker['id']}` ({blocker['severity']}): {blocker['summary_zh']} count={blocker['count']}")
        for command in blocker.get("commands", []):
            print(f"  - `{command}`")
        for command in blocker.get("command_templates", []):
            print(f"  - template: `{command}`")
    print()
print("## 下一步")
print()
for action in next_actions:
    print(f"- {action}")
print(f"- 最终门禁命令：{final_gate_command}")
if errors:
    print()
    print("## Errors")
    print()
    for error in errors:
        print(f"- {error}")
print()
print("## 复核命令")
print()
print("```bash")
print("rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics")
print("rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json")
print("rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict")
print(final_gate_command)
print("```")

sys.exit(exit_code)
