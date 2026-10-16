#!/usr/bin/env bash
# LAN Team MCP, systemd ExecStart. Run as an unprivileged service user.
set -euo pipefail
ROOT="$(printenv KH_INSTALL_ROOT || echo /srv/knowledge-hub)"
PYTHON="$(printenv KH_PYTHON || echo /usr/bin/python3)"
TOKEN="$(printenv KH_TEAM_TOKEN_FILE || echo /etc/knowledge-hub/team-token)"
PORT="$(printenv KH_TEAM_PORT || echo 3000)"
CURRENT="$(readlink -f "$ROOT/current")"
[[ -n "$CURRENT" && -d "$CURRENT" && -f "$CURRENT/.serving-sha" ]] || exit 2
case "$CURRENT" in "$ROOT"/releases/*) ;; *) echo "invalid release path" >&2; exit 2 ;; esac
SHA="$(cat "$CURRENT/.serving-sha")"
[[ "$SHA" =~ ^[a-f0-9]{40}$ && "$CURRENT" == "$ROOT/releases/$SHA" ]] || exit 2
export PYTHONPATH="$CURRENT"
exec "$PYTHON" -m tools.codex_assets.knowledge_hub.mcp_http_server \
  --root "$CURRENT" --host 127.0.0.1 --port "$PORT" \
  --team --team-token-file "$TOKEN" --serving-sha "$SHA" --max-inflight 8
