import argparse
import json
import os
import pathlib
import stat
import sys
from collections import Counter

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]
home = pathlib.Path.home()

parser = argparse.ArgumentParser(
    description="Report-only audit for retired archive path mentions across hub, codex and runtime memory surfaces."
)
parser.add_argument(
    "--scope",
    choices=["hub", "codex", "memories", "sessions", "skills", "runtime-rules", "all"],
    default="hub",
    help="Scope to scan. all includes hub, codex, memories, sessions, runtime rules and Codex live/vendor/source skill assets.",
)
parser.add_argument("--json", action="store_true")
parser.add_argument("--max-matches", type=int, default=100)
parser.add_argument("--max-per-file", type=int, default=20)
parser.add_argument("--strict", action="store_true", help="Return non-zero when runtime route candidates are found.")
args = parser.parse_args(argv)

TERMS = [
    ("~/embedded/knowledge", "~/embedded/knowledge"),
    ("~/embedded/knowledge", str(home / "embedded" / "knowledge")),
    ("EMBEDDED_KNOWLEDGE_HOME", "EMBEDDED_KNOWLEDGE_HOME"),
    ("~/embedded/engineering_archive", "~/embedded/engineering_archive"),
    ("~/embedded/engineering_archive", str(home / "embedded" / "engineering_archive")),
    ("~/codex/docs/archive", "~/codex/docs/archive"),
    ("~/codex/docs/archive", str(home / "codex" / "docs" / "archive")),
]

CANONICAL_ROUTES = {}

DETECTOR_CONFIG_PATHS = {
    "tests/fixtures/retrieval_cases.json",
    "tools/codex_assets/knowledge_hub/check_cli.py",
    "tools/codex_assets/knowledge_hub/check_validation_pre.py",
    "tools/codex_assets/knowledge_hub/path_audit_cli.py",
    "tools/codex_assets/knowledge_hub/retrieval.py",
}

TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".conf",
    ".csv",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".rst",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
SCAN_EXCLUDED_DIRS = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tmp",
    "__pycache__",
    "build",
    "dist",
    "tmp",
}
MAX_SCAN_FILE_BYTES = 8 * 1024 * 1024
MAX_SCAN_TOTAL_BYTES = 256 * 1024 * 1024
MAX_SCAN_FILES = 50000

memory_note_dir = home / ".codex" / "memories" / "extensions" / "ad_hoc" / "notes"
memory_supersession_notes = sorted(memory_note_dir.glob("*knowledge-hub-hardcut-path-routing*.md"))
memory_supersession_note = memory_supersession_notes[-1] if memory_supersession_notes else None
memory_supersession_active = memory_supersession_note is not None


def existing_scopes():
    values = {
        "hub": root,
        "codex": home / "codex",
        "memories": home / ".codex" / "memories",
        "sessions": home / ".codex" / "sessions",
    }
    runtime_rule_values = {
        "runtime-global-agents": home / ".codex" / "AGENTS.md",
        "runtime-codex-source-agents": home / "codex" / "src" / "codex-home" / "AGENTS.md",
        "runtime-codex-repo-agents": home / "codex" / "AGENTS.md",
        "runtime-vsdata-agents": pathlib.Path("/") / "vsdata" / home.name / "AGENTS.md",
        "runtime-pcr02-app-agents": home / "work" / "sigmastar" / "pcr02_ssc305" / "SourceCode" / "sdk" / "verify" / "xcrz_sigmastar_demo" / "AGENTS.md",
        "runtime-pcr02-app-dev-agents": home / "work" / "sigmastar" / "pcr02_ssc305" / "SourceCode" / "sdk" / "verify" / "xcrz_sigmastar_demo_dev" / "AGENTS.md",
        "runtime-mcu-agents": home / "work" / "mcu" / "AGENTS.md",
        "runtime-gd32-agents": home / "work" / "mcu" / "gd32l235" / "AGENTS.md",
        "runtime-hc32-agents": home / "work" / "mcu" / "hc32f072" / "AGENTS.md",
    }
    skill_values = {
        "skills-live": home / ".codex" / "skills",
        "skills-live-vendor": home / ".codex" / "vendor" / "skills",
        "skills-codex-source": home / "codex" / "src" / "codex-home" / "vendor" / "skills",
    }
    if args.scope == "all":
        combined = {**values, **runtime_rule_values, **skill_values}
        return {key: path for key, path in combined.items() if path.exists()}
    if args.scope == "runtime-rules":
        return {key: path for key, path in runtime_rule_values.items() if path.exists()}
    if args.scope == "skills":
        return {key: path for key, path in skill_values.items() if path.exists()}
    path = values[args.scope]
    return {args.scope: path} if path.exists() else {}


def rel(path):
    try:
        if root == path or root in path.parents:
            return str(path.relative_to(root))
    except Exception:
        pass
    try:
        if home == path or home in path.parents:
            return "~/" + str(path.relative_to(home))
    except Exception:
        pass
    return str(path)


