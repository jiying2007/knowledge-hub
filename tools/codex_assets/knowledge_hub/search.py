"""Cached, explainable Knowledge Hub search.

The index is an ignored local SQLite FTS5 database. Registry metadata remains
authoritative; the cache can always be deleted and rebuilt from tracked files.
"""

from __future__ import annotations

import base64
import contextlib
import fcntl
import hashlib
import json
import math
import os
import pathlib
import re
import sqlite3
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Set, Tuple

import yaml

from .common import (
    KnowledgeHubError,
    TEXT_SUFFIXES,
    bytes_sha256,
    compact_json,
    ensure_private_directory,
    ensure_private_file,
    load_json,
    load_jsonl,
    normalize_relpath,
    read_repository_bytes_bounded,
    registry_items,
    source_id,
    utc_timestamp,
)
from .metrics import (
    INTERACTION_CONTRACT,
    INTERACTIVE_TELEMETRY_SCHEMA_VERSION,
    PERFORMANCE_CONTRACT,
    append_optional_telemetry,
    make_interaction_id,
)
from .model import ITEM_KINDS, ITEM_STATUSES
from .schemas import validate_instance


INDEX_SCHEMA_VERSION = 8
TOKEN_CACHE_SCHEMA_VERSION = 2
TOKEN_CACHE_MAX_ENTRIES = 10000
TOKEN_CACHE_MAX_VALUE_BYTES = 4 * 1024 * 1024
TOKEN_CACHE_MAX_TOTAL_BYTES = 128 * 1024 * 1024
FULL_REBUILD_DEPENDENCIES = frozenset(
    {
        "registry/items.jsonl",
        "registry/sources.json",
        "registry/retired-sources.jsonl",
    }
)
MAX_INCREMENTAL_FILES = 128
SEARCH_MAX_FILE_BYTES = 8 * 1024 * 1024
SEARCH_MAX_TOTAL_BYTES = 256 * 1024 * 1024
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
    "性能": ("performance", "优化", "效率"),
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
SEARCH_TRACE_EXCLUDED_LIMIT = 5
SEARCH_TRACE_SCORE_LIMIT = 128
SEARCH_MAX_LIMIT = 100
SEARCH_MAX_QUERY_CHARS = 4096
SEARCH_MAX_FILTER_VALUES = 32
SEARCH_MAX_FILTER_VALUE_CHARS = 256
SEARCH_MAX_CURSOR_CHARS = 2048
SEARCH_AUTHORITY_CANDIDATE_LIMIT = 512
CONTENT_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_IPV4_PATTERN = re.compile(
    r"(?<![0-9])(?:10(?:\.[0-9]{1,3}){3}|192\.168(?:\.[0-9]{1,3}){2}|"
    r"172\.(?:1[6-9]|2[0-9]|3[01])(?:\.[0-9]{1,3}){2})(?::[0-9]{1,5})?(?![0-9])"
)
ARCHIVE_INTENT_TERMS = frozenset(
    {"archive", "archived", "historical", "history", "legacy", "归档", "历史", "旧版"}
)
DEFAULT_SEARCH_EXCLUDED_ROOTS = frozenset(
    {
        ".github",
        "artifacts",
        "indexes",
        "issues",
        "registry",
        "schemas",
        "sources",
        "templates",
        "tools",
    }
)
DEFAULT_SEARCH_EXCLUDED_PATHS = frozenset({"AGENTS.md"})

FileState = Tuple[int, int, int, int, int, str]


class SearchBoundaryError(KnowledgeHubError):
    """A security or resource boundary that must not degrade to repository scan."""


def _item_is_default_searchable(item: Mapping[str, Any]) -> bool:
    """Return whether a registry item belongs to the governed default corpus.

    Registry membership is necessary but not sufficient: control-plane and derived
    files remain out of the user-facing corpus unless the registry opts them in
    explicitly.  ``searchable: false`` always wins.
    """

    searchable = item.get("searchable")
    if searchable is False:
        return False
    if str(item.get("visibility", "")) == "personal-local":
        return False
    try:
        relative = normalize_relpath(str(item.get("path", "")))
    except KnowledgeHubError:
        return False
    if not relative:
        return False
    root_name = relative.split("/", 1)[0]
    is_control = (
        relative in DEFAULT_SEARCH_EXCLUDED_PATHS
        or root_name in DEFAULT_SEARCH_EXCLUDED_ROOTS
    )
    return searchable is True or not is_control


def _governed_items_by_path(
    root: pathlib.Path,
) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {}
    for item in registry_items(root):
        if not _item_is_default_searchable(item):
            continue
        try:
            relative = normalize_relpath(str(item.get("path", "")))
        except KnowledgeHubError as exc:
            raise SearchBoundaryError(str(exc)) from exc
        if pathlib.Path(relative).suffix.lower() not in TEXT_SUFFIXES:
            continue
        result.setdefault(relative, []).append(item)
    duplicates = sorted(path for path, rows in result.items() if len(rows) > 1)
    if duplicates:
        raise SearchBoundaryError(
            "registry contains duplicate searchable path(s): {}".format(
                ", ".join(duplicates[:10])
            )
        )
    return result


