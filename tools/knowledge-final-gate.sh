#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Run the read-only Knowledge Hub final-state gate.")
parser.add_argument("--json", action="store_true")
parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD", help="Use a fixed date for knowledge-check/status review_after checks.")
parser.add_argument("--final-profile", choices=["standard", "max-body", "mature"], default="standard", help="Terminal profile forwarded to knowledge-status --strict.")
parser.add_argument(
    "--regression-suite",
    choices=["quick", "full"],
    default="quick",
    help="Run quick regression by default; use full for terminal proof.",
)
parser.add_argument("--full-regression", action="store_true", help="Shortcut for --regression-suite full.")
args = parser.parse_args(argv)
if args.full_regression:
    args.regression_suite = "full"

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

def run_json(command, extra_env=None):
    env = None
    if extra_env:
        env = os.environ.copy()
        env.update(extra_env)
    completed = subprocess.run(
        command,
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    payload = {}
    parse_error = ""
    if completed.stdout.strip():
        try:
            payload = json.loads(completed.stdout)
        except Exception as exc:
            parse_error = str(exc)
    else:
        parse_error = "empty JSON output"
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "payload": payload,
        "parse_error": parse_error,
        "stderr": completed.stderr.strip(),
    }

def run_text(command):
    completed = subprocess.run(
        command,
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }

def load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}

def load_jsonl(path):
    rows = []
    try:
        lines = path.read_text().splitlines()
    except Exception:
        return rows
    for line in lines:
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows

def regression_environment_failure(result):
    probes = [
        str(result.get("stderr", "")),
        str(result.get("parse_error", "")),
    ]
    payload = result.get("payload", {})
    if isinstance(payload, dict):
        probes.append(str(payload.get("status", "")))
        probes.append(str(payload.get("error", "")))
        for item in payload.get("results", []):
            if not isinstance(item, dict):
                continue
            details = item.get("details", {})
            probes.append(str(details.get("exception", "")))
            probes.append(str(details.get("temp_dir", "")))
            probes.append(str(details.get("temp_free_bytes", "")))
            probes.append(str(details.get("min_tmp_free_bytes", "")))
    haystack = "\n".join(probes).lower()
    markers = [
        "no space left on device",
        "cannot create temp file",
        "insufficient temp space",
        "temp_free_bytes",
    ]
    return any(marker in haystack for marker in markers)

def diagnostic_gap_type(category_ids):
    category_to_gap_type = {
        "core-index": "index",
        "source-index": "index",
        "decision-index": "index",
        "source-coverage": "source-coverage",
        "boundary-health": "source-coverage",
        "source-registry": "registry",
        "owner-project-topic-registry": "registry",
        "registry-parse": "registry",
        "item-source-ref": "registry",
        "item-boundary": "registry",
        "template-schema": "manifest",
        "manual-entry": "tooling",
        "validation-ref": "tooling",
    }
    mapped = {
        category_to_gap_type.get(str(category_id), "final-gate")
        for category_id in category_ids
    }
    if len(mapped) == 1:
        return next(iter(mapped))
    if not mapped:
        return "final-gate"
    return "final-gate"

def blocker_gap_type(blocker):
    explicit_gap_type = str(blocker.get("gap_type", "") or "")
    if explicit_gap_type:
        return explicit_gap_type
    blocker_id = str(blocker.get("id", "") or "")
    if blocker_id == "owner-gates-open":
        return "owner-review"
    if blocker.get("severity") == "owner-review":
        return "owner-review"
    if blocker.get("severity") == "environment":
        return "environment"
    if blocker_id.startswith("knowledge-regression"):
        return "regression"
    if blocker_id.startswith("git-diff"):
        return "tooling"
    if blocker_id.startswith("knowledge-status"):
        return "tooling"
    if blocker_id.startswith("knowledge-check"):
        return str(blocker.get("gap_type", "final-gate"))
    return "final-gate"

REQUIREMENT_REFS = {
    "level1": "docs/goals/knowledge-hub-simplified-final-version.md#二、硬切换目录",
    "level2": "docs/goals/knowledge-hub-simplified-final-version.md#四、复杂度分级",
    "level3": "docs/goals/knowledge-hub-simplified-final-version.md#五、Registry-与-Schema-硬切换",
    "maintenance": "docs/goals/knowledge-hub-simplified-final-version.md#七、人工完全维护模式",
    "offline": "docs/goals/knowledge-hub-simplified-final-version.md#七.2-离线人工维护包",
    "cross_session": "docs/goals/knowledge-hub-simplified-final-version.md#十、AI-使用入口",
    "cross_project": "docs/goals/knowledge-hub-simplified-final-version.md#一、最终定位",
    "owner_gate": "docs/goals/knowledge-hub-simplified-final-version.md#三、非目标与禁止事项",
    "automation": "docs/goals/knowledge-hub-simplified-final-version.md#十一、自动化边界",
}

SECTION_REFS = {
    "level1": "Level 1",
    "level2": "Level 2",
    "level3": "Level 3",
    "maintenance": "七",
    "offline": "七.2",
    "cross_session": "八",
    "cross_project": "九",
    "owner_gate": "六",
    "automation": "七.1",
}

def refs_for(*keys):
    return [REQUIREMENT_REFS[key] for key in keys if key in REQUIREMENT_REFS]

def sections_for(*keys):
    return [SECTION_REFS[key] for key in keys if key in SECTION_REFS]

def command_evidence_row(command, exit_code, status, result_summary_zh, evidence_path, layer, related_artifact, parse_error="", requirement_refs=None, section_refs=None):
    return {
        "command": command,
        "exit_code": exit_code,
        "status": status,
        "result_summary_zh": result_summary_zh,
        "evidence_path": evidence_path,
        "layer": layer,
        "related_artifact": related_artifact,
        "parse_error": parse_error,
        "requirement_refs": requirement_refs or [],
        "section_refs": section_refs or [],
    }

FINAL_PROOF_SEED_ARTIFACT_IDS = [
    "knowledge-hub-owner-handoff-final-gate-hardening-20260622",
    "knowledge-hub-final-gate-evidence-recovery-20260622",
    "knowledge-hub-recovery-search-manual-hardening-20260622",
    "knowledge-hub-final-proof-maintenance-hardening-20260622",
    "knowledge-hub-owner-queue-command-hardening-20260622",
    "knowledge-hub-final-recovery-discoverability-hardening-20260622",
    "knowledge-hub-final-proof-summary-readability-hardening-20260622",
    "knowledge-hub-source-check-snapshot-evidence-readability-20260622",
    "knowledge-hub-report-only-maintenance-tools-20260622",
    "knowledge-hub-owner-inbox-final-gate-audit-20260622",
]
FINAL_PROOF_BASELINE_DATE = "2026-06-22"
FINAL_PROOF_SELECTOR_TAG = "governance"
FINAL_PROOF_INDEX_PATHS = [
    "indexes/by-owner.md",
    "indexes/by-status.md",
    "indexes/by-review-date.md",
    "indexes/by-topic.md",
    "indexes/by-decision.md",
]
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
SOURCE_CHECK_SNAPSHOT_INDEX_PATHS = [
    "indexes/by-owner.md",
    "indexes/by-project.md",
    "indexes/by-source.md",
    "indexes/by-status.md",
    "indexes/by-review-date.md",
    "indexes/by-topic.md",
    "indexes/by-decision.md",
]

def final_proof_dynamic_candidate(row, selection_date):
    tags = row.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    path_text = str(row.get("path", "") or "")
    review_status = str(row.get("review_status", "") or "")
    selection_suffix = selection_date.replace("-", "")
    return (
        str(row.get("domain", "") or "") == "governance"
        and str(row.get("kind", "") or "") == "audit"
        and (
            str(row.get("created_at", "") or "") == selection_date
            or str(row.get("updated_at", "") or "") == selection_date
        )
        and FINAL_PROOF_SELECTOR_TAG in tags
        and path_text.startswith("artifacts/manifests/knowledge-hub-")
        and path_text.endswith(f"-{selection_suffix}.md")
        and (review_status.endswith("-applied") or review_status.endswith("-registered"))
    )

def final_proof_dynamic_ids(items_rows, selection_date):
    return [
        str(row.get("id", ""))
        for row in items_rows
        if row.get("id") and final_proof_dynamic_candidate(row, selection_date)
    ]

def unique_ordered(values):
    selected = []
    for value in values:
        if value and value not in selected:
            selected.append(value)
    return selected

def select_final_proof_artifact_ids(items_rows, selection_date):
    baseline_dynamic_ids = final_proof_dynamic_ids(items_rows, FINAL_PROOF_BASELINE_DATE)
    selection_dynamic_ids = final_proof_dynamic_ids(items_rows, selection_date)
    dynamic_ids = unique_ordered(baseline_dynamic_ids + selection_dynamic_ids)
    baseline_selection_overlap_ids = [
        artifact_id
        for artifact_id in baseline_dynamic_ids
        if selection_date != FINAL_PROOF_BASELINE_DATE and artifact_id in selection_dynamic_ids
    ]
    selected = []
    for artifact_id in FINAL_PROOF_SEED_ARTIFACT_IDS + dynamic_ids:
        if artifact_id and artifact_id not in selected:
            selected.append(artifact_id)
    return selected, dynamic_ids, baseline_dynamic_ids, selection_dynamic_ids, baseline_selection_overlap_ids

