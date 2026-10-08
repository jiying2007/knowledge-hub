"""Read lexical and authority lanes with one snapshot and unique body reads."""

from typing import Any, Dict, List, Tuple

from .search_candidate_io import (
    MAX_CANDIDATES, _candidate_headers, _validate_headers,
)
from .search_core import SearchBoundaryError


def read_candidate_lanes(connection, expression: str, normalized: str,
                         lexical_limit: int, authority_limit: int) -> Tuple[List[Dict[str, Any]], int]:
    for limit in (lexical_limit, authority_limit):
        if type(limit) is not int or not 1 <= limit <= MAX_CANDIDATES:
            raise SearchBoundaryError('SQLite candidate limit must be between 1 and 4096')
    connection.execute('begin')
    lexical = _candidate_headers(connection, expression, lexical_limit, normalized, False)
    authority = _candidate_headers(connection, expression, authority_limit, normalized, True)
    _validate_headers(lexical, lexical_limit)
    _validate_headers(authority, authority_limit)
    headers, seen = [], set()
    for header in authority + lexical:
        if header['id'] not in seen:
            seen.add(header['id'])
            headers.append(header)
    _validate_headers(headers, lexical_limit + authority_limit)
    result = []
    for offset in range(0, len(headers), 32):
        batch = headers[offset:offset + 32]
        ids = [header['id'] for header in batch]
        rows = connection.execute(
            """select * from documents where id in (
                ?,?,?,?,?,?,?,?, ?,?,?,?,?,?,?,?,
                ?,?,?,?,?,?,?,?, ?,?,?,?,?,?,?,?
            )""",
            ids + [None] * (32 - len(ids)),
        ).fetchall()
        by_id = {row['id']:dict(row) for row in rows}
        if len(by_id) != len(ids):
            raise SearchBoundaryError('SQLite candidate snapshot is inconsistent')
        for header in batch:
            row = by_id[header['id']]
            row['fts_rank'] = header['fts_rank']
            result.append(row)
    return result, len(authority)
