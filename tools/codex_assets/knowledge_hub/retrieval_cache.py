"""Disposable, bounded derived cache; never a source or authorization store."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sqlite3
from typing import Any, Callable, Dict, Optional

from .common import KnowledgeHubError, ensure_private_directory_tree, ensure_private_file

MAX_DATABASE_BYTES = 64 * 1024 * 1024
MAX_ENTRY_BYTES = 4 * 1024 * 1024
MAX_ENTRIES = 4096
MAX_WRITES = 256


def fingerprint(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class DerivedCache:
    """One query owns this connection. Cache errors disable caching, not evidence.

    Canonical content must be read and authorized before resolve(). Checksums
    detect corruption, not malicious edits by the local account. No query text,
    principal, authority decision or provider credentials are persisted.
    """

    def __init__(self, root: pathlib.Path, enabled: bool = True) -> None:
        if type(enabled) is not bool:
            raise KnowledgeHubError("cache_enabled must be a boolean")
        self.connection: Optional[sqlite3.Connection] = None
        self.stats: Dict[str, Any] = {
            "enabled": False, "reason": "disabled-by-caller" if not enabled else "available",
            "hits": 0, "misses": 0, "writes": 0, "invalid_entries": 0,
            "by_namespace": {}, "max_database_bytes": MAX_DATABASE_BYTES,
        }
        if enabled:
            self._open(pathlib.Path(root))

    def _open(self, root: pathlib.Path) -> None:
        directory = root / ".cache" / "knowledge-hub"
        ensure_private_directory_tree(root, directory)
        path = directory / "retrieval-derived-v1.sqlite3"
        for suffix in ("", "-journal", "-wal", "-shm"):
            candidate = pathlib.Path(str(path) + suffix)
            if candidate.is_symlink():
                raise KnowledgeHubError("derived cache must not contain symlinks")
            ensure_private_file(candidate)
        if path.exists() and path.stat().st_size > MAX_DATABASE_BYTES:
            self.stats["reason"] = "database-budget"
            return
        try:
            descriptor = os.open(str(path), os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
            os.close(descriptor)
            self.connection = sqlite3.connect(str(path), timeout=0.05, isolation_level=None)
            self.connection.execute("pragma trusted_schema=off")
            self.connection.execute("pragma journal_mode=delete")
            self.connection.execute("pragma page_size=4096")
            if self.connection.execute("pragma page_size").fetchone()[0] != 4096:
                self._disable("unsupported-cache-page-size")
                return
            self.connection.execute("pragma max_page_count=16384")
            self.connection.execute("pragma secure_delete=on")
            self.connection.execute("""create table if not exists entries (
                seq integer primary key, namespace text not null, key text not null,
                revision text not null, payload blob not null, digest text not null,
                unique(namespace,key))""")
            self.stats["enabled"] = True
        except (OSError, sqlite3.Error):
            self._disable("cache-unavailable")

    def _disable(self, reason: str) -> None:
        self.close()
        self.stats.update(enabled=False, reason=reason)

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def __enter__(self) -> "DerivedCache":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def _read(self, namespace: str, key: str, revision: str) -> Any:
        if self.connection is None:
            return None
        try:
            row = self.connection.execute(
                "select length(payload) from entries where namespace=? and key=? and revision=?",
                (namespace, key, revision),
            ).fetchone()
            if row is None or not 0 < row[0] <= MAX_ENTRY_BYTES:
                return None
            # The predicate also applies to the payload read: no header/read race.
            row = self.connection.execute(
                "select payload,digest from entries where namespace=? and key=? and revision=? and length(payload)<=?",
                (namespace, key, revision, MAX_ENTRY_BYTES),
            ).fetchone()
            if row is None:
                return None
            if not isinstance(row[0], bytes) or not isinstance(row[1], str):
                self.stats["invalid_entries"] += 1
                return None
            raw = row[0]
            if hashlib.sha256(raw).hexdigest() != row[1]:
                self.stats["invalid_entries"] += 1
                return None
            return json.loads(raw.decode("utf-8"))
        except (ValueError, TypeError, UnicodeError, RecursionError):
            self.stats["invalid_entries"] += 1
            return None
        except sqlite3.Error:
            self._disable("cache-read-failed")
            return None

    def _write(self, namespace: str, key: str, revision: str, value: Any) -> None:
        if self.connection is None or self.stats["writes"] >= MAX_WRITES:
            return
        raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(raw) > MAX_ENTRY_BYTES:
            return
        try:
            # A short atomic transaction; never hold a write lock over a provider call.
            self.connection.execute("begin immediate")
            self.connection.execute("delete from entries where namespace=? and key=?", (namespace, key))
            count = self.connection.execute("select count(*) from entries").fetchone()[0]
            if count >= MAX_ENTRIES:
                self.connection.execute(
                    "delete from entries where seq in (select seq from entries order by seq limit ?)",
                    (count - MAX_ENTRIES + 1,),
                )
            self.connection.execute(
                "insert into entries(namespace,key,revision,payload,digest) values(?,?,?,?,?)",
                (namespace, key, revision, raw, hashlib.sha256(raw).hexdigest()),
            )
            self.connection.execute("commit")
            self.stats["writes"] += 1
        except sqlite3.Error:
            self._disable("cache-write-failed")

    def resolve(
        self, namespace: str, key: str, revision: str,
        build: Callable[[], Any], valid: Callable[[Any], bool],
    ) -> Any:
        counters = self.stats["by_namespace"].setdefault(namespace, {"hits": 0, "misses": 0})
        value = self._read(namespace, key, revision)
        if value is not None:
            try:
                cache_valid = valid(value)
            except (TypeError, ValueError, OverflowError, KeyError):
                cache_valid = False
            if cache_valid:
                self.stats["hits"] += 1
                counters["hits"] += 1
                return value
            self.stats["invalid_entries"] += 1
        self.stats["misses"] += 1
        counters["misses"] += 1
        value = build()  # Source/provider failures must propagate, never become cache fallback.
        if not valid(value):
            raise KnowledgeHubError("invalid derived {} payload".format(namespace))
        self._write(namespace, key, revision, value)
        return value
