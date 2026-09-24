"""Bound SQLite candidate payloads before loading bodies into Python."""

from __future__ import annotations

import math
import sqlite3
from typing import Any, Dict, List

from .search_core import SEARCH_MAX_FILE_BYTES, SEARCH_MAX_TOTAL_BYTES, SearchBoundaryError

MAX_CANDIDATES = 4096
MAX_METADATA_BYTES = 1024 * 1024
BODY_BATCH_SIZE = 32


def _candidate_headers(
    connection: sqlite3.Connection, expression: str, limit: int,
    normalized_query: str, authority_only: bool,
) -> List[sqlite3.Row]:
    condition = ""
    parameters: List[Any] = [expression]
    if authority_only:
        condition = """and (
            d.path = 'README.md'
            or d.path like 'projects/%/current/%'
            or d.item_json like '%"status":"active"%'
            or lower(documents_fts.title) = ?
            or lower(documents_fts.item_id) = ?
            or lower(d.path) = ?
        )"""
        parameters.extend([normalized_query] * 3)
    parameters.append(limit)
    sql = """select d.id,
        length(cast(d.body as blob)) as body_bytes,
        length(cast(d.doc_key as blob)) + length(cast(d.path as blob))
        + length(cast(d.suffix as blob)) + length(cast(d.physical_sources as blob))
        + length(cast(d.item_json as blob)) + length(cast(d.indexed_title as blob)) as metadata_bytes,
        bm25(documents_fts, 1.2, 1.1, 0.9, 0.8, 0.5, 0.25, 0.35) as fts_rank
        from documents_fts join documents d on d.id = documents_fts.rowid
        where documents_fts match ? {} order by fts_rank, d.id limit ?""".format(condition)
    return connection.execute(sql, parameters).fetchall()


def _validate_headers(headers: List[sqlite3.Row], limit: int) -> None:
    if len(headers) > limit:
        raise SearchBoundaryError("SQLite candidate count exceeds budget")
    total = 0
    for header in headers:
        for field, maximum in (("body_bytes", SEARCH_MAX_FILE_BYTES), ("metadata_bytes", MAX_METADATA_BYTES)):
            value = header[field]
            if type(value) is not int or not 0 <= value <= maximum:
                raise SearchBoundaryError("SQLite candidate {} exceeds byte budget".format(field))
            total += value
        if total > SEARCH_MAX_TOTAL_BYTES:
            raise SearchBoundaryError("SQLite candidate payload exceeds byte budget")
        rank = header["fts_rank"]
        if type(rank) not in (int, float) or not math.isfinite(rank):
            raise SearchBoundaryError("SQLite candidate rank must be finite")


def read_candidate_payloads(
    connection: sqlite3.Connection, expression: str, candidate_limit: int,
    *, normalized_query: str = "", authority_only: bool = False,
) -> List[Dict[str, Any]]:
    """Use one read snapshot; SQLite faults propagate to the visible scan fallback.

    The caller owns and closes a fresh connection with sqlite3.Row row_factory.
    Resource-boundary failures must not fall back to an unbounded SQL scan.
    """
    if type(candidate_limit) is not int or not 1 <= candidate_limit <= MAX_CANDIDATES:
        raise SearchBoundaryError("SQLite candidate limit must be between 1 and 4096")
    connection.execute("begin")
    headers = _candidate_headers(connection, expression, candidate_limit, normalized_query, authority_only)
    _validate_headers(headers, candidate_limit)
    result: List[Dict[str, Any]] = []
    for offset in range(0, len(headers), BODY_BATCH_SIZE):
        batch = headers[offset:offset + BODY_BATCH_SIZE]
        ids = [header["id"] for header in batch]
        placeholders = ",".join("?" for _ in ids)
        rows = connection.execute(
            "select * from documents where id in ({})".format(placeholders), ids,
        ).fetchall()
        by_id = {row["id"]: dict(row) for row in rows}
        if len(by_id) != len(ids):
            raise SearchBoundaryError("SQLite candidate snapshot is inconsistent")
        for header in batch:
            row = by_id[header["id"]]
            row["fts_rank"] = header["fts_rank"]
            result.append(row)
    return result
