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

usage() {
  cat <<EOF
Usage:
  rtk bash tools/knowledge-new.sh --kind <kind> --domain <domain> --id <id> --path <path> [--project <project>] [--owner <owner>]
  rtk bash tools/knowledge-new.sh --source --source-id <source-id> --source-path <path> --role <role> --authority <authority> --write-policy <policy> [--check <command>] [--no-check-reason <reason>] [--owner <owner>]

Examples:
  rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner team-core --id pcr02-example-runbook --path domains/projects/pcr02/current/runbooks/example.md
  rtk bash tools/knowledge-new.sh --kind decision --domain governance --owner leiwenjun --id governance-example-decision --path governance/example-decision.md
  rtk bash tools/knowledge-new.sh --source --source-id example-source --source-path /path/to/source --role project-current-docs-source --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved --no-check-reason "manual source; classify-first pending coverage"

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

if [[ "$SOURCE_MODE" == "true" ]]; then
  DISPLAY_SOURCE_ID="${SOURCE_ID:-${ITEM_ID:-<source-id>}}"
  DISPLAY_SOURCE_PATH="${SOURCE_PATH:-${TARGET_PATH:-<source-root>}}"
  DISPLAY_SOURCE_ROLE="${SOURCE_ROLE:-<role>}"
  DISPLAY_SOURCE_AUTHORITY="${SOURCE_AUTHORITY:-<authority>}"
  DISPLAY_SOURCE_STATUS="${SOURCE_STATUS:-registered}"
  DISPLAY_SOURCE_WRITE_POLICY="${SOURCE_WRITE_POLICY:-<write_policy>}"
  DISPLAY_SOURCE_CHECK="${SOURCE_CHECK:-}"
  DISPLAY_SOURCE_NO_CHECK_REASON="${SOURCE_NO_CHECK_REASON:-<no-check reason if check is empty>}"
  JSON_SOURCE_ID="$(json_escape "$DISPLAY_SOURCE_ID")"
  JSON_SOURCE_PATH="$(json_escape "$DISPLAY_SOURCE_PATH")"
  JSON_SOURCE_ROLE="$(json_escape "$DISPLAY_SOURCE_ROLE")"
  JSON_SOURCE_AUTHORITY="$(json_escape "$DISPLAY_SOURCE_AUTHORITY")"
  JSON_SOURCE_STATUS="$(json_escape "$DISPLAY_SOURCE_STATUS")"
  JSON_SOURCE_WRITE_POLICY="$(json_escape "$DISPLAY_SOURCE_WRITE_POLICY")"
  JSON_SOURCE_CHECK="$(json_escape "$DISPLAY_SOURCE_CHECK")"
  JSON_SOURCE_NO_CHECK_REASON="$(json_escape "$DISPLAY_SOURCE_NO_CHECK_REASON")"
  JSON_OWNER="$(json_escape "${OWNER:-leiwenjun}")"
  TODAY="$(date -u +%F)"
  TODAY_COMPACT="${TODAY//-/}"
  CHECK_FIELD=""
  NO_CHECK_FIELD=",\"no_check_reason\":\"${JSON_SOURCE_NO_CHECK_REASON}\""
  if [[ -n "$DISPLAY_SOURCE_CHECK" ]]; then
    CHECK_FIELD=",\"check\":\"${JSON_SOURCE_CHECK}\""
    NO_CHECK_FIELD=""
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
- no_check_reason: ${DISPLAY_SOURCE_NO_CHECK_REASON}
- owner: ${OWNER:-leiwenjun}

## 最小人工步骤

1. 先确认 source 是外部资料源、历史归档、项目目录、工具目录还是辅助召回层。
2. 在 registry/sources.json 增加 source object；只登记 source，不复制正文。
3. 在 indexes/by-source.md 的 Knowledge Sources 主表增加一行。
4. 在最新 artifacts/manifests/knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl 增加 coverage row，写清 status、classification、decision、risk、owner、checked_at；没有可执行 check 时写 no_check_reason。
5. 如果 source 涉及项目，同步 indexes/by-project.md；涉及主题时同步 indexes/by-topic.md；涉及 owner gate 时补 owner-ready package 或 worksheet。
6. 运行：

   rtk bash tools/knowledge-index-plan.sh --section source
   rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics

## 可复制草稿

### registry/sources.json object

\`\`\`json
{"id":"${JSON_SOURCE_ID}","path":"${JSON_SOURCE_PATH}","role":"${JSON_SOURCE_ROLE}","authority":"${JSON_SOURCE_AUTHORITY}","status":"${JSON_SOURCE_STATUS}","write_policy":"${JSON_SOURCE_WRITE_POLICY}","migration_strategy":"classify-first","owner":"${JSON_OWNER}","review_after":"${TODAY}","final_disposition":"owner-gated-pending-decision"${CHECK_FIELD}${NO_CHECK_FIELD}}
\`\`\`

### indexes/by-source.md 主表行

\`\`\`md
| ${DISPLAY_SOURCE_ID} | ${DISPLAY_SOURCE_ROLE} | \`${DISPLAY_SOURCE_PATH}\` |
\`\`\`

### source coverage JSONL row

\`\`\`json
{"id":"SCC-${TODAY_COMPACT}-${JSON_SOURCE_ID}","source_id":"${JSON_SOURCE_ID}","status":"registered-pending-classification","classification":"classify-first","decision":"新增 source 已进入 Knowledge Hub 控制面；默认不复制正文、不提升 active。","evidence":"registry/sources.json; indexes/by-source.md","risk":"source coverage 只代表治理状态，不代表 owner decision 或 active fact。","owner":"${JSON_OWNER}","checked_at":"${TODAY}","no_check_reason":"${JSON_SOURCE_NO_CHECK_REASON}","source_identity":{"type":"directory-or-external-source","notes":"目录型 source 可用 manifest/evidence refs 表达 identity；不要强制 hash 整个目录。"}}
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

case "$KIND" in
  runbook)
    TEMPLATE="templates/runbook.md"
    ;;
  decision)
    TEMPLATE="templates/decision.md"
    ;;
  validation)
    TEMPLATE="templates/validation-report.md"
    ;;
  project-archive)
    TEMPLATE="templates/archive-note.md"
    ;;
  artifact-ref)
    TEMPLATE="templates/artifact-ref.md"
    ;;
  *)
    TEMPLATE="templates/item.md"
    ;;
esac

DISPLAY_ID="${ITEM_ID:-<id>}"
DISPLAY_KIND="${KIND:-<kind>}"
DISPLAY_DOMAIN="${DOMAIN:-<domain>}"
DISPLAY_PATH="${TARGET_PATH:-<path>}"
DISPLAY_OWNER="${OWNER:-leiwenjun}"
DISPLAY_SCOPE="team-general"
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
DISPLAY_PROJECT="${PROJECT:-<project>}"
JSON_ID="$(json_escape "$DISPLAY_ID")"
JSON_KIND="$(json_escape "$DISPLAY_KIND")"
JSON_DOMAIN="$(json_escape "$DISPLAY_DOMAIN")"
JSON_PATH="$(json_escape "$DISPLAY_PATH")"
JSON_SCOPE="$(json_escape "$DISPLAY_SCOPE")"
JSON_OWNER="$(json_escape "$DISPLAY_OWNER")"
JSON_TITLE="$(json_escape "<中文标题>")"
JSON_SOURCE_FROM="$(json_escape "manual-entry:knowledge-new.sh")"
TODAY="$(date -u +%F)"
if DEFAULT_REVIEW_AFTER="$(date -u -d '+3 months' +%F 2>/dev/null)"; then
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

cat <<EOF
# Knowledge Hub 人工新增向导

本命令只输出人工维护清单，不创建、不修改、不提交任何文件。

## 用法

$(usage)

## 输入摘要

- id: ${ITEM_ID:-<待填写>}
- kind: ${KIND:-<待填写>}
- domain: ${DOMAIN:-<待填写>}
- project: ${PROJECT:-<可选>}
- owner: ${DISPLAY_OWNER}
- path: ${TARGET_PATH:-<待填写>}
- 推荐模板: ${TEMPLATE}
${PROJECT_WARNING_BLOCK}

## 最小人工步骤

1. 先确认正文唯一位置，避免同一正文维护两份。
2. 从 ${TEMPLATE} 复制内容到目标路径，正文默认使用简体中文。
3. 在 registry/items.jsonl 新增一行，字段对齐 registry/schema.md；至少确认 promotion、tags、validation_refs 已填写。
4. 在 indexes/by-owner.md、indexes/by-review-date.md、indexes/by-status.md 登记新 id，避免 missing、stale 或 duplicate item reference。
${PROJECT_STEP_5}
6. 在 registry/migrations.jsonl 新增迁移或治理记录，to 指向真实本地路径。
7. 在正文、manifest 或验证报告中写 Evidence Index，至少记录完整 rtk 命令、退出码、中文结果摘要和证据路径。
8. 运行只读索引计划和验证：

   rtk bash tools/knowledge-index-plan.sh --section all
   rtk bash tools/knowledge-check.sh --dry-run --json
   rtk bash tools/knowledge-check.sh --dry-run --json --explain ${DISPLAY_ID}
   rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
   rtk bash tools/knowledge-search.sh "${ITEM_ID:-<id>}" --json

## 可复制草稿

以下内容是人工填写起点，不会自动落盘。复制前必须把尖括号占位符替换为真实值，并确认 owner、review_after、source、validation_refs、tags 和 migration notes。

默认日期已按当前 UTC 日期生成：created_at / updated_at / checked_at = ${TODAY}，review_after = ${DEFAULT_REVIEW_AFTER}。如 owner 或 review cycle 另有要求，人工落盘前可修改。

### registry/items.jsonl

\`\`\`json
{"id":"${JSON_ID}","title":"${JSON_TITLE}","kind":"${JSON_KIND}","domain":"${JSON_DOMAIN}","path":"${JSON_PATH}","scope":"${JSON_SCOPE}","visibility":"team-internal","status":"reviewing","owner":"${JSON_OWNER}","source":{"type":"manual","from":"${JSON_SOURCE_FROM}"},"validation_refs":["tools/knowledge-check.sh --dry-run --json"],"tags":["knowledge-hub","<topic>"],"review_after":"${DEFAULT_REVIEW_AFTER}","promotion":"none","created_at":"${TODAY}","updated_at":"${TODAY}"}
\`\`\`

### 核心索引

\`\`\`md
# indexes/by-owner.md
- \`${DISPLAY_ID}\`

# indexes/by-review-date.md
- ${DEFAULT_REVIEW_AFTER}: \`${DISPLAY_ID}\`

# indexes/by-status.md
- reviewing: \`${DISPLAY_ID}\`
${PROJECT_INDEX_DRAFT}
\`\`\`

### registry/migrations.jsonl

\`\`\`json
{"from":"<source-or-manual-entry>","to":"${JSON_PATH}","mode":"manual-entry","status":"applied","checked_at":"${TODAY}","notes":"Manual entry created with one canonical body, registry item, core indexes and validation evidence; no source project docs modified, no automation enabled, no active promotion, and no memory written."}
\`\`\`

### Evidence Index

\`\`\`md
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| \`rtk bash tools/knowledge-check.sh --dry-run --json\` | 0 | 中文摘要，说明本次新增条目的 registry、index、migration 和正文通过全仓门禁。 | <manifest-or-report-path> | Knowledge Hub | ${DISPLAY_ID} |
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
