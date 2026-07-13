"""Read-only local Git workspace discovery by registered remote key."""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import pathlib
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from .common import KnowledgeHubError, file_sha256, load_json, pretty_json, repository_rows
from .context import normalize_remote_key, remote_urls_from_config
from .store import RepositoryTransaction


PRUNED_DIRECTORY_NAMES = {
    ".cache",
    ".git",
    ".local",
    ".npm",
    ".repo",
    ".toolchains",
    ".venv",
    ".vscode-server",
    "__pycache__",
    "artifacts",
    "build",
    "dist",
    "downloads",
    "node_modules",
    "out",
    "output",
    "sysroot",
    "target",
}

PATH_PENALTIES = {
    "compile": 40,
    "release": 40,
    "scratch": 50,
    "old": 50,
    "dev": 20,
    "log": 20,
    "wifi": 10,
}

BUILD_ENTRY_NAMES = {
    "build.sh",
    "build.py",
    "cmakelists.txt",
    "configure",
    "cargo.toml",
    "go.mod",
    "makefile",
    "meson.build",
    "package.json",
    "pom.xml",
    "pyproject.toml",
}
TEST_ENTRY_NAMES = {
    "pytest.ini",
    "tox.ini",
    "test",
    "tests",
}
VERSION_ENTRY_NAMES = {
    "changelog.md",
    "version",
    "version.h",
    "version.txt",
}


def _git_config(repo_root: pathlib.Path) -> Optional[pathlib.Path]:
    git_entry = repo_root / ".git"
    if git_entry.is_dir():
        config = git_entry / "config"
        return config if config.is_file() else None
    if not git_entry.is_file():
        return None
    try:
        content = git_entry.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    if not content.startswith("gitdir:"):
        return None
    git_dir = pathlib.Path(content.split(":", 1)[1].strip())
    if not git_dir.is_absolute():
        git_dir = (repo_root / git_dir).resolve(strict=False)
    config = git_dir / "config"
    return config if config.is_file() else None


def _walk_repository_roots(scan_root: pathlib.Path, maximum_depth: int) -> Tuple[List[pathlib.Path], int]:
    if not scan_root.is_dir():
        return [], 1
    repositories: List[pathlib.Path] = []
    errors = 0
    stack: List[Tuple[pathlib.Path, int]] = [(scan_root, 0)]
    visited: Set[Tuple[int, int]] = set()
    while stack:
        directory, depth = stack.pop()
        try:
            stat = os.stat(str(directory), follow_symlinks=False)
        except OSError:
            errors += 1
            continue
        identity = (stat.st_dev, stat.st_ino)
        if identity in visited:
            continue
        visited.add(identity)
        if _git_config(directory):
            repositories.append(directory)
        if depth >= maximum_depth:
            continue
        try:
            entries = list(os.scandir(directory))
        except OSError:
            errors += 1
            continue
        for entry in reversed(sorted(entries, key=lambda value: value.name.lower())):
            if entry.name in PRUNED_DIRECTORY_NAMES or entry.name.startswith("."):
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    stack.append((pathlib.Path(entry.path), depth + 1))
            except OSError:
                errors += 1
    return sorted(set(repositories), key=lambda value: str(value)), errors


def _head_evidence(config: pathlib.Path) -> Dict[str, str]:
    git_dir = config.parent
    head_path = git_dir / "HEAD"
    try:
        head = head_path.read_text(encoding="ascii", errors="replace").strip()
    except OSError:
        return {"git_ref": "", "git_head": ""}
    if not head.startswith("ref:"):
        return {"git_ref": "detached", "git_head": head if len(head) == 40 else ""}
    ref = head.split(":", 1)[1].strip()
    try:
        commit = (git_dir / ref).read_text(encoding="ascii", errors="replace").strip()
    except OSError:
        commit = ""
        try:
            for line in (git_dir / "packed-refs").read_text(encoding="ascii", errors="replace").splitlines():
                if line and not line.startswith(("#", "^")):
                    value, name = line.split(" ", 1)
                    if name == ref:
                        commit = value
                        break
        except (OSError, ValueError):
            commit = ""
    return {"git_ref": ref, "git_head": commit if len(commit) == 40 else ""}


def _source_entries(repo_root: pathlib.Path) -> Dict[str, Any]:
    try:
        entries = sorted(repo_root.iterdir(), key=lambda value: value.name.lower())
    except OSError:
        entries = []
    readmes = [entry.name for entry in entries if entry.is_file() and entry.name.lower().startswith("readme")]
    build = [entry.name for entry in entries if entry.name.lower() in BUILD_ENTRY_NAMES]
    tests = [entry.name for entry in entries if entry.name.lower() in TEST_ENTRY_NAMES]
    versions = [entry.name for entry in entries if entry.name.lower() in VERSION_ENTRY_NAMES]
    config = _git_config(repo_root)
    head = _head_evidence(config) if config else {"git_ref": "", "git_head": ""}
    fingerprint_input = "\n".join(readmes + build + tests + versions + [head["git_ref"], head["git_head"]])
    return {
        "readme_entries": readmes,
        "build_entries": build,
        "test_entries": tests,
        "version_entries": versions,
        **head,
        "evidence_sha256": hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest(),
    }


def _selection_score(path: pathlib.Path, scan_roots: Sequence[pathlib.Path]) -> Tuple[int, int, str]:
    normalized = path.as_posix().lower()
    penalty = 0
    if "/work/" in normalized:
        penalty -= 20
    if "/bin/" in normalized:
        penalty -= 10
    for marker, value in PATH_PENALTIES.items():
        if marker in path.name.lower() or "/{}".format(marker) in normalized:
            penalty += value
    root_rank = next(
        (index for index, root in enumerate(scan_roots) if path == root or root in path.parents),
        len(scan_roots),
    )
    return penalty + root_rank, len(path.parts), normalized


