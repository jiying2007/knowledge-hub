"""Cached, explainable Knowledge Hub search.

The index is an ignored local SQLite FTS5 database. Registry metadata remains
authoritative; the cache can always be deleted and rebuilt from tracked files.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

import yaml

from .common import (
    KnowledgeHubError,
    compact_json,
    display_path,
    file_sha256,
    iter_text_file_records,
    iter_text_files,
    load_json,
    load_jsonl,
    registry_items,
    source_id,
    utc_timestamp,
)
from .metrics import (
    INTERACTION_CONTRACT,
    INTERACTIVE_TELEMETRY_SCHEMA_VERSION,
    append_optional_telemetry,
    make_interaction_id,
)
from .model import ITEM_KINDS, ITEM_STATUSES


INDEX_SCHEMA_VERSION = 4
FULL_REBUILD_DEPENDENCIES = frozenset(
    {
        "registry/items.jsonl",
        "registry/sources.json",
        "registry/retired-sources.jsonl",
    }
)
MAX_INCREMENTAL_FILES = 128
KIND_ALIASES = {
    "validation-report": "validation",
    "archive-note": "project-archive",
    "external-source": "external-source-note",
    "owner-worksheet": "owner-decision-worksheet",
}
QUERY_PATTERN = re.compile(r"[a-z0-9_./:+-]+|[\u4e00-\u9fff]+", re.IGNORECASE)
ASCII_TOKEN_PATTERN = re.compile(r"[a-z0-9_:+.-]+", re.IGNORECASE)
CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]+")
SYNONYMS: Dict[str, Tuple[str, ...]] = {
    "双向链接": ("backlink", "backlinks", "反向链接"),
    "反向链接": ("backlink", "backlinks", "双向链接"),
    "知识图谱": ("graph", "关系图"),
    "发布": ("release",),
    "归档": ("archive",),
    "排障": ("debug", "triage"),
    "决策": ("decision",),
    "验证": ("validation",),
}
GENERIC_QUERY_TERMS = {
    "knowledge",
    "hub",
    "guide",
    "runbook",
    "readiness",
    "validation",
    "项目",
    "候选",
    "文档",
}


@dataclass
class SearchFilters:
    sources: Sequence[str] = field(default_factory=tuple)
    owners: Sequence[str] = field(default_factory=tuple)
    statuses: Sequence[str] = field(default_factory=tuple)
    kinds: Sequence[str] = field(default_factory=tuple)
    domains: Sequence[str] = field(default_factory=tuple)
    source_ids: Sequence[str] = field(default_factory=tuple)

    @property
    def normalized_kinds(self) -> List[str]:
        return [KIND_ALIASES.get(value, value) for value in self.kinds]

    @property
    def structured(self) -> bool:
        return bool(self.owners or self.statuses or self.kinds or self.domains or self.source_ids)

    def validate(self) -> None:
        invalid_statuses = sorted(set(self.statuses) - ITEM_STATUSES)
        invalid_kinds = sorted(value for value in set(self.kinds) if KIND_ALIASES.get(value, value) not in ITEM_KINDS)
        if invalid_statuses:
            raise KnowledgeHubError(
                "invalid --status value(s): {}; allowed: {}".format(
                    ", ".join(invalid_statuses), ", ".join(sorted(ITEM_STATUSES))
                )
            )
        if invalid_kinds:
            allowed = sorted(ITEM_KINDS | set(KIND_ALIASES))
            raise KnowledgeHubError(
                "invalid --kind value(s): {}; allowed: {}".format(", ".join(invalid_kinds), ", ".join(allowed))
            )


def query_terms(query: str) -> List[str]:
    terms = [match.group(0).lower() for match in QUERY_PATTERN.finditer(query.lower())]
    return terms or ([query.lower()] if query.strip() else [])


def _cjk_ngrams(value: str) -> Set[str]:
    grams: Set[str] = set()
    for segment in CJK_PATTERN.findall(value):
        if len(segment) == 1:
            grams.add(segment)
            continue
        grams.add(segment)
        for width in (2, 3):
            for index in range(max(0, len(segment) - width + 1)):
                grams.add(segment[index : index + width])
    return grams


def search_tokens(value: str, maximum: int = 20000) -> List[str]:
    normalized = value.lower()
    tokens = set(ASCII_TOKEN_PATTERN.findall(normalized))
    tokens.update(_cjk_ngrams(normalized))
    return sorted(tokens)[:maximum]


def _term_variants(term: str) -> Tuple[str, ...]:
    variants = [term]
    variants.extend(SYNONYMS.get(term.lower(), ()))
    return tuple(dict.fromkeys(value.lower() for value in variants if value))


def _metadata_haystack(item: Mapping[str, Any]) -> str:
    fields: List[str] = [
        str(item.get("id", "")),
        str(item.get("title", "")),
        str(item.get("path", "")),
        str(item.get("kind", "")),
        str(item.get("domain", "")),
        str(item.get("status", "")),
        str(item.get("owner", "")),
        str(item.get("summary_zh", "")),
        str(item.get("review_status", "")),
        source_id(item),
    ]
    tags = item.get("tags", [])
    if isinstance(tags, list):
        fields.extend(str(value) for value in tags)
    source = item.get("source")
    if isinstance(source, dict):
        fields.extend(str(value) for value in source.values() if isinstance(value, (str, int, float)))
    return "\n".join(value for value in fields if value).lower()


def _indexed_title(relative: str, body: str, item: Mapping[str, Any]) -> str:
    title = str(item.get("title", "")) if item else ""
    if title:
        return title
    if body.startswith("---\n"):
        marker = body.find("\n---\n", 4)
        if marker >= 0:
            try:
                metadata = yaml.safe_load(body[4:marker]) or {}
                if isinstance(metadata, dict) and metadata.get("title"):
                    return str(metadata["title"])
            except (ValueError, TypeError, yaml.YAMLError):
                pass
    for line in body.splitlines()[:80]:
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1)
    return pathlib.PurePosixPath(relative).stem.replace("-", " ").replace("_", " ")


def _source_roots(root: pathlib.Path) -> List[Tuple[str, pathlib.Path]]:
    rows = list((load_json(root / "registry/sources.json", {}) or {}).get("sources", []))
    rows.extend(load_jsonl(root / "registry/retired-sources.jsonl"))
    result: List[Tuple[str, pathlib.Path]] = []
    for row in rows:
        source_path = str(row.get("path", ""))
        source_name = str(row.get("id", ""))
        if not source_path or not source_name:
            continue
        candidate = pathlib.Path(source_path).expanduser()
        if not candidate.is_absolute():
            candidate = root / candidate
        result.append((source_name, candidate.resolve(strict=False)))
    return result


def _physical_sources(path: pathlib.Path, roots: Sequence[Tuple[str, pathlib.Path]]) -> List[str]:
    result = ["knowledge-hub"]
    resolved = path.resolve(strict=False)
    for source_name, source_root in roots:
        try:
            resolved.relative_to(source_root)
        except ValueError:
            continue
        result.append(source_name)
    return result


def _signature(
    root: pathlib.Path,
) -> Tuple[str, List[pathlib.Path], Dict[str, Tuple[int, int]]]:
    records = sorted(iter_text_file_records(root), key=lambda value: value[1])
    paths = [path for path, _, _ in records]
    digest = hashlib.sha256()
    digest.update(str(INDEX_SCHEMA_VERSION).encode("ascii"))
    file_states: Dict[str, Tuple[int, int]] = {}
    for _, relative, file_stat in records:
        file_states[relative] = (file_stat.st_size, file_stat.st_mtime_ns)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(file_stat.st_size).encode("ascii"))
        digest.update(b":")
        digest.update(str(file_stat.st_mtime_ns).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest(), paths, file_states


class SearchIndex:
    CANDIDATE_LIMIT = 256

    def __init__(self, root: pathlib.Path) -> None:
        self.root = root.resolve()
        self.cache_root = self.root / ".cache" / "knowledge-hub"
        cache_name = "search-index-v{}".format(INDEX_SCHEMA_VERSION)
        self.path = self.cache_root / "{}.sqlite3".format(cache_name)
        self.lock_path = self.cache_root / "{}.lock".format(cache_name)
        self._ensure_cache: Optional[Tuple[float, Dict[str, Any]]] = None

    def _current_signature(self) -> str:
        if not self.path.exists():
            return ""
        try:
            with sqlite3.connect(str(self.path)) as connection:
                row = connection.execute("select value from meta where key='signature'").fetchone()
                schema = connection.execute("select value from meta where key='schema_version'").fetchone()
            if not row or not schema or int(schema[0]) != INDEX_SCHEMA_VERSION:
                return ""
            return str(row[0])
        except (sqlite3.Error, OSError, ValueError):
            return ""

    @contextlib.contextmanager
    def _lock(self) -> Iterable[None]:
        self.cache_root.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def ensure(self, force: bool = False) -> Dict[str, Any]:
        if not force and self._ensure_cache and time.monotonic() - self._ensure_cache[0] <= 30.0:
            cached = dict(self._ensure_cache[1])
            cached["state"] = "warm-session"
            cached["rebuilt"] = False
            cached["updated"] = False
            cached["lock_wait_duration_ms"] = 0.0
            cached["signature_duration_ms"] = 0.0
            return cached
        lock_started = time.monotonic()
        with self._lock():
            lock_wait_duration_ms = round((time.monotonic() - lock_started) * 1000, 2)
            signature_started = time.monotonic()
            signature, paths, file_states = _signature(self.root)
            signature_duration_ms = round((time.monotonic() - signature_started) * 1000, 2)
            if not force and self._current_signature() == signature:
                result = {
                    "state": "warm",
                    "mode": "local-index",
                    "fresh": True,
                    "rebuilt": False,
                    "updated": False,
                    "signature": signature,
                    "document_files": len(paths),
                    "lock_wait_duration_ms": lock_wait_duration_ms,
                    "signature_duration_ms": signature_duration_ms,
                }
                self._ensure_cache = (time.monotonic(), result)
                return result
            started = time.monotonic()
            incremental = None
            if not force:
                try:
                    incremental = self._incremental_update(signature, file_states)
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
                    "document_rows": incremental["document_rows"],
                    "changed_files": incremental["changed_files"],
                    "deleted_files": incremental["deleted_files"],
                    "lock_wait_duration_ms": lock_wait_duration_ms,
                    "signature_duration_ms": signature_duration_ms,
                    "transaction_duration_ms": incremental["transaction_duration_ms"],
                    "update_duration_ms": round((time.monotonic() - started) * 1000, 2),
                }
                self._ensure_cache = (time.monotonic(), result)
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
                "document_rows": document_count,
                "lock_wait_duration_ms": lock_wait_duration_ms,
                "signature_duration_ms": signature_duration_ms,
                "build_duration_ms": round((time.monotonic() - started) * 1000, 2),
            }
            self._ensure_cache = (time.monotonic(), result)
            return result

    def _indexed_file_states(self) -> Optional[Dict[str, Tuple[int, int]]]:
        if not self.path.exists():
            return None
        try:
            with sqlite3.connect(str(self.path)) as connection:
                schema = connection.execute(
                    "select value from meta where key='schema_version'"
                ).fetchone()
                if not schema or int(schema[0]) != INDEX_SCHEMA_VERSION:
                    return None
                rows = connection.execute(
                    "select path,size,mtime_ns from indexed_files"
                ).fetchall()
            return {str(path): (int(size), int(mtime_ns)) for path, size, mtime_ns in rows}
        except (sqlite3.Error, OSError, ValueError):
            return None

    def _index_inputs(
        self,
    ) -> Tuple[Dict[str, List[Dict[str, Any]]], List[Tuple[str, pathlib.Path]]]:
        items = registry_items(self.root)
        items_by_path: Dict[str, List[Dict[str, Any]]] = {}
        for item in items:
            path = str(item.get("path", ""))
            if path:
                items_by_path.setdefault(path, []).append(item)
        return items_by_path, _source_roots(self.root)

    def _insert_path(
        self,
        connection: sqlite3.Connection,
        path: pathlib.Path,
        items_by_path: Mapping[str, Sequence[Mapping[str, Any]]],
        source_roots: Sequence[Tuple[str, pathlib.Path]],
    ) -> int:
        try:
            body = path.read_text(encoding="utf-8", errors="ignore")
            relative = path.relative_to(self.root).as_posix()
        except (OSError, ValueError):
            return 0
        linked_items = items_by_path.get(relative, []) or [{}]
        physical = _physical_sources(path, source_roots)
        count = 0
        for item in linked_items:
            item_id = str(item.get("id", ""))
            doc_key = "{}#{}".format(relative, item_id or "unregistered")
            metadata = _metadata_haystack(item) if item else ""
            token_text = " ".join(search_tokens(metadata + "\n" + body))
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
            rowid = int(cursor.lastrowid)
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
        file_states: Mapping[str, Tuple[int, int]],
    ) -> Optional[Dict[str, Any]]:
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
                size, mtime_ns = file_states[relative]
                connection.execute(
                    "insert or replace into indexed_files(path,size,mtime_ns) values(?,?,?)",
                    (relative, size, mtime_ns),
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
        file_states: Mapping[str, Tuple[int, int]],
    ) -> int:
        temporary = self.cache_root / "search-index-v{}.{}.sqlite3".format(
            INDEX_SCHEMA_VERSION, uuid.uuid4().hex
        )
        items_by_path, source_roots = self._index_inputs()
        connection = sqlite3.connect(str(temporary))
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
                    mtime_ns integer not null
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
                    title, item_id, tags, summary, path, body, tokens,
                    tokenize='unicode61 remove_diacritics 2'
                );
                """
            )
            for path in paths:
                count += self._insert_path(connection, path, items_by_path, source_roots)
            connection.executemany(
                "insert into indexed_files(path,size,mtime_ns) values(?,?,?)",
                (
                    (relative, state[0], state[1])
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
        try:
            os.replace(str(temporary), str(self.path))
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return count

    def candidates(self, query: str) -> List[sqlite3.Row]:
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
                    (expression, self.CANDIDATE_LIMIT),
                ).fetchall()
            except sqlite3.Error:
                rows = connection.execute("select d.*, 0.0 as fts_rank from documents d").fetchall()
            return rows
        finally:
            connection.close()


def _path_priority(relative: str) -> Tuple[int, str]:
    normalized = relative.replace("\\", "/")
    if normalized == "README.md":
        return 100, "root-entry"
    if normalized.startswith("projects/") and any(part in normalized for part in ("/current/", "/decisions/", "/validation/")):
        return 120, "project-canonical"
    if normalized.startswith("domains/embedded/") and any(part in normalized for part in ("/runbooks/", "/standards/", "/architecture/")):
        return 115, "domain-canonical"
    if normalized.startswith("projects/") and "/archive/" in normalized:
        return 55, "project-archive"
    if normalized.startswith("governance/status/"):
        return 80, "governance-status"
    if normalized.startswith("governance/"):
        return 65, "governance"
    if normalized.startswith("indexes/"):
        return 35, "derived-index"
    if normalized.startswith("tools/"):
        return 20, "tooling"
    if normalized.startswith("artifacts/manifests/"):
        return 0, "historical-manifest"
    if normalized.startswith("registry/"):
        return -20, "registry-ledger"
    return 40, "body"


def _status_priority(status: str) -> int:
    return {
        "active": 100,
        "reviewing": 55,
        "draft": 20,
        "personal": 0,
        "archived": -15,
        "superseded": -80,
        "rejected": -100,
    }.get(status, 0)


def _term_matches(term: str, haystack: str) -> bool:
    variants = _term_variants(term)
    if any(variant in haystack for variant in variants):
        return True
    for variant in variants:
        cjk = "".join(CJK_PATTERN.findall(variant))
        if len(cjk) < 2:
            continue
        grams = _cjk_ngrams(cjk)
        short = [value for value in grams if len(value) == 2]
        if short and sum(1 for value in short if value in haystack) / float(len(short)) >= 0.5:
            return True
    return False


def _filters_match(item: Mapping[str, Any], physical_sources: Sequence[str], filters: SearchFilters) -> bool:
    if filters.sources and not set(filters.sources).intersection(physical_sources):
        return False
    if filters.structured and not item:
        return False
    if filters.owners and item.get("owner", "") not in filters.owners:
        return False
    if filters.statuses and item.get("status", "") not in filters.statuses:
        return False
    if filters.normalized_kinds and item.get("kind", "") not in filters.normalized_kinds:
        return False
    if filters.domains and not any(str(item.get("domain", "")).startswith(prefix) for prefix in filters.domains):
        return False
    if filters.source_ids and source_id(item) not in filters.source_ids:
        return False
    return True


def _filter_reason(item: Mapping[str, Any], physical_sources: Sequence[str], filters: SearchFilters) -> str:
    if filters.sources and not set(filters.sources).intersection(physical_sources):
        return "physical-source"
    if filters.structured and not item:
        return "unregistered-structured-result"
    if filters.owners and item.get("owner", "") not in filters.owners:
        return "owner"
    if filters.statuses and item.get("status", "") not in filters.statuses:
        return "status"
    if filters.normalized_kinds and item.get("kind", "") not in filters.normalized_kinds:
        return "kind"
    if filters.domains and not any(str(item.get("domain", "")).startswith(prefix) for prefix in filters.domains):
        return "domain"
    if filters.source_ids and source_id(item) not in filters.source_ids:
        return "source-id"
    return ""


def _scan_candidates(root: pathlib.Path) -> List[Dict[str, Any]]:
    items_by_path: Dict[str, List[Dict[str, Any]]] = {}
    for item in registry_items(root):
        relative = str(item.get("path", ""))
        if relative:
            items_by_path.setdefault(relative, []).append(item)
    source_roots = _source_roots(root)
    rows: List[Dict[str, Any]] = []
    for path in iter_text_files(root):
        try:
            relative = path.relative_to(root).as_posix()
            body = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, ValueError):
            continue
        for item in items_by_path.get(relative, []) or [{}]:
            rows.append(
                {
                    "path": relative,
                    "suffix": path.suffix.lower(),
                    "physical_sources": compact_json(_physical_sources(path, source_roots)),
                    "item_json": compact_json(item) if item else "{}",
                    "indexed_title": _indexed_title(relative, body, item),
                    "body": body,
                    "fts_rank": 0.0,
                }
            )
    return rows


