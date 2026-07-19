import errno
import json
import os
import sqlite3

import pytest

from tools.codex_assets.knowledge_hub import metrics
from tools.codex_assets.knowledge_hub import search as search_module
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.search import (
    INDEX_SCHEMA_VERSION,
    SearchFilters,
    SearchIndex,
    _signature,
    _index_tokens,
    _indexed_title,
    _physical_sources,
    record_search_telemetry,
    search,
    search_tokens,
)


def _jsonl(rows):
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)


def _search_root(tmp_path):
    (tmp_path / "registry").mkdir()
    (tmp_path / "governance").mkdir()
    (tmp_path / "projects/p1/current").mkdir(parents=True)
    (tmp_path / "governance/obsidian.md").write_text("# Obsidian\n\nBacklinks 和 Graph 作为受控工作台视图。\n")
    (tmp_path / "projects/p1/current/unregistered.md").write_text("raw secret marker\n")
    items = [
        {
            "id": "obsidian-workbench",
            "title": "Obsidian 受控工作台",
            "kind": "standard",
            "domain": "governance",
            "path": "governance/obsidian.md",
            "status": "reviewing",
            "owner": "owner-a",
            "source": {"type": "manual"},
            "summary_zh": "使用 Backlinks 建立关系导航。",
            "review_after": "2026-10-13",
            "tags": ["obsidian", "backlinks"],
        }
    ]
    (tmp_path / "registry/items.jsonl").write_text(_jsonl(items))
    (tmp_path / "registry/sources.json").write_text('{"sources": []}\n')
    (tmp_path / "registry/retired-sources.jsonl").write_text("")
    return tmp_path


def test_search_supports_chinese_synonym_and_registry_ranking(tmp_path):
    root = _search_root(tmp_path)
    payload = search(root, "Obsidian 双向链接", limit=5)
    assert payload["results"][0]["item_id"] == "obsidian-workbench"
    assert payload["results"][0]["query_coverage"] == 1.0
    assert payload["schema_version"] == 3
    assert payload["status"] == "pass"
    assert payload["index"]["mode"] == "local-index"
    assert payload["zero_hit"]["is_zero_hit"] is False
    assert payload["timing"]["total_ms"] == payload["latency_ms"]
    assert set(payload["timing"]) == {
        "validation_ms",
        "index_ensure_ms",
        "candidate_query_ms",
        "ranking_ms",
        "total_ms",
    }


def test_search_schema_avoids_duplicate_body_inverted_index(tmp_path):
    root = _search_root(tmp_path)
    search(root, "raw secret marker", limit=5)
    index = SearchIndex(root)

    with sqlite3.connect(str(index.path)) as connection:
        schema = connection.execute(
            "select sql from sqlite_master where name='documents_fts'"
        ).fetchone()[0]

    assert INDEX_SCHEMA_VERSION == 7
    assert index.path.name == "search-index-v7.sqlite3"
    assert "body unindexed" in schema.lower()
    with sqlite3.connect(str(index.path)) as connection:
        indexed_columns = {
            row[1] for row in connection.execute("pragma table_info(indexed_files)")
        }
    assert {"ctime_ns", "device", "inode", "content_sha256"} <= indexed_columns


def test_forced_rebuild_reuses_exact_persistent_token_provenance(monkeypatch, tmp_path):
    root = _search_root(tmp_path)
    calls = []
    original = search_module._index_tokens

    def counted(value, maximum=20000):
        calls.append(value)
        return original(value, maximum)

    monkeypatch.setattr(search_module, "_index_tokens", counted)
    first = search(root, "Obsidian 双向链接", limit=5, rebuild_index=True)
    first_call_count = len(calls)
    second = search(root, "Obsidian 双向链接", limit=5, rebuild_index=True)

    assert first_call_count > 0
    assert len(calls) == first_call_count
    assert first["results"] == second["results"]
    assert first["index"]["token_cache_misses"] == first_call_count
    assert second["index"]["token_cache_hits"] == first_call_count
    assert second["index"]["token_cache_misses"] == 0
    assert second["index"]["token_cache_status"] == "ready"


