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
parser.add_argument("--snapshot-source-id", default="")
parser.add_argument("--snapshot-source-path", default="")
parser.add_argument("--snapshot-claimed-revision", default="")
parser.add_argument("--reconcile-snapshot", default="")
args = parser.parse_args(argv)

if args.reconcile_snapshot:
    from .common import KnowledgeHubError
    from .external_source_snapshot import SourceSnapshotError
    from .source_snapshot_reconcile import reconcile_private_snapshot

    if args.snapshot_source_id or args.snapshot_source_path or args.snapshot_claimed_revision:
        parser.error("--reconcile-snapshot is exclusive of source capture options")
    try:
        result = reconcile_private_snapshot(root, pathlib.Path(args.reconcile_snapshot))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        sys.exit(0)
    except (SourceSnapshotError, KnowledgeHubError, OSError, ValueError) as exc:
        reason = str(exc) if isinstance(exc, (SourceSnapshotError, KnowledgeHubError)) else "source reconciliation I/O error"
        print(json.dumps({"status": "blocked", "reason": reason,
                          "full_external_migration_proven": False}, ensure_ascii=False))
        sys.exit(1)

if args.snapshot_source_id or args.snapshot_source_path or args.snapshot_claimed_revision:
    # Reuse the existing public inventory entry point, without creating a 50th wrapper.
    from .external_source_snapshot import (
        SourceSnapshotError, capture_source_snapshot, persist_private_snapshot,
    )

    if not args.snapshot_source_id or not args.snapshot_source_path:
        parser.error("--snapshot-source-id and --snapshot-source-path must be supplied together")
    try:
        candidate = capture_source_snapshot(
            root, args.snapshot_source_id, pathlib.Path(args.snapshot_source_path),
            args.snapshot_claimed_revision,
        )
        private_path = persist_private_snapshot(root, candidate)
        print(json.dumps({
            "status": "candidate", "source_id": candidate["source_id"],
            "file_count": candidate["file_count"], "total_bytes": candidate["total_bytes"],
            "capture_sha256": candidate["capture_sha256"],
            "private_local_manifest": private_path, "read_only_source": True,
            "revision_verified": False, "external_migration_proven": False,
            "owner_review_performed": False, "product_terminal_changed": False,
        }, ensure_ascii=False, sort_keys=True))
        sys.exit(0)
    except (SourceSnapshotError, OSError, ValueError) as exc:
        # Do not expose private absolute paths from OS error diagnostics.
        reason = str(exc) if isinstance(exc, SourceSnapshotError) else "source snapshot I/O or argument error"
        print(json.dumps({"status": "blocked", "reason": reason,
                          "external_migration_proven": False}, ensure_ascii=False))
        sys.exit(1)

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

def user_path_prefixes():
    prefixes = [str(pathlib.Path.home())]
    user_name = os.environ.get("USER", "")
    if user_name:
        prefixes.append("/" + "vsdata" + "/" + user_name)
    return [prefix for prefix in prefixes if prefix and prefix != "/"]

def display_path(value):
    text = str(value)
    for prefix in user_path_prefixes():
        if text == prefix:
            text = "~"
        elif text.startswith(prefix + "/"):
            text = "~" + text[len(prefix):]
        else:
            text = text.replace(prefix, "~")
    return text

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
        "path": display_path(base),
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
    "root": display_path(root),
    "max_files_per_source": args.max_files,
    "sources": [inventory(source) for source in sources],
}

if args.markdown:
    print(f"# Knowledge Hub Source Inventory ({dt.date.today().isoformat()})")
    print()
    print(f"- root: `{display_path(root)}`")
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