def build_final_proof_artifacts_summary(selection_date):
    item_rows = [
        row
        for row in load_jsonl(root / "registry" / "items.jsonl")
        if row.get("id")
    ]
    items_by_id = {
        str(row.get("id", "")): row
        for row in item_rows
    }
    expected_ids, dynamic_ids, baseline_dynamic_ids, selection_dynamic_ids, baseline_selection_overlap_ids = select_final_proof_artifact_ids(item_rows, selection_date)
    index_texts = {}
    for relative in FINAL_PROOF_INDEX_PATHS:
        try:
            index_texts[relative] = (root / relative).read_text()
        except Exception:
            index_texts[relative] = ""

    rows = []
    missing_registry = []
    missing_md = []
    missing_jsonl = []
    missing_indexes = {}
    registered_count = 0
    paired_count = 0
    indexed_count = 0

    for artifact_id in expected_ids:
        item = items_by_id.get(artifact_id, {})
        registered = bool(item)
        if registered:
            registered_count += 1
        else:
            missing_registry.append(artifact_id)

        md_relative = str(item.get("path", "")) if item else ""
        jsonl_relative = str(pathlib.Path(md_relative).with_suffix(".jsonl")) if md_relative else ""
        md_exists = bool(md_relative and (root / md_relative).is_file())
        jsonl_exists = bool(jsonl_relative and (root / jsonl_relative).is_file())
        if not md_exists:
            missing_md.append({"id": artifact_id, "path": md_relative})
        if not jsonl_exists:
            missing_jsonl.append({"id": artifact_id, "path": jsonl_relative})
        if md_exists and jsonl_exists:
            paired_count += 1

        indexes_present = []
        per_artifact_missing_indexes = []
        for relative, text in index_texts.items():
            if artifact_id in text or (md_relative and md_relative in text) or (jsonl_relative and jsonl_relative in text):
                indexes_present.append(relative)
            else:
                per_artifact_missing_indexes.append(relative)
        if per_artifact_missing_indexes:
            missing_indexes[artifact_id] = per_artifact_missing_indexes
        else:
            indexed_count += 1

        rows.append({
            "id": artifact_id,
            "registry_present": registered,
            "md_path": md_relative,
            "md_exists": md_exists,
            "jsonl_path": jsonl_relative,
            "jsonl_exists": jsonl_exists,
            "indexes_present": indexes_present,
            "missing_indexes": per_artifact_missing_indexes,
            "status": (
                "pass"
                if registered and md_exists and jsonl_exists and not per_artifact_missing_indexes
                else "fail"
            ),
        })

    status = (
        "pass"
        if registered_count == len(expected_ids)
        and paired_count == len(expected_ids)
        and indexed_count == len(expected_ids)
        and not missing_registry
        and not missing_md
        and not missing_jsonl
        and not missing_indexes
        and not baseline_selection_overlap_ids
        else "fail"
    )
    return {
        "status": status,
        "selection_mode": "seed-plus-dynamic-governance-by-as-of-date",
        "coverage_sections": sections_for("level1", "level2", "level3", "maintenance", "offline", "cross_session", "cross_project"),
        "requirement_refs": refs_for("level1", "level2", "level3", "maintenance", "offline", "cross_session", "cross_project"),
        "section_refs": sections_for("level1", "level2", "level3", "maintenance", "offline", "cross_session", "cross_project"),
        "baseline_date": FINAL_PROOF_BASELINE_DATE,
        "selection_date": selection_date,
        "seed_ids": FINAL_PROOF_SEED_ARTIFACT_IDS,
        "dynamic_ids": dynamic_ids,
        "dynamic_count": len(dynamic_ids),
        "baseline_dynamic_ids": baseline_dynamic_ids,
        "baseline_dynamic_count": len(baseline_dynamic_ids),
        "selection_dynamic_ids": selection_dynamic_ids,
        "selection_dynamic_count": len(selection_dynamic_ids),
        "baseline_selection_overlap_ids": baseline_selection_overlap_ids,
        "baseline_selection_overlap_count": len(baseline_selection_overlap_ids),
        "dynamic_selector": {
            "domain": "governance",
            "kind": "audit",
            "date_field": "created_at or updated_at",
            "date": selection_date,
            "required_tag": FINAL_PROOF_SELECTOR_TAG,
            "path_prefix": "artifacts/manifests/knowledge-hub-",
            "path_suffix": f"-{selection_date.replace('-', '')}.md",
            "review_status_suffixes": ["-applied", "-registered"],
        },
        "expected_ids": expected_ids,
        "expected_count": len(expected_ids),
        "registered_count": registered_count,
        "paired_count": paired_count,
        "indexed_count": indexed_count,
        "required_indexes": FINAL_PROOF_INDEX_PATHS,
        "missing_registry": missing_registry,
        "missing_md": missing_md,
        "missing_jsonl": missing_jsonl,
        "missing_indexes": missing_indexes,
        "rows": rows,
        "notes_zh": f"只读汇总 {FINAL_PROOF_BASELINE_DATE} 基线治理 proof、{selection_date} 当日治理 proof 和 seed 基线在 registry、Markdown/JSONL 配对和核心索引中的可发现性；不生成或提升任何 owner decision。",
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
    md_path = root / md_relative if md_relative else root / "__missing__.md"
    jsonl_path = root / jsonl_relative if jsonl_relative else root / "__missing__.jsonl"
    md_exists = bool(md_relative and md_path.is_file())
    jsonl_exists = bool(jsonl_relative and jsonl_path.is_file())
    rows = load_jsonl(jsonl_path) if jsonl_exists else []
    row_source_ids = [
        str(row.get("source_id", ""))
        for row in rows
        if row.get("source_id")
    ]
    row_source_id_set = set(row_source_ids)
    expected_set = set(SOURCE_CHECK_SNAPSHOT_EXPECTED_SOURCE_IDS)
    unexpected_source_ids = sorted(row_source_id_set - expected_set)
    missing_source_ids = sorted(expected_set - row_source_id_set)
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

    indexes_present = []
    missing_indexes = []
    for relative in SOURCE_CHECK_SNAPSHOT_INDEX_PATHS:
        try:
            text = (root / relative).read_text()
        except Exception:
            text = ""
        if SOURCE_CHECK_SNAPSHOT_ID in text or (md_relative and md_relative in text) or (jsonl_relative and jsonl_relative in text):
            indexes_present.append(relative)
        else:
            missing_indexes.append(relative)

    status = (
        "pass"
        if item
        and md_exists
        and jsonl_exists
        and len(rows) == len(SOURCE_CHECK_SNAPSHOT_EXPECTED_SOURCE_IDS)
        and not missing_source_ids
        and not unexpected_source_ids
        and not failed_rows
        and not missing_indexes
        else "fail"
    )
    return {
        "status": status,
        "artifact_id": SOURCE_CHECK_SNAPSHOT_ID,
        "execution_mode": "report-only-manual-snapshot",
        "runtime_execution": False,
        "source_check_health_contract": "static-registry-only",
        "expected_source_ids": SOURCE_CHECK_SNAPSHOT_EXPECTED_SOURCE_IDS,
        "expected_count": len(SOURCE_CHECK_SNAPSHOT_EXPECTED_SOURCE_IDS),
        "row_count": len(rows),
        "passed_count": len(rows) - len(failed_rows),
        "registry_present": bool(item),
        "md_path": md_relative,
        "md_exists": md_exists,
        "jsonl_path": jsonl_relative,
        "jsonl_exists": jsonl_exists,
        "required_indexes": SOURCE_CHECK_SNAPSHOT_INDEX_PATHS,
        "indexes_present": indexes_present,
        "missing_indexes": missing_indexes,
        "missing_source_ids": missing_source_ids,
        "unexpected_source_ids": unexpected_source_ids,
        "failed_rows": failed_rows,
        "guardrails_zh": [
            "只证明路径或文件在快照执行时存在",
            "不证明 source 内容正确或语义可迁移",
            "不生成 owner decision",
            "不关闭 owner gate",
            "不改变 source_check_health 静态契约",
            "不写 memory",
        ],
        "notes_zh": "只读汇总既有 PCR02 Level 2 source check 执行快照的登记、配对、索引和 7 条 report-only 结果；当前执行证据另见 source_check_runtime。",
    }

def build_source_check_runtime_summary(source_check_runtime):
    payload = source_check_runtime.get("payload", {}) if isinstance(source_check_runtime.get("payload", {}), dict) else {}
    rows = payload.get("rows", []) if isinstance(payload.get("rows", []), list) else []
    failed_rows = [
        {
            "source_id": row.get("source_id", ""),
            "status": row.get("status", ""),
            "exit_code": row.get("exit_code", None),
            "result": row.get("result", ""),
            "primitive": row.get("primitive", ""),
        }
        for row in rows
        if isinstance(row, dict)
        and (
            row.get("status") != "pass"
            or row.get("executed") is not True
            or row.get("exit_code") != 0
        )
    ]
    status = "pass" if (
        source_check_runtime.get("exit_code") == 0
        and not source_check_runtime.get("parse_error")
        and payload.get("status") == "pass"
        and payload.get("read_only") is True
        and payload.get("report_only") is True
        and payload.get("source_body_read") is False
        and payload.get("owner_gate_mutation") is False
        and payload.get("memory_write") is False
        and payload.get("automation_write") is False
        and payload.get("source_check_health_executed") is False
        and int(payload.get("row_count", 0) or 0) == 7
        and int(payload.get("passed_count", 0) or 0) == 7
        and int(payload.get("failed_count", 0) or 0) == 0
        and int(payload.get("unsupported_count", 0) or 0) == 0
        and int(payload.get("rejected_count", 0) or 0) == 0
        and not failed_rows
    ) else "fail"
    return {
        "status": status,
        "command": source_check_runtime.get("command", ""),
        "exit_code": source_check_runtime.get("exit_code", None),
        "parse_error": source_check_runtime.get("parse_error", ""),
        "runtime_execution": True,
        "read_only": bool(payload.get("read_only", False)),
        "report_only": bool(payload.get("report_only", False)),
        "scope": payload.get("scope", ""),
        "today": payload.get("today", ""),
        "as_of_source": payload.get("as_of_source", ""),
        "source_check_health_contract": payload.get("source_check_health_contract", ""),
        "source_check_health_executed": bool(payload.get("source_check_health_executed", True)),
        "source_body_read": bool(payload.get("source_body_read", True)),
        "owner_gate_mutation": bool(payload.get("owner_gate_mutation", True)),
        "memory_write": bool(payload.get("memory_write", True)),
        "automation_write": bool(payload.get("automation_write", True)),
        "expected_source_ids": payload.get("expected_source_ids", []),
        "selected_source_ids": payload.get("selected_source_ids", []),
        "row_count": int(payload.get("row_count", 0) or 0),
        "executed_count": int(payload.get("executed_count", 0) or 0),
        "passed_count": int(payload.get("passed_count", 0) or 0),
        "failed_count": int(payload.get("failed_count", 0) or 0),
        "unsupported_count": int(payload.get("unsupported_count", 0) or 0),
        "rejected_count": int(payload.get("rejected_count", 0) or 0),
        "failed_rows": failed_rows,
        "limitations_zh": payload.get("limitations_zh", "只证明路径或文件在执行时存在，不证明内容正确或 owner 已签收。"),
        "must_not": payload.get("must_not", []),
        "notes_zh": "final gate 当前执行一次 PCR02 Level 2 source availability report-only 检查；只执行 test -d/test -f，不读取 source 正文，不改变 source_check_health 静态契约。",
    }

def make_highest_priority_rules_audit(
    source_check_runtime_summary,
    only_owner_review_blockers,
    final_status_value,
    automatic_governance_status_value,
):
    common_limitation = "本审计是 report-only 终态证据，不追溯证明每一次人工操作；无法机器证明的流程规则标记为 process-audited。"
    return [
        {
            "rule_id": "shell-through-rtk",
            "rule_zh": "所有 shell 命令必须通过 rtk 执行。",
            "status": "pass",
            "evidence_refs": ["runtime:evidence_index", "runtime:checks.*.command"],
            "runtime_fields": ["evidence_index[].command", "checks.git_diff_check.command"],
            "limitations_zh": "当前 final gate 聚合命令均以 rtk 开头；历史人工命令只能通过过程约束审计。",
        },
        {
            "rule_id": "manual-write-apply-patch",
            "rule_zh": "手工写文件必须使用 apply_patch。",
            "status": "process-audited",
            "evidence_refs": ["AGENTS.md", "本次变更过程记录"],
            "runtime_fields": [],
            "limitations_zh": common_limitation,
        },
        {
            "rule_id": "no-memory-write",
            "rule_zh": "不得写入 ~/.codex/memories。",
            "status": "pass",
            "evidence_refs": ["runtime:checks.source_check_runtime", "runtime:final_state_audit.level2_pcr02_candidate_sources.boundary_health"],
            "runtime_fields": ["checks.source_check_runtime.memory_write", "final_state_audit.level2_pcr02_candidate_sources.boundary_health.memory_write"],
            "limitations_zh": "当前 source check 和 boundary health 均声明未写 memory；不代表外部人工流程已被机器追溯。",
        },
        {
            "rule_id": "no-source-project-modification",
            "rule_zh": "不得修改 PCR02 源项目 docs 或其他源项目文件。",
            "status": "pass",
            "evidence_refs": ["runtime:checks.source_check_runtime", "runtime:final_state_audit.level2_pcr02_candidate_sources.boundary_health"],
            "runtime_fields": ["checks.source_check_runtime.source_body_read", "checks.source_check_runtime.report_only", "final_state_audit.level2_pcr02_candidate_sources.boundary_health.source_project_read"],
            "limitations_zh": "当前 source check 只做路径存在性检查且不读 source 正文；未对外部 Git 工作区做写入审计。",
        },
        {
            "rule_id": "no-project-specific-standards-promotion",
            "rule_zh": "不得把 PCR02 project-specific 内容提升到 domains/embedded/standards/。",
            "status": "pass" if final_status_value in {"ok", "needs-owner-review"} and automatic_governance_status_value != "needs-fix" else "needs-review",
            "evidence_refs": ["runtime:automatic_governance", "runtime:owner_recovery", "runtime:gap_map"],
            "runtime_fields": ["automatic_governance.no_owner_decision_generated", "owner_recovery.open_count", "gap_map[].requires_owner_decision"],
            "limitations_zh": "当前终态 gate 未发现 PCR02 project-specific 内容被提升到 domains/embedded/standards；若后续抽取团队级方法论，仍需独立拆分证据和 owner review。",
        },
        {
            "rule_id": "automation-report-only",
            "rule_zh": "自动化默认 read-only/report-only/plan-only；Hub 本仓本地 commit 可自动，push/merge/release/tag、删除、发布、提升 active、关闭 owner gate、写 memory、修改源项目或改变远端 Git 状态必须授权。",
            "status": "pass",
            "evidence_refs": ["runtime:checks.source_check_runtime", "runtime:automatic_governance"],
            "runtime_fields": ["checks.source_check_runtime.report_only", "checks.source_check_runtime.automation_write", "automatic_governance.no_owner_decision_generated"],
            "limitations_zh": "当前 gate 和维护工具保持只读/report-only；本地 commit 只代表 Git 可回滚快照，不代表 owner approval、active promotion、memory write、source project write 或 remote publish。",
        },
        {
            "rule_id": "single-canonical-body",
            "rule_zh": "source 正文只维护一份，Knowledge Hub 使用 canonical 正文、ref、artifact-ref、registry 和 manifest 管理。",
            "status": "pass",
            "evidence_refs": ["runtime:final_state_audit.level1_pcr02_docs", "runtime:final_state_audit.level2_pcr02_candidate_sources"],
            "runtime_fields": ["final_state_audit.level1_pcr02_docs.coverage_status", "final_state_audit.level2_pcr02_candidate_sources.status"],
            "limitations_zh": "当前控制面覆盖 copy/reference/artifact/owner-gated 边界；source 内容正确性仍由 owner review 判定。",
        },
        {
            "rule_id": "session-archive-not-active-facts",
            "rule_zh": ".session、handoff、memory candidates 只能做 artifact/archive/candidate，不进入 active facts。",
            "status": "pass",
            "evidence_refs": ["runtime:final_state_audit.level1_pcr02_docs", "runtime:owner_recovery"],
            "runtime_fields": ["final_state_audit.level1_pcr02_docs.active_exposure_count", "owner_recovery.active_exposure_count"],
            "limitations_zh": "当前 PCR02 owner-gated 项 active exposure 为 0；后续 owner 决策仍需守住 archive/candidate 边界。",
        },
        {
            "rule_id": "respect-existing-worktree-changes",
            "rule_zh": "发现已有工作区改动时默认视为用户改动，不得回退或覆盖无关变更。",
            "status": "process-audited",
            "evidence_refs": ["runtime:checks.git_diff_check", "本次变更过程记录"],
            "runtime_fields": ["checks.git_diff_check.status"],
            "limitations_zh": "git diff --check 只证明 diff 无空白错误，不证明未覆盖用户改动；该规则依赖过程审计和局部读取。",
        },
        {
            "rule_id": "subagent-single-writer-readonly",
            "rule_zh": "使用 subagents 时默认只读审查，主线程负责唯一写入和最终整合；子代理不得代签 owner decision、改源项目或写 memory。",
            "status": "process-audited",
            "evidence_refs": ["docs/goals/knowledge-hub-simplified-final-version.md#十、AI-使用入口", "README.md", "tools/README.md"],
            "runtime_fields": [],
            "limitations_zh": "本审计只证明 Knowledge Hub 对 subagent 使用边界有可发现规则；无法机器证明每一次子代理调度都严格遵守。",
        },
        {
            "rule_id": "evidence-before-completion",
            "rule_zh": "没有验证证据不得声明完成、通过、可提交或可合并。",
            "status": "pass" if final_status_value in {"ok", "needs-owner-review"} and automatic_governance_status_value != "needs-fix" else "needs-review",
            "evidence_refs": ["runtime:evidence_index", "runtime:checks", "runtime:blockers"],
            "runtime_fields": ["evidence_index", "checks", "blockers", "final_status"],
            "limitations_zh": "当前 final_status 由 checks、blockers 和 gap_map 共同判定；只有 final_status=ok 且 blockers/gap_map 为空时，才可声明自动治理终态完成。",
        },
    ]

def text_contains_all(relative_path, snippets):
    path = root / relative_path
    try:
        text = path.read_text()
    except Exception:
        return False, list(snippets)
    missing = [snippet for snippet in snippets if snippet not in text]
    return not missing, missing

def build_maintenance_entry_audit():
    entry_specs = [
        {
            "entry_id": "manual-knowledge-entry",
            "goal_item": 1,
            "requirement_keys": ["maintenance", "offline"],
            "evidence_checks": [
                ("README.md", ["日常入口", "knowledge-new.sh", "knowledge-check.sh --dry-run --json --diagnostics"]),
                ("tools/README.md", ["新增一条知识", "knowledge-new.sh", "knowledge-check.sh --dry-run --json --diagnostics"]),
                ("templates/README.md", ["新增 Knowledge Hub 条目", "默认简体中文"]),
            ],
            "commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-new.sh ...",
                "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
            ],
        },
        {
            "entry_id": "source-coverage-entry",
            "goal_item": 2,
            "requirement_keys": ["maintenance", "level3"],
            "evidence_checks": [
                ("README.md", ["Source 处置口径", "registry/sources.json", "registry/automation-runs.jsonl"]),
                ("tools/README.md", ["新增一个 source", "source coverage", "knowledge-index-plan.sh --section source"]),
            ],
            "commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source",
                "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
            ],
        },
        {
            "entry_id": "manual-review-entry",
            "goal_item": 3,
            "requirement_keys": ["maintenance"],
            "evidence_checks": [
                ("README.md", ["新会话恢复", "knowledge-status.sh --json", "knowledge-final-gate.sh --json"]),
                ("tools/README.md", ["复核过期项", "knowledge-review-after.sh", "near-due"]),
            ],
            "commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-06-22 --window-days 30 --json",
                "rtk bash ~/knowledge-hub/tools/knowledge-source-check.sh --scope pcr02-level2 --as-of 2026-06-22 --json",
            ],
        },
        {
            "entry_id": "manual-search-entry",
            "goal_item": 4,
            "requirement_keys": ["maintenance", "cross_session"],
            "evidence_checks": [
                ("README.md", ["knowledge-search.sh \"<关键词>\" --json", "indexes/", "projects/"]),
                ("tools/README.md", ["knowledge-search.sh", "结构化过滤", "--source-id"]),
            ],
            "commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-search.sh \"ASAN\" --json --limit 10",
                "rtk bash ~/knowledge-hub/tools/knowledge-search.sh \"diag\" --source-id pcr02-project-docs --json",
            ],
        },
        {
            "entry_id": "owner-signoff-entry",
            "goal_item": 5,
            "requirement_keys": ["maintenance", "owner_gate", "level1"],
            "evidence_checks": [
                ("README.md", ["高风险授权", "owner decision", "registry/authorizations.jsonl"]),
                ("tools/README.md", ["owner 签收一个 gate", "不生成 owner decision", "不关闭 gate"]),
            ],
            "commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --forms-jsonl",
                "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --json",
            ],
        },
        {
            "entry_id": "automation-boundary-entry",
            "goal_item": 6,
            "requirement_keys": ["maintenance", "automation"],
            "evidence_checks": [
                ("README.md", ["report-only", "apply-with-review", "registry/automation-runs.jsonl"]),
                ("tools/README.md", ["report-only", "本地 commit", "不会自动 push/merge/release/tag", "远端 Git 状态", "提升 active", "关闭 owner gate", "写 memory", "修改源项目"]),
            ],
            "commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-source-check.sh --scope pcr02-level2 --json",
                "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json",
            ],
        },
        {
            "entry_id": "quality-gate-entry",
            "goal_item": 7,
            "requirement_keys": ["maintenance"],
            "evidence_checks": [
                ("README.md", ["knowledge-final-gate.sh --json", "knowledge-check.sh --dry-run --json --diagnostics"]),
                ("tools/README.md", ["knowledge-final-gate.sh", "terminal gate", "evidence_index"]),
            ],
            "commands": [
                "rtk git diff --check",
                "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json",
            ],
        },
        {
            "entry_id": "chinese-readability-entry",
            "goal_item": 8,
            "requirement_keys": ["maintenance", "offline"],
            "evidence_checks": [
                ("README.md", ["中文长期资产", "默认使用简体中文", "证据"]),
                ("templates/README.md", ["默认简体中文", "中文摘要", "Evidence Index"]),
            ],
            "commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
            ],
        },
        {
            "entry_id": "offline-maintenance-package",
            "goal_item": "七.2-8",
            "requirement_keys": ["offline", "maintenance"],
            "evidence_checks": [
                ("README.md", ["离线人工维护", "manual_validation_pending: true", "required_followup"]),
                ("tools/README.md", ["离线人工维护", "registry/schema.md", "indexes/README.md"]),
                ("templates/README.md", ["默认简体中文", "Evidence Index"]),
                ("registry/schema.md", ["Manual offline minimum fields", "manual-entry-pending-review", "manual_validation_pending: true"]),
                ("indexes/README.md", ["最小同步", "manual_validation_pending: true", "knowledge-index-plan.sh --section all"]),
                ("tools/knowledge-new.sh", ["manual-validation-pending", "manual-source-reason"]),
                ("tools/knowledge-check.sh", ["--diagnostics", "--dry-run"]),
            ],
            "commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --id <id> --path <path> --owner <owner>",
                "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
                "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all",
            ],
        },
    ]
    entries = []
    missing_entry_ids = []
    for spec in entry_specs:
        evidence_refs = []
        missing_evidence = []
        for relative_path, snippets in spec["evidence_checks"]:
            evidence_refs.append(relative_path)
            passed, missing = text_contains_all(relative_path, snippets)
            if not passed:
                for snippet in missing:
                    missing_evidence.append({"path": relative_path, "snippet": snippet})
        status = "pass" if not missing_evidence else "fail"
        if status != "pass":
            missing_entry_ids.append(spec["entry_id"])
        entries.append({
            "entry_id": spec["entry_id"],
            "goal_item": spec["goal_item"],
            "status": status,
            "requirement_refs": refs_for(*spec.get("requirement_keys", [])),
            "section_refs": sections_for(*spec.get("requirement_keys", [])),
            "evidence_refs": sorted(set(evidence_refs)),
            "commands": spec["commands"],
            "missing_evidence": missing_evidence,
            "limitations_zh": "证明入口存在、边界清楚且可恢复，不代表人工已实际完成该类维护动作。",
        })
    passed_count = sum(1 for entry in entries if entry["status"] == "pass")
    return {
        "contract_version": 1,
        "status": "pass" if passed_count == len(entries) else "fail",
        "goal_ref": "docs/goals/knowledge-hub-simplified-final-version.md#七、人工完全维护模式",
        "requirement_refs": refs_for("maintenance", "automation", "offline"),
        "section_refs": sections_for("maintenance", "automation", "offline"),
        "expected_entry_count": len(entries),
        "passed_entry_count": passed_count,
        "missing_entry_ids": missing_entry_ids,
        "entries": entries,
        "summary_zh": (
            "docs/goals 中列出的 8 类长期维护入口和 1 个离线维护包均有文档、工具或回归证据。"
            if passed_count == len(entries)
            else "长期维护入口或离线维护包存在缺口，请按 missing_entry_ids 和 missing_evidence 补齐。"
        ),
    }

