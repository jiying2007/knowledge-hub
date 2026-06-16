#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import json
import sys

parser = argparse.ArgumentParser(description="Plan a Knowledge Hub promotion.")
parser.add_argument("--id", required=True)
parser.add_argument("--target", required=True)
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args(sys.argv[2:])

result = {
    "action": "promote",
    "status": "planned" if args.dry_run and not args.apply else "blocked",
    "id": args.id,
    "target": args.target,
    "required_review": True,
    "apply_supported": False,
    "message": "Promotion requires human review; --apply is intentionally blocked in bootstrap version."
}
if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    for key, value in result.items():
        print(f"{key}: {value}")
sys.exit(0 if args.dry_run and not args.apply else 3)
PY
