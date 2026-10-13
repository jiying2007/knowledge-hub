#!/usr/bin/env bash
set -euo pipefail
export KNOWLEDGE_PROVIDER_CALLER_CWD="$PWD"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
exec "$ROOT/tools/ci/python-runtime.sh" -m tools.codex_assets.knowledge_hub.context_cli --root "$ROOT" "$@"
