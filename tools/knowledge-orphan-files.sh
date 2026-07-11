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

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(
    prog="knowledge-orphan-files.sh",
    description="Report Knowledge Hub Markdown bodies that are not represented by registry/items.jsonl.",
)
parser.add_argument("--json", action="store_true", help="Print JSON output.")
parser.add_argument("--all", action="store_true", help="Scan all Hub body Markdown files. Default scans changed files only.")
parser.add_argument("--strict", action="store_true", help="Exit non-zero when missing registry references are found.")
parser.add_argument("--limit", type=int, default=50, help="Maximum missing rows to include in output.")
args = parser.parse_args(argv)

if args.limit < 1:
    parser.error("--limit must be >= 1")

body_prefixes = ("projects/", "domains/", "governance/", "notes/")
excluded_names = {"README.md"}
excluded_prefixes = (
    "projects/pcr02/archive/engineering-archive/pcr02/decision-index.md",
)


def load_registry_paths():
    paths = set()
    ids_by_path = {}
    items_path = root / "registry" / "items.jsonl"
    for line_no, line in enumerate(items_path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"registry/items.jsonl:{line_no}: invalid JSON: {exc}") from exc
        path = row.get("path", "")
        if path:
            paths.add(path)
            ids_by_path.setdefault(path, []).append(row.get("id", ""))
    return paths, ids_by_path


def is_body_markdown(path):
    if not path.endswith(".md"):
        return False
    if pathlib.Path(path).name in excluded_names:
        return False
    if path in excluded_prefixes:
        return False
    return path.startswith(body_prefixes)


def changed_markdown_paths():
    completed = subprocess.run(
        ["rtk", "git", "status", "--porcelain"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or "git status failed")
    paths = []
    for raw in completed.stdout.splitlines():
        if not raw:
            continue
        path = raw[3:] if len(raw) > 3 else ""
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip()
        if is_body_markdown(path):
            paths.append(path)
    return sorted(set(paths))


def all_markdown_paths():
    paths = []
    for prefix in body_prefixes:
        base = root / prefix.rstrip("/")
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            rel = path.relative_to(root).as_posix()
            if is_body_markdown(rel):
                paths.append(rel)
    return sorted(set(paths))


registry_paths, ids_by_path = load_registry_paths()
checked_paths = all_markdown_paths() if args.all else changed_markdown_paths()
missing = [path for path in checked_paths if path not in registry_paths]
registered = [
    {"path": path, "ids": ids_by_path.get(path, [])}
    for path in checked_paths
    if path in registry_paths
]

output = {
    "schema_version": 1,
    "read_only": True,
    "mode": "all" if args.all else "changed-only",
    "strict": args.strict,
    "status": "needs-fix" if missing else "ok",
    "checked_count": len(checked_paths),
    "registered_count": len(registered),
    "missing_registry_count": len(missing),
    "missing_registry": missing[: args.limit],
    "registered": registered[: args.limit],
    "notes_zh": (
        "changed-only 模式用于阻断本次新增或修改正文遗漏 registry；--all 模式暴露历史归档长尾，"
        "默认只作 advisory，不代表 mature blocker。"
    ),
}

if args.json:
    print(json.dumps(output, ensure_ascii=False, indent=2))
else:
    print("# Knowledge Hub Orphan Files")
    print()
    print(f"- mode: {output['mode']}")
    print(f"- status: {output['status']}")
    print(f"- checked: {output['checked_count']}")
    print(f"- missing_registry: {output['missing_registry_count']}")
    for path in output["missing_registry"]:
        print(f"  - {path}")

if args.strict and missing:
    raise SystemExit(1)
PY
