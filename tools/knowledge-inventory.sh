#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Inventory registered Knowledge Hub sources without modifying them.")
parser.add_argument("--json", action="store_true")
parser.add_argument("--markdown", action="store_true")
parser.add_argument("--max-files", type=int, default=50000)
parser.add_argument("--sample-limit", type=int, default=8)
args = parser.parse_args(argv)

sources_path = root / "registry" / "sources.json"
sources = json.loads(sources_path.read_text()).get("sources", [])

skip_dirs = {
    ".git",
    ".cache",
    ".tmp",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
    "out",
}
text_suffixes = {".md", ".txt", ".json", ".jsonl", ".csv", ".yml", ".yaml", ".rst", ".adoc"}
binary_suffixes = {".bin", ".elf", ".hex", ".img", ".iso", ".zip", ".7z", ".rar", ".tar", ".gz", ".tgz", ".xz", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}

def path_from_source(value):
    return pathlib.Path(str(value).replace("~", str(pathlib.Path.home()))).expanduser()

def human_bytes(size):
    value = float(size)
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"

def git_summary(base):
    git_dir = base / ".git"
    if not git_dir.exists():
        return {"is_git": False}
    try:
        branch = subprocess.run(
            ["rtk", "git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=base,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.strip()
        status = subprocess.run(
            ["rtk", "git", "status", "--short"],
            cwd=base,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.splitlines()
        return {
            "is_git": True,
            "branch": branch,
            "dirty_entries": len(status),
            "dirty_sample": status[:5],
        }
    except Exception as exc:
        return {"is_git": True, "error": str(exc)}

def inventory(source):
    base = path_from_source(source.get("path", ""))
    item = {
        "id": source.get("id", ""),
        "path": str(base),
        "role": source.get("role", ""),
        "authority": source.get("authority", ""),
        "write_policy": source.get("write_policy", ""),
        "exists": base.exists(),
        "is_dir": base.is_dir(),
        "scan_status": "missing",
        "file_count": 0,
        "dir_count": 0,
        "total_bytes": 0,
        "total_human": "0 B",
        "extensions": {},
        "text_like_files": 0,
        "binary_like_files": 0,
        "samples": [],
        "truncated": False,
        "git": {},
    }
    if not base.exists():
        return item
    item["git"] = git_summary(base)
    if not base.is_dir():
        item["scan_status"] = "single-file"
        try:
            size = base.stat().st_size
        except OSError:
            size = 0
        suffix = base.suffix.lower() or "<none>"
        item.update({
            "file_count": 1,
            "total_bytes": size,
            "total_human": human_bytes(size),
            "extensions": {suffix: 1},
            "text_like_files": 1 if suffix in text_suffixes else 0,
            "binary_like_files": 1 if suffix in binary_suffixes else 0,
            "samples": [base.name],
        })
        return item

    extensions = collections.Counter()
    samples = []
    item["scan_status"] = "scanned"
    for current, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        item["dir_count"] += len(dirs)
        for name in files:
            path = pathlib.Path(current) / name
            rel = path.relative_to(base)
            suffix = path.suffix.lower() or "<none>"
            item["file_count"] += 1
            extensions[suffix] += 1
            if suffix in text_suffixes:
                item["text_like_files"] += 1
            if suffix in binary_suffixes:
                item["binary_like_files"] += 1
            try:
                item["total_bytes"] += path.stat().st_size
            except OSError:
                pass
            if len(samples) < args.sample_limit:
                samples.append(str(rel))
            if item["file_count"] >= args.max_files:
                item["truncated"] = True
                break
        if item["truncated"]:
            break
    item["total_human"] = human_bytes(item["total_bytes"])
    item["extensions"] = dict(extensions.most_common(12))
    item["samples"] = samples
    return item

result = {
    "schema_version": 1,
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "root": str(root),
    "max_files_per_source": args.max_files,
    "sources": [inventory(source) for source in sources],
}

if args.markdown:
    print(f"# Knowledge Hub Source Inventory ({dt.date.today().isoformat()})")
    print()
    print(f"- root: `{root}`")
    print(f"- max_files_per_source: `{args.max_files}`")
    print()
    print("| source | exists | files | dirs | size | text | binary | git | policy |")
    print("|---|---:|---:|---:|---:|---:|---:|---|---|")
    for source in result["sources"]:
        git = source.get("git", {})
        git_text = "no"
        if git.get("is_git"):
            git_text = f"{git.get('branch', '?')} dirty={git.get('dirty_entries', '?')}"
        print(
            f"| `{source['id']}` | {source['exists']} | {source['file_count']} | "
            f"{source['dir_count']} | {source['total_human']} | {source['text_like_files']} | "
            f"{source['binary_like_files']} | {git_text} | `{source['write_policy']}` |"
        )
    print()
    for source in result["sources"]:
        print(f"## {source['id']}")
        print()
        print(f"- path: `{source['path']}`")
        print(f"- authority: `{source['authority']}`")
        print(f"- role: `{source['role']}`")
        print(f"- scan_status: `{source['scan_status']}`")
        print(f"- truncated: `{source['truncated']}`")
        print(f"- top_extensions: `{json.dumps(source['extensions'], ensure_ascii=False)}`")
        print("- samples:")
        for sample in source["samples"]:
            print(f"  - `{sample}`")
        if not source["samples"]:
            print("  - none")
        print()
else:
    print(json.dumps(result, ensure_ascii=False, indent=2))
PY
