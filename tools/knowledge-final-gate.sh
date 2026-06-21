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
args = parser.parse_args(argv)

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

knowledge_check = run_json(["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
git_diff_check = run_text(["rtk", "git", "diff", "--check"])
if os.environ.get("KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION") == "1":
    knowledge_regression = {
        "command": "rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json",
        "exit_code": 0,
        "payload": {"status": "pass", "result_count": 0, "results": [], "skipped_for_self_test": True},
        "parse_error": "",
        "stderr": "",
    }
else:
    knowledge_regression = run_json(["rtk", "bash", "tools/knowledge-regression.sh", "--json"])
strict_status = run_json(["rtk", "bash", "tools/knowledge-status.sh", "--strict", "--json"])

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
    blockers.append({
        "id": "knowledge-check-failed",
        "severity": "blocker",
        "count": len(check_payload.get("errors", [])),
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
    return {
        "gap_id": blocker_id,
        "gap_type": "owner-review" if is_owner_gate else "environment" if is_environment else "final-gate",
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

gap_map = [blocker_to_gap(blocker) for blocker in blockers]
only_owner_review_blockers = bool(blockers) and all(item.get("severity") == "owner-review" for item in blockers)
core_checks_pass = (
    not knowledge_check["parse_error"]
    and knowledge_check["exit_code"] == 0
    and git_diff_check["exit_code"] == 0
    and not knowledge_regression["parse_error"]
    and knowledge_regression["exit_code"] == 0
)
owner_payload = strict_payload.get("owner_gates", {}) if isinstance(strict_payload, dict) else {}
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
level1_status = (
    "complete-except-owner-review"
    if core_checks_pass
    and str(owner_payload.get("owner_ready_package_coverage", "")) == "7/7"
    and int(owner_payload.get("open_count", 0) or 0) == 7
    and int(owner_payload.get("active_exposure_count", 0) or 0) == 0
    and bool(pcr02_docs_coverage)
    else "needs-fix"
)
level2_status = "complete" if not missing_level2_sources and not missing_level2_coverage else "needs-fix"
level3_status = (
    "complete"
    if source_registry_ids and not missing_registered_coverage and not missing_source_final_state_fields
    else "needs-fix"
)
final_state_audit = {
    "level1_pcr02_docs": {
        "status": level1_status,
        "source_id": "pcr02-project-docs",
        "coverage_status": str(pcr02_docs_coverage.get("status", "")),
        "owner_gate_open_count": int(owner_payload.get("open_count", 0) or 0),
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
        "missing_coverage_ids": missing_registered_coverage,
        "missing_final_state_fields": missing_source_final_state_fields,
        "evidence_refs": [
            "registry/sources.json",
            latest_coverage_manifest,
            "tools/knowledge-check.sh --dry-run --json --diagnostics",
        ],
        "summary_zh": "registry/sources.json 中 registered source 已由最新 source coverage manifest 覆盖，且 source registry 终态字段已补齐。",
    },
}

result = {
    "schema_version": 1,
    "root": str(root),
    "read_only": True,
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
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
        "summary_zh": (
            "Codex 自动治理已闭环；剩余事项是人工 owner decision，不能由 Codex 代签。"
            if automatic_governance_status == "complete-except-owner-review"
            else "终态完全通过。"
            if automatic_governance_status == "complete"
            else "仍存在非 owner 的自动治理缺口，需要先修复。"
        ),
    },
    "final_state_audit": final_state_audit,
    "checks": {
        "knowledge_check": {
            "exit_code": knowledge_check["exit_code"],
            "status": knowledge_check["payload"].get("status", "<missing>"),
            "error_count": len(knowledge_check["payload"].get("errors", [])),
            "warning_count": len(knowledge_check["payload"].get("warnings", [])),
            "parse_error": knowledge_check["parse_error"],
        },
        "knowledge_regression": {
            "exit_code": knowledge_regression["exit_code"],
            "status": knowledge_regression["payload"].get("status", "<missing>"),
            "result_count": knowledge_regression["payload"].get("result_count", 0),
            "skipped_for_self_test": bool(knowledge_regression["payload"].get("skipped_for_self_test", False)),
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
