#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

KIND=""
DOMAIN=""
PROJECT=""
OWNER="leiwenjun"
ITEM_ID=""
TARGET_PATH=""
SOURCE_MODE="false"
SOURCE_ID=""
SOURCE_PATH=""
SOURCE_ROLE=""
SOURCE_AUTHORITY=""
SOURCE_STATUS="registered"
SOURCE_WRITE_POLICY=""
SOURCE_CHECK=""
SOURCE_NO_CHECK_REASON=""
ITEM_SOURCE_ID=""
ITEM_SOURCE_PATH=""
MANUAL_SOURCE_REASON="manual-entry:knowledge-new.sh"
MANUAL_VALIDATION_PENDING="false"
MANUAL_VALIDATION_REASON=""
GENERATED_BY_AI="false"
AI_ROLE="none"

usage() {
  cat <<EOF
Usage:
  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --id <id> --path <path> [--project <project>] [--owner <owner>] [--item-source-id <source-id>] [--item-source-path <source-path>] [--manual-source-reason <reason>] [--manual-validation-pending --manual-validation-reason <reason>] [--generated-by-ai --ai-role <role>]
  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id <source-id> --source-path <path> --role <role> --authority <authority> --write-policy <policy> (--check <command> | --no-check-reason <reason>) [--owner <owner>]

Examples:
  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner team-core --id pcr02-example-runbook --path domains/projects/pcr02/current/runbooks/example.md
  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner team-core --id pcr02-example-runbook --path domains/projects/pcr02/current/runbooks/example.md --item-source-id pcr02-project-docs --item-source-path runbooks/example.md
  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner team-core --id pcr02-example-runbook --path domains/projects/pcr02/current/runbooks/example.md --manual-source-reason field-debug --manual-validation-pending --manual-validation-reason "offline lab note awaiting rtk validation"
  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind decision --domain governance --owner leiwenjun --id governance-example-decision --path governance/example-decision.md
  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id example-source --source-path /path/to/source --role project-current-docs-source --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved --check "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"
  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id example-source --source-path /path/to/source --role project-current-docs-source --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved --no-check-reason "manual source; classify-first pending coverage"

This command is read-only. It prints a manual checklist and never creates, edits, commits or promotes files.
EOF
}

read_value() {
  local option="$1"
  local value="${2:-}"
  if [[ -z "$value" || "$value" == --* ]]; then
    printf "ERROR %s requires a value.\n" "$option" >&2
    printf "Run: rtk bash %s --help\n" "$0" >&2
    exit 2
  fi
  printf "%s" "$value"
}

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf "%s" "$value"
}

owner_registry_status() {
  local owner="$1"
  if [[ ! -f "$ROOT/registry/owners.json" ]]; then
    printf "owners-registry-missing"
    return 0
  fi
  if rtk python3 - "$ROOT/registry/owners.json" "$owner" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
owner = sys.argv[2]
data = json.loads(path.read_text())
owner_ids = {
    str(row.get("id", ""))
    for row in data.get("owners", [])
    if isinstance(row, dict)
}
sys.exit(0 if owner in owner_ids else 1)
PY
  then
    printf "registered"
  else
    printf "unknown-owner"
  fi
}

knowledge_today() {
  local raw="${KNOWLEDGE_TODAY:-}"
  if [[ -n "$raw" ]]; then
    if [[ ! "$raw" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
      printf "ERROR KNOWLEDGE_TODAY must be YYYY-MM-DD: %s\n" "$raw" >&2
      exit 2
    fi
    if [[ "$(date -u -d "$raw" +%F 2>/dev/null || true)" != "$raw" ]]; then
      printf "ERROR KNOWLEDGE_TODAY is not a valid date: %s\n" "$raw" >&2
      exit 2
    fi
    printf "%s" "$raw"
  else
    date -u +%F
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE_MODE="true"
      shift
      ;;
    --source-id)
      SOURCE_ID="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --source-path)
      SOURCE_PATH="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --item-source-id)
      ITEM_SOURCE_ID="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --item-source-path)
      ITEM_SOURCE_PATH="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --role)
      SOURCE_ROLE="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --authority)
      SOURCE_AUTHORITY="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --write-policy)
      SOURCE_WRITE_POLICY="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --source-status)
      SOURCE_STATUS="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --check)
      SOURCE_CHECK="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --no-check-reason)
      SOURCE_NO_CHECK_REASON="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --kind)
      KIND="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --domain)
      DOMAIN="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --project)
      PROJECT="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --owner)
      OWNER="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --manual-source-reason)
      MANUAL_SOURCE_REASON="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --manual-validation-pending)
      MANUAL_VALIDATION_PENDING="true"
      shift
      ;;
    --manual-validation-reason)
      MANUAL_VALIDATION_REASON="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --generated-by-ai)
      GENERATED_BY_AI="true"
      shift
      ;;
    --ai-role)
      AI_ROLE="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --id)
      ITEM_ID="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    --path)
      TARGET_PATH="$(read_value "$1" "${2:-}")"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf "ERROR unknown argument: %s\n" "$1" >&2
      printf "Run: rtk bash %s --help\n" "$0" >&2
      exit 2
      ;;
  esac
done

if [[ "$KIND" == "source" ]]; then
  SOURCE_MODE="true"
fi

