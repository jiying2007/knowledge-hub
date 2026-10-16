#!/usr/bin/env bash
# Run from the engineer's project; preserve their cwd and their Git identity.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
export PYTHONPATH="$ROOT"
exec "$ROOT/tools/ci/python-runtime.sh" -m tools.codex_assets.knowledge_hub.team_submit \
  --hub-repo "$ROOT" "$@"
