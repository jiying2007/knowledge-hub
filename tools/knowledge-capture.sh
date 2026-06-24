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
parser = argparse.ArgumentParser(description="Plan a Knowledge Hub capture.")
parser.add_argument("--source", required=True)
parser.add_argument("--kind", required=True)
parser.add_argument("--target", default="inbox")
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args(sys.argv[2:])

source = pathlib.Path(args.source).expanduser()
result = {
    "action": "capture",
    "status": "planned" if args.dry_run and not args.apply else "blocked",
    "source": str(source),
    "source_exists": source.exists(),
    "kind": args.kind,
    "target": args.target,
    "apply_supported": False,
    "message": "Dry-run capture plan only; --apply is intentionally blocked in bootstrap version."
}
if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    for key, value in result.items():
        print(f"{key}: {value}")
sys.exit(0 if args.dry_run and not args.apply else 3)
PY
