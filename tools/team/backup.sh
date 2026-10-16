#!/usr/bin/env bash
# Weekly backup to a separately mounted filesystem and offline restore smoke.
# Does not copy the team token, derived cache, or untracked workspace material.
set -euo pipefail
ROOT="$(printenv KH_INSTALL_ROOT || echo /srv/knowledge-hub)"
BACKUP="$(printenv KH_BACKUP_DIR || true)"
[[ -n "$BACKUP" && -d "$BACKUP" && -d "$ROOT/source.git" ]] || {
  echo "status=blocked reason=backup-location-not-configured"; exit 2;
}
if [[ "$(stat -c '%d' "$BACKUP")" == "$(stat -c '%d' "$ROOT")" ]]; then
  echo "status=blocked reason=backup-not-independent-filesystem"; exit 2
fi
SHA="$(git --git-dir="$ROOT/source.git" rev-parse master)"
[[ "$SHA" =~ ^[a-f0-9]{40}$ ]] || exit 2
DATE="$(date -u +%Y%m%d)"
DEST="$BACKUP/knowledge-hub-$DATE-$SHA.bundle"
TMP="$DEST.tmp.$$"
git --git-dir="$ROOT/source.git" bundle create "$TMP" master
git --git-dir="$ROOT/source.git" bundle verify "$TMP" >/dev/null
mv -f "$TMP" "$DEST"
sha256sum "$DEST" > "$DEST.sha256"
RESTORED="$(mktemp -d)"
trap 'rm -rf -- "$RESTORED"' EXIT
git clone --quiet "$DEST" "$RESTORED/knowledge-hub"
RESTORED_SHA="$(git -C "$RESTORED/knowledge-hub" rev-parse HEAD)"
[[ "$RESTORED_SHA" == "$SHA" ]] || {
  echo "status=blocked reason=restore-revision-mismatch"; exit 2;
}
test -s "$RESTORED/knowledge-hub/registry/items.jsonl"
echo "status=pass sha=$SHA independent_bundle=$DEST"
