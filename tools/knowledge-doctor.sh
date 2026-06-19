#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ITEM_ID=""

usage() {
  cat <<EOF
Usage:
  rtk bash tools/knowledge-doctor.sh [--id <item-id>]

Examples:
  rtk bash tools/knowledge-doctor.sh
  rtk bash tools/knowledge-doctor.sh --id knowledge-hub-root

This command is read-only. It runs diagnostics, optional item explain and optional search; it never creates, edits, commits or promotes files.
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

while [[ $# -gt 0 ]]; do
  case "$1" in
    --id)
      ITEM_ID="$(read_value "$1" "${2:-}")"
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

run_step() {
  local title="$1"
  shift
  printf "\n## %s\n\n" "$title"
  set +e
  "$@"
  local status=$?
  set -e
  printf "\nstatus: %s\n" "$status"
  return "$status"
}

final_status=0

run_step "全仓诊断" rtk bash "$ROOT/tools/knowledge-check.sh" --dry-run --json --diagnostics || final_status=$?

if [[ -n "$ITEM_ID" ]]; then
  run_step "条目解释: $ITEM_ID" rtk bash "$ROOT/tools/knowledge-check.sh" --dry-run --json --explain "$ITEM_ID" || {
    step_status=$?
    if [[ "$final_status" -eq 0 ]]; then
      final_status="$step_status"
    fi
  }

  run_step "可检索性: $ITEM_ID" rtk bash "$ROOT/tools/knowledge-search.sh" "$ITEM_ID" --json || {
    step_status=$?
    if [[ "$final_status" -eq 0 ]]; then
      final_status="$step_status"
    fi
  }
fi

printf "\n## 下一步\n\n"
if [[ "$final_status" -eq 0 ]]; then
  printf "诊断通过。若刚新增或修改条目，仍需确认 registry、核心索引、migration 和正文已经人工复核。\n"
else
  printf "诊断未通过。优先按 diagnostics.category 的 action_zh 修复；若提供了 --id，再参考 explain 和 search 输出定位具体条目。\n"
fi

exit "$final_status"
