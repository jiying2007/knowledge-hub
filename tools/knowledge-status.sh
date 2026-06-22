#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import collections
import datetime as dt
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
args = parser.parse_args(argv)

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
migrations = load_jsonl(root / "registry" / "migrations.jsonl")
sources = load_json(root / "registry" / "sources.json").get("sources", [])

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
        "owner": owner,
        "source_id": source_id,
        "open_count": len(owner_rows),
        "worksheet_ids": [str(row.get("id", "")) for row in owner_rows],
        "next_worksheet_id": str(next_owner_row.get("id", "")) if next_owner_row else "",
        "suggested_local_owner_decisions_path": local_path,
        "manual_owner_fields": required_fields,
        "recommended_sequence": [
            {"step": "1-review-summary", "command": summary},
            {"step": "2-check-evidence-readiness", "command": readiness},
            {"step": "3-export-forms", "command": forms, "output_path_hint": local_path},
            {"step": "4-validate-filled-forms", "command_template": validate, "replace_placeholder_with": local_path},
            {"step": "5-plan-manual-landing", "command_template": landing_plan, "replace_placeholder_with": local_path},
            {"step": "6-audit-manual-landing", "command_template": landing_audit, "replace_placeholder_with": local_path},
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
    registry_items = row.get("registry_items", []) if isinstance(row.get("registry_items", []), list) else []
    return {
        "worksheet_id": worksheet_id,
        "source_id": source_id,
        "source_path": str(row.get("source_path", "")),
        "owner": str(row.get("owner", "")),
        "owner_route": row.get("owner_route", {}),
        "review_after": str(row.get("review_after", "")),
        "owner_question_zh": str(row.get("owner_question_zh", "")),
        "owner_ready_package_status": "ready-package-present" if registry_items else "missing-owner-ready-package",
        "owner_ready_package_ids": [str(item.get("id", "")) for item in registry_items if isinstance(item, dict)],
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
    rows_by_owner = collections.defaultdict(list)
    for row in open_owner_rows:
        rows_by_owner[str(row.get("owner", "") or "<missing-owner>")].append(row)
    for owner, owner_rows in sorted(rows_by_owner.items()):
        source_ids = sorted({
            str(row.get("source_id", ""))
            for row in owner_rows
            if row.get("source_id")
        })
        source_id = source_ids[0] if len(source_ids) == 1 else ""
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
            "owner_route": owner_routes[0] if len(owner_routes) == 1 else {},
            "owner_routes": owner_routes,
            "row_count": len(owner_rows),
            "open_count": len(owner_rows),
            "worksheet_ids": [str(row.get("id", "")) for row in owner_rows],
            "source_paths": [str(row.get("source_path", "")) for row in owner_rows],
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
            "notes_zh": "status dashboard 只读 owner 分派摘要；用于跨会话恢复 owner 领取、表单导出、校验和 landing-plan 入口，不生成 owner decision，不关闭 gate。",
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

owner_gates_failed = owner_gates["exit_code"] != 0

if errors:
    status = "blocked"
elif knowledge_check["exit_code"] != 0 or owner_gates_failed or active_exposure_count:
    status = "needs-fix"
elif open_owner_gate_count:
    status = "needs-owner-review"
else:
    status = "ok"

exit_code = 1 if status in {"blocked", "needs-fix"} or (args.strict and status != "ok") else 0
if today_source == "system-date":
    final_gate_command = "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json"
else:
    final_gate_command = f"rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --as-of {today.isoformat()} --json"
review_after_command = "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date"
source_review_after_command = "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source"
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
        "migration_strategy": str(source.get("migration_strategy", "")),
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
            "需要按责任人分派 owner gate 时，先读取 JSON 中的 `owner_gates.owner_dispatch[]`，或运行 owner 过滤总览，例如："
            f"{owner_summary_commands[0]}。"
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
            "责任人表单校验通过后，按 owner 范围审计 worksheet、registry、migration 和 index 人工落点："
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
    "notes_zh": "owner gate 数量、owner-ready 覆盖和 active exposure 均来自本 status 输出的 owner_gates；本结构只解释 blocker 来源，不生成 owner decision，不关闭 gate。",
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

result = {
    "schema_version": 1,
    "root": str(root),
    "read_only": True,
    "strict": args.strict,
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
        "boundary_health": check_payload.get("boundary_health", {}),
    },
    "migrations": {
        "record_count": len(migrations),
        "by_status": count_by(migrations, "status"),
    },
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
print(f"- today: {today.isoformat()}")
print(f"- knowledge-check: {result['knowledge_check']['status']} (exit={knowledge_check['exit_code']}, errors={result['knowledge_check']['error_count']}, warnings={result['knowledge_check']['warning_count']})")
print(f"- registry items: {len(items)}")
print(f"- registered sources: {len(sources)}")
print(f"- migrations: {len(migrations)}")
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
if stale_items:
    for item in stale_items[:10]:
        print(f"  - `{item['id']}` status={item['status']} review_after={item['review_after']} owner={item['owner']}")
print()
print("## Sources")
print()
print(f"- stale source review_after: {len(stale_sources)}")
print(f"- source review_after command: `{source_review_after_command}`")
if stale_sources:
    for source in stale_sources[:10]:
        print(
            f"  - `{source['id']}` status={source['status']} "
            f"review_after={source['review_after']} owner={source['owner']}"
        )
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
PY
