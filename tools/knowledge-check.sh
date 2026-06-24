#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import json
import os
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
parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD", help="Use a fixed date for review_after checks.")
args = parser.parse_args(argv)

errors = []
warnings = []
explain = None
READABILITY_GATE_START = dt.date(2026, 6, 21)

def resolve_today():
    if args.as_of:
        raw_value = args.as_of
        source = "arg:--as-of"
    else:
        raw_value = os.environ.get("KNOWLEDGE_TODAY", "")
        source = "env:KNOWLEDGE_TODAY" if raw_value else "system-date"
    if raw_value:
        try:
            return dt.date.fromisoformat(raw_value), source
        except Exception:
            parser.error(f"invalid date for {source}: {raw_value}")
    return dt.date.today(), source

today, today_source = resolve_today()

SOURCE_COVERAGE_RE = re.compile(r"^knowledge-hub-source-coverage-closeout-(\d{8})\.jsonl$")
TEXT_FILE_SUFFIXES = {".md", ".json", ".jsonl", ".sh", ".txt"}

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

def iter_text_files(scan_roots, suffixes=TEXT_FILE_SUFFIXES):
    seen_paths = set()
    for base in scan_roots:
        if not base.exists():
            continue
        candidates = [base] if base.is_file() else base.rglob("*")
        for path in candidates:
            if path in seen_paths:
                continue
            seen_paths.add(path)
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            yield path

EXPECTED_BOUNDARY_MANIFESTS = {
    "pcr02-tools-boundary-20260620": {
        "md": "artifacts/manifests/pcr02-tools-boundary-20260620.md",
        "jsonl": "artifacts/manifests/pcr02-tools-boundary-20260620.jsonl",
        "source_id": "pcr02-project-tools",
        "required_text": "memory-candidate-automation-ref",
    },
    "pcr02-knowledge-secret-config-boundary-20260620": {
        "md": "artifacts/manifests/pcr02-knowledge-secret-config-boundary-20260620.md",
        "jsonl": "artifacts/manifests/pcr02-knowledge-secret-config-boundary-20260620.jsonl",
        "source_id": "pcr02-project-knowledge",
        "required_text": "project-local-standard-candidate",
    },
    "pcr02-product-test-artifact-config-interface-boundary-20260620": {
        "md": "artifacts/manifests/pcr02-product-test-artifact-config-interface-boundary-20260620.md",
        "jsonl": "artifacts/manifests/pcr02-product-test-artifact-config-interface-boundary-20260620.jsonl",
        "source_id": "pcr02-product-test",
        "required_text": "build-artifact-generated",
    },
    "pcr02-scratch-archive-boundary-20260620": {
        "md": "artifacts/manifests/pcr02-scratch-archive-boundary-20260620.md",
        "jsonl": "artifacts/manifests/pcr02-scratch-archive-boundary-20260620.jsonl",
        "source_id": "pcr02-project-scratch",
        "required_text": "historical-session-evidence",
    },
    "pcr02-root-artifacts-boundary-20260620": {
        "md": "artifacts/manifests/pcr02-root-artifacts-boundary-20260620.md",
        "jsonl": "artifacts/manifests/pcr02-root-artifacts-boundary-20260620.jsonl",
        "source_id": "pcr02-project-root-artifacts",
        "required_text": "source-coverage-evidence-drift",
    },
    "pcr02-module-agent-rules-boundary-20260620": {
        "md": "artifacts/manifests/pcr02-module-agent-rules-boundary-20260620.md",
        "jsonl": "artifacts/manifests/pcr02-module-agent-rules-boundary-20260620.jsonl",
        "source_id": "pcr02-module-agent-rules",
        "required_text": "module-local-owner-gated-control-entry-rule",
    },
    "pcr02-agent-config-boundary-20260620": {
        "md": "artifacts/manifests/pcr02-agent-config-boundary-20260620.md",
        "jsonl": "artifacts/manifests/pcr02-agent-config-boundary-20260620.jsonl",
        "source_id": "pcr02-project-agent-config",
        "required_text": "third-party-dependency-artifact",
    },
}