def test_corrupt_persistent_token_cache_fails_open(monkeypatch, tmp_path):
    root = _search_root(tmp_path)
    search(root, "Obsidian 双向链接", limit=5, rebuild_index=True)
    index = SearchIndex(root)
    index.token_cache_path.write_text("not a sqlite database")
    calls = []
    original = search_module._index_tokens

    def counted(value, maximum=20000):
        calls.append(value)
        return original(value, maximum)

    monkeypatch.setattr(search_module, "_index_tokens", counted)
    payload = search(root, "Obsidian 双向链接", limit=5, rebuild_index=True)

    assert payload["status"] == "pass"
    assert calls
    assert payload["index"]["token_cache_status"] == "degraded"
    assert payload["index"]["token_cache_hits"] == 0
    assert payload["index"]["token_cache_misses"] == len(calls)


def test_valid_sqlite_token_cache_row_tampering_is_recomputed(tmp_path):
    root = _search_root(tmp_path)
    first = search(root, "Obsidian 双向链接", limit=5, rebuild_index=True)
    index = SearchIndex(root)
    with sqlite3.connect(str(index.token_cache_path)) as connection:
        connection.execute("update token_cache set token_text='tampered tokens'")
        connection.commit()

    second = search(root, "Obsidian 双向链接", limit=5, rebuild_index=True)

    assert second["results"] == first["results"]
    assert second["index"]["token_cache_status"] == "recovered"
    assert second["index"]["token_cache_hits"] == 0
    assert second["index"]["token_cache_misses"] > 0


def test_persistent_token_provenance_invalidates_exact_changed_input(tmp_path):
    root = _search_root(tmp_path)
    first = search(root, "raw secret marker", limit=5, rebuild_index=True)
    index = SearchIndex(root)
    assert index.token_cache_path.stat().st_mode & 0o777 == 0o600

    (root / "projects/p1/current/unregistered.md").write_text(
        "replacement provenance needle\n"
    )
    second = search(root, "replacement provenance needle", limit=5, rebuild_index=True)

    assert first["results"][0]["path"] == "projects/p1/current/unregistered.md"
    assert second["results"][0]["path"] == "projects/p1/current/unregistered.md"
    assert second["index"]["token_cache_misses"] >= 1
    assert second["index"]["token_cache_hits"] >= 1


def test_persistent_token_cache_bounds_pending_memory(monkeypatch, tmp_path):
    monkeypatch.setattr(search_module, "TOKEN_CACHE_MAX_TOTAL_BYTES", 1)
    cache = search_module._PersistentTokenCache(tmp_path / "token-cache.sqlite3")

    assert cache.token_text("several searchable tokens")
    assert cache.pending == {}
    assert cache.pending_bytes == 0
    cache.close()


def test_index_tokens_preserve_search_token_set_with_deterministic_order():
    value = "Knowledge Hub 重复重复 token TOKEN 与中文检索"

    first = _index_tokens(value)
    second = _index_tokens(value)

    assert first == second
    assert set(first) == set(search_tokens(value))


def test_indexed_title_fast_path_preserves_yaml_scalar_and_block_values():
    assert _indexed_title(
        "notes/plain.md",
        "---\ntitle: 简单标题\n---\n# ignored\n",
        {},
    ) == "简单标题"
    assert _indexed_title(
        "notes/quoted.md",
        '---\ntitle: "带冒号: 标题"\n---\n# ignored\n',
        {},
    ) == "带冒号: 标题"
    assert _indexed_title(
        "notes/block.md",
        "---\ntitle: >-\n  分块\n  标题\n---\n# ignored\n",
        {},
    ) == "分块 标题"
    assert _indexed_title(
        "notes/multiline-quoted.md",
        '---\ntitle: "多行\n  引号标题"\n---\n# ignored\n',
        {},
    ) == "多行 引号标题"
    assert _indexed_title(
        "notes/heading.md",
        "---\ntags: [example]\n---\n# 正文标题\n",
        {},
    ) == "正文标题"


