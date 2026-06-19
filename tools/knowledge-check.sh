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
if args.project:
    warnings.append(f"knowledge-check: --project is reserved and does not narrow validation scope: {args.project}")
if args.domain:
    warnings.append(f"knowledge-check: --domain is reserved and does not narrow validation scope: {args.domain}")

ALLOWED_ITEM_KINDS = {
    "standard",
    "runbook",
    "architecture",
    "decision",
    "project-current",
    "project-archive",
    "validation",
    "audit",
    "patent",
    "codex-session",
    "codex-workflow",
    "personal-note",
    "artifact-ref",
}
ALLOWED_ITEM_STATUSES = {
    "draft",
    "active",
    "reviewing",
    "archived",
    "superseded",
    "rejected",
    "personal",
}
ALLOWED_ITEM_SCOPES = {
    "team-general",
    "project-specific",
    "codex-memory-curation-governance",
}
ALLOWED_ITEM_VISIBILITIES = {
    "team-internal",
    "personal-local",
}
ALLOWED_DOMAIN_ROOTS = {
    "root",
    "governance",
    "projects",
    "embedded",
    "patents",
    "codex",
    "personal",
}
ALLOWED_SOURCE_ROLES = {
    "team-knowledge-source",
    "project-archive-source",
    "patent-source",
    "codex-governance-source",
    "auxiliary-memory-source",
    "project-current-docs-source",
}
ALLOWED_SOURCE_AUTHORITIES = {
    "legacy-team-ssot",
    "legacy-project-history",
    "patent-materials",
    "codex-workflow-history",
    "auxiliary-recall-only",
    "legacy-project-current-docs",
}
ALLOWED_SOURCE_STATUSES = {
    "registered",
    "deprecated",
    "retired",
}
ALLOWED_SOURCE_WRITE_POLICIES = {
    "do-not-write-through-knowledge-hub",
    "copy-first-migration-only",
    "do-not-mix-with-engineering-knowledge",
    "use-codex-archive-tools",
    "read-only-unless-explicitly-approved",
    "externalize-to-knowledge-hub-before-prune",
}

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
source_ids = set()
for source in sources:
    for field in ["id", "path", "role", "authority", "status", "write_policy"]:
        if not source.get(field):
            errors.append(f"sources:{source.get('id', '<unknown>')} missing {field}")
    source_id = source.get("id", "<unknown>")
    if source.get("id"):
        if source_id in source_ids:
            errors.append(f"sources:{source_id} duplicate id")
        source_ids.add(source_id)
    if source.get("role") and source.get("role") not in ALLOWED_SOURCE_ROLES:
        errors.append(f"sources:{source_id} invalid role: {source.get('role')}")
    if source.get("authority") and source.get("authority") not in ALLOWED_SOURCE_AUTHORITIES:
        errors.append(f"sources:{source_id} invalid authority: {source.get('authority')}")
    if source.get("status") and source.get("status") not in ALLOWED_SOURCE_STATUSES:
        errors.append(f"sources:{source_id} invalid status: {source.get('status')}")
    if source.get("write_policy") and source.get("write_policy") not in ALLOWED_SOURCE_WRITE_POLICIES:
        errors.append(f"sources:{source_id} invalid write_policy: {source.get('write_policy')}")
    path = pathlib.Path(str(source.get("path", "")).replace("~", str(pathlib.Path.home()))).expanduser()
    if not path.exists():
        warnings.append(f"sources:{source.get('id')} path missing: {path}")

