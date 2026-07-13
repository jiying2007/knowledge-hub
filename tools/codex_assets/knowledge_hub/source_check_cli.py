import argparse
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

PCR02_LEVEL2_SOURCE_IDS = [
    "pcr02-project-tools",
    "pcr02-project-knowledge",
    "pcr02-product-test",
    "pcr02-project-scratch",
    "pcr02-project-root-artifacts",
    "pcr02-module-agent-rules",
    "pcr02-project-agent-config",
]

parser = argparse.ArgumentParser(
    description="Run report-only source availability checks for a small allowlisted scope."
)
parser.add_argument("--scope", choices=["pcr02-level2"], default="pcr02-level2")
parser.add_argument("--source-id", default="", metavar="SOURCE_ID")
parser.add_argument("--json", action="store_true")
parser.add_argument("--plan", action="store_true", help="Only print the allowlisted execution plan.")
parser.add_argument("--strict", action="store_true", help="Return non-zero when any selected source check fails.")
parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD", help="Record a fixed date in the report.")
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

def resolve_user_path(value):
    return pathlib.Path(str(value)).expanduser()

def load_sources():
    sources_path = root / "registry" / "sources.json"
    try:
        payload = json.loads(sources_path.read_text())
    except Exception as exc:
        return {}, [f"cannot read registry/sources.json: {exc}"]
    current_rows = payload.get("sources", [])
    try:
        retired_rows = [
            json.loads(line)
            for line in (root / "registry" / "retired-sources.jsonl").read_text().splitlines()
            if line.strip()
        ]
    except FileNotFoundError:
        retired_rows = []
    except Exception as exc:
        return {}, [f"cannot read registry/retired-sources.jsonl: {exc}"]
    if not isinstance(current_rows, list):
        return {}, ["registry/sources.json field sources must be a list"]
    rows = current_rows + retired_rows
    return {str(row.get("id", "")): row for row in rows if row.get("id")}, []

sources_by_id, errors = load_sources()
selected_ids = list(PCR02_LEVEL2_SOURCE_IDS)
if args.source_id:
    if args.source_id not in PCR02_LEVEL2_SOURCE_IDS:
        errors.append(f"source-id outside pcr02-level2 allowlist: {args.source_id}")
        selected_ids = []
    else:
        selected_ids = [args.source_id]

BASH_TEST_COMMAND_RE = re.compile(r"^rtk bash -lc 'test -(?P<kind>[df]) (?P<path>[^']+)'$")
RTK_TEST_COMMAND_RE = re.compile(r"^rtk test -(?P<kind>[df]) (?P<path>\S+)$")
BANNED_PATH_CHARS = set(";|&><`$*?[")

def resolve_check_path(value):
    raw = str(value)
    if raw.startswith("/") or raw.startswith("~/"):
        return pathlib.Path(raw).expanduser()
    return root / raw

def path_within_source(check_path, source_path):
    try:
        check_resolved = resolve_check_path(check_path).resolve()
        source_resolved = resolve_check_path(source_path).resolve()
    except Exception:
        return False
    return check_resolved == source_resolved or source_resolved in check_resolved.parents

def validate_check_target(check_path, source):
    if ".." in pathlib.PurePosixPath(check_path.replace("~/", "", 1)).parts:
        return "check target must not use parent traversal"
    if any(char in check_path for char in BANNED_PATH_CHARS):
        return "check target contains shell control, expansion or glob characters"
    if not (check_path.startswith("/") or check_path.startswith("~/")):
        try:
            resolved = resolve_check_path(check_path).resolve()
            root_resolved = root.resolve()
        except Exception:
            return "relative check target could not be resolved under the hub root"
        if resolved != root_resolved and root_resolved not in resolved.parents:
            return "relative check target must stay under the hub root"
    source_path = str(source.get("path", ""))
    if ".." in pathlib.PurePosixPath(source_path.replace("~/", "", 1)).parts:
        return "source registry path must not use parent traversal"
    if not path_within_source(check_path, source_path):
        return "check target must equal or stay under the registered source path"
    return ""

def parse_check_command(check):
    for command_re in (BASH_TEST_COMMAND_RE, RTK_TEST_COMMAND_RE):
        match = command_re.match(check)
        if match:
            return match
    return None

