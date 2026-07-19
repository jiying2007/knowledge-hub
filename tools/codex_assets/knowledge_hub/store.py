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
import tempfile
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

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


@dataclass
class PlannedWrite:
    path: str
    content: bytes
    expected_sha256: str = ""


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
    def __init__(self, root: pathlib.Path, transaction_id: str = "") -> None:
        self.root = root.resolve()
        self.transaction_id = transaction_id or "kh-{}-{}".format(utc_timestamp().replace(":", "").replace("-", ""), uuid.uuid4().hex[:8])
        self.writes: Dict[str, PlannedWrite] = {}
        self.runtime_root = self.root / ".tmp" / "transactions" / self.transaction_id
        self.stage_root = self.runtime_root / "stage"
        self.backup_root = self.runtime_root / "before"
        self.journal_path = self.runtime_root / "journal.json"
        self.lock_path = self.root / ".tmp" / "locks" / "knowledge-hub.lock"

    def add_text(self, relative: str, content: str, expected_sha256: str = "") -> None:
        self.add_bytes(relative, content.encode("utf-8"), expected_sha256=expected_sha256)

    def add_bytes(self, relative: str, content: bytes, expected_sha256: str = "") -> None:
        safe = normalize_relpath(relative)
        if expected_sha256 and len(expected_sha256) != 64:
            raise KnowledgeHubError("expected SHA256 must have 64 hexadecimal characters: {}".format(safe))
        self.writes[safe] = PlannedWrite(safe, content, expected_sha256)

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
    def _lock(self) -> Iterable[None]:
        ensure_private_directory(self.root / ".tmp")
        ensure_private_directory(self.lock_path.parent)
        if self.lock_path.is_symlink():
            raise KnowledgeHubError("transaction lock must not be a symlink")
        with self.lock_path.open("a+") as handle:
            os.chmod(str(self.lock_path), 0o600)
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise KnowledgeHubError("another Knowledge Hub write transaction is active") from exc
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
        if not changed:
            return TransactionResult(self.transaction_id, "no-change", [], unchanged, "")

        with self._lock():
            # Re-evaluate all preconditions after acquiring the single-writer lock.
            for row in changed:
                relative = row["path"]
                target = resolve_inside(self.root, relative)
                current_hash = file_sha256(target) if target.exists() else ""
                expected = self.writes[relative].expected_sha256
                if expected and current_hash != expected:
                    raise KnowledgeHubError(
                        "optimistic write precondition failed for {}: expected {} actual {}".format(
                            relative, expected, current_hash or "<missing>"
                        )
                    )
                if current_hash != row["before_sha256"]:
                    raise KnowledgeHubError("input changed after planning: {}".format(relative))

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
                    target.parent.mkdir(parents=True, exist_ok=True)
                    os.replace(str(staged), str(target))
                    _fsync_directory(target.parent)
                    journal["applied_paths"].append(relative)
                    self._write_journal(journal)
                journal["status"] = "applied"
                journal["completed_at"] = utc_timestamp()
                self._write_journal(journal)
            except BaseException as exc:
                diagnostics = ["apply failed: {}".format(exc)]
                self._rollback_locked(journal, diagnostics)
                raise KnowledgeHubError("transaction {} failed and was rolled back: {}".format(self.transaction_id, exc)) from exc

        return TransactionResult(
            self.transaction_id,
            "applied",
            [row["path"] for row in changed],
            unchanged,
            str(self.journal_path.relative_to(self.root)),
        )

    def _rollback_locked(self, journal: Dict[str, Any], diagnostics: List[str]) -> None:
        for relative in reversed(list(journal.get("applied_paths", []))):
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
        journal["status"] = "rollback-incomplete" if len(journal.get("rollback_paths", [])) != len(journal.get("applied_paths", [])) else "rolled-back"
        journal["rollback_at"] = utc_timestamp()
        journal["diagnostics"] = diagnostics
        self._write_journal(journal)


def incomplete_transactions(root: pathlib.Path) -> List[Dict[str, Any]]:
    transaction_root = root / ".tmp" / "transactions"
    rows: List[Dict[str, Any]] = []
    if not transaction_root.exists():
        return rows
    for journal_path in sorted(transaction_root.glob("*/journal.json")):
        try:
            journal = json.loads(journal_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
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
                journal = json.loads(journal_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                rows.append(
                    {
                        "transaction_id": journal_path.parent.name,
                        "status": "invalid-journal",
                        "journal": str(journal_path.relative_to(root)),
                        "errors": [str(exc)],
                        "recovery_action": "inspect journal and before/ directory manually; do not overwrite tracked files",
                    }
                )
                continue
            applied = [str(value) for value in journal.get("applied_paths", [])]
            write_paths = [str(value.get("path", "")) for value in journal.get("writes", []) if isinstance(value, dict)]
            backup_present = []
            backup_missing = []
            for relative in applied:
                backup = journal_path.parent / "before" / relative
                if backup.exists():
                    backup_present.append(relative)
                else:
                    backup_missing.append(relative)
            status = str(journal.get("status", "unknown"))
            recoverable = status in {"staged", "applying", "rollback-incomplete"} and not backup_missing
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
