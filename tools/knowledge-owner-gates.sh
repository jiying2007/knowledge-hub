#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Print a read-only owner-gate board from owner decision worksheets.")
parser.add_argument("--json", action="store_true")
parser.add_argument("--source-id", default="")
parser.add_argument("--status", choices=["all", "open", "resolved"], default="open")
args = parser.parse_args(argv)

errors = []

def load_jsonl(path):
    rows = []
    if not path.exists():
        errors.append(f"missing {path.relative_to(root)}")
        return rows
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

def is_resolved(row):
    state_text = " ".join(
        str(row.get(field, ""))
        for field in ["worksheet_status", "row_status", "status", "default_state"]
    ).lower()
    has_owner_decision = any(
        row.get(field)
        for field in ["owner_decision", "target_decision", "reviewed_by", "reviewed_at"]
    )
    return has_owner_decision and any(token in state_text for token in ["resolved", "owner-approved", "approved", "closed"])

items = load_jsonl(root / "registry" / "items.jsonl")
items_by_source_path = {}
active_by_source_path = {}
for item in items:
    source = item.get("source") if isinstance(item.get("source"), dict) else {}
    source_id = source.get("source_id")
    source_path = source.get("source_path")
    if not source_id or not source_path:
        continue
    key = (source_id, source_path)
    item_ref = {
        "id": item.get("id", ""),
        "status": item.get("status", ""),
        "path": item.get("path", ""),
        "review_status": item.get("review_status", ""),
    }
    items_by_source_path.setdefault(key, []).append(item_ref)
    if item.get("status") == "active":
        active_by_source_path.setdefault(key, []).append(item_ref)

worksheet_paths = sorted((root / "artifacts" / "manifests").glob("*owner-decision-worksheets-*.jsonl"))
if not worksheet_paths:
    errors.append("missing artifacts/manifests/*owner-decision-worksheets-*.jsonl")

rows = []
for worksheet_path in worksheet_paths:
    for row in load_jsonl(worksheet_path):
        source_id = str(row.get("source_id", ""))
        source_path = str(row.get("source_path", ""))
        if args.source_id and source_id != args.source_id:
            continue
        key = (source_id, source_path)
        resolved = is_resolved(row)
        row_status = "resolved" if resolved else "open"
        if args.status != "all" and row_status != args.status:
            continue
        rows.append(
            {
                "id": row.get("id", ""),
                "source_id": source_id,
                "source_path": source_path,
                "owner": row.get("owner_required") or row.get("owner_candidate") or "",
                "status": row_status,
                "worksheet_status": row.get("worksheet_status") or row.get("status") or row.get("default_state") or "",
                "decision_options": row.get("decision_options", []),
                "required_owner_fields": row.get("required_owner_fields", []),
                "must_not": row.get("must_not", []),
                "review_after": row.get("review_after", ""),
                "worksheet": str(worksheet_path.relative_to(root)),
                "registry_items": items_by_source_path.get(key, []),
                "active_registry_items": active_by_source_path.get(key, []),
            }
        )

open_count = sum(1 for row in rows if row["status"] == "open")
resolved_count = sum(1 for row in rows if row["status"] == "resolved")
active_exposure_count = sum(len(row["active_registry_items"]) for row in rows)

result = {
    "status": "blocked" if errors else "ok",
    "root": str(root),
    "read_only": True,
    "source_id": args.source_id,
    "filter_status": args.status,
    "worksheet_count": len(worksheet_paths),
    "row_count": len(rows),
    "open_count": open_count,
    "resolved_count": resolved_count,
    "active_exposure_count": active_exposure_count,
    "errors": errors,
    "rows": rows,
}

if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1 if errors else 0)

print("# Knowledge Owner Gates")
print()
print("本命令只读汇总 owner decision worksheets，不创建、不修改、不提交、不提升任何文件。")
print()
print(f"- status: {result['status']}")
print(f"- worksheets: {len(worksheet_paths)}")
print(f"- rows: {len(rows)}")
print(f"- open: {open_count}")
print(f"- resolved: {resolved_count}")
print(f"- active exposure: {active_exposure_count}")
if args.source_id:
    print(f"- source_id: {args.source_id}")
print(f"- filter: {args.status}")
for error in errors:
    print(f"- ERROR: {error}")

for row in rows:
    active_marker = "YES" if row["active_registry_items"] else "no"
    print()
    print(f"## {row['source_path'] or row['id']}")
    print()
    print(f"- id: `{row['id']}`")
    print(f"- source_id: `{row['source_id']}`")
    print(f"- owner: {row['owner'] or '<missing-owner>'}")
    print(f"- status: {row['status']} ({row['worksheet_status'] or '<missing-worksheet-status>'})")
    print(f"- review_after: {row['review_after'] or '<missing-review_after>'}")
    print(f"- active exposure: {active_marker}")
    if row["decision_options"]:
        print(f"- decision_options: {', '.join(str(item) for item in row['decision_options'])}")
    if row["required_owner_fields"]:
        print(f"- required_owner_fields: {', '.join(str(item) for item in row['required_owner_fields'][:8])}")
    if row["must_not"]:
        print(f"- must_not: {', '.join(str(item) for item in row['must_not'][:5])}")
    if row["registry_items"]:
        print("- registry_items:")
        for item in row["registry_items"]:
            print(
                f"  - `{item['id']}` status={item['status'] or '<missing-status>'} "
                f"path={item['path'] or '<missing-path>'}"
            )

print()
print("## 验证")
print()
print("```bash")
print("rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics")
print("```")

sys.exit(1 if errors else 0)
PY
