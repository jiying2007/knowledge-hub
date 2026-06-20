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
parser.add_argument("--explain", default="", metavar="ITEM_ID")
parser.add_argument("--diagnostics", action="store_true")
args = parser.parse_args(argv)

errors = []
warnings = []
explain = None
if args.project:
    warnings.append(f"knowledge-check: --project is reserved and does not narrow validation scope: {args.project}")
if args.domain:
    warnings.append(f"knowledge-check: --domain is reserved and does not narrow validation scope: {args.domain}")
if args.sources_only and args.explain:
    warnings.append(f"knowledge-check: --explain is ignored with --sources-only: {args.explain}")

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
ALLOWED_ITEM_PROMOTIONS = {
    "none",
}
OWNER_GATE_BLOCKING_REVIEW_STATUSES = {
    "pending-owner-review",
    "needs-owner-resolution",
    "owner-intake-ready",
    "source-identity-match",
    "embedded-knowledge-owner-review-required",
    "blocked-pending-owner-review",
    "blocked-pending-owner-status-decision",
    "blocked-personal-local",
    "blocked-pending-archive-metadata",
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
    "project-current-tools-source",
    "project-current-knowledge-source",
    "project-product-test-source",
    "project-scratch-source",
    "project-root-artifact-source",
    "project-agent-rules-source",
    "project-agent-config-source",
}
ALLOWED_SOURCE_AUTHORITIES = {
    "legacy-team-ssot",
    "legacy-project-history",
    "patent-materials",
    "codex-workflow-history",
    "auxiliary-recall-only",
    "legacy-project-current-docs",
    "legacy-project-current-tools",
    "legacy-project-current-knowledge",
    "legacy-project-product-test",
    "legacy-project-scratch",
    "legacy-project-root-artifacts",
    "legacy-project-agent-rules",
    "legacy-project-agent-config",
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
ALLOWED_SOURCE_FINAL_DISPOSITIONS = {
    "fully-migrated",
    "copy-first-migrated",
    "reference-first-registered",
    "artifact-ref-registered",
    "archive-only-registered",
    "owner-gated-pending-decision",
    "no-migration-with-reason",
    "auxiliary-recall-only",
    "external-tool-owned",
    "mixed-terminal-coverage",
}
SHA256_RE = re.compile(r"[0-9a-f]{64}")

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

def build_diagnostics(error_items, warning_items):
    rules = [
        (
            "registry-parse",
            "registry JSON/JSONL 解析失败",
            "先修复对应 registry 文件的 JSON 或 JSONL 语法，再重跑 knowledge-check。",
            lambda msg: "invalid json" in msg or "invalid jsonl" in msg,
        ),
        (
            "source-registry",
            "source registry 字段或枚举异常",
            "检查 registry/sources.json 中对应 source 的 id、role、authority、status 和 write_policy。",
            lambda msg: msg.startswith("sources:"),
        ),
        (
            "source-index",
            "source index 漏登或残留",
            "同步 indexes/by-source.md 的 Knowledge Sources 表，确保和 registry/sources.json 一致。",
            lambda msg: msg.startswith("index:indexes/by-source.md"),
        ),
        (
            "source-coverage",
            "source coverage 终态矩阵异常",
            "更新最新 artifacts/manifests/knowledge-hub-source-coverage-closeout-*.jsonl，确保每个 registered source 都有终态分类、决策和风险说明。",
            lambda msg: msg.startswith("source-coverage:"),
        ),
        (
            "owner-gated-active",
            "owner-gated 源路径被提升为 active",
            "检查 owner decision worksheets 和 item owner gate 字段；未完成 owner 决策、目标决策和复核证据前，不要登记为 active。",
            lambda msg: msg.startswith(("owner-gated:", "owner-gate:")),
        ),
        (
            "owner-project-topic-registry",
            "owner/project/topic registry 异常",
            "检查 registry/owners.json、registry/projects.json 或 registry/topics.json 的登记项和枚举。",
            lambda msg: msg.startswith(("owners:", "projects:", "topics:")),
        ),
        (
            "migration-record",
            "migration 记录异常",
            "检查 registry/migrations.jsonl 的 from、to、mode、status、checked_at、notes 和本地目标路径。",
            lambda msg: msg.startswith("migrations:"),
        ),
        (
            "template-schema",
            "模板字段缺失",
            "检查 templates/*.md，补齐 registry/schema.md 要求的字段，保持人工新增入口可用。",
            lambda msg: msg.startswith("template:"),
        ),
        (
            "manual-entry",
            "人工新增入口过期",
            "同步 tools/knowledge-new.sh 和 templates/README.md 中当前 registry/index/migration 门禁提示。",
            lambda msg: msg.startswith("manual-entry:"),
        ),
        (
            "item-source-ref",
            "item source 或 artifact 引用异常",
            "检查 registry/items.jsonl 中 source_id、migration_manifest、source_sha256 或 artifact-ref 元数据。",
            lambda msg: msg.startswith("items:") and any(
                token in msg
                for token in [
                    "source_id",
                    "migration_manifest",
                    "source_sha256",
                    "artifact-ref",
                    "artifact ",
                    "artifact sha256",
                    "artifact size",
                ]
            ),
        ),
        (
            "validation-ref",
            "validation_refs 异常",
            "检查 registry/items.jsonl 中 validation_refs 是否为非空字符串列表；本地路径必须存在，命令型引用不会被执行。",
            lambda msg: msg.startswith("items:") and "validation_ref" in msg,
        ),
        (
            "item-boundary",
            "item 字段、枚举或边界异常",
            "检查 registry/items.jsonl 中对应 item 的必填字段、枚举、domain/path/scope/visibility 边界。",
            lambda msg: msg.startswith("items:"),
        ),
        (
            "core-index",
            "核心索引覆盖异常",
            "同步 indexes/by-owner.md、indexes/by-review-date.md、indexes/by-status.md，确保每个 registry item 恰好有规范引用。",
            lambda msg: msg.startswith(("index:indexes/by-owner.md", "index:indexes/by-review-date.md", "index:indexes/by-status.md")),
        ),
        (
            "decision-index",
            "决策索引覆盖异常",
            "同步 registry/decisions.jsonl 与 indexes/by-decision.md，只要求 registry decision 在决策索引中恰好出现一次，不把 owner worksheet 或 migration decision 当作 registry decision。",
            lambda msg: msg.startswith("index:indexes/by-decision.md"),
        ),
        (
            "index-local-ref",
            "索引中的本地路径引用失效",
            "检查 indexes/*.md 中反引号包裹的本地路径或 glob，修正为存在的 Knowledge Hub 相对路径。",
            lambda msg: msg.startswith("index:") and "missing local" in msg,
        ),
        (
            "active-safety",
            "active 安全边界异常",
            "检查 active bucket、personal-local、AI 生成内容人工复核字段，未满足门禁前不要提升为 active。",
            lambda msg: "active bucket references" in msg or "personal-local" in msg or "ai-generated active" in msg,
        ),
        (
            "secret-pattern",
            "疑似 secret 模式命中",
            "立即检查对应文本，移除 token、private key、password、cookie 等运行时 secret；保留脱敏引用。",
            lambda msg: msg.startswith("secret-pattern:"),
        ),
        (
            "explain",
            "explain 目标不存在",
            "确认 --explain 参数使用的是 registry/items.jsonl 中真实存在的 item id。",
            lambda msg: msg.startswith("explain:"),
        ),
    ]
    buckets = {}
    for message in error_items:
        category = None
        for category_id, title_zh, action_zh, matcher in rules:
            if matcher(message):
                category = (category_id, title_zh, action_zh)
                break
        if category is None:
            category = ("other", "未分类错误", "查看原始 ERROR 行，必要时补充 diagnostics 分类规则。")
        category_id, title_zh, action_zh = category
        bucket = buckets.setdefault(
            category_id,
            {
                "id": category_id,
                "title_zh": title_zh,
                "severity": "error",
                "count": 0,
                "action_zh": action_zh,
                "examples": [],
            },
        )
        bucket["count"] += 1
        if len(bucket["examples"]) < 5:
            bucket["examples"].append(message)
    warning_examples = list(warning_items[:5])
    return {
        "summary_zh": f"发现 {len(error_items)} 个错误，{len(warning_items)} 个警告，归类为 {len(buckets)} 类。",
        "categories": sorted(buckets.values(), key=lambda item: (-item["count"], item["id"])),
        "warnings": {
            "count": len(warning_items),
            "examples": warning_examples,
            "action_zh": "warning 不阻断检查，但应按 review_after、兼容参数或外部 source 可用性安排人工复核。",
        },
    }

sources_path = root / "registry" / "sources.json"
sources = load_json(sources_path).get("sources", [])
owner_ids_for_sources = {
    owner.get("id", "")
    for owner in load_json(root / "registry" / "owners.json").get("owners", [])
    if owner.get("id")
}
source_ids = set()
for source in sources:
    for field in ["id", "path", "role", "authority", "status", "write_policy", "migration_strategy", "owner", "review_after", "final_disposition"]:
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
    if source.get("owner") and source.get("owner") not in owner_ids_for_sources:
        errors.append(f"sources:{source_id} unknown owner: {source.get('owner')}")
    if source.get("review_after"):
        try:
            dt.date.fromisoformat(str(source.get("review_after")))
        except Exception:
            errors.append(f"sources:{source_id} invalid review_after: {source.get('review_after')}")
    if source.get("final_disposition") and source.get("final_disposition") not in ALLOWED_SOURCE_FINAL_DISPOSITIONS:
        errors.append(f"sources:{source_id} invalid final_disposition: {source.get('final_disposition')}")
    if not str(source.get("check", "")).strip() and not str(source.get("no_check_reason", "")).strip():
        errors.append(f"sources:{source_id} missing no_check_reason for empty check")
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

    source_coverage_paths = sorted((root / "artifacts" / "manifests").glob("knowledge-hub-source-coverage-closeout-*.jsonl"))
    if not source_coverage_paths:
        errors.append("source-coverage: missing knowledge-hub-source-coverage-closeout manifest")
    else:
        source_coverage_path = source_coverage_paths[-1]
        source_coverage_rows = load_jsonl(source_coverage_path)
        source_coverage_ids = set()
        for row in source_coverage_rows:
            row_source_id = row.get("source_id")
            row_id = row.get("id", row_source_id or "<unknown>")
            if not row_source_id:
                errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} row {row_id} missing source_id")
                continue
            if row_source_id in source_coverage_ids:
                errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} duplicate source {row_source_id}")
            source_coverage_ids.add(row_source_id)
            for field in ["status", "classification", "decision", "risk", "owner", "checked_at"]:
                if not row.get(field):
                    errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} source {row_source_id} missing {field}")
            checked_at = str(row.get("checked_at", ""))
            if checked_at:
                try:
                    dt.date.fromisoformat(checked_at)
                except Exception:
                    errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} source {row_source_id} invalid checked_at: {checked_at}")
        for source_id in sorted(source_ids):
            if source_id not in source_coverage_ids:
                errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} missing source {source_id}")
        for covered_source_id in sorted(source_coverage_ids):
            if covered_source_id not in source_ids:
                errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} stale source {covered_source_id}")

    def owner_gate_value_filled(value):
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict)):
            return bool(value)
        return True

    def owner_gate_row_resolved(row):
        row_state = " ".join(
            str(row.get(field, ""))
            for field in ["worksheet_status", "row_status", "status", "default_state"]
        ).lower()
        if not any(token in row_state for token in ("resolved", "owner-approved", "approved", "closed")):
            return False
        required_fields = list(row.get("required_owner_fields", []))
        for field in ["owner_decision", "target_decision", "reviewed_by", "reviewed_at", "review_after", "source_status", "evidence_refs", "status_reason"]:
            if field not in required_fields:
                required_fields.append(field)
        return all(owner_gate_value_filled(row.get(field)) for field in required_fields)

    owner_gated_source_paths = {}
    owner_gate_paths = sorted((root / "artifacts" / "manifests").glob("*owner-decision-worksheets-*.jsonl"))
    for owner_gate_path in owner_gate_paths:
        for row in load_jsonl(owner_gate_path):
            row_source_id = row.get("source_id")
            row_source_path = row.get("source_path")
            if not row_source_id or not row_source_path:
                continue
            if owner_gate_row_resolved(row):
                continue
            owner_gated_source_paths[(row_source_id, row_source_path)] = owner_gate_path.relative_to(root)

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

    local_path_prefixes = (
        "artifacts/",
        "docs/",
        "domains/",
        "registry/",
        "indexes/",
        "governance/",
        "tools/",
        "templates/",
    )
    migrations = load_jsonl(root / "registry" / "migrations.jsonl")
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
            if not (target_ref.startswith(local_path_prefixes) or target_ref in {"README.md", "AGENTS.md"}):
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
        "promotion",
        "tags",
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

    manual_entry_terms = [
        "promotion",
        "tags",
        "validation_refs",
        "indexes/by-owner.md",
        "indexes/by-review-date.md",
        "indexes/by-status.md",
        "- reviewing:",
        "registry/migrations.jsonl",
        "duplicate",
    ]
    manual_entry_files = [
        root / "tools" / "knowledge-new.sh",
        root / "templates" / "README.md",
    ]
    for manual_entry_file in manual_entry_files:
        manual_text = manual_entry_file.read_text()
        rel_manual = manual_entry_file.relative_to(root)
        for term in manual_entry_terms:
            if term not in manual_text:
                errors.append(f"manual-entry:{rel_manual} missing current gate term: {term}")

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
        for field in ["title", "kind", "domain", "path", "scope", "visibility", "status", "owner", "source", "review_after", "created_at", "updated_at", "promotion", "tags"]:
            if field not in item or item.get(field) in ("", None, []):
                errors.append(f"items:{item_id} missing {field}")
        tags = item.get("tags")
        if tags is not None:
            if not isinstance(tags, list):
                errors.append(f"items:{item_id} tags must be list")
            else:
                for tag in tags:
                    if not isinstance(tag, str) or not tag.strip():
                        errors.append(f"items:{item_id} invalid tag: {tag}")
        if item.get("promotion") and item.get("promotion") not in ALLOWED_ITEM_PROMOTIONS:
            errors.append(f"items:{item_id} invalid promotion: {item.get('promotion')}")
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
        validation_refs = item.get("validation_refs")
        if item.get("status") in {"active", "reviewing"}:
            if validation_refs in (None, []):
                errors.append(f"items:{item_id} active/reviewing missing validation_refs")
        if validation_refs is not None:
            if not isinstance(validation_refs, list):
                errors.append(f"items:{item_id} validation_refs must be list")
            else:
                for validation_ref in validation_refs:
                    if not isinstance(validation_ref, str) or not validation_ref.strip():
                        errors.append(f"items:{item_id} invalid validation_ref: {validation_ref}")
                        continue
                    if " " in validation_ref:
                        continue
                    if pathlib.Path(validation_ref).is_absolute() or validation_ref.startswith(("./", "../")):
                        errors.append(f"items:{item_id} validation_ref must be repo-relative or command: {validation_ref}")
                        continue
                    if validation_ref.startswith(local_path_prefixes) or validation_ref in {"README.md", "AGENTS.md"}:
                        if not (root / validation_ref).exists():
                            errors.append(f"items:{item_id} validation_ref missing local path: {validation_ref}")
                    elif "/" in validation_ref or pathlib.Path(validation_ref).suffix:
                        errors.append(f"items:{item_id} unsupported validation_ref format: {validation_ref}")
        source = item.get("source")
        if source and not isinstance(source, dict):
            errors.append(f"items:{item_id} source must be object")
            source = {}
        if isinstance(source, dict):
            item_source_id = source.get("source_id")
            if item_source_id and item_source_id not in source_ids:
                errors.append(f"items:{item_id} source_id not registered: {item_source_id}")
            migration_manifest = source.get("migration_manifest")
            if migration_manifest:
                manifest_path = pathlib.Path(str(migration_manifest))
                if manifest_path.is_absolute():
                    errors.append(f"items:{item_id} migration_manifest must be relative: {migration_manifest}")
                elif not (root / manifest_path).exists():
                    errors.append(f"items:{item_id} migration_manifest missing: {migration_manifest}")
            source_sha256 = source.get("source_sha256")
            if source_sha256 and not SHA256_RE.fullmatch(str(source_sha256)):
                errors.append(f"items:{item_id} invalid source_sha256: {source_sha256}")
            item_source_path = source.get("source_path")
            if item.get("status") == "active" and item_source_id and item_source_path:
                owner_gate_path = owner_gated_source_paths.get((item_source_id, item_source_path))
                if owner_gate_path:
                    errors.append(
                        f"owner-gated:{item_id} active item references unresolved owner-gated source "
                        f"{item_source_id}:{item_source_path} ({owner_gate_path})"
                    )
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
        if domain == "governance" and not path_text.startswith(("governance/", "registry/", "indexes/", "tools/", "templates/", "docs/goals/", "artifacts/manifests/")):
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
        if status == "active":
            owner_gate_verified = item.get("owner_gate_verified")
            if owner_gate_verified is False or str(owner_gate_verified).strip().lower() == "false":
                errors.append(f"owner-gate:{item_id} active item has owner_gate_verified=false")
            review_status = str(item.get("review_status", "")).strip()
            if review_status in OWNER_GATE_BLOCKING_REVIEW_STATUSES:
                errors.append(f"owner-gate:{item_id} active item has blocking review_status: {review_status}")
        if status == "superseded" and not item.get("superseded_by"):
            errors.append(f"items:{item_id} superseded missing superseded_by")
        if item.get("kind") == "artifact-ref":
            for field in ["uri", "size", "sha256"]:
                if not item.get(field):
                    errors.append(f"items:{item_id} artifact-ref missing {field}")
            if item.get("sha256") and not SHA256_RE.fullmatch(str(item.get("sha256"))):
                errors.append(f"items:{item_id} invalid artifact sha256: {item.get('sha256')}")
            if item.get("size") and (not isinstance(item.get("size"), int) or item.get("size") <= 0):
                errors.append(f"items:{item_id} invalid artifact size: {item.get('size')}")
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

    def item_ref_counts(path, canonical_status_only=False):
        if not path.exists():
            errors.append(f"index missing: {path.relative_to(root)}")
            return {}
        counts = {}
        lines = path.read_text().splitlines()
        range_pattern = re.compile(r"`([^`]+?)(\d+)`\.\.`([^`]+?)(\d+)`")
        for line in lines:
            if canonical_status_only and not (
                line.startswith("- active:") or line.startswith("- reviewing:") or line.startswith("- archived:")
            ):
                continue
            explicit_line = range_pattern.sub("", line)
            for ref in re.findall(r"`([^`]+)`", explicit_line):
                if ref in ids:
                    counts[ref] = counts.get(ref, 0) + 1
            for ref in expand_range_ids(line, path):
                if ref in ids:
                    counts[ref] = counts.get(ref, 0) + 1
        return counts

    decision_rows = load_jsonl(root / "registry" / "decisions.jsonl")
    registry_decision_ids = set()
    for decision in decision_rows:
        decision_id = str(decision.get("decision_id", "")).strip()
        if not decision_id:
            errors.append("decisions: missing decision_id")
            continue
        if decision_id in registry_decision_ids:
            errors.append(f"decisions:{decision_id} duplicate decision_id")
        registry_decision_ids.add(decision_id)

    by_decision_path = root / "indexes" / "by-decision.md"
    by_decision_counts = {}
    if not by_decision_path.exists():
        errors.append("index missing: indexes/by-decision.md")
    else:
        for ref in re.findall(r"`([^`]+)`", by_decision_path.read_text()):
            if ref in registry_decision_ids:
                by_decision_counts[ref] = by_decision_counts.get(ref, 0) + 1
    for decision_id in sorted(registry_decision_ids):
        count = by_decision_counts.get(decision_id, 0)
        if count == 0:
            errors.append(f"index:indexes/by-decision.md missing registry decision {decision_id}")
        elif count > 1:
            errors.append(f"index:indexes/by-decision.md duplicate registry decision {decision_id} ({count}x)")

    index_requirements = {
        "indexes/by-owner.md": "owner",
        "indexes/by-review-date.md": "review_after",
        "indexes/by-status.md": "status",
    }
    for rel_index, field in index_requirements.items():
        index_path = root / rel_index
        if rel_index == "indexes/by-status.md":
            status_seen = {status: status_bucket_ids(index_path, status) for status in ["active", "reviewing", "archived"]}
            seen = set().union(*status_seen.values())
        else:
            status_seen = {}
            seen = indexed_ids(index_path)
        for item in items:
            item_id = item.get("id")
            if item_id and item_id not in seen:
                errors.append(f"index:{rel_index} missing item {item_id} ({field}={item.get(field, '<missing>')})")
            if rel_index == "indexes/by-status.md" and item_id:
                expected_status = item.get("status", "")
                if expected_status in status_seen and item_id in seen and item_id not in status_seen[expected_status]:
                    found_buckets = [status for status, bucket_ids in status_seen.items() if item_id in bucket_ids]
                    errors.append(
                        f"index:{rel_index} item {item_id} in wrong status bucket "
                        f"(registry status={expected_status}, buckets={','.join(found_buckets) or '<none>'})"
                    )
        stale_seen = seen if rel_index == "indexes/by-status.md" else seen
        for indexed_id in sorted(stale_seen):
            if indexed_id not in ids:
                errors.append(f"index:{rel_index} stale item reference {indexed_id}")
        duplicate_counts = item_ref_counts(root / rel_index, canonical_status_only=rel_index == "indexes/by-status.md")
        for indexed_id, count in sorted(duplicate_counts.items()):
            if count > 1:
                errors.append(f"index:{rel_index} duplicate item reference {indexed_id} ({count}x)")

    items_by_id = {item.get("id"): item for item in items if item.get("id")}
    if args.explain:
        explain_id = args.explain
        explained_item = items_by_id.get(explain_id)
        explain = {
            "id": explain_id,
            "found": bool(explained_item),
            "registry": {},
            "indexes": {},
            "maintenance_hints": [],
        }
        if not explained_item:
            errors.append(f"explain:{explain_id} item not found")
        else:
            explained_path = pathlib.Path(str(explained_item.get("path", "")))
            explained_path_exists = (
                bool(str(explained_item.get("path", "")))
                and not explained_path.is_absolute()
                and (root / explained_path).exists()
            )
            validation_refs = explained_item.get("validation_refs", [])
            if not isinstance(validation_refs, list):
                validation_refs = []
            explain["registry"] = {
                "title": explained_item.get("title", ""),
                "kind": explained_item.get("kind", ""),
                "domain": explained_item.get("domain", ""),
                "path": explained_item.get("path", ""),
                "path_exists": explained_path_exists,
                "scope": explained_item.get("scope", ""),
                "visibility": explained_item.get("visibility", ""),
                "status": explained_item.get("status", ""),
                "owner": explained_item.get("owner", ""),
                "review_after": explained_item.get("review_after", ""),
                "promotion": explained_item.get("promotion", ""),
                "tags_count": len(explained_item.get("tags", [])) if isinstance(explained_item.get("tags"), list) else 0,
                "validation_refs_count": len(validation_refs),
            }
            for rel_index in ["indexes/by-owner.md", "indexes/by-review-date.md", "indexes/by-status.md"]:
                canonical_only = rel_index == "indexes/by-status.md"
                ref_count = item_ref_counts(root / rel_index, canonical_status_only=canonical_only).get(explain_id, 0)
                if ref_count == 0:
                    index_status = "missing"
                    explain["maintenance_hints"].append(f"{rel_index}: add `{explain_id}` to the appropriate section")
                elif ref_count == 1:
                    index_status = "ok"
                else:
                    index_status = "duplicate"
                    explain["maintenance_hints"].append(f"{rel_index}: keep exactly one canonical `{explain_id}` reference")
                explain["indexes"][rel_index] = {
                    "reference_count": ref_count,
                    "status": index_status,
                }
            status_index_path = root / "indexes" / "by-status.md"
            for bucket in ["active", "reviewing", "archived"]:
                if explain_id in status_bucket_ids(status_index_path, bucket):
                    explain["indexes"]["indexes/by-status.md"]["bucket"] = bucket
                    break
            if not explained_path_exists:
                explain["maintenance_hints"].append("registry path is missing or absolute; keep item path repo-relative and existing")
            if explained_item.get("status") in {"active", "reviewing"} and not validation_refs:
                explain["maintenance_hints"].append("active/reviewing item needs non-empty validation_refs")
            if not explain["maintenance_hints"]:
                explain["maintenance_hints"].append("no immediate manual maintenance action detected for this item")

    active_index_ids = status_bucket_ids(root / "indexes" / "by-status.md", "active")
    for indexed_id in sorted(active_index_ids):
        item = items_by_id.get(indexed_id)
        if not item:
            continue
        if item.get("visibility") == "personal-local" or item.get("domain") == "personal":
            errors.append(f"index:indexes/by-status.md active bucket references personal-local item {indexed_id}")

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
if explain is not None:
    result["explain"] = explain
