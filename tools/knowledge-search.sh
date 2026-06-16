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
parser.add_argument("--source", action="append", default=[])
args = parser.parse_args(argv)

query = args.query.lower()
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
        lower = text.lower()
        index = lower.find(query)
        if index < 0:
            continue
        line_no = lower[:index].count("\n") + 1
        line = text.splitlines()[line_no - 1][:240] if text.splitlines() else ""
        results.append({
            "source": sid,
            "path": str(path),
            "line": line_no,
            "preview": line,
        })
    if len(results) >= args.limit:
        break

if args.json:
    print(json.dumps({"query": args.query, "count": len(results), "results": results}, ensure_ascii=False, indent=2))
else:
    print(f"query: {args.query}")
    print(f"count: {len(results)}")
    for item in results:
        print(f"{item['source']}:{item['path']}:{item['line']}: {item['preview']}")
sys.exit(0 if results else 1)
PY
