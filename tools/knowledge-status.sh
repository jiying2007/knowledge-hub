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
import shlex
import subprocess
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Print a read-only Knowledge Hub status dashboard.")
parser.add_argument("--json", action="store_true")
parser.add_argument("--strict", action="store_true", help="Return non-zero unless the final status is ok.")
args = parser.parse_args(argv)

today = dt.date.today()
errors = []

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
    if completed.stdout.strip():
        try:
            payload = json.loads(completed.stdout)
        except Exception as exc:
            errors.append(f"cannot parse {' '.join(command)} output: {exc}")
    else:
        errors.append(f"{' '.join(command)} returned no JSON output")
    return {
        "command": command,
        "exit_code": completed.returncode,
        "payload": payload,
        "stderr": completed.stderr.strip(),
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

knowledge_check = run_json(["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
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
coverage_paths = sorted((root / "artifacts" / "manifests").glob("knowledge-hub-source-coverage-closeout-*.jsonl"))
if coverage_paths:
    latest_source_coverage = str(coverage_paths[-1].relative_to(root))

owner_payload = owner_gates["payload"]
check_payload = knowledge_check["payload"]
active_exposure_count = int(owner_payload.get("active_exposure_count", 0) or 0)
open_owner_gate_count = int(owner_payload.get("open_count", 0) or 0)
owner_rows = owner_payload.get("rows", [])
open_owner_rows = sorted(
    [row for row in owner_rows if row.get("status") == "open"],
    key=lambda row: (
        str(row.get("review_after", "") or "9999-12-31"),
        str(row.get("id", "")),
    ),
)
next_owner_gate = {}
summary_commands = []
if open_owner_rows:
    for source_id in sorted({str(row.get("source_id", "")) for row in open_owner_rows if row.get("source_id")}):
        summary_command = [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            source_id,
            "--summary",
        ]
        summary_commands.append(" ".join(shlex.quote(str(part)) for part in summary_command))
    first_open = open_owner_rows[0]
    next_open_command = [
        "rtk",
        "bash",
        "tools/knowledge-owner-gates.sh",
        "--source-id",
        first_open.get("source_id", ""),
        "--next-open",
        "--checklist",
        "--forms",
    ]
    focus_command = [
        "rtk",
        "bash",
        "tools/knowledge-owner-gates.sh",
        "--source-id",
        first_open.get("source_id", ""),
        "--worksheet-id",
        first_open.get("id", ""),
        "--checklist",
        "--forms",
    ]
    next_owner_gate = {
        "worksheet_id": first_open.get("id", ""),
        "source_id": first_open.get("source_id", ""),
        "source_path": first_open.get("source_path", ""),
        "owner": first_open.get("owner", ""),
        "review_after": first_open.get("review_after", ""),
        "selection_order": "review_after, worksheet_id",
        "next_open_command": " ".join(shlex.quote(str(part)) for part in next_open_command),
        "focus_command": " ".join(shlex.quote(str(part)) for part in focus_command),
    }

if errors:
    status = "blocked"
elif knowledge_check["exit_code"] != 0 or active_exposure_count:
    status = "needs-fix"
elif open_owner_gate_count:
    status = "needs-owner-review"
else:
    status = "ok"

exit_code = 1 if status in {"blocked", "needs-fix"} or (args.strict and status != "ok") else 0

next_actions = []
if knowledge_check["exit_code"] != 0:
    next_actions.append("先按 knowledge-check diagnostics 的 action_zh 修复阻断错误。")
if active_exposure_count:
    next_actions.append("立即移除 owner-gated active exposure，owner 决策闭环前不得 active。")
if open_owner_gate_count:
    if summary_commands:
        next_actions.append(
            "先查看 owner gate 总览以分派全部 open gate；运行："
            f"{summary_commands[0]}。"
        )
    if next_owner_gate:
        next_actions.append(
            "继续处理 owner decision worksheet；下一条是 "
            f"{next_owner_gate['worksheet_id']} ({next_owner_gate['source_path']})；运行："
            f"{next_owner_gate['next_open_command']}。"
        )
    else:
        next_actions.append("继续处理 owner decision worksheet；本状态表示语义决策未闭环，不是工具失败。")
if stale_items:
    next_actions.append("复核 review_after 已过期的 active/reviewing 条目。")
if not next_actions:
    next_actions.append("控制面无阻断；新增内容仍按 README 人工最短路径登记、索引和验证。")

result = {
    "schema_version": 1,
    "root": str(root),
    "read_only": True,
    "strict": args.strict,
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "status": status,
    "today": today.isoformat(),
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
    },
    "sources": {
        "registered_count": len(sources),
        "latest_coverage_manifest": latest_source_coverage,
    },
    "migrations": {
        "record_count": len(migrations),
        "by_status": count_by(migrations, "status"),
    },
    "owner_gates": {
        "exit_code": owner_gates["exit_code"],
        "worksheet_count": owner_payload.get("worksheet_count", 0),
        "row_count": owner_payload.get("row_count", 0),
        "open_count": open_owner_gate_count,
        "resolved_count": owner_payload.get("resolved_count", 0),
        "active_exposure_count": active_exposure_count,
        "summary_commands": summary_commands,
        "next_open": next_owner_gate,
    },
    "errors": errors,
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
if latest_source_coverage:
    print(f"- source coverage: `{latest_source_coverage}`")
print()
print("## Registry")
print()
for key, value in result["registry"]["by_status"].items():
    print(f"- status `{key}`: {value}")
print(f"- stale review_after: {len(stale_items)}")
if stale_items:
    for item in stale_items[:10]:
        print(f"  - `{item['id']}` status={item['status']} review_after={item['review_after']} owner={item['owner']}")
print()
print("## Owner Gates")
print()
print(f"- worksheets: {result['owner_gates']['worksheet_count']}")
print(f"- rows: {result['owner_gates']['row_count']}")
print(f"- open: {open_owner_gate_count}")
print(f"- resolved: {owner_payload.get('resolved_count', 0)}")
print(f"- active exposure: {active_exposure_count}")
if summary_commands:
    print("- summary commands:")
    for command in summary_commands:
        print(f"  - `{command}`")
if next_owner_gate:
    print(f"- next open: `{next_owner_gate['worksheet_id']}` ({next_owner_gate['source_path']})")
    print(f"- next-open command: `{next_owner_gate['next_open_command']}`")
    print(f"- focus command: `{next_owner_gate['focus_command']}`")
print()
print("## 下一步")
print()
for action in next_actions:
    print(f"- {action}")
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
print("rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics")
print("rtk bash tools/knowledge-owner-gates.sh --status all --json")
print("rtk bash tools/knowledge-status.sh --strict")
print("```")

sys.exit(exit_code)
PY