def _preview(body: str, terms: Sequence[str], item: Mapping[str, Any]) -> Tuple[int, str, bool]:
    lower = body.lower()
    positions = [(lower.find(term), term) for term in terms if lower.find(term) >= 0]
    if not positions:
        grams = [gram for term in terms for gram in _cjk_ngrams(term) if len(gram) >= 2]
        positions = [(lower.find(gram), gram) for gram in grams if lower.find(gram) >= 0]
    if not positions:
        summary = item.get("summary_zh") or item.get("title") or item.get("id", "")
        return 1, "registry metadata: {}".format(summary)[:240], False
    index, _ = min(positions, key=lambda value: value[0])
    line_no = lower[:index].count("\n") + 1
    lines = body.splitlines()
    line = lines[line_no - 1].strip()[:240] if lines and line_no <= len(lines) else ""
    return line_no, line, True


def _score(
    relative: str,
    suffix: str,
    body: str,
    item: Mapping[str, Any],
    indexed_title: str,
    terms: Sequence[str],
    query: str,
) -> Optional[Tuple[int, List[str], float]]:
    body_haystack = body.lower()
    metadata = _metadata_haystack(item) if item else ""
    combined = metadata + "\n" + body_haystack
    matched_terms = [term for term in terms if _term_matches(term, combined)]
    if not matched_terms:
        return None
    coverage = len(matched_terms) / float(max(1, len(terms)))
    score, path_reason = _path_priority(relative)
    reasons = [path_reason, "query-coverage:{:.2f}".format(coverage)]
    score += int(coverage * 180)
    if item:
        status = str(item.get("status", ""))
        score += 300 + _status_priority(status)
        reasons.extend(["registry-backed", "status:{}".format(status)])
    title = (str(item.get("title", "")) if item else indexed_title).lower()
    item_id = str(item.get("id", "")).lower() if item else ""
    path_text = str(item.get("path", relative)).lower() if item else relative.lower()
    summary = str(item.get("summary_zh", "")).lower() if item else ""
    tags = " ".join(str(value).lower() for value in item.get("tags", [])) if item and isinstance(item.get("tags"), list) else ""
    normalized_query = query.lower().strip()
    if normalized_query and normalized_query in title:
        score += 190
        reasons.append("exact-title")
    elif title:
        title_hits = sum(1 for term in terms if _term_matches(term, title))
        score += title_hits * 70
        if title_hits:
            reasons.append("title-tokens")
    if normalized_query and normalized_query in item_id:
        score += 150
        reasons.append("exact-id")
    elif item_id:
        id_hits = sum(1 for term in terms if _term_matches(term, item_id))
        score += id_hits * 55
        if id_hits:
            reasons.append("id-tokens")
    for field, weight, reason in ((tags, 45, "tag-tokens"), (summary, 40, "summary-tokens"), (path_text, 30, "path-tokens")):
        hits = sum(1 for term in terms if _term_matches(term, field))
        if hits:
            score += hits * weight
            reasons.append(reason)
    distinctive_terms = [term for term in terms if term not in GENERIC_QUERY_TERMS and len(term) >= 3]
    metadata_fields = "\n".join((title, item_id, tags, summary, path_text))
    distinctive_hits = [term for term in distinctive_terms if _term_matches(term, metadata_fields)]
    if distinctive_hits:
        score += min(480, sum(min(180, 45 + (12 * len(term))) for term in distinctive_hits))
        reasons.append("distinctive-metadata:{}".format(len(distinctive_hits)))
    body_only_hits = [
        term
        for term in distinctive_terms
        if _term_matches(term, body_haystack) and not _term_matches(term, metadata_fields)
    ]
    if body_only_hits:
        score -= min(120, len(body_only_hits) * 30)
        reasons.append("body-only-distinctive-penalty")
    ascii_distinctive = [
        term
        for term in distinctive_terms
        if ASCII_TOKEN_PATTERN.fullmatch(term) and term not in GENERIC_QUERY_TERMS
    ]
    if len(ascii_distinctive) >= 2 and all(term in path_text for term in ascii_distinctive):
        score += 220
        reasons.append("exact-path-term-set")
    if normalized_query and normalized_query in body_haystack:
        score += 55
        reasons.append("exact-body")
    elif any(_term_matches(term, body_haystack) for term in terms):
        score += 20
        reasons.append("body-tokens")
    if suffix in {".json", ".jsonl"}:
        score -= 55
        reasons.append("structured-ledger-penalty")
    if relative.startswith("artifacts/manifests/"):
        score -= 75
        reasons.append("historical-penalty")
    if relative.startswith("registry/"):
        score -= 110
        reasons.append("registry-noise-penalty")
    source_type = str((item.get("source") or {}).get("type", "")) if item and isinstance(item.get("source"), dict) else ""
    if source_type in {"retired-source-provenance", "artifact-ref"}:
        score -= 35
        reasons.append("provenance-penalty")
    return int(score), reasons, coverage