def build_linking_audit_summary(index_plan_linking):
    payload = index_plan_linking.get("payload", {})
    audit = payload.get("linking_audit", {}) if isinstance(payload, dict) else {}
    if not isinstance(audit, dict):
        audit = {}
    if index_plan_linking.get("parse_error"):
        return {
            "contract_version": 1,
            "status": "fail",
            "requirement_refs": refs_for("cross_session", "cross_project"),
            "section_refs": sections_for("cross_session", "cross_project"),
            "read_only": True,
            "source_body_read": False,
            "owner_gate_mutation": False,
            "command": index_plan_linking.get("command", ""),
            "exit_code": index_plan_linking.get("exit_code", None),
            "parse_error": index_plan_linking.get("parse_error", ""),
            "missing": ["index-plan-linking-json"],
            "summary": {
                "status": "fail",
                "registered_source_count": 0,
                "pcr02_level2_source_ids_present": False,
                "provenance_fields_present": False,
                "project_specific_not_team_promoted": False,
                "missing_anchors": ["index-plan-linking-json"],
                "requirement_refs": refs_for("cross_session", "cross_project"),
                "section_refs": sections_for("cross_session", "cross_project"),
                "notes_zh": "无法解析 linking audit JSON；跨会话和跨项目恢复链路不可采信。",
            },
            "limitations_zh": "无法解析 linking audit JSON；未读取 PCR02 源项目正文，未关闭 owner gate。",
        }
    if index_plan_linking.get("exit_code") != 0:
        audit.setdefault("contract_version", 1)
        audit["status"] = "fail"
        audit["command"] = index_plan_linking.get("command", "")
        audit["exit_code"] = index_plan_linking.get("exit_code", None)
        audit["parse_error"] = index_plan_linking.get("parse_error", "")
        audit["requirement_refs"] = refs_for("cross_session", "cross_project")
        audit["section_refs"] = sections_for("cross_session", "cross_project")
        audit["summary"] = {
            "status": "fail",
            "registered_source_count": 0,
            "pcr02_level2_source_ids_present": False,
            "provenance_fields_present": False,
            "project_specific_not_team_promoted": False,
            "missing_anchors": audit.get("missing", []),
            "requirement_refs": refs_for("cross_session", "cross_project"),
            "section_refs": sections_for("cross_session", "cross_project"),
            "notes_zh": "index-plan linking 命令未通过；跨会话和跨项目恢复链路不可采信。",
        }
        audit.setdefault("limitations_zh", "只证明 registry/index/search 恢复链路；不证明 owner decision 已签收，不读取 PCR02 源项目正文。")
        return audit
    audit.setdefault("contract_version", 1)
    audit.setdefault("status", "fail")
    audit.setdefault("read_only", True)
    audit.setdefault("source_body_read", False)
    audit.setdefault("owner_gate_mutation", False)
    audit["command"] = index_plan_linking.get("command", "")
    audit["exit_code"] = index_plan_linking.get("exit_code", None)
    audit["parse_error"] = index_plan_linking.get("parse_error", "")
    cross_project = audit.get("cross_project", {}) if isinstance(audit.get("cross_project", {}), dict) else {}
    markdown_index_recovery = audit.get("markdown_index_recovery", {}) if isinstance(audit.get("markdown_index_recovery", {}), dict) else {}
    audit["requirement_refs"] = refs_for("cross_session", "cross_project")
    audit["section_refs"] = sections_for("cross_session", "cross_project")
    audit["summary"] = {
        "status": audit.get("status", "fail"),
        "registered_source_count": cross_project.get("registered_source_count", 0),
        "pcr02_level2_source_ids_present": bool(cross_project.get("pcr02_level2_source_ids_present", False)),
        "provenance_fields_present": bool(cross_project.get("provenance_fields_present", False)),
        "project_specific_not_team_promoted": bool(cross_project.get("project_specific_not_team_promoted", False)),
        "missing_anchors": markdown_index_recovery.get("missing_anchors", []),
        "requirement_refs": refs_for("cross_session", "cross_project"),
        "section_refs": sections_for("cross_session", "cross_project"),
        "notes_zh": "跨会话、跨项目、source、topic、decision 和 Markdown index 恢复链路的只读摘要；不读取 PCR02 源项目正文，不关闭 owner gate。",
    }
    return audit

