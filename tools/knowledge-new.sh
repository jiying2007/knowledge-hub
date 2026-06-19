#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

KIND=""
DOMAIN=""
PROJECT=""
ITEM_ID=""
TARGET_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --kind)
      KIND="${2:-}"
      shift 2
      ;;
    --domain)
      DOMAIN="${2:-}"
      shift 2
      ;;
    --project)
      PROJECT="${2:-}"
      shift 2
      ;;
    --id)
      ITEM_ID="${2:-}"
      shift 2
      ;;
    --path)
      TARGET_PATH="${2:-}"
      shift 2
      ;;
    -h|--help)
      KIND="${KIND:-}"
      shift
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
    TEMPLATE="templates/migration-record.md"
    ;;
  *)
    TEMPLATE="templates/item.md"
    ;;
esac

cat <<EOF
# Knowledge Hub 人工新增向导

本命令只输出人工维护清单，不创建、不修改、不提交任何文件。

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
3. 在 registry/items.jsonl 新增一行，字段对齐 registry/schema.md。
4. 在 indexes/by-owner.md、indexes/by-review-date.md、indexes/by-status.md 登记新 id。
5. 如需主题入口，在 indexes/by-topic.md 增加可读路径引用。
6. 在 registry/migrations.jsonl 新增迁移或治理记录，to 指向真实本地路径。
7. 运行验证：

   rtk bash tools/knowledge-check.sh --dry-run --json
   rtk bash tools/knowledge-search.sh "${ITEM_ID:-<id>}" --json

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
