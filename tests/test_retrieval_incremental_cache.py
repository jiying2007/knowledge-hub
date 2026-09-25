"""Derived cache lifecycle and real-entrypoint parity, not production evidence."""

import datetime as dt
import json
import os
import shutil

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub import retrieval_cache as cache_module
from tools.codex_assets.knowledge_hub import retrieval_chunks as chunks_module
from tools.codex_assets.knowledge_hub import retrieval_v4 as retrieval
from tools.codex_assets.knowledge_hub.retrieval_cache import DerivedCache


def _resolve(cache, revision="one", build=lambda: [1], key="key"):
    return cache.resolve("test", key, revision, build, lambda v: v == [1] or v == [2])


def test_persistent_hit_reuses_bytes_without_recomputing(tmp_path):
    with DerivedCache(tmp_path) as cache:
        assert _resolve(cache) == [1]
    with DerivedCache(tmp_path) as cache:
        assert _resolve(cache, build=lambda: pytest.fail("unexpected recomputation")) == [1]
        assert cache.stats["hits"] == 1


def test_revision_replaces_one_entry_instead_of_growing_history(tmp_path):
    with DerivedCache(tmp_path) as cache:
        _resolve(cache)
        assert _resolve(cache, revision="two", build=lambda: [2]) == [2]
        assert cache.connection.execute("select count(*) from entries").fetchone()[0] == 1


def test_corrupt_checksum_recomputes_without_trusting_cached_value(tmp_path):
    with DerivedCache(tmp_path) as cache:
        _resolve(cache)
        cache.connection.execute("update entries set digest='bad'")
        assert _resolve(cache, build=lambda: [2]) == [2]
        assert cache.stats["invalid_entries"] == 1


def test_oversized_payload_is_not_loaded(tmp_path, monkeypatch):
    with DerivedCache(tmp_path) as cache:
        _resolve(cache)
        monkeypatch.setattr(cache_module, "MAX_ENTRY_BYTES", 1)
        trace = []
        cache.connection.set_trace_callback(trace.append)
        assert cache._read("test", "key", "one") is None
        assert not any("select payload,digest" in sql for sql in trace)


def test_corrupt_database_degrades_to_bounded_computation(tmp_path):
    directory = tmp_path / ".cache/knowledge-hub"
    directory.mkdir(parents=True)
    (directory / "retrieval-derived-v1.sqlite3").write_bytes(b"broken database")
    with DerivedCache(tmp_path) as cache:
        assert cache.stats["enabled"] is False
        assert _resolve(cache) == [1]
        assert cache.stats["reason"] == "cache-unavailable"


def test_locked_database_does_not_require_a_retry_loop(tmp_path):
    with DerivedCache(tmp_path) as first:
        first.connection.execute("begin exclusive")
        with DerivedCache(tmp_path) as second:
            assert second.stats["enabled"] is False
            assert _resolve(second) == [1]
        first.connection.execute("rollback")


@pytest.mark.parametrize("suffix", ["", "-journal", "-wal", "-shm"])
def test_cache_symlink_is_not_followed(tmp_path, suffix):
    directory = tmp_path / ".cache/knowledge-hub"
    directory.mkdir(parents=True)
    target = tmp_path / "target"
    target.write_bytes(b"do not change")
    (directory / ("retrieval-derived-v1.sqlite3" + suffix)).symlink_to(target)
    with pytest.raises(KnowledgeHubError, match="symlink"):
        DerivedCache(tmp_path)
    assert target.read_bytes() == b"do not change"


def test_cache_count_and_write_budgets(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_module, "MAX_ENTRIES", 2)
    monkeypatch.setattr(cache_module, "MAX_WRITES", 3)
    with DerivedCache(tmp_path) as cache:
        for i in range(5):
            assert _resolve(cache, key=str(i)) == [1]
        assert cache.connection.execute("select count(*) from entries").fetchone()[0] == 2
        assert cache.stats["writes"] == 3


def test_disabled_cache_does_not_create_any_files(tmp_path):
    with DerivedCache(tmp_path, enabled=False) as cache:
        assert _resolve(cache) == [1]
    assert list(tmp_path.iterdir()) == []


def test_source_failure_is_not_swallowed_as_a_cache_failure(tmp_path):
    def fail():
        raise KnowledgeHubError("source absent")
    with DerivedCache(tmp_path) as cache:
        with pytest.raises(KnowledgeHubError, match="source absent"):
            _resolve(cache, build=fail)
        assert cache.stats["writes"] == 0