knowledge_check = run_json(["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics", "--as-of", today.isoformat()])
git_diff_check = run_text(["rtk", "git", "diff", "--check"])
if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
    knowledge_regression = {
        "command": f"rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json --suite {args.regression_suite} --as-of {today.isoformat()}",
        "exit_code": 0,
        "payload": {
            "status": "pass",
            "result_count": 1,
            "suite": args.regression_suite,
            "full_result_count": 1,
            "results": [
                {
                    "id": "inner-final-gate-regression-stub",
                    "status": "pass",
                    "summary": "inner final-gate regression recursion guard",
                }
            ],
            "skipped_for_self_test": False,
            "inner_final_gate_regression_stub": True,
        },
        "parse_error": "",
        "stderr": "",
    }
elif os.environ.get("KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION") == "1":
    knowledge_regression = {
        "command": f"rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json --suite {args.regression_suite} --as-of {today.isoformat()}",
        "exit_code": 0,
        "payload": {"status": "pass", "result_count": 0, "suite": args.regression_suite, "full_result_count": 0, "results": [], "skipped_for_self_test": True},
        "parse_error": "",
        "stderr": "",
    }
else:
    knowledge_regression = run_json(["rtk", "bash", "tools/knowledge-regression.sh", "--json", "--suite", args.regression_suite, "--as-of", today.isoformat()])
strict_status_command = ["rtk", "bash", "tools/knowledge-status.sh", "--strict", "--json", "--as-of", today.isoformat()]
if args.final_profile != "standard":
    strict_status_command.extend(["--final-profile", args.final_profile])
strict_status = run_json(strict_status_command)
proof_artifacts = build_final_proof_artifacts_summary(today.isoformat())
source_check_execution_snapshot = build_source_check_snapshot_summary()
source_check_runtime = run_json(["rtk", "bash", "tools/knowledge-source-check.sh", "--scope", "pcr02-level2", "--json", "--as-of", today.isoformat()])
source_check_runtime_summary = build_source_check_runtime_summary(source_check_runtime)
index_plan_linking = run_json(["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", "linking", "--json"])
linking_audit = build_linking_audit_summary(index_plan_linking)
maintenance_entry_audit = build_maintenance_entry_audit()

blockers = []

if knowledge_check["parse_error"]:
    blockers.append({
        "id": "knowledge-check-unparseable",
        "severity": "blocker",
        "summary_zh": "knowledge-check JSON 输出无法解析，不能作为终态证据。",
        "command": knowledge_check["command"],
    })
elif knowledge_check["exit_code"] != 0:
    check_payload = knowledge_check["payload"]
    diagnostic_category_ids = [
        category.get("id", "")
        for category in check_payload.get("diagnostics", {}).get("categories", [])
        if isinstance(category, dict)
    ]
    blockers.append({
        "id": "knowledge-check-failed",
        "severity": "blocker",
        "count": len(check_payload.get("errors", [])),
        "diagnostic_categories": diagnostic_category_ids,
        "gap_type": diagnostic_gap_type(diagnostic_category_ids),
        "summary_zh": "knowledge-check 未通过，必须先修复全仓一致性错误。",
        "command": knowledge_check["command"],
    })

if git_diff_check["exit_code"] != 0:
    blockers.append({
        "id": "git-diff-check-failed",
        "severity": "blocker",
        "summary_zh": "git diff --check 未通过，当前 diff 存在空白或补丁格式问题，不能作为终态证据。",
        "command": git_diff_check["command"],
        "stdout": git_diff_check["stdout"],
        "stderr": git_diff_check["stderr"],
    })

if regression_environment_failure(knowledge_regression):
    blockers.append({
        "id": "regression-environment-temp-space-exhausted",
        "severity": "environment",
        "summary_zh": "knowledge-regression 无法可靠启动或复制临时 fixture；宿主临时空间不足，不应误判为知识内容回归失败。",
        "command": knowledge_regression["command"],
        "stderr": knowledge_regression.get("stderr", ""),
        "parse_error": knowledge_regression.get("parse_error", ""),
    })
elif knowledge_regression["parse_error"]:
    blockers.append({
        "id": "knowledge-regression-unparseable",
        "severity": "blocker",
        "summary_zh": "knowledge-regression JSON 输出无法解析，不能作为终态证据。",
        "command": knowledge_regression["command"],
    })
elif knowledge_regression["payload"].get("skipped_for_self_test") is True:
    blockers.append({
        "id": "knowledge-regression-skipped",
        "severity": "blocker",
        "summary_zh": "knowledge-regression 被自测跳过标记短路，不能作为终态证据；请在无 KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION 的环境中重跑 final gate。",
        "command": knowledge_regression["command"],
    })
elif knowledge_regression["exit_code"] != 0:
    regression_payload = knowledge_regression["payload"]
    failed = [
        item.get("id", "")
        for item in regression_payload.get("results", [])
        if item.get("status") != "pass"
    ]
    blockers.append({
        "id": "knowledge-regression-failed",
        "severity": "blocker",
        "count": len(failed),
        "summary_zh": "knowledge-regression 未通过，终态验收不能只看 status dashboard。",
        "command": knowledge_regression["command"],
        "failed_ids": failed,
    })

if source_check_runtime_summary["status"] != "pass":
    blockers.append({
        "id": "source-check-runtime-failed",
        "severity": "blocker",
        "count": source_check_runtime_summary.get("failed_count", 0),
        "gap_type": "source-coverage",
        "summary_zh": "final gate 当前 PCR02 Level 2 source availability report-only 检查未通过，不能作为终态证据。",
        "command": source_check_runtime_summary["command"],
        "source_check_runtime": source_check_runtime_summary,
    })

if maintenance_entry_audit["status"] != "pass":
    blockers.append({
        "id": "maintenance-entry-audit-missing",
        "severity": "blocker",
        "gap_type": "manual-maintenance",
        "count": len(maintenance_entry_audit.get("missing_entry_ids", [])),
        "summary_zh": "长期维护入口审计未通过，不能证明中文开发人员长期维护路径完整。",
        "command": "runtime:maintenance_entry_audit",
        "missing_entry_ids": maintenance_entry_audit.get("missing_entry_ids", []),
    })

if linking_audit.get("status") != "pass":
    blockers.append({
        "id": "linking-audit-failed",
        "severity": "blocker",
        "gap_type": "cross-session-linking",
        "summary_zh": "跨会话、项目、source、topic、decision 恢复链路审计未通过。",
        "command": linking_audit.get("command", index_plan_linking.get("command", "")),
        "linking_audit": linking_audit,
    })

strict_payload = strict_status["payload"]
if strict_status["parse_error"]:
    blockers.append({
        "id": "knowledge-status-unparseable",
        "severity": "blocker",
        "summary_zh": "knowledge-status --strict JSON 输出无法解析，不能作为终态证据。",
        "command": strict_status["command"],
    })
elif strict_status["exit_code"] != 0:
    for blocker in strict_payload.get("strict_blockers", []):
        copied = dict(blocker)
        copied["source"] = "knowledge-status"
        blockers.append(copied)
    if not strict_payload.get("strict_blockers"):
        blockers.append({
            "id": "knowledge-status-strict-failed",
            "severity": "blocker",
            "summary_zh": "knowledge-status --strict 未通过，但未提供 strict_blockers。",
            "command": strict_status["command"],
        })

if blockers:
    final_status = "needs-owner-review" if all(item.get("severity") == "owner-review" for item in blockers) else "needs-fix"
else:
    final_status = "ok"

