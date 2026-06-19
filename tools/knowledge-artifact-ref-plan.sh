#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import hashlib
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Create an artifact-ref manifest for non-text files from a registered source.")
parser.add_argument("--source-id", required=True)
parser.add_argument("--id-prefix", default="")
parser.add_argument("--output", required=True)
parser.add_argument("--exclude-ext", action="append", default=[".md", ".txt"])
parser.add_argument("--force", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args(argv)

errors = []
warnings = []

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "artifact"

def safe_rel(path_text):
    rel = pathlib.PurePosixPath(path_text)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe relative path: {path_text}")
    return rel

try:
    sources_doc = json.loads((root / "registry" / "sources.json").read_text())
except Exception as exc:
    sources_doc = {"sources": []}
    errors.append(f"registry/sources.json unreadable: {exc}")

source = None
for candidate in sources_doc.get("sources", []):
    if candidate.get("id") == args.source_id:
        source = candidate
        break
if not source:
    errors.append(f"source not registered: {args.source_id}")

output = root / safe_rel(args.output)
if output.exists() and not args.force:
    errors.append(f"output already exists: {args.output}")
if not str(output.relative_to(root)).startswith("artifacts/manifests/"):
    errors.append(f"output must live under artifacts/manifests/: {args.output}")

rows = []
if source and not errors:
    source_root = pathlib.Path(str(source.get("path", "")).replace("~", str(pathlib.Path.home()))).expanduser().resolve()
    if not source_root.exists() or not source_root.is_dir():
        errors.append(f"source path missing or not directory: {source_root}")
    else:
        excluded = {ext.lower() for ext in args.exclude_ext}
        id_prefix = args.id_prefix or f"{slugify(args.source_id)}-artifact"
        files = []
        for path in sorted(source_root.rglob("*")):
            if not path.is_file():
                continue
            if any(part.startswith(".") for part in path.relative_to(source_root).parts):
                continue
            if path.suffix.lower() in excluded:
                continue
            files.append(path)
        for index, path in enumerate(files, 1):
            rel = path.relative_to(source_root).as_posix()
            rows.append(
                {
                    "id": f"{id_prefix}-{index:03d}",
                    "source_id": args.source_id,
                    "source_root": str(source_root),
                    "source_path": rel,
                    "uri": f"source://{args.source_id}/{rel}",
                    "size": path.stat().st_size,
                    "sha256": sha256(path),
                    "artifact_type": path.suffix.lower().lstrip(".") or "binary",
                    "mode": "artifact-ref-register",
                    "status": "registered-reference-only",
                }
            )

if not errors:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n")

result = {
    "status": "planned" if not errors else "blocked",
    "source_id": args.source_id,
    "output": args.output,
    "row_count": len(rows),
    "errors": errors,
    "warnings": warnings,
}
if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    print(f"status: {result['status']}")
    print(f"source_id: {result['source_id']}")
    print(f"output: {result['output']}")
    print(f"row_count: {result['row_count']}")
    for item in errors:
        print(f"ERROR {item}")
    for item in warnings:
        print(f"WARN {item}")

sys.exit(1 if errors else 0)
PY
