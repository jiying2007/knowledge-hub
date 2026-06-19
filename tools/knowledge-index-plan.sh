#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import collections
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Print a read-only plan for core Knowledge Hub indexes from registry/items.jsonl.")
parser.add_argument("--section", choices=["all", "owner", "review-date", "status"], default="all")
parser.add_argument("--json", action="store_true")
args = parser.parse_args(argv)

items_path = root / "registry" / "items.jsonl"
items = []
errors = []

try:
    for line_no, line in enumerate(items_path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"registry/items.jsonl:{line_no}: {exc}")
            continue
        items.append(item)
except Exception as exc:
    errors.append(f"cannot read registry/items.jsonl: {exc}")

by_owner = collections.defaultdict(list)
by_review_date = collections.defaultdict(list)
by_status = collections.defaultdict(list)

for item in items:
    item_id = str(item.get("id", ""))
    if not item_id:
        continue
    by_owner[str(item.get("owner", ""))].append(item_id)
    by_review_date[str(item.get("review_after", ""))].append(item_id)
    by_status[str(item.get("status", ""))].append(item_id)

status_order = ["active", "reviewing", "archived"]

result = {
    "status": "planned" if not errors else "blocked",
    "root": str(root),
    "item_count": len(items),
    "section": args.section,
    "read_only": True,
    "errors": errors,
    "indexes": {
        "by_owner": dict(sorted(by_owner.items())),
        "by_review_date": dict(sorted(by_review_date.items())),
        "by_status": {status: by_status.get(status, []) for status in status_order if status in by_status},
    },
}

if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1 if errors else 0)

print("# Knowledge Index Plan")
print()
print("本命令只读生成核心索引视图，不创建、不修改、不提交任何文件。")
print()
print(f"- items: {len(items)}")
print(f"- section: {args.section}")
print(f"- status: {result['status']}")
for error in errors:
    print(f"- ERROR: {error}")

def print_owner():
    print()
    print("## By Owner")
    for owner, ids in sorted(by_owner.items()):
        owner_label = owner or "<missing-owner>"
        print()
        print(f"### {owner_label}")
        for item_id in ids:
            print(f"- `{item_id}`")

def print_review_date():
    print()
    print("## By Review Date")
    for review_after, ids in sorted(by_review_date.items()):
        date_label = review_after or "<missing-review_after>"
        for item_id in ids:
            print(f"- {date_label}: `{item_id}`")

def print_status():
    print()
    print("## By Status")
    for status in status_order:
        ids = by_status.get(status, [])
        if ids:
            joined = ", ".join(f"`{item_id}`" for item_id in ids)
            print(f"- {status}: {joined}")
    extra_statuses = sorted(status for status in by_status if status not in status_order)
    if extra_statuses:
        print()
        print("### Non-canonical Status Values")
        for status in extra_statuses:
            joined = ", ".join(f"`{item_id}`" for item_id in by_status[status])
            print(f"- {status or '<missing-status>'}: {joined}")

if args.section in {"all", "owner"}:
    print_owner()
if args.section in {"all", "review-date"}:
    print_review_date()
if args.section in {"all", "status"}:
    print_status()

print()
print("## 验证")
print()
print("```bash")
print("rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics")
print("```")

sys.exit(1 if errors else 0)
PY