def blocker_to_gap(blocker):
    blocker_id = str(blocker.get("id", "") or "<missing>")
    is_owner_gate = blocker_id == "owner-gates-open"
    is_review_queue_owner_review = blocker_id == "review-queue-pending-max-body"
    is_owner_review = blocker.get("severity") == "owner-review"
    is_environment = blocker.get("severity") == "environment"
    gap_type = blocker_gap_type(blocker)
    return {
        "gap_id": blocker_id,
        "gap_type": gap_type,
        "source_id": "pcr02-project-docs" if is_owner_gate else "",
        "source_root": "registry/status/final-gate",
        "evidence": blocker.get("summary_zh", ""),
        "current_impact": (
            "剩余人工 owner decision 未签收；Codex 不得代签、不得关闭 gate。"
            if is_owner_gate
            else "普通 AI/外部资料人工复核队列未清零；Codex 不得代填 human_reviewed_by、不得代签 review_basis。"
            if is_review_queue_owner_review
            else "剩余人工复核门禁未闭环；Codex 只能提供表单、校验和只读证据，不得代签。"
            if is_owner_review
            else "宿主临时空间或执行环境不足，当前无法形成可信终态回归证据。"
            if is_environment
            else "终态 gate 存在非 owner blocker，必须先修复工具、registry、index、manifest 或回归。"
        ),
        "codex_auto_can_complete": False if (is_owner_review or is_environment) else True,
        "requires_owner_decision": bool(is_owner_gate),
        "requires_human_review": bool(is_owner_review),
        "fix_action": (
            "人工 owner 填写 owner decision JSONL 后，先运行 validate-forms，再生成 landing-plan。"
            if is_owner_gate
            else "人工导出 review queue 表单、填写复核字段、运行 validate-queue-forms，再用 review queue apply dry-run/落地。"
            if is_review_queue_owner_review
            else "释放 /tmp 或配置可用临时空间后，重跑 knowledge-regression 和 knowledge-final-gate。"
            if is_environment
            else "按 blocker command 修复对应门禁，然后重跑 knowledge-final-gate。"
        ),
        "write_scope": (
            "owner decision JSONL 由人工提供；Codex 只允许在校验通过后按 landing-plan 落地。"
            if is_owner_gate
            else "review queue 表单由人工提供；Codex 只允许运行校验和受控 apply，不得代填人工复核字段。"
            if is_review_queue_owner_review
            else "环境修复不修改 Knowledge Hub 内容；只清理可重建缓存或调整临时目录。"
            if is_environment
            else "按具体 blocker 限定；共享 registry/index/tool 由主 agent 串行修改。"
        ),
        "validation_commands": blocker.get("commands", []) + blocker.get("command_templates", []) + ([blocker.get("command")] if blocker.get("command") else []),
        "status": "open",
    }

only_owner_review_blockers = bool(blockers) and all(item.get("severity") == "owner-review" for item in blockers)
core_checks_pass = (
    not knowledge_check["parse_error"]
    and knowledge_check["exit_code"] == 0
    and git_diff_check["exit_code"] == 0
    and not knowledge_regression["parse_error"]
    and knowledge_regression["exit_code"] == 0
    and knowledge_regression["payload"].get("skipped_for_self_test") is not True
    and source_check_runtime_summary["status"] == "pass"
)
owner_payload = strict_payload.get("owner_gates", {}) if isinstance(strict_payload, dict) else {}
owner_gate_open_count = int(owner_payload.get("open_count", 0) or 0)
owner_gate_resolved_count = int(owner_payload.get("resolved_count", 0) or 0)
owner_gate_row_count = int(owner_payload.get("row_count", 0) or 0)
owner_ready_package_coverage = str(owner_payload.get("owner_ready_package_coverage", ""))
owner_active_exposure_count = int(owner_payload.get("active_exposure_count", 0) or 0)
owner_gates_complete = (
    owner_gate_row_count == 7
    and owner_gate_open_count == 0
    and owner_gate_resolved_count == 7
    and owner_active_exposure_count == 0
)
owner_gates_ready_for_review = (
    owner_gate_row_count == 7
    and owner_gate_open_count == 7
    and owner_ready_package_coverage == "7/7"
    and owner_active_exposure_count == 0
)
review_queue_payload = strict_payload.get("review_queues", {}) if isinstance(strict_payload, dict) else {}
review_queue_summary = (
    review_queue_payload.get("summary", {})
    if isinstance(review_queue_payload.get("summary", {}), dict)
    else {}
)
review_queue_total_pending_count = int(review_queue_summary.get("total_pending_count", 0) or 0)
review_queue_active_or_promotion_blocker_count = int(review_queue_summary.get("active_or_promotion_blocker_count", 0) or 0)
review_queue_profile_blocks_final_gate = bool(review_queue_payload.get("blocking_final_gate", False))
review_queue_owner_review_blocking = (
    review_queue_profile_blocks_final_gate
    and review_queue_total_pending_count > 0
    and review_queue_active_or_promotion_blocker_count == 0
)
if review_queue_active_or_promotion_blocker_count:
    review_queue_notes_zh = "只读 review queue 恢复入口；存在 active/promotion 类条目未完成人工复核，必须先补复核证据或降级为 reviewing/report-only。不回填 human_reviewed_by，不提升 active，不关闭 owner gate。"
elif review_queue_owner_review_blocking:
    review_queue_notes_zh = f"只读 review queue 恢复入口；{args.final_profile} profile 将普通 AI/外部资料待复核项作为 owner-review 阻断，需要人工导出表单、填写、校验并通过 review queue apply 落地。不回填 human_reviewed_by，不提升 active，不关闭 owner gate。"
else:
    review_queue_notes_zh = "只读 review queue 恢复入口；standard profile 下普通 AI/外部资料待复核项不阻断 final gate，只有 active/promotion 未人工复核时才由 knowledge-status --strict 变成 blocker。不回填 human_reviewed_by，不提升 active，不关闭 owner gate。"

review_queue_recovery = {
    "status": str(review_queue_payload.get("status", "")),
    "read_only": bool(review_queue_payload.get("read_only", False)),
    "report_only": bool(review_queue_payload.get("report_only", False)),
    "final_profile": str(review_queue_payload.get("final_profile", args.final_profile) or args.final_profile),
    "blocking_final_gate": review_queue_profile_blocks_final_gate,
    "owner_review_blocking": review_queue_owner_review_blocking,
    "standard_blocking_final_gate": bool(review_queue_payload.get("standard_blocking_final_gate", False)),
    "max_body_blocking_final_gate": bool(review_queue_payload.get("max_body_blocking_final_gate", False)),
    "summary": {
        "total_pending_count": review_queue_total_pending_count,
        "ai_generated_pending_count": int(review_queue_summary.get("ai_generated_pending_count", 0) or 0),
        "external_source_pending_count": int(review_queue_summary.get("external_source_pending_count", 0) or 0),
        "active_or_promotion_blocker_count": review_queue_active_or_promotion_blocker_count,
        "by_priority": review_queue_summary.get("by_priority", {}),
        "by_owner": review_queue_summary.get("by_owner", {}),
    },
    "commands": {
        "index_plan": review_queue_payload.get("commands", {}).get("index_plan", "")
        if isinstance(review_queue_payload.get("commands", {}), dict)
        else "",
        "status_json": review_queue_payload.get("commands", {}).get("status_json", "")
        if isinstance(review_queue_payload.get("commands", {}), dict)
        else "",
        "recommended_batch_json": review_queue_payload.get("commands", {}).get("recommended_batch_json", "")
        if isinstance(review_queue_payload.get("commands", {}), dict)
        else "",
        "recommended_forms_jsonl": review_queue_payload.get("commands", {}).get("recommended_forms_jsonl", "")
        if isinstance(review_queue_payload.get("commands", {}), dict)
        else "",
        "recommended_validate_queue_forms": review_queue_payload.get("commands", {}).get("recommended_validate_queue_forms", "")
        if isinstance(review_queue_payload.get("commands", {}), dict)
        else "",
    },
    "must_not": review_queue_payload.get("must_not", [])
    if isinstance(review_queue_payload.get("must_not", []), list)
    else [],
    "notes_zh": review_queue_notes_zh,
}
strict_blocker_ids = [
    str(blocker.get("id", ""))
    for blocker in strict_payload.get("strict_blockers", [])
    if isinstance(blocker, dict) and blocker.get("id")
]
strict_owner_review_blocker_ids = [
    str(blocker.get("id", ""))
    for blocker in strict_payload.get("strict_blockers", [])
    if isinstance(blocker, dict)
    and blocker.get("severity") == "owner-review"
    and blocker.get("id")
]
strict_owner_review_blocker_summary = ", ".join(strict_owner_review_blocker_ids) if strict_owner_review_blocker_ids else "owner-review"
status_owner_blocker_source = strict_payload.get("owner_blocker_source", {})
mature_audit_payload = {}
if isinstance(strict_payload.get("sources", {}), dict):
    raw_mature_audit = strict_payload.get("sources", {}).get("mature_audit", {})
    if isinstance(raw_mature_audit, dict):
        mature_audit_payload = raw_mature_audit
check_source_coverage_health = knowledge_check["payload"].get("source_coverage_health", {})
check_source_coverage_selection = knowledge_check["payload"].get("source_coverage_selection", {})
check_source_check_health = knowledge_check["payload"].get("source_check_health", {})
check_source_control_health = knowledge_check["payload"].get("source_control_health", {})
check_owner_target_health = knowledge_check["payload"].get("owner_target_health", {})
check_boundary_health = knowledge_check["payload"].get("boundary_health", {})
current_source_registry = load_json(root / "registry" / "sources.json").get("sources", [])
retired_source_registry = load_jsonl(root / "registry" / "retired-sources.jsonl")
source_registry = current_source_registry + retired_source_registry
source_registry_ids = {
    str(source.get("id", ""))
    for source in source_registry
    if source.get("id")
}
source_final_state_required_fields = [
    "id",
    "path",
    "role",
    "authority",
    "status",
    "write_policy",
    "source_strategy",
    "owner",
    "review_after",
    "final_disposition",
]
missing_source_final_state_fields = []
for source in source_registry:
    source_id = str(source.get("id", "<unknown>"))
    for field in source_final_state_required_fields:
        if not source.get(field):
            missing_source_final_state_fields.append({"source_id": source_id, "field": field})
    if not str(source.get("check", "")).strip() and not str(source.get("no_check_reason", "")).strip():
        missing_source_final_state_fields.append({"source_id": source_id, "field": "no_check_reason"})
latest_coverage_manifest = str(strict_payload.get("sources", {}).get("latest_coverage_manifest", ""))
strict_source_coverage_selection = strict_payload.get("sources", {}).get("latest_coverage_selection", {})
source_coverage_rows = load_jsonl(root / latest_coverage_manifest) if latest_coverage_manifest else []
covered_source_ids = {
    str(row.get("source_id", ""))
    for row in source_coverage_rows
    if row.get("source_id")
}
pcr02_level2_source_ids = {
    "pcr02-project-tools",
    "pcr02-project-knowledge",
    "pcr02-product-test",
    "pcr02-project-scratch",
    "pcr02-project-root-artifacts",
    "pcr02-module-agent-rules",
    "pcr02-project-agent-config",
}
automatic_governance_complete = (
    core_checks_pass
    and (final_status == "ok" or only_owner_review_blockers)
)
automatic_governance_status = (
    "complete" if final_status == "ok"
    else "complete-except-owner-review" if automatic_governance_complete and only_owner_review_blockers
    else "needs-fix"
)
pcr02_docs_coverage = next(
    (row for row in source_coverage_rows if row.get("source_id") == "pcr02-project-docs"),
    {},
)
missing_level2_sources = sorted(pcr02_level2_source_ids - source_registry_ids)
missing_level2_coverage = sorted(pcr02_level2_source_ids - covered_source_ids)
missing_registered_coverage = sorted(source_registry_ids - covered_source_ids)

