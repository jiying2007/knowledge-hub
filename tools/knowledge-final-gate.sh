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
args = parser.parse_args(argv)

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
        "migration-record": "migration-record",
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
    blocker_id = str(blocker.get("id", "") or "")
    if blocker_id == "owner-gates-open":
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

def command_evidence_row(command, exit_code, status, result_summary_zh, evidence_path, layer, related_artifact, parse_error=""):
    return {
        "command": command,
        "exit_code": exit_code,
        "status": status,
        "result_summary_zh": result_summary_zh,
        "evidence_path": evidence_path,
        "layer": layer,
        "related_artifact": related_artifact,
        "parse_error": parse_error,
    }

knowledge_check = run_json(["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics", "--as-of", today.isoformat()])
git_diff_check = run_text(["rtk", "git", "diff", "--check"])
if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
    knowledge_regression = {
        "command": f"rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json --as-of {today.isoformat()}",
        "exit_code": 0,
        "payload": {
            "status": "pass",
            "result_count": 1,
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
        "command": f"rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json --as-of {today.isoformat()}",
        "exit_code": 0,
        "payload": {"status": "pass", "result_count": 0, "results": [], "skipped_for_self_test": True},
        "parse_error": "",
        "stderr": "",
    }
else:
    knowledge_regression = run_json(["rtk", "bash", "tools/knowledge-regression.sh", "--json", "--as-of", today.isoformat()])
strict_status = run_json(["rtk", "bash", "tools/knowledge-status.sh", "--strict", "--json", "--as-of", today.isoformat()])

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
            else "宿主临时空间或执行环境不足，当前无法形成可信终态回归证据。"
            if is_environment
            else "终态 gate 存在非 owner blocker，必须先修复工具、registry、index、manifest 或回归。"
        ),
        "codex_auto_can_complete": False if (is_owner_gate or is_environment) else True,
        "requires_owner_decision": bool(is_owner_gate),
        "fix_action": (
            "人工 owner 填写 owner decision JSONL 后，先运行 validate-forms，再生成 landing-plan。"
            if is_owner_gate
            else "释放 /tmp 或配置可用临时空间后，重跑 knowledge-regression 和 knowledge-final-gate。"
            if is_environment
            else "按 blocker command 修复对应门禁，然后重跑 knowledge-final-gate。"
        ),
        "write_scope": (
            "owner decision JSONL 由人工提供；Codex 只允许在校验通过后按 landing-plan 落地。"
            if is_owner_gate
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
)
owner_payload = strict_payload.get("owner_gates", {}) if isinstance(strict_payload, dict) else {}
strict_blocker_ids = [
    str(blocker.get("id", ""))
    for blocker in strict_payload.get("strict_blockers", [])
    if isinstance(blocker, dict) and blocker.get("id")
]
status_owner_blocker_source = strict_payload.get("owner_blocker_source", {})
check_source_coverage_health = knowledge_check["payload"].get("source_coverage_health", {})
check_source_coverage_selection = knowledge_check["payload"].get("source_coverage_selection", {})
check_source_check_health = knowledge_check["payload"].get("source_check_health", {})
check_boundary_health = knowledge_check["payload"].get("boundary_health", {})
source_registry = load_json(root / "registry" / "sources.json").get("sources", [])
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
    "migration_strategy",
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
            "source_root": "registry/sources.json",
            "evidence": f"PCR02 Level 2 source {source_id} is missing from registry/sources.json.",
            "current_impact": "PCR02 候选 source 不能从 source registry 恢复，Level 2 source coverage 不完整。",
            "codex_auto_can_complete": True,
            "requires_owner_decision": False,
            "fix_action": "补 registry/sources.json source object，并同步 by-source、source coverage manifest 和 registry/index 证据。",
            "write_scope": "registry/sources.json、indexes/by-source.md、artifacts/manifests/*source-coverage*.jsonl 和对应 manifest/registry/index。",
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
            "write_scope": "artifacts/manifests/*source-coverage*.jsonl、indexes/by-source.md、必要 registry/migration/index。",
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
            "current_impact": "source registry 不能独立说明 owner、review_after、migration_strategy、final_disposition 或 check/no-check 边界。",
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
    "complete-except-owner-review"
    if core_checks_pass
    and str(owner_payload.get("owner_ready_package_coverage", "")) == "7/7"
    and int(owner_payload.get("open_count", 0) or 0) == 7
    and int(owner_payload.get("active_exposure_count", 0) or 0) == 0
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
    else "needs-fix"
)
final_state_audit = {
    "level1_pcr02_docs": {
        "status": level1_status,
        "source_id": "pcr02-project-docs",
        "coverage_status": str(pcr02_docs_coverage.get("status", "")),
        "expected_owner_gate_count": 7,
        "expected_owner_gate_count_source": "artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl open rows with owner-ready package coverage",
        "worksheet_count": int(owner_payload.get("worksheet_count", 0) or 0),
        "worksheet_row_count": int(owner_payload.get("row_count", 0) or 0),
        "owner_gate_open_count": int(owner_payload.get("open_count", 0) or 0),
        "owner_gate_count_matches_expected": int(owner_payload.get("open_count", 0) or 0) == 7,
        "owner_ready_package_count": int(owner_payload.get("owner_ready_package_count", 0) or 0),
        "owner_ready_expected_count": int(owner_payload.get("row_count", 0) or 0),
        "owner_ready_package_coverage": str(owner_payload.get("owner_ready_package_coverage", "")),
        "active_exposure_count": int(owner_payload.get("active_exposure_count", 0) or 0),
        "no_owner_decision_generated": only_owner_review_blockers,
        "evidence_refs": [
            latest_coverage_manifest,
            "artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl",
            "artifacts/manifests/pcr02-owner-decision-intake-execution-20260620.md",
            "tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json",
        ],
        "summary_zh": "PCR02 docs 控制面已闭合；剩余 7 个 owner-gated docs 只能由 owner 人工签收。",
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
        "evidence_refs": [
            "registry/sources.json",
            latest_coverage_manifest,
            "artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.md",
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
        "evidence_refs": [
            "registry/sources.json",
            latest_coverage_manifest,
            "tools/knowledge-check.sh --dry-run --json --diagnostics",
        ],
        "summary_zh": (
            "registry/sources.json 中 registered source 已由最新 source coverage manifest 覆盖，且 source registry 终态字段已补齐。"
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
            "knowledge-status --strict 仅剩 owner-gates-open；这是人工 owner decision blocker，不是工具失败。"
            if only_owner_review_blockers
            else "knowledge-status --strict 通过。"
            if not strict_status["parse_error"] and strict_status["exit_code"] == 0
            else "knowledge-status --strict 存在非 owner blocker 或 JSON 解析问题。"
        ),
        "runtime:checks.knowledge_status_strict",
        "final-gate",
        "knowledge-status",
        strict_status["parse_error"],
    ),
]
if status_owner_blocker_source:
    evidence_index.append(
        command_evidence_row(
            "runtime:automatic_governance.owner_blocker_source",
            0,
            "owner-review" if only_owner_review_blockers else "not-applicable",
            (
                "owner blocker provenance 已由 knowledge-status --strict 提供；owner gate 数量、owner-ready 覆盖和 active exposure 可追溯到 owner_gates 字段。"
                if only_owner_review_blockers
                else "当前终态不是纯 owner-review blocker；owner blocker provenance 仅作为辅助上下文。"
            ),
            "runtime:automatic_governance.owner_blocker_source",
            "final-gate",
            "owner-blocker-provenance",
        )
    )

result = {
    "schema_version": 1,
    "root": str(root),
    "read_only": True,
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "today": today.isoformat(),
    "as_of_source": today_source,
    "final_status": final_status,
    "automatic_governance": {
        "status": automatic_governance_status,
        "complete": automatic_governance_complete,
        "core_checks_pass": core_checks_pass,
        "only_owner_review_blockers": only_owner_review_blockers,
        "remaining_owner_gate_count": int(owner_payload.get("open_count", 0) or 0),
        "owner_ready_package_coverage": str(owner_payload.get("owner_ready_package_coverage", "")),
        "active_exposure_count": int(owner_payload.get("active_exposure_count", 0) or 0),
        "no_owner_decision_generated": only_owner_review_blockers,
        "owner_blocker_source": status_owner_blocker_source or {
            "status_source": "knowledge-status --strict",
            "strict_blocker_ids": strict_blocker_ids,
            "owner_gate_open_count_field": "owner_gates.open_count",
            "owner_ready_package_coverage_field": "owner_gates.owner_ready_package_coverage",
            "active_exposure_count_field": "owner_gates.active_exposure_count",
            "notes_zh": "owner gate 数量、owner-ready 覆盖和 active exposure 均来自 strict status 的 owner_gates；final gate 不自行关闭或生成 owner decision。",
        },
        "summary_zh": (
            "Codex 自动治理已闭环；剩余事项是人工 owner decision，不能由 Codex 代签。"
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
print(f"- automatic_governance: {result['automatic_governance']['status']}")
print(f"- level1_pcr02_docs: {final_state_audit['level1_pcr02_docs']['status']}")
print(f"- level2_pcr02_candidate_sources: {final_state_audit['level2_pcr02_candidate_sources']['status']}")
print(f"- level3_registered_sources: {final_state_audit['level3_registered_sources']['status']}")
print(f"- knowledge-check: {result['checks']['knowledge_check']['status']} exit={knowledge_check['exit_code']} errors={result['checks']['knowledge_check']['error_count']} warnings={result['checks']['knowledge_check']['warning_count']}")
print(f"- knowledge-regression: {result['checks']['knowledge_regression']['status']} exit={knowledge_regression['exit_code']} results={result['checks']['knowledge_regression']['result_count']}")
print(f"- knowledge-status --strict: {result['checks']['knowledge_status_strict']['status']} exit={strict_status['exit_code']} blockers={result['checks']['knowledge_status_strict']['strict_blocker_count']}")
print()
print("## Evidence Index")
print()
for row in evidence_index:
    print(f"- `{row['command']}` -> {row['status']} exit={row['exit_code']}: {row['result_summary_zh']}")
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
        print(f"  - fix: {gap['fix_action']}")
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