def _registered_remote_map(root: pathlib.Path, include_external: bool) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for row in repository_rows(root):
        if not include_external and row.get("lifecycle") != "first-party":
            continue
        remote_key = normalize_remote_key(row.get("remote_key", ""))
        if remote_key:
            result[remote_key] = dict(row)
    return result


def _stable_payload(existing: Mapping[str, Any], workspaces: List[Dict[str, Any]], unmatched: List[str]) -> Dict[str, Any]:
    stable_existing = {
        "workspaces": existing.get("workspaces", []),
        "unmatched_registered_remote_keys": existing.get("unmatched_registered_remote_keys", []),
    }
    stable_next = {"workspaces": workspaces, "unmatched_registered_remote_keys": unmatched}
    generated_at = existing.get("generated_at", "") if stable_existing == stable_next else dt.date.today().isoformat()
    return {
        "schema_version": 1,
        "generated_at": generated_at or dt.date.today().isoformat(),
        "discovery_mode": "read-only-local-git-remote-match",
        "tracked": False,
        "workspaces": workspaces,
        "unmatched_registered_remote_keys": unmatched,
        "limitations_zh": "只登记当前机器实际发现且 remote key 精确匹配的仓库；绝对路径仅保存在本文件，不得复制到 tracked registry、正文或导出包。",
    }


def discover_workspaces(
    root: pathlib.Path,
    scan_roots: Sequence[pathlib.Path],
    maximum_depth: int = 12,
    include_external: bool = True,
    apply: bool = False,
) -> Dict[str, Any]:
    if maximum_depth < 1 or maximum_depth > 32:
        raise KnowledgeHubError("maximum depth must be between 1 and 32")
    resolved_roots = [path.expanduser().resolve(strict=False) for path in scan_roots]
    if not resolved_roots:
        raise KnowledgeHubError("at least one --scan-root is required")
    registered = _registered_remote_map(root, include_external=include_external)
    matches: Dict[str, List[pathlib.Path]] = defaultdict(list)
    scanned_repositories = 0
    scan_error_count = 0
    for scan_root in resolved_roots:
        repositories, errors = _walk_repository_roots(scan_root, maximum_depth)
        scan_error_count += errors
        scanned_repositories += len(repositories)
        for repo_root in repositories:
            config = _git_config(repo_root)
            remote_keys = {
                normalize_remote_key(row.get("remote_key", ""))
                for row in remote_urls_from_config(config)
            }
            for remote_key in sorted(remote_keys.intersection(registered)):
                matches[remote_key].append(repo_root)

    workspaces: List[Dict[str, Any]] = []
    duplicate_remote_keys: List[str] = []
    for remote_key, repo in sorted(registered.items(), key=lambda row: str(row[1].get("repo_id", ""))):
        candidates = sorted(set(matches.get(remote_key, [])), key=lambda value: _selection_score(value, resolved_roots))
        if not candidates:
            continue
        selected = candidates[0]
        if len(candidates) > 1:
            duplicate_remote_keys.append(remote_key)
        workspaces.append(
            {
                "workspace_ref": repo.get("workspace_ref", ""),
                "repo_id": repo.get("repo_id", ""),
                "project_id": repo.get("project_id", ""),
                "remote_key": remote_key,
                "path": str(selected),
                "present": True,
                "read_only_discovery": True,
                "source_evidence": _source_entries(selected),
                "alternate_count": max(0, len(candidates) - 1),
                "alternate_paths": [str(value) for value in candidates[1:]],
            }
        )
    unmatched = sorted(set(registered) - set(matches))
    local_path = root / "local/workspaces.json"
    existing = load_json(local_path, {}) or {}
    local_payload = _stable_payload(existing, workspaces, unmatched)
    content = pretty_json(local_payload) + "\n"
    transaction = RepositoryTransaction(root)
    transaction.add_text(
        "local/workspaces.json",
        content,
        expected_sha256=file_sha256(local_path) if local_path.exists() else "",
    )
    plan = transaction.plan()
    result: Dict[str, Any] = {
        "schema_version": 1,
        "action": "discover-local-workspaces",
        "status": "ready" if plan["changed_count"] else "no-change",
        "read_only_source_scan": True,
        "tracked_registry_written": False,
        "scan_roots": [str(value) for value in resolved_roots],
        "maximum_depth": maximum_depth,
        "registered_remote_count": len(registered),
        "scanned_repository_count": scanned_repositories,
        "matched_remote_count": len(workspaces),
        "unmatched_remote_count": len(unmatched),
        "unmatched_remote_keys": unmatched,
        "duplicate_remote_count": len(duplicate_remote_keys),
        "duplicate_remote_keys": duplicate_remote_keys,
        "scan_error_count": scan_error_count,
        "workspaces": workspaces,
        "transaction": {
            "transaction_id": plan["transaction_id"],
            "changed_count": plan["changed_count"],
            "changed_paths": [row["path"] for row in plan["writes"] if row["changed"]],
        },
    }
    if apply:
        applied = transaction.apply()
        result["status"] = applied.status
        result["transaction"].update(
            {
                "journal": applied.journal,
                "changed_paths": applied.changed_paths,
                "unchanged_paths": applied.unchanged_paths,
            }
        )
    return result
