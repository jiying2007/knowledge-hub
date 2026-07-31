"""Bounded retention planning for ignored Knowledge Hub runtime artifacts."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError, read_utf8_bounded, utc_timestamp
from .search import INDEX_SCHEMA_VERSION, TOKEN_CACHE_SCHEMA_VERSION


RUNTIME_JOURNAL_MAX_BYTES = 1024 * 1024
DEFAULT_TRANSACTION_RETENTION_DAYS = 14
DEFAULT_TRANSACTION_MIN_KEEP = 20
TERMINAL_TRANSACTION_STATUSES = {"applied", "rolled-back"}
CACHE_PATTERNS: Sequence[Tuple[re.Pattern, str, int]] = (
    (
        re.compile(r"^search-index-v(?P<version>[0-9]+)(?:\.sqlite3(?:-(?:shm|wal))?|\.lock)$"),
        "search-index",
        INDEX_SCHEMA_VERSION,
    ),
    (
        re.compile(r"^search-token-cache-v(?P<version>[0-9]+)\.sqlite3(?:-(?:shm|wal))?$"),
        "search-token-cache",
        TOKEN_CACHE_SCHEMA_VERSION,
    ),
)
RUNTIME_PERMISSION_ROOTS = (".cache/knowledge-hub", ".tmp")
RUNTIME_PERMISSION_EXCLUDED_PREFIXES = (".tmp/engineering/venv",)


def runtime_maintenance_summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    protected_by_reason: Dict[str, int] = {}
    for row in payload.get("protected", []):
        if not isinstance(row, Mapping):
            continue
        reason = str(row.get("reason", "unspecified"))
        protected_by_reason[reason] = protected_by_reason.get(reason, 0) + 1
    return {
        "schema_version": 1,
        "projection": "runtime-maintenance-summary-v1",
        "action": payload.get("action", ""),
        "status": payload.get("status", "blocked"),
        "scope": payload.get("scope", ""),
        "as_of": payload.get("as_of", ""),
        "generated_at": payload.get("generated_at", ""),
        "candidate_count": payload.get(
            "candidate_count", payload.get("planned_count", 0)
        ),
        "candidate_bytes": payload.get("candidate_bytes", 0),
        "candidate_sample": [
            {
                key: row.get(key)
                for key in (
                    "path",
                    "action",
                    "artifact_kind",
                    "reason",
                    "current_mode",
                    "desired_mode",
                    "size_bytes",
                )
                if key in row
            }
            for row in payload.get("candidates", [])[:20]
            if isinstance(row, Mapping)
        ],
        "protected_count": payload.get("protected_count", 0),
        "protected_by_reason": dict(sorted(protected_by_reason.items())),
        "deleted_count": payload.get("deleted_count", 0),
        "deleted_bytes": payload.get("deleted_bytes", 0),
        "hardened_count": payload.get("hardened_count", 0),
        "error_count": payload.get("error_count", len(payload.get("errors", []))),
        "errors": list(payload.get("errors", []))[:20],
        "telemetry_pruned": payload.get(
            "telemetry_pruned",
            (payload.get("policy", {}) or {}).get("telemetry_pruned", False),
        ),
        "incomplete_transactions_pruned": payload.get(
            "incomplete_transactions_pruned",
            (payload.get("policy", {}) or {}).get(
                "incomplete_transactions_pruned", False
            ),
        ),
    }


def _relative(root: pathlib.Path, path: pathlib.Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise KnowledgeHubError("runtime artifact escapes Knowledge Hub root") from exc


def _identity(path: pathlib.Path) -> Dict[str, int]:
    file_stat = path.lstat()
    return {
        "device": int(file_stat.st_dev),
        "inode": int(file_stat.st_ino),
        "mode": int(file_stat.st_mode),
        "size": int(file_stat.st_size),
        "mtime_ns": int(file_stat.st_mtime_ns),
    }


def _cache_plan(root: pathlib.Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    cache_root = root / ".cache" / "knowledge-hub"
    candidates: List[Dict[str, Any]] = []
    protected: List[Dict[str, Any]] = []
    errors: List[str] = []
    if not cache_root.exists():
        return candidates, protected, errors
    if cache_root.is_symlink() or not cache_root.is_dir():
        return candidates, protected, ["runtime cache root must be a real directory"]
    for path in sorted(cache_root.iterdir(), key=lambda value: value.name):
        matched = False
        for pattern, artifact_kind, current_version in CACHE_PATTERNS:
            match = pattern.match(path.name)
            if not match:
                continue
            matched = True
            version = int(match.group("version"))
            try:
                file_stat = path.lstat()
            except OSError as exc:
                errors.append("unable to inspect {}: {}".format(_relative(root, path), type(exc).__name__))
                break
            if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
                errors.append("obsolete cache candidate must be a regular non-symlink file: {}".format(_relative(root, path)))
                break
            row = {
                "path": _relative(root, path),
                "artifact_kind": artifact_kind,
                "version": version,
                "current_version": current_version,
                "size_bytes": int(file_stat.st_size),
                "identity": _identity(path),
            }
            if version == current_version:
                row["reason"] = "current-schema-version"
                protected.append(row)
            elif version < current_version:
                row["reason"] = "obsolete-schema-version"
                candidates.append(row)
            else:
                row["reason"] = "future-schema-version-protected"
                protected.append(row)
            break
        if matched:
            continue
    return candidates, protected, errors


def _parse_terminal_date(payload: Mapping[str, Any]) -> dt.date:
    raw = str(payload.get("completed_at") or payload.get("rollback_at") or "")
    if not raw:
        raise KnowledgeHubError("terminal transaction journal is missing completion time")
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError as exc:
        raise KnowledgeHubError("terminal transaction journal has invalid completion time") from exc


def _tree_snapshot(path: pathlib.Path) -> Tuple[int, str]:
    digest = hashlib.sha256()
    total_bytes = 0
    stack = [path]
    while stack:
        current = stack.pop()
        current_stat = current.lstat()
        relative = current.relative_to(path).as_posix() if current != path else "."
        if stat.S_ISLNK(current_stat.st_mode):
            raise KnowledgeHubError("runtime transaction tree must not contain symlinks")
        if stat.S_ISDIR(current_stat.st_mode):
            digest.update("D\0{}\0{}\0{}\n".format(relative, current_stat.st_mode, current_stat.st_mtime_ns).encode("utf-8"))
            children = sorted(current.iterdir(), key=lambda value: value.name, reverse=True)
            stack.extend(children)
            continue
        if not stat.S_ISREG(current_stat.st_mode):
            raise KnowledgeHubError("runtime transaction tree contains a special file")
        total_bytes += int(current_stat.st_size)
        digest.update(
            "F\0{}\0{}\0{}\0{}\n".format(
                relative,
                current_stat.st_mode,
                current_stat.st_size,
                current_stat.st_mtime_ns,
            ).encode("utf-8")
        )
    return total_bytes, digest.hexdigest()


def _transaction_plan(
    root: pathlib.Path,
    today: dt.date,
    retention_days: int,
    minimum_keep: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    transaction_root = root / ".tmp" / "transactions"
    candidates: List[Dict[str, Any]] = []
    protected: List[Dict[str, Any]] = []
    errors: List[str] = []
    if not transaction_root.exists():
        return candidates, protected, errors
    if transaction_root.is_symlink() or not transaction_root.is_dir():
        return candidates, protected, ["transaction root must be a real directory"]
    terminal: List[Tuple[dt.date, pathlib.Path, Mapping[str, Any]]] = []
    for path in sorted(transaction_root.iterdir(), key=lambda value: value.name):
        if path.is_symlink() or not path.is_dir():
            errors.append("transaction entry must be a real directory: {}".format(_relative(root, path)))
            continue
        journal = path / "journal.json"
        if not journal.exists():
            protected.append({"path": _relative(root, path), "reason": "journal-missing-protected"})
            continue
        try:
            payload = json.loads(
                read_utf8_bounded(journal, RUNTIME_JOURNAL_MAX_BYTES, "transaction journal")
            )
            if not isinstance(payload, dict):
                raise KnowledgeHubError("transaction journal root must be an object")
        except (KnowledgeHubError, json.JSONDecodeError) as exc:
            errors.append("invalid transaction journal {}: {}".format(_relative(root, journal), str(exc)))
            continue
        status = str(payload.get("status", ""))
        if status not in TERMINAL_TRANSACTION_STATUSES:
            protected.append(
                {"path": _relative(root, path), "reason": "non-terminal-transaction", "status": status}
            )
            continue
        try:
            terminal_date = _parse_terminal_date(payload)
        except KnowledgeHubError as exc:
            errors.append("{}: {}".format(_relative(root, journal), str(exc)))
            continue
        terminal.append((terminal_date, path, payload))

    terminal.sort(key=lambda value: (value[0], value[1].name), reverse=True)
    for position, (terminal_date, path, payload) in enumerate(terminal):
        age_days = (today - terminal_date).days
        base = {
            "path": _relative(root, path),
            "status": str(payload.get("status", "")),
            "completed_date": terminal_date.isoformat(),
            "age_days": age_days,
        }
        if position < minimum_keep:
            protected.append(dict(base, reason="minimum-newest-retention"))
            continue
        if age_days < retention_days:
            protected.append(dict(base, reason="within-retention-window"))
            continue
        try:
            size_bytes, fingerprint = _tree_snapshot(path)
        except (KnowledgeHubError, OSError) as exc:
            errors.append("unsafe transaction tree {}: {}".format(_relative(root, path), str(exc)))
            continue
        candidates.append(
            dict(
                base,
                reason="terminal-transaction-retention-expired",
                size_bytes=size_bytes,
                tree_fingerprint=fingerprint,
                identity=_identity(path),
            )
        )
    return candidates, protected, errors


def _permission_plan(
    root: pathlib.Path, excluded_delete_paths: Sequence[str]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    candidates: List[Dict[str, Any]] = []
    errors: List[str] = []

    def excluded(relative: str) -> bool:
        explicitly_deleted = any(
            relative == delete_path or relative.startswith(delete_path.rstrip("/") + "/")
            for delete_path in excluded_delete_paths
        )
        managed_runtime = any(
            relative == prefix or relative.startswith(prefix.rstrip("/") + "/")
            for prefix in RUNTIME_PERMISSION_EXCLUDED_PREFIXES
        )
        return explicitly_deleted or managed_runtime

    for relative_root in RUNTIME_PERMISSION_ROOTS:
        runtime_root = root / relative_root
        if not runtime_root.exists():
            continue
        stack = [runtime_root]
        while stack:
            path = stack.pop()
            relative = _relative(root, path)
            if excluded(relative):
                continue
            try:
                path_stat = path.lstat()
            except OSError as exc:
                errors.append("unable to inspect runtime permission path {}: {}".format(relative, type(exc).__name__))
                continue
            if stat.S_ISLNK(path_stat.st_mode):
                errors.append("runtime permission tree must not contain symlinks: {}".format(relative))
                continue
            if stat.S_ISDIR(path_stat.st_mode):
                desired_mode = 0o700
                try:
                    stack.extend(sorted(path.iterdir(), key=lambda value: value.name, reverse=True))
                except OSError as exc:
                    errors.append("unable to enumerate runtime directory {}: {}".format(relative, type(exc).__name__))
                    continue
            elif stat.S_ISREG(path_stat.st_mode):
                desired_mode = 0o600
            else:
                errors.append("runtime permission tree contains a special file: {}".format(relative))
                continue
            current_mode = stat.S_IMODE(path_stat.st_mode)
            if current_mode == desired_mode:
                continue
            candidates.append(
                {
                    "path": relative,
                    "action": "chmod",
                    "artifact_kind": "runtime-permission",
                    "reason": "runtime-permission-hardening",
                    "current_mode": "{:04o}".format(current_mode),
                    "desired_mode": "{:04o}".format(desired_mode),
                    "size_bytes": 0,
                    "identity": _identity(path),
                }
            )
    return candidates, errors


def plan_runtime_maintenance(
    root: pathlib.Path,
    today: dt.date,
    scope: str = "all",
    transaction_retention_days: int = DEFAULT_TRANSACTION_RETENTION_DAYS,
    transaction_min_keep: int = DEFAULT_TRANSACTION_MIN_KEEP,
) -> Dict[str, Any]:
    if scope not in {
        "all",
        "obsolete-search-index",
        "terminal-transactions",
        "runtime-permissions",
    }:
        raise KnowledgeHubError("invalid runtime maintenance scope: {}".format(scope))
    if transaction_retention_days < 1 or transaction_retention_days > 3650:
        raise KnowledgeHubError("transaction retention days must be between 1 and 3650")
    if transaction_min_keep < 1 or transaction_min_keep > 10000:
        raise KnowledgeHubError("transaction minimum keep must be between 1 and 10000")
    root = root.resolve()
    candidates: List[Dict[str, Any]] = []
    protected: List[Dict[str, Any]] = []
    errors: List[str] = []
    if scope in {"all", "obsolete-search-index"}:
        found, retained, found_errors = _cache_plan(root)
        candidates.extend(found)
        protected.extend(retained)
        errors.extend(found_errors)
    if scope in {"all", "terminal-transactions"}:
        found, retained, found_errors = _transaction_plan(
            root, today, transaction_retention_days, transaction_min_keep
        )
        candidates.extend(found)
        protected.extend(retained)
        errors.extend(found_errors)
    for row in candidates:
        row.setdefault("action", "delete")
    if scope in {"all", "runtime-permissions"}:
        permission_candidates, permission_errors = _permission_plan(
            root,
            [str(row["path"]) for row in candidates if row.get("action") == "delete"],
        )
        candidates.extend(permission_candidates)
        errors.extend(permission_errors)
    candidates.sort(key=lambda row: str(row["path"]))
    protected.sort(key=lambda row: str(row["path"]))
    return {
        "schema_version": 1,
        "action": "runtime-maintenance-plan",
        "status": "blocked" if errors else "ready",
        "read_only": True,
        "tracked_files_written": False,
        "scope": scope,
        "as_of": today.isoformat(),
        "generated_at": utc_timestamp(),
        "policy": {
            "current_search_index_version": INDEX_SCHEMA_VERSION,
            "current_token_cache_version": TOKEN_CACHE_SCHEMA_VERSION,
            "transaction_retention_days": transaction_retention_days,
            "transaction_minimum_newest_keep": transaction_min_keep,
            "telemetry_pruned": False,
            "incomplete_transactions_pruned": False,
        },
        "candidate_count": len(candidates),
        "candidate_bytes": sum(
            int(row.get("size_bytes", 0))
            for row in candidates
            if row.get("action") == "delete"
        ),
        "candidates": candidates,
        "protected_count": len(protected),
        "protected": protected,
        "error_count": len(errors),
        "errors": errors,
    }


def _same_identity(path: pathlib.Path, expected: Mapping[str, Any]) -> bool:
    try:
        actual = _identity(path)
    except OSError:
        return False
    return all(int(actual[field]) == int(expected[field]) for field in actual)


def _fchmod_identity_safe(
    path: pathlib.Path,
    expected: Mapping[str, Any],
    desired_mode: int,
) -> None:
    expected_mode = int(expected["mode"])
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    if stat.S_ISDIR(expected_mode):
        flags |= getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(str(path), flags)
    try:
        opened = os.fstat(descriptor)
        actual = {
            "device": int(opened.st_dev),
            "inode": int(opened.st_ino),
            "mode": int(opened.st_mode),
            "size": int(opened.st_size),
            "mtime_ns": int(opened.st_mtime_ns),
        }
        if not all(int(actual[field]) == int(expected[field]) for field in actual):
            raise KnowledgeHubError("runtime permission target changed after planning")
        if not (stat.S_ISDIR(opened.st_mode) or stat.S_ISREG(opened.st_mode)):
            raise KnowledgeHubError("runtime permission target changed type")
        os.fchmod(descriptor, desired_mode)
    finally:
        os.close(descriptor)


def _delete_tree(path: pathlib.Path) -> None:
    path_stat = path.lstat()
    if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISDIR(path_stat.st_mode):
        raise KnowledgeHubError("runtime transaction delete target changed type")
    if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
        raise KnowledgeHubError("platform lacks symlink-safe directory removal")
    shutil.rmtree(path)


def apply_runtime_maintenance(
    root: pathlib.Path,
    today: dt.date,
    scope: str = "all",
    transaction_retention_days: int = DEFAULT_TRANSACTION_RETENTION_DAYS,
    transaction_min_keep: int = DEFAULT_TRANSACTION_MIN_KEEP,
) -> Dict[str, Any]:
    plan = plan_runtime_maintenance(
        root,
        today,
        scope=scope,
        transaction_retention_days=transaction_retention_days,
        transaction_min_keep=transaction_min_keep,
    )
    if plan["status"] != "ready":
        raise KnowledgeHubError("runtime maintenance plan is blocked")
    root = root.resolve()
    deleted: List[Dict[str, Any]] = []
    hardened: List[Dict[str, Any]] = []
    errors: List[str] = []
    for row in plan["candidates"]:
        path = root / str(row["path"])
        try:
            if row.get("action") == "chmod":
                desired_mode = int(str(row["desired_mode"]), 8)
                _fchmod_identity_safe(path, row["identity"], desired_mode)
                hardened.append(
                    {
                        "path": row["path"],
                        "from_mode": row["current_mode"],
                        "to_mode": row["desired_mode"],
                    }
                )
            else:
                if not _same_identity(path, row["identity"]):
                    raise KnowledgeHubError("runtime artifact changed after planning")
            if row.get("action") != "chmod" and row.get("tree_fingerprint"):
                _, fingerprint = _tree_snapshot(path)
                if fingerprint != row["tree_fingerprint"]:
                    raise KnowledgeHubError("runtime transaction tree changed after planning")
                _delete_tree(path)
            elif row.get("action") != "chmod":
                file_stat = path.lstat()
                if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
                    raise KnowledgeHubError("cache candidate is no longer a regular file")
                path.unlink()
            if row.get("action") != "chmod":
                deleted.append(
                    {
                        "path": row["path"],
                        "reason": row["reason"],
                        "size_bytes": row.get("size_bytes", 0),
                    }
                )
        except (KnowledgeHubError, OSError) as exc:
            errors.append("{}: {}".format(row["path"], str(exc)))
            break
    return {
        "schema_version": 1,
        "action": "runtime-maintenance-apply",
        "status": "applied" if not errors else "partial-failure",
        "read_only": False,
        "tracked_files_written": False,
        "scope": scope,
        "as_of": today.isoformat(),
        "generated_at": utc_timestamp(),
        "planned_count": plan["candidate_count"],
        "deleted_count": len(deleted),
        "deleted_bytes": sum(int(row["size_bytes"]) for row in deleted),
        "deleted": deleted,
        "hardened_count": len(hardened),
        "hardened": hardened,
        "errors": errors,
        "telemetry_pruned": False,
        "incomplete_transactions_pruned": False,
    }