case "$AI_ROLE" in
  none|drafted|summarized|translated|rewritten|classified|extracted)
    ;;
  *)
    printf "ERROR --ai-role must be one of: none, drafted, summarized, translated, rewritten, classified, extracted.\n" >&2
    exit 2
    ;;
esac

if [[ "$AI_ROLE" != "none" ]]; then
  GENERATED_BY_AI="true"
fi

if [[ "$GENERATED_BY_AI" == "true" && "$AI_ROLE" == "none" ]]; then
  printf "ERROR --generated-by-ai requires --ai-role <drafted|summarized|translated|rewritten|classified|extracted>.\n" >&2
  exit 2
fi

if [[ "$MANUAL_VALIDATION_PENDING" == "true" && -z "$MANUAL_VALIDATION_REASON" ]]; then
  printf "ERROR --manual-validation-pending requires --manual-validation-reason <reason>.\n" >&2
  exit 2
fi

if [[ "$SOURCE_MODE" == "true" ]]; then
  if [[ -n "$ITEM_SOURCE_ID" || -n "$ITEM_SOURCE_PATH" ]]; then
    printf "ERROR source mode cannot combine --item-source-id/--item-source-path; those options are for normal registry items.\n" >&2
    exit 2
  fi
  if [[ -z "$SOURCE_CHECK" && -z "$SOURCE_NO_CHECK_REASON" ]]; then
    printf "ERROR source mode requires either --check <command> or --no-check-reason <reason>.\n" >&2
    exit 2
  fi
  if [[ -n "$SOURCE_CHECK" && -n "$SOURCE_NO_CHECK_REASON" ]]; then
    printf "ERROR source mode cannot combine --check with --no-check-reason; choose exactly one.\n" >&2
    exit 2
  fi
fi

validate_source_enum() {
  local field="$1"
  local value="$2"
  case "$field" in
    role)
      case "$value" in
        team-knowledge-source|project-archive-source|patent-source|codex-governance-source|auxiliary-memory-source|project-current-docs-source|project-current-tools-source|project-current-knowledge-source|project-product-test-source|project-scratch-source|project-root-artifact-source|project-agent-rules-source|project-agent-config-source) return 0 ;;
      esac
      ;;
    authority)
      case "$value" in
        legacy-team-ssot|legacy-project-history|patent-materials|codex-workflow-history|auxiliary-recall-only|legacy-project-current-docs|legacy-project-current-tools|legacy-project-current-knowledge|legacy-project-product-test|legacy-project-scratch|legacy-project-root-artifacts|legacy-project-agent-rules|legacy-project-agent-config) return 0 ;;
      esac
      ;;
    status)
      case "$value" in
        registered|deprecated|retired) return 0 ;;
      esac
      ;;
    write_policy)
      case "$value" in
        do-not-write-through-knowledge-hub|copy-first-migration-only|do-not-mix-with-engineering-knowledge|use-codex-archive-tools|read-only-unless-explicitly-approved|externalize-to-knowledge-hub-before-prune) return 0 ;;
      esac
      ;;
  esac
  printf "ERROR source %s value is not allowed by registry/schema.md: %s\n" "$field" "$value" >&2
  exit 2
}

if [[ "$SOURCE_MODE" == "true" ]]; then
  [[ -n "$SOURCE_ROLE" ]] && validate_source_enum "role" "$SOURCE_ROLE"
  [[ -n "$SOURCE_AUTHORITY" ]] && validate_source_enum "authority" "$SOURCE_AUTHORITY"
  [[ -n "$SOURCE_STATUS" ]] && validate_source_enum "status" "$SOURCE_STATUS"
  [[ -n "$SOURCE_WRITE_POLICY" ]] && validate_source_enum "write_policy" "$SOURCE_WRITE_POLICY"
fi

