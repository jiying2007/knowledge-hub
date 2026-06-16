#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

printf "%s\n" "knowledge-new is not enabled in bootstrap mode."
printf "%s\n" "Use templates/ manually after a reviewed implementation plan."
exit 3