def _registered_text_file_records(
    root: pathlib.Path,
    items_by_path: Optional[Mapping[str, Sequence[Mapping[str, Any]]]] = None,
) -> List[Tuple[pathlib.Path, str, os.stat_result]]:
    governed = items_by_path or _governed_items_by_path(root)
    records: List[Tuple[pathlib.Path, str, os.stat_result]] = []
    for relative in sorted(governed):
        path = root / relative
        try:
            file_stat = path.lstat()
        except OSError as exc:
            raise SearchBoundaryError(
                "registered search body is unavailable: {}".format(relative)
            ) from exc
        if path.is_symlink() or not path.is_file():
            raise SearchBoundaryError(
                "registered search body must be a regular non-symlink file: {}".format(
                    relative
                )
            )
        records.append((path, relative, file_stat))
    return records


def _validate_filter_values(name: str, values: Sequence[str]) -> None:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise KnowledgeHubError("{} filter values must be a sequence".format(name))
    if len(values) > SEARCH_MAX_FILTER_VALUES:
        raise KnowledgeHubError(
            "{} filter values exceed {}".format(name, SEARCH_MAX_FILTER_VALUES)
        )
    for value in values:
        text = str(value)
        if not text.strip():
            raise KnowledgeHubError("{} filter values must not be empty".format(name))
        if len(text) > SEARCH_MAX_FILTER_VALUE_CHARS:
            raise KnowledgeHubError(
                "{} filter value exceeds {} characters".format(
                    name, SEARCH_MAX_FILTER_VALUE_CHARS
                )
            )


def _domain_matches(domain: Any, prefix: str) -> bool:
    domain_text = str(domain or "").rstrip("/")
    prefix_text = str(prefix or "").rstrip("/")
    return bool(
        prefix_text
        and (domain_text == prefix_text or domain_text.startswith(prefix_text + "/"))
    )


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
        for name, values in (
            ("source", self.sources),
            ("owner", self.owners),
            ("status", self.statuses),
            ("kind", self.kinds),
            ("domain", self.domains),
            ("source-id", self.source_ids),
        ):
            _validate_filter_values(name, values)
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


def _index_tokens(value: str, maximum: int = 20000) -> List[str]:
    normalized = value.lower()
    tokens: Dict[str, None] = {
        token: None for token in ASCII_TOKEN_PATTERN.findall(normalized)
    }
    for segment in CJK_PATTERN.findall(normalized):
        if len(segment) == 1:
            tokens.setdefault(segment, None)
            continue
        tokens.setdefault(segment, None)
        for width in (2, 3):
            for index in range(max(0, len(segment) - width + 1)):
                tokens.setdefault(segment[index : index + width], None)
    return list(tokens)[:maximum]


def _hash_token_cache_value(cache_key: str, token_text: str) -> str:
    digest = hashlib.sha256()
    digest.update(cache_key.encode("ascii"))
    digest.update(b"\0")
    digest.update(token_text.encode("utf-8"))
    return digest.hexdigest()