if [[ "$SOURCE_MODE" == "true" ]]; then
  DISPLAY_SOURCE_ID="${SOURCE_ID:-${ITEM_ID:-<source-id>}}"
  DISPLAY_SOURCE_PATH="${SOURCE_PATH:-${TARGET_PATH:-<source-root>}}"
  DISPLAY_SOURCE_ROLE="${SOURCE_ROLE:-<role>}"
  DISPLAY_SOURCE_AUTHORITY="${SOURCE_AUTHORITY:-<authority>}"
  DISPLAY_SOURCE_STATUS="${SOURCE_STATUS:-registered}"
  DISPLAY_SOURCE_COVERAGE_STATUS="${DISPLAY_SOURCE_STATUS}-pending-classification"
  DISPLAY_SOURCE_WRITE_POLICY="${SOURCE_WRITE_POLICY:-<write_policy>}"
  DISPLAY_SOURCE_CHECK="${SOURCE_CHECK:-}"
  DISPLAY_SOURCE_NO_CHECK_REASON="${SOURCE_NO_CHECK_REASON:-<no-check reason if check is empty>}"
  JSON_SOURCE_ID="$(json_escape "$DISPLAY_SOURCE_ID")"
  JSON_SOURCE_PATH="$(json_escape "$DISPLAY_SOURCE_PATH")"
  JSON_SOURCE_ROLE="$(json_escape "$DISPLAY_SOURCE_ROLE")"
  JSON_SOURCE_AUTHORITY="$(json_escape "$DISPLAY_SOURCE_AUTHORITY")"
  JSON_SOURCE_STATUS="$(json_escape "$DISPLAY_SOURCE_STATUS")"
  JSON_SOURCE_COVERAGE_STATUS="$(json_escape "$DISPLAY_SOURCE_COVERAGE_STATUS")"
  JSON_SOURCE_WRITE_POLICY="$(json_escape "$DISPLAY_SOURCE_WRITE_POLICY")"
  JSON_SOURCE_CHECK="$(json_escape "$DISPLAY_SOURCE_CHECK")"
  JSON_SOURCE_NO_CHECK_REASON="$(json_escape "$DISPLAY_SOURCE_NO_CHECK_REASON")"
  JSON_OWNER="$(json_escape "${OWNER:-leiwenjun}")"
  TODAY="$(knowledge_today)"
  TODAY_COMPACT="${TODAY//-/}"
  if DEFAULT_REVIEW_AFTER="$(date -u -d "${TODAY} +3 months" +%F 2>/dev/null)"; then
    :
  else
    DEFAULT_REVIEW_AFTER="$TODAY"
  fi
  SOURCE_OWNER_REGISTRY_STATUS="$(owner_registry_status "${OWNER:-leiwenjun}")"
  SOURCE_OWNER_WARNING_LINE=""
  if [[ "$SOURCE_OWNER_REGISTRY_STATUS" == "unknown-owner" ]]; then
    SOURCE_OWNER_WARNING_LINE="- owner_warning_zh: source registry owner 未在 registry/owners.json 登记；落盘前请先补 owner registry，或改用已登记 owner。"
  elif [[ "$SOURCE_OWNER_REGISTRY_STATUS" == "owners-registry-missing" ]]; then
    SOURCE_OWNER_WARNING_LINE="- owner_warning_zh: registry/owners.json 不存在；落盘前请先恢复 owner registry。"
  fi
  RECOMMENDED_SOURCE_FINAL_DISPOSITION="owner-gated-pending-decision"
  RECOMMENDED_SOURCE_MIGRATION_STRATEGY="classify-first"
  SOURCE_DISPOSITION_REASON_ZH="默认保持 owner-gated-pending-decision；需要先完成 source coverage、owner gate 或人工治理判断，不能由向导代签终态。"
  SOURCE_MIGRATION_REASON_ZH="默认保持 classify-first；先登记 source，再由 coverage manifest、registry 和 owner review 决定 copy/reference/artifact/archive/no-migration。"
  case "$DISPLAY_SOURCE_ROLE:$DISPLAY_SOURCE_WRITE_POLICY" in
    project-archive-source:copy-first-migration-only)
      RECOMMENDED_SOURCE_FINAL_DISPOSITION="copy-first-migrated"
      RECOMMENDED_SOURCE_MIGRATION_STRATEGY="copy-first-archive"
      SOURCE_DISPOSITION_REASON_ZH="历史归档 source 且策略为 copy-first-migration-only；人工确认正文唯一位置和索引后，可考虑 copy-first-migrated。"
      SOURCE_MIGRATION_REASON_ZH="归档语料适合按迁移清单批量登记，仍需 manifest 和 registry 证据证明已迁移。"
      ;;
    codex-governance-source:use-codex-archive-tools)
      RECOMMENDED_SOURCE_FINAL_DISPOSITION="reference-first-registered"
      RECOMMENDED_SOURCE_MIGRATION_STRATEGY="reference-first"
      SOURCE_DISPOSITION_REASON_ZH="Codex governance 历史由专用归档工具维护，Knowledge Hub 优先登记引用，不复制原始归档正文。"
      SOURCE_MIGRATION_REASON_ZH="使用引用和恢复入口表达治理关系，避免把历史工作流正文复制成第二份。"
      ;;
    auxiliary-memory-source:*)
      RECOMMENDED_SOURCE_FINAL_DISPOSITION="auxiliary-recall-only"
      RECOMMENDED_SOURCE_MIGRATION_STRATEGY="reference-first"
      SOURCE_DISPOSITION_REASON_ZH="辅助记忆源只能用于召回候选，不写 memory、不进入 active facts、不替代 registry 或 source evidence。"
      SOURCE_MIGRATION_REASON_ZH="只登记辅助召回边界和 no-memory-write 约束，不迁移为团队知识正文。"
      ;;
    project-scratch-source:*)
      RECOMMENDED_SOURCE_FINAL_DISPOSITION="archive-only-registered"
      RECOMMENDED_SOURCE_MIGRATION_STRATEGY="archive-only"
      SOURCE_DISPOSITION_REASON_ZH="scratch/session/handoff 默认 archive-only；memory candidates 和上下文草稿不得进入 active facts。"
      SOURCE_MIGRATION_REASON_ZH="保留历史证据与边界，不复制为当前项目事实。"
      ;;
    project-agent-config-source:*)
      RECOMMENDED_SOURCE_FINAL_DISPOSITION="artifact-ref-registered"
      RECOMMENDED_SOURCE_MIGRATION_STRATEGY="artifact-ref"
      SOURCE_DISPOSITION_REASON_ZH="agent config 属于配置或自动化制品引用；默认登记 config/artifact-ref，自动化必须 report-only。"
      SOURCE_MIGRATION_REASON_ZH="记录路径、hash、owner 和安全边界，不把配置正文提升为团队规则。"
      ;;
  esac
  if [[ -n "$DISPLAY_SOURCE_CHECK" ]]; then
    case "$DISPLAY_SOURCE_ROLE" in
      project-current-tools-source|project-current-knowledge-source|project-product-test-source|project-root-artifact-source)
        RECOMMENDED_SOURCE_FINAL_DISPOSITION="mixed-terminal-coverage"
        RECOMMENDED_SOURCE_MIGRATION_STRATEGY="mixed-terminal-coverage"
        SOURCE_DISPOSITION_REASON_ZH="当前项目目录有稳定只读 check，可按文件类型混合登记 copy/reference/artifact/config/tool-ref；不默认复制脚本或二进制正文。"
        SOURCE_MIGRATION_REASON_ZH="用 coverage manifest 表达多种终态组合，check 只证明可复核，不证明 owner 签收或 active 提升。"
        ;;
    esac
  elif [[ "$DISPLAY_SOURCE_ROLE" == project-current-* ]]; then
    RECOMMENDED_SOURCE_FINAL_DISPOSITION="owner-gated-pending-decision"
    RECOMMENDED_SOURCE_MIGRATION_STRATEGY="classify-first"
    SOURCE_DISPOSITION_REASON_ZH="当前项目 source 没有稳定 check；先保持 owner-gated-pending-decision，避免把未复核内容误写成终态。"
    SOURCE_MIGRATION_REASON_ZH="需要先补 coverage row、source identity 或 no-check reason，再由 owner/维护者确认后续处置。"
  fi
  CHECK_FIELD=""
  NO_CHECK_FIELD=",\"no_check_reason\":\"${JSON_SOURCE_NO_CHECK_REASON}\""
  DISPLAY_SOURCE_NO_CHECK_SUMMARY="${DISPLAY_SOURCE_NO_CHECK_REASON}"
  if [[ -n "$DISPLAY_SOURCE_CHECK" ]]; then
    CHECK_FIELD=",\"check\":\"${JSON_SOURCE_CHECK}\""
    NO_CHECK_FIELD=""
    DISPLAY_SOURCE_NO_CHECK_SUMMARY="<not-required: check provided>"
  fi
  cat <<EOF
