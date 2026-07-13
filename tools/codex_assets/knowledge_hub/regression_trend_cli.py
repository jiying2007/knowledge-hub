import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(
    prog="knowledge-regression-trend.sh",
    description="Summarize Knowledge Hub regression output into a compact performance trend record.",
)
parser.add_argument("--json", action="store_true", help="Print JSON output.")
parser.add_argument("--from-json", default="", help="Read an existing knowledge-regression JSON output.")
parser.add_argument("--run", action="store_true", help="Run knowledge-regression and summarize the result.")
parser.add_argument("--suite", default="full", choices=["quick", "full"])
parser.add_argument("--as-of", default=dt.date.today().isoformat(), metavar="YYYY-MM-DD")
parser.add_argument("--top", type=int, default=10, help="Number of slowest results to include.")
args = parser.parse_args(argv)

try:
    dt.date.fromisoformat(args.as_of)
except ValueError:
    parser.error("--as-of must be YYYY-MM-DD")
if args.top < 1:
    parser.error("--top must be >= 1")
if bool(args.from_json) == bool(args.run):
    parser.error("exactly one of --from-json or --run is required")


def parse_payload(text):
    try:
        return json.loads(text), ""
    except Exception as exc:
        return {}, str(exc)


def display_path(path):
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


source = {}
if args.from_json:
    path = pathlib.Path(args.from_json)
    if not path.is_absolute():
        path = root / path
    payload, parse_error = parse_payload(path.read_text())
    source = {
        "mode": "from-json",
        "path": display_path(path),
        "exit_code": 0 if not parse_error else 1,
        "parse_error": parse_error,
    }
else:
    command = [
        "rtk",
        "bash",
        "tools/knowledge-regression.sh",
        "--json",
        "--suite",
        args.suite,
        "--as-of",
        args.as_of,
    ]
    completed = subprocess.run(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload, parse_error = parse_payload(completed.stdout)
    source = {
        "mode": "run",
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "parse_error": parse_error,
        "stderr_sample": completed.stderr[:500],
    }

results = payload.get("results", []) if isinstance(payload, dict) else []
failed_ids = [row.get("id", "") for row in results if row.get("status") != "pass"]
slowest = payload.get("slowest_results", []) if isinstance(payload, dict) else []
output = {
    "schema_version": 1,
    "read_only": True,
    "as_of": args.as_of,
    "source": source,
    "regression_status": payload.get("status", "unparseable") if isinstance(payload, dict) else "unparseable",
    "suite": payload.get("suite", args.suite) if isinstance(payload, dict) else args.suite,
    "selected_test_count": payload.get("selected_test_count", 0) if isinstance(payload, dict) else 0,
    "full_test_count": payload.get("full_test_count", 0) if isinstance(payload, dict) else 0,
    "result_count": payload.get("result_count", len(results)) if isinstance(payload, dict) else 0,
    "full_result_count": payload.get("full_result_count", 0) if isinstance(payload, dict) else 0,
    "failed_count": len(failed_ids),
    "failed_ids": failed_ids,
    "slowest_results": slowest[: args.top],
    "notes_zh": "只生成压缩趋势摘要，不保存 full regression 原始 JSON，不修改 registry、owner gate、memory 或源项目。",
}

if args.json:
    print(json.dumps(output, ensure_ascii=False, indent=2))
else:
    print("# Knowledge Regression Trend")
    print()
    print(f"- status: {output['regression_status']}")
    print(f"- suite: {output['suite']}")
    print(f"- selected_test_count: {output['selected_test_count']}")
    print(f"- result_count: {output['result_count']}")
    print(f"- failed_count: {output['failed_count']}")
    for row in output["slowest_results"]:
        print(f"- {row.get('duration_sec', 0)}s `{row.get('id', '')}` {row.get('status', '')}")

if output["regression_status"] != "pass" or output["failed_count"]:
    raise SystemExit(1)