def select_source_coverage_closeout(root):
    paths = sorted((root / "artifacts" / "manifests").glob("knowledge-hub-source-coverage-closeout-*.jsonl"))
    dated = []
    ignored = []
    for path in paths:
        relative = str(path.relative_to(root))
        match = SOURCE_COVERAGE_RE.match(path.name)
        if not match:
            ignored.append(relative)
            continue
        date_text = match.group(1)
        try:
            dt.datetime.strptime(date_text, "%Y%m%d").date()
        except Exception:
            ignored.append(relative)
            continue
        dated.append((date_text, relative, path))
    dated.sort(key=lambda row: (row[0], row[1]))
    selection = {
        "pattern": "artifacts/manifests/knowledge-hub-source-coverage-closeout-*.jsonl",
        "required_filename": "knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl",
        "strategy": "filename-yyyymmdd-sort-last",
        "candidate_count": len(paths),
        "candidates": [str(path.relative_to(root)) for path in paths],
        "dated_candidate_count": len(dated),
        "dated_candidates": [row[1] for row in dated],
        "ignored_non_date_candidates": ignored,
        "selected": dated[-1][1] if dated else "",
        "reason_zh": "只按 knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl 的日期字段选择最新 closeout；非日期候选会被忽略并作为 warning 暴露，避免 future/latest 等文件名被静默选中。",
    }
    return selection, dated[-1][2] if dated else None

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
    "debug-record",
    "external-source-note",
    "owner-decision-worksheet",
    "migration-record",
    "patent-disclosure",
    "codex-session",
    "codex-workflow",
    "personal-note",
    "artifact-ref",
    "authorization",
    "automation-run",
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
    "notes",
    "embedded",
    "patents",
    "codex",
}
ALLOWED_SOURCE_ROLES = {
    "hub-migrated-source",
    "hub-native-source",
    "hub-runtime-input",
}
ALLOWED_SOURCE_AUTHORITIES = {
    "knowledge-hub-canonical",
    "knowledge-hub-ledger",
    "runtime-input-provenance",
}
ALLOWED_SOURCE_STATUSES = {
    "registered",
    "deprecated",
    "retired",
}
ALLOWED_SOURCE_WRITE_POLICIES = {
    "knowledge-hub-only",
    "hub-native-registry",
    "runtime-read-only-input",
}
ALLOWED_SOURCE_FINAL_DISPOSITIONS = {
    "hard-migrated-to-hub",
    "hub-native-source",
    "runtime-input-not-migrated",
}
ALLOWED_SOURCE_CONTROL_OBJECT_TYPES = {
    "markdown",
    "session",
    "history",
    "tool",
    "source-code",
    "config",
    "artifact",
    "binary",
    "log",
    "archive",
    "automation-run",
    "unknown",
}
ALLOWED_SOURCE_CONTROL_DISPOSITIONS = {
    "copy-body",
    "summary-only",
    "artifact-ref",
    "reference-only",
    "archive-only",
    "exclude",
}
ALLOWED_SOURCE_CONTROL_STATUSES = {
    "pending",
    "covered",
    "blocked",
    "excluded",
}
SOURCE_CONTROL_REQUIRED_FILES = [
    "README.md",
    "inventory.jsonl",
    "coverage.md",
    "migration-plan.md",
]
SOURCE_CONTROL_REQUIRED_ROW_FIELDS = [
    "id",
    "source_id",
    "source_path",
    "object_type",
    "hub_disposition",
    "target_path",
    "status",
    "reason_zh",
    "risk_zh",
    "checked_at",
]
SOURCE_CONTROL_RAW_OBJECT_TYPES = {"session", "history", "source-code", "binary", "log"}
LOCAL_PATH_PREFIXES = (
    "artifacts/",
    "docs/",
    "domains/",
    "inbox/",
    "notes/",
    "projects/",
    "sources/",
    "registry/",
    "indexes/",
    "governance/",
    "tools/",
    "templates/",
)
SHA256_RE = re.compile(r"[0-9a-f]{64}")
OWNER_DECISION_DRAFT_FIELDS = {
    "owner_decision",
    "target_decision",
    "reviewed_by",
    "reviewed_at",
    "source_sha256",
    "source_size",
    "evidence_refs",
    "status_reason",
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

def is_owner_decision_draft_path(path):
    name = path.name
    if name.endswith(".local.jsonl"):
        return False
    if "owner-decision-worksheets" in name or "owner-intake-package" in name:
        return False
    return (
        "owner-decision" in name
        or "owner-decisions" in name
    ) and path.suffix == ".jsonl"

def audit_owner_decision_draft_leaks(registered_paths):
    manifest_dir = root / "artifacts" / "manifests"
    if not manifest_dir.exists():
        return
    candidate_paths = sorted({
        *manifest_dir.glob("*owner-decision*.jsonl"),
        *manifest_dir.glob("*owner-decisions*.jsonl"),
    })
    for path in candidate_paths:
        if not is_owner_decision_draft_path(path):
            continue
        relative = str(path.relative_to(root))
        rows = load_jsonl(path)
        has_owner_fields = any(
            isinstance(row, dict)
            and any(str(row.get(field, "")).strip() for field in OWNER_DECISION_DRAFT_FIELDS)
            for row in rows
        )
        if has_owner_fields and relative not in registered_paths:
            warnings.append(
                f"owner-decision-draft:{relative} non-local owner decision JSONL with owner fields is not registered; use *.local.jsonl for drafts or register an explicit reviewed landing artifact"
            )

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
            "source-control",
            "source 主控目录异常",
            "检查 sources/<source_id>/README.md、inventory.jsonl、coverage.md、migration-plan.md，确保每个 registered source 都有 Hub 内控制面，raw/session/source-code 不能 copy-body 进入正文层。",
            lambda msg: msg.startswith("source-control:"),
        ),
        (
            "owner-target",
            "owner 决策目标缺失",
            "检查 owner decision landing JSONL 的 target_decision，并确认已映射到硬切换后的 projects/ 目标文件；reference-only/report-only 项不要求本地正文目标。",
            lambda msg: msg.startswith("owner-target:"),
        ),
        (
            "owner-decision-draft",
            "owner decision 草稿命名异常",
            "将未签收 owner decision 草稿改为 *.local.jsonl，或在真实 owner 签收后登记为 reviewed landing artifact；Codex 不代签、不关闭 gate。",
            lambda msg: msg.startswith("owner-decision-draft:"),
        ),
        (
            "automation-boundary",
            "自动化 report-only / no-memory 边界异常",
            "检查 registry/maintenance-runs.jsonl 中 enabled、mode、writes_memory、writes_team_active_index 和 no_memory_write_gate 字段；自动化默认只能 read-only/report-only/plan-only/local-commit。",
            lambda msg: msg.startswith("maintenance-runs:"),
        ),
        (
            "boundary-health",
            "PCR02 boundary manifest 内部证据异常",
            "检查 PCR02 Level 2 boundary manifest、registry item、by-source 和 by-project 索引；该检查只看 Knowledge Hub 内部证据，不读取源项目正文。",
            lambda msg: msg.startswith("boundary-health:"),
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
            "owner-routing",
            "owner decision 角色路由异常",
            "检查 registry/owner-routing.json，确保每个 open owner worksheet 角色都有只读分派路由，routing_owner 和 candidate_registry_owners 已登记，且不得把 routing_owner 当作 owner decision。",
            lambda msg: msg.startswith("owner-routing:"),
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
            "manifest-jsonl-profile",
            "manifest JSONL 轻量契约异常",
            "检查 2026-06-21 及之后的 Knowledge Hub governance manifest JSONL，补齐 id、status、中文说明、证据和边界字段；历史 manifest 不做反向强制改写。",
            lambda msg: msg.startswith("manifest-profile:"),
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
            "user-path-boundary",
            "用户绝对路径边界异常",
            "把长期文本中的用户机器绝对路径改为 ~/ 形式；工具内部可解析真实路径，但对外输出必须脱敏。",
            lambda msg: msg.startswith("user-path-boundary:"),
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
source_check_health = {
    "mode": "static-registry-only",
    "executed": False,
    "registered_source_count": len(sources),
    "with_check_count": 0,
    "with_no_check_reason_count": 0,
    "check_command_count": 0,
    "no_check_reason_count": 0,
    "path_exists_count": 0,
    "missing_check_or_reason_ids": [],
    "both_check_and_no_check_reason_ids": [],
    "non_rtk_check_ids": [],
    "missing_source_path_ids": [],
    "stale_review_after_ids": [],
    "missing_check_or_reason_source_ids": [],
    "both_check_and_no_check_reason_source_ids": [],
    "non_rtk_check_command_source_ids": [],
    "check_command_source_ids": [],
    "no_check_reason_source_ids": [],
    "path_missing_source_ids": [],
    "stale_review_after_source_ids": [],
    "rows": [],
    "report_only_findings": [
        "source check commands are inspected but not executed by knowledge-check",
    ],
}
source_control_health = {
    "mode": "hub-source-control-directories",
    "registered_source_count": len(sources),
    "required_file_count": len(sources) * len(SOURCE_CONTROL_REQUIRED_FILES),
    "present_file_count": 0,
    "missing_source_ids": [],
    "missing_files": [],
    "inventory_row_count": 0,
    "invalid_inventory_rows": [],
    "unsafe_raw_copy_rows": [],
    "rows_by_source": {},
    "status": "pass",
}
owner_target_health = {
    "mode": "owner-decision-landing-target-existence",
    "landing_manifest": "artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.jsonl",
    "checked_count": 0,
    "present_count": 0,
    "skipped_count": 0,
    "missing_targets": [],
    "rows": [],
    "status": "pass",
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
            source_review_after = dt.date.fromisoformat(str(source.get("review_after")))
            if source_review_after < today:
                source_check_health["stale_review_after_ids"].append(source_id)
                source_check_health["stale_review_after_source_ids"].append(source_id)
                warnings.append(f"sources:{source_id} review_after is stale: {source.get('review_after')}")
        except Exception:
            errors.append(f"sources:{source_id} invalid review_after: {source.get('review_after')}")
    if source.get("final_disposition") and source.get("final_disposition") not in ALLOWED_SOURCE_FINAL_DISPOSITIONS:
        errors.append(f"sources:{source_id} invalid final_disposition: {source.get('final_disposition')}")
    check_command = str(source.get("check", "")).strip()
    no_check_reason = str(source.get("no_check_reason", "")).strip()
    source_path_text = str(source.get("path", ""))
    if (
        source_path_text.startswith("~/")
        or source_path_text.startswith("/")
        or source_path_text.startswith("../")
        or source_path_text.startswith("./")
        or not source_path_text.startswith("sources/")
    ):
        errors.append(f"sources:{source_id} path must point to Hub source control directory: {source_path_text}")
    if any(token in check_command for token in ["~/embedded", "~/codex/docs/archive", "~/work/", "~/.codex", "/vsdata/"]):
        errors.append(f"sources:{source_id} check must not depend on retired external source path")
    path = pathlib.Path(source_path_text.replace("~", str(pathlib.Path.home()))).expanduser()
    if not path.is_absolute():
        path = root / path
    path_exists = path.exists()
    if check_command:
        source_check_health["with_check_count"] += 1
        source_check_health["check_command_count"] += 1
        source_check_health["check_command_source_ids"].append(source_id)
        if not check_command.startswith("rtk "):
            source_check_health["non_rtk_check_ids"].append(source_id)
            source_check_health["non_rtk_check_command_source_ids"].append(source_id)
            errors.append(f"sources:{source_id} check must start with rtk")
    if no_check_reason:
        source_check_health["with_no_check_reason_count"] += 1
        source_check_health["no_check_reason_count"] += 1
        source_check_health["no_check_reason_source_ids"].append(source_id)
    if not check_command and not no_check_reason:
        source_check_health["missing_check_or_reason_ids"].append(source_id)
        source_check_health["missing_check_or_reason_source_ids"].append(source_id)
        errors.append(f"sources:{source_id} missing no_check_reason for empty check")
    if check_command and no_check_reason:
        source_check_health["both_check_and_no_check_reason_ids"].append(source_id)
        source_check_health["both_check_and_no_check_reason_source_ids"].append(source_id)
        errors.append(f"sources:{source_id} has both check and no_check_reason")
    if path_exists:
        source_check_health["path_exists_count"] += 1
    else:
        source_check_health["missing_source_path_ids"].append(source_id)
        source_check_health["path_missing_source_ids"].append(source_id)
        warnings.append(f"sources:{source.get('id')} path missing: {path}")
    source_check_health["rows"].append({
        "source_id": source_id,
        "has_check": bool(check_command),
        "has_no_check_reason": bool(no_check_reason),
        "check_contract_status": "ok" if check_command or no_check_reason else "missing-check-or-no-check-reason",
        "execution_status": "not-run",
        "path_exists": path_exists,
        "check_command": check_command,
        "no_check_reason": no_check_reason,
        "review_after": str(source.get("review_after", "")),
        "review_after_stale": source_id in source_check_health["stale_review_after_ids"],
    })
source_check_health["check_command_source_ids"] = sorted(source_check_health["check_command_source_ids"])
source_check_health["no_check_reason_source_ids"] = sorted(source_check_health["no_check_reason_source_ids"])
source_check_health["missing_check_or_reason_source_ids"] = sorted(source_check_health["missing_check_or_reason_source_ids"])
source_check_health["both_check_and_no_check_reason_source_ids"] = sorted(source_check_health["both_check_and_no_check_reason_source_ids"])
source_check_health["non_rtk_check_command_source_ids"] = sorted(source_check_health["non_rtk_check_command_source_ids"])
source_check_health["path_missing_source_ids"] = sorted(source_check_health["path_missing_source_ids"])
source_check_health["missing_check_or_reason_ids"] = sorted(source_check_health["missing_check_or_reason_ids"])
source_check_health["both_check_and_no_check_reason_ids"] = sorted(source_check_health["both_check_and_no_check_reason_ids"])
source_check_health["non_rtk_check_ids"] = sorted(source_check_health["non_rtk_check_ids"])
source_check_health["missing_source_path_ids"] = sorted(source_check_health["missing_source_path_ids"])
source_check_health["stale_review_after_ids"] = sorted(source_check_health["stale_review_after_ids"])
source_check_health["stale_review_after_source_ids"] = sorted(source_check_health["stale_review_after_source_ids"])
source_check_health["rows"] = sorted(source_check_health["rows"], key=lambda row: row["source_id"])

def local_inventory_target_exists(target_text):
    if not target_text:
        return True
    if pathlib.Path(target_text).is_absolute() or target_text.startswith(("./", "../")):
        return False
    target_path = root / target_text
    if target_text.startswith(LOCAL_PATH_PREFIXES):
        return target_path.exists()
    return True

for source_id in sorted(source_ids):
    source_dir = root / "sources" / source_id
    missing_for_source = []
    for filename in SOURCE_CONTROL_REQUIRED_FILES:
        required_path = source_dir / filename
        if required_path.exists():
            source_control_health["present_file_count"] += 1
        else:
            rel_missing = str(required_path.relative_to(root))
            missing_for_source.append(rel_missing)
            source_control_health["missing_files"].append(rel_missing)
            errors.append(f"source-control:{source_id} missing {rel_missing}")
    if missing_for_source:
        source_control_health["missing_source_ids"].append(source_id)
    inventory_path = source_dir / "inventory.jsonl"
    source_control_health["rows_by_source"][source_id] = 0
    if not inventory_path.exists():
        continue
    for line_no, row in enumerate(load_jsonl(inventory_path), 1):
        row_id = str(row.get("id", f"{source_id}:{line_no}"))
        source_control_health["inventory_row_count"] += 1
        source_control_health["rows_by_source"][source_id] += 1
        row_errors = []
        for field in SOURCE_CONTROL_REQUIRED_ROW_FIELDS:
            if field not in row or row.get(field) in (None, ""):
                row_errors.append(f"missing {field}")
        row_source_id = str(row.get("source_id", ""))
        if row_source_id and row_source_id != source_id:
            row_errors.append(f"source_id mismatch: {row_source_id}")
        object_type = str(row.get("object_type", ""))
        hub_disposition = str(row.get("hub_disposition", ""))
        status = str(row.get("status", ""))
        if object_type and object_type not in ALLOWED_SOURCE_CONTROL_OBJECT_TYPES:
            row_errors.append(f"invalid object_type: {object_type}")
        if hub_disposition and hub_disposition not in ALLOWED_SOURCE_CONTROL_DISPOSITIONS:
            row_errors.append(f"invalid hub_disposition: {hub_disposition}")
        if status and status not in ALLOWED_SOURCE_CONTROL_STATUSES:
            row_errors.append(f"invalid status: {status}")
        checked_at = str(row.get("checked_at", ""))
        if checked_at:
            try:
                dt.date.fromisoformat(checked_at)
            except Exception:
                row_errors.append(f"invalid checked_at: {checked_at}")
        target_path_text = str(row.get("target_path", "")).strip()
        if target_path_text:
            if pathlib.Path(target_path_text).is_absolute() or target_path_text.startswith(("./", "../")):
                row_errors.append(f"target_path must be repo-relative or source-local reference: {target_path_text}")
            elif not local_inventory_target_exists(target_path_text):
                row_errors.append(f"target_path missing: {target_path_text}")
        if object_type in SOURCE_CONTROL_RAW_OBJECT_TYPES and hub_disposition == "copy-body":
            raw_row = {
                "source_id": source_id,
                "row_id": row_id,
                "object_type": object_type,
                "hub_disposition": hub_disposition,
                "target_path": target_path_text,
            }
            source_control_health["unsafe_raw_copy_rows"].append(raw_row)
            row_errors.append("raw/session/source-code/log/binary must not use copy-body")
        if row_errors:
            invalid = {
                "source_id": source_id,
                "row_id": row_id,
                "line": line_no,
                "errors": row_errors,
            }
            source_control_health["invalid_inventory_rows"].append(invalid)
            for row_error in row_errors:
                errors.append(f"source-control:{source_id} inventory row {row_id} {row_error}")

owner_target_landing_path = root / owner_target_health["landing_manifest"]
for row in load_jsonl(owner_target_landing_path):
    worksheet_id = str(row.get("worksheet_id", "<unknown>"))
    owner_decision = str(row.get("owner_decision", ""))
    target_decision = str(row.get("target_decision", ""))
    target_status = "skipped"
    target_path = ""
    skip_decisions = {"reference-only", "no-migration", "report-only-governance-candidate"}
    if owner_decision in {"reference-only", "teamized-report-only"} or target_decision in skip_decisions:
        owner_target_health["skipped_count"] += 1
    elif target_decision.startswith("domains/projects/"):
        target_path = "projects/" + target_decision[len("domains/projects/"):]
    elif target_decision.startswith("projects/"):
        target_path = target_decision
    if target_path:
        owner_target_health["checked_count"] += 1
        if (root / target_path).exists():
            owner_target_health["present_count"] += 1
            target_status = "present"
        else:
            target_status = "missing"
            missing = {
                "worksheet_id": worksheet_id,
                "target_decision": target_decision,
                "mapped_target_path": target_path,
            }
            owner_target_health["missing_targets"].append(missing)
            errors.append(f"owner-target:{worksheet_id} target path missing: {target_path}")
    owner_target_health["rows"].append({
        "worksheet_id": worksheet_id,
        "owner_decision": owner_decision,
        "target_decision": target_decision,
        "mapped_target_path": target_path,
        "status": target_status,
    })
source_control_health["missing_source_ids"] = sorted(set(source_control_health["missing_source_ids"]))
source_control_health["missing_files"] = sorted(source_control_health["missing_files"])
source_control_health["status"] = "fail" if (
    source_control_health["missing_files"]
    or source_control_health["invalid_inventory_rows"]
    or source_control_health["unsafe_raw_copy_rows"]
) else "pass"
owner_target_health["status"] = "fail" if owner_target_health["missing_targets"] else "pass"

automation_safety_health = {
    "mode": "registry-maintenance-runs",
    "record_count": 0,
    "checked_count": 0,
    "unsafe_run_ids": [],
    "missing_guard_run_ids": [],
    "authorization_required_run_ids": [],
    "rows": [],
}
authorization_rows = load_jsonl(root / "registry" / "authorizations.jsonl")
authorization_ids = {
    str(row.get("authorization_id", ""))
    for row in authorization_rows
    if isinstance(row, dict) and str(row.get("authorization_id", "")).strip()
}
for run in load_jsonl(root / "registry" / "maintenance-runs.jsonl"):
    run_id = str(run.get("run_id", "<unknown>"))
    automation_safety_health["record_count"] += 1
    if "automation_id" not in run:
        automation_safety_health["rows"].append({
            "run_id": run_id,
            "automation_id": "",
            "check_status": "not-automation-record",
        })
        continue
    automation_safety_health["checked_count"] += 1
    enabled = run.get("enabled")
    mode = str(run.get("mode", ""))
    authorization_id = str(run.get("authorization_id", "")).strip()
    writes_memory = run.get("writes_memory")
    writes_team_active_index = run.get("writes_team_active_index")
    no_memory_write_gate = str(run.get("no_memory_write_gate", "")).strip()
    row_errors = []
    if enabled is not False:
        row_errors.append("enabled must be false")
    if mode not in {"read-only", "report-only", "plan-only", "local-commit", "apply-with-review", "forbidden"}:
        row_errors.append("mode must be read-only/report-only/plan-only/local-commit/apply-with-review/forbidden")
    if mode == "apply-with-review" and authorization_id not in authorization_ids:
        row_errors.append("apply-with-review requires registered authorization_id")
    if mode in {"read-only", "report-only", "plan-only", "local-commit"}:
        if writes_memory is not False:
            row_errors.append("writes_memory must be false without authorization")
        if writes_team_active_index is not False:
            row_errors.append("writes_team_active_index must be false without authorization")
    if mode == "apply-with-review" and (writes_memory is not False or writes_team_active_index is not False) and authorization_id not in authorization_ids:
        row_errors.append("write actions require registered authorization_id")
    if not no_memory_write_gate:
        row_errors.append("no_memory_write_gate is required")
    if row_errors:
        automation_safety_health["unsafe_run_ids"].append(run_id)
        if "no_memory_write_gate is required" in row_errors:
            automation_safety_health["missing_guard_run_ids"].append(run_id)
        if any("authorization_id" in row_error for row_error in row_errors):
            automation_safety_health["authorization_required_run_ids"].append(run_id)
        for row_error in row_errors:
            errors.append(f"maintenance-runs:{run_id} {row_error}")
    automation_safety_health["rows"].append({
        "run_id": run_id,
        "automation_id": str(run.get("automation_id", "")),
        "enabled": enabled,
        "mode": mode,
        "authorization_id": authorization_id,
        "writes_memory": writes_memory,
        "writes_team_active_index": writes_team_active_index,
        "has_no_memory_write_gate": bool(no_memory_write_gate),
        "check_status": "pass" if not row_errors else "fail",
        "errors": row_errors,
    })
automation_safety_health["unsafe_run_ids"] = sorted(automation_safety_health["unsafe_run_ids"])
automation_safety_health["missing_guard_run_ids"] = sorted(automation_safety_health["missing_guard_run_ids"])
automation_safety_health["authorization_required_run_ids"] = sorted(automation_safety_health["authorization_required_run_ids"])

authorization_health = {
    "record_count": len(authorization_rows),
    "active_count": 0,
    "invalid_authorization_ids": [],
    "rows": [],
}
allowed_authorization_actions = {
    "owner-decision-landing",
    "active-promotion",
    "memory-write",
    "source-project-write",
    "automation-apply-with-review",
    "external-publish",
    "delete-or-prune",
    "remote-git-write",
}
allowed_authorization_statuses = {"active", "expired", "revoked", "used", "superseded"}
for row in authorization_rows:
    auth_id = str(row.get("authorization_id", "<unknown>"))
    row_errors = []
    for field in ["authorization_id", "authorized_by", "authorized_at", "scope", "allowed_actions", "expires_at", "evidence_refs", "rollback_path", "validation_commands", "status"]:
        if row.get(field) in ("", None, []):
            row_errors.append(f"missing {field}")
    for field in ["authorized_at", "expires_at"]:
        value = str(row.get(field, ""))
        if value:
            try:
                dt.date.fromisoformat(value)
            except Exception:
                row_errors.append(f"invalid {field}")
    actions = row.get("allowed_actions", [])
    if not isinstance(actions, list) or not actions:
        row_errors.append("allowed_actions must be non-empty list")
    else:
        for action in actions:
            if action not in allowed_authorization_actions:
                row_errors.append(f"invalid allowed_action {action}")
    status = str(row.get("status", ""))
    if status and status not in allowed_authorization_statuses:
        row_errors.append(f"invalid status {status}")
    if status == "active":
        authorization_health["active_count"] += 1
    if row_errors:
        authorization_health["invalid_authorization_ids"].append(auth_id)
        for row_error in row_errors:
            errors.append(f"authorizations:{auth_id} {row_error}")
    authorization_health["rows"].append({
        "authorization_id": auth_id,
        "status": status,
        "allowed_actions": actions if isinstance(actions, list) else [],
        "check_status": "pass" if not row_errors else "fail",
        "errors": row_errors,
    })
authorization_health["invalid_authorization_ids"] = sorted(authorization_health["invalid_authorization_ids"])

source_coverage_selection = {
    "pattern": "artifacts/manifests/knowledge-hub-source-coverage-closeout-*.jsonl",
    "required_filename": "knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl",
    "strategy": "filename-yyyymmdd-sort-last",
    "candidate_count": 0,
    "candidates": [],
    "dated_candidate_count": 0,
    "dated_candidates": [],
    "ignored_non_date_candidates": [],
    "selected": "",
    "reason_zh": "只按 knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl 的日期字段选择最新 closeout；非日期候选会被忽略并作为 warning 暴露，避免 future/latest 等文件名被静默选中。",
}
source_coverage_health = {
    "registered_source_count": len(source_ids),
    "row_count": 0,
    "unique_source_count": 0,
    "missing_source_ids": [],
    "stale_source_ids": [],
    "duplicate_source_ids": [],
    "missing_required_field_rows": [],
    "invalid_checked_at_rows": [],
}
boundary_health = {
    "schema_version": 1,
    "status": "not-run",
    "mode": "read-only-internal-evidence",
    "scope": "pcr02-level2-boundary-manifests",
    "source_project_read": False,
    "owner_gate_mutation": False,
    "memory_write": False,
    "expected_source_ids": sorted({spec["source_id"] for spec in EXPECTED_BOUNDARY_MANIFESTS.values()}),
    "latest_source_coverage_manifest": "",
    "expected_boundary_count": len(EXPECTED_BOUNDARY_MANIFESTS),
    "jsonl_manifest_count": 0,
    "md_manifest_count": 0,
    "row_count": 0,
    "source_ids": [],
    "missing_manifest_ids": [],
    "missing_jsonl_paths": [],
    "missing_md_paths": [],
    "missing_registry_item_ids": [],
    "missing_by_source_refs": [],
    "missing_by_project_refs": [],
    "source_id_mismatch_rows": [],
    "missing_required_field_rows": [],
    "invalid_checked_at_rows": [],
    "required_text_missing": [],
    "summary": {},
    "hard_failures": [],
    "warnings": [],
    "report_only_findings": [
        "boundary health checks Knowledge Hub manifest/registry/index evidence only and does not read PCR02 source bodies",
    ],
}

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

    source_coverage_selection, source_coverage_path = select_source_coverage_closeout(root)
    if source_coverage_selection.get("ignored_non_date_candidates"):
        warnings.append(
            "source-coverage: ignored non-date closeout candidates: "
            + ", ".join(source_coverage_selection.get("ignored_non_date_candidates", []))
        )
    source_coverage_ids = set()
    if not source_coverage_selection.get("candidates"):
        errors.append("source-coverage: missing knowledge-hub-source-coverage-closeout manifest")
    elif source_coverage_path is None:
        errors.append("source-coverage: missing dated knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl manifest")
    else:
        source_coverage_rows = load_jsonl(source_coverage_path)
        source_coverage_health["row_count"] = len(source_coverage_rows)
        duplicate_source_ids = set()
        missing_required_field_rows = []
        invalid_checked_at_rows = []
        for row in source_coverage_rows:
            row_source_id = row.get("source_id")
            row_id = row.get("id", row_source_id or "<unknown>")
            if not row_source_id:
                errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} row {row_id} missing source_id")
                continue
            if row_source_id in source_coverage_ids:
                duplicate_source_ids.add(row_source_id)
                errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} duplicate source {row_source_id}")
            source_coverage_ids.add(row_source_id)
            for field in ["status", "classification", "decision", "risk", "owner", "checked_at"]:
                if not row.get(field):
                    missing_required_field_rows.append({"source_id": row_source_id, "field": field})
                    errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} source {row_source_id} missing {field}")
            checked_at = str(row.get("checked_at", ""))
            if checked_at:
                try:
                    dt.date.fromisoformat(checked_at)
                except Exception:
                    invalid_checked_at_rows.append({"source_id": row_source_id, "checked_at": checked_at})
                    errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} source {row_source_id} invalid checked_at: {checked_at}")
        source_coverage_health["unique_source_count"] = len(source_coverage_ids)
        source_coverage_health["missing_source_ids"] = sorted(source_ids - source_coverage_ids)
        source_coverage_health["stale_source_ids"] = sorted(source_coverage_ids - source_ids)
        source_coverage_health["duplicate_source_ids"] = sorted(duplicate_source_ids)
        source_coverage_health["missing_required_field_rows"] = missing_required_field_rows
        source_coverage_health["invalid_checked_at_rows"] = invalid_checked_at_rows
        for source_id in sorted(source_ids):
            if source_id not in source_coverage_ids:
                errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} missing source {source_id}")
        for covered_source_id in sorted(source_coverage_ids):
            if covered_source_id not in source_ids:
                errors.append(f"source-coverage:{source_coverage_path.relative_to(root)} stale source {covered_source_id}")
    boundary_health["latest_source_coverage_manifest"] = source_coverage_selection.get("selected", "")

    boundary_registry_ids = set()
    try:
        for row in load_jsonl(root / "registry" / "items.jsonl"):
            if row.get("id"):
                boundary_registry_ids.add(str(row.get("id")))
    except Exception:
        pass
    by_source_text = ""
    by_project_text = ""
    try:
        by_source_text = (root / "indexes" / "by-source.md").read_text()
    except Exception as exc:
        errors.append(f"boundary-health:indexes/by-source.md unreadable: {exc}")
    try:
        by_project_text = (root / "indexes" / "by-project.md").read_text()
    except Exception as exc:
        errors.append(f"boundary-health:indexes/by-project.md unreadable: {exc}")
    boundary_source_ids = set()
    for item_id, spec in EXPECTED_BOUNDARY_MANIFESTS.items():
        md_rel = spec["md"]
        jsonl_rel = spec["jsonl"]
        md_path = root / md_rel
        jsonl_path = root / jsonl_rel
        if not md_path.exists():
            boundary_health["missing_md_paths"].append(md_rel)
            boundary_health["missing_manifest_ids"].append(item_id)
            errors.append(f"boundary-health:{item_id} missing markdown {md_rel}")
        else:
            boundary_health["md_manifest_count"] += 1
            try:
                md_text = md_path.read_text()
            except Exception as exc:
                md_text = ""
                errors.append(f"boundary-health:{md_rel} unreadable: {exc}")
            if spec["required_text"] not in md_text:
                boundary_health["required_text_missing"].append({"id": item_id, "text": spec["required_text"]})
                errors.append(f"boundary-health:{item_id} missing required text {spec['required_text']}")
        if not jsonl_path.exists():
            boundary_health["missing_jsonl_paths"].append(jsonl_rel)
            if item_id not in boundary_health["missing_manifest_ids"]:
                boundary_health["missing_manifest_ids"].append(item_id)
            errors.append(f"boundary-health:{item_id} missing jsonl {jsonl_rel}")
            continue
        boundary_health["jsonl_manifest_count"] += 1
        rows = load_jsonl(jsonl_path)
        boundary_health["row_count"] += len(rows)
        for row_index, row in enumerate(rows, 1):
            row_id = str(row.get("id", f"{item_id}:{row_index}"))
            row_source_id = str(row.get("source_id", ""))
            if row_source_id:
                boundary_source_ids.add(row_source_id)
            if row_source_id != spec["source_id"]:
                boundary_health["source_id_mismatch_rows"].append({
                    "manifest_id": item_id,
                    "row_id": row_id,
                    "expected_source_id": spec["source_id"],
                    "actual_source_id": row_source_id,
                })
                errors.append(f"boundary-health:{item_id} row {row_id} source_id mismatch: {row_source_id}")
            for field in ["id", "source_id", "source_path", "classification", "decision", "status", "owner", "risk", "checked_at"]:
                if not row.get(field):
                    boundary_health["missing_required_field_rows"].append({
                        "manifest_id": item_id,
                        "row_id": row_id,
                        "field": field,
                    })
                    errors.append(f"boundary-health:{item_id} row {row_id} missing {field}")
            checked_at = str(row.get("checked_at", ""))
            if checked_at:
                try:
                    dt.date.fromisoformat(checked_at)
                except Exception:
                    boundary_health["invalid_checked_at_rows"].append({
                        "manifest_id": item_id,
                        "row_id": row_id,
                        "checked_at": checked_at,
                    })
                    errors.append(f"boundary-health:{item_id} row {row_id} invalid checked_at: {checked_at}")
        if item_id not in boundary_registry_ids:
            boundary_health["missing_registry_item_ids"].append(item_id)
            errors.append(f"boundary-health:{item_id} missing registry item")
        if md_rel not in by_source_text:
            boundary_health["missing_by_source_refs"].append(md_rel)
            errors.append(f"boundary-health:{item_id} missing by-source ref {md_rel}")
        if md_rel not in by_project_text:
            boundary_health["missing_by_project_refs"].append(md_rel)
            errors.append(f"boundary-health:{item_id} missing by-project ref {md_rel}")
    boundary_health["source_ids"] = sorted(boundary_source_ids)
    boundary_health["missing_manifest_ids"] = sorted(set(boundary_health["missing_manifest_ids"]))
    boundary_health["missing_jsonl_paths"] = sorted(boundary_health["missing_jsonl_paths"])
    boundary_health["missing_md_paths"] = sorted(boundary_health["missing_md_paths"])
    boundary_health["missing_registry_item_ids"] = sorted(boundary_health["missing_registry_item_ids"])
    boundary_health["missing_by_source_refs"] = sorted(boundary_health["missing_by_source_refs"])
    boundary_health["missing_by_project_refs"] = sorted(boundary_health["missing_by_project_refs"])
    boundary_health["hard_failures"] = [message for message in errors if message.startswith("boundary-health:")]
    boundary_health["warnings"] = [message for message in warnings if message.startswith("boundary-health:")]
    boundary_health["status"] = "fail" if boundary_health["hard_failures"] else "pass"
    boundary_expected_sources = set(boundary_health["expected_source_ids"])
    boundary_health["summary"] = {
        "expected_manifest_count": boundary_health["expected_boundary_count"],
        "present_md_manifest_count": boundary_health["md_manifest_count"],
        "present_jsonl_manifest_count": boundary_health["jsonl_manifest_count"],
        "registered_item_count": boundary_health["expected_boundary_count"] - len(boundary_health["missing_registry_item_ids"]),
        "source_coverage_count": len(boundary_expected_sources & source_coverage_ids),
        "by_source_reference_count": boundary_health["expected_boundary_count"] - len(boundary_health["missing_by_source_refs"]),
        "by_project_reference_count": boundary_health["expected_boundary_count"] - len(boundary_health["missing_by_project_refs"]),
    }

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
    owner_gate_roles = set()
    owner_gate_paths = sorted((root / "artifacts" / "manifests").glob("*owner-decision-worksheets-*.jsonl"))
    for owner_gate_path in owner_gate_paths:
        for row in load_jsonl(owner_gate_path):
            row_source_id = row.get("source_id")
            row_source_path = row.get("source_path")
            row_owner_role = row.get("owner_required") or row.get("owner_candidate") or ""
            if not row_source_id or not row_source_path:
                continue
            if row_owner_role:
                owner_gate_roles.add((str(row_source_id), str(row_owner_role)))
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

    owner_routing_doc = load_json(root / "registry" / "owner-routing.json")
    owner_route_keys = set()
    allowed_owner_route_statuses = {
        "mapped-to-registry-owner",
        "needs-human-assignment",
        "unmapped",
        "retired",
    }
    for route in owner_routing_doc.get("routes", []):
        role = str(route.get("decision_owner_role", ""))
        source_id = str(route.get("source_id", ""))
        route_id = f"{source_id}:{role}" if source_id or role else "<unknown>"
        for field in ["decision_owner_role", "source_id", "routing_status", "routing_owner", "required_real_owner_zh", "escalation_zh", "notes_zh"]:
            if not route.get(field):
                errors.append(f"owner-routing:{route_id} missing {field}")
        key = (source_id, role)
        if key in owner_route_keys:
            errors.append(f"owner-routing:{route_id} duplicate route")
        owner_route_keys.add(key)
        if source_id and source_id not in source_ids:
            errors.append(f"owner-routing:{route_id} unknown source_id: {source_id}")
        if route.get("routing_status") and route.get("routing_status") not in allowed_owner_route_statuses:
            errors.append(f"owner-routing:{route_id} invalid routing_status: {route.get('routing_status')}")
        routing_owner = route.get("routing_owner")
        if routing_owner and routing_owner not in owner_ids:
            errors.append(f"owner-routing:{route_id} unknown routing_owner: {routing_owner}")
        candidate_registry_owners = route.get("candidate_registry_owners", [])
        if not isinstance(candidate_registry_owners, list):
            errors.append(f"owner-routing:{route_id} candidate_registry_owners must be list")
        else:
            for candidate_owner in candidate_registry_owners:
                if candidate_owner not in owner_ids:
                    errors.append(f"owner-routing:{route_id} unknown candidate_registry_owner: {candidate_owner}")
        if not isinstance(route.get("must_not", []), list) or not route.get("must_not", []):
            errors.append(f"owner-routing:{route_id} missing must_not")
    for source_id, role in sorted(owner_gate_roles):
        if (source_id, role) not in owner_route_keys:
            errors.append(f"owner-routing:{source_id}:{role} missing route for owner worksheet role")

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
            if str(topic_domain).startswith(("domains/projects", "domains/personal")):
                errors.append(f"topics:{topic_id} domain uses deprecated canonical path: {topic_domain}")
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

    retention_path = root / "registry" / "retention.json"
    if retention_path.exists():
        retention_doc = load_json(retention_path)
        rules = retention_doc.get("rules", [])
        if not isinstance(rules, list):
            errors.append("retention: rules must be list")
        else:
            for index, rule in enumerate(rules):
                if not isinstance(rule, dict):
                    errors.append(f"retention:{index} rule must be object")
                    continue
                rule_domain = str(rule.get("domain", ""))
                if rule_domain.startswith(("domains/projects", "domains/personal")):
                    errors.append(f"retention:{index} domain uses deprecated canonical path: {rule_domain}")

    local_path_prefixes = LOCAL_PATH_PREFIXES
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
        checked_date = None
        try:
            checked_date = dt.date.fromisoformat(checked_at)
        except Exception:
            errors.append(f"migrations:{migration_id} invalid checked_at: {checked_at}")
        if checked_date and checked_date >= READABILITY_GATE_START and not is_bootstrap_empty:
            notes_zh = str(migration.get("notes_zh", "")).strip()
            if not notes_zh:
                errors.append(f"migrations:{migration_id} missing notes_zh for post-2026-06-21 readability gate")
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

    manifest_profile_paths = []
    for candidate_path in sorted((root / "artifacts" / "manifests").glob("knowledge-hub-*.jsonl")):
        date_match = re.search(r"(20\d{6})", candidate_path.name)
        if not date_match:
            continue
        try:
            manifest_date = dt.datetime.strptime(date_match.group(1), "%Y%m%d").date()
        except Exception:
            continue
        if manifest_date >= READABILITY_GATE_START:
            manifest_profile_paths.append(candidate_path)
    manifest_evidence_fields = ["evidence", "evidence_refs", "validation_refs", "verification_commands", "source_refs"]
    manifest_boundary_fields = ["boundaries", "guardrails", "must_not", "non_goals", "rollback_policy", "risk"]
    for manifest_path in manifest_profile_paths:
        rel_manifest = manifest_path.relative_to(root)
        manifest_stem = manifest_path.stem
        filename_has_date = bool(re.search(r"20\d{6}", manifest_path.name))
        rows = load_jsonl(manifest_path)
        for row_index, row in enumerate(rows, 1):
            row_id = str(row.get("id", "")).strip()
            label = row_id or f"{rel_manifest}:{row_index}"
            row_type = str(row.get("row_type", "")).strip()
            if row_id != manifest_stem and row_type != "summary":
                continue
            if not row_id:
                errors.append(f"manifest-profile:{label} missing id")
            if not str(row.get("status", "")).strip():
                errors.append(f"manifest-profile:{label} missing status")
            if not (filename_has_date or str(row.get("checked_at", "")).strip() or str(row.get("created_at", "")).strip() or str(row.get("updated_at", "")).strip() or str(row.get("review_after", "")).strip()):
                errors.append(f"manifest-profile:{label} missing date field")
            if not (str(row.get("summary_zh", "")).strip() or str(row.get("notes_zh", "")).strip()):
                errors.append(f"manifest-profile:{label} missing summary_zh or notes_zh")
            has_evidence = False
            for field in manifest_evidence_fields:
                value = row.get(field)
                if isinstance(value, list) and value:
                    has_evidence = True
                elif isinstance(value, str) and value.strip():
                    has_evidence = True
            if not has_evidence:
                errors.append(f"manifest-profile:{label} missing evidence field")
            has_boundary = False
            for field in manifest_boundary_fields:
                value = row.get(field)
                if isinstance(value, list) and value:
                    has_boundary = True
                elif isinstance(value, dict) and value:
                    has_boundary = True
                elif isinstance(value, str) and value.strip():
                    has_boundary = True
            if not has_boundary:
                errors.append(f"manifest-profile:{label} missing boundary field")

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
    template_readability_fields = [
        "summary_zh",
        "review_status",
        "primary_language",
        "source_language",
        "translation_status",
        "terminology_status",
        "evidence_strength",
        "evidence_refs",
        "promotion_decision",
        "generated_by_ai",
        "ai_role",
        "ai_model_or_tool",
        "ai_generated_at",
        "human_reviewed_by",
        "human_reviewed_at",
        "review_basis",
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
        for field in template_readability_fields:
            if not re.search(rf"^{re.escape(field)}:", template_text, re.MULTILINE):
                errors.append(f"template:{rel_template} missing readability field {field}")
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

    manual_entry_file_specific_terms = {
        root / "tools" / "knowledge-new.sh": [
            "owner_registry_status",
            "personal-local",
            "recommended_final_disposition",
            "recommended_migration_strategy",
            "recommendation_scope_zh",
            "--item-source-id",
            "--check",
            "--no-check-reason",
            "Evidence Index",
        ],
        root / "templates" / "README.md": [
            "personal-local",
            "recommended_final_disposition",
            "recommended_migration_strategy",
            "不替代 owner decision",
            "不关闭 owner gate",
            "Evidence Index",
        ],
    }
    for manual_entry_file, terms in manual_entry_file_specific_terms.items():
        manual_text = manual_entry_file.read_text()
        rel_manual = manual_entry_file.relative_to(root)
        for term in terms:
            if term not in manual_text:
                errors.append(f"manual-entry:{rel_manual} missing terminal manual-entry term: {term}")

    manual_entry_anchor_checks = {
        "README.md": [
            "日常入口",
            "目录边界",
            "迁移口径",
            "高风险授权",
            "中文长期资产",
            "新会话恢复",
            "knowledge-index-plan.sh --section linking --json",
            "registry/authorizations.jsonl",
            "registry/automation-runs.jsonl",
        ],
        "tools/README.md": [
            "低复杂度入口速查",
            "knowledge-owner-gates.sh --owner-inbox",
            "owner_inbox_json_command",
            "knowledge-index-plan.sh --section linking --json",
            "离线人工维护",
            "personal-local",
            "role-aware 推荐终态",
        ],
        "indexes/README.md": [
            "最小同步",
            "knowledge-index-plan.sh --section linking --json",
            "knowledge-index-plan.sh --section manifest --json",
            "manual_validation_pending: true",
        ],
    }
    for relative, terms in manual_entry_anchor_checks.items():
        path = root / relative
        text = path.read_text()
        for term in terms:
            if term not in text:
                errors.append(f"manual-entry:{relative} missing maintenance anchor: {term}")

    ids = set()
    items = load_jsonl(root / "registry" / "items.jsonl")
    registered_item_paths = {
        str(item.get("path", "")).strip()
        for item in items
        if isinstance(item, dict) and str(item.get("path", "")).strip()
    }
    for item in items:
        if not isinstance(item, dict):
            continue
        validation_refs = item.get("validation_refs", [])
        if not isinstance(validation_refs, list):
            continue
        for validation_ref in validation_refs:
            ref_text = str(validation_ref).strip()
            if ref_text and not ref_text.startswith("rtk ") and not ref_text.startswith("command:"):
                registered_item_paths.add(ref_text)
    audit_owner_decision_draft_leaks(registered_item_paths)
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
        if item_dates.get("created_at") and item_dates["created_at"] >= READABILITY_GATE_START:
            if item.get("domain") == "governance" and item.get("kind") == "audit":
                for field in ["summary_zh", "primary_language", "source_language", "translation_status", "terminology_status"]:
                    if not str(item.get(field, "")).strip():
                        errors.append(f"items:{item_id} missing {field} for post-2026-06-21 governance audit readability gate")
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
            if not path_text.startswith((f"projects/{project_id}/", "artifacts/manifests/")):
                errors.append(f"items:{item_id} project domain path mismatch: domain={domain} path={path_text}")
        if domain == "notes" and not path_text.startswith(("notes/", "artifacts/manifests/")):
            errors.append(f"items:{item_id} notes domain path outside notes/control artifacts: {path_text}")
        if domain == "codex" and not path_text.startswith(("domains/codex/", "artifacts/manifests/")):
            errors.append(f"items:{item_id} codex domain path outside codex control plane: {path_text}")
        if domain == "embedded" and not path_text.startswith(("domains/embedded/", "artifacts/manifests/")):
            errors.append(f"items:{item_id} embedded domain path outside embedded/control artifacts: {path_text}")
        if domain == "patents" and not path_text.startswith(("domains/patents/", "artifacts/manifests/")):
            errors.append(f"items:{item_id} patents domain path outside patents/control artifacts: {path_text}")
        if domain == "personal":
            errors.append(f"items:{item_id} deprecated personal domain; use domain=notes path=notes/personal/**")
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
        if item.get("generated_by_ai") is True and str(item.get("created_at", "")) >= "2026-06-21":
            missing_provenance = [
                field
                for field in ["ai_role", "ai_model_or_tool", "ai_generated_at"]
                if not item.get(field)
            ]
            if missing_provenance:
                errors.append(
                    f"items:{item_id} ai-generated item missing provenance fields: {','.join(missing_provenance)}"
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
        if item.get("visibility") == "personal-local" or str(item.get("path", "")).startswith("notes/personal/"):
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
        root / "notes",
        root / "projects",
        root / "sources",
        root / "registry",
        root / "governance",
        root / "templates",
        root / "indexes",
        root / "tools",
        root / "docs",
        root / "README.md",
        root / "AGENTS.md",
        root / "artifacts" / "manifests",
    ]
    forbidden_path_prefixes = user_path_prefixes()
    for path in iter_text_files(scan_roots):
        try:
            text = path.read_text(errors="ignore")
        except Exception as exc:
            warnings.append(f"{display_path(path)}: unreadable: {exc}")
            continue
        for prefix in forbidden_path_prefixes:
            if prefix in text:
                errors.append(f"user-path-boundary:{path.relative_to(root)}")
                break
        for pattern in secret_patterns:
            if pattern.search(text):
                errors.append(f"secret-pattern:{path.relative_to(root)}")
                break

result = {
    "status": "pass" if not errors else "fail",
    "root": display_path(root),
    "today": today.isoformat(),
    "as_of_source": today_source,
    "source_coverage_selection": source_coverage_selection,
    "source_coverage_health": source_coverage_health,
    "source_check_health": source_check_health,
    "source_control_health": source_control_health,
    "owner_target_health": owner_target_health,
    "authorization_health": authorization_health,
    "automation_safety_health": automation_safety_health,
    "boundary_health": boundary_health,
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
