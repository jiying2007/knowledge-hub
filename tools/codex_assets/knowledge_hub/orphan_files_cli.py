import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(
    prog="knowledge-orphan-files.sh",
    description="Report Knowledge Hub Markdown bodies that lack exact registry or frozen collection coverage.",
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
    "projects/pcr02-ssc305/archive/engineering-archive/pcr02/decision-index.md",
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


def inventory_hash(paths):
    payload = "".join(f"{path}\n" for path in sorted(paths))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
        if is_body_markdown(path) and (root / path).is_file():
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


def load_collection_coverage(registry_paths):
    coverage_path = root / "registry" / "body-coverage.json"
    if not coverage_path.exists():
        return [], ["registry/body-coverage.json is missing"]
    try:
        payload = json.loads(coverage_path.read_text())
    except Exception as exc:
        return [], [f"registry/body-coverage.json is invalid: {exc}"]
    if payload.get("schema_version") != 2:
        return [], ["registry/body-coverage.json schema_version must be 2"]
    collections = payload.get("collections", [])
    if not isinstance(collections, list):
        return [], ["registry/body-coverage.json collections must be a list"]

    rows = []
    errors = []
    seen_ids = set()
    seen_prefixes = set()
    try:
        owners_payload = json.loads((root / "registry" / "owners.json").read_text())
        registered_owners = {
            str(owner.get("id", ""))
            for owner in owners_payload.get("owners", [])
            if isinstance(owner, dict) and owner.get("id")
        }
    except Exception as exc:
        registered_owners = set()
        errors.append(f"registry/owners.json is invalid: {exc}")
    for index, row in enumerate(collections, 1):
        row_id = str(row.get("id", "")).strip()
        prefix = str(row.get("path_prefix", "")).strip()
        owner = str(row.get("owner", "")).strip()
        review_after = str(row.get("review_after", "")).strip()
        mode = str(row.get("coverage_mode", "")).strip()
        inventory_scope = str(row.get("inventory_scope", "")).strip()
        expected_count = row.get("expected_markdown_count")
        expected_hash = str(row.get("inventory_sha256", "")).strip()
        row_errors = []
        if not row_id:
            row_errors.append("missing id")
        elif row_id in seen_ids:
            row_errors.append("duplicate id")
        seen_ids.add(row_id)
        normalized_prefix = pathlib.PurePosixPath(prefix.rstrip("/")).as_posix() if prefix else ""
        if (
            not prefix
            or not prefix.endswith("/")
            or prefix.startswith(("/", "~/", "../", "./"))
            or "\\" in prefix
            or normalized_prefix != prefix.rstrip("/")
            or ".." in pathlib.PurePosixPath(prefix).parts
        ):
            row_errors.append("path_prefix must be a repo-relative directory ending in /")
        elif prefix in seen_prefixes:
            row_errors.append("duplicate path_prefix")
        seen_prefixes.add(prefix)
        if not owner or owner not in registered_owners:
            row_errors.append(f"owner is not registered: {owner or '<missing>'}")
        if mode not in {"archive-corpus", "domain-baseline", "governance-baseline"}:
            row_errors.append(f"invalid coverage_mode: {mode}")
        if inventory_scope != "unregistered-only":
            row_errors.append("inventory_scope must be unregistered-only")
        try:
            dt.date.fromisoformat(review_after)
        except Exception:
            row_errors.append(f"invalid review_after: {review_after}")
        if not isinstance(expected_count, int) or expected_count < 1:
            row_errors.append("expected_markdown_count must be a positive integer")
        if len(expected_hash) != 64 or any(ch not in "0123456789abcdef" for ch in expected_hash):
            row_errors.append("inventory_sha256 must be lowercase SHA256")

        current_paths = []
        exact_registered_under_prefix_count = 0
        if prefix and not prefix.startswith(("/", "~/", "../", "./")):
            base = root / prefix.rstrip("/")
            if not base.is_dir():
                row_errors.append("path_prefix directory is missing")
            else:
                all_current_paths = sorted(
                    path.relative_to(root).as_posix()
                    for path in base.rglob("*.md")
                    if is_body_markdown(path.relative_to(root).as_posix())
                )
                current_paths = [
                    path for path in all_current_paths if path not in registry_paths
                ]
                exact_registered_under_prefix_count = (
                    len(all_current_paths) - len(current_paths)
                )
        actual_hash = inventory_hash(current_paths)
        if isinstance(expected_count, int) and len(current_paths) != expected_count:
            row_errors.append(
                f"inventory count drift: expected {expected_count}, actual {len(current_paths)}"
            )
        if expected_hash and actual_hash != expected_hash:
            row_errors.append(
                f"inventory hash drift: expected {expected_hash}, actual {actual_hash}"
            )
        rows.append({
            "id": row_id,
            "path_prefix": prefix,
            "coverage_mode": mode,
            "inventory_scope": inventory_scope,
            "owner": owner,
            "review_after": review_after,
            "expected_markdown_count": expected_count,
            "actual_markdown_count": len(current_paths),
            "exact_registered_under_prefix_count": exact_registered_under_prefix_count,
            "inventory_sha256": expected_hash,
            "actual_inventory_sha256": actual_hash,
            "status": "pass" if not row_errors else "fail",
            "errors": row_errors,
            "paths": current_paths,
        })
        errors.extend(f"{row_id or index}: {message}" for message in row_errors)
    return rows, errors


registry_paths, ids_by_path = load_registry_paths()
coverage_rows, coverage_errors = load_collection_coverage(registry_paths)
coverage_by_path = {}
for row in coverage_rows:
    if row["status"] != "pass":
        continue
    for path in row["paths"]:
        existing = coverage_by_path.get(path)
        if existing and existing != row["id"]:
            coverage_errors.append(
                f"{path}: overlapping collection coverage: {existing}, {row['id']}"
            )
            continue
        coverage_by_path[path] = row["id"]
checked_paths = all_markdown_paths() if args.all else changed_markdown_paths()
missing = [
    path for path in checked_paths
    if path not in registry_paths and path not in coverage_by_path
]
registered = [
    {"path": path, "ids": ids_by_path.get(path, [])}
    for path in checked_paths
    if path in registry_paths
]
collection_covered = [
    {"path": path, "coverage_id": coverage_by_path[path]}
    for path in checked_paths
    if path not in registry_paths and path in coverage_by_path
]
needs_fix = bool(missing or coverage_errors)

output = {
    "schema_version": 1,
    "read_only": True,
    "mode": "all" if args.all else "changed-only",
    "strict": args.strict,
    "status": "needs-fix" if needs_fix else "ok",
    "checked_count": len(checked_paths),
    "registered_count": len(registered),
    "exact_registered_count": len(registered),
    "collection_covered_count": len(collection_covered),
    "missing_registry_count": len(missing),
    "missing_registry": missing[: args.limit],
    "registered": registered[: args.limit],
    "collection_covered": collection_covered[: args.limit],
    "coverage_registry": "registry/body-coverage.json",
    "coverage_contract_status": "pass" if not coverage_errors else "fail",
    "coverage_errors": coverage_errors[: args.limit],
    "coverage_collections": [
        {key: value for key, value in row.items() if key != "paths"}
        for row in coverage_rows
    ],
    "notes_zh": (
        "正文必须由 registry/items.jsonl 精确登记，或由 registry/body-coverage.json 的冻结路径清单覆盖。"
        "集合只冻结未精确登记的历史 corpus，不产生 active、owner decision 或 promotion；"
        "新增且已精确登记的正文不会改变集合 hash，新增未登记路径仍会使 inventory hash 漂移并阻断 strict gate。"
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
    print(f"- exact_registered: {output['exact_registered_count']}")
    print(f"- collection_covered: {output['collection_covered_count']}")
    print(f"- missing_registry: {output['missing_registry_count']}")
    for path in output["missing_registry"]:
        print(f"  - {path}")

if args.strict and needs_fix:
    raise SystemExit(1)