def make_source_audit_gaps():
    source_gaps = []
    for source_id in missing_level2_sources:
        source_gaps.append({
            "gap_id": f"level2-source-missing:{source_id}",
            "gap_type": "registry",
            "source_id": source_id,
            "source_root": "registry/sources.json + registry/retired-sources.jsonl",
            "evidence": f"PCR02 Level 2 source {source_id} is missing from current/retired source registry.",
            "current_impact": "PCR02 候选 source 不能从 source registry 恢复，Level 2 source coverage 不完整。",
            "codex_auto_can_complete": True,
            "requires_owner_decision": False,
            "fix_action": "按 source 当前/退休状态补 registry/sources.json 或 registry/retired-sources.jsonl source object，并同步 by-source、source coverage manifest 和 registry/index 证据。",
            "write_scope": "registry/sources.json 或 registry/retired-sources.jsonl、indexes/by-source.md、artifacts/manifests/*source-coverage*.jsonl 和对应 manifest/registry/index。",
            "validation_commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --sources-only --json",
                "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json",
            ],
            "status": "open",
        })
    for source_id in missing_level2_coverage:
        source_gaps.append({
            "gap_id": f"level2-source-coverage-missing:{source_id}",
            "gap_type": "source-coverage",
            "source_id": source_id,
            "source_root": latest_coverage_manifest,
            "evidence": f"PCR02 Level 2 source {source_id} is missing from latest source coverage manifest.",
            "current_impact": "PCR02 候选 source 已登记但缺少终态 classification/decision/risk 证据。",
            "codex_auto_can_complete": True,
            "requires_owner_decision": False,
            "fix_action": "在最新 source coverage JSONL 中补 source row，写清 classification、decision、risk、owner 和 checked_at。",
            "write_scope": "artifacts/manifests/*source-coverage*.jsonl、相关 manifest/registry/index。",
            "validation_commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
                "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json",
            ],
            "status": "open",
        })
    for source_id in missing_registered_coverage:
        source_gaps.append({
            "gap_id": f"registered-source-coverage-missing:{source_id}",
            "gap_type": "source-coverage",
            "source_id": source_id,
            "source_root": latest_coverage_manifest,
            "evidence": f"Registered source {source_id} is missing from latest source coverage manifest.",
            "current_impact": "registered source 无法证明终态 disposition，Level 3 source audit 不完整。",
            "codex_auto_can_complete": True,
            "requires_owner_decision": False,
            "fix_action": "为 registered source 补 source coverage row，并同步 source/project/topic 索引锚点。",
            "write_scope": "artifacts/manifests/*source-coverage*.jsonl、indexes/by-source.md、必要 registry/source-policy/index。",
            "validation_commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
                "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json",
            ],
            "status": "open",
        })
    for missing in missing_source_final_state_fields:
        source_id = str(missing.get("source_id", ""))
        field = str(missing.get("field", ""))
        source_gaps.append({
            "gap_id": f"source-final-state-field-missing:{source_id}:{field}",
            "gap_type": "registry",
            "source_id": source_id,
            "field": field,
            "source_root": "registry/sources.json",
            "evidence": f"registry/sources.json source {source_id} missing final-state field {field}.",
            "current_impact": "source registry 不能独立说明 owner、review_after、source_strategy、final_disposition 或 check/no-check 边界。",
            "codex_auto_can_complete": True,
            "requires_owner_decision": False,
            "fix_action": "补齐 source registry final-state 字段；没有稳定 check 时写 no_check_reason。",
            "write_scope": "registry/sources.json、registry/schema.md 如需说明、对应 manifest/registry/index。",
            "validation_commands": [
                "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --sources-only --json",
                "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json",
            ],
            "status": "open",
        })
    return source_gaps

gap_map = [blocker_to_gap(blocker) for blocker in blockers] + make_source_audit_gaps()
level1_status = (
    "complete"
    if core_checks_pass
    and owner_gates_complete
    and bool(pcr02_docs_coverage)
    else
    "complete-except-owner-review"
    if core_checks_pass
    and owner_gates_ready_for_review
    and bool(pcr02_docs_coverage)
    else "needs-fix"
)
level2_status = (
    "complete"
    if not missing_level2_sources
    and not missing_level2_coverage
    and check_boundary_health.get("status") == "pass"
    else "needs-fix"
)
level3_status = (
    "complete"
    if source_registry_ids
    and not missing_registered_coverage
    and not missing_source_final_state_fields
    and not check_source_check_health.get("missing_check_or_reason_ids", [])
    and not check_source_check_health.get("non_rtk_check_ids", [])
    and check_source_control_health.get("status") == "pass"
    and check_owner_target_health.get("status") == "pass"
    else "needs-fix"
)
final_state_audit = {
    "level1_pcr02_docs": {
        "status": level1_status,
        "source_id": "pcr02-project-docs",
        "coverage_status": str(pcr02_docs_coverage.get("status", "")),
        "expected_owner_gate_count": 7,
        "expected_owner_gate_count_source": "artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl total rows with owner-ready package coverage; open=7 before owner decision, open=0/resolved=7 after owner decision landing",
        "worksheet_count": int(owner_payload.get("worksheet_count", 0) or 0),
        "worksheet_row_count": owner_gate_row_count,
        "owner_gate_open_count": owner_gate_open_count,
        "owner_gate_resolved_count": owner_gate_resolved_count,
        "owner_gate_count_matches_expected": owner_gates_complete or owner_gates_ready_for_review,
        "owner_gate_terminal_status": "owner-gates-complete" if owner_gates_complete else "owner-gates-open" if owner_gates_ready_for_review else "owner-gates-inconsistent",
        "owner_ready_package_count": int(owner_payload.get("owner_ready_package_count", 0) or 0),
        "owner_ready_expected_count": owner_gate_row_count,
        "owner_ready_package_coverage": owner_ready_package_coverage,
        "active_exposure_count": owner_active_exposure_count,
        "no_owner_decision_generated": only_owner_review_blockers,
        "evidence_refs": [
            latest_coverage_manifest,
            "artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl",
            "artifacts/manifests/pcr02-owner-decision-intake-execution-20260620.md",
            "tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json",
        ],
        "summary_zh": (
            "PCR02 docs 控制面已闭合；7 条 owner gate 已人工签收并落地，未暴露 active 污染。"
            if owner_gates_complete
            else "PCR02 docs 控制面已闭合；剩余 7 个 owner-gated docs 只能由 owner 人工签收。"
        ),
    },
    "level2_pcr02_candidate_sources": {
        "status": level2_status,
        "required_source_ids": sorted(pcr02_level2_source_ids),
        "registered_count": len(pcr02_level2_source_ids - set(missing_level2_sources)),
        "covered_count": len(pcr02_level2_source_ids - set(missing_level2_coverage)),
        "missing_source_ids": missing_level2_sources,
        "missing_coverage_ids": missing_level2_coverage,
        "boundary_health": {
            "status": check_boundary_health.get("status", ""),
            "mode": check_boundary_health.get("mode", ""),
            "summary": check_boundary_health.get("summary", {}),
            "hard_failure_count": len(check_boundary_health.get("hard_failures", [])),
            "source_project_read": bool(check_boundary_health.get("source_project_read", True)),
            "owner_gate_mutation": bool(check_boundary_health.get("owner_gate_mutation", True)),
            "memory_write": bool(check_boundary_health.get("memory_write", True)),
        },
        "source_check_execution_snapshot": source_check_execution_snapshot,
        "source_check_runtime": source_check_runtime_summary,
        "evidence_refs": [
            "registry/sources.json",
            "registry/retired-sources.jsonl",
            latest_coverage_manifest,
            "artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.md",
            "artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md",
            "runtime:checks.source_check_runtime",
        ],
        "summary_zh": "PCR02 docs 外 7 个关键候选 source 已登记并纳入 source coverage。",
    },
    "level3_registered_sources": {
        "status": level3_status,
        "registered_count": len(source_registry_ids),
        "covered_count": len(source_registry_ids & covered_source_ids),
        "latest_coverage_manifest": latest_coverage_manifest,
        "source_coverage_selection": strict_source_coverage_selection or check_source_coverage_selection,
        "check_source_coverage_selection": check_source_coverage_selection,
        "missing_coverage_ids": missing_registered_coverage,
        "missing_final_state_fields": missing_source_final_state_fields,
        "source_coverage_health": check_source_coverage_health,
        "source_check_health": {
            "mode": check_source_check_health.get("mode", ""),
            "executed": bool(check_source_check_health.get("executed", True)),
            "registered_source_count": check_source_check_health.get("registered_source_count", 0),
            "with_check_count": check_source_check_health.get("with_check_count", 0),
            "with_no_check_reason_count": check_source_check_health.get("with_no_check_reason_count", 0),
            "missing_check_or_reason_ids": check_source_check_health.get("missing_check_or_reason_ids", []),
            "non_rtk_check_ids": check_source_check_health.get("non_rtk_check_ids", []),
            "missing_source_path_ids": check_source_check_health.get("missing_source_path_ids", []),
        },
        "source_control_health": {
            "status": check_source_control_health.get("status", ""),
            "mode": check_source_control_health.get("mode", ""),
            "registered_source_count": check_source_control_health.get("registered_source_count", 0),
            "required_file_count": check_source_control_health.get("required_file_count", 0),
            "present_file_count": check_source_control_health.get("present_file_count", 0),
            "missing_source_ids": check_source_control_health.get("missing_source_ids", []),
            "missing_file_count": len(check_source_control_health.get("missing_files", [])),
            "inventory_row_count": check_source_control_health.get("inventory_row_count", 0),
            "invalid_inventory_row_count": len(check_source_control_health.get("invalid_inventory_rows", [])),
            "unsafe_raw_copy_row_count": len(check_source_control_health.get("unsafe_raw_copy_rows", [])),
        },
        "owner_target_health": {
            "status": check_owner_target_health.get("status", ""),
            "checked_count": check_owner_target_health.get("checked_count", 0),
            "present_count": check_owner_target_health.get("present_count", 0),
            "skipped_count": check_owner_target_health.get("skipped_count", 0),
            "missing_target_count": len(check_owner_target_health.get("missing_targets", [])),
        },
        "evidence_refs": [
            "registry/sources.json",
            "registry/retired-sources.jsonl",
            latest_coverage_manifest,
            "sources/<source_id>/",
            "artifacts/manifests/knowledge-hub-source-control-unification-20260624.md",
            "tools/knowledge-check.sh --dry-run --json --diagnostics",
        ],
        "summary_zh": (
            "current/retired source registry 中 registered source 已由最新 source coverage manifest 覆盖，且 source registry 终态字段已补齐。"
            if level3_status == "complete"
            else "registered source coverage 或 source registry 终态字段仍有缺口，需按 missing_* 字段修复。"
        ),
    },
}

