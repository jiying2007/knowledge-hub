#!/usr/bin/env bash
# SHA-bound, fail-closed LAN team deployment; never pulls into serving directories.
set -euo pipefail
ROOT="$(printenv KH_INSTALL_ROOT || echo /srv/knowledge-hub)"
PYTHON="$(printenv KH_PYTHON || echo /usr/bin/python3)"
TOKEN="$(printenv KH_TEAM_TOKEN_FILE || echo /etc/knowledge-hub/team-token)"
REMOTE="$(printenv KH_REMOTE || echo https://github.com/jiying2007/knowledge-hub.git)"
REPOSITORY="$(printenv KH_REPOSITORY || echo jiying2007/knowledge-hub)"
PROBE_PORT="$(printenv KH_PROBE_PORT || echo 31317)"
LIVE_PORT="$(printenv KH_TEAM_PORT || echo 3000)"
SERVICE="$(printenv KH_SYSTEMD_SERVICE || echo knowledge-hub-team-mcp.service)"
SYSTEMCTL_MODE="$(printenv KH_SYSTEMCTL_MODE || echo user)"
if [[ "$SYSTEMCTL_MODE" == user ]]; then
  service_ctl() { systemctl --user "$@"; }
else
  service_ctl() { systemctl "$@"; }
fi
mkdir -p "$ROOT/state" "$ROOT/releases"
exec 9>"$ROOT/state/deploy.lock"
flock -n 9 || { echo "status=busy"; exit 2; }
[[ -f "$TOKEN" ]] || { echo "status=blocked reason=missing-token"; exit 2; }
MIRROR="$ROOT/source.git"
if [[ ! -d "$MIRROR" ]]; then
  git init --bare --quiet "$MIRROR"
  git --git-dir="$MIRROR" remote add origin "$REMOTE"
fi
git --git-dir="$MIRROR" fetch --no-tags --quiet origin master:refs/heads/master || {
  echo "status=offline serving-sha=$(cat "$ROOT/state/serving-sha" 2>/dev/null || true)"
  exit 2
}
SHA="$(git --git-dir="$MIRROR" rev-parse FETCH_HEAD)"
[[ "$SHA" =~ ^[a-f0-9]{40}$ ]] || exit 2
PREVIOUS=""
if [[ -L "$ROOT/current" ]]; then
  PREVIOUS="$(readlink -f "$ROOT/current")"
  case "$PREVIOUS" in "$ROOT"/releases/*) ;; *) echo "status=blocked reason=unsafe-current"; exit 2 ;; esac
  PREVIOUS="$(basename "$PREVIOUS")"
  [[ "$PREVIOUS" =~ ^[a-f0-9]{40}$ ]] || exit 2
fi
if [[ "$PREVIOUS" == "$SHA" ]]; then
  echo "status=no-change serving-sha=$SHA"
  exit 0
fi
if [[ -n "$PREVIOUS" ]]; then
  git --git-dir="$MIRROR" merge-base --is-ancestor "$PREVIOUS" "$SHA" || {
    echo "status=blocked reason=non-fast-forward"
    exit 2
  }
fi
STAGE="$(mktemp -d "$ROOT/releases/.candidate.XXXXXX")"
PID=""
cleanup() {
  if [[ -n "$PID" ]]; then kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; fi
  if [[ -d "$STAGE" ]]; then rm -rf -- "$STAGE"; fi
}
trap cleanup EXIT
git --git-dir="$MIRROR" archive "$SHA" | tar -x -C "$STAGE"
printf '%s\n' "$SHA" > "$STAGE/.serving-sha"
mkdir -p "$STAGE/.cache/knowledge-hub"
chmod 0700 "$STAGE/.cache" "$STAGE/.cache/knowledge-hub"

# A CI green from a different SHA, failed API call, or absent Signed run never deploys.
PYTHONPATH="$STAGE" "$PYTHON" -m tools.codex_assets.knowledge_hub.team_ci_gate \
  --sha "$SHA" --repository "$REPOSITORY" > "$ROOT/state/ci-candidate.json" || {
  echo "status=pending reason=exact-ci-not-ready sha=$SHA"
  exit 2
}
cd "$STAGE"
export KNOWLEDGE_PYTHON_RUNTIME="$PYTHON"
bash tools/knowledge-check.sh --dry-run --summary-json > "$ROOT/state/check-candidate.json" || {
  echo "status=blocked reason=knowledge-check sha=$SHA"
  exit 2
}
PYTHONPATH="$STAGE" "$PYTHON" -m tools.codex_assets.knowledge_hub.mcp_http_server \
  --root "$STAGE" --team --team-token-file "$TOKEN" --serving-sha "$SHA" \
  --host 127.0.0.1 --port "$PROBE_PORT" > "$ROOT/state/probe.log" 2>&1 &
PID="$!"
OK=0
for attempt in 1 2 3 4 5; do
  if PYTHONPATH="$STAGE" "$PYTHON" -m tools.codex_assets.knowledge_hub.team_smoke \
      --root "$STAGE" --serving-sha "$SHA" --token-file "$TOKEN" \
      --url "http://127.0.0.1:$PROBE_PORT/mcp" > "$ROOT/state/probe-result.json" 2>/dev/null; then
    OK=1; break
  fi
  sleep 2
done
[[ "$OK" == 1 ]] || { echo "status=blocked reason=probe-failed sha=$SHA"; exit 2; }
kill "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true
PID=""

# Canonical content and code cannot be changed by the serving process.
find "$STAGE" -path "$STAGE/.cache" -prune -o -type f -exec chmod 0444 {} +
find "$STAGE" -path "$STAGE/.cache" -prune -o -type d -exec chmod 0555 {} +
mv "$STAGE" "$ROOT/releases/$SHA"
STAGE=""
NEXT="$ROOT/.current.$SHA.$$"
ln -s "releases/$SHA" "$NEXT"
mv -Tf "$NEXT" "$ROOT/current"
LIVE_OK=0
if service_ctl restart "$SERVICE"; then
  for attempt in 1 2 3 4 5; do
    if PYTHONPATH="$ROOT/current" "$PYTHON" -m tools.codex_assets.knowledge_hub.team_smoke \
        --root "$ROOT/current" --serving-sha "$SHA" --token-file "$TOKEN" \
        --url "http://127.0.0.1:$LIVE_PORT/mcp" > "$ROOT/state/live-result.json" 2>/dev/null; then
      LIVE_OK=1; break
    fi
    sleep 2
  done
fi
if [[ "$LIVE_OK" != 1 ]]; then
  if [[ -n "$PREVIOUS" ]]; then
    ln -s "releases/$PREVIOUS" "$NEXT"
    mv -Tf "$NEXT" "$ROOT/current"
    service_ctl restart "$SERVICE" || true
  else
    service_ctl stop "$SERVICE" || true
    rm -f "$ROOT/current"
  fi
  printf '%s\n' "post-switch smoke failed: $SHA" > "$ROOT/state/last-failure"
  echo "status=rolled-back attempted-sha=$SHA previous-sha=$PREVIOUS"
  exit 2
fi
printf '%s\n' "$SHA" > "$ROOT/state/serving-sha"
printf '%s\n' "$PREVIOUS" > "$ROOT/state/last-good-sha"
rm -f "$ROOT/state/last-failure"
echo "status=deployed serving-sha=$SHA previous-sha=$PREVIOUS"
