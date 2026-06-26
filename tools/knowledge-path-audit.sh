#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import json
import pathlib
import subprocess
import sys
from collections import Counter

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]
home = pathlib.Path.home()

parser = argparse.ArgumentParser(
    description="Report-only audit for retired archive path mentions across hub, codex and runtime memory surfaces."
)
parser.add_argument(
    "--scope",
    choices=["hub", "codex", "memories", "sessions", "all"],
    default="hub",
    help="Scope to scan. all includes hub, codex, memories and sessions.",
)
parser.add_argument("--json", action="store_true")
parser.add_argument("--max-matches", type=int, default=100)
parser.add_argument("--max-per-file", type=int, default=20)
parser.add_argument("--strict", action="store_true", help="Return non-zero when runtime route candidates are found.")
args = parser.parse_args(argv)

TERMS = [
    ("~/embedded/engineering_archive", "~/embedded/engineering_archive"),
    ("~/embedded/engineering_archive", str(home / "embedded" / "engineering_archive")),
    ("~/codex/docs/archive", "~/codex/docs/archive"),
    ("~/codex/docs/archive", str(home / "codex" / "docs" / "archive")),
]

CANONICAL_ROUTES = {
    "~/embedded/engineering_archive": "~/knowledge-hub/projects/pcr02/archive/engineering-archive",
    "~/embedded/engineering_archive/pcr02": "~/knowledge-hub/projects/pcr02/archive/engineering-archive/pcr02",
    "~/codex/docs/archive": "~/knowledge-hub/domains/codex/archive/codex-archive",
    "~/codex/docs/archive/_registry": "~/knowledge-hub/domains/codex/archive/codex-archive-registry",
}

def existing_scopes():
    values = {
        "hub": root,
        "codex": home / "codex",
        "memories": home / ".codex" / "memories",
        "sessions": home / ".codex" / "sessions",
    }
    if args.scope == "all":
        return {key: path for key, path in values.items() if path.exists()}
    path = values[args.scope]
    return {args.scope: path} if path.exists() else {}

def rel(path):
    try:
        if root == path or root in path.parents:
            return str(path.relative_to(root))
    except Exception:
        pass
    try:
        if home == path or home in path.parents:
            return "~/" + str(path.relative_to(home))
    except Exception:
        pass
    return str(path)

def classify(scope, rel_path, line_text):
    normalized = rel_path.replace("\\", "/")
    text = line_text.lower()
    if scope == "sessions":
        return "historical-session"
    if scope == "memories":
        return "runtime-route-candidate"
    if scope == "codex":
        return "runtime-route-candidate"
    if normalized in {"README.md", "governance/path-routing.md", "governance/source-boundaries.md", "governance/migration-policy.md", "registry/schema.md", "tools/knowledge-path-audit.sh", "tools/knowledge-check.sh"}:
        return "canonical-policy"
    if normalized.startswith("domains/codex/archive/codex-archive/"):
        return "provenance"
    if normalized.startswith("sources/") or normalized == "registry/sources.json":
        return "provenance"
    if normalized.startswith("artifacts/manifests/") or normalized.startswith("registry/authorizations") or normalized.startswith("registry/automation-runs"):
        return "provenance"
    if "旧" in line_text or "retired" in text or "provenance" in text or "不再作为" in line_text:
        return "canonical-policy"
    return "runtime-route-candidate"

def scan_scope(scope, path):
    cmd = [
        "rtk",
        "rg",
        "-n",
        "--fixed-strings",
        "--no-heading",
        "--max-count",
        str(args.max_per_file),
    ]
    for _display, term in TERMS:
        cmd.extend(["-e", term])
    cmd.append(str(path))
    completed = subprocess.run(
        cmd,
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    rows = []
    if completed.returncode not in (0, 1):
        return rows, completed.stderr.strip()
    for raw in completed.stdout.splitlines():
        if len(rows) >= args.max_matches:
            break
        parts = raw.split(":", 2)
        if len(parts) != 3:
            continue
        file_path = pathlib.Path(parts[0])
        line_no = parts[1]
        line_text = parts[2]
        display = rel(file_path)
        rows.append(
            {
                "scope": scope,
                "path": display,
                "line": int(line_no) if line_no.isdigit() else line_no,
                "classification": classify(scope, display, line_text),
                "text": line_text.strip()[:240],
            }
        )
    return rows, ""

all_rows = []
errors = []
for scope, path in existing_scopes().items():
    rows, error = scan_scope(scope, path)
    all_rows.extend(rows)
    if error:
        errors.append({"scope": scope, "error": error})

counts = Counter(row["classification"] for row in all_rows)
runtime_count = counts.get("runtime-route-candidate", 0)
payload = {
    "schema_version": 1,
    "read_only": True,
    "root": "~/knowledge-hub",
    "scope": args.scope,
    "searched_terms": sorted({display for display, _term in TERMS}),
    "canonical_routes": CANONICAL_ROUTES,
    "summary": {
        "match_count": len(all_rows),
        "classification_counts": dict(sorted(counts.items())),
        "runtime_route_candidate_count": runtime_count,
        "errors": errors,
        "truncated": len(all_rows) >= args.max_matches,
    },
    "next_actions_zh": [
        "Hub 内 canonical-policy/provenance 命中通常保留。",
        "runtime-route-candidate 需要在对应仓库、skill、memory candidate 或 Codex 资产链路中修复。",
        "historical-session 默认不改写，只作为召回风险证据。",
    ],
    "matches": all_rows,
}

if args.json:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
else:
    print(f"scope: {args.scope}")
    print(f"matches: {len(all_rows)}")
    print(f"runtime-route-candidates: {runtime_count}")
    for key, value in sorted(counts.items()):
        print(f"- {key}: {value}")
    for row in all_rows[: min(len(all_rows), 20)]:
        print(f"{row['classification']}: {row['path']}:{row['line']}")

if errors:
    sys.exit(2)
if args.strict and runtime_count:
    sys.exit(1)
PY
