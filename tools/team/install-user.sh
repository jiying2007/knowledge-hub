#!/usr/bin/env bash
# One-user LAN Team MCP bootstrap. This never exposes a public network listener.
set -euo pipefail
umask 077
CHECKOUT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROOT="${KH_INSTALL_ROOT:-/srv/knowledge-hub}"
VENVDIR="${KH_VENV_DIR:-$HOME/.venvs/knowledge-hub}"
TOKEN="$HOME/.config/knowledge-hub/team-token"
SERVICE_UNITS="$HOME/.config/systemd/user"
case "$ROOT" in
  /*) ;;
  *) echo "status=blocked reason=install-root-not-absolute" >&2; exit 2 ;;
esac
case "$ROOT" in *[!a-zA-Z0-9_./-]*)
  echo "status=blocked reason=unsafe-root-characters" >&2; exit 2 ;;
esac
case "$VENVDIR" in
  /*) ;;
  *) echo "status=blocked reason=venv-not-absolute" >&2; exit 2 ;;
esac
case "$VENVDIR" in *[!a-zA-Z0-9_./-]*)
  echo "status=blocked reason=unsafe-venv-characters" >&2; exit 2 ;;
esac

if ! mkdir -p "$ROOT/releases" "$ROOT/state" 2>/dev/null; then
  echo "status=blocked reason=install-root-not-writable path=$ROOT" >&2
  exit 2
fi
ROOT="$(readlink -f "$ROOT")"
mkdir -p "$HOME/.config/knowledge-hub" "$SERVICE_UNITS" "$(dirname "$VENVDIR")"
chmod 0700 "$HOME/.config/knowledge-hub"
if [[ ! -e "$TOKEN" ]]; then
  openssl rand -hex 32 > "$TOKEN"
fi
[[ -f "$TOKEN" && ! -L "$TOKEN" ]] || {
  echo "status=blocked reason=unsafe-token-file" >&2; exit 2;
}
chmod 0600 "$TOKEN"

if [[ ! -x "$VENVDIR/bin/python" ]]; then
  python3 -m venv "$VENVDIR" || {
    echo "status=blocked reason=python-venv-missing" >&2; exit 2;
  }
fi
PYTHON="$VENVDIR/bin/python"
"$PYTHON" -m pip install --disable-pip-version-check --require-hashes   -r "$CHECKOUT/requirements-runtime.lock" >/dev/null

# Keep configs per-user, and keep credential bytes outside tracked Git.
for unit in "$CHECKOUT"/tools/team/systemd/*.service "$CHECKOUT"/tools/team/systemd/*.timer; do
  out="$SERVICE_UNITS/$(basename "$unit")"
  cp "$unit" "$out"
  # Rewrite deployment root for a custom install; never change MCP bind address.
  sed -i "s#/srv/knowledge-hub#$ROOT#g" "$out"
  sed -i "s#^Environment=KH_PYTHON=/usr/bin/python3#Environment=KH_PYTHON=$PYTHON#g" "$out"
done
systemctl --user daemon-reload || {
  echo "status=blocked reason=user-systemd-unavailable" >&2; exit 2;
}
KH_INSTALL_ROOT="$ROOT" KH_PYTHON="$PYTHON" KH_TEAM_TOKEN_FILE="$TOKEN"   KH_SYSTEMCTL_MODE=user bash "$CHECKOUT/tools/team/deploy.sh"
systemctl --user enable --now knowledge-hub-team-mcp.service knowledge-hub-team-deploy.timer
if [[ -n "${KH_BACKUP_DIR:-}" ]]; then
  case "$KH_BACKUP_DIR" in
    /*) ;;
    *) echo "status=blocked reason=backup-dir-not-absolute" >&2; exit 2 ;;
  esac
  case "$KH_BACKUP_DIR" in *[!a-zA-Z0-9_./-]*)
    echo "status=blocked reason=unsafe-backup-path" >&2; exit 2 ;;
  esac
  test -d "$KH_BACKUP_DIR" || {
    echo "status=blocked reason=backup-dir-missing" >&2; exit 2;
  }
  if [[ "$(stat -c '%d' "$KH_BACKUP_DIR")" == "$(stat -c '%d' "$ROOT")" ]]; then
    echo "status=blocked reason=backup-not-independent-filesystem" >&2
    exit 2
  fi
  sed -i "s#^Environment=KH_BACKUP_DIR=#Environment=KH_BACKUP_DIR=$KH_BACKUP_DIR#"     "$SERVICE_UNITS/knowledge-hub-team-backup.service"
  systemctl --user daemon-reload
  systemctl --user enable --now knowledge-hub-team-backup.timer
fi
echo "status=installed root=$ROOT serving-sha=$(cat "$ROOT/state/serving-sha")"
