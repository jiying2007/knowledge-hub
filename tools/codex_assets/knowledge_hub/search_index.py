"""SQLite index lifecycle for Knowledge Hub search."""

from __future__ import annotations

import contextlib
import fcntl
import os
import pathlib
import sqlite3
import time
import uuid
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple
from .common import KnowledgeHubError, compact_json, ensure_private_directory, ensure_private_file, read_repository_bytes_bounded, utc_timestamp
from .search_core import (
    FULL_REBUILD_DEPENDENCIES,
    FileState,
    INDEX_SCHEMA_VERSION,
    MAX_INCREMENTAL_FILES,
    SEARCH_AUTHORITY_CANDIDATE_LIMIT,
    SEARCH_MAX_FILE_BYTES,
    SearchBoundaryError,
    TOKEN_CACHE_SCHEMA_VERSION,
    _PersistentTokenCache,
    _governed_items_by_path,
    _index_tokens,
    _indexed_title,
    _metadata_haystack,
    _physical_sources,
    _signature,
    _source_roots,
    _term_variants,
    query_terms,
    search_tokens,
)

class SearchIndex:
    CANDIDATE_LIMIT = 4096
    STRUCTURED_CANDIDATE_LIMIT = 4096

    def __init__(self, root: pathlib.Path) -> None:
        self.root = root.resolve()
        self.cache_root = self.root / ".cache" / "knowledge-hub"
        cache_name = "search-index-v{}".format(INDEX_SCHEMA_VERSION)
        self.path = self.cache_root / "{}.sqlite3".format(cache_name)
        self.lock_path = self.cache_root / "{}.lock".format(cache_name)
        self.token_cache_path = self.cache_root / "search-token-cache-v{}.sqlite3".format(
            TOKEN_CACHE_SCHEMA_VERSION
        )
        self._token_cache_stats: Dict[str, Any] = {}

    def _current_signature(self) -> str:
        if not self.path.exists():
            return ""
        try:
            ensure_private_file(self.path)
            with sqlite3.connect(str(self.path)) as connection:
                row = connection.execute("select value from meta where key='signature'").fetchone()
                schema = connection.execute("select value from meta where key='schema_version'").fetchone()
            if not row or not schema or int(schema[0]) != INDEX_SCHEMA_VERSION:
                return ""
            return str(row[0])
        except (KnowledgeHubError, sqlite3.Error, OSError, ValueError):
            return ""

    @contextlib.contextmanager
    def _lock(self, exclusive: bool = True) -> Iterator[None]:
        ensure_private_directory(self.cache_root)
        if self.lock_path.is_symlink():
            raise KnowledgeHubError("search index lock must not be a symlink")
        with self.lock_path.open("a+") as handle:
            os.chmod(str(self.lock_path), 0o600)
            fcntl.flock(
                handle.fileno(),
                fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH,
            )
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def ensure(self, force: bool = False) -> Dict[str, Any]:
        if not force:
            shared_lock_started = time.monotonic()
            with self._lock(exclusive=False):
                shared_lock_wait_duration_ms = round(
                    (time.monotonic() - shared_lock_started) * 1000,
                    2,
                )
                signature_started = time.monotonic()
                indexed_states = self._indexed_file_states()
                signature_stats: Dict[str, int] = {}
                signature, paths, file_states = _signature(
                    self.root,
                    previous_states=indexed_states,
                    stats=signature_stats,
                )
                signature_duration_ms = round(
                    (time.monotonic() - signature_started) * 1000,
                    2,
                )
                if (
                    indexed_states is not None
                    and indexed_states == file_states
                    and self._current_signature() == signature
                ):
                    result = {
                        "state": "warm",
                        "mode": "local-index",
                        "fresh": True,
                        "rebuilt": False,
                        "updated": False,
                        "signature": signature,
                        "document_files": len(paths),
                        "lock_mode": "shared",
                        "lock_wait_duration_ms": shared_lock_wait_duration_ms,
                        "signature_duration_ms": signature_duration_ms,
                        "metadata_refreshed_files": 0,
                    }
                    result.update(signature_stats)
                    return result
        lock_started = time.monotonic()
        with self._lock(exclusive=True):
            lock_wait_duration_ms = round((time.monotonic() - lock_started) * 1000, 2)
            signature_started = time.monotonic()
            indexed_states = None if force else self._indexed_file_states()
            exclusive_signature_stats: Dict[str, int] = {}
            signature, paths, file_states = _signature(
                self.root,
                previous_states=indexed_states,
                stats=exclusive_signature_stats,
            )
            signature_duration_ms = round((time.monotonic() - signature_started) * 1000, 2)
            if not force and self._current_signature() == signature:
                metadata_refreshed_files = self._refresh_indexed_file_states(
                    file_states,
                    indexed_states,
                )
                result = {
                    "state": "warm",
                    "mode": "local-index",
                    "fresh": True,
                    "rebuilt": False,
                    "updated": False,
                    "signature": signature,
                    "document_files": len(paths),
                    "lock_mode": "exclusive",
                    "lock_wait_duration_ms": lock_wait_duration_ms,
                    "signature_duration_ms": signature_duration_ms,
                    "metadata_refreshed_files": metadata_refreshed_files,
                }
                result.update(exclusive_signature_stats)
                return result
            started = time.monotonic()
            incremental = None
            if not force:
                try:
                    incremental = self._incremental_update(
                        signature,
                        file_states,
                        indexed_states=indexed_states,
                    )
                except (OSError, sqlite3.Error, ValueError):
                    incremental = None
            if incremental is not None:
                result = {
                    "state": "updated",
                    "mode": "local-index",
                    "fresh": True,
                    "rebuilt": False,
                    "updated": True,
                    "signature": signature,
                    "document_files": len(paths),
                    "lock_mode": "exclusive",
                    "document_rows": incremental["document_rows"],
                    "changed_files": incremental["changed_files"],
                    "deleted_files": incremental["deleted_files"],
                    "lock_wait_duration_ms": lock_wait_duration_ms,
                    "signature_duration_ms": signature_duration_ms,
                    "transaction_duration_ms": incremental["transaction_duration_ms"],
                    "update_duration_ms": round((time.monotonic() - started) * 1000, 2),
                }
                result.update(exclusive_signature_stats)
                return result
            document_count = self._rebuild(signature, paths, file_states)
            result = {
                "state": "rebuilt",
                "mode": "local-index",
                "fresh": True,
                "rebuilt": True,
                "updated": False,
                "signature": signature,
                "document_files": len(paths),
                "lock_mode": "exclusive",
                "document_rows": document_count,
                "lock_wait_duration_ms": lock_wait_duration_ms,
                "signature_duration_ms": signature_duration_ms,
                "build_duration_ms": round((time.monotonic() - started) * 1000, 2),
            }
            result.update(exclusive_signature_stats)
            result.update(self._token_cache_stats)
            return result

    def _indexed_file_states(self) -> Optional[Dict[str, FileState]]:
        if not self.path.exists():
            return None
        try:
            ensure_private_file(self.path)
            with sqlite3.connect(str(self.path)) as connection:
                schema = connection.execute(
                    "select value from meta where key='schema_version'"
                ).fetchone()
                if not schema or int(schema[0]) != INDEX_SCHEMA_VERSION:
                    return None
                rows = connection.execute(
                    "select path,size,mtime_ns,ctime_ns,device,inode,content_sha256 "
                    "from indexed_files"
                ).fetchall()
            return {
                str(path): (
                    int(size),
                    int(mtime_ns),
                    int(ctime_ns),
                    int(device),
                    int(inode),
                    str(content_sha256),
                )
                for path, size, mtime_ns, ctime_ns, device, inode, content_sha256 in rows
            }
        except (KnowledgeHubError, sqlite3.Error, OSError, ValueError):
            return None

    def _refresh_indexed_file_states(
        self,
        file_states: Mapping[str, FileState],
        indexed_states: Optional[Mapping[str, FileState]],
    ) -> int:
        if indexed_states is None:
            return 0
        changed = [
            (relative, state)
            for relative, state in file_states.items()
            if indexed_states.get(relative) != state
        ]
        if not changed:
            return 0
        with sqlite3.connect(str(self.path)) as connection:
            connection.executemany(
                "insert or replace into indexed_files"
                "(path,size,mtime_ns,ctime_ns,device,inode,content_sha256) "
                "values(?,?,?,?,?,?,?)",
                (
                    (relative,) + tuple(state)
                    for relative, state in changed
                ),
            )
            connection.commit()
        ensure_private_file(self.path)
        return len(changed)

    def _index_inputs(
        self,
    ) -> Tuple[Dict[str, List[Dict[str, Any]]], List[Tuple[str, pathlib.Path]]]:
        return _governed_items_by_path(self.root), _source_roots(self.root)

    def _insert_path(
        self,
        connection: sqlite3.Connection,
        path: pathlib.Path,
        items_by_path: Mapping[str, Sequence[Mapping[str, Any]]],
        source_roots: Sequence[Tuple[str, pathlib.Path]],
        token_cache: Optional[_PersistentTokenCache] = None,
    ) -> int:
        try:
            relative = path.relative_to(self.root).as_posix()
        except ValueError:
            return 0
        try:
            body = read_repository_bytes_bounded(
                self.root,
                relative,
                SEARCH_MAX_FILE_BYTES,
                "search text file",
            ).decode("utf-8", errors="ignore")
        except KnowledgeHubError as exc:
            raise SearchBoundaryError(str(exc)) from exc
        linked_items = items_by_path.get(relative, [])
        if not linked_items:
            return 0
        physical = _physical_sources(path, source_roots)
        count = 0
        for item in linked_items:
            item_id = str(item.get("id", ""))
            doc_key = "{}#{}".format(relative, item_id or "unregistered")
            metadata = _metadata_haystack(item) if item else ""
            token_input = metadata + "\n" + body
            token_text = (
                token_cache.token_text(token_input)
                if token_cache is not None
                else " ".join(_index_tokens(token_input))
            )
            title = _indexed_title(relative, body, item)
            tags = " ".join(
                str(value) for value in item.get("tags", []) if isinstance(value, str)
            )
            summary = str(item.get("summary_zh", ""))
            cursor = connection.execute(
                "insert into documents(doc_key,path,suffix,physical_sources,item_json,indexed_title,body) values(?,?,?,?,?,?,?)",
                (
                    doc_key,
                    relative,
                    path.suffix.lower(),
                    compact_json(physical),
                    compact_json(item) if item else "{}",
                    title,
                    body,
                ),
            )
            if cursor.lastrowid is None:
                raise KnowledgeHubError("SQLite did not return a document row id")
            rowid = cursor.lastrowid
            connection.execute(
                "insert into documents_fts(rowid,title,item_id,tags,summary,path,body,tokens) values(?,?,?,?,?,?,?,?)",
                (rowid, title, item_id, tags, summary, relative, body, token_text),
            )
            count += 1
        return count

    @staticmethod
    def _delete_path(connection: sqlite3.Connection, relative: str) -> None:
        row_ids = [
            int(row[0])
            for row in connection.execute(
                "select id from documents where path=?", (relative,)
            ).fetchall()
        ]
        if row_ids:
            connection.executemany(
                "delete from documents_fts where rowid=?",
                ((row_id,) for row_id in row_ids),
            )
        connection.execute("delete from documents where path=?", (relative,))
        connection.execute("delete from indexed_files where path=?", (relative,))

    def _incremental_update(
        self,
        signature: str,
        file_states: Mapping[str, FileState],
        indexed_states: Optional[Mapping[str, FileState]] = None,
    ) -> Optional[Dict[str, Any]]:
        if indexed_states is None:
            indexed_states = self._indexed_file_states()
        if indexed_states is None:
            return None
        if any(
            indexed_states.get(relative) != file_states.get(relative)
            for relative in FULL_REBUILD_DEPENDENCIES
        ):
            return None
        changed = sorted(
            relative
            for relative, state in file_states.items()
            if indexed_states.get(relative) != state
        )
        deleted = sorted(set(indexed_states) - set(file_states))
        if not changed and not deleted:
            return None
        if len(changed) + len(deleted) > MAX_INCREMENTAL_FILES:
            return None

        items_by_path, source_roots = self._index_inputs()
        transaction_started = time.monotonic()
        connection = sqlite3.connect(str(self.path))
        try:
            connection.execute("pragma journal_mode=delete")
            connection.execute("pragma synchronous=normal")
            connection.execute("begin immediate")
            for relative in deleted:
                self._delete_path(connection, relative)
            for relative in changed:
                self._delete_path(connection, relative)
                self._insert_path(
                    connection,
                    self.root / relative,
                    items_by_path,
                    source_roots,
                )
                size, mtime_ns, ctime_ns, device, inode, content_sha256 = file_states[relative]
                connection.execute(
                    "insert or replace into indexed_files"
                    "(path,size,mtime_ns,ctime_ns,device,inode,content_sha256) "
                    "values(?,?,?,?,?,?,?)",
                    (
                        relative,
                        size,
                        mtime_ns,
                        ctime_ns,
                        device,
                        inode,
                        content_sha256,
                    ),
                )
            document_count = int(
                connection.execute("select count(*) from documents").fetchone()[0]
            )
            connection.executemany(
                "insert or replace into meta(key,value) values(?,?)",
                (
                    ("signature", signature),
                    ("updated_at", utc_timestamp()),
                    ("document_count", str(document_count)),
                )
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return {
            "document_rows": document_count,
            "changed_files": len(changed),
            "deleted_files": len(deleted),
            "transaction_duration_ms": round(
                (time.monotonic() - transaction_started) * 1000, 2
            ),
        }

    def _rebuild(
        self,
        signature: str,
        paths: Sequence[pathlib.Path],
        file_states: Mapping[str, FileState],
    ) -> int:
        temporary = self.cache_root / "search-index-v{}.{}.sqlite3".format(
            INDEX_SCHEMA_VERSION, uuid.uuid4().hex
        )
        items_by_path, source_roots = self._index_inputs()
        token_cache = _PersistentTokenCache(self.token_cache_path)
        connection = sqlite3.connect(str(temporary))
        os.chmod(str(temporary), 0o600)
        count = 0
        try:
            connection.executescript(
                """
                pragma journal_mode=off;
                pragma synchronous=off;
                create table meta (key text primary key, value text not null);
                create table indexed_files (
                    path text primary key,
                    size integer not null,
                    mtime_ns integer not null,
                    ctime_ns integer not null,
                    device integer not null,
                    inode integer not null,
                    content_sha256 text not null
                );
                create table documents (
                    id integer primary key,
                    doc_key text not null unique,
                    path text not null,
                    suffix text not null,
                    physical_sources text not null,
                    item_json text not null,
                    indexed_title text not null,
                    body text not null
                );
                create virtual table documents_fts using fts5(
                    title, item_id, tags, summary, path, body unindexed, tokens,
                    tokenize='unicode61 remove_diacritics 2'
                );
                """
            )
            for path in paths:
                count += self._insert_path(
                    connection,
                    path,
                    items_by_path,
                    source_roots,
                    token_cache=token_cache,
                )
            connection.executemany(
                "insert into indexed_files"
                "(path,size,mtime_ns,ctime_ns,device,inode,content_sha256) "
                "values(?,?,?,?,?,?,?)",
                (
                    (relative,) + tuple(state)
                    for relative, state in sorted(file_states.items())
                ),
            )
            connection.executemany(
                "insert into meta(key,value) values(?,?)",
                (
                    ("schema_version", str(INDEX_SCHEMA_VERSION)),
                    ("signature", signature),
                    ("built_at", utc_timestamp()),
                    ("document_count", str(count)),
                ),
            )
            connection.commit()
        finally:
            connection.close()
            token_cache.close()
            self._token_cache_stats = token_cache.stats()
        try:
            os.replace(str(temporary), str(self.path))
            ensure_private_file(self.path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return count

    def candidates(
        self,
        query: str,
        candidate_limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        candidate_limit = candidate_limit or self.CANDIDATE_LIMIT
        expanded_query = " ".join(
            variant
            for term in query_terms(query)
            for variant in _term_variants(term)
        )
        tokens = search_tokens(expanded_query, maximum=64)
        if not tokens:
            return []
        expression = " OR ".join('"{}"'.format(value.replace('"', '""')) for value in tokens)
        connection = sqlite3.connect(str(self.path))
        connection.row_factory = sqlite3.Row
        try:
            try:
                rows = connection.execute(
                    """
                    select d.*, bm25(documents_fts, 1.2, 1.1, 0.9, 0.8, 0.5, 0.25, 0.35) as fts_rank
                    from documents_fts join documents d on d.id = documents_fts.rowid
                    where documents_fts match ?
                    order by fts_rank
                    limit ?
                    """,
                    (expression, candidate_limit),
                ).fetchall()
            except sqlite3.Error:
                rows = connection.execute("select d.*, 0.0 as fts_rank from documents d").fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def authority_candidates(
        self,
        query: str,
        candidate_limit: int = SEARCH_AUTHORITY_CANDIDATE_LIMIT,
    ) -> List[Dict[str, Any]]:
        """Preserve exact/current/active matches before the generic FTS cutoff."""

        expanded_query = " ".join(
            variant
            for term in query_terms(query)
            for variant in _term_variants(term)
        )
        tokens = search_tokens(expanded_query, maximum=64)
        if not tokens:
            return []
        expression = " OR ".join(
            '"{}"'.format(value.replace('"', '""')) for value in tokens
        )
        normalized_query = query.strip().lower()
        connection = sqlite3.connect(str(self.path))
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                """
                select d.*, bm25(documents_fts, 1.2, 1.1, 0.9, 0.8, 0.5, 0.25, 0.35) as fts_rank
                from documents_fts join documents d on d.id = documents_fts.rowid
                where documents_fts match ?
                  and (
                    d.path = 'README.md'
                    or d.path like 'projects/%/current/%'
                    or d.item_json like '%\"status\":\"active\"%'
                    or lower(documents_fts.title) = ?
                    or lower(documents_fts.item_id) = ?
                    or lower(d.path) = ?
                  )
                order by fts_rank
                limit ?
                """,
                (
                    expression,
                    normalized_query,
                    normalized_query,
                    normalized_query,
                    candidate_limit,
                ),
            ).fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error:
            return []
        finally:
            connection.close()