def classify(scope, rel_path, line_text):
    normalized = rel_path.replace("\\", "/")
    text = line_text.lower()
    if scope == "sessions":
        return "historical-session"
    if scope == "memories":
        return "memory-superseded" if memory_supersession_active else "runtime-route-candidate"
    if scope.startswith("runtime-"):
        return "runtime-route-candidate"
    if scope == "codex" or scope.startswith("skills-"):
        return "runtime-route-candidate"
    if normalized in DETECTOR_CONFIG_PATHS:
        return "detector-config"
    if normalized in {
        "README.md",
        "governance/path-routing.md",
        "governance/source-boundaries.md",
        "governance/source-lifecycle-policy.md",
        "registry/schema.md",
        "tools/knowledge-path-audit.sh",
        "tools/knowledge-check.sh",
    }:
        return "canonical-policy"
    if normalized.startswith("domains/codex/archive/codex-archive/"):
        return "provenance"
    if normalized.startswith("sources/") or normalized in {
        "registry/sources.json",
        "registry/retired-sources.jsonl",
    }:
        return "provenance"
    if (
        normalized.startswith("artifacts/manifests/")
        or normalized.startswith("registry/authorizations")
        or normalized.startswith("registry/automation-runs")
    ):
        return "provenance"
    if "旧" in line_text or "retired" in text or "provenance" in text or "不再作为" in line_text:
        return "canonical-policy"
    return "runtime-route-candidate"


def _candidate_files(path):
    if path.is_file():
        yield path
        return
    for directory, dirnames, filenames in os.walk(str(path), topdown=True, followlinks=False):
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in SCAN_EXCLUDED_DIRS
            and not pathlib.Path(directory, name).is_symlink()
        )
        for name in sorted(filenames):
            candidate = pathlib.Path(directory) / name
            if candidate.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                info = candidate.lstat()
            except OSError:
                continue
            if stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode):
                yield candidate


def _read_text_bounded(path):
    info = path.lstat()
    if info.st_size > MAX_SCAN_FILE_BYTES:
        raise ValueError("file exceeds scan byte budget")
    with path.open("rb") as handle:
        raw = handle.read(MAX_SCAN_FILE_BYTES + 1)
    if len(raw) > MAX_SCAN_FILE_BYTES:
        raise ValueError("file exceeds scan byte budget")
    if b"\x00" in raw:
        return ""
    return raw.decode("utf-8", errors="replace")


def scan_scope(scope, path):
    rows = []
    errors = []
    total_bytes = 0
    file_count = 0
    terms = tuple(term for _display, term in TERMS)
    try:
        candidates = _candidate_files(path)
        for file_path in candidates:
            if len(rows) >= args.max_matches:
                break
            file_count += 1
            if file_count > MAX_SCAN_FILES:
                errors.append("scan file budget exceeded")
                break
            try:
                file_size = file_path.lstat().st_size
            except OSError as exc:
                errors.append("{}: {}".format(rel(file_path), exc))
                continue
            total_bytes += file_size
            if total_bytes > MAX_SCAN_TOTAL_BYTES:
                errors.append("scan total byte budget exceeded")
                break
            try:
                text = _read_text_bounded(file_path)
            except (OSError, ValueError) as exc:
                errors.append("{}: {}".format(rel(file_path), exc))
                continue
            if not text:
                continue
            per_file = 0
            for line_no, line_text in enumerate(text.splitlines(), 1):
                if not any(term in line_text for term in terms):
                    continue
                display = rel(file_path)
                rows.append(
                    {
                        "scope": scope,
                        "path": display,
                        "line": line_no,
                        "classification": classify(scope, display, line_text),
                        "text": line_text.strip()[:240],
                    }
                )
                per_file += 1
                if per_file >= args.max_per_file or len(rows) >= args.max_matches:
                    break
    except OSError as exc:
        errors.append(str(exc))
    return rows, errors


all_rows = []
errors = []
for scope, path in existing_scopes().items():
    rows, scope_errors = scan_scope(scope, path)
    all_rows.extend(rows)
    for error in scope_errors:
        errors.append({"scope": scope, "error": error})

counts = Counter(row["classification"] for row in all_rows)
runtime_count = counts.get("runtime-route-candidate", 0)
payload = {
    "schema_version": 1,
    "read_only": True,
    "root": "~/knowledge-hub",
    "scope": args.scope,
    "searched_terms": sorted({display for display, _term in TERMS}),
    "canonical_routes": CANONICAL_ROUTES,
    "hard_cut_policy": "no alias, shim, fallback or dual route",
    "memory_supersession": {
        "active": memory_supersession_active,
        "note": rel(memory_supersession_note) if memory_supersession_note else None,
    },
    "summary": {
        "match_count": len(all_rows),
        "classification_counts": dict(sorted(counts.items())),
        "runtime_route_candidate_count": runtime_count,
        "errors": errors,
        "truncated": len(all_rows) >= args.max_matches,
    },
    "next_actions_zh": [
        "detector-config 和不可执行 provenance 命中可保留，但不得形成 alias、shim、fallback 或双路由。",
        "runtime-route-candidate 需要在对应仓库、skill、agent metadata、memory candidate 或 Codex 资产链路中修复。",
        "memory-superseded 表示旧 memory 文字已被硬切换 note 废止，不能作为当前路径路由。",
        "historical-session 只作为历史证据；当前活动 session 可能包含本次查询和工具输出，不作为路径路由。",
    ],
    "matches": all_rows,
}

if args.json:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
else:
    print("scope: {}".format(args.scope))
    print("matches: {}".format(len(all_rows)))
    print("runtime-route-candidates: {}".format(runtime_count))
    for key, value in sorted(counts.items()):
        print("- {}: {}".format(key, value))
    for row in all_rows[: min(len(all_rows), 20)]:
        print("{}: {}:{}".format(row["classification"], row["path"], row["line"]))

if errors:
    sys.exit(2)
if args.strict and runtime_count:
    sys.exit(1)
