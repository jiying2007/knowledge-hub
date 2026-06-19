#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Validate Knowledge Hub registry and safety boundaries.")
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--json", action="store_true")
parser.add_argument("--sources-only", action="store_true")
parser.add_argument("--project", default="")
parser.add_argument("--domain", default="")
args = parser.parse_args(argv)

errors = []
warnings = []

def load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        errors.append(f"{path}: invalid json: {exc}")
        return {}

def load_jsonl(path):
    rows = []
    if not path.exists():
        warnings.append(f"{path}: missing")
        return rows
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception as exc:
            errors.append(f"{path}:{lineno}: invalid jsonl: {exc}")
    return rows

sources_path = root / "registry" / "sources.json"
sources = load_json(sources_path).get("sources", [])
for source in sources:
    for field in ["id", "path", "role", "authority", "status", "write_policy"]:
        if not source.get(field):
            errors.append(f"sources:{source.get('id', '<unknown>')} missing {field}")
    path = pathlib.Path(str(source.get("path", "")).replace("~", str(pathlib.Path.home()))).expanduser()
    if not path.exists():
        warnings.append(f"sources:{source.get('id')} path missing: {path}")

if not args.sources_only:
    ids = set()
    items = load_jsonl(root / "registry" / "items.jsonl")
    today = dt.date.today()
    for item in items:
        item_id = item.get("id")
        if not item_id:
            errors.append("items: missing id")
            continue
        if item_id in ids:
            errors.append(f"items:{item_id} duplicate id")
        ids.add(item_id)
        for field in ["title", "kind", "domain", "path", "scope", "visibility", "status", "owner", "source", "review_after", "created_at", "updated_at"]:
            if field not in item or item.get(field) in ("", None, []):
                errors.append(f"items:{item_id} missing {field}")
        rel_path = pathlib.Path(str(item.get("path", "")))
        if rel_path.is_absolute():
            errors.append(f"items:{item_id} path must be relative: {rel_path}")
        elif not (root / rel_path).exists():
            errors.append(f"items:{item_id} path missing: {rel_path}")
        status = item.get("status")
        if status in {"active", "reviewing"}:
            if not item.get("owner"):
                errors.append(f"items:{item_id} active/reviewing missing owner")
            review_after = str(item.get("review_after", ""))
            try:
                review_date = dt.date.fromisoformat(review_after)
                if review_date < today:
                    warnings.append(f"items:{item_id} review_after is stale: {review_after}")
            except Exception:
                errors.append(f"items:{item_id} invalid review_after: {review_after}")
        if status == "superseded" and not item.get("superseded_by"):
            errors.append(f"items:{item_id} superseded missing superseded_by")
        if item.get("kind") == "artifact-ref":
            for field in ["uri", "size", "sha256"]:
                if not item.get(field):
                    errors.append(f"items:{item_id} artifact-ref missing {field}")
        if item.get("scope") == "project-specific" and str(item.get("path", "")).startswith("domains/embedded/standards/"):
            errors.append(f"items:{item_id} project-specific under embedded standards")
        if item.get("visibility") == "personal-local" and item.get("status") == "active":
            warnings.append(f"items:{item_id} personal-local active item requires careful review")

    def expand_range_ids(text, path):
        expanded = set()
        for prefix_start, number_start, prefix_end, number_end in re.findall(r"`([^`]+?)(\d+)`\.\.`([^`]+?)(\d+)`", text):
            if prefix_start != prefix_end:
                warnings.append(f"index:{path.relative_to(root)} unsupported range prefix: {prefix_start}..{prefix_end}")
                continue
            width = max(len(number_start), len(number_end))
            for number in range(int(number_start), int(number_end) + 1):
                expanded.add(f"{prefix_start}{number:0{width}d}")
        return expanded

    def indexed_ids(path):
        if not path.exists():
            errors.append(f"index missing: {path.relative_to(root)}")
            return set()
        text = path.read_text()
        found = set(re.findall(r"`([^`]+)`", text))
        found.update(expand_range_ids(text, path))
        return found

    def canonical_status_ids(path):
        if not path.exists():
            errors.append(f"index missing: {path.relative_to(root)}")
            return set()
        found = set()
        for line in path.read_text().splitlines():
            if not (line.startswith("- active:") or line.startswith("- reviewing:") or line.startswith("- archived:")):
                continue
            found.update(re.findall(r"`([^`]+)`", line))
            found.update(expand_range_ids(line, path))
        return found

    index_requirements = {
        "indexes/by-owner.md": "owner",
        "indexes/by-review-date.md": "review_after",
        "indexes/by-status.md": "status",
    }
    for rel_index, field in index_requirements.items():
        seen = indexed_ids(root / rel_index)
        for item in items:
            item_id = item.get("id")
            if item_id and item_id not in seen:
                errors.append(f"index:{rel_index} missing item {item_id} ({field}={item.get(field, '<missing>')})")
        stale_seen = canonical_status_ids(root / rel_index) if rel_index == "indexes/by-status.md" else seen
        for indexed_id in sorted(stale_seen):
            if indexed_id not in ids:
                errors.append(f"index:{rel_index} stale item reference {indexed_id}")

    secret_patterns = [
        re.compile(r"-----BEGIN (RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----"),
        re.compile(r"(?i)(api[_-]?key|token|password|passwd|secret)\s*[:=]\s*['\"]?[^'\"\s]{12,}"),
        re.compile(r"(?i)cookie\s*[:=]\s*['\"]?[^'\"\s]{12,}"),
    ]
    scan_roots = [root / "domains", root / "registry", root / "governance", root / "templates"]
    for base in scan_roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".jsonl", ".sh", ".txt"}:
                continue
            try:
                text = path.read_text(errors="ignore")
            except Exception as exc:
                warnings.append(f"{path}: unreadable: {exc}")
                continue
            for pattern in secret_patterns:
                if pattern.search(text):
                    errors.append(f"secret-pattern:{path.relative_to(root)}")
                    break

result = {
    "status": "pass" if not errors else "fail",
    "root": str(root),
    "errors": errors,
    "warnings": warnings,
    "dry_run": bool(args.dry_run),
}
if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    print(f"status: {result['status']}")
    print(f"errors: {len(errors)}")
    print(f"warnings: {len(warnings)}")
    for item in errors[:40]:
        print(f"ERROR {item}")
    for item in warnings[:40]:
        print(f"WARN {item}")
sys.exit(0 if not errors else 1)
PY