if not args.sources_only:
    for registry_json_path in sorted((root / "registry").glob("*.json")):
        try:
            json.loads(registry_json_path.read_text())
        except Exception as exc:
            errors.append(f"registry:{registry_json_path.relative_to(root)} invalid json: {exc}")

    for registry_jsonl_path in sorted((root / "registry").glob("*.jsonl")):
        for lineno, line in enumerate(registry_jsonl_path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except Exception as exc:
                errors.append(f"registry:{registry_jsonl_path.relative_to(root)}:{lineno} invalid jsonl: {exc}")

    by_source_path = root / "indexes" / "by-source.md"
    if not by_source_path.exists():
        errors.append("index missing: indexes/by-source.md")
    else:
        by_source_ids = set()
        in_sources_section = False
        in_source_table = False
        for line in by_source_path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                in_sources_section = stripped == "# Knowledge Sources"
                in_source_table = False
                continue
            if in_sources_section and stripped.startswith("#"):
                break
            if not in_sources_section:
                continue
            if not stripped:
                if in_source_table:
                    break
                continue
            if not stripped.startswith("|"):
                if in_source_table:
                    break
                continue
            in_source_table = True
            cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
            if len(cells) < 3 or cells[0] in {"Source", "---"}:
                continue
            by_source_ids.add(cells[0])
        for source_id in sorted(source_ids):
            if source_id not in by_source_ids:
                errors.append(f"index:indexes/by-source.md missing source {source_id}")
        for indexed_source_id in sorted(by_source_ids):
            if indexed_source_id not in source_ids:
                errors.append(f"index:indexes/by-source.md stale source {indexed_source_id}")

    owner_ids = set()
    owners_doc = load_json(root / "registry" / "owners.json")
    for owner in owners_doc.get("owners", []):
        owner_id = owner.get("id")
        if not owner_id:
            errors.append("owners: missing id")
            continue
        if owner_id in owner_ids:
            errors.append(f"owners:{owner_id} duplicate id")
        owner_ids.add(owner_id)

    project_ids = set()
    projects_doc = load_json(root / "registry" / "projects.json")
    for project in projects_doc.get("projects", []):
        project_id = project.get("id")
        if not project_id:
            errors.append("projects: missing id")
            continue
        if project_id in project_ids:
            errors.append(f"projects:{project_id} duplicate id")
        project_ids.add(project_id)

    topic_ids = set()
    topics_doc = load_json(root / "registry" / "topics.json")
    for topic in topics_doc.get("topics", []):
        topic_id = topic.get("id")
        if not topic_id:
            errors.append("topics: missing id")
            continue
        if topic_id in topic_ids:
            errors.append(f"topics:{topic_id} duplicate id")
        topic_ids.add(topic_id)
        topic_domain = topic.get("domain")
        if not topic_domain:
            errors.append(f"topics:{topic_id} missing domain")
        else:
            topic_path = pathlib.Path(str(topic_domain))
            if topic_path.is_absolute():
                errors.append(f"topics:{topic_id} domain must be relative: {topic_domain}")
            elif not (root / topic_path).exists():
                errors.append(f"topics:{topic_id} domain path missing: {topic_domain}")
        allowed_kinds = topic.get("allowed_kinds")
        if not isinstance(allowed_kinds, list) or not allowed_kinds:
            errors.append(f"topics:{topic_id} missing allowed_kinds")
        else:
            for allowed_kind in allowed_kinds:
                if allowed_kind not in ALLOWED_ITEM_KINDS:
                    errors.append(f"topics:{topic_id} invalid allowed_kind: {allowed_kind}")

    migrations = load_jsonl(root / "registry" / "migrations.jsonl")
    local_migration_target_prefixes = (
        "artifacts/",
        "domains/",
        "registry/",
        "indexes/",
        "governance/",
        "tools/",
        "templates/",
    )
    for migration in migrations:
        migration_id = migration.get("to") or migration.get("mode") or "<unknown>"
        missing_fields = set()
        for field in ["from", "to", "mode", "status", "checked_at", "notes"]:
            if field not in migration:
                missing_fields.add(field)
                errors.append(f"migrations:{migration_id} missing {field}")
        is_bootstrap_empty = migration.get("mode") == "none" and migration.get("status") == "bootstrap-empty"
        for field in ["mode", "status", "checked_at", "notes"]:
            if field in missing_fields:
                continue
            if migration.get(field) in ("", None, []):
                errors.append(f"migrations:{migration_id} empty {field}")
        if not is_bootstrap_empty:
            for field in ["from", "to"]:
                if field in missing_fields:
                    continue
                if migration.get(field) in ("", None, []):
                    errors.append(f"migrations:{migration_id} empty {field}")
        checked_at = str(migration.get("checked_at", ""))
        try:
            dt.date.fromisoformat(checked_at)
        except Exception:
            errors.append(f"migrations:{migration_id} invalid checked_at: {checked_at}")
        target_refs = [part.strip() for part in re.split(r"\s*;\s*", str(migration.get("to", ""))) if part.strip()]
        for target_ref in target_refs:
            target_path = pathlib.Path(target_ref)
            if target_path.is_absolute():
                errors.append(f"migrations:{migration_id} to must be relative local path: {target_ref}")
                continue
            if not (target_ref.startswith(local_migration_target_prefixes) or target_ref in {"README.md", "AGENTS.md"}):
                errors.append(f"migrations:{migration_id} to must reference a Knowledge Hub local path: {target_ref}")
                continue
            if "*" in target_ref:
                if not list(root.glob(target_ref)):
                    errors.append(f"migrations:{migration_id} missing local glob target: {target_ref}")
            elif not (root / target_path).exists():
                errors.append(f"migrations:{migration_id} missing local target: {target_ref}")

    template_required_fields = [
        "id",
        "title",
        "kind",
        "domain",
        "path",
        "scope",
        "visibility",
        "status",
        "owner",
        "source",
        "review_after",
        "created_at",
        "updated_at",
    ]
    template_skip = {"README.md", "migration-record.md"}
    for template_path in sorted((root / "templates").glob("*.md")):
        rel_template = template_path.relative_to(root)
        if template_path.name in template_skip:
            continue
        template_text = template_path.read_text()
        for field in template_required_fields:
            if not re.search(rf"^{re.escape(field)}:", template_text, re.MULTILINE):
                errors.append(f"template:{rel_template} missing {field}")
        if template_path.name == "artifact-ref.md":
            for field in ["uri", "size", "sha256"]:
                if not re.search(rf"^{re.escape(field)}:", template_text, re.MULTILINE):
                    errors.append(f"template:{rel_template} artifact-ref missing {field}")

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
        item_dates = {}
        for field in ["created_at", "updated_at", "review_after"]:
            value = str(item.get(field, ""))
            if not value:
                continue
            try:
                item_dates[field] = dt.date.fromisoformat(value)
            except Exception:
                errors.append(f"items:{item_id} invalid {field}: {value}")
        if item_dates.get("created_at") and item_dates.get("updated_at"):
            if item_dates["updated_at"] < item_dates["created_at"]:
                errors.append(
                    f"items:{item_id} updated_at before created_at: {item.get('updated_at')} < {item.get('created_at')}"
                )
        if item.get("owner") and item.get("owner") not in owner_ids:
            errors.append(f"items:{item_id} owner not registered: {item.get('owner')}")
        if item.get("kind") and item.get("kind") not in ALLOWED_ITEM_KINDS:
            errors.append(f"items:{item_id} invalid kind: {item.get('kind')}")
        if item.get("status") and item.get("status") not in ALLOWED_ITEM_STATUSES:
            errors.append(f"items:{item_id} invalid status: {item.get('status')}")
        if item.get("scope") and item.get("scope") not in ALLOWED_ITEM_SCOPES:
            errors.append(f"items:{item_id} invalid scope: {item.get('scope')}")
        if item.get("visibility") and item.get("visibility") not in ALLOWED_ITEM_VISIBILITIES:
            errors.append(f"items:{item_id} invalid visibility: {item.get('visibility')}")
        domain = str(item.get("domain", ""))
        domain_root = domain.split("/", 1)[0] if domain else ""
        if domain and domain_root not in ALLOWED_DOMAIN_ROOTS:
            errors.append(f"items:{item_id} invalid domain root: {domain}")
        if item.get("scope") == "project-specific" and not domain.startswith("projects/"):
            errors.append(f"items:{item_id} project-specific scope outside projects domain: {domain}")
        if domain.startswith("projects/"):
            project_id = domain.split("/", 1)[1]
            if project_id not in project_ids:
                errors.append(f"items:{item_id} project not registered: {project_id}")
        if item.get("scope") == "codex-memory-curation-governance" and domain != "codex":
            errors.append(f"items:{item_id} codex memory scope outside codex domain: {domain}")
        rel_path = pathlib.Path(str(item.get("path", "")))
        if rel_path.is_absolute():
            errors.append(f"items:{item_id} path must be relative: {rel_path}")
        elif not (root / rel_path).exists():
            errors.append(f"items:{item_id} path missing: {rel_path}")
        path_text = str(item.get("path", ""))
        if domain == "root" and path_text not in {"README.md", "AGENTS.md"}:
            errors.append(f"items:{item_id} root domain path outside root docs: {path_text}")
        if domain == "governance" and not path_text.startswith(("governance/", "registry/", "indexes/", "tools/", "templates/", "artifacts/manifests/")):
            errors.append(f"items:{item_id} governance domain path outside governance control plane: {path_text}")
        if domain.startswith("projects/"):
            project_id = domain.split("/", 1)[1]
            if not path_text.startswith((f"domains/projects/{project_id}/", "artifacts/manifests/")):
                errors.append(f"items:{item_id} project domain path mismatch: domain={domain} path={path_text}")
        if domain == "codex" and not path_text.startswith(("domains/codex/", "artifacts/manifests/")):
            errors.append(f"items:{item_id} codex domain path outside codex control plane: {path_text}")
        if domain == "embedded" and not path_text.startswith(("domains/embedded/", "artifacts/manifests/")):
            errors.append(f"items:{item_id} embedded domain path outside embedded/control artifacts: {path_text}")
        if domain == "patents" and not path_text.startswith(("domains/patents/", "artifacts/manifests/")):
            errors.append(f"items:{item_id} patents domain path outside patents/control artifacts: {path_text}")
        if domain == "personal" and not path_text.startswith(("domains/personal/", "artifacts/manifests/")):
            errors.append(f"items:{item_id} personal domain path outside personal/control artifacts: {path_text}")
        status = item.get("status")
        if status in {"active", "reviewing"}:
            if not item.get("owner"):
                errors.append(f"items:{item_id} active/reviewing missing owner")
            review_date = item_dates.get("review_after")
            if review_date:
                if review_date < today:
                    warnings.append(f"items:{item_id} review_after is stale: {item.get('review_after')}")
        if status == "superseded" and not item.get("superseded_by"):
            errors.append(f"items:{item_id} superseded missing superseded_by")
        if item.get("kind") == "artifact-ref":
            for field in ["uri", "size", "sha256"]:
                if not item.get(field):
                    errors.append(f"items:{item_id} artifact-ref missing {field}")
        if item.get("scope") == "project-specific" and str(item.get("path", "")).startswith("domains/embedded/standards/"):
            errors.append(f"items:{item_id} project-specific under embedded standards")
        if item.get("visibility") == "personal-local" and item.get("status") == "active":
            errors.append(f"items:{item_id} personal-local item must not be active")
        if item.get("generated_by_ai") is True and item.get("status") == "active":
            missing_review = [
                field
                for field in ["human_reviewed_by", "human_reviewed_at", "review_basis"]
                if not item.get(field)
            ]
            if missing_review:
                errors.append(
                    f"items:{item_id} ai-generated active item missing human review fields: {','.join(missing_review)}"
                )

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

    def status_bucket_ids(path, bucket):
        if not path.exists():
            errors.append(f"index missing: {path.relative_to(root)}")
            return set()
        found = set()
        prefix = f"- {bucket}:"
        for line in path.read_text().splitlines():
            if not line.startswith(prefix):
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

    items_by_id = {item.get("id"): item for item in items if item.get("id")}
    active_index_ids = status_bucket_ids(root / "indexes" / "by-status.md", "active")
    for indexed_id in sorted(active_index_ids):
        item = items_by_id.get(indexed_id)
        if not item:
            continue
        if item.get("visibility") == "personal-local" or item.get("domain") == "personal":
            errors.append(f"index:indexes/by-status.md active bucket references personal-local item {indexed_id}")

    local_path_prefixes = (
        "artifacts/",
        "domains/",
        "registry/",
        "indexes/",
        "governance/",
        "tools/",
        "templates/",
    )
    for index_path in sorted((root / "indexes").glob("*.md")):
        text = index_path.read_text()
        for ref in sorted(set(re.findall(r"`([^`]+)`", text))):
            if not (ref.startswith(local_path_prefixes) or ref in {"README.md", "AGENTS.md"}):
                continue
            if "*" in ref:
                if not list(root.glob(ref)):
                    errors.append(f"index:{index_path.relative_to(root)} missing local glob reference {ref}")
            elif not (root / ref).exists():
                errors.append(f"index:{index_path.relative_to(root)} missing local path reference {ref}")

    secret_patterns = [
        re.compile(r"-----BEGIN (RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----"),
        re.compile(r"(?i)(api[_-]?key|token|password|passwd|secret)\s*[:=]\s*['\"]?[^'\"\s]{12,}"),
        re.compile(r"(?i)cookie\s*[:=]\s*['\"]?[^'\"\s]{12,}"),
    ]
    scan_roots = [
        root / "domains",
        root / "registry",
        root / "governance",
        root / "templates",
        root / "artifacts" / "manifests",
    ]
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