def search(
    root: pathlib.Path,
    query: str,
    limit: int = 20,
    filters: Optional[SearchFilters] = None,
    rebuild_index: bool = False,
    search_index: Optional[SearchIndex] = None,
) -> Dict[str, Any]:
    started = time.monotonic()
    if limit < 1:
        raise KnowledgeHubError("--limit must be >= 1")
    if not query.strip():
        raise KnowledgeHubError("query must not be empty")
    filters = filters or SearchFilters()
    filters.validate()
    index = search_index or SearchIndex(root)
    try:
        index_state = index.ensure(force=rebuild_index)
        indexed_rows: Sequence[Mapping[str, Any]] = index.candidates(query)
    except (KnowledgeHubError, OSError, sqlite3.Error) as exc:
        index_state = {
            "state": "fallback",
            "mode": "repository-scan-fallback",
            "fresh": False,
            "rebuilt": False,
            "reason": str(exc),
        }
        indexed_rows = _scan_candidates(root)
    index_state["candidate_count"] = len(indexed_rows)
    index_state["candidate_limit"] = (
        index.CANDIDATE_LIMIT if index_state.get("mode") == "local-index" else None
    )
    terms = query_terms(query)
    candidates: List[Dict[str, Any]] = []
    filtered_reasons: Counter = Counter()
    for row in indexed_rows:
        try:
            item = json.loads(row["item_json"])
            physical_sources = json.loads(row["physical_sources"])
        except (json.JSONDecodeError, TypeError):
            continue
        filter_reason = _filter_reason(item, physical_sources, filters)
        if filter_reason:
            filtered_reasons[filter_reason] += 1
            continue
        scored = _score(
            str(row["path"]),
            str(row["suffix"]),
            str(row["body"]),
            item,
            str(row["indexed_title"]),
            terms,
            query,
        )
        if scored is None:
            continue
        score, reasons, coverage = scored
        line_no, preview, body_match = _preview(str(row["body"]), terms, item)
        selected_source = "knowledge-hub"
        if filters.sources:
            selected_source = next((value for value in filters.sources if value in physical_sources), "knowledge-hub")
        result: Dict[str, Any] = {
            "source": selected_source,
            "path": str(row["path"]),
            "line": line_no,
            "preview": preview,
            "score": score,
            "match": "body-and-metadata" if body_match and item else "body" if body_match else "registry-metadata",
            "match_kind": reasons[0],
            "why_selected": reasons,
            "query_coverage": round(coverage, 3),
            "evidence_strength": item.get("evidence_strength", "") if item else "unregistered-body",
            "manual_validation_pending": bool(item.get("manual_validation_pending", False)) if item else True,
        }
        if item:
            result.update(
                {
                    "item_id": item.get("id", ""),
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "kind": item.get("kind", ""),
                    "domain": item.get("domain", ""),
                    "status": item.get("status", ""),
                    "owner": item.get("owner", ""),
                    "source_id": source_id(item),
                    "review_after": item.get("review_after", ""),
                    "tags": item.get("tags", []),
                }
            )
        elif row["indexed_title"]:
            result["title"] = str(row["indexed_title"])
        candidates.append(result)
    candidates.sort(key=lambda value: (-int(value["score"]), str(value.get("path", "")), str(value.get("item_id", ""))))
    results = candidates[:limit]
    elapsed_ms = round((time.monotonic() - started) * 1000, 2)
    zero_hit = {
        "is_zero_hit": not bool(results),
        "reason": "" if results else "no indexed document matched the query and structured filters",
        "degraded_terms": [],
        "filtered_by_reason": dict(sorted(filtered_reasons.items())),
        "suggestions": [] if results else [
            "remove one structured filter",
            "use a project/repository alias from registry/project-routes.json",
            "try a shorter domain term or exact item id",
        ],
    }
    payload = {
        "schema_version": 2,
        "status": "pass" if results else "zero-hit",
        "query": query,
        "query_terms": terms,
        "count": len(results),
        "total_matches": len(candidates),
        "ranking": "sqlite-fts5-registry-canonical-distinctive-terms-v3",
        "filters": {
            "source": list(filters.sources),
            "owner": list(filters.owners),
            "status": list(filters.statuses),
            "kind": list(filters.kinds),
            "kind_normalized": filters.normalized_kinds,
            "domain": list(filters.domains),
            "source_id": list(filters.source_ids),
        },
        "index": index_state,
        "filter_diagnostics": {
            "filtered_count": sum(filtered_reasons.values()),
            "by_reason": dict(sorted(filtered_reasons.items())),
        },
        "latency_ms": elapsed_ms,
        "results": results,
        "zero_hit": zero_hit,
    }
    return payload