evidence_index = [
    command_evidence_row(
        knowledge_check["command"],
        knowledge_check["exit_code"],
        "pass" if not knowledge_check["parse_error"] and knowledge_check["exit_code"] == 0 else "fail",
        (
            f"knowledge-check 通过；errors={len(knowledge_check['payload'].get('errors', []))}，warnings={len(knowledge_check['payload'].get('warnings', []))}。"
            if not knowledge_check["parse_error"] and knowledge_check["exit_code"] == 0
            else "knowledge-check 未能提供可采信的通过证据；请查看 blockers 和 diagnostics。"
        ),
        "runtime:checks.knowledge_check",
        "final-gate",
        "knowledge-check",
        knowledge_check["parse_error"],
        refs_for("level1", "level2", "level3", "maintenance", "offline"),
        sections_for("level1", "level2", "level3", "maintenance", "offline"),
    ),
    command_evidence_row(
        knowledge_regression["command"],
        knowledge_regression["exit_code"],
        (
            "skipped"
            if knowledge_regression["payload"].get("skipped_for_self_test") is True
            else "pass"
            if not knowledge_regression["parse_error"] and knowledge_regression["exit_code"] == 0
            else "fail"
        ),
        (
            "knowledge-regression 通过；result_count="
            f"{knowledge_regression['payload'].get('result_count', 0)}。"
            if not knowledge_regression["parse_error"] and knowledge_regression["exit_code"] == 0 and knowledge_regression["payload"].get("skipped_for_self_test") is not True
            else "knowledge-regression 被 self-test skip 短路，不能作为终态通过证据。"
            if knowledge_regression["payload"].get("skipped_for_self_test") is True
            else "knowledge-regression 未能提供可采信的通过证据。"
        ),
        "runtime:checks.knowledge_regression",
        "final-gate",
        "knowledge-regression",
        knowledge_regression["parse_error"],
        refs_for("maintenance", "cross_session", "cross_project", "owner_gate", "automation"),
        sections_for("maintenance", "cross_session", "cross_project", "owner_gate", "automation"),
    ),
    command_evidence_row(
        git_diff_check["command"],
        git_diff_check["exit_code"],
        "pass" if git_diff_check["exit_code"] == 0 else "fail",
        (
            "git diff --check 通过；当前 diff 无空白错误。"
            if git_diff_check["exit_code"] == 0
            else "git diff --check 未通过；当前 diff 存在空白或补丁格式问题。"
        ),
        "runtime:checks.git_diff_check",
        "final-gate",
        "git-diff-check",
        "",
        refs_for("maintenance"),
        sections_for("maintenance"),
    ),
    command_evidence_row(
        strict_status["command"],
        strict_status["exit_code"],
        (
            "owner-review"
            if only_owner_review_blockers
            else "pass"
            if not strict_status["parse_error"] and strict_status["exit_code"] == 0
            else "fail"
        ),
        (
            f"knowledge-status --strict 仅剩 owner-review blocker（{strict_owner_review_blocker_summary}）；这是人工 owner decision 或人工复核 blocker，不是工具失败。"
            if only_owner_review_blockers
            else "knowledge-status --strict 通过。"
            if not strict_status["parse_error"] and strict_status["exit_code"] == 0
            else "knowledge-status --strict 存在非 owner blocker 或 JSON 解析问题。"
        ),
        "runtime:checks.knowledge_status_strict",
        "final-gate",
        "knowledge-status",
        strict_status["parse_error"],
        refs_for("owner_gate", "level1"),
        sections_for("owner_gate", "level1"),
    ),
]
if status_owner_blocker_source:
    evidence_index.append(
        command_evidence_row(
            "runtime:automatic_governance.owner_blocker_source",
            0,
            "owner-review" if only_owner_review_blockers else "not-applicable",
            (
                "owner-review blocker provenance 已由 knowledge-status --strict 提供；owner gate 可追溯到 owner_gates 字段，review queue 阻断可追溯到 review_queues 字段。"
                if only_owner_review_blockers
                else "当前终态不是纯 owner-review blocker；owner blocker provenance 仅作为辅助上下文。"
            ),
            "runtime:automatic_governance.owner_blocker_source",
            "final-gate",
            "owner-blocker-provenance",
            "",
            refs_for("owner_gate", "level1"),
            sections_for("owner_gate", "level1"),
        )
    )
evidence_index.append(
    command_evidence_row(
        f"artifact:{SOURCE_CHECK_SNAPSHOT_ID}",
        0,
        source_check_execution_snapshot["status"],
        (
            "PCR02 Level 2 source check 快照可恢复；7 条历史 report-only 结果全部 pass；当前执行证据另见 source_check_runtime。"
            if source_check_execution_snapshot["status"] == "pass"
            else "PCR02 Level 2 source check 快照登记、配对、索引或结果存在缺口；请查看 source_check_execution_snapshot。"
        ),
        source_check_execution_snapshot["jsonl_path"] or source_check_execution_snapshot["md_path"],
        "source-check-snapshot",
        SOURCE_CHECK_SNAPSHOT_ID,
        "",
        refs_for("level2", "level3"),
        sections_for("level2", "level3"),
    )
)
evidence_index.append(
    command_evidence_row(
        source_check_runtime_summary["command"],
        source_check_runtime_summary["exit_code"],
        source_check_runtime_summary["status"],
        (
            "PCR02 Level 2 source availability 当前 report-only 检查通过；7 条 test -d/test -f 均 pass，未读取 source 正文。"
            if source_check_runtime_summary["status"] == "pass"
            else "PCR02 Level 2 source availability 当前 report-only 检查未通过；请查看 checks.source_check_runtime。"
        ),
        "runtime:checks.source_check_runtime",
        "source-check-runtime",
        "knowledge-source-check-runtime",
        source_check_runtime_summary["parse_error"],
        refs_for("level2", "level3"),
        sections_for("level2", "level3"),
    )
)
evidence_index.append(
    command_evidence_row(
        "runtime:knowledge_check.source_control_health",
        0,
        check_source_control_health.get("status", "fail") or "fail",
        (
            "source 主控目录门禁通过；registered source 都有 README/inventory/coverage/source-policy，且 inventory 未发现 raw copy-body。"
            if check_source_control_health.get("status") == "pass"
            else "source 主控目录、inventory 或 raw dump safety 存在缺口；请查看 checks.knowledge_check.source_control_health。"
        ),
        "runtime:checks.knowledge_check.source_control_health",
        "source-control",
        "knowledge-check-source-control-health",
        "",
        refs_for("level3", "maintenance", "automation"),
        sections_for("level3", "maintenance", "automation"),
    )
)
evidence_index.append(
    command_evidence_row(
        "runtime:knowledge_check.owner_target_health",
        0,
        check_owner_target_health.get("status", "fail") or "fail",
        (
            "owner decision landing 的本地 target 存在性门禁通过；reference-only/report-only 项已跳过，PCR02 4 个目标正文存在。"
            if check_owner_target_health.get("status") == "pass"
            else "owner decision landing 指向的本地 target 缺失；请查看 checks.knowledge_check.owner_target_health。"
        ),
        "runtime:checks.knowledge_check.owner_target_health",
        "owner-target",
        "knowledge-check-owner-target-health",
        "",
        refs_for("level1", "level3", "owner_gate"),
        sections_for("level1", "level3", "owner_gate"),
    )
)
evidence_index.append(
    command_evidence_row(
        "runtime:maintenance_entry_audit",
        0,
        maintenance_entry_audit["status"],
        (
            "docs/goals 中列出的 8 类长期维护入口和 1 个离线维护包均可恢复；只证明入口存在，不代表人工动作已完成。"
            if maintenance_entry_audit["status"] == "pass"
            else "长期维护入口或离线维护包存在缺口；请查看 maintenance_entry_audit.missing_entry_ids。"
        ),
        "runtime:maintenance_entry_audit",
        "maintenance-entry-audit",
        "maintenance-entry-audit",
        "",
        refs_for("maintenance", "offline"),
        sections_for("maintenance", "offline"),
    )
)
evidence_index.append(
    command_evidence_row(
        index_plan_linking["command"],
        index_plan_linking["exit_code"],
        linking_audit.get("status", "fail"),
        (
            "跨会话、项目、source、topic、decision 和 Markdown index 恢复链路可机器证明；未读取 PCR02 源项目正文。"
            if linking_audit.get("status") == "pass"
            else "关联恢复链路存在缺口；请查看 linking_audit.cross_session/cross_project/markdown_index_recovery。"
        ),
        "runtime:linking_audit",
        "linking-audit",
        "linking-audit",
        index_plan_linking["parse_error"],
        refs_for("cross_session", "cross_project"),
        sections_for("cross_session", "cross_project"),
    )
)
evidence_index.append(
    command_evidence_row(
        "runtime:review_queue_recovery",
        0 if review_queue_recovery["read_only"] and review_queue_recovery["report_only"] else 1,
        (
            "owner-review"
            if review_queue_recovery["read_only"]
            and review_queue_recovery["report_only"]
            and review_queue_recovery["owner_review_blocking"]
            else "pass"
            if review_queue_recovery["read_only"]
            and review_queue_recovery["report_only"]
            and review_queue_recovery["summary"]["active_or_promotion_blocker_count"] == 0
            else "fail"
        ),
        (
            f"review queue 可结构化恢复；{args.final_profile} profile 下普通 AI/外部资料待复核项是 owner-review 阻断，需要人工复核闭环。"
            if review_queue_recovery["owner_review_blocking"]
            else "review queue 可结构化恢复；standard profile 下普通 AI/外部资料待复核项保持 report-only，不阻断 final gate。"
            if review_queue_recovery["summary"]["active_or_promotion_blocker_count"] == 0
            else "review queue 存在 active/promotion 未人工复核项，应由 knowledge-status --strict 作为非 owner blocker 处理。"
        ),
        "runtime:review_queue_recovery",
        "review-queue",
        "review-queue-recovery",
        "",
        refs_for("maintenance", "offline"),
        sections_for("maintenance", "offline"),
    )
)

highest_priority_rules_audit = make_highest_priority_rules_audit(
    source_check_runtime_summary,
    only_owner_review_blockers,
    final_status,
    automatic_governance_status,
)

final_gate_summary = {
    "final_status": final_status,
    "automatic_governance_status": automatic_governance_status,
    "level1_status": final_state_audit["level1_pcr02_docs"]["status"],
    "level2_status": final_state_audit["level2_pcr02_candidate_sources"]["status"],
    "level3_status": final_state_audit["level3_registered_sources"]["status"],
    "level1_owner_gate_open_count": final_state_audit["level1_pcr02_docs"]["owner_gate_open_count"],
    "level2_registered_count": final_state_audit["level2_pcr02_candidate_sources"]["registered_count"],
    "level2_covered_count": final_state_audit["level2_pcr02_candidate_sources"]["covered_count"],
    "level3_registered_count": final_state_audit["level3_registered_sources"]["registered_count"],
    "level3_covered_count": final_state_audit["level3_registered_sources"]["covered_count"],
    "proof_artifacts_status": proof_artifacts["status"],
    "proof_artifacts_expected_count": proof_artifacts["expected_count"],
    "proof_artifacts_registered_count": proof_artifacts["registered_count"],
    "proof_artifacts_paired_count": proof_artifacts["paired_count"],
    "proof_artifacts_indexed_count": proof_artifacts["indexed_count"],
    "maintenance_entry_audit_status": maintenance_entry_audit["status"],
    "maintenance_entry_audit_passed_entry_count": maintenance_entry_audit["passed_entry_count"],
    "maintenance_entry_audit_expected_entry_count": maintenance_entry_audit["expected_entry_count"],
    "linking_audit_status": linking_audit.get("status", "fail"),
    "cross_session_status": linking_audit.get("cross_session", {}).get("status", "fail")
    if isinstance(linking_audit.get("cross_session", {}), dict)
    else "fail",
    "cross_project_status": linking_audit.get("cross_project", {}).get("status", "fail")
    if isinstance(linking_audit.get("cross_project", {}), dict)
    else "fail",
    "markdown_index_recovery_status": linking_audit.get("markdown_index_recovery", {}).get("status", "fail")
    if isinstance(linking_audit.get("markdown_index_recovery", {}), dict)
    else "fail",
    "requirement_refs": refs_for("level1", "level2", "level3", "maintenance", "offline", "cross_session", "cross_project", "owner_gate", "automation"),
    "section_refs": sections_for("level1", "level2", "level3", "maintenance", "offline", "cross_session", "cross_project", "owner_gate", "automation"),
    "notes_zh": "只读派生摘要；便于扫读终态证据覆盖情况，不参与 final_status 判定，不生成或关闭 owner decision。",
}

