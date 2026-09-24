"""Use real SQLite FTS5 to verify metadata-first bounded candidate loading."""

import json
import sqlite3

import pytest

from tools.codex_assets.knowledge_hub import search_candidate_io as candidate_io
from tools.codex_assets.knowledge_hub.search_core import SearchBoundaryError
from tools.codex_assets.knowledge_hub.search_index import SearchIndex


def _database(path, count=3):
    with sqlite3.connect(str(path)) as connection:
        connection.executescript("""
            create table documents (
                id integer primary key, doc_key text, path text, suffix text,
                physical_sources text, item_json text, indexed_title text, body text
            );
            create virtual table documents_fts using fts5(
                title, item_id, tags, summary, path, body unindexed, tokens
            );
        """)
        for index in range(count):
            item = {"id": "doc-{}".format(index), "status": "active" if index == 1 else "draft"}
            connection.execute(
                "insert into documents values (?,?,?,?,?,?,?,?)",
                (index + 1, item["id"], item["id"] + ".md", ".md", "[]",
                 json.dumps(item, separators=(",", ":")), "proof", "proof " * (index + 1)),
            )
            connection.execute(
                "insert into documents_fts(rowid,title,item_id,tags,summary,path,body,tokens) values (?,?,?,?,?,?,?,?)",
                (index + 1, "proof", item["id"], "", "", item["id"] + ".md", "proof", "proof"),
            )
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    return connection


def test_body_reads_follow_a_bounded_header_query(tmp_path):
    connection = _database(tmp_path / "index.db")
    trace = []
    connection.set_trace_callback(trace.append)
    try:
        rows = candidate_io.read_candidate_payloads(connection, '"proof"', 2)
        assert len(rows) == 2
        assert all(row["fts_rank"] < 0 for row in rows)  # BM25 negative scores remain valid.
        selects = [sql for sql in trace if "body_bytes" in sql or "select * from documents where" in sql]
        assert "body_bytes" in selects[0]
        assert "limit 2" in selects[0]
        assert "where id in" in selects[1]
    finally:
        connection.close()


@pytest.mark.parametrize("value", [0, -1, 4097, True, "2"])
def test_invalid_limits_are_not_coerced(tmp_path, value):
    connection = _database(tmp_path / "index.db")
    try:
        with pytest.raises(SearchBoundaryError, match="limit"):
            candidate_io.read_candidate_payloads(connection, '"proof"', value)
    finally:
        connection.close()


@pytest.mark.parametrize("bound", ["SEARCH_MAX_FILE_BYTES", "MAX_METADATA_BYTES", "SEARCH_MAX_TOTAL_BYTES"])
def test_payload_budget_fails_before_any_body_select(tmp_path, monkeypatch, bound):
    connection = _database(tmp_path / "index.db")
    trace = []
    connection.set_trace_callback(trace.append)
    monkeypatch.setattr(candidate_io, bound, 1)
    try:
        with pytest.raises(SearchBoundaryError, match="budget"):
            candidate_io.read_candidate_payloads(connection, '"proof"', 3)
        assert not any("select * from documents" in sql.lower() for sql in trace)
    finally:
        connection.close()


def test_authority_prefilter_keeps_the_existing_scope(tmp_path):
    connection = _database(tmp_path / "index.db")
    try:
        rows = candidate_io.read_candidate_payloads(connection, '"proof"', 3, authority_only=True)
        assert [json.loads(row["item_json"])["id"] for row in rows] == ["doc-1"]
    finally:
        connection.close()


def test_body_batching_preserves_rank_order(tmp_path, monkeypatch):
    connection = _database(tmp_path / "index.db", count=5)
    trace = []
    connection.set_trace_callback(trace.append)
    monkeypatch.setattr(candidate_io, "BODY_BATCH_SIZE", 2)
    try:
        rows = candidate_io.read_candidate_payloads(connection, '"proof"', 5)
        assert [row["id"] for row in rows] == [1, 2, 3, 4, 5]
        assert len([sql for sql in trace if "select * from documents" in sql]) == 3
    finally:
        connection.close()


def test_sqlite_error_is_not_converted_to_an_unbounded_full_table_result(tmp_path):
    path = tmp_path / "broken.db"
    connection = _database(path)
    connection.execute("drop table documents_fts")
    connection.commit()
    connection.close()
    index = SearchIndex(tmp_path)
    index.path = path
    with pytest.raises(sqlite3.Error):
        index.candidates("proof", candidate_limit=2)
    with pytest.raises(sqlite3.Error):
        index.authority_candidates("proof", candidate_limit=2)


def test_metadata_first_loading_is_used_by_the_public_index(tmp_path):
    path = tmp_path / "index.db"
    _database(path).close()
    index = SearchIndex(tmp_path)
    index.path = path
    rows = index.candidates("proof", candidate_limit=2)
    assert len(rows) == 2
    assert rows[0]["body"].startswith("proof")
    assert len(index.authority_candidates("proof")) == 3  # All three are exact-title hits.
