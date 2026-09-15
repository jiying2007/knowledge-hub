#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

if [[ "${1:-}" == "--ui" ]]; then
  shift
  exec "$ROOT/tools/ci/python-runtime.sh" -m tools.codex_assets.knowledge_hub.operator_ui "$ROOT" "$@"
fi

exec "$ROOT/tools/ci/python-runtime.sh" -m tools.codex_assets.knowledge_hub.status_cli "$ROOT" "$@"
