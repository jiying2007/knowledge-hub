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
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(
    prog="knowledge-reviewing-triage.sh",
    description="Summarize reviewing Knowledge Hub items for periodic triage.",
)
parser.add_argument("--json", action="store_true", help="Print JSON output.")
parser.add_argument("--as-of", default=dt.date.today().isoformat(), metavar="YYYY-MM-DD")
parser.add_argument("--window-days", type=int, default=30, help="Near-due review_after window.")
parser.add_argument("--limit", type=int, default=50, help="Maximum reviewing rows to include.")
args = parser.parse_args(argv)

try:
    as_of = dt.date.fromisoformat(args.as_of)
except ValueError:
    parser.error("--as-of must be YYYY-MM-DD")
if args.window_days < 0:
    parser.error("--window-days must be >= 0")
if args.limit < 1:
    parser.error("--limit must be >= 1")


def load_items():
    rows = []
    for line_no, line in enumerate((root / "registry" / "items.jsonl").read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"registry/items.jsonl:{line_no}: invalid JSON: {exc}") from exc
    return rows


def bucket_for(row):
    item_id = row.get("id", "")
    domain = row.get("domain", "")
    kind = row.get("kind", "")
    tags = set(row.get("tags", []) or [])
    if domain == "codex" and ("codex-archive" in tags or "archive" in item_id or "tombstone" in tags):
        return "codex-archive-provenance"
    if domain == "codex":
        return "codex-runtime-governance"
    if domain == "projects/pcr02" and kind == "decision":
        return "pcr02-decision-candidate"
    if domain == "projects/pcr02":
        return "pcr02-reviewing-record"
    return domain or "uncategorized"


def action_for(row):
    tags = set(row.get("tags", []) or [])
    if row.get("decision_status") == "candidate" or "decision-candidate" in tags:
        return "owner-review-and-validation"
    if "manual-validation-pending" in tags:
        return "evidence-needed"
    if "archive-ready" in tags:
        return "archive-ready-check"
    if row.get("generated_by_ai") and not row.get("human_reviewed_by"):
        return "human-review-needed"
    return "keep-reviewing"


def parse_date(value):
    try:
        return dt.date.fromisoformat(value or "")
    except ValueError:
        return None


items = [row for row in load_items() if row.get("status") == "reviewing"]
window_end = as_of + dt.timedelta(days=args.window_days)
by_bucket = collections.Counter(bucket_for(row) for row in items)
by_action = collections.Counter(action_for(row) for row in items)
near_due = []
for row in items:
    review_after = parse_date(row.get("review_after", ""))
    if review_after and review_after <= window_end:
        near_due.append(row)

rows = []
for row in sorted(items, key=lambda item: (item.get("review_after", ""), item.get("domain", ""), item.get("id", ""))):
    rows.append(
        {
            "id": row.get("id", ""),
            "title": row.get("title", ""),
            "domain": row.get("domain", ""),
            "kind": row.get("kind", ""),
            "owner": row.get("owner", ""),
            "review_after": row.get("review_after", ""),
            "bucket": bucket_for(row),
            "recommended_action": action_for(row),
            "promotion": row.get("promotion", ""),
            "decision_status": row.get("decision_status", ""),
            "path": row.get("path", ""),
        }
    )

output = {
    "schema_version": 1,
    "read_only": True,
    "report_only": True,
    "as_of": args.as_of,
    "window_days": args.window_days,
    "reviewing_count": len(items),
    "near_due_count": len(near_due),
    "by_bucket": dict(sorted(by_bucket.items())),
    "by_recommended_action": dict(sorted(by_action.items())),
    "items": rows[: args.limit],
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
    print("# Knowledge Hub Reviewing Triage")
    print()
    print(f"- as_of: {output['as_of']}")
    print(f"- reviewing: {output['reviewing_count']}")
    print(f"- near_due: {output['near_due_count']}")
    print(f"- by_bucket: {output['by_bucket']}")
    print(f"- by_action: {output['by_recommended_action']}")
    for row in output["items"]:
        print(f"- {row['review_after']}: `{row['id']}` [{row['bucket']}] {row['recommended_action']}")
PY
