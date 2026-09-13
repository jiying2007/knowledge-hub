"""Public query execution and telemetry for Knowledge Hub search."""

from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import time
from collections import Counter
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set
from .common import KnowledgeHubError, source_id, utc_timestamp
from .retrieval_telemetry import IMPLEMENTATION_GENERATION, INTERACTION_CONTRACT, INTERACTIVE_TELEMETRY_SCHEMA_VERSION, PERFORMANCE_CONTRACT, append_optional_telemetry, make_interaction_id
from .search_ranking import is_historical_result as _historical_result
from .search_core import (
    SEARCH_AUTHORITY_CANDIDATE_LIMIT,
    SEARCH_MAX_LIMIT,
    SEARCH_MAX_QUERY_CHARS,
    SEARCH_TRACE_EXCLUDED_LIMIT,
    SEARCH_TRACE_SCORE_LIMIT,
    SearchBoundaryError,
    SearchFilters,
    query_terms,
)
from .search_index import SearchIndex
from .search_query_support import (
    _archive_intent,
    _cursor_fingerprint,
    _decode_cursor,
    _encode_cursor,
    _filter_reason,
    _matched_query_terms,
    _preview,
    _scan_candidates,
    _score,
    _validate_retrieval_contract,
)

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
        "implementation_generation": IMPLEMENTATION_GENERATION,
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
