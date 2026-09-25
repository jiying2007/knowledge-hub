"""Shared FTS-backed candidate discovery for governed retrieval lanes."""

from __future__ import annotations

import json
import pathlib
import sqlite3
from typing import Any, Dict, Mapping, Set, Tuple

from .common import KnowledgeHubError
from .search_core import SearchBoundaryError
from .search_index import SearchIndex

MAX_LEXICAL_CANDIDATES = 4096
MAX_DIAGNOSTIC_CHARS = 512


def lexical_candidate_set(
    root: pathlib.Path,
    query: str,
    allowed_ids: Set[str],
) -> Tuple[Set[str], Dict[str, Any]]:
    """Return FTS candidates without ever widening caller eligibility."""

    if not isinstance(allowed_ids, set):
        raise KnowledgeHubError("allowed_ids must be a set")
    if len(allowed_ids) > 5000:
        raise KnowledgeHubError("authorized lexical corpus exceeds explicit budget")
    if not allowed_ids:
        return set(), {
            "mode": "fts-index",
            "state": "empty-authorized-corpus",
            "indexed_candidate_count": 0,
            "selected_candidate_count": 0,
            "fallback": False,
        }

    index = SearchIndex(root)
    try:
        state = index.ensure()
        rows = list(index.authority_candidates(query)) + list(
            index.candidates(query, candidate_limit=MAX_LEXICAL_CANDIDATES)
        )
    except SearchBoundaryError:
        raise
    except (KnowledgeHubError, OSError, sqlite3.Error, ValueError) as exc:
        return set(allowed_ids), {
            "mode": "authorized-scan-fallback",
            "state": "degraded",
            "indexed_candidate_count": 0,
            "selected_candidate_count": len(allowed_ids),
            "fallback": True,
            "reason": str(exc)[:MAX_DIAGNOSTIC_CHARS],
        }

    selected: Set[str] = set()
    seen_rows = 0
    for row in rows:
        seen_rows += 1
        if seen_rows > MAX_LEXICAL_CANDIDATES * 2:
            raise SearchBoundaryError("FTS candidate stream exceeds explicit budget")
        try:
            item = json.loads(row.get("item_json", ""))
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(item, Mapping):
            continue
        item_id = str(item.get("id", ""))
        if item_id in allowed_ids:
            selected.add(item_id)
    return selected, {
        "mode": "fts-index",
        "state": str(state.get("state", "unknown")),
        "indexed_candidate_count": seen_rows,
        "selected_candidate_count": len(selected),
        "fallback": False,
        "index_fresh": bool(state.get("fresh", False)),
        "index_signature": str(state.get("signature", "")),
    }
