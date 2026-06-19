#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

KIND=""
DOMAIN=""
PROJECT=""
ITEM_ID=""
TARGET_PATH=""

usage() {
  cat <<EOF
Usage:
  rtk bash tools/knowledge-new.sh --kind <kind> --domain <domain> --id <id> --path <path> [--project <project>]

Examples:
  rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --project pcr02 --id pcr02-example-runbook --path domains/projects/pcr02/current/runbooks/example.md
  rtk bash tools/knowledge-new.sh --kind decision --domain governance --id governance-example-decision --path governance/example-decision.md

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
DISPLAY_PROJECT="${PROJECT:-<project>}"
DISPLAY_PATH="${TARGET_PATH:-<path>}"
DISPLAY_SCOPE="team-general"
if [[ "$DOMAIN" == projects/* ]]; then
  DISPLAY_SCOPE="project-specific"
fi
JSON_ID="$(json_escape "$DISPLAY_ID")"
JSON_KIND="$(json_escape "$DISPLAY_KIND")"
JSON_DOMAIN="$(json_escape "$DISPLAY_DOMAIN")"
JSON_PATH="$(json_escape "$DISPLAY_PATH")"
JSON_SCOPE="$(json_escape "$DISPLAY_SCOPE")"
JSON_TITLE="$(json_escape "<中文标题>")"
JSON_SOURCE_FROM="$(json_escape "manual-entry:knowledge-new.sh")"
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
- path: ${TARGET_PATH:-<待填写>}
- 推荐模板: ${TEMPLATE}

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

### registry/items.jsonl

\`\`\`json
{"id":"${JSON_ID}","title":"${JSON_TITLE}","kind":"${JSON_KIND}","domain":"${JSON_DOMAIN}","path":"${JSON_PATH}","scope":"${JSON_SCOPE}","visibility":"team-internal","status":"reviewing","owner":"leiwenjun","source":{"type":"manual","from":"${JSON_SOURCE_FROM}"},"validation_refs":["tools/knowledge-check.sh --dry-run --json"],"tags":["knowledge-hub","<topic>"],"review_after":"<YYYY-MM-DD>","promotion":"none","created_at":"<YYYY-MM-DD>","updated_at":"<YYYY-MM-DD>"}
\`\`\`

### 核心索引

\`\`\`md
# indexes/by-owner.md
- \`${DISPLAY_ID}\`

# indexes/by-review-date.md
- <YYYY-MM-DD>: \`${DISPLAY_ID}\`

# indexes/by-status.md
- reviewing: \`${DISPLAY_ID}\`
${PROJECT_INDEX_DRAFT}
\`\`\`

### registry/migrations.jsonl

\`\`\`json
{"from":"<source-or-manual-entry>","to":"${JSON_PATH}","mode":"manual-entry","status":"applied","checked_at":"<YYYY-MM-DD>","notes":"Manual entry created with one canonical body, registry item, core indexes and validation evidence; no source project docs modified, no automation enabled, no active promotion, and no memory written."}
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
