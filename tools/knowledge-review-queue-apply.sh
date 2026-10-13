#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
if [[ "${1:-}" == "--ai-delegated" ]]; then
    shift
    exec "$ROOT/tools/ci/python-runtime.sh" -m tools.codex_assets.knowledge_hub.delegated_content_review_cli --root "$ROOT" "$@"
fi
exec "$ROOT/tools/ci/python-runtime.sh" -m tools.codex_assets.knowledge_hub.review_queue_apply_cli "$ROOT" "$@"
