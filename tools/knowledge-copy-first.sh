#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import hashlib
import json
import pathlib
import shutil
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Apply a reviewed copy-first Knowledge Hub migration manifest.")
parser.add_argument("--manifest", required=True)
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--apply", action="store_true")
parser.add_argument("--verify-existing", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args(argv)

errors = []
warnings = []
planned = []
copied = []
verified = []

if args.apply and args.dry_run:
    errors.append("--apply and --dry-run are mutually exclusive")
if args.apply and args.verify_existing:
    errors.append("--apply and --verify-existing are mutually exclusive")
if args.dry_run and args.verify_existing:
    errors.append("--dry-run and --verify-existing are mutually exclusive")
if not args.apply and not args.verify_existing:
    args.dry_run = True

manifest = pathlib.Path(args.manifest)
if not manifest.is_absolute():
    manifest = root / manifest

def rel_target(path_text, bucket):
    target = pathlib.PurePosixPath(path_text)
    if target.is_absolute() or ".." in target.parts:
        raise ValueError(f"unsafe target path: {path_text}")
    if target.parts[:3] == ("domains", "projects", "pcr02"):
        if len(target.parts) < 4 or target.parts[3] != bucket:
            raise ValueError(f"target bucket mismatch: bucket={bucket} path={path_text}")
    elif target.parts[:2] == ("domains", "patents"):
        if len(target.parts) < 3 or target.parts[2] != bucket:
            raise ValueError(f"target bucket mismatch: bucket={bucket} path={path_text}")
    else:
        raise ValueError(f"target outside supported copy-first domains: {path_text}")
    return root / pathlib.Path(*target.parts)

def rel_source(source_root_text, source_path_text):
    source_root = pathlib.Path(source_root_text).resolve()
    source_rel = pathlib.PurePosixPath(source_path_text)
    if source_rel.is_absolute() or ".." in source_rel.parts:
        raise ValueError(f"unsafe source path: {source_path_text}")
    source = (source_root / pathlib.Path(*source_rel.parts)).resolve()
    try:
        source.relative_to(source_root)
    except ValueError:
        raise ValueError(f"source escapes source_root: {source_path_text}")
    return source

def existing_ancestor_symlink(path):
    current = root
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return str(path)
    for part in rel_parts[:-1]:
        current = current / part
        if current.exists() and current.is_symlink():
            return str(current)
    return ""

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

try:
    rows = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
except Exception as exc:
    rows = []
    errors.append(f"manifest unreadable or invalid jsonl: {exc}")

required = {
    "id",
    "source_id",
    "source_root",
    "source_path",
    "target_path",
    "bucket",
    "mode",
    "source_sha256",
    "size",
    "owner",
    "review_status",
    "risk",
    "rollback_policy",
    "source_status",
}

seen = set()
targets = set()
for index, row in enumerate(rows, 1):
    item_id = row.get("id", f"line-{index}")
    missing = sorted(required - set(row))
    if missing:
        errors.append(f"{item_id}: missing fields: {', '.join(missing)}")
        continue
    if item_id in seen:
        errors.append(f"{item_id}: duplicate id")
    seen.add(item_id)
    if row["mode"] != "copy-first-dry-run":
        errors.append(f"{item_id}: unsupported mode: {row['mode']}")
    if row["rollback_policy"] != "remove-copied-target-only":
        errors.append(f"{item_id}: unsupported rollback_policy: {row['rollback_policy']}")
    if row["bucket"] not in {"current", "decisions", "archive", "validation"}:
        errors.append(f"{item_id}: unsupported bucket: {row['bucket']}")

    try:
        source = rel_source(row["source_root"], row["source_path"])
        target = rel_target(row["target_path"], row["bucket"])
    except Exception as exc:
        errors.append(f"{item_id}: {exc}")
        continue

    target_key = str(target)
    if target_key in targets:
        errors.append(f"{item_id}: duplicate target_path: {row['target_path']}")
    targets.add(target_key)
    if not source.exists() or not source.is_file():
        errors.append(f"{item_id}: source missing or not file: {source}")
        continue
    try:
        actual_size = source.stat().st_size
        actual_hash = sha256(source)
    except Exception as exc:
        errors.append(f"{item_id}: source unreadable: {exc}")
        continue
    if actual_size != int(row["size"]):
        errors.append(f"{item_id}: size mismatch: manifest={row['size']} actual={actual_size}")
    if actual_hash != row["source_sha256"]:
        errors.append(f"{item_id}: sha256 mismatch: manifest={row['source_sha256']} actual={actual_hash}")
    if args.verify_existing and not target.exists():
        errors.append(f"{item_id}: target missing: {target}")
    if not args.verify_existing and target.exists():
        errors.append(f"{item_id}: target already exists: {target}")
    symlink_ancestor = existing_ancestor_symlink(target)
    if symlink_ancestor:
        errors.append(f"{item_id}: target ancestor is symlink or outside root: {symlink_ancestor}")
    if args.verify_existing and target.exists() and target.is_file():
        try:
            target_size = target.stat().st_size
            target_hash = sha256(target)
        except Exception as exc:
            errors.append(f"{item_id}: target unreadable: {exc}")
            continue
        if target_size != int(row["size"]):
            errors.append(f"{item_id}: target size mismatch: manifest={row['size']} actual={target_size}")
        if target_hash != row["source_sha256"]:
            errors.append(f"{item_id}: target sha256 mismatch: manifest={row['source_sha256']} actual={target_hash}")
        verified.append(item_id)
    planned.append({
        "id": item_id,
        "source": str(source),
        "target": str(target),
        "bucket": row["bucket"],
        "review_status": row["review_status"],
    })

if args.verify_existing:
    result_status = "verified" if not errors else "blocked"
elif args.apply and errors:
    result_status = "blocked"
elif args.apply:
    for item in planned:
        source = pathlib.Path(item["source"])
        target = pathlib.Path(item["target"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied_hash = sha256(target)
        source_hash = sha256(source)
        if copied_hash != source_hash:
            errors.append(f"{item['id']}: copied hash mismatch")
            break
        copied.append(item)
    result_status = "applied" if not errors else "fail"
else:
    result_status = "planned" if not errors else "blocked"

result = {
    "status": result_status,
    "root": str(root),
    "manifest": str(manifest),
    "dry_run": bool(not args.apply),
    "planned_count": len(planned),
    "copied_count": len(copied),
    "verified_count": len(verified),
    "errors": errors,
    "warnings": warnings,
}

if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    for key in ["status", "root", "manifest", "dry_run", "planned_count", "copied_count", "verified_count"]:
        print(f"{key}: {result[key]}")
    for item in errors:
        print(f"ERROR {item}")
    for item in warnings:
        print(f"WARN {item}")

if errors:
    sys.exit(3 if result_status == "blocked" else 1)
sys.exit(0)
PY