def record_search_telemetry(
    root: pathlib.Path,
    payload: Mapping[str, Any],
    enabled: bool = True,
) -> Dict[str, Any]:
    query = str(payload.get("query", ""))
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    recorded_at = utc_timestamp()
    result_ids = []
    for result in payload.get("results", []):
        result_id = str(result.get("item_id") or result.get("id") or "")
        if result_id and result_id not in result_ids:
            result_ids.append(result_id)
    row = {
        "schema_version": INTERACTIVE_TELEMETRY_SCHEMA_VERSION,
        "sample_kind": "interactive",
        "interaction_contract": INTERACTION_CONTRACT,
        "interaction_id": make_interaction_id("search", query_hash, recorded_at),
        "retrieval_kind": "search",
        "recorded_at": recorded_at,
        "query_sha256": query_hash,
        "query_term_count": len(payload.get("query_terms", [])),
        "result_count": int(payload.get("count", 0)),
        "result_ids": result_ids,
        "total_matches": int(payload.get("total_matches", 0)),
        "latency_ms": payload.get("latency_ms", 0),
        "index_state": (payload.get("index") or {}).get("state", ""),
        "index_rebuilt": bool((payload.get("index") or {}).get("rebuilt", False)),
        "index_updated": bool((payload.get("index") or {}).get("updated", False)),
        "index_lock_wait_ms": (payload.get("index") or {}).get("lock_wait_duration_ms", 0),
        "index_signature_ms": (payload.get("index") or {}).get("signature_duration_ms", 0),
        "index_transaction_ms": (payload.get("index") or {}).get("transaction_duration_ms", 0),
        "raw_query_stored": False,
    }
    path = root / ".cache/knowledge-hub/search-telemetry.jsonl"
    return append_optional_telemetry(path, row, enabled=enabled)