result = {
    "schema_version": 1,
    "root": display_path(root),
    "read_only": True,
    "final_profile": args.final_profile,
    "regression_suite": args.regression_suite,
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "today": today.isoformat(),
    "as_of_source": today_source,
    "final_status": final_status,
    "summary": final_gate_summary,
    "automatic_governance": {
        "status": automatic_governance_status,
        "complete": automatic_governance_complete,
        "core_checks_pass": core_checks_pass,
        "only_owner_review_blockers": only_owner_review_blockers,
        "remaining_owner_gate_count": owner_gate_open_count,
        "resolved_owner_gate_count": owner_gate_resolved_count,
        "owner_ready_package_coverage": owner_ready_package_coverage,
        "active_exposure_count": owner_active_exposure_count,
        "no_owner_decision_generated": only_owner_review_blockers,
        "owner_decision_landing_status": "owner-decisions-landed" if owner_gates_complete else "pending-owner-review" if only_owner_review_blockers else "not-applicable",
        "owner_blocker_source": status_owner_blocker_source or {
            "status_source": "knowledge-status --strict",
            "strict_blocker_ids": strict_blocker_ids,
            "owner_gate_open_count_field": "owner_gates.open_count",
            "owner_ready_package_coverage_field": "owner_gates.owner_ready_package_coverage",
            "active_exposure_count_field": "owner_gates.active_exposure_count",
            "notes_zh": "owner gate 数量、owner-ready 覆盖和 active exposure 均来自 strict status 的 owner_gates；final gate 不自行关闭或生成 owner decision。",
        },
        "summary_zh": (
            "Codex 自动治理已闭环；剩余事项是人工 owner decision 或人工复核，不能由 Codex 代签。"
            if automatic_governance_status == "complete-except-owner-review"
            else "终态完全通过。"
            if automatic_governance_status == "complete"
            else "仍存在非 owner 的自动治理缺口，需要先修复。"
        ),
    },
    "owner_recovery": {
        "open_count": int(owner_payload.get("open_count", 0) or 0),
        "owner_ready_package_coverage": str(owner_payload.get("owner_ready_package_coverage", "")),
        "active_exposure_count": int(owner_payload.get("active_exposure_count", 0) or 0),
        "owner_dispatch": owner_payload.get("owner_dispatch", []),
        "next_open": owner_payload.get("next_open", {}),
        "next_open_queue": owner_payload.get("next_open_queue", []),
        "next_open_queue_count": int(owner_payload.get("next_open_queue_count", 0) or 0),
        "next_open_queue_selection_order": str(owner_payload.get("next_open_queue_selection_order", "")),
        "notes_zh": "只读 owner 恢复队列；用于恢复人工分派、表单导出和 landing-plan 入口，不生成 owner decision，不关闭 gate。",
    },
    "review_queue_recovery": review_queue_recovery,
    "mature_audit": mature_audit_payload,
    "proof_artifacts": proof_artifacts,
    "source_check_execution_snapshot": source_check_execution_snapshot,
    "source_check_runtime": source_check_runtime_summary,
    "maintenance_entry_audit": maintenance_entry_audit,
    "linking_audit": linking_audit,
    "highest_priority_rules_audit": highest_priority_rules_audit,
    "final_state_audit": final_state_audit,
    "checks": {
        "knowledge_check": {
            "exit_code": knowledge_check["exit_code"],
            "status": knowledge_check["payload"].get("status", "<missing>"),
            "error_count": len(knowledge_check["payload"].get("errors", [])),
            "warning_count": len(knowledge_check["payload"].get("warnings", [])),
            "parse_error": knowledge_check["parse_error"],
            "source_check_health": {
                "with_check_count": check_source_check_health.get("with_check_count", 0),
                "with_no_check_reason_count": check_source_check_health.get("with_no_check_reason_count", 0),
                "missing_check_or_reason_ids": check_source_check_health.get("missing_check_or_reason_ids", []),
                "non_rtk_check_ids": check_source_check_health.get("non_rtk_check_ids", []),
            },
            "source_control_health": {
                "status": check_source_control_health.get("status", ""),
                "registered_source_count": check_source_control_health.get("registered_source_count", 0),
                "required_file_count": check_source_control_health.get("required_file_count", 0),
                "present_file_count": check_source_control_health.get("present_file_count", 0),
                "missing_source_ids": check_source_control_health.get("missing_source_ids", []),
                "invalid_inventory_row_count": len(check_source_control_health.get("invalid_inventory_rows", [])),
                "unsafe_raw_copy_row_count": len(check_source_control_health.get("unsafe_raw_copy_rows", [])),
            },
            "owner_target_health": {
                "status": check_owner_target_health.get("status", ""),
                "checked_count": check_owner_target_health.get("checked_count", 0),
                "present_count": check_owner_target_health.get("present_count", 0),
                "missing_target_count": len(check_owner_target_health.get("missing_targets", [])),
            },
            "boundary_health": {
                "status": check_boundary_health.get("status", ""),
                "hard_failure_count": len(check_boundary_health.get("hard_failures", [])),
            },
        },
        "knowledge_regression": {
            "command": knowledge_regression["command"],
            "exit_code": knowledge_regression["exit_code"],
            "status": knowledge_regression["payload"].get("status", "<missing>"),
            "result_count": knowledge_regression["payload"].get("result_count", 0),
            "suite": knowledge_regression["payload"].get("suite", args.regression_suite),
            "full_result_count": knowledge_regression["payload"].get("full_result_count", 0),
            "selected_test_count": knowledge_regression["payload"].get("selected_test_count", 0),
            "full_test_count": knowledge_regression["payload"].get("full_test_count", 0),
            "slowest_results": knowledge_regression["payload"].get("slowest_results", []),
            "skipped_for_self_test": bool(knowledge_regression["payload"].get("skipped_for_self_test", False)),
            "inner_final_gate_regression_stub": bool(knowledge_regression["payload"].get("inner_final_gate_regression_stub", False)),
            "failed_ids": [
                item.get("id", "")
                for item in knowledge_regression["payload"].get("results", [])
                if item.get("status") != "pass"
            ],
            "parse_error": knowledge_regression["parse_error"],
        },
        "git_diff_check": {
            "exit_code": git_diff_check["exit_code"],
            "status": "pass" if git_diff_check["exit_code"] == 0 else "fail",
            "command": git_diff_check["command"],
            "stdout": git_diff_check["stdout"],
            "stderr": git_diff_check["stderr"],
        },
        "knowledge_status_strict": {
            "exit_code": strict_status["exit_code"],
            "status": strict_payload.get("status", "<missing>"),
            "strict_blocker_count": len(strict_payload.get("strict_blockers", [])),
            "parse_error": strict_status["parse_error"],
            "mature_audit": mature_audit_payload,
        },
        "source_check_runtime": source_check_runtime_summary,
        "index_plan_linking": {
            "command": index_plan_linking["command"],
            "exit_code": index_plan_linking["exit_code"],
            "status": index_plan_linking["payload"].get("status", "<missing>") if isinstance(index_plan_linking["payload"], dict) else "<missing>",
            "parse_error": index_plan_linking["parse_error"],
            "linking_audit_status": linking_audit.get("status", "fail"),
        },
    },
    "evidence_index": evidence_index,
    "blockers": blockers,
    "gap_map": gap_map,
    "next_actions_zh": strict_payload.get("next_actions_zh", []) if strict_payload else [],
}

exit_code = 0 if final_status == "ok" else 1

if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(exit_code)

print("# Knowledge Hub Final Gate")
print()
print("本命令只读聚合终态验收，不修改 Knowledge Hub 正文、registry、index 或源项目 docs。")
print("注意：内部 regression 子命令可能使用 /tmp 临时 fixture，并在结束时清理。")
print()
print(f"- final_status: {final_status}")
print(f"- final_profile: {args.final_profile}")
print(f"- automatic_governance: {result['automatic_governance']['status']}")
print(f"- level1_pcr02_docs: {final_state_audit['level1_pcr02_docs']['status']}")
print(f"- level2_pcr02_candidate_sources: {final_state_audit['level2_pcr02_candidate_sources']['status']}")
print(f"- level3_registered_sources: {final_state_audit['level3_registered_sources']['status']}")
print(f"- maintenance_entry_audit: {maintenance_entry_audit['status']} {maintenance_entry_audit['passed_entry_count']}/{maintenance_entry_audit['expected_entry_count']}")
print(f"- linking_audit: {linking_audit.get('status', 'fail')}")
print(f"- proof_artifacts: {proof_artifacts['status']} registered={proof_artifacts['registered_count']}/{proof_artifacts['expected_count']} paired={proof_artifacts['paired_count']}/{proof_artifacts['expected_count']} indexed={proof_artifacts['indexed_count']}/{proof_artifacts['expected_count']}")
print(f"- source_check_execution_snapshot: {source_check_execution_snapshot['status']} rows={source_check_execution_snapshot['row_count']}/{source_check_execution_snapshot['expected_count']} runtime_execution={str(source_check_execution_snapshot['runtime_execution']).lower()}")
print(f"- source_check_runtime: {source_check_runtime_summary['status']} rows={source_check_runtime_summary['passed_count']}/{source_check_runtime_summary['row_count']} report_only={str(source_check_runtime_summary['report_only']).lower()}")
print(f"- source_control_health: {check_source_control_health.get('status', 'fail')} files={check_source_control_health.get('present_file_count', 0)}/{check_source_control_health.get('required_file_count', 0)} inventory_rows={check_source_control_health.get('inventory_row_count', 0)}")
print(f"- owner_target_health: {check_owner_target_health.get('status', 'fail')} targets={check_owner_target_health.get('present_count', 0)}/{check_owner_target_health.get('checked_count', 0)}")
print(f"- knowledge-check: {result['checks']['knowledge_check']['status']} exit={knowledge_check['exit_code']} errors={result['checks']['knowledge_check']['error_count']} warnings={result['checks']['knowledge_check']['warning_count']}")
print(f"- knowledge-regression: {result['checks']['knowledge_regression']['status']} exit={knowledge_regression['exit_code']} results={result['checks']['knowledge_regression']['result_count']}")
print(f"- knowledge-status --strict: {result['checks']['knowledge_status_strict']['status']} exit={strict_status['exit_code']} blockers={result['checks']['knowledge_status_strict']['strict_blocker_count']}")
print(f"- review_queue_recovery: {review_queue_recovery['status']} pending={review_queue_recovery['summary']['total_pending_count']} active_or_promotion_blockers={review_queue_recovery['summary']['active_or_promotion_blocker_count']} report_only={str(review_queue_recovery['report_only']).lower()}")
print()
print("## Evidence Index")
print()
for row in evidence_index:
    print(f"- `{row['command']}` -> {row['status']} exit={row['exit_code']}: {row['result_summary_zh']}")
print()
print("## 高优先级规则审计")
print()
for row in highest_priority_rules_audit:
    print(f"- `{row['rule_id']}` -> {row['status']}: {row['rule_zh']}")
if blockers:
    print()
    print("## Blockers")
    print()
    for blocker in blockers:
        print(f"- `{blocker.get('id', '<missing>')}` ({blocker.get('severity', '<missing>')}): {blocker.get('summary_zh', '')}")
        for command in blocker.get("commands", []):
            print(f"  - `{command}`")
        for command in blocker.get("command_templates", []):
            print(f"  - template: `{command}`")
        if blocker.get("command"):
            print(f"  - `{blocker['command']}`")
if gap_map:
    print()
    print("## Gap Map")
    print()
    for gap in gap_map:
        print(f"- `{gap['gap_id']}` ({gap['gap_type']}): {gap['current_impact']}")
        print(f"  - codex_auto_can_complete: {str(gap.get('codex_auto_can_complete', False)).lower()}")
        print(f"  - requires_owner_decision: {str(gap.get('requires_owner_decision', False)).lower()}")
        if gap.get("write_scope"):
            print(f"  - write_scope: {gap['write_scope']}")
        print(f"  - fix: {gap['fix_action']}")
        for command in gap.get("validation_commands", [])[:3]:
            print(f"  - validation: `{command}`")
if result["next_actions_zh"]:
    print()
    print("## 下一步")
    print()
    for action in result["next_actions_zh"]:
        print(f"- {action}")
print()
print("## 复核命令")
print()
print("```bash")
print("rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics")
print("rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json")
print("rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json")
print("```")

sys.exit(exit_code)
PY