class _PersistentTokenCache:
    """Best-effort exact-input token cache; never an authority for search data."""

    def __init__(self, path: pathlib.Path) -> None:
        self.path = path
        self.connection: Optional[sqlite3.Connection] = None
        self.pending: Dict[str, Tuple[str, str]] = {}
        self.pending_bytes = 0
        self.hits = 0
        self.misses = 0
        self.entry_count = 0
        self.status = "ready"
        try:
            ensure_private_directory(path.parent)
            if path.is_symlink():
                raise KnowledgeHubError("token cache must not be a symlink")
            ensure_private_file(path)
            self.connection = sqlite3.connect(str(path))
            self.connection.execute("pragma journal_mode=delete")
            self.connection.execute("pragma synchronous=normal")
            self.connection.execute(
                """
                create table if not exists token_cache (
                    cache_key text primary key,
                    token_text text not null,
                    token_digest text not null
                )
                """
            )
            ensure_private_file(path)
        except (KnowledgeHubError, OSError, sqlite3.Error):
            self._disable()

    def _disable(self) -> None:
        self.status = "degraded"
        if self.connection is not None:
            try:
                self.connection.close()
            except sqlite3.Error:
                pass
        self.connection = None
        self.pending = {}
        self.pending_bytes = 0

    @staticmethod
    def _key(value: str, maximum: int) -> str:
        digest = hashlib.sha256()
        digest.update(str(TOKEN_CACHE_SCHEMA_VERSION).encode("ascii"))
        digest.update(b":")
        digest.update(str(maximum).encode("ascii"))
        digest.update(b"\0")
        digest.update(value.encode("utf-8"))
        return digest.hexdigest()

    def token_text(self, value: str, maximum: int = 20000) -> str:
        cache_key = self._key(value, maximum)
        if self.connection is not None:
            try:
                row = self.connection.execute(
                    "select token_text,token_digest from token_cache where cache_key=?",
                    (cache_key,),
                ).fetchone()
            except sqlite3.Error:
                self._disable()
                row = None
            if row and isinstance(row[0], str) and isinstance(row[1], str):
                token_text = str(row[0])
                expected_digest = _hash_token_cache_value(cache_key, token_text)
                if str(row[1]) == expected_digest:
                    self.hits += 1
                    return token_text
                self.status = "recovered"
                try:
                    self.connection.execute(
                        "delete from token_cache where cache_key=?",
                        (cache_key,),
                    )
                except sqlite3.Error:
                    self._disable()
        self.misses += 1
        token_text = " ".join(_index_tokens(value, maximum))
        token_bytes = len(token_text.encode("utf-8"))
        if (
            self.connection is not None
            and token_bytes <= TOKEN_CACHE_MAX_VALUE_BYTES
            and len(self.pending) < TOKEN_CACHE_MAX_ENTRIES
            and self.pending_bytes + token_bytes <= TOKEN_CACHE_MAX_TOTAL_BYTES
        ):
            if cache_key not in self.pending:
                self.pending[cache_key] = (
                    token_text,
                    _hash_token_cache_value(cache_key, token_text),
                )
                self.pending_bytes += token_bytes
        return token_text

    def _prune(self) -> None:
        if self.connection is None:
            return
        count = int(
            self.connection.execute("select count(*) from token_cache").fetchone()[0]
        )
        if count > TOKEN_CACHE_MAX_ENTRIES:
            self.connection.execute(
                "delete from token_cache where rowid in "
                "(select rowid from token_cache order by rowid limit ?)",
                (count - TOKEN_CACHE_MAX_ENTRIES,),
            )
        total_bytes = int(
            self.connection.execute(
                "select coalesce(sum(length(cast(token_text as blob))), 0) from token_cache"
            ).fetchone()[0]
        )
        while total_bytes > TOKEN_CACHE_MAX_TOTAL_BYTES:
            rows = self.connection.execute(
                "select rowid,length(cast(token_text as blob)) "
                "from token_cache order by rowid limit 256"
            ).fetchall()
            if not rows:
                break
            self.connection.executemany(
                "delete from token_cache where rowid=?",
                ((int(row[0]),) for row in rows),
            )
            total_bytes -= sum(int(row[1]) for row in rows)

    def close(self) -> None:
        if self.connection is None:
            return
        try:
            if self.pending:
                self.connection.executemany(
                    "insert or replace into token_cache(cache_key,token_text,token_digest) "
                    "values(?,?,?)",
                    (
                        (cache_key, value[0], value[1])
                        for cache_key, value in self.pending.items()
                    ),
                )
            self._prune()
            self.entry_count = int(
                self.connection.execute("select count(*) from token_cache").fetchone()[0]
            )
            self.connection.commit()
            self.connection.close()
            self.connection = None
            self.pending = {}
            self.pending_bytes = 0
        except sqlite3.Error:
            connection = self.connection
            if connection is not None:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
            self._disable()

    def stats(self) -> Dict[str, Any]:
        return {
            "token_cache_schema_version": TOKEN_CACHE_SCHEMA_VERSION,
            "token_cache_status": self.status,
            "token_cache_hits": self.hits,
            "token_cache_misses": self.misses,
            "token_cache_entries": self.entry_count,
        }


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
            raw_title = ""
            for line in body[4:marker].splitlines():
                if line.startswith("title:"):
                    raw_title = line.partition(":")[2].strip()
            needs_full_yaml = bool(raw_title and raw_title[0] in "|>*")
            if raw_title and raw_title[0] not in "|>*":
                try:
                    scalar = yaml.safe_load(raw_title)
                    if scalar is not None:
                        return str(scalar)
                except (ValueError, TypeError, yaml.YAMLError):
                    needs_full_yaml = True
            if needs_full_yaml:
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
    candidate = (
        path.resolve(strict=False)
        if path.is_symlink() or not path.is_absolute()
        else path
    )
    candidate_text = os.fspath(candidate)
    for source_name, source_root in roots:
        source_text = os.fspath(source_root)
        source_prefix = source_text if source_text.endswith(os.sep) else source_text + os.sep
        if candidate_text == source_text or candidate_text.startswith(source_prefix):
            result.append(source_name)
    return result