rows = []
for source_id in selected_ids:
    source = sources_by_id.get(source_id)
    if not source:
        rows.append(
            {
                "source_id": source_id,
                "status": "fail",
                "executed": False,
                "exit_code": None,
                "result": "missing-source-registry-row",
                "check_command": "",
                "primitive": "",
                "path": "",
                "reason_zh": "registry/sources.json 中缺少该 source。",
            }
        )
        continue
    check = str(source.get("check", ""))
    match = parse_check_command(check)
    if not match:
        rows.append(
            {
                "source_id": source_id,
                "status": "fail",
                "executed": False,
                "exit_code": None,
                "result": "unsupported-runtime-check",
                "check_command": check,
                "primitive": "",
                "path": display_path(source.get("path", "")),
                "reason_zh": "仅允许执行 registry 中形如 rtk test -d/-f <path> 或 rtk bash -lc 'test -d/-f <path>' 的只读存在性检查。",
            }
        )
        continue
    primitive = f"test -{match.group('kind')}"
    check_path = match.group("path")
    target_error = validate_check_target(check_path, source)
    if target_error:
        rows.append(
            {
                "source_id": source_id,
                "status": "fail",
                "executed": False,
                "exit_code": None,
                "result": "rejected-runtime-check",
                "check_command": check,
                "primitive": primitive,
                "path": display_path(check_path),
                "reason_zh": f"拒绝执行：{target_error}。",
            }
        )
        continue
    row = {
        "source_id": source_id,
        "status": "planned" if args.plan else "pending",
        "executed": False,
        "exit_code": None,
        "result": "planned" if args.plan else "",
        "check_command": check,
        "primitive": primitive,
        "path": display_path(check_path),
        "reason_zh": "只读路径存在性检查；不读取 source 正文。",
    }
    if not args.plan:
        execution_check_path = str(resolve_check_path(check_path))
        shell_payload = f"{primitive} {shlex.quote(execution_check_path)}"
        completed = subprocess.run(
            ["rtk", "bash", "-lc", shell_payload],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        row["executed"] = True
        row["exit_code"] = completed.returncode
        row["stdout"] = completed.stdout[:1000]
        row["stderr"] = completed.stderr[:1000]
        if completed.returncode == 0:
            row["status"] = "pass"
            row["result"] = "path-exists" if primitive == "test -d" else "file-exists"
        else:
            row["status"] = "fail"
            row["result"] = "path-missing-or-inaccessible"
    rows.append(row)

failed_rows = [row for row in rows if row.get("status") == "fail"]
unsupported_rows = [row for row in rows if row.get("result") == "unsupported-runtime-check"]
rejected_rows = [row for row in rows if row.get("result") == "rejected-runtime-check"]
missing_rows = [row for row in rows if row.get("result") == "missing-source-registry-row"]
executed_rows = [row for row in rows if row.get("executed") is True]
status = "fail" if errors or failed_rows else "planned" if args.plan else "pass"

output = {
    "schema_version": 1,
    "status": status,
    "root": display_path(root),
    "read_only": True,
    "report_only": True,
    "scope": args.scope,
    "source_id_filter": args.source_id,
    "today": today.isoformat(),
    "as_of_source": today_source,
    "plan_only": args.plan,
    "source_check_health_contract": "static-registry-only",
    "source_check_health_executed": False,
    "source_body_read": False,
    "owner_gate_mutation": False,
    "memory_write": False,
    "automation_write": False,
    "allowed_primitives": ["test -d", "test -f"],
    "expected_source_ids": PCR02_LEVEL2_SOURCE_IDS,
    "selected_source_ids": selected_ids,
    "row_count": len(rows),
    "executed_count": len(executed_rows),
    "passed_count": len([row for row in rows if row.get("status") == "pass"]),
    "failed_count": len(failed_rows),
    "unsupported_count": len(unsupported_rows),
    "rejected_count": len(rejected_rows),
    "missing_registry_count": len(missing_rows),
    "rows": rows,
    "errors": errors,
    "limitations_zh": "只证明路径或文件在执行时存在，不证明内容正确、语义可迁移、owner 已签收、owner gate 可关闭或 active promotion 可成立。",
    "must_not": [
        "不得把 path-exists 当作内容正确",
        "不得关闭 owner gate",
        "不得生成 owner decision",
        "不得修改源项目",
        "不得写 memory",
        "不得改变 knowledge-check 的 static-registry-only 契约",
    ],
}

if args.json:
    print(json.dumps(output, ensure_ascii=False, indent=2))
else:
    print("# Knowledge Source Check")
    print()
    print(f"- status: {status}")
    print(f"- scope: {args.scope}")
    print(f"- selected sources: {len(selected_ids)}")
    print(f"- executed: {len(executed_rows)}")
    print(f"- failed: {len(failed_rows)}")
    print("- mode: report-only")
    print("- source_check_health_contract: static-registry-only")
    print()
    for row in rows:
        exit_code = row.get("exit_code")
        exit_text = "-" if exit_code is None else str(exit_code)
        print(f"- {row.get('status')}: {row.get('source_id')} ({row.get('primitive') or 'unsupported'}, exit={exit_text}) {row.get('result')}")
    if errors:
        print()
        for error in errors:
            print(f"ERROR {error}")

exit_code = 0
if errors or unsupported_rows or rejected_rows or missing_rows:
    exit_code = 1
elif args.strict and failed_rows:
    exit_code = 1
sys.exit(exit_code)