if args.diagnostics:
    result["diagnostics"] = build_diagnostics(errors, warnings)
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
    if explain is not None:
        print("explain:")
        print(f"  id: {explain['id']}")
        print(f"  found: {str(explain['found']).lower()}")
        if explain["registry"]:
            registry = explain["registry"]
            print(f"  title: {registry.get('title', '')}")
            print(f"  status: {registry.get('status', '')}")
            print(f"  owner: {registry.get('owner', '')}")
            print(f"  path: {registry.get('path', '')}")
            print(f"  path_exists: {str(registry.get('path_exists', False)).lower()}")
        for rel_index, detail in explain["indexes"].items():
            bucket = f", bucket={detail['bucket']}" if "bucket" in detail else ""
            print(f"  index {rel_index}: {detail['status']} ({detail['reference_count']}x{bucket})")
        for hint in explain["maintenance_hints"]:
            print(f"  hint: {hint}")
    if args.diagnostics:
        diagnostics = result["diagnostics"]
        print("diagnostics:")
        print(f"  summary: {diagnostics['summary_zh']}")
        for category in diagnostics["categories"]:
            print(f"  category {category['id']}: {category['title_zh']} ({category['count']}x)")
            print(f"    action: {category['action_zh']}")
            for example in category["examples"]:
                print(f"    example: {example}")
        if diagnostics["warnings"]["count"]:
            print(f"  warnings: {diagnostics['warnings']['count']}x")
            print(f"    action: {diagnostics['warnings']['action_zh']}")
            for example in diagnostics["warnings"]["examples"]:
                print(f"    example: {example}")
sys.exit(0 if not errors else 1)
PY