def _signature(
    root: pathlib.Path,
    previous_states: Optional[Mapping[str, FileState]] = None,
    stats: Optional[Dict[str, int]] = None,
) -> Tuple[str, List[pathlib.Path], Dict[str, FileState]]:
    items_by_path = _governed_items_by_path(root)
    document_records = _registered_text_file_records(root, items_by_path)
    paths = [path for path, _, _ in document_records]
    records_by_relative = {
        relative: (path, relative, file_stat)
        for path, relative, file_stat in document_records
    }
    for relative in sorted(FULL_REBUILD_DEPENDENCIES):
        dependency = root / relative
        try:
            dependency_stat = dependency.lstat()
        except OSError as exc:
            raise SearchBoundaryError(
                "search index dependency is unavailable: {}".format(relative)
            ) from exc
        if dependency.is_symlink() or not dependency.is_file():
            raise SearchBoundaryError(
                "search index dependency must be a regular non-symlink file: {}".format(
                    relative
                )
            )
        records_by_relative[relative] = (
            dependency,
            relative,
            dependency_stat,
        )
    records = [records_by_relative[key] for key in sorted(records_by_relative)]
    digest = hashlib.sha256()
    digest.update(str(INDEX_SCHEMA_VERSION).encode("ascii"))
    file_states: Dict[str, FileState] = {}
    total_bytes = 0
    hashed_files = 0
    reused_content_hashes = 0
    for _, relative, file_stat in records:
        if file_stat.st_size > SEARCH_MAX_FILE_BYTES:
            raise SearchBoundaryError(
                "search text file exceeds {} bytes: {}".format(
                    SEARCH_MAX_FILE_BYTES, relative
                )
            )
        total_bytes += file_stat.st_size
        if total_bytes > SEARCH_MAX_TOTAL_BYTES:
            raise SearchBoundaryError(
                "search text corpus exceeds {} bytes".format(
                    SEARCH_MAX_TOTAL_BYTES
                )
            )
        identity = (
            file_stat.st_size,
            file_stat.st_mtime_ns,
            file_stat.st_ctime_ns,
            file_stat.st_dev,
            file_stat.st_ino,
        )
        previous = (previous_states or {}).get(relative)
        if (
            previous is not None
            and previous[:5] == identity
            and CONTENT_SHA256_PATTERN.fullmatch(str(previous[5])) is not None
        ):
            content_sha256 = str(previous[5])
            reused_content_hashes += 1
        else:
            try:
                raw = read_repository_bytes_bounded(
                    root,
                    relative,
                    SEARCH_MAX_FILE_BYTES,
                    "search text file",
                )
                post_read_stat = (root / relative).lstat()
                verification_raw = read_repository_bytes_bounded(
                    root,
                    relative,
                    SEARCH_MAX_FILE_BYTES,
                    "search text file verification",
                )
                verification_stat = (root / relative).lstat()
            except (KnowledgeHubError, OSError) as exc:
                raise SearchBoundaryError(str(exc)) from exc
            post_read_identity = (
                post_read_stat.st_size,
                post_read_stat.st_mtime_ns,
                post_read_stat.st_ctime_ns,
                post_read_stat.st_dev,
                post_read_stat.st_ino,
            )
            verification_identity = (
                verification_stat.st_size,
                verification_stat.st_mtime_ns,
                verification_stat.st_ctime_ns,
                verification_stat.st_dev,
                verification_stat.st_ino,
            )
            if (
                post_read_identity != identity
                or verification_identity != identity
                or verification_raw != raw
            ):
                raise SearchBoundaryError(
                    "search text file changed during signature: {}".format(relative)
                )
            content_sha256 = bytes_sha256(raw)
            hashed_files += 1
        file_states[relative] = identity + (content_sha256,)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content_sha256.encode("ascii"))
        digest.update(b"\n")
    if stats is not None:
        stats.update(
            {
                "hashed_files": hashed_files,
                "reused_content_hashes": reused_content_hashes,
                "signature_files": len(records),
            }
        )
    return digest.hexdigest(), paths, file_states


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


def _matched_query_terms(
    terms: Sequence[str],
    body: str,
    item: Mapping[str, Any],
) -> List[str]:
    """Return query terms matched by a row without exposing matched body text."""

    combined = (_metadata_haystack(item) if item else "") + "\n" + body.lower()
    return [term for term in terms if _term_matches(term, combined)]


def _archive_intent(query: str) -> bool:
    lowered = query.lower()
    return any(_term_matches(term, lowered) for term in ARCHIVE_INTENT_TERMS)


def _historical_result(item: Mapping[str, Any], relative: str) -> bool:
    return str(item.get("status", "")) in {
        "archived",
        "superseded",
        "rejected",
    } or "/archive/" in relative


def _redact_internal_endpoints(value: str) -> Tuple[str, bool]:
    redacted = PRIVATE_IPV4_PATTERN.sub("[内部端点已脱敏]", value)
    return redacted, redacted != value


def _cursor_fingerprint(query: str, filters: SearchFilters) -> str:
    payload = {
        "query": query,
        "filters": {
            "source": list(filters.sources),
            "owner": list(filters.owners),
            "status": list(filters.statuses),
            "kind": list(filters.kinds),
            "domain": list(filters.domains),
            "source_id": list(filters.source_ids),
        },
    }
    return hashlib.sha256(compact_json(payload).encode("utf-8")).hexdigest()


