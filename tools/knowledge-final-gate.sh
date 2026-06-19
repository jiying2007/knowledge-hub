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

knowledge_check = run_json(["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
if os.environ.get("KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION") == "1":
    knowledge_regression = {
        "command": "rtk bash tools/knowledge-regression.sh --json",
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

if knowledge_regression["parse_error"]:
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

result = {
    "schema_version": 1,
    "root": str(root),
    "read_only": True,
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "final_status": final_status,
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
        "knowledge_status_strict": {
            "exit_code": strict_status["exit_code"],
            "status": strict_payload.get("status", "<missing>"),
            "strict_blocker_count": len(strict_payload.get("strict_blockers", [])),
            "parse_error": strict_status["parse_error"],
        },
    },
    "blockers": blockers,
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
        if blocker.get("command"):
            print(f"  - `{blocker['command']}`")
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
print("rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics")
print("rtk bash tools/knowledge-regression.sh --json")
print("rtk bash tools/knowledge-status.sh --strict --json")
print("```")

sys.exit(exit_code)
PY
