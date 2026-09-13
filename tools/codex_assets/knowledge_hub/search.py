"""Stable compatibility facade for cached, explainable Knowledge Hub search."""

from __future__ import annotations

import sys as _sys
import types as _types

from . import search_core as _core
from . import search_index as _index
from . import search_query as _query
from . import search_query_support as _query_support

_IMPLEMENTATIONS = (_core, _index, _query_support, _query)

# Preserve the broad historical module surface, including imported helpers used
# by tests and callers for dependency injection. Explicit aliases below keep
# statically imported public/private definitions visible to mypy as well.
for _module in _IMPLEMENTATIONS:
    for _name, _value in vars(_module).items():
        if not _name.startswith("__"):
            globals().setdefault(_name, _value)

ARCHIVE_INTENT_TERMS = _core.ARCHIVE_INTENT_TERMS
ASCII_TOKEN_PATTERN = _core.ASCII_TOKEN_PATTERN
CJK_PATTERN = _core.CJK_PATTERN
CONTENT_SHA256_PATTERN = _core.CONTENT_SHA256_PATTERN
DEFAULT_SEARCH_EXCLUDED_PATHS = _core.DEFAULT_SEARCH_EXCLUDED_PATHS
DEFAULT_SEARCH_EXCLUDED_ROOTS = _core.DEFAULT_SEARCH_EXCLUDED_ROOTS
FULL_REBUILD_DEPENDENCIES = _core.FULL_REBUILD_DEPENDENCIES
FileState = _core.FileState
GENERIC_QUERY_TERMS = _core.GENERIC_QUERY_TERMS
INDEX_SCHEMA_VERSION = _core.INDEX_SCHEMA_VERSION
KIND_ALIASES = _core.KIND_ALIASES
MAX_INCREMENTAL_FILES = _core.MAX_INCREMENTAL_FILES
QUERY_PATTERN = _core.QUERY_PATTERN
SEARCH_AUTHORITY_CANDIDATE_LIMIT = _core.SEARCH_AUTHORITY_CANDIDATE_LIMIT
SEARCH_MAX_CURSOR_CHARS = _core.SEARCH_MAX_CURSOR_CHARS
SEARCH_MAX_FILE_BYTES = _core.SEARCH_MAX_FILE_BYTES
SEARCH_MAX_FILTER_VALUES = _core.SEARCH_MAX_FILTER_VALUES
SEARCH_MAX_FILTER_VALUE_CHARS = _core.SEARCH_MAX_FILTER_VALUE_CHARS
SEARCH_MAX_LIMIT = _core.SEARCH_MAX_LIMIT
SEARCH_MAX_QUERY_CHARS = _core.SEARCH_MAX_QUERY_CHARS
SEARCH_MAX_TOTAL_BYTES = _core.SEARCH_MAX_TOTAL_BYTES
SEARCH_TRACE_EXCLUDED_LIMIT = _core.SEARCH_TRACE_EXCLUDED_LIMIT
SEARCH_TRACE_SCORE_LIMIT = _core.SEARCH_TRACE_SCORE_LIMIT
SYNONYMS = _core.SYNONYMS
SearchBoundaryError = _core.SearchBoundaryError
SearchFilters = _core.SearchFilters
SearchIndex = _index.SearchIndex
TOKEN_CACHE_MAX_ENTRIES = _core.TOKEN_CACHE_MAX_ENTRIES
TOKEN_CACHE_MAX_TOTAL_BYTES = _core.TOKEN_CACHE_MAX_TOTAL_BYTES
TOKEN_CACHE_MAX_VALUE_BYTES = _core.TOKEN_CACHE_MAX_VALUE_BYTES
TOKEN_CACHE_SCHEMA_VERSION = _core.TOKEN_CACHE_SCHEMA_VERSION
_PersistentTokenCache = _core._PersistentTokenCache
_archive_intent = _query_support._archive_intent
_cjk_ngrams = _core._cjk_ngrams
_cursor_fingerprint = _query_support._cursor_fingerprint
_decode_cursor = _query_support._decode_cursor
_domain_matches = _core._domain_matches
_encode_cursor = _query_support._encode_cursor
_filter_reason = _query_support._filter_reason
_filters_match = _query_support._filters_match
_governed_items_by_path = _core._governed_items_by_path
_hash_token_cache_value = _core._hash_token_cache_value
_index_tokens = _core._index_tokens
_indexed_title = _core._indexed_title
_item_is_default_searchable = _core._item_is_default_searchable
_matched_query_terms = _query_support._matched_query_terms
_metadata_haystack = _core._metadata_haystack
_physical_sources = _core._physical_sources
_preview = _query_support._preview
_registered_text_file_records = _core._registered_text_file_records
_scan_candidates = _query_support._scan_candidates
_score = _query_support._score
_signature = _core._signature
_source_roots = _core._source_roots
_term_matches = _query_support._term_matches
_term_variants = _core._term_variants
_validate_filter_values = _core._validate_filter_values
_validate_retrieval_contract = _query_support._validate_retrieval_contract
query_terms = _core.query_terms
record_search_telemetry = _query.record_search_telemetry
search = _query.search
search_tokens = _core.search_tokens

class _SearchFacadeModule(_types.ModuleType):
    """Propagate facade monkeypatches to implementation-module globals."""

    def __setattr__(self, name: str, value: object) -> None:
        _types.ModuleType.__setattr__(self, name, value)
        if name.startswith("__"):
            return
        for module in _IMPLEMENTATIONS:
            if hasattr(module, name):
                setattr(module, name, value)


_sys.modules[__name__].__class__ = _SearchFacadeModule