def _encode_cursor(signature: str, fingerprint: str, offset: int) -> str:
    raw = compact_json(
        {
            "schema_version": 1,
            "signature": signature,
            "fingerprint": fingerprint,
            "offset": offset,
        }
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(value: str, signature: str, fingerprint: str) -> int:
    if len(value) > SEARCH_MAX_CURSOR_CHARS:
        raise KnowledgeHubError(
            "cursor exceeds {} characters".format(SEARCH_MAX_CURSOR_CHARS)
        )
    try:
        padding = "=" * (-len(value) % 4)
        payload = json.loads(
            base64.b64decode(value + padding, altchars=b"-_", validate=True)
        )
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("cursor is invalid") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise KnowledgeHubError("cursor is invalid")
    if payload.get("signature") != signature:
        raise KnowledgeHubError("cursor is stale for the current search corpus")
    if payload.get("fingerprint") != fingerprint:
        raise KnowledgeHubError("cursor does not match the query and filters")
    offset = payload.get("offset")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise KnowledgeHubError("cursor offset is invalid")
    return offset


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
    if filters.domains and not any(_domain_matches(item.get("domain", ""), prefix) for prefix in filters.domains):
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
    if filters.domains and not any(_domain_matches(item.get("domain", ""), prefix) for prefix in filters.domains):
        return "domain"
    if filters.source_ids and source_id(item) not in filters.source_ids:
        return "source-id"
    return ""


def _scan_candidates(root: pathlib.Path) -> List[Dict[str, Any]]:
    items_by_path = _governed_items_by_path(root)
    source_roots = _source_roots(root)
    rows: List[Dict[str, Any]] = []
    total_bytes = 0
    for path, relative, file_stat in _registered_text_file_records(
        root, items_by_path
    ):
        try:
            file_size = file_stat.st_size
            if file_size > SEARCH_MAX_FILE_BYTES:
                raise SearchBoundaryError(
                    "search text file exceeds {} bytes: {}".format(
                        SEARCH_MAX_FILE_BYTES, relative
                    )
                )
            total_bytes += file_size
            if total_bytes > SEARCH_MAX_TOTAL_BYTES:
                raise SearchBoundaryError(
                    "search text corpus exceeds {} bytes".format(
                        SEARCH_MAX_TOTAL_BYTES
                    )
                )
            raw = read_repository_bytes_bounded(
                root,
                relative,
                SEARCH_MAX_FILE_BYTES,
                "search text file",
            )
            body = raw.decode("utf-8", errors="ignore")
        except SearchBoundaryError:
            raise
        except KnowledgeHubError as exc:
            raise SearchBoundaryError(str(exc)) from exc
        except (OSError, ValueError):
            continue
        for item in items_by_path.get(relative, []):
            rows.append(
                {
                    "path": relative,
                    "suffix": path.suffix.lower(),
                    "physical_sources": compact_json(_physical_sources(path, source_roots)),
                    "item_json": compact_json(item),
                    "indexed_title": _indexed_title(relative, body, item),
                    "body": body,
                    "fts_rank": 0.0,
                }
            )
    return rows


def _validate_retrieval_contract(
    root: pathlib.Path,
    payload: Mapping[str, Any],
) -> Dict[str, Any]:
    """Validate the public search contract before a successful return."""

    catalog_path = root / "schemas" / "catalog.json"
    if catalog_path.is_file():
        validation = validate_instance(root, "retrieval-result-v3", payload)
        if validation.get("status") != "pass":
            details = "; ".join(
                "{path}: {message}".format(**row)
                for row in validation.get("errors", [])[:5]
            )
            raise KnowledgeHubError(
                "retrieval result violates retrieval-result-v3: {}".format(details)
            )
        return {
            "status": "pass",
            "contract_id": "retrieval-result-v3",
            "error_count": 0,
        }

    required_payload = {
        "schema_version",
        "status",
        "query",
        "index",
        "results",
        "pagination",
        "search_trace",
        "zero_hit",
        "timing",
    }
    missing_payload = sorted(required_payload - set(payload))
    result_errors: List[str] = []
    for index, result in enumerate(payload.get("results", [])):
        required_result = {"id", "path", "status", "score", "why_selected"}
        missing = sorted(required_result - set(result))
        if missing:
            result_errors.append(
                "results[{}] missing {}".format(index, ", ".join(missing))
            )
    if missing_payload or result_errors:
        fallback_details: List[str] = []
        if missing_payload:
            fallback_details.append(
                "payload missing {}".format(", ".join(missing_payload))
            )
        fallback_details.extend(result_errors[:5])
        raise KnowledgeHubError(
            "retrieval result violates fallback contract: {}".format(
                "; ".join(fallback_details)
            )
        )
    return {
        "status": "pass",
        "contract_id": "retrieval-result-v3-essential-fields",
        "error_count": 0,
    }


def _preview(
    body: str,
    terms: Sequence[str],
    item: Mapping[str, Any],
) -> Tuple[int, str, bool, bool]:
    lower = body.lower()
    positions = [(lower.find(term), term) for term in terms if lower.find(term) >= 0]
    if not positions:
        grams = [gram for term in terms for gram in _cjk_ngrams(term) if len(gram) >= 2]
        positions = [(lower.find(gram), gram) for gram in grams if lower.find(gram) >= 0]
    if not positions:
        summary = item.get("summary_zh") or item.get("title") or item.get("id", "")
        preview, redacted = _redact_internal_endpoints(
            "registry metadata: {}".format(summary)[:240]
        )
        return 1, preview, False, redacted
    index, _ = min(positions, key=lambda value: value[0])
    line_no = lower[:index].count("\n") + 1
    lines = body.splitlines()
    line = lines[line_no - 1].strip()[:240] if lines and line_no <= len(lines) else ""
    preview, redacted = _redact_internal_endpoints(line)
    return line_no, preview, True, redacted


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
    matched_terms = _matched_query_terms(terms, body, item)
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
    for field_text, weight, reason in ((tags, 45, "tag-tokens"), (summary, 40, "summary-tokens"), (path_text, 30, "path-tokens")):
        hits = sum(1 for term in terms if _term_matches(term, field_text))
        if hits:
            score += hits * weight
            reasons.append(reason)
    distinctive_terms = [
        term
        for term in terms
        if term not in GENERIC_QUERY_TERMS
        and (
            len(term) >= 3
            or len("".join(CJK_PATTERN.findall(term))) >= 2
        )
    ]
    metadata_fields = "\n".join((title, item_id, tags, summary, path_text))
    matched_distinctive_anywhere = [
        term
        for term in distinctive_terms
        if _term_matches(term, metadata_fields) or _term_matches(term, body_haystack)
    ]
    matched_distinctive_metadata = [
        term for term in distinctive_terms if _term_matches(term, metadata_fields)
    ]
    exact_query_match = bool(
        normalized_query
        and (
            normalized_query in metadata_fields
            or normalized_query in body_haystack
        )
    )
    if len(distinctive_terms) >= 2 and not exact_query_match:
        minimum_distinctive = (
            2
            if len(distinctive_terms) == 2
            else max(2, int(math.ceil(len(distinctive_terms) * 0.5)))
        )
        if (
            len(matched_distinctive_anywhere) < minimum_distinctive
            or not matched_distinctive_metadata
        ):
            return None
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
    metadata_term_match = any(
        _term_matches(term, metadata_fields) for term in terms
    )
    if relative == "README.md" and not metadata_term_match:
        score -= 160
        reasons.append("root-body-only-penalty")
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
    if "project-readiness" in tags or "template-projection" in tags:
        score -= 180
        reasons.append("template-projection-penalty")
    if _historical_result(item, relative) and not _archive_intent(query):
        reasons.append("historical-fallback-lane")
    return int(score), reasons, coverage


def search(
    root: pathlib.Path,
    query: str,
    limit: int = 20,
    filters: Optional[SearchFilters] = None,
    rebuild_index: bool = False,
    search_index: Optional[SearchIndex] = None,
    cursor: str = "",
) -> Dict[str, Any]:
    started = time.monotonic()
    if not 1 <= limit <= SEARCH_MAX_LIMIT:
        raise KnowledgeHubError(
            "--limit must be between 1 and {}".format(SEARCH_MAX_LIMIT)
        )
    if not query.strip():
        raise KnowledgeHubError("query must not be empty")
    if len(query) > SEARCH_MAX_QUERY_CHARS:
        raise KnowledgeHubError(
            "query exceeds {} characters".format(SEARCH_MAX_QUERY_CHARS)
        )
    filters = filters or SearchFilters()
    filters.validate()
    validated_at = time.monotonic()
    index = search_index or SearchIndex(root)
    base_candidate_limit = int(getattr(index, "CANDIDATE_LIMIT", 256))
    candidate_limit = (
        int(getattr(index, "STRUCTURED_CANDIDATE_LIMIT", 4096))
        if filters.structured
        else base_candidate_limit
    )
    ensure_started = time.monotonic()
    index_ready: Optional[float] = None
    candidate_started = ensure_started
    try:
        index_state = index.ensure(force=rebuild_index)
        index_ready = time.monotonic()
        candidate_started = index_ready
        indexed_rows: Sequence[Mapping[str, Any]] = index.candidates(
            query,
            candidate_limit=candidate_limit,
        )
        authority_method = getattr(index, "authority_candidates", None)
        authority_rows = (
            authority_method(query, SEARCH_AUTHORITY_CANDIDATE_LIMIT)
            if callable(authority_method)
            else []
        )
        combined_rows: List[Mapping[str, Any]] = []
        seen_document_keys: Set[str] = set()
        for row in list(authority_rows) + list(indexed_rows):
            document_key = str(row.get("doc_key", "")) or "{}#{}".format(
                row.get("path", ""),
                row.get("item_json", ""),
            )
            if document_key in seen_document_keys:
                continue
            seen_document_keys.add(document_key)
            combined_rows.append(row)
        indexed_rows = combined_rows
        index_state["authority_candidate_count"] = len(authority_rows)
        candidate_ready = time.monotonic()
    except SearchBoundaryError:
        raise
    except (KnowledgeHubError, OSError, sqlite3.Error) as exc:
        failed_at = time.monotonic()
        if index_ready is None:
            index_ready = failed_at
        candidate_started = index_ready
        index_state = {
            "state": "fallback",
            "mode": "repository-scan-fallback",
            "fresh": False,
            "rebuilt": False,
            "reason": str(exc),
        }
        indexed_rows = _scan_candidates(root)
        index_state["authority_candidate_count"] = 0
        candidate_ready = time.monotonic()
    ranking_started = candidate_ready
    index_state["candidate_count"] = len(indexed_rows)
    index_state["candidate_limit"] = (
        candidate_limit if index_state.get("mode") == "local-index" else None
    )
    terms = query_terms(query)
    candidates: List[Dict[str, Any]] = []
    filtered_reasons: Counter = Counter()
    excluded_registered_total = 0
    excluded_registered: List[Dict[str, Any]] = []
    for row in indexed_rows:
        try:
            item = json.loads(row["item_json"])
            physical_sources = json.loads(row["physical_sources"])
        except (json.JSONDecodeError, TypeError):
            continue
        if not item:
            raise SearchBoundaryError(
                "search index contains an unregistered document: {}".format(
                    row.get("path", "")
                )
            )
        filter_reason = _filter_reason(item, physical_sources, filters)
        if filter_reason:
            filtered_reasons[filter_reason] += 1
            if item and item.get("visibility") != "personal-local":
                matched_terms = _matched_query_terms(terms, str(row["body"]), item)
                if matched_terms:
                    excluded_registered_total += 1
                    if len(excluded_registered) < SEARCH_TRACE_SCORE_LIMIT:
                        scored_hidden = _score(
                            str(row["path"]),
                            str(row["suffix"]),
                            str(row["body"]),
                            item,
                            str(row["indexed_title"]),
                            terms,
                            query,
                        )
                        if scored_hidden is not None:
                            hidden_score, _, hidden_coverage = scored_hidden
                            excluded_registered.append(
                                {
                                    "id": str(item.get("id", "")),
                                    "path": str(item.get("path", row["path"])),
                                    "kind": str(item.get("kind", "")),
                                    "status": str(item.get("status", "")),
                                    "domain": str(item.get("domain", "")),
                                    "owner": str(item.get("owner", "")),
                                    "excluded_by": filter_reason,
                                    "matched_terms": matched_terms,
                                    "query_coverage": round(hidden_coverage, 3),
                                    "score": hidden_score,
                                }
                            )
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
        line_no, preview, body_match, preview_redacted = _preview(
            str(row["body"]),
            terms,
            item,
        )
        selected_source = "knowledge-hub"
        if filters.sources:
            selected_source = next((value for value in filters.sources if value in physical_sources), "knowledge-hub")
        result: Dict[str, Any] = {
            "source": selected_source,
            "path": str(row["path"]),
            "line": line_no,
            "preview": preview,
            "preview_redacted": preview_redacted,
            "score": score,
            "match": "body-and-metadata" if body_match and item else "body" if body_match else "registry-metadata",
            "match_kind": reasons[0],
            "why_selected": reasons,
            "query_coverage": round(coverage, 3),
            "evidence_strength": item.get("evidence_strength", ""),
            "manual_validation_pending": bool(item.get("manual_validation_pending", False)),
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
        candidates.append(result)
    candidates.sort(key=lambda value: (-int(value["score"]), str(value.get("path", "")), str(value.get("item_id", ""))))
    deduplicated: List[Dict[str, Any]] = []
    seen_paths: Set[str] = set()
    for candidate in candidates:
        candidate_path = str(candidate.get("path", ""))
        if candidate_path in seen_paths:
            continue
        seen_paths.add(candidate_path)
        deduplicated.append(candidate)
    candidates = deduplicated
    if not _archive_intent(query):
        current_candidates = [
            row
            for row in candidates
            if not _historical_result(row, str(row.get("path", "")))
        ]
        historical_candidates = [
            row
            for row in candidates
            if _historical_result(row, str(row.get("path", "")))
        ]
        current_ceiling = max(
            (int(row.get("score", 0)) for row in current_candidates),
            default=-10**9,
        )
        dominant_historical = [
            row
            for row in historical_candidates
            if int(row.get("score", 0)) >= current_ceiling + 400
        ]
        fallback_historical = [
            row for row in historical_candidates if row not in dominant_historical
        ]
        for row in dominant_historical:
            row["why_selected"] = list(row.get("why_selected", [])) + [
                "historical-dominant-match"
            ]
        candidates = dominant_historical + current_candidates + fallback_historical
    cursor_fingerprint = _cursor_fingerprint(query, filters)
    index_signature = str(index_state.get("signature", ""))
    if cursor and index_state.get("mode") != "local-index":
        raise KnowledgeHubError(
            "cursor pagination requires the governed local index"
        )
    offset = (
        _decode_cursor(cursor, index_signature, cursor_fingerprint)
        if cursor
        else 0
    )
    results = candidates[offset : offset + limit]
    next_offset = offset + len(results)
    has_more = next_offset < len(candidates)
    next_cursor = (
        _encode_cursor(index_signature, cursor_fingerprint, next_offset)
        if has_more and index_signature
        else ""
    )
    excluded_registered.sort(
        key=lambda value: (
            -int(value["score"]),
            str(value.get("path", "")),
            str(value.get("id", "")),
        )
    )
    excluded_slice = [
        {key: value for key, value in row.items() if key != "score"}
        for row in excluded_registered[:SEARCH_TRACE_EXCLUDED_LIMIT]
    ]
    filter_payload = {
        "source": list(filters.sources),
        "owner": list(filters.owners),
        "status": list(filters.statuses),
        "kind": list(filters.kinds),
        "kind_normalized": filters.normalized_kinds,
        "domain": list(filters.domains),
        "source_id": list(filters.source_ids),
    }
    retry_queries = []
    if not results and excluded_slice:
        retry_queries.append(
            {
                "query": query,
                "drop_filters": sorted(
                    {str(row["excluded_by"]) for row in excluded_slice}
                ),
            }
        )
    search_trace = {
        "schema_version": "knowledge-hub.search-trace.v1",
        "query_terms": terms,
        "applied_filters": filter_payload,
        "candidate_pool": {
            "indexed": len(indexed_rows),
            "after_filters": len(candidates),
            "returned": len(results),
        },
        "excluded_by_filters_total": excluded_registered_total,
        "excluded_by_filters": excluded_slice,
        "excluded_truncated": excluded_registered_total > len(excluded_slice),
        "retry_queries": retry_queries,
    }
    zero_hit = {
        "is_zero_hit": not bool(results),
        "reason": ""
        if results
        else "matching registered items were excluded by structured filters"
        if excluded_registered_total
        else "no indexed document matched the query and structured filters",
        "degraded_terms": [],
        "filtered_by_reason": dict(sorted(filtered_reasons.items())),
        "suggestions": [] if results else [
            "remove one structured filter",
            "use a project/repository alias from registry/project-routes.json",
            "try a shorter domain term or exact item id",
        ],
    }
    finished = time.monotonic()
    elapsed_ms = round((finished - started) * 1000, 2)
    timing = {
        "validation_ms": round((validated_at - started) * 1000, 2),
        "index_ensure_ms": round((index_ready - ensure_started) * 1000, 2),
        "candidate_query_ms": round((candidate_ready - candidate_started) * 1000, 2),
        "ranking_ms": round((finished - ranking_started) * 1000, 2),
        "total_ms": elapsed_ms,
    }
    payload: Dict[str, Any] = {
        "schema_version": 3,
        "status": "pass" if results else "zero-hit",
        "query": query,
        "query_terms": terms,
        "count": len(results),
        "total_matches": len(candidates),
        "ranking": "sqlite-fts5-registry-canonical-distinctive-terms-v3",
        "filters": filter_payload,
        "index": index_state,
        "filter_diagnostics": {
            "filtered_count": sum(filtered_reasons.values()),
            "by_reason": dict(sorted(filtered_reasons.items())),
        },
        "latency_ms": elapsed_ms,
        "timing": timing,
        "results": results,
        "pagination": {
            "offset": offset,
            "limit": limit,
            "returned": len(results),
            "total": len(candidates),
            "has_more": has_more,
            "next_cursor": next_cursor,
            "signature_bound": True,
        },
        "search_trace": search_trace,
        "zero_hit": zero_hit,
    }
    payload["schema_validation"] = _validate_retrieval_contract(root, payload)
    contract_finished = time.monotonic()
    contract_elapsed_ms = round((contract_finished - started) * 1000, 2)
    payload["latency_ms"] = contract_elapsed_ms
    timing["total_ms"] = contract_elapsed_ms
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
        "performance_contract": PERFORMANCE_CONTRACT,
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
        "index_build_ms": (payload.get("index") or {}).get("build_duration_ms", 0),
        "token_cache_status": (payload.get("index") or {}).get("token_cache_status", ""),
        "token_cache_hits": (payload.get("index") or {}).get("token_cache_hits", 0),
        "token_cache_misses": (payload.get("index") or {}).get("token_cache_misses", 0),
        "stage_timing": dict(payload.get("timing") or {}),
        "raw_query_stored": False,
    }
    path = root / ".cache/knowledge-hub/search-telemetry.jsonl"
    return append_optional_telemetry(path, row, enabled=enabled)
