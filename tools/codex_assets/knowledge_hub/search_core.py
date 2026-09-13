"""Core corpus, token, and cache primitives for Knowledge Hub search."""

from __future__ import annotations

import hashlib
import os
import pathlib
import re
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple
import yaml
from .common import KnowledgeHubError, TEXT_SUFFIXES, bytes_sha256, ensure_private_directory, ensure_private_file, load_json, load_jsonl, normalize_relpath, read_repository_bytes_bounded, registry_items, source_id
from .model import ITEM_KINDS, ITEM_STATUSES

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
