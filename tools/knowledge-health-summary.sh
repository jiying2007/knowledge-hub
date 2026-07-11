#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(
    prog="knowledge-health-summary.sh",
    description="Print a concise Knowledge Hub health dashboard.",
)
parser.add_argument("--json", action="store_true", help="Print JSON output.")
parser.add_argument("--as-of", default=dt.date.today().isoformat(), metavar="YYYY-MM-DD")
parser.add_argument("--final-profile", default="mature", choices=["standard", "max-body", "mature"])
parser.add_argument(
    "--skip-final-gate",
    action="store_true",
    help="Skip the terminal final gate and report status dashboard only.",
)
args = parser.parse_args(argv)

try:
    dt.date.fromisoformat(args.as_of)
except ValueError:
    parser.error("--as-of must be YYYY-MM-DD")


def run_cmd(command):
    completed = subprocess.run(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    parsed = {}
    parse_error = ""
    if completed.stdout.strip():
        try:
            parsed = json.loads(completed.stdout)
        except Exception as exc:
            parse_error = str(exc)
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "parsed": parsed,
        "parse_error": parse_error,
    }


def load_registry_rows():
    rows = []
    items_path = root / "registry" / "items.jsonl"
    for line_no, line in enumerate(items_path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"registry/items.jsonl:{line_no}: invalid JSON: {exc}") from exc
    return rows


def count_registry(rows):
    by_status = {}
    summary_gap_by_status = {}
    for row in rows:
        status = row.get("status", "")
        by_status[status] = by_status.get(status, 0) + 1
        if not row.get("summary_zh"):
            summary_gap_by_status[status] = summary_gap_by_status.get(status, 0) + 1
    return {
        "item_count": len(rows),
        "by_status": dict(sorted(by_status.items())),
        "summary_gap_total": sum(summary_gap_by_status.values()),
        "summary_gap_by_status": dict(sorted(summary_gap_by_status.items())),
    }


registry = count_registry(load_registry_rows())
status_result = run_cmd(
    [
        "rtk",
        "bash",
        "tools/knowledge-status.sh",
        "--strict",
        "--json",
        "--as-of",
        args.as_of,
        "--final-profile",
        args.final_profile,
    ]
)
status_payload = status_result["parsed"] if isinstance(status_result["parsed"], dict) else {}

final_gate = {
    "skipped": True,
    "command": "",
    "exit_code": None,
    "final_status": "skipped",
    "parse_error": "",
}
if not args.skip_final_gate:
    final_result = run_cmd(
        [
            "rtk",
            "bash",
            "tools/knowledge-final-gate.sh",
            "--json",
            "--final-profile",
            args.final_profile,
            "--as-of",
            args.as_of,
        ]
    )
    final_payload = final_result["parsed"] if isinstance(final_result["parsed"], dict) else {}
    final_gate = {
        "skipped": False,
        "command": final_result["command"],
        "exit_code": final_result["exit_code"],
        "final_status": final_payload.get("final_status", "unparseable"),
        "parse_error": final_result["parse_error"],
        "blocker_count": len(final_payload.get("blockers", []) or []),
        "gap_count": len(final_payload.get("gap_map", []) or []),
    }

review_summary = status_payload.get("review_queues", {}).get("summary", {})
source_summary = status_payload.get("sources", {})
mature_audit = source_summary.get("mature_audit", {})
owner_gates = status_payload.get("owner_gates", {})

health_status = "ok"
if status_result["exit_code"] != 0 or status_result["parse_error"]:
    health_status = "needs-fix"
elif registry["summary_gap_total"]:
    health_status = "needs-fix"
elif not args.skip_final_gate and final_gate.get("final_status") != "ok":
    health_status = "needs-fix"

output = {
    "schema_version": 1,
    "read_only": True,
    "root": "~/knowledge-hub",
    "as_of": args.as_of,
    "final_profile": args.final_profile,
    "health_status": health_status,
    "registry": registry,
    "review_queue": {
        "pending_total": review_summary.get("total_pending_count", 0),
        "ai_generated_pending": review_summary.get("ai_generated_pending_count", 0),
        "external_source_pending": review_summary.get("external_source_pending_count", 0),
        "active_or_promotion_blocker_count": review_summary.get("active_or_promotion_blocker_count", 0),
    },
    "review_after": {
        "stale_item_count": status_payload.get("registry", {}).get("stale_review_after_count", 0),
        "stale_source_count": source_summary.get("stale_review_after_count", 0),
        "near_due_command": status_payload.get("registry", {}).get("review_after_near_due_command", ""),
    },
    "owner_gates": {
        "open_count": owner_gates.get("open_count", 0),
        "active_exposure_count": owner_gates.get("active_exposure_count", 0),
    },
    "mature_audit": {
        "status": mature_audit.get("status", ""),
        "blocker_count": mature_audit.get("blocker_count", 0),
        "reviewing_count": mature_audit.get("reviewing_count", 0),
        "reviewing_ratio": mature_audit.get("reviewing_ratio", 0),
    },
    "status_dashboard": {
        "command": status_result["command"],
        "exit_code": status_result["exit_code"],
        "status": status_payload.get("status", "unparseable"),
        "strict_blocker_count": len(status_payload.get("strict_blockers", []) or []),
        "parse_error": status_result["parse_error"],
    },
    "final_gate": final_gate,
    "must_not": [
        "不生成 owner decision",
        "不关闭 owner gate",
        "不提升 active",
        "不写 memory",
        "不修改源项目",
    ],
}

if args.json:
    print(json.dumps(output, ensure_ascii=False, indent=2))
else:
    print("# Knowledge Hub Health Summary")
    print()
    print(f"- health: {output['health_status']}")
    print(f"- as_of: {output['as_of']}")
    print(f"- items: {registry['item_count']} {registry['by_status']}")
    print(f"- summary_gap: {registry['summary_gap_total']} {registry['summary_gap_by_status']}")
    print(f"- review_queue_pending: {output['review_queue']['pending_total']}")
    print(
        "- stale_review_after: "
        f"items={output['review_after']['stale_item_count']} "
        f"sources={output['review_after']['stale_source_count']}"
    )
    print(
        "- mature: "
        f"status={output['mature_audit']['status']} "
        f"blockers={output['mature_audit']['blocker_count']} "
        f"reviewing={output['mature_audit']['reviewing_count']} "
        f"ratio={output['mature_audit']['reviewing_ratio']}"
    )
    print(
        "- final_gate: "
        f"status={output['final_gate']['final_status']} "
        f"exit={output['final_gate']['exit_code']}"
    )

sys.exit(0 if output["health_status"] == "ok" else 1)
PY