def test_physical_sources_use_path_boundaries_and_resolve_file_symlinks(tmp_path):
    source_root = (tmp_path / "source").resolve()
    source_root.mkdir()
    inside = source_root / "inside.md"
    inside.write_text("inside\n")
    collision = tmp_path / "source-other.md"
    collision.write_text("outside\n")
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n")
    link = source_root / "outside-link.md"
    link.symlink_to(outside)
    roots = [("registered-source", source_root)]

    assert _physical_sources(inside, roots) == ["knowledge-hub", "registered-source"]
    assert _physical_sources(collision, roots) == ["knowledge-hub"]
    assert _physical_sources(link, roots) == ["knowledge-hub"]


def test_search_never_indexes_repository_file_symlink(tmp_path):
    root = _search_root(tmp_path)
    outside = tmp_path.parent / "outside-search.md"
    outside.write_text("outside-search-confidential-marker\n", encoding="utf-8")
    link = root / "projects/p1/current/external-link.md"
    link.symlink_to(outside)

    payload = search(root, "outside-search-confidential-marker", limit=5)

    assert payload["status"] == "zero-hit"
    assert payload["results"] == []


def test_search_index_and_cache_directory_are_private(tmp_path):
    root = _search_root(tmp_path)

    search(root, "Obsidian", limit=5)
    index = SearchIndex(root)

    assert index.cache_root.stat().st_mode & 0o777 == 0o700
    assert index.path.stat().st_mode & 0o777 == 0o600
    assert index.lock_path.stat().st_mode & 0o777 == 0o600
    assert index.token_cache_path.stat().st_mode & 0o777 == 0o600


