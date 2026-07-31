import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys

from .common import (
    KnowledgeHubError,
    display_path,
    file_sha256,
    load_markdown,
    user_path_prefixes,
)
from .model import FRONTMATTER_MIRROR_FIELDS, validate_item
from .output_contract import status_contract
from .security import scan_secret_text
from .source_coverage import select_source_coverage_closeout

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Validate Knowledge Hub registry and safety boundaries.")
parser.add_argument("--dry-run", action="store_true")
output_mode = parser.add_mutually_exclusive_group()
output_mode.add_argument("--json", action="store_true")
output_mode.add_argument("--summary-json", action="store_true")
parser.add_argument("--sources-only", action="store_true")
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

TEXT_FILE_SUFFIXES = {".md", ".json", ".jsonl", ".sh", ".txt"}

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

def frontmatter_scalar(path, field):
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except Exception:
        return ""
    if not lines or lines[0].strip() != "---":
        return ""
    pattern = re.compile(rf"^{re.escape(field)}:\s*(.*?)\s*$")
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip("\"'")
    return ""

def normalize_frontmatter_value(value):
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {
            str(key): normalize_frontmatter_value(row)
            for key, row in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [normalize_frontmatter_value(row) for row in value]
    return value

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
    "hub-canonical-source",
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
    "retired",
}
ALLOWED_SOURCE_WRITE_POLICIES = {
    "knowledge-hub-only",
    "hub-native-registry",
    "runtime-read-only-input",
}
ALLOWED_SOURCE_FINAL_DISPOSITIONS = {
    "hub-canonical",
    "hub-native-source",
    "runtime-input-reference-only",
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
    "manifest",
    "automation-run",
    "unknown",
}
ALLOWED_SOURCE_CONTROL_DISPOSITIONS = {
    "copy-body",
    "summary-only",
    "artifact-ref",
    "reference-only",
    "archive-only",
    "hash-only-provenance",
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
    "source-policy.md",
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
REVIEW_CONTENT_BOUND_DECISIONS = {"accept-as-review-record", "archive-only", "reject"}
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
ALLOWED_PROJECT_REGISTRY_STATUSES = {"registered", "retired"}
ALLOWED_REPOSITORY_LIFECYCLES = {"first-party", "external-reference", "workspace-only", "retired"}
ALLOWED_COMPONENT_STATUSES = {"registered", "workspace-only", "external-reference", "retired"}
ALLOWED_REMOTE_KINDS = {"internal-git", "github", "gitee", "external-git", "local-only"}
ALLOWED_LOGICAL_WORKSPACE_PREFIXES = ("workspace://", "~/knowledge-hub", "~/codex", "~/.codex")
FORBIDDEN_REGISTRY_PATH_TOKENS = ("/home/", "/vsdata/", "~/work/", "~/embedded", "~/bin/", "/work/", "/bin/")

def contains_forbidden_registry_path(value):
    text = str(value or "")
    return any(token in text for token in FORBIDDEN_REGISTRY_PATH_TOKENS)

def is_allowed_workspace_ref(value):
    text = str(value or "")
    return text.startswith(ALLOWED_LOGICAL_WORKSPACE_PREFIXES)

def registry_relpath_ok(value):
    text = str(value or "")
    if not text:
        return False
    return not pathlib.Path(text).is_absolute() and not text.startswith(("./", "../", "~"))

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
            "检查 sources/<source_id>/README.md、inventory.jsonl、coverage.md、source-policy.md，确保每个 registered source 都有 Hub 内控制面，raw/session/source-code 不能 copy-body 进入正文层。",
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
            lambda msg: msg.startswith(("owners:", "projects:", "project-groups:", "repositories:", "components:", "project-routes:", "workspaces:", "topics:")),
        ),
        (
            "owner-routing",
            "owner decision 角色路由异常",
            "检查 registry/owner-routing.json，确保每个 open owner worksheet 角色都有只读分派路由，routing_owner 和 candidate_registry_owners 已登记，且不得把 routing_owner 当作 owner decision。",
            lambda msg: msg.startswith("owner-routing:"),
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
            "同步 tools/knowledge-new.sh 和 templates/README.md 中当前 registry/index/source-policy 门禁提示。",
            lambda msg: msg.startswith("manual-entry:"),
        ),
        (
            "item-source-ref",
            "item source 或 artifact 引用异常",
            "检查 registry/items.jsonl 中 source_id、source_manifest、source_sha256 或 artifact-ref 元数据。",
            lambda msg: msg.startswith("items:") and any(
                token in msg
                for token in [
                    "source_id",
                    "source_manifest",
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
            "frontmatter-status",
            "正文 frontmatter 与 registry 状态不一致",
            "以 registry/items.jsonl 为生命周期权威；不得自动提升 active。由 owner 确认后，将正文 status 调整为 registry 状态，或按授权更新 registry。",
            lambda msg: msg.startswith("frontmatter-status:"),
        ),
        (
            "body-coverage",
            "长期正文缺少精确登记或冻结集合覆盖",
            "检查 registry/body-coverage.json 的路径清单 hash；新增 L2 正文应精确登记，历史 corpus 只能通过显式集合覆盖，不能用宽泛前缀静默吞掉新文件。",
            lambda msg: msg.startswith("body-coverage:"),
        ),
        (
            "artifact-vault",
            "附件 vault 完整性异常",
            "核对 patent artifact manifest 与 artifacts/vault 的 path、size、sha256；缺失附件必须明确标成 external-reference-only，不能宣称本地存在。",
            lambda msg: msg.startswith("artifact-vault:"),
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
            "同步 registry/decisions.jsonl 与 indexes/by-decision.md，只要求 registry decision 在决策索引中恰好出现一次，不把 owner worksheet 或 source-policy decision 当作 registry decision。",
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
            "path-routing",
            "全局路径路由漂移",
            "按 governance/path-routing.md 收敛旧归档路径；Hub 内不得重新出现会影响回答或新增落盘的旧路径 runtime 入口。",
            lambda msg: msg.startswith("path-routing:"),
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
            "action_zh": "warning 不阻断检查，但应按 review_after、参数边界或外部 source 可用性安排人工复核。",
        },
    }

sources_path = root / "registry" / "sources.json"
sources_payload = load_json(sources_path)
current_sources = sources_payload.get("sources", [])
retired_sources = load_jsonl(root / "registry" / "retired-sources.jsonl")
if not isinstance(current_sources, list):
    errors.append("sources: sources must be a list")
    current_sources = []
for source in current_sources:
    if isinstance(source, dict) and source.get("status") != "registered":
        errors.append(f"sources:{source.get('id', '<unknown>')} current registry requires status=registered")
for source in retired_sources:
    if isinstance(source, dict) and source.get("status") != "retired":
        errors.append(f"retired-sources:{source.get('id', '<unknown>')} retired ledger requires status=retired")
sources = current_sources + retired_sources
current_source_ids = {
    str(source.get("id", ""))
    for source in current_sources
    if isinstance(source, dict) and source.get("id") and source.get("status") == "registered"
}
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
    for field in ["id", "path", "role", "authority", "status", "write_policy", "source_strategy", "owner", "review_after", "final_disposition"]:
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
    elif target_decision.startswith("domains/projects/") or target_decision.startswith("domains/personal/"):
        target_status = "noncanonical-target-rejected"
        missing = {
            "worksheet_id": worksheet_id,
            "target_decision": target_decision,
            "mapped_target_path": "",
            "reason": "domains/projects and domains/personal are not canonical owner targets in the current contract",
        }
        owner_target_health["missing_targets"].append(missing)
        errors.append(f"owner-target:{worksheet_id} noncanonical target path rejected: {target_decision}")
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
route_registry_health = {
    "schema_version": 1,
    "status": "not-run",
    "mode": "git-remote-first-route-registry",
    "project_count": 0,
    "group_count": 0,
    "repository_count": 0,
    "component_count": 0,
    "route_count": 0,
    "workspace_example_count": 0,
    "forbidden_path_hits": [],
    "missing_entry_paths": [],
    "invalid_reference_count": 0,
    "report_only_findings": [
        "workspace:// refs are logical adapters; local machine paths belong in untracked local/workspaces.json",
        "~/knowledge-hub, ~/codex and ~/.codex are the only allowed long-term local path conventions",
    ],
}
frontmatter_status_health = {
    "status": "not-run",
    "checked_item_count": 0,
    "declared_status_count": 0,
    "mismatch_count": 0,
    "invalid_status_count": 0,
    "owner_mismatch_count": 0,
    "review_after_mismatch_count": 0,
    "rows": [],
    "notes_zh": "registry/items.jsonl 是 status、owner、review_after 权威；正文 frontmatter 声明这些字段时只能镜像同一值。",
}
body_coverage_health = {
    "status": "not-run",
    "mode": "exact-item-or-frozen-collection",
    "coverage_registry": "registry/body-coverage.json",
    "checked_count": 0,
    "exact_registered_count": 0,
    "collection_covered_count": 0,
    "missing_registry_count": 0,
    "coverage_contract_status": "not-run",
    "coverage_errors": [],
    "missing_registry": [],
}
artifact_vault_health = {
    "status": "not-run",
    "manifest": "artifacts/manifests/patent-disclosure-artifact-ref-20260619.jsonl",
    "vault_root": "artifacts/vault/patent-disclosure",
    "row_count": 0,
    "expected_row_count": 181,
    "required_present_count": 0,
    "external_reference_only_count": 0,
    "missing_required_count": 0,
    "hash_mismatch_count": 0,
    "size_mismatch_count": 0,
    "extra_file_count": 0,
    "duplicate_id_count": 0,
    "duplicate_path_count": 0,
    "invalid_identity_count": 0,
    "symlink_count": 0,
    "errors": [],
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
    project_group_ids = set()
    repository_ids = set()
    remote_keys = set()
    projects_doc = load_json(root / "registry" / "projects.json")
    project_rows = projects_doc.get("projects", [])
    route_registry_health["project_count"] = len(project_rows)
    for project in project_rows:
        project_id = project.get("id")
        if not project_id:
            errors.append("projects: missing id")
            route_registry_health["invalid_reference_count"] += 1
            continue
        if project_id in project_ids:
            errors.append(f"projects:{project_id} duplicate id")
            route_registry_health["invalid_reference_count"] += 1
        project_ids.add(project_id)
        for field in ["name", "type", "domain", "entry", "current", "archive", "decisions", "validation", "groups", "repo_boundary", "status"]:
            if project.get(field) in ("", None, []):
                errors.append(f"projects:{project_id} missing {field}")
                route_registry_health["invalid_reference_count"] += 1
        status = project.get("status")
        if status and status not in ALLOWED_PROJECT_REGISTRY_STATUSES:
            errors.append(f"projects:{project_id} invalid status: {status}")
            route_registry_health["invalid_reference_count"] += 1
        for field in ["domain", "entry", "current", "archive", "decisions", "validation"]:
            value = str(project.get(field, ""))
            if value and contains_forbidden_registry_path(value):
                route_registry_health["forbidden_path_hits"].append(f"projects:{project_id}:{field}")
                errors.append(f"projects:{project_id} {field} must not use machine path: {value}")
            if value and not registry_relpath_ok(value):
                errors.append(f"projects:{project_id} {field} must be repo-relative: {value}")
                route_registry_health["invalid_reference_count"] += 1
        entry = str(project.get("entry", ""))
        if entry and registry_relpath_ok(entry) and not (root / entry).exists():
            route_registry_health["missing_entry_paths"].append(entry)
            errors.append(f"projects:{project_id} entry path missing: {entry}")
        groups_value = project.get("groups", [])
        if not isinstance(groups_value, list) or not groups_value:
            errors.append(f"projects:{project_id} groups must be non-empty list")
            route_registry_health["invalid_reference_count"] += 1

    project_groups_doc = load_json(root / "registry" / "project-groups.json")
    group_rows = project_groups_doc.get("groups", [])
    route_registry_health["group_count"] = len(group_rows)
    for group in group_rows:
        group_id = group.get("id")
        if not group_id:
            errors.append("project-groups: missing id")
            route_registry_health["invalid_reference_count"] += 1
            continue
        if group_id in project_group_ids:
            errors.append(f"project-groups:{group_id} duplicate id")
            route_registry_health["invalid_reference_count"] += 1
        project_group_ids.add(group_id)
        for field in ["name", "type", "entry", "member_project_ids", "status"]:
            if group.get(field) in ("", None, []):
                errors.append(f"project-groups:{group_id} missing {field}")
                route_registry_health["invalid_reference_count"] += 1
        if group.get("status") and group.get("status") not in ALLOWED_PROJECT_REGISTRY_STATUSES:
            errors.append(f"project-groups:{group_id} invalid status: {group.get('status')}")
            route_registry_health["invalid_reference_count"] += 1
        entry = str(group.get("entry", ""))
        if entry and contains_forbidden_registry_path(entry):
            route_registry_health["forbidden_path_hits"].append(f"project-groups:{group_id}:entry")
            errors.append(f"project-groups:{group_id} entry must not use machine path: {entry}")
        if entry and registry_relpath_ok(entry) and not (root / entry).exists():
            route_registry_health["missing_entry_paths"].append(entry)
            errors.append(f"project-groups:{group_id} entry path missing: {entry}")
        for member_project_id in group.get("member_project_ids", []):
            if member_project_id not in project_ids:
                errors.append(f"project-groups:{group_id} unknown member_project_id: {member_project_id}")
                route_registry_health["invalid_reference_count"] += 1

    for project in project_rows:
        project_id = project.get("id", "<unknown>")
        for group_id in project.get("groups", []) if isinstance(project.get("groups", []), list) else []:
            if group_id not in project_group_ids:
                errors.append(f"projects:{project_id} unknown group: {group_id}")
                route_registry_health["invalid_reference_count"] += 1

    repositories_doc = load_json(root / "registry" / "repositories.json")
    repository_rows = repositories_doc.get("repositories", [])
    route_registry_health["repository_count"] = len(repository_rows)
    for repo in repository_rows:
        repo_id = repo.get("repo_id")
        if not repo_id:
            errors.append("repositories: missing repo_id")
            route_registry_health["invalid_reference_count"] += 1
            continue
        if repo_id in repository_ids:
            errors.append(f"repositories:{repo_id} duplicate repo_id")
            route_registry_health["invalid_reference_count"] += 1
        repository_ids.add(repo_id)
        for field in ["remote_key", "remote_kind", "workspace_ref", "groups", "lifecycle", "status"]:
            if repo.get(field) in ("", None, []):
                errors.append(f"repositories:{repo_id} missing {field}")
                route_registry_health["invalid_reference_count"] += 1
        project_id = str(repo.get("project_id", ""))
        lifecycle = str(repo.get("lifecycle", ""))
        if project_id and project_id not in project_ids:
            errors.append(f"repositories:{repo_id} unknown project_id: {project_id}")
            route_registry_health["invalid_reference_count"] += 1
        if not project_id and lifecycle != "external-reference":
            errors.append(f"repositories:{repo_id} empty project_id only allowed for external-reference")
            route_registry_health["invalid_reference_count"] += 1
        remote_key = str(repo.get("remote_key", ""))
        if remote_key:
            if remote_key in remote_keys:
                errors.append(f"repositories:{repo_id} duplicate remote_key: {remote_key}")
                route_registry_health["invalid_reference_count"] += 1
            remote_keys.add(remote_key)
            if any(token in remote_key for token in ("://", "@", "/home/", "/vsdata/")) or remote_key.endswith(".git") or remote_key.startswith("/"):
                errors.append(f"repositories:{repo_id} remote_key must be normalized logical key: {remote_key}")
                route_registry_health["invalid_reference_count"] += 1
        if repo.get("remote_kind") and repo.get("remote_kind") not in ALLOWED_REMOTE_KINDS:
            errors.append(f"repositories:{repo_id} invalid remote_kind: {repo.get('remote_kind')}")
            route_registry_health["invalid_reference_count"] += 1
        if lifecycle and lifecycle not in ALLOWED_REPOSITORY_LIFECYCLES:
            errors.append(f"repositories:{repo_id} invalid lifecycle: {lifecycle}")
            route_registry_health["invalid_reference_count"] += 1
        if repo.get("status") and repo.get("status") not in ALLOWED_PROJECT_REGISTRY_STATUSES:
            errors.append(f"repositories:{repo_id} invalid status: {repo.get('status')}")
            route_registry_health["invalid_reference_count"] += 1
        workspace_ref = str(repo.get("workspace_ref", ""))
        if workspace_ref and not is_allowed_workspace_ref(workspace_ref):
            errors.append(f"repositories:{repo_id} workspace_ref must be logical or allowed local convention: {workspace_ref}")
            route_registry_health["invalid_reference_count"] += 1
        if workspace_ref and contains_forbidden_registry_path(workspace_ref):
            route_registry_health["forbidden_path_hits"].append(f"repositories:{repo_id}:workspace_ref")
            errors.append(f"repositories:{repo_id} workspace_ref must not use machine path: {workspace_ref}")
        for group_id in repo.get("groups", []) if isinstance(repo.get("groups", []), list) else []:
            if group_id not in project_group_ids:
                errors.append(f"repositories:{repo_id} unknown group: {group_id}")
                route_registry_health["invalid_reference_count"] += 1

    components_doc = load_json(root / "registry" / "components.json")
    component_rows = components_doc.get("components", [])
    route_registry_health["component_count"] = len(component_rows)
    component_ids = set()
    for component in component_rows:
        component_id = component.get("component_id")
        if not component_id:
            errors.append("components: missing component_id")
            route_registry_health["invalid_reference_count"] += 1
            continue
        if component_id in component_ids:
            errors.append(f"components:{component_id} duplicate component_id")
            route_registry_health["invalid_reference_count"] += 1
        component_ids.add(component_id)
        for field in ["parent_project_id", "component_uri", "kind", "relative_path", "status"]:
            if field not in component or component.get(field) is None:
                errors.append(f"components:{component_id} missing {field}")
                route_registry_health["invalid_reference_count"] += 1
        parent_project_id = str(component.get("parent_project_id", ""))
        if parent_project_id and parent_project_id not in project_ids:
            errors.append(f"components:{component_id} unknown parent_project_id: {parent_project_id}")
            route_registry_health["invalid_reference_count"] += 1
        component_uri = str(component.get("component_uri", ""))
        if component_uri and not component_uri.startswith("component://"):
            errors.append(f"components:{component_id} component_uri must start with component://")
            route_registry_health["invalid_reference_count"] += 1
        relative_path = str(component.get("relative_path", ""))
        if relative_path and (pathlib.Path(relative_path).is_absolute() or relative_path.startswith(("./", "../", "~")) or contains_forbidden_registry_path(relative_path)):
            errors.append(f"components:{component_id} relative_path must be source-relative logical path: {relative_path}")
            route_registry_health["invalid_reference_count"] += 1
        if component.get("status") and component.get("status") not in ALLOWED_COMPONENT_STATUSES:
            errors.append(f"components:{component_id} invalid status: {component.get('status')}")
            route_registry_health["invalid_reference_count"] += 1

    project_routes_doc = load_json(root / "registry" / "project-routes.json")
    route_rows = project_routes_doc.get("routes", [])
    route_registry_health["route_count"] = len(route_rows)
    route_keys = set()
    for route in route_rows:
        project_id = str(route.get("project_id", ""))
        route_key = project_id or str(route.get("group_id", "<unknown>"))
        if route_key in route_keys:
            errors.append(f"project-routes:{route_key} duplicate route")
            route_registry_health["invalid_reference_count"] += 1
        route_keys.add(route_key)
        for field in ["project_id", "name", "type", "aliases", "repo_refs", "workspace_refs", "hub_entry", "current_path", "archive_path", "decisions_path", "validation_path", "route_key_policy"]:
            if route.get(field) in ("", None, []):
                errors.append(f"project-routes:{route_key} missing {field}")
                route_registry_health["invalid_reference_count"] += 1
        if project_id and project_id not in project_ids:
            errors.append(f"project-routes:{route_key} unknown project_id: {project_id}")
            route_registry_health["invalid_reference_count"] += 1
        group_id = str(route.get("group_id", ""))
        if group_id and group_id not in project_group_ids:
            errors.append(f"project-routes:{route_key} unknown group_id: {group_id}")
            route_registry_health["invalid_reference_count"] += 1
        if "cwd_patterns" in route:
            errors.append(f"project-routes:{route_key} cwd_patterns is not part of the current route contract")
            route_registry_health["invalid_reference_count"] += 1
        if str(route.get("engineering_archive_path", "")):
            errors.append(f"project-routes:{route_key} engineering_archive_path is unsupported; use archive_path")
            route_registry_health["invalid_reference_count"] += 1
        if "retired_route_ids" in route:
            errors.append(f"project-routes:{route_key} retired_route_ids is not part of the current route contract")
            route_registry_health["invalid_reference_count"] += 1
        default_source_ids = route.get("default_source_ids", [])
        if not isinstance(default_source_ids, list):
            errors.append(f"project-routes:{route_key} default_source_ids must be a list")
            route_registry_health["invalid_reference_count"] += 1
        else:
            for default_source_id in default_source_ids:
                if default_source_id not in current_source_ids:
                    errors.append(
                        f"project-routes:{route_key} default_source_id is not a current registered source: {default_source_id}"
                    )
                    route_registry_health["invalid_reference_count"] += 1
        for repo_id in route.get("repo_refs", []) if isinstance(route.get("repo_refs", []), list) else []:
            if repo_id not in repository_ids:
                errors.append(f"project-routes:{route_key} unknown repo_ref: {repo_id}")
                route_registry_health["invalid_reference_count"] += 1
        for workspace_ref in route.get("workspace_refs", []) if isinstance(route.get("workspace_refs", []), list) else []:
            if not is_allowed_workspace_ref(workspace_ref):
                errors.append(f"project-routes:{route_key} invalid workspace_ref: {workspace_ref}")
                route_registry_health["invalid_reference_count"] += 1
            if contains_forbidden_registry_path(workspace_ref):
                route_registry_health["forbidden_path_hits"].append(f"project-routes:{route_key}:workspace_ref")
                errors.append(f"project-routes:{route_key} workspace_ref must not use machine path: {workspace_ref}")
        for field in ["hub_entry", "current_path", "archive_path", "decisions_path", "validation_path"]:
            value = str(route.get(field, ""))
            if value and contains_forbidden_registry_path(value):
                route_registry_health["forbidden_path_hits"].append(f"project-routes:{route_key}:{field}")
                errors.append(f"project-routes:{route_key} {field} must not use machine path: {value}")
            if value and not registry_relpath_ok(value):
                errors.append(f"project-routes:{route_key} {field} must be repo-relative: {value}")
                route_registry_health["invalid_reference_count"] += 1
        hub_entry = str(route.get("hub_entry", ""))
        if hub_entry and registry_relpath_ok(hub_entry) and not (root / hub_entry).exists():
            route_registry_health["missing_entry_paths"].append(hub_entry)
            errors.append(f"project-routes:{route_key} hub_entry path missing: {hub_entry}")

    workspaces_example_doc = load_json(root / "registry" / "workspaces.example.json")
    workspace_rows = workspaces_example_doc.get("workspaces", [])
    route_registry_health["workspace_example_count"] = len(workspace_rows)
    for index, workspace in enumerate(workspace_rows, 1):
        workspace_ref = str(workspace.get("workspace_ref", ""))
        label = workspace_ref or f"row-{index}"
        if not workspace_ref:
            errors.append(f"workspaces:{label} missing workspace_ref")
            route_registry_health["invalid_reference_count"] += 1
        elif not is_allowed_workspace_ref(workspace_ref):
            errors.append(f"workspaces:{label} invalid workspace_ref: {workspace_ref}")
            route_registry_health["invalid_reference_count"] += 1
        for field in ["path", "path_example"]:
            value = str(workspace.get(field, ""))
            if value and contains_forbidden_registry_path(value):
                route_registry_health["forbidden_path_hits"].append(f"workspaces:{label}:{field}")
                errors.append(f"workspaces:{label} {field} must not use machine path: {value}")
        repo_id = str(workspace.get("repo_id", ""))
        group_id = str(workspace.get("project_group_id", ""))
        if repo_id and repo_id not in repository_ids:
            errors.append(f"workspaces:{label} unknown repo_id: {repo_id}")
            route_registry_health["invalid_reference_count"] += 1
        if group_id and group_id not in project_group_ids:
            errors.append(f"workspaces:{label} unknown project_group_id: {group_id}")
            route_registry_health["invalid_reference_count"] += 1

    route_registry_health["forbidden_path_hits"] = sorted(set(route_registry_health["forbidden_path_hits"]))
    route_registry_health["missing_entry_paths"] = sorted(set(route_registry_health["missing_entry_paths"]))
    route_registry_health["status"] = "fail" if (
        route_registry_health["invalid_reference_count"]
        or route_registry_health["forbidden_path_hits"]
        or route_registry_health["missing_entry_paths"]
    ) else "pass"

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
                errors.append(f"topics:{topic_id} domain uses a noncanonical path: {topic_domain}")
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
                    errors.append(f"retention:{index} domain uses a noncanonical path: {rule_domain}")

    local_path_prefixes = LOCAL_PATH_PREFIXES
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
    template_skip = {"README.md"}
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
        "duplicate",
    ]
    manual_entry_files = {
        root / "tools" / "knowledge-new.sh": [
            root / "tools" / "knowledge-new.sh",
            root / "tools" / "codex_assets" / "knowledge_hub" / "new_cli.py",
            root / "tools" / "codex_assets" / "knowledge_hub" / "lifecycle.py",
        ],
        root / "templates" / "README.md": [root / "templates" / "README.md"],
    }
    for manual_entry_file, implementation_files in manual_entry_files.items():
        manual_text = "\n".join(path.read_text() for path in implementation_files)
        rel_manual = manual_entry_file.relative_to(root)
        terms = manual_entry_terms
        if manual_entry_file.name == "knowledge-new.sh":
            terms = [
                "promotion",
                "tags",
                "validation_refs",
                "indexes/by-owner.md",
                "indexes/by-review-date.md",
                "indexes/by-status.md",
                'choices=("draft", "reviewing", "personal")',
                "registry item id already exists",
            ]
        for term in terms:
            if term not in manual_text:
                errors.append(f"manual-entry:{rel_manual} missing current gate term: {term}")

    manual_entry_file_specific_terms = {
        root / "tools" / "knowledge-new.sh": [
            "owner_registry_status",
            "personal-local",
            "recommended_final_disposition",
            "recommended_source_strategy",
            "recommendation_scope_zh",
            "--item-source-id",
            "--check",
            "--no-check-reason",
            "Evidence Index",
        ],
        root / "templates" / "README.md": [
            "personal-local",
            "recommended_final_disposition",
            "recommended_source_strategy",
            "不替代 owner decision",
            "不关闭 owner gate",
            "Evidence Index",
        ],
    }
    for manual_entry_file, terms in manual_entry_file_specific_terms.items():
        implementation_files = manual_entry_files.get(manual_entry_file, [manual_entry_file])
        manual_text = "\n".join(path.read_text() for path in implementation_files)
        rel_manual = manual_entry_file.relative_to(root)
        for term in terms:
            if term not in manual_text:
                errors.append(f"manual-entry:{rel_manual} missing terminal manual-entry term: {term}")

    manual_entry_anchor_checks = {
        "README.md": [
            "日常入口",
            "目录边界",
            "Source 处置口径",
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
    item_ids_by_path = {}
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
        for model_error in validate_item(item):
            errors.append(f"items:{item_id} model: {model_error}")
        item_path = str(item.get("path", "")).strip()
        if item_path:
            previous_id = item_ids_by_path.get(item_path)
            if previous_id:
                errors.append(
                    f"items:{item_id} duplicate path {item_path}; canonical item is {previous_id}"
                )
            else:
                item_ids_by_path[item_path] = item_id
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
            source_manifest = source.get("source_manifest")
            if source_manifest:
                manifest_path = pathlib.Path(str(source_manifest))
                if manifest_path.is_absolute():
                    errors.append(f"items:{item_id} source_manifest must be relative: {source_manifest}")
                elif not (root / manifest_path).exists():
                    errors.append(f"items:{item_id} source_manifest missing: {source_manifest}")
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
        elif rel_path.suffix.lower() == ".md":
            frontmatter_status_health["checked_item_count"] += 1
            try:
                frontmatter_metadata, _frontmatter_body = load_markdown(root / rel_path)
            except KnowledgeHubError as exc:
                errors.append(f"frontmatter-status:{item_id} invalid YAML: {exc}")
                frontmatter_metadata = {}
            for field in FRONTMATTER_MIRROR_FIELDS:
                if field not in frontmatter_metadata:
                    continue
                registry_value = normalize_frontmatter_value(item.get(field))
                frontmatter_value = normalize_frontmatter_value(
                    frontmatter_metadata.get(field)
                )
                if registry_value == frontmatter_value:
                    continue
                frontmatter_status_health["mismatch_count"] += 1
                frontmatter_status_health["rows"].append({
                    "item_id": item_id,
                    "path": rel_path.as_posix(),
                    "field": field,
                    "registry_value": registry_value,
                    "frontmatter_value": frontmatter_value,
                    "status": "mismatch",
                })
                errors.append(
                    f"frontmatter-status:{item_id} field={field} registry={registry_value!r} "
                    f"frontmatter={frontmatter_value!r}: {rel_path.as_posix()}"
                )
            declared_status = frontmatter_scalar(root / rel_path, "status")
            if declared_status:
                frontmatter_status_health["declared_status_count"] += 1
                row = {
                    "item_id": item_id,
                    "path": rel_path.as_posix(),
                    "registry_status": str(item.get("status", "")),
                    "frontmatter_status": declared_status,
                    "status": "pass",
                }
                if declared_status not in ALLOWED_ITEM_STATUSES:
                    row["status"] = "invalid-frontmatter-status"
                    frontmatter_status_health["invalid_status_count"] += 1
                    errors.append(
                        f"frontmatter-status:{item_id} invalid status {declared_status}: {rel_path.as_posix()}"
                    )
                elif declared_status != str(item.get("status", "")):
                    row["status"] = "mismatch"
                    frontmatter_status_health["mismatch_count"] += 1
                    errors.append(
                        f"frontmatter-status:{item_id} registry={item.get('status', '')} "
                        f"frontmatter={declared_status}: {rel_path.as_posix()}"
                    )
                frontmatter_status_health["rows"].append(row)
            for field, counter in (
                ("owner", "owner_mismatch_count"),
                ("review_after", "review_after_mismatch_count"),
            ):
                declared_value = frontmatter_scalar(root / rel_path, field)
                registry_value = str(item.get(field, ""))
                if declared_value and declared_value != registry_value:
                    frontmatter_status_health[counter] += 1
                    frontmatter_status_health["rows"].append({
                        "item_id": item_id,
                        "path": rel_path.as_posix(),
                        "field": field,
                        "registry_value": registry_value,
                        "frontmatter_value": declared_value,
                        "status": "mismatch",
                    })
                    errors.append(
                        f"frontmatter-status:{item_id} field={field} registry={registry_value} "
                        f"frontmatter={declared_value}: {rel_path.as_posix()}"
                    )
        human_review_content_sha256 = str(item.get("human_review_content_sha256", ""))
        if human_review_content_sha256:
            if not SHA256_RE.fullmatch(human_review_content_sha256):
                errors.append(
                    f"items:{item_id} invalid human_review_content_sha256: {human_review_content_sha256}"
                )
            elif (
                str(item.get("human_review_decision", "")) in REVIEW_CONTENT_BOUND_DECISIONS
                and not rel_path.is_absolute()
                and (root / rel_path).is_file()
            ):
                current_content_sha256 = file_sha256(root / rel_path)
                if current_content_sha256 != human_review_content_sha256:
                    errors.append(
                        f"items:{item_id} human review content drift: "
                        f"reviewed={human_review_content_sha256} current={current_content_sha256}"
                    )
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
            errors.append(f"items:{item_id} noncanonical personal domain; use domain=notes path=notes/personal/**")
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

    frontmatter_status_health["status"] = (
        "pass"
        if not frontmatter_status_health["mismatch_count"]
        and not frontmatter_status_health["invalid_status_count"]
        and not frontmatter_status_health["owner_mismatch_count"]
        and not frontmatter_status_health["review_after_mismatch_count"]
        else "fail"
    )

    body_coverage_command = [
        "rtk",
        "bash",
        "tools/knowledge-orphan-files.sh",
        "--all",
        "--strict",
        "--json",
        "--limit",
        "50",
    ]
    body_coverage_run = subprocess.run(
        body_coverage_command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        body_coverage_payload = json.loads(body_coverage_run.stdout)
    except Exception as exc:
        body_coverage_payload = {}
        errors.append(f"body-coverage:unable to parse orphan helper JSON: {exc}")
    if body_coverage_payload:
        body_coverage_health.update(body_coverage_payload)
    if body_coverage_run.returncode != 0:
        if body_coverage_payload.get("coverage_errors"):
            for message in body_coverage_payload.get("coverage_errors", [])[:10]:
                errors.append(f"body-coverage:{message}")
        if body_coverage_payload.get("missing_registry"):
            for path in body_coverage_payload.get("missing_registry", [])[:10]:
                errors.append(f"body-coverage:missing exact or collection coverage: {path}")
        if not body_coverage_payload.get("coverage_errors") and not body_coverage_payload.get("missing_registry"):
            errors.append(
                "body-coverage:strict helper failed without structured findings: "
                + body_coverage_run.stderr.strip()[:300]
            )

    artifact_manifest_path = root / artifact_vault_health["manifest"]
    artifact_vault_root = root / artifact_vault_health["vault_root"]
    artifact_errors = []
    artifact_expected_paths = set()
    if not artifact_manifest_path.exists():
        artifact_errors.append("artifact manifest is missing")
    elif not artifact_vault_root.is_dir():
        artifact_errors.append("artifact vault root is missing")
    else:
        artifact_rows = load_jsonl(artifact_manifest_path)
        artifact_vault_health["row_count"] = len(artifact_rows)
        if len(artifact_rows) != artifact_vault_health["expected_row_count"]:
            artifact_errors.append(
                "artifact identity row count mismatch: "
                f"expected {artifact_vault_health['expected_row_count']}, actual {len(artifact_rows)}"
            )
        seen_artifact_ids = set()
        for row in artifact_rows:
            artifact_id = str(row.get("id", "")).strip()
            source_path = str(row.get("source_path", "")).strip()
            presence = str(row.get("vault_presence", "required")).strip() or "required"
            expected_size = row.get("size")
            expected_hash = str(row.get("sha256", ""))
            identity_invalid = False
            if not artifact_id:
                artifact_errors.append("artifact row has missing id")
                identity_invalid = True
                artifact_id = "<unknown>"
            elif artifact_id in seen_artifact_ids:
                artifact_vault_health["duplicate_id_count"] += 1
                artifact_errors.append(f"duplicate artifact id: {artifact_id}")
                identity_invalid = True
            seen_artifact_ids.add(artifact_id)
            source_parts = pathlib.PurePosixPath(source_path).parts
            if (
                not source_path
                or pathlib.Path(source_path).is_absolute()
                or source_path.startswith(("../", "./", "~/"))
                or "\\" in source_path
                or pathlib.PurePosixPath(source_path).as_posix() != source_path
                or ".." in source_parts
            ):
                artifact_errors.append(f"{artifact_id} invalid source_path: {source_path}")
                artifact_vault_health["invalid_identity_count"] += 1
                continue
            if source_path in artifact_expected_paths:
                artifact_vault_health["duplicate_path_count"] += 1
                artifact_errors.append(f"duplicate artifact source_path: {source_path}")
                identity_invalid = True
            artifact_expected_paths.add(source_path)
            if not isinstance(expected_size, int) or expected_size <= 0:
                artifact_errors.append(f"{artifact_id} invalid size: {expected_size}")
                identity_invalid = True
            if len(expected_hash) != 64 or any(ch not in "0123456789abcdef" for ch in expected_hash):
                artifact_errors.append(f"{artifact_id} invalid sha256: {expected_hash}")
                identity_invalid = True
            if identity_invalid:
                artifact_vault_health["invalid_identity_count"] += 1
            target = artifact_vault_root / source_path
            if presence == "external-reference-only":
                artifact_vault_health["external_reference_only_count"] += 1
                if target.exists():
                    artifact_errors.append(
                        f"{artifact_id} is marked external-reference-only but exists in vault"
                    )
                continue
            if presence != "required":
                artifact_errors.append(f"{artifact_id} invalid vault_presence: {presence}")
                continue
            if target.is_symlink():
                artifact_vault_health["symlink_count"] += 1
                artifact_errors.append(f"{artifact_id} vault file must not be a symlink: {source_path}")
                continue
            if not target.is_file():
                artifact_vault_health["missing_required_count"] += 1
                artifact_errors.append(f"{artifact_id} required vault file is missing: {source_path}")
                continue
            artifact_vault_health["required_present_count"] += 1
            actual_size = target.stat().st_size
            if not isinstance(expected_size, int) or actual_size != expected_size:
                artifact_vault_health["size_mismatch_count"] += 1
                artifact_errors.append(
                    f"{artifact_id} size mismatch: expected {expected_size}, actual {actual_size}"
                )
            actual_hash = file_sha256(target)
            if expected_hash != actual_hash:
                artifact_vault_health["hash_mismatch_count"] += 1
                artifact_errors.append(
                    f"{artifact_id} sha256 mismatch: expected {expected_hash}, actual {actual_hash}"
                )
        vault_entries = list(artifact_vault_root.rglob("*"))
        unexpected_symlinks = [
            path.relative_to(artifact_vault_root).as_posix()
            for path in vault_entries
            if path.is_symlink()
        ]
        artifact_vault_health["symlink_count"] = len(unexpected_symlinks)
        artifact_errors.extend(f"vault symlink is forbidden: {path}" for path in unexpected_symlinks[:20])
        actual_paths = {
            path.relative_to(artifact_vault_root).as_posix()
            for path in vault_entries
            if path.is_file() and not path.is_symlink()
        }
        extra_paths = sorted(actual_paths - artifact_expected_paths)
        artifact_vault_health["extra_file_count"] = len(extra_paths)
        artifact_errors.extend(f"unregistered vault file: {path}" for path in extra_paths[:20])
    artifact_vault_health["errors"] = artifact_errors
    artifact_vault_health["status"] = "pass" if not artifact_errors else "fail"
    errors.extend(f"artifact-vault:{message}" for message in artifact_errors)

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
            status_seen = {
                status: status_bucket_ids(index_path, status)
                for status in ["draft", "active", "reviewing", "archived", "superseded", "rejected", "personal"]
            }
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
        if scan_secret_text(text):
            errors.append(f"secret-pattern:{path.relative_to(root)}")

PATH_ROUTING_TERMS = [
    ("~/embedded/knowledge", "~/embedded/knowledge"),
    ("~/embedded/knowledge", str(pathlib.Path.home() / "embedded" / "knowledge")),
    ("EMBEDDED_KNOWLEDGE_HOME", "EMBEDDED_KNOWLEDGE_HOME"),
    ("~/embedded/engineering_archive", "~/embedded/engineering_archive"),
    ("~/embedded/engineering_archive", str(pathlib.Path.home() / "embedded" / "engineering_archive")),
    ("~/codex/docs/archive", "~/codex/docs/archive"),
    ("~/codex/docs/archive", str(pathlib.Path.home() / "codex" / "docs" / "archive")),
]

PATH_ROUTING_CANONICAL_ROUTES = {
}

def classify_path_routing_hit(rel_path, line_text):
    normalized = rel_path.replace("\\", "/")
    text = line_text.lower()
    if normalized in {
        "README.md",
        "governance/path-routing.md",
        "governance/source-boundaries.md",
        "governance/source-lifecycle-policy.md",
        "registry/schema.md",
        "tools/knowledge-path-audit.sh",
        "tools/knowledge-check.sh",
    }:
        return "canonical-policy"
    if normalized.startswith("domains/codex/archive/codex-archive/"):
        return "provenance"
    if normalized.startswith("sources/") or normalized in {"registry/sources.json", "registry/retired-sources.jsonl"}:
        return "provenance"
    if normalized.startswith("artifacts/manifests/") or normalized.startswith("registry/authorizations") or normalized.startswith("registry/automation-runs"):
        return "provenance"
    if "旧" in line_text or "retired" in text or "provenance" in text or "不再作为" in line_text:
        return "canonical-policy"
    return "runtime-route-candidate"

path_routing_health = {
    "status": "pass",
    "mode": "hub-local-hard-gate",
    "terms": sorted({display for display, _term in PATH_ROUTING_TERMS}),
    "canonical_routes": PATH_ROUTING_CANONICAL_ROUTES,
    "match_count": 0,
    "canonical_policy_count": 0,
    "provenance_count": 0,
    "runtime_route_candidate_count": 0,
    "runtime_route_candidates": [],
    "notes_zh": "旧路径和环境变量没有兼容路由；只允许出现在 detector config 或不可执行 provenance 中，runtime-route-candidate 会阻断 knowledge-check。",
}

if not args.sources_only:
    for path in iter_text_files(scan_roots):
        rel_path = str(path.relative_to(root))
        try:
            lines = path.read_text(errors="ignore").splitlines()
        except Exception as exc:
            warnings.append(f"path-routing:{display_path(path)} unreadable: {exc}")
            continue
        for lineno, line in enumerate(lines, start=1):
            if not any(term in line for _display, term in PATH_ROUTING_TERMS):
                continue
            classification = classify_path_routing_hit(rel_path, line)
            path_routing_health["match_count"] += 1
            if classification == "canonical-policy":
                path_routing_health["canonical_policy_count"] += 1
            elif classification == "provenance":
                path_routing_health["provenance_count"] += 1
            else:
                row = {
                    "path": rel_path,
                    "line": lineno,
                    "text": line.strip()[:200],
                }
                path_routing_health["runtime_route_candidate_count"] += 1
                path_routing_health["runtime_route_candidates"].append(row)
                errors.append(f"path-routing:{rel_path}:{lineno}")
    if path_routing_health["runtime_route_candidate_count"]:
        path_routing_health["status"] = "fail"

result = {
    "status": "pass" if not errors else "needs-fix",
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
    "route_registry_health": route_registry_health,
    "path_routing_health": path_routing_health,
    "frontmatter_status_health": frontmatter_status_health,
    "body_coverage_health": body_coverage_health,
    "artifact_vault_health": artifact_vault_health,
    "errors": errors,
    "warnings": warnings,
    "dry_run": bool(args.dry_run),
}
result["status_contract"] = status_contract(result["status"])
if explain is not None:
    result["explain"] = explain
if args.diagnostics:
    result["diagnostics"] = build_diagnostics(errors, warnings)
if args.json or args.summary_json:
    projection = result
    if args.summary_json:
        diagnostics = result.get("diagnostics", {})
        projection = {
            "schema_version": 1,
            "projection": "knowledge-check-summary-v1",
            "status": result["status"],
            "status_contract": result["status_contract"],
            "root": result["root"],
            "today": result["today"],
            "dry_run": result["dry_run"],
            "error_count": len(errors),
            "warning_count": len(warnings),
            "error_sample": errors[:20],
            "warning_sample": warnings[:10],
            "diagnostic_categories": [
                {
                    "id": row.get("id", ""),
                    "count": row.get("count", 0),
                    "action_zh": row.get("action_zh", ""),
                }
                for row in diagnostics.get("categories", [])[:20]
            ],
            "health": {
                "source_coverage": source_coverage_health.get("status", ""),
                "source_control": source_control_health.get("status", ""),
                "owner_target": owner_target_health.get("status", ""),
                "authorization": authorization_health.get("status", ""),
                "automation_safety": automation_safety_health.get(
                    "status", ""
                ),
                "route_registry": route_registry_health.get("status", ""),
                "path_routing": path_routing_health.get("status", ""),
                "frontmatter": frontmatter_status_health.get("status", ""),
                "body_coverage": body_coverage_health.get("status", ""),
                "artifact_vault": artifact_vault_health.get("status", ""),
            },
        }
    print(json.dumps(projection, ensure_ascii=False, indent=2))
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
