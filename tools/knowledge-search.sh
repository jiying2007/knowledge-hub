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

parser = argparse.ArgumentParser(description="Search Knowledge Hub and registered sources.")
parser.add_argument("query")
parser.add_argument("--json", action="store_true")
parser.add_argument("--limit", type=int, default=20)
parser.add_argument("--source", action="append", default=[], help="Physical scan source id, for example knowledge-hub or pcr02-project-docs.")
parser.add_argument("--owner", action="append", default=[], help="Filter local registered items by registry owner. Repeatable.")
parser.add_argument("--status", action="append", default=[], help="Filter local registered items by registry status. Repeatable.")
parser.add_argument("--kind", action="append", default=[], help="Filter local registered items by registry kind. Repeatable.")
parser.add_argument("--domain", action="append", default=[], help="Filter local registered items by registry domain prefix. Repeatable.")
parser.add_argument("--source-id", action="append", default=[], help="Filter local registered items by registry source.source_id. Repeatable.")
args = parser.parse_args(argv)

query = args.query.lower()

if args.limit < 1:
    parser.error("--limit must be >= 1")

allowed_statuses = {"draft", "active", "reviewing", "archived", "superseded", "rejected", "personal"}
allowed_kinds = {
    "standard",
    "runbook",
    "architecture",
    "decision",
    "project-current",
    "project-archive",
    "validation",
    "audit",
    "patent",
    "codex-session",
    "codex-workflow",
    "personal-note",
    "artifact-ref",
}
invalid_statuses = sorted(set(args.status) - allowed_statuses)
invalid_kinds = sorted(set(args.kind) - allowed_kinds)
if invalid_statuses:
    parser.error(f"invalid --status value(s): {', '.join(invalid_statuses)}; allowed: {', '.join(sorted(allowed_statuses))}")
if invalid_kinds:
    parser.error(f"invalid --kind value(s): {', '.join(invalid_kinds)}; allowed: {', '.join(sorted(allowed_kinds))}")

def load_registry_items():
    path = root / "registry" / "items.jsonl"
    by_path = {}
    if not path.exists():
        return by_path
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        item_path = item.get("path")
        if not item_path:
            continue
        try:
            full_path = (root / item_path).resolve()
        except Exception:
            continue
        by_path.setdefault(str(full_path), []).append(item)
    return by_path

registry_by_path = load_registry_items()

def item_source_id(item):
    source = item.get("source")
    if isinstance(source, dict):
        return source.get("source_id", "")
    return ""

def item_matches_filters(item):
    if args.owner and item.get("owner", "") not in args.owner:
        return False
    if args.status and item.get("status", "") not in args.status:
        return False
    if args.kind and item.get("kind", "") not in args.kind:
        return False
    if args.domain and not any(item.get("domain", "").startswith(prefix) for prefix in args.domain):
        return False
    if args.source_id and item_source_id(item) not in args.source_id:
        return False
    return True

def has_structured_filters():
    return bool(args.owner or args.status or args.kind or args.domain or args.source_id)

def metadata_for_item(item):
    return {
        "item_id": item.get("id", ""),
        "title": item.get("title", ""),
        "kind": item.get("kind", ""),
        "domain": item.get("domain", ""),
        "status": item.get("status", ""),
        "owner": item.get("owner", ""),
        "source_id": item_source_id(item),
        "review_after": item.get("review_after", ""),
        "tags": item.get("tags", []),
    }

sources = [
    {"id": "knowledge-hub", "path": str(root)},
]
sources_path = root / "registry" / "sources.json"
if sources_path.exists():
    data = json.loads(sources_path.read_text())
    sources.extend(data.get("sources", []))

allowed_suffixes = {".md", ".txt", ".json", ".jsonl", ".csv"}
results = []
seen = set()
for source in sources:
    sid = source.get("id", "")
    if args.source and sid not in args.source:
        continue
    base = pathlib.Path(str(source.get("path", "")).replace("~", str(pathlib.Path.home()))).expanduser()
    if not base.exists():
        continue
    for path in base.rglob("*"):
        if len(results) >= args.limit:
            break
        if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
            continue
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        try:
            text = path.read_text(errors="ignore")
        except Exception:
            continue
        items = registry_by_path.get(key, [])
        matching_items = [item for item in items if item_matches_filters(item)]
        if has_structured_filters() and not matching_items:
            continue
        lower = text.lower()
        index = lower.find(query)
        if index < 0:
            continue
        line_no = lower[:index].count("\n") + 1
        line = text.splitlines()[line_no - 1][:240] if text.splitlines() else ""
        item = matching_items[0] if matching_items else (items[0] if items else {})
        result = {
            "source": sid,
            "path": str(path),
            "line": line_no,
            "preview": line,
        }
        if item:
            result.update(metadata_for_item(item))
        results.append(result)
    if len(results) >= args.limit:
        break

if args.json:
    filters = {
        "source": args.source,
        "owner": args.owner,
        "status": args.status,
        "kind": args.kind,
        "domain": args.domain,
        "source_id": args.source_id,
    }
    print(json.dumps({"query": args.query, "count": len(results), "filters": filters, "results": results}, ensure_ascii=False, indent=2))
else:
    print(f"query: {args.query}")
    print(f"count: {len(results)}")
    for item in results:
        metadata = ""
        if item.get("item_id"):
            metadata = (
                f" [item={item.get('item_id', '')}"
                f" owner={item.get('owner', '')}"
                f" status={item.get('status', '')}"
                f" kind={item.get('kind', '')}"
                f" domain={item.get('domain', '')}"
                f" source_id={item.get('source_id', '')}]"
            )
        print(f"{item['source']}:{item['path']}:{item['line']}{metadata}: {item['preview']}")
sys.exit(0 if results else 1)
PY