def test_search_signature_hashes_content_even_when_size_and_mtime_match(tmp_path):
    root = _search_root(tmp_path)
    target = root / "projects/p1/current/unregistered.md"
    first_signature, _, _ = _signature(root)
    original_stat = target.stat()
    target.write_text("new secret marker\n", encoding="utf-8")
    assert target.stat().st_size == original_stat.st_size
    os.utime(target, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

    second_signature, _, _ = _signature(root)

    assert second_signature != first_signature


def test_warm_search_reuses_trusted_content_hashes(tmp_path):
    root = _search_root(tmp_path)
    index = SearchIndex(root)

    first = index.ensure()
    second = index.ensure()

    assert first["state"] == "rebuilt"
    assert second["state"] == "warm"
    assert second["hashed_files"] == 0
    assert second["reused_content_hashes"] == second["document_files"]


def test_cached_signature_detects_same_size_and_mtime_content_change(tmp_path):
    root = _search_root(tmp_path)
    target = root / "projects/p1/current/unregistered.md"
    index = SearchIndex(root)
    index.ensure()
    original_stat = target.stat()
    target.write_text("new secret marker\n", encoding="utf-8")
    assert target.stat().st_size == original_stat.st_size
    os.utime(target, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

    payload = search(root, "new secret marker", limit=5, search_index=index)

    assert payload["results"][0]["path"].endswith("unregistered.md")
    assert payload["index"]["state"] == "updated"
    assert payload["index"]["hashed_files"] >= 1


def test_invalid_cached_content_hash_is_recomputed(tmp_path):
    root = _search_root(tmp_path)
    index = SearchIndex(root)
    index.ensure()
    with sqlite3.connect(str(index.path)) as connection:
        connection.execute(
            "update indexed_files set content_sha256='invalid' where path=?",
            ("governance/obsidian.md",),
        )
        connection.commit()

    payload = index.ensure()

    assert payload["state"] == "warm"
    assert payload["hashed_files"] >= 1
    with sqlite3.connect(str(index.path)) as connection:
        digest = connection.execute(
            "select content_sha256 from indexed_files where path=?",
            ("governance/obsidian.md",),
        ).fetchone()[0]
    assert len(digest) == 64


def test_unchanged_content_metadata_refresh_only_rehashes_once(tmp_path):
    root = _search_root(tmp_path)
    target = root / "projects/p1/current/unregistered.md"
    index = SearchIndex(root)
    index.ensure()
    original_stat = target.stat()
    os.utime(
        target,
        ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns + 1_000_000),
    )

    refreshed = index.ensure()
    stable = index.ensure()

    assert refreshed["state"] == "warm"
    assert refreshed["hashed_files"] == 1
    assert refreshed["metadata_refreshed_files"] == 1
    assert stable["hashed_files"] == 0
    assert stable["metadata_refreshed_files"] == 0


def test_signature_fails_closed_when_file_changes_during_read(monkeypatch, tmp_path):
    root = _search_root(tmp_path)
    target = root / "projects/p1/current/unregistered.md"
    original_reader = search_module.read_repository_bytes_bounded

    def mutating_reader(read_root, relative, maximum_bytes, label):
        raw = original_reader(read_root, relative, maximum_bytes, label)
        if relative == "projects/p1/current/unregistered.md":
            target.write_text("new secret marker\n", encoding="utf-8")
        return raw

    monkeypatch.setattr(
        search_module,
        "read_repository_bytes_bounded",
        mutating_reader,
    )

    with pytest.raises(KnowledgeHubError, match="changed during signature"):
        _signature(root)


def test_search_rejects_text_file_over_configured_byte_budget(monkeypatch, tmp_path):
    root = _search_root(tmp_path)
    monkeypatch.setattr(search_module, "SEARCH_MAX_FILE_BYTES", 16, raising=False)

    with pytest.raises(KnowledgeHubError, match="search text file exceeds"):
        search(root, "Obsidian", limit=5)


def test_structured_filter_excludes_unregistered_raw_file(tmp_path):
    root = _search_root(tmp_path)
    payload = search(root, "secret marker", limit=5, filters=SearchFilters(owners=("owner-a",)))
    assert payload["results"] == []
    assert payload["status"] == "zero-hit"
    assert payload["index"]["candidate_limit"] == SearchIndex.STRUCTURED_CANDIDATE_LIMIT
    assert payload["zero_hit"]["is_zero_hit"] is True
    assert payload["filter_diagnostics"]["by_reason"]["unregistered-structured-result"] >= 1


def test_zero_hit_trace_returns_registered_item_hidden_by_wrong_filter(tmp_path):
    root = _search_root(tmp_path)

    payload = search(
        root,
        "obsidian-workbench",
        limit=5,
        filters=SearchFilters(kinds=("patent",)),
    )

    assert payload["status"] == "zero-hit"
    assert payload["zero_hit"]["reason"] == (
        "matching registered items were excluded by structured filters"
    )
    trace = payload["search_trace"]
    assert trace["schema_version"] == "knowledge-hub.search-trace.v1"
    assert trace["excluded_by_filters_total"] == 1
    assert trace["excluded_by_filters"] == [
        {
            "id": "obsidian-workbench",
            "path": "governance/obsidian.md",
            "kind": "standard",
            "status": "reviewing",
            "domain": "governance",
            "owner": "owner-a",
            "excluded_by": "kind",
            "matched_terms": ["obsidian-workbench"],
            "query_coverage": 1.0,
        }
    ]
    assert trace["retry_queries"] == [
        {"query": "obsidian-workbench", "drop_filters": ["kind"]}
    ]
    assert "Backlinks" not in json.dumps(trace, ensure_ascii=False)


def test_zero_hit_trace_does_not_expose_personal_local_metadata(tmp_path):
    root = _search_root(tmp_path)
    personal_path = root / "governance/personal.md"
    personal_path.write_text("# private trace\n\npersonal-private-needle\n")
    items_path = root / "registry/items.jsonl"
    rows = [json.loads(line) for line in items_path.read_text().splitlines() if line]
    rows.append(
        {
            "id": "personal-private-item",
            "title": "personal-private-needle",
            "kind": "standard",
            "domain": "governance",
            "path": "governance/personal.md",
            "status": "personal",
            "owner": "owner-a",
            "visibility": "personal-local",
            "source": {"type": "manual"},
            "summary_zh": "personal-private-needle",
            "review_after": "2026-10-13",
            "tags": ["personal-private-needle"],
        }
    )
    items_path.write_text(_jsonl(rows))

    payload = search(
        root,
        "personal-private-needle",
        limit=5,
        filters=SearchFilters(kinds=("patent",)),
    )

    trace = payload["search_trace"]
    serialized = json.dumps(trace, ensure_ascii=False)
    assert trace["excluded_by_filters_total"] == 0
    assert trace["excluded_by_filters"] == []
    assert "personal-private-item" not in serialized
    assert "governance/personal.md" not in serialized
    assert payload["zero_hit"]["reason"] == (
        "no indexed document matched the query and structured filters"
    )


def test_domain_filter_uses_path_segment_boundary(tmp_path):
    root = _search_root(tmp_path)
    (root / "projects/p10/current").mkdir(parents=True)
    other_path = root / "projects/p10/current/other.md"
    other_path.write_text("boundary-project-needle\n")
    items_path = root / "registry/items.jsonl"
    rows = [json.loads(line) for line in items_path.read_text().splitlines() if line]
    rows.append(
        {
            "id": "project-p10-item",
            "title": "boundary-project-needle",
            "kind": "project-current",
            "domain": "projects/p10",
            "path": "projects/p10/current/other.md",
            "status": "reviewing",
            "owner": "owner-a",
            "source": {"type": "manual"},
            "summary_zh": "boundary-project-needle",
            "review_after": "2026-10-13",
            "tags": ["boundary-project-needle"],
        }
    )
    items_path.write_text(_jsonl(rows))

    payload = search(
        root,
        "boundary-project-needle",
        limit=5,
        filters=SearchFilters(domains=("projects/p1",)),
    )

    assert payload["results"] == []
    assert payload["search_trace"]["excluded_by_filters"][0]["id"] == "project-p10-item"


def test_search_rejects_unbounded_query_limit_and_filters(tmp_path):
    root = _search_root(tmp_path)
    with pytest.raises(KnowledgeHubError, match="query exceeds"):
        search(root, "q" * 4097)
    with pytest.raises(KnowledgeHubError, match="limit must be between"):
        search(root, "demo", limit=101)
    with pytest.raises(KnowledgeHubError, match="filter values"):
        search(root, "demo", filters=SearchFilters(owners=tuple("owner-{}".format(i) for i in range(33))))
    with pytest.raises(KnowledgeHubError, match="filter value exceeds"):
        search(root, "demo", filters=SearchFilters(domains=("d" * 257,)))


def test_search_incrementally_updates_changed_added_and_deleted_bodies(tmp_path):
    root = _search_root(tmp_path)
    initial = search(root, "raw secret marker", limit=5)
    assert initial["index"]["state"] == "rebuilt"

    existing = root / "projects/p1/current/unregistered.md"
    existing.write_text("incremental replacement needle\n")
    changed = search(root, "incremental replacement needle", limit=5)

    assert changed["index"]["state"] == "updated"
    assert changed["index"]["rebuilt"] is False
    assert changed["index"]["updated"] is True
    assert changed["index"]["changed_files"] == 1
    assert changed["index"]["deleted_files"] == 0
    assert changed["results"][0]["path"] == "projects/p1/current/unregistered.md"

    old_query = search(root, "raw secret marker", limit=5)
    assert all(
        row["path"] != "projects/p1/current/unregistered.md"
        for row in old_query["results"]
    )

    added_path = root / "projects/p1/current/added.md"
    added_path.write_text("new incremental document token\n")
    added = search(root, "new incremental document token", limit=5)
    assert added["index"]["state"] == "updated"
    assert added["index"]["changed_files"] == 1
    assert added["results"][0]["path"] == "projects/p1/current/added.md"

    added_path.unlink()
    deleted = search(root, "new incremental document token", limit=5)
    assert deleted["index"]["state"] == "updated"
    assert deleted["index"]["deleted_files"] == 1
    assert all(row["path"] != "projects/p1/current/added.md" for row in deleted["results"])


def test_search_rebuilds_when_registry_metadata_changes(tmp_path):
    root = _search_root(tmp_path)
    initial = search(root, "Obsidian 受控工作台", limit=5)
    assert initial["index"]["state"] == "rebuilt"

    items_path = root / "registry/items.jsonl"
    rows = [json.loads(line) for line in items_path.read_text().splitlines() if line]
    rows[0]["title"] = "Obsidian 增量索引元数据"
    items_path.write_text(_jsonl(rows))
    refreshed = search(root, "Obsidian 增量索引元数据", limit=5)

    assert refreshed["index"]["state"] == "rebuilt"
    assert refreshed["index"]["rebuilt"] is True
    assert refreshed["index"]["updated"] is False
    assert refreshed["results"][0]["item_id"] == "obsidian-workbench"


def test_search_falls_back_to_repository_scan_when_index_fails(tmp_path):
    root = _search_root(tmp_path)

    class BrokenIndex:
        def ensure(self, force=False):
            raise sqlite3.OperationalError("FTS unavailable")

    payload = search(root, "Obsidian Backlinks", limit=5, search_index=BrokenIndex())

    assert payload["status"] == "pass"
    assert payload["index"]["mode"] == "repository-scan-fallback"
    assert payload["index"]["fresh"] is False
    assert payload["results"][0]["item_id"] == "obsidian-workbench"


def test_search_telemetry_storage_failure_is_non_blocking(monkeypatch, tmp_path):
    def deny_write(path, row):
        raise PermissionError(errno.EACCES, "permission denied")

    monkeypatch.setenv("KNOWLEDGE_TELEMETRY", "1")
    monkeypatch.setattr(metrics, "_append_locked", deny_write)
    result = record_search_telemetry(
        tmp_path,
        {
            "query": "private search query",
            "query_terms": ["private"],
            "count": 1,
            "total_matches": 1,
            "latency_ms": 5,
            "index": {"state": "fresh"},
        },
    )

    assert result["status"] == "degraded"
    assert result["reason"] == "read-only-or-permission-denied"
    assert result["error_code"] == "EACCES"
    assert "private search query" not in json.dumps(result)


def test_search_telemetry_binds_current_interaction_and_result_ids(monkeypatch, tmp_path):
    captured = {}

    def capture(path, row):
        captured.update(row)

    monkeypatch.setenv("KNOWLEDGE_TELEMETRY", "1")
    monkeypatch.setattr(metrics, "_append_locked", capture)
    result = record_search_telemetry(
        tmp_path,
        {
            "query": "private search query",
            "query_terms": ["private"],
            "count": 1,
            "total_matches": 1,
            "latency_ms": 5,
            "index": {
                "state": "updated",
                "rebuilt": False,
                "updated": True,
                "lock_wait_duration_ms": 1.5,
                "signature_duration_ms": 12.5,
                "transaction_duration_ms": 8.5,
            },
            "results": [{"item_id": "item-a"}],
        },
    )

    assert result["status"] == "recorded"
    assert captured["schema_version"] == metrics.INTERACTIVE_TELEMETRY_SCHEMA_VERSION
    assert captured["interaction_contract"] == metrics.INTERACTION_CONTRACT
    assert captured["performance_contract"] == metrics.PERFORMANCE_CONTRACT
    assert captured["result_ids"] == ["item-a"]
    assert captured["index_rebuilt"] is False
    assert captured["index_updated"] is True
    assert captured["index_lock_wait_ms"] == 1.5
    assert captured["index_signature_ms"] == 12.5
    assert captured["index_transaction_ms"] == 8.5
    assert captured["stage_timing"] == {}
    assert "private search query" not in json.dumps(captured)