# Knowledge Hub Source 登记向导

本命令只输出 source 人工维护清单，不创建、不修改、不提交任何文件。

## 输入摘要

- source_id: ${DISPLAY_SOURCE_ID}
- source_path: ${DISPLAY_SOURCE_PATH}
- role: ${DISPLAY_SOURCE_ROLE}
- authority: ${DISPLAY_SOURCE_AUTHORITY}
- status: ${DISPLAY_SOURCE_STATUS}
- write_policy: ${DISPLAY_SOURCE_WRITE_POLICY}
- check: ${DISPLAY_SOURCE_CHECK:-<空>}
- no_check_reason: ${DISPLAY_SOURCE_NO_CHECK_SUMMARY}
- owner: ${OWNER:-leiwenjun}
- owner_registry_status: ${SOURCE_OWNER_REGISTRY_STATUS}
${SOURCE_OWNER_WARNING_LINE}

## 只读推荐提示

- recommended_final_disposition: ${RECOMMENDED_SOURCE_FINAL_DISPOSITION}
- recommended_migration_strategy: ${RECOMMENDED_SOURCE_MIGRATION_STRATEGY}
- disposition_reason_zh: ${SOURCE_DISPOSITION_REASON_ZH}
- migration_reason_zh: ${SOURCE_MIGRATION_REASON_ZH}
- recommendation_scope_zh: 以上只是人工填写提示，不代表 owner decision，不关闭 owner gate；可复制 JSON 仍默认保守，落盘前必须按 registry/schema.md、coverage manifest 和 owner gate 状态确认。

## 最小人工步骤

1. 先确认 source 是外部资料源、历史归档、项目目录、工具目录还是辅助召回层。
2. 在 registry/sources.json 增加 source object；只登记 source，不复制正文。
3. 在 indexes/by-source.md 的 Knowledge Sources 主表增加一行。
4. 在最新 artifacts/manifests/knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl 增加 coverage row，写清 status、classification、decision、risk、owner、checked_at；没有可执行 check 时写 no_check_reason。
5. 如果 source 涉及项目，同步 indexes/by-project.md；涉及主题时同步 indexes/by-topic.md；涉及 owner gate 时补 owner-ready package 或 worksheet。
6. 运行：

   rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source
   rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics

## 枚举速查

- role: team-knowledge-source / project-archive-source / patent-source / codex-governance-source / auxiliary-memory-source / project-current-docs-source / project-current-tools-source / project-current-knowledge-source / project-product-test-source / project-scratch-source / project-root-artifact-source / project-agent-rules-source / project-agent-config-source
- authority: legacy-team-ssot / legacy-project-history / patent-materials / codex-workflow-history / auxiliary-recall-only / legacy-project-current-docs / legacy-project-current-tools / legacy-project-current-knowledge / legacy-project-product-test / legacy-project-scratch / legacy-project-root-artifacts / legacy-project-agent-rules / legacy-project-agent-config
- status: registered / deprecated / retired
- write_policy: do-not-write-through-knowledge-hub / copy-first-migration-only / do-not-mix-with-engineering-knowledge / use-codex-archive-tools / read-only-unless-explicitly-approved / externalize-to-knowledge-hub-before-prune
- final_disposition 常用值: fully-migrated / copy-first-migrated / reference-first-registered / artifact-ref-registered / archive-only-registered / owner-gated-pending-decision / no-migration-with-reason / auxiliary-recall-only / external-tool-owned / mixed-terminal-coverage

