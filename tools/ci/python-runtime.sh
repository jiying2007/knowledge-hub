#!/usr/bin/env bash
set -euo pipefail

# Public wrappers use one fail-closed, capability-based interpreter selector.
# Prefer the host's unversioned python3 when it can load the runtime stack,
# then fall back to the repository environment and versioned interpreters.
# Dependency discovery deliberately uses find_spec instead of importing the
# runtime stack: the selected command performs the real imports, while the
# selector avoids paying the PyYAML/jsonschema startup cost twice per CLI call.
knowledge_ci_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
knowledge_repo_root="$(cd "$knowledge_ci_dir/../.." && pwd)"
knowledge_runtime_lock="$knowledge_repo_root/requirements-runtime.lock"
knowledge_runtime_cache_dir="$knowledge_repo_root/.cache/knowledge-hub"
knowledge_runtime_cache="$knowledge_runtime_cache_dir/python-runtime-selection-v1"
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
    python3
    "$knowledge_repo_root/.tmp/engineering/venv/bin/python"
    python3.14
    python3.13
    python3.12
    python3.11
    python3.10
    python3.9
    python3.8
  )
fi

knowledge_cache_eligible=false
if [[ "${1:-}" == "-m" && "${2:-}" == tools.codex_assets.knowledge_hub.* ]]; then
  knowledge_cache_eligible=true
fi

# Public Hub modules import the runtime stack themselves. After one complete
# selector validation, reuse only the same allowed interpreter while the
# selector, runtime lock and interpreter remain older than the private cache.
# This removes the second Python startup from warm CLI calls without turning
# the cache into an authority source or weakening first-use validation.
if [[ "$knowledge_cache_eligible" == true
      && -f "$knowledge_runtime_cache"
      && ! -L "$knowledge_runtime_cache"
      && -O "$knowledge_runtime_cache" ]]; then
  mapfile -t knowledge_cached_runtime < "$knowledge_runtime_cache"
  if [[ "${#knowledge_cached_runtime[@]}" -eq 2 ]]; then
    knowledge_cached_python="${knowledge_cached_runtime[0]}"
    knowledge_cached_version="${knowledge_cached_runtime[1]}"
    knowledge_cached_allowed=false
    for knowledge_python_candidate in "${knowledge_python_candidates[@]}"; do
      knowledge_python_resolved="$(command -v "$knowledge_python_candidate" 2>/dev/null || true)"
      if [[ -n "$knowledge_python_resolved"
            && "$knowledge_python_resolved" == "$knowledge_cached_python" ]]; then
        knowledge_cached_allowed=true
        break
      fi
    done
    if [[ "$knowledge_cached_version" =~ ^3\.[0-9]+$
          && "$knowledge_cached_allowed" == true
          && "$knowledge_cached_python" == /*
          && -x "$knowledge_cached_python"
          && "$knowledge_runtime_cache" -nt "$knowledge_cached_python"
          && "$knowledge_runtime_cache" -nt "$knowledge_runtime_lock"
          && "$knowledge_runtime_cache" -nt "${BASH_SOURCE[0]}" ]]; then
      exec rtk "$knowledge_cached_python" "$@"
    fi
  fi
fi

for knowledge_python_candidate in "${knowledge_python_candidates[@]}"; do
  knowledge_python_resolved="$(command -v "$knowledge_python_candidate" 2>/dev/null || true)"
  if [[ -z "$knowledge_python_resolved" ]]; then
    continue
  fi
  knowledge_python_version="$(
    rtk "$knowledge_python_resolved" -c \
      'import importlib.util, sys; required = ("yaml", "jsonschema") + (("tomli",) if sys.version_info < (3, 11) else ()); missing = [name for name in required if importlib.util.find_spec(name) is None]; sys.exit(1) if missing else print("{}.{}".format(sys.version_info[0], sys.version_info[1]))' \
      2>/dev/null || true
  )"
  if [[ "$knowledge_python_version" =~ ^3\.[0-9]+$ ]]; then
    if [[ "$knowledge_cache_eligible" == true ]] \
      && rtk mkdir -p "$knowledge_runtime_cache_dir" 2>/dev/null; then
      umask 077
      knowledge_runtime_cache_tmp="$knowledge_runtime_cache.${BASHPID}.tmp"
      if printf '%s\n%s\n' \
        "$knowledge_python_resolved" \
        "$knowledge_python_version" > "$knowledge_runtime_cache_tmp"; then
        rtk mv -f "$knowledge_runtime_cache_tmp" "$knowledge_runtime_cache" \
          2>/dev/null || true
      fi
    fi
    exec rtk "$knowledge_python_resolved" "$@"
  fi
done

printf '%s\n' 'Knowledge Hub requires a usable Python 3 interpreter with yaml, jsonschema and (before Python 3.11) tomli; no capable interpreter was found' >&2
exit 69
