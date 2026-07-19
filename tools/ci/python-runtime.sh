#!/usr/bin/env bash
set -euo pipefail

# Public wrappers use one fail-closed interpreter selector. An unversioned
# python3 is accepted only when it is inside the repository's supported range;
# otherwise locally installed versioned interpreters are tried explicitly.
knowledge_ci_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
knowledge_repo_root="$(cd "$knowledge_ci_dir/../.." && pwd)"
if [[ -n "${KNOWLEDGE_PYTHON_RUNTIME:-}" ]]; then
  case "$KNOWLEDGE_PYTHON_RUNTIME" in
    /*)
      knowledge_python_candidates=("$KNOWLEDGE_PYTHON_RUNTIME")
      ;;
    *)
      printf '%s\n' 'KNOWLEDGE_PYTHON_RUNTIME must be an absolute interpreter path' >&2
      exit 69
      ;;
  esac
else
  knowledge_python_candidates=(
    "$knowledge_repo_root/.tmp/engineering/venv/bin/python"
    python3
    python3.14
    python3.13
    python3.12
    python3.11
    python3.10
  )
fi

for knowledge_python_candidate in "${knowledge_python_candidates[@]}"; do
  if ! command -v "$knowledge_python_candidate" >/dev/null 2>&1; then
    continue
  fi
  knowledge_python_version="$(
    rtk "$knowledge_python_candidate" -c \
      'import sys, yaml, jsonschema; __import__("tomli") if sys.version_info < (3, 11) else None; print("{}.{}".format(sys.version_info[0], sys.version_info[1]))' \
      2>/dev/null || true
  )"
  case "$knowledge_python_version" in
    3.10|3.11|3.12|3.13|3.14)
      exec rtk "$knowledge_python_candidate" "$@"
      ;;
  esac
done

printf '%s\n' 'Knowledge Hub requires Python 3.10 through 3.14 with locked runtime dependencies; no usable interpreter was found' >&2
exit 69