脚本会对已传入的 role、authority、status 和 write_policy 做预校验；final_disposition 仍需落盘前按 \`registry/schema.md\` 人工确认。

## 可复制草稿

### registry/sources.json object

\`\`\`json
{"id":"${JSON_SOURCE_ID}","path":"${JSON_SOURCE_PATH}","role":"${JSON_SOURCE_ROLE}","authority":"${JSON_SOURCE_AUTHORITY}","status":"${JSON_SOURCE_STATUS}","write_policy":"${JSON_SOURCE_WRITE_POLICY}","migration_strategy":"classify-first","owner":"${JSON_OWNER}","review_after":"${DEFAULT_REVIEW_AFTER}","final_disposition":"owner-gated-pending-decision"${CHECK_FIELD}${NO_CHECK_FIELD}}
\`\`\`

### indexes/by-source.md 主表行

\`\`\`md
| ${DISPLAY_SOURCE_ID} | ${DISPLAY_SOURCE_ROLE} | \`${DISPLAY_SOURCE_PATH}\` |
\`\`\`

### source coverage JSONL row

\`\`\`json
{"id":"SCC-${TODAY_COMPACT}-${JSON_SOURCE_ID}","source_id":"${JSON_SOURCE_ID}","status":"${JSON_SOURCE_COVERAGE_STATUS}","classification":"classify-first","decision":"新增 source 已进入 Knowledge Hub 控制面；默认不复制正文、不提升 active。","evidence":"registry/sources.json; indexes/by-source.md","risk":"source coverage 只代表治理状态，不代表 owner decision 或 active fact。","owner":"${JSON_OWNER}","checked_at":"${TODAY}"${CHECK_FIELD}${NO_CHECK_FIELD},"source_identity":{"type":"directory-or-external-source","notes":"目录型 source 可用 manifest/evidence refs 表达 identity；不要强制 hash 整个目录。"}}
\`\`\`

## 不要做

- 不修改 source 目录或源项目文件。
- 不复制大附件、日志、二进制、脚本或 session 正文。
- 不把 project-specific 内容提升到 domains/embedded/standards。
- 不生成 owner decision，不关闭 owner gate。
- 不启用自动化写操作，不写 memory。
EOF
  exit 0
fi

if [[ -n "$ITEM_SOURCE_PATH" && -z "$ITEM_SOURCE_ID" ]]; then
  printf "ERROR --item-source-path requires --item-source-id <registered-source-id>.\n" >&2
  exit 2
fi

if [[ -n "$ITEM_SOURCE_ID" ]]; then
  if [[ ! -f "$ROOT/registry/sources.json" ]]; then
    printf "ERROR registry/sources.json is missing; cannot validate --item-source-id %s.\n" "$ITEM_SOURCE_ID" >&2
    exit 2
  fi
  if ! rtk python3 - "$ROOT/registry/sources.json" "$ITEM_SOURCE_ID" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
source_id = sys.argv[2]
data = json.loads(path.read_text())
source_ids = {
    str(row.get("id", ""))
    for row in data.get("sources", [])
    if isinstance(row, dict)
}
sys.exit(0 if source_id in source_ids else 1)
PY
  then
    printf "ERROR --item-source-id is not registered in registry/sources.json: %s\n" "$ITEM_SOURCE_ID" >&2
    exit 2
  fi
fi

case "$KIND" in
  runbook)
    TEMPLATE="templates/runbook.md"
    ;;
  decision)
    TEMPLATE="templates/decision.md"
    ;;
  validation|validation-report)
    TEMPLATE="templates/validation-report.md"
    ;;
  project-archive|archive-note)
    TEMPLATE="templates/archive-note.md"
    ;;
  debug-record)
    TEMPLATE="templates/debug-record.md"
    ;;
  external-source-note|external-source)
    TEMPLATE="templates/external-source-note.md"
    ;;
  owner-decision-worksheet|owner-worksheet)
    TEMPLATE="templates/owner-decision-worksheet.md"
    ;;
  patent-disclosure|patent)
    TEMPLATE="templates/patent-disclosure.md"
    ;;
  migration-record|migration)
    TEMPLATE="templates/migration-record.md"
    ;;
  artifact-ref)
    TEMPLATE="templates/artifact-ref.md"
    ;;
  *)
    TEMPLATE="templates/item.md"
    ;;
esac

REGISTRY_KIND="${KIND:-<kind>}"
case "$KIND" in
  validation-report)
    REGISTRY_KIND="validation"
    ;;
  archive-note)
    REGISTRY_KIND="project-archive"
    ;;
  external-source)
    REGISTRY_KIND="external-source-note"
    ;;
  owner-worksheet)
    REGISTRY_KIND="owner-decision-worksheet"
    ;;
  migration)
    REGISTRY_KIND="migration-record"
    ;;
esac

DRAFT_STATUS="reviewing"
STATUS_INDEX_BUCKET="reviewing"
if [[ "$REGISTRY_KIND" == "project-archive" ]]; then
  DRAFT_STATUS="archived"
  STATUS_INDEX_BUCKET="archived"
fi

DISPLAY_ID="${ITEM_ID:-<id>}"
DISPLAY_INPUT_KIND="${KIND:-<kind>}"
DISPLAY_KIND="$REGISTRY_KIND"
DISPLAY_PATH="${TARGET_PATH:-<path>}"
DISPLAY_OWNER="${OWNER:-leiwenjun}"
ITEM_OWNER_REGISTRY_STATUS="$(owner_registry_status "$DISPLAY_OWNER")"
ITEM_OWNER_WARNING_LINE=""
if [[ "$ITEM_OWNER_REGISTRY_STATUS" == "unknown-owner" ]]; then
  ITEM_OWNER_WARNING_LINE="- owner_warning_zh: item owner 未在 registry/owners.json 登记；落盘前请先补 owner registry，或改用已登记 owner。"
elif [[ "$ITEM_OWNER_REGISTRY_STATUS" == "owners-registry-missing" ]]; then
  ITEM_OWNER_WARNING_LINE="- owner_warning_zh: registry/owners.json 不存在；落盘前请先恢复 owner registry。"
fi
if [[ -z "$DOMAIN" && "$TARGET_PATH" == domains/personal/* ]]; then
  DOMAIN="personal"
fi
DISPLAY_DOMAIN="${DOMAIN:-<domain>}"
DISPLAY_SCOPE="team-general"
DISPLAY_VISIBILITY="team-internal"
PROJECT_WARNING_BLOCK=""
if [[ "$DOMAIN" == projects/* ]]; then
  DISPLAY_SCOPE="project-specific"
  PROJECT_FROM_DOMAIN="${DOMAIN#projects/}"
  if [[ -z "$PROJECT" ]]; then
    PROJECT="$PROJECT_FROM_DOMAIN"
  elif [[ "$PROJECT" != "$PROJECT_FROM_DOMAIN" ]]; then
    printf -v PROJECT_WARNING_BLOCK '\n## 输入提示\n\n- WARNING: --project `%s` 与 --domain `%s` 推导出的项目 `%s` 不一致；请人工确认项目导航和 registry domain。\n' "$PROJECT" "$DOMAIN" "$PROJECT_FROM_DOMAIN"
  fi
fi
PERSONAL_WARNING_BLOCK=""
PERSONAL_DEFAULT_REASON=""
if [[ "$DOMAIN" == "personal" ]]; then
  DISPLAY_VISIBILITY="personal-local"
  DRAFT_STATUS="personal"
  STATUS_INDEX_BUCKET="personal"
  PERSONAL_DEFAULT_REASON="- personal_default_reason_zh: personal-local 条目默认不进入团队 active index，不得标记 active，不代表 owner decision。"
fi
if [[ -n "$TARGET_PATH" && "$TARGET_PATH" == domains/personal/* && "$DOMAIN" != "personal" ]]; then
  printf -v PERSONAL_WARNING_BLOCK '\n## 输入提示\n\n- WARNING: 目标路径 `%s` 位于 domains/personal/，但 --domain 为 `%s`；该组合会被 domain/path invariant 拦截，不可直接落盘。请改为 `--domain personal`，或移动目标路径。\n' "$TARGET_PATH" "${DOMAIN:-<未指定>}"
fi
DISPLAY_PROJECT="${PROJECT:-<project>}"
JSON_ID="$(json_escape "$DISPLAY_ID")"
JSON_KIND="$(json_escape "$DISPLAY_KIND")"
JSON_DOMAIN="$(json_escape "$DISPLAY_DOMAIN")"
JSON_PATH="$(json_escape "$DISPLAY_PATH")"
JSON_SCOPE="$(json_escape "$DISPLAY_SCOPE")"
JSON_VISIBILITY="$(json_escape "$DISPLAY_VISIBILITY")"
JSON_OWNER="$(json_escape "$DISPLAY_OWNER")"
JSON_TITLE="$(json_escape "<中文标题>")"
JSON_SOURCE_FROM="$(json_escape "$MANUAL_SOURCE_REASON")"
JSON_ITEM_SOURCE_ID="$(json_escape "$ITEM_SOURCE_ID")"
JSON_ITEM_SOURCE_PATH="$(json_escape "$ITEM_SOURCE_PATH")"
JSON_MANUAL_VALIDATION_REASON="$(json_escape "$MANUAL_VALIDATION_REASON")"
JSON_AI_ROLE="$(json_escape "$AI_ROLE")"
TODAY="$(knowledge_today)"
AI_MODEL_OR_TOOL=""
AI_GENERATED_AT=""
if [[ "$GENERATED_BY_AI" == "true" ]]; then
  AI_MODEL_OR_TOOL="Codex"
  AI_GENERATED_AT="$TODAY"
fi
JSON_AI_MODEL_OR_TOOL="$(json_escape "$AI_MODEL_OR_TOOL")"
JSON_AI_GENERATED_AT="$(json_escape "$AI_GENERATED_AT")"
if DEFAULT_REVIEW_AFTER="$(date -u -d "${TODAY} +3 months" +%F 2>/dev/null)"; then
  :
else
  DEFAULT_REVIEW_AFTER="$TODAY"
fi
PROJECT_INDEX_DRAFT=""
PROJECT_STEP_5="5. 如需主题入口，在 indexes/by-topic.md 增加可读路径引用。"
if [[ "$DOMAIN" == projects/* ]]; then
  PROJECT_STEP_5="5. 同步 indexes/by-project.md 的项目导航入口；如需主题入口，在 indexes/by-topic.md 增加可读路径引用。"
  printf -v PROJECT_INDEX_DRAFT '\n# indexes/by-project.md\n# 项目域条目：在对应项目段增加目标路径或 manifest 路径。\n- %s: %s\n' "$DISPLAY_PROJECT" "$DISPLAY_PATH"
fi
DECISION_INDEX_DRAFT=""
DECISION_INDEX_STEP=""
if [[ "$KIND" == "decision" ]]; then
  DECISION_INDEX_STEP="如 kind=decision，必须同步 indexes/by-decision.md，记录 decision id、owner、状态和证据路径。"
  printf -v DECISION_INDEX_DRAFT '\n# indexes/by-decision.md\n# 决策类条目：在 registry decision、owner worksheet 或 migration decision 入口登记可恢复路径。\n- %s: %s\n' "$DISPLAY_ID" "$DISPLAY_PATH"
fi
SOURCE_INDEX_DRAFT=""
SOURCE_INDEX_STEP="若 source.from 或后续人工 source_id 指向 registry/sources.json 中的已登记 source，必须同步 indexes/by-source.md。"
printf -v SOURCE_INDEX_DRAFT '\n# indexes/by-source.md\n# 条件索引：本次未提供 --item-source-id；未知来源不要同步 by-source，也不要复制 `<source-id>` 占位行。\n# 后续确认 source_id 已存在于 registry/sources.json 后，再按真实 source_id 追加，或重新运行 --item-source-id 生成草稿：\n# - <真实-source-id>: `%s`\n' "$DISPLAY_ID"
SOURCE_OBJECT_JSON="{\"type\":\"manual\",\"from\":\"${JSON_SOURCE_FROM}\"}"
SOURCE_SEARCH_COMMAND="rtk bash ~/knowledge-hub/tools/knowledge-search.sh \"${ITEM_ID:-<id>}\" --json"
if [[ -n "$ITEM_SOURCE_ID" ]]; then
  SOURCE_INDEX_STEP="已提供 --item-source-id，必须同步 indexes/by-source.md，并确认该 source 仍处于 registry/sources.json 管理范围。"
  printf -v SOURCE_INDEX_DRAFT '\n# indexes/by-source.md\n# 已登记 source 条目：按真实 source_id 增加可恢复引用，不复制 source 正文。\n- %s: `%s`\n' "$ITEM_SOURCE_ID" "$DISPLAY_ID"
  SOURCE_SEARCH_COMMAND="rtk bash ~/knowledge-hub/tools/knowledge-search.sh \"${ITEM_ID:-<id>}\" --source-id ${ITEM_SOURCE_ID} --json"
  if [[ -n "$ITEM_SOURCE_PATH" ]]; then
    SOURCE_OBJECT_JSON="{\"type\":\"registered\",\"source_id\":\"${JSON_ITEM_SOURCE_ID}\",\"source_path\":\"${JSON_ITEM_SOURCE_PATH}\",\"from\":\"${JSON_SOURCE_FROM}\"}"
  else
    SOURCE_OBJECT_JSON="{\"type\":\"registered\",\"source_id\":\"${JSON_ITEM_SOURCE_ID}\",\"from\":\"${JSON_SOURCE_FROM}\"}"
  fi
fi
VALIDATION_REFS_JSON='["rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"]'
MANUAL_VALIDATION_BLOCK=""
if [[ "$MANUAL_VALIDATION_PENDING" == "true" ]]; then
  VALIDATION_REFS_JSON="[\"manual_validation_pending: true\",\"reason: ${JSON_MANUAL_VALIDATION_REASON}\",\"required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics\"]"
  printf -v MANUAL_VALIDATION_BLOCK '\n### 人工待验证说明\n\n```yaml\nmanual_validation_pending: true\nmanual_validation_reason: %s\nrequired_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics\n```\n' "$MANUAL_VALIDATION_REASON"
fi

cat <<EOF
# Knowledge Hub 人工新增向导

本命令只输出人工维护清单，不创建、不修改、不提交任何文件。

## 用法

$(usage)

## 输入摘要

- id: ${ITEM_ID:-<待填写>}
- input_kind: ${DISPLAY_INPUT_KIND}
- registry_kind: ${DISPLAY_KIND}
- domain: ${DOMAIN:-<待填写>}
- project: ${PROJECT:-<可选>}
- owner: ${DISPLAY_OWNER}
- owner_registry_status: ${ITEM_OWNER_REGISTRY_STATUS}
${ITEM_OWNER_WARNING_LINE}
- path: ${TARGET_PATH:-<待填写>}
- item_source_id: ${ITEM_SOURCE_ID:-<未指定>}
- item_source_path: ${ITEM_SOURCE_PATH:-<未指定>}
- 推荐模板: ${TEMPLATE}
- 推荐 registry status: ${DRAFT_STATUS}
- 推荐 visibility: ${DISPLAY_VISIBILITY}
- 推荐 scope: ${DISPLAY_SCOPE}
${PERSONAL_DEFAULT_REASON}
- manual_source_reason: ${MANUAL_SOURCE_REASON}
- manual_validation_pending: ${MANUAL_VALIDATION_PENDING}
- generated_by_ai: ${GENERATED_BY_AI}
- ai_role: ${AI_ROLE}
${PROJECT_WARNING_BLOCK}
${PERSONAL_WARNING_BLOCK}

## 最小人工步骤

1. 先确认正文唯一位置，避免同一正文维护两份。
2. 从 ${TEMPLATE} 复制内容到目标路径，正文默认使用简体中文。
3. 在 registry/items.jsonl 新增一行，字段对齐 registry/schema.md；至少确认 promotion、promotion_decision、tags、validation_refs 已填写。\`promotion\` 是当前允许枚举值，\`promotion_decision\` 是提升或不提升的中文决策说明，二者不能混用。
4. 在 indexes/by-owner.md、indexes/by-review-date.md、indexes/by-status.md 登记新 id，避免 missing、stale 或 duplicate item reference。
${PROJECT_STEP_5}
6. ${SOURCE_INDEX_STEP} ${DECISION_INDEX_STEP}
7. 如涉及迁移、引用或归档，在 registry/migrations.jsonl 新增迁移或治理记录，to 指向真实本地路径；普通新知识不强制新增 migration。
8. 在正文、manifest 或验证报告中写 Evidence Index，至少记录完整 rtk 命令、退出码、中文结果摘要和证据路径。
9. 运行只读索引计划和验证：

   rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
   rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json
   rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain ${DISPLAY_ID}
   rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
   ${SOURCE_SEARCH_COMMAND}

## 可复制草稿

以下内容是人工填写起点，不会自动落盘。复制前必须把尖括号占位符替换为真实值，并确认 owner、review_after、source、validation_refs、tags 和 migration notes。

默认日期已按当前 UTC 日期生成：created_at / updated_at / checked_at = ${TODAY}，review_after = ${DEFAULT_REVIEW_AFTER}。如 owner 或 review cycle 另有要求，人工落盘前可修改。

### registry/items.jsonl

\`\`\`json
{"id":"${JSON_ID}","title":"${JSON_TITLE}","kind":"${JSON_KIND}","domain":"${JSON_DOMAIN}","path":"${JSON_PATH}","scope":"${JSON_SCOPE}","visibility":"${JSON_VISIBILITY}","status":"${DRAFT_STATUS}","owner":"${JSON_OWNER}","source":${SOURCE_OBJECT_JSON},"summary_zh":"<中文 1-3 句摘要>","primary_language":"zh-CN","source_language":"zh-CN","translation_status":"not-required","terminology_status":"pending-review","review_status":"manual-entry-pending-review","evidence_strength":"manual-entry-pending-validation","evidence_refs":[],"promotion_decision":"none","generated_by_ai":${GENERATED_BY_AI},"ai_role":"${JSON_AI_ROLE}","ai_model_or_tool":"${JSON_AI_MODEL_OR_TOOL}","ai_generated_at":"${JSON_AI_GENERATED_AT}","human_reviewed_by":"","human_reviewed_at":"","review_basis":"","validation_refs":${VALIDATION_REFS_JSON},"tags":["knowledge-hub","<topic>"],"review_after":"${DEFAULT_REVIEW_AFTER}","promotion":"none","created_at":"${TODAY}","updated_at":"${TODAY}"}
\`\`\`
${MANUAL_VALIDATION_BLOCK}

### 核心索引

\`\`\`md
# indexes/by-owner.md
- \`${DISPLAY_ID}\`

# indexes/by-review-date.md
- ${DEFAULT_REVIEW_AFTER}: \`${DISPLAY_ID}\`

# indexes/by-status.md
- ${STATUS_INDEX_BUCKET}: \`${DISPLAY_ID}\`
# 状态提示：默认非归档条目使用 - reviewing: \`<id>\`；registry kind 为 project-archive 时使用 - archived: \`<id>\`。
${PROJECT_INDEX_DRAFT}
${SOURCE_INDEX_DRAFT}
${DECISION_INDEX_DRAFT}
\`\`\`

### registry/migrations.jsonl（仅迁移、引用或归档时使用）

\`\`\`json
{"from":"<source-or-manual-entry>","to":"${JSON_PATH}","mode":"manual-entry","status":"applied","checked_at":"${TODAY}","notes":"Manual entry created with one canonical body, registry item, core indexes and validation evidence; no source project docs modified, no automation enabled, no active promotion, and no memory written.","notes_zh":"人工新增条目已按唯一正文、registry item、核心索引和验证证据登记；未修改源项目、未启用自动化、未提升 active、未写 memory。"}
\`\`\`

### Evidence Index

\`\`\`md
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| \`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics\` | 0 | 中文摘要，说明本次新增条目的 registry、index、migration 和正文通过全仓门禁。 | <manifest-or-report-path> | Knowledge Hub | ${DISPLAY_ID} |
\`\`\`

## 不要做

- 不把 project-specific 内容提升到 domains/embedded/standards。
- 不把 personal-local 内容加入团队 active index。
- 不把 raw log、SDK、release binary 或 secret 写入正文。
- 不把 AI 生成内容直接标记为 active，除非已有人工复核证据。

## 低维护原则

- 人工可以直接按模板新增内容；脚本不是唯一入口。
- 自动化默认 report-only。
- 只在 registry、index、migration 三处留下最小可追溯记录。
EOF
