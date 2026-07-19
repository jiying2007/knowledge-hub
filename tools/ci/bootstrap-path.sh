#!/usr/bin/env bash
set -euo pipefail

# GitHub owns these variables and creates GITHUB_PATH below RUNNER_TEMP. Refuse
# local or redirected destinations so this helper cannot become a generic file
# append primitive.
if [[ -z "${GITHUB_WORKSPACE:-}" || -z "${GITHUB_PATH:-}" || -z "${RUNNER_TEMP:-}" ]]; then
  printf '%s\n' 'GitHub runner path variables are required' >&2
  exit 64
fi
if [[ "$GITHUB_PATH" != "$RUNNER_TEMP"/_runner_file_commands/* ]]; then
  printf '%s\n' 'GITHUB_PATH is outside the runner command directory' >&2
  exit 64
fi
if [[ ! -f "$GITHUB_PATH" || -L "$GITHUB_PATH" ]]; then
  printf '%s\n' 'GITHUB_PATH must be an existing regular non-symlink file' >&2
  exit 64
fi
if [[ ! -d "$GITHUB_WORKSPACE/tools/ci" || -L "$GITHUB_WORKSPACE/tools/ci" ]]; then
  printf '%s\n' 'CI transport directory is missing or unsafe' >&2
  exit 64
fi

printf '%s\n' "$GITHUB_WORKSPACE/tools/ci" >> "$GITHUB_PATH"
