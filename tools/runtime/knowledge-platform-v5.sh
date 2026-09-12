#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec "$ROOT/tools/ci/python-runtime.sh" -m tools.codex_assets.knowledge_hub.runtime_p5_p10_cli --root "$ROOT" "$@"