def _body(tmp_path, text="# Evidence\nproof\n"):
    path = tmp_path / "note.md"
    path.write_bytes(text.encode("utf-8"))
    return {"id": "note", "path": "note.md"}, path


def test_cached_chunks_retain_exact_spans_and_skip_splitter(tmp_path, monkeypatch):
    item, path = _body(tmp_path, "# 证据\r\n原文🙂 proof\r\n")
    with DerivedCache(tmp_path) as cache:
        first = chunks_module.hierarchical_chunks(tmp_path, item, cache=cache)
    monkeypatch.setattr(chunks_module, "_split_body", lambda *a: pytest.fail("unexpected split"))
    with DerivedCache(tmp_path) as cache:
        second = chunks_module.hierarchical_chunks(tmp_path, item, cache=cache)
        assert first == second
        assert "".join(c["text"] for c in second).encode("utf-8") == path.read_bytes()
        assert cache.stats["hits"] == 1


def test_same_size_same_mtime_content_change_invalidates_chunks(tmp_path):
    item, path = _body(tmp_path, "old proof")
    original_stat = path.stat()
    with DerivedCache(tmp_path) as cache:
        first = chunks_module.hierarchical_chunks(tmp_path, item, cache=cache)
        path.write_text("new proof", encoding="utf-8")
        os.utime(path, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
        second = chunks_module.hierarchical_chunks(tmp_path, item, cache=cache)
        assert first[0]["content_sha256"] != second[0]["content_sha256"]
        assert second[0]["text"] == "new proof"
        assert cache.stats["misses"] == 2


@pytest.mark.parametrize("change", ["delete", "symlink"])
def test_warm_cache_never_masks_missing_or_unsafe_source(tmp_path, change):
    item, path = _body(tmp_path)
    with DerivedCache(tmp_path) as cache:
        chunks_module.hierarchical_chunks(tmp_path, item, cache=cache)
        path.unlink()
        if change == "symlink":
            path.symlink_to(tmp_path / "nonexistent")
        with pytest.raises(KnowledgeHubError):
            chunks_module.hierarchical_chunks(tmp_path, item, cache=cache)


def test_chunker_revision_invalidates_even_when_content_is_unchanged(tmp_path, monkeypatch):
    item, _ = _body(tmp_path)
    with DerivedCache(tmp_path) as cache:
        chunks_module.hierarchical_chunks(tmp_path, item, cache=cache)
        monkeypatch.setattr(chunks_module, "CHUNKER_REVISION", "next-chunker")
        result = chunks_module.hierarchical_chunks(tmp_path, item, cache=cache)
        assert result[0]["chunker_revision"] == "next-chunker"
        assert cache.stats["misses"] == 2


def test_large_heading_label_is_bounded_but_original_text_is_lossless():
    text = "# " + "标" * 12000 + "\nproof"
    chunks = chunks_module._split_body("doc", text)
    assert "".join(c["text"] for c in chunks) == text
    assert all(len(h) <= chunks_module.MAX_HEADING_CHARS for c in chunks for h in c["heading_path"])


def _root(tmp_path):
    (tmp_path / "registry").mkdir()
    shutil.copyfile(repository_root() / "registry/knowledge-runtime-v3.json", tmp_path / "registry/knowledge-runtime-v3.json")
    row = {"id": "note", "title": "proof", "path": "projects/pcr02/note.md",
           "domain": "projects/pcr02", "status": "active", "updated_at": "2026-09-10",
           "visibility": "team-internal", "owner": "alice", "acl": ["alice"]}
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    path = tmp_path / row["path"]
    path.parent.mkdir(parents=True)
    path.write_text("# Proof\nquasar evidence\n", encoding="utf-8")
    return tmp_path, row


def _retrieve(root, **kwargs):
    return retrieval.retrieve_v4(root, "quasar", {
        "principal_id": "alice", "organization_id": "engineering",
        "groups": ["team:embedded"], "scopes": ["projects/pcr02"],
    }, agent_id="embedded-expert", as_of="2026-09-25", **kwargs)


def _identity(**changes):
    value = {"provider": "fixture", "model": "fixture-vector", "revision": "1",
             "preprocessing": "plain-v1", "dimensions": 2}
    value.update(changes)
    return value


def test_entrypoint_cold_warm_disabled_have_identical_evidence(tmp_path):
    root, _ = _root(tmp_path)
    cold, warm, uncached = _retrieve(root), _retrieve(root), _retrieve(root, cache_enabled=False)
    for result in (warm, uncached):
        assert result["results"] == cold["results"]
        assert result["answerability"] == cold["answerability"]
    assert warm["derived_cache"]["by_namespace"]["chunks"]["hits"] == 1
    assert warm["derived_cache"]["by_namespace"]["vectors"]["hits"] == 1


def test_identified_provider_warm_call_only_embeds_the_query(tmp_path):
    root, _ = _root(tmp_path)
    calls = []
    def embed(text):
        calls.append(text)
        return [1.0, 0.0]
    kwargs = {"embedding_fn": embed, "embedding_identity": _identity()}
    _retrieve(root, **kwargs)
    calls.clear()
    warm = _retrieve(root, **kwargs)
    assert calls == ["quasar"]
    assert warm["lane_health"]["independent_semantic_recall"] is True


@pytest.mark.parametrize("field,value", [("provider", "other"), ("model", "other"),
    ("revision", "2"), ("preprocessing", "plain-v2"), ("dimensions", 3)])
def test_each_provider_identity_field_invalidates_vectors(tmp_path, field, value):
    root, _ = _root(tmp_path)
    _retrieve(root, embedding_fn=lambda text: [1.0, 0.0], embedding_identity=_identity())
    identity = _identity(**{field: value})
    calls = []
    def embed(text):
        calls.append(text)
        return [1.0] + [0.0] * (identity["dimensions"] - 1)
    _retrieve(root, embedding_fn=embed, embedding_identity=identity)
    assert len(calls) == 2


def test_unidentified_provider_is_not_persistently_cached(tmp_path):
    root, _ = _root(tmp_path)
    calls = []
    def embed(text):
        calls.append(text)
        return [1.0, 0.0]
    _retrieve(root, embedding_fn=embed)
    calls.clear()
    result = _retrieve(root, embedding_fn=embed)
    assert len(calls) == 2
    assert result["derived_cache"]["document_vector_cache_identified"] is False


@pytest.mark.parametrize("change", ["acl", "expired", "deleted"])
def test_warm_cache_cannot_restore_revoked_expired_or_removed_registry_item(tmp_path, change):
    root, row = _root(tmp_path)
    _retrieve(root)
    if change == "acl":
        row.update(owner="bob", acl=["bob"])
    elif change == "expired":
        row["valid_to"] = "2026-09-24"
    (root / "registry/items.jsonl").write_text("" if change == "deleted" else json.dumps(row) + "\n", encoding="utf-8")
    (root / row["path"]).unlink()
    result = _retrieve(root)
    assert result["results"] == []
    assert result["derived_cache"]["hits"] == 0


def test_authority_is_freshly_computed_not_cached(tmp_path):
    root, row = _root(tmp_path)
    _retrieve(root)
    row["status"] = "draft"
    (root / "registry/items.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    result = _retrieve(root)
    assert result["answerability"] == "provisional-only"
    assert result["results"][0]["authoritative"] is False


@pytest.mark.parametrize("identity", [{}, _identity(dimensions=True), _identity(revision=""), []])
def test_invalid_provider_identity_fails_closed(identity):
    with pytest.raises(KnowledgeHubError):
        retrieval._embedding_binding(lambda t: [1.0, 0.0], identity)


def test_provider_dimension_contract_is_checked(tmp_path):
    root, _ = _root(tmp_path)
    with pytest.raises(KnowledgeHubError, match="dimensions"):
        _retrieve(root, embedding_fn=lambda t: [1.0], embedding_identity=_identity())


def test_scoring_returns_only_span_metadata_not_retained_corpus_bodies(tmp_path):
    root, row = _root(tmp_path)
    chunks, *_ = retrieval._score_lanes(root, "quasar", [row], dt.date(2026, 9, 25), None)
    assert chunks["note"]
    assert all("text" not in chunk for chunk in chunks["note"])


def test_integer_sqlite_payload_never_becomes_a_bytes_allocation(tmp_path):
    with DerivedCache(tmp_path) as cache:
        _resolve(cache)
        cache.connection.execute("update entries set payload=1000000000")
        assert _resolve(cache, build=lambda: [2]) == [2]
        assert cache.stats["invalid_entries"] == 1


@pytest.mark.parametrize("text", ["a\r\nb\r\nc", "a\rb\rc", "a\nb\nc", "x" * 3999 + "\r\ntail"])
def test_cached_line_numbers_are_checked_against_current_source(text):
    rows = chunks_module._split_body("doc", text)
    digest = rows[0]["source_content_sha256"]
    assert chunks_module._valid_chunks(rows, text, "doc", digest)
    rows[0]["line_start"] = rows[0]["line_end"] = 999
    assert not chunks_module._valid_chunks(rows, text, "doc", digest)
