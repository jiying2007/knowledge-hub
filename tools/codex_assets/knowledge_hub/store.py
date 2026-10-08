"""Transactional tracked-file updates for Knowledge Hub.

The transaction is recoverable rather than pretending a group of filesystem
renames is globally atomic. A write-ahead journal and per-file backups make a
partial process interruption deterministic to inspect and roll back.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import pathlib
import shutil
import uuid
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Mapping, Set

from .common import (
    KnowledgeHubError,
    bytes_sha256,
    ensure_private_directory,
    ensure_private_directory_tree,
    ensure_private_file,
    file_sha256,
    normalize_relpath,
    pretty_json,
    resolve_inside,
    utc_timestamp,
)


def _fsync_directory(path: pathlib.Path) -> None:
    descriptor = os.open(str(path), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class WriteConflict(KnowledgeHubError):
    """A pre-write contention conflict that can safely be replanned."""


@dataclass
class PlannedWrite:
    path: str
    content: bytes
    expected_sha256: str = ""
    expected_missing: bool = False


@dataclass
class TransactionResult:
    transaction_id: str
    status: str
    changed_paths: List[str]
    unchanged_paths: List[str]
    journal: str
    rolled_back: bool = False
    diagnostics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "status": self.status,
            "changed_paths": self.changed_paths,
            "unchanged_paths": self.unchanged_paths,
            "journal": self.journal,
            "rolled_back": self.rolled_back,
            "diagnostics": self.diagnostics,
        }


class RepositoryTransaction:
    def __init__(self, root: pathlib.Path, transaction_id: str = "", expected_inputs=None) -> None:
        self.root = root.resolve()
        self.transaction_id = transaction_id or "kh-{}-{}".format(utc_timestamp().replace(":", "").replace("-", ""), uuid.uuid4().hex[:8])
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}", self.transaction_id) or self.transaction_id in {'.', '..'}:
            raise KnowledgeHubError("transaction identity is invalid")
        self.writes: Dict[str, PlannedWrite] = {}
        self.expected_inputs = dict(expected_inputs) if expected_inputs is not None else None
        self.runtime_root = self.root / ".tmp" / "transactions" / self.transaction_id
        self.stage_root = self.runtime_root / "stage"
        self.backup_root = self.runtime_root / "before"
        self.journal_path = self.runtime_root / "journal.json"
        self.lock_path = self.root / ".tmp" / "locks" / "knowledge-hub.lock"

    def add_text(self, relative: str, content: str, expected_sha256: str = "") -> None:
        self.add_bytes(relative, content.encode("utf-8"), expected_sha256=expected_sha256)

    def add_bytes(self, relative: str, content: bytes, expected_sha256: str = "") -> None:
        safe = normalize_relpath(relative)
        if expected_sha256 and not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            raise KnowledgeHubError("expected SHA256 must have 64 hexadecimal characters: {}".format(safe))
        missing = self.expected_inputs is not None and safe not in self.expected_inputs
        if self.expected_inputs is not None:
            expected_sha256 = self.expected_inputs.get(safe, "")
        self.writes[safe] = PlannedWrite(safe, content, expected_sha256, missing)

    def plan(self) -> Dict[str, Any]:
        rows = []
        for relative in sorted(self.writes):
            write = self.writes[relative]
            target = resolve_inside(self.root, relative)
            before_hash = file_sha256(target) if target.exists() else ""
            after_hash = bytes_sha256(write.content)
            rows.append(
                {
                    "path": relative,
                    "exists_before": target.exists(),
                    "before_sha256": before_hash,
                    "after_sha256": after_hash,
                    "changed": before_hash != after_hash,
                    "expected_sha256": write.expected_sha256,
                }
            )
        return {
            "transaction_id": self.transaction_id,
            "read_only": True,
            "write_count": len(rows),
            "changed_count": sum(1 for row in rows if row["changed"]),
            "writes": rows,
        }

    @contextlib.contextmanager
    def _lock(self) -> Iterator[None]:
        ensure_private_directory(self.root / ".tmp")
        ensure_private_directory(self.lock_path.parent)
        if self.lock_path.is_symlink():
            raise KnowledgeHubError("transaction lock must not be a symlink")
        with self.lock_path.open("a+") as handle:
            os.chmod(str(self.lock_path), 0o600)
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise WriteConflict("another Knowledge Hub write transaction is active") from exc
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _write_journal(self, payload: Mapping[str, Any]) -> None:
        ensure_private_directory(self.root / ".tmp")
        ensure_private_directory(self.root / ".tmp" / "transactions")
        ensure_private_directory(self.runtime_root)
        temporary = self.journal_path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            os.chmod(str(temporary), 0o600)
            handle.write(pretty_json(dict(payload)) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(self.journal_path))
        ensure_private_file(self.journal_path)
        _fsync_directory(self.journal_path.parent)

    def _stage(self, changed: List[Dict[str, Any]]) -> None:
        for row in changed:
            relative = row["path"]
            target = resolve_inside(self.root, relative)
            staged = self.stage_root / relative
            backup = self.backup_root / relative
            ensure_private_directory(self.stage_root)
            ensure_private_directory_tree(self.stage_root, staged.parent)
            with staged.open("wb") as handle:
                os.chmod(str(staged), 0o600)
                handle.write(self.writes[relative].content)
                handle.flush()
                os.fsync(handle.fileno())
            if target.exists():
                ensure_private_directory(self.backup_root)
                ensure_private_directory_tree(self.backup_root, backup.parent)
                shutil.copy2(str(target), str(backup))
                ensure_private_file(backup)
                with backup.open("rb") as handle:
                    os.fsync(handle.fileno())
                _fsync_directory(backup.parent)

    def apply(self) -> TransactionResult:
        plan = self.plan()
        changed = [row for row in plan["writes"] if row["changed"]]
        unchanged = [row["path"] for row in plan["writes"] if not row["changed"]]
        with self._lock():
            self._verify_inputs()
            # Re-evaluate all preconditions after acquiring the single-writer lock.
            for row in changed:
                relative = row["path"]
                target = resolve_inside(self.root, relative)
                current_hash = file_sha256(target) if target.exists() else ""
                expected = self.writes[relative].expected_sha256
                if expected and current_hash != expected:
                    raise WriteConflict(
                        "optimistic write precondition failed for {}: expected {} actual {}".format(
                            relative, expected, current_hash or "<missing>"
                        )
                    )
                if current_hash != row["before_sha256"]:
                    raise WriteConflict("input changed after planning: {}".format(relative))

            if not changed:
                return TransactionResult(self.transaction_id, "no-change", [], unchanged, "")

            self._stage(changed)
            journal: Dict[str, Any] = {
                "schema_version": 1,
                "transaction_id": self.transaction_id,
                "status": "staged",
                "created_at": utc_timestamp(),
                "root": "~/knowledge-hub",
                "writes": changed,
                "applied_paths": [],
                "rollback_paths": [],
            }
            self._write_journal(journal)
            try:
                journal["status"] = "applying"
                self._write_journal(journal)
                for row in changed:
                    relative = row["path"]
                    target = resolve_inside(self.root, relative)
                    staged = self.stage_root / relative
                    journal["pending_path"] = relative
                    self._write_journal(journal)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(str(staged), str(target))
                    _fsync_directory(target.parent)
                    journal["applied_paths"].append(relative)
                    journal["pending_path"] = ""
                    self._write_journal(journal)
                journal["status"] = "applied"
                journal["completed_at"] = utc_timestamp()
                self._write_journal(journal)
            except BaseException as exc:
                diagnostics = ["apply failed: {}".format(exc)]
                self._rollback_locked(journal, diagnostics)
                raise KnowledgeHubError("transaction {} failed; recovery status {}: {}".format(self.transaction_id, journal["status"], exc)) from exc

        return TransactionResult(
            self.transaction_id,
            "applied",
            [row["path"] for row in changed],
            unchanged,
            str(self.journal_path.relative_to(self.root)),
        )

    def _rollback_locked(self, journal: Dict[str, Any], diagnostics: List[str]) -> None:
        states = reconcile_writes(self.root, self.runtime_root, journal)
        applied = [row["path"] for row in states if row["state"] == "after"]
        conflicts = [row["path"] for row in states if row["state"] in {"conflict", "backup-invalid"}]
        journal["applied_paths"] = list(dict.fromkeys(list(journal.get("applied_paths", [])) + applied))
        for relative in reversed(applied):
            target = resolve_inside(self.root, relative)
            backup = self.backup_root / relative
            try:
                if backup.exists():
                    temporary = target.with_name(target.name + ".kh-rollback")
                    shutil.copy2(str(backup), str(temporary))
                    os.replace(str(temporary), str(target))
                    _fsync_directory(target.parent)
                elif target.exists():
                    target.unlink()
                    _fsync_directory(target.parent)
                journal.setdefault("rollback_paths", []).append(relative)
            except OSError as exc:
                diagnostics.append("rollback failed for {}: {}".format(relative, exc))
        diagnostics.extend("recovery conflict: {}".format(path) for path in conflicts)
        journal["status"] = "rollback-incomplete" if conflicts or len(journal.get("rollback_paths", [])) != len(journal.get("applied_paths", [])) else "rolled-back"
        journal["rollback_at"] = utc_timestamp()
        journal["diagnostics"] = diagnostics
        self._write_journal(journal)

    def _verify_inputs(self) -> None:
        for relative, write in self.writes.items():
            if write.expected_missing and resolve_inside(self.root, relative).exists():
                raise WriteConflict("expected new target is no longer missing: {}".format(relative))
        for relative, expected in (self.expected_inputs or {}).items():
            target = resolve_inside(self.root, relative)
            actual = file_sha256(target) if target.exists() else ""
            if actual != expected:
                raise WriteConflict("read snapshot changed before commit: {}".format(relative))


def snapshot_inputs(root: pathlib.Path) -> Dict[str, str]:
    """Bind lifecycle preparation to its original registry, views and body bytes."""
    from .common import registry_items, iter_text_files

    # Producers also rewrite project entries that are not yet registered.
    # Capture these before reading; an absent target must really have been absent.
    paths: Set[pathlib.Path] = set(iter_text_files(root))
    for directory in ("registry", "indexes"):
        paths.update(path for path in (root / directory).rglob("*") if path.is_file())
    result = {str(path.relative_to(root)): file_sha256(path) for path in sorted(paths)}
    for item in registry_items(root):
        relative = str(item.get("path", ""))
        if relative:
            target = resolve_inside(root, relative)
            if target.is_file():
                result[relative] = file_sha256(target)
    return result


def validate_journal(journal):
    """Reject malformed recovery material before paths or rows are consumed."""
    if not isinstance(journal, dict):
        raise KnowledgeHubError("journal must be an object")
    if not isinstance(journal.get("status"), str) or journal["status"] not in {"staged", "applying", "applied", "rolled-back", "rollback-incomplete"}:
        raise KnowledgeHubError("journal status is invalid")
    writes = journal.get("writes")
    if not isinstance(writes, list) or len(writes) > 10000:
        raise KnowledgeHubError("journal writes must be a bounded array")
    paths = set()
    for write in writes:
        if not isinstance(write, dict) or not isinstance(write.get("path"), str):
            raise KnowledgeHubError("journal write must be an object with a path")
        path = normalize_relpath(write["path"])
        if path in paths:
            raise KnowledgeHubError("journal contains duplicate write paths")
        paths.add(path)
        # Older journals without hashes are inspectable but cannot prove recovery.
        for key in ("before_sha256", "after_sha256"):
            value = write.get(key)
            if value is not None and (not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}|", value)):
                raise KnowledgeHubError("journal hash is invalid")
        if "exists_before" in write and type(write["exists_before"]) is not bool:
            raise KnowledgeHubError("journal exists_before must be boolean")
    for key in ("applied_paths", "rollback_paths"):
        values = journal.get(key, [])
        if not isinstance(values, list) or any(not isinstance(v, str) or v not in paths for v in values):
            raise KnowledgeHubError("journal path list is invalid")
    if not isinstance(journal.get("pending_path", ""), str):
        raise KnowledgeHubError('journal pending path must be a string')
    if journal.get("pending_path", "") and journal["pending_path"] not in paths:
        raise KnowledgeHubError("journal pending path is outside writes")
    if not set(journal.get('rollback_paths', [])) <= set(journal.get('applied_paths', [])):
        raise KnowledgeHubError('journal rollback paths are outside applied paths')
    if 'schema_version' in journal and (type(journal['schema_version']) is not int or journal['schema_version'] != 1):
        raise KnowledgeHubError('journal schema version is unsupported')


def _read_journal(path):
    if path.is_symlink() or path.stat().st_size > 8 * 1024 * 1024:
        raise KnowledgeHubError("journal must be bounded and non-symlink")
    journal = json.loads(path.read_text(encoding="utf-8"))
    validate_journal(journal)
    return journal


def reconcile_writes(root, runtime_root, journal):
    """Classify all intended writes, including a replace not yet marked applied."""
    validate_journal(journal)
    rows = []
    for write in journal.get("writes", []):
        relative = write.get("path", "")
        target = resolve_inside(root, relative)
        actual = file_sha256(target) if target.exists() else ""
        before, after = write.get("before_sha256"), write.get("after_sha256")
        if before is None or after is None:
            state = "after" if relative in journal.get("applied_paths", []) else "unknown"
        else:
            state = "before" if actual == before else "after" if actual == after else "conflict"
        backup = runtime_root / "before" / relative
        if state == "after" and write.get("exists_before") is True:
            if not backup.is_file() or file_sha256(backup) != before:
                state = "backup-invalid"
        rows.append({"path":relative, "state":state, "actual_sha256":actual})
    return rows


def incomplete_transactions(root: pathlib.Path) -> List[Dict[str, Any]]:
    transaction_root = root / ".tmp" / "transactions"
    rows: List[Dict[str, Any]] = []
    if not transaction_root.exists():
        return rows
    for journal_path in sorted(transaction_root.glob("*/journal.json")):
        try:
            journal = _read_journal(journal_path)
        except (OSError, ValueError, KnowledgeHubError):
            rows.append({"journal": str(journal_path), "status": "invalid-journal"})
            continue
        if journal.get("status") not in {"applied", "rolled-back"}:
            row = dict(journal)
            row["journal"] = str(journal_path.relative_to(root))
            rows.append(row)
    return rows


def audit_transactions(root: pathlib.Path, transaction_id: str = "") -> Dict[str, Any]:
    """Inspect journals and recovery material without mutating repository files."""

    transaction_root = root / ".tmp" / "transactions"
    rows: List[Dict[str, Any]] = []
    if transaction_root.exists():
        journal_paths = sorted(transaction_root.glob("*/journal.json"))
        for journal_path in journal_paths:
            if transaction_id and journal_path.parent.name != transaction_id:
                continue
            try:
                journal = _read_journal(journal_path)
            except (OSError, ValueError, KnowledgeHubError) as exc:
                rows.append(
                    {
                        "transaction_id": journal_path.parent.name,
                        "status": "invalid-journal",
                        "journal": str(journal_path.relative_to(root)),
                        "errors": [str(exc)],
                        "recoverable": False,
                        "requires_attention": True,
                        "recovery_action": "inspect journal and before/ directory manually; do not overwrite tracked files",
                    }
                )
                continue
            status = str(journal.get("status", "unknown"))
            reconciliation = (reconcile_writes(root, journal_path.parent, journal)
                              if status not in {"applied", "rolled-back"} else [])
            applied = list(dict.fromkeys([str(value) for value in journal.get("applied_paths", [])]
                                        + [row["path"] for row in reconciliation if row["state"] == "after"]))
            write_paths = [str(value.get("path", "")) for value in journal.get("writes", []) if isinstance(value, dict)]
            backup_present = []
            backup_missing = []
            for relative in applied:
                backup = journal_path.parent / "before" / relative
                if backup.exists():
                    backup_present.append(relative)
                elif not any(write.get("path") == relative and write.get("exists_before") is False
                             for write in journal.get("writes", [])):
                    backup_missing.append(relative)
            conflicts = [row["path"] for row in reconciliation if row["state"] in {"conflict", "backup-invalid"}]
            recoverable = status in {"staged", "applying", "rollback-incomplete"} and not backup_missing and not conflicts
            rows.append(
                {
                    "transaction_id": str(journal.get("transaction_id", journal_path.parent.name)),
                    "status": status,
                    "journal": str(journal_path.relative_to(root)),
                    "write_paths": write_paths,
                    "applied_paths": applied,
                    "rollback_paths": list(journal.get("rollback_paths", [])),
                    "backup_present": backup_present,
                    "backup_missing": backup_missing,
                    "reconciliation": reconciliation,
                    "conflict_paths": conflicts,
                    "recoverable": recoverable,
                    "requires_attention": status not in {"applied", "rolled-back"},
                    "recovery_action": (
                        "use before/ backups for a reviewed targeted rollback"
                        if recoverable
                        else "none"
                        if status in {"applied", "rolled-back"}
                        else "inspect journal and backups before any write"
                    ),
                }
            )
    return {
        "schema_version": 1,
        "read_only": True,
        "transaction_count": len(rows),
        "attention_count": sum(1 for row in rows if row.get("requires_attention")),
        "status": "pass" if all(not row.get("requires_attention") for row in rows) else "needs-recovery-review",
        "rows": rows,
        "must_not": [
            "do not delete transaction journals before review",
            "do not overwrite unrelated worktree changes",
            "do not infer owner approval from a filesystem recovery",
        ],
    }
