import errno
import json
import sqlite3

from tools.codex_assets.knowledge_hub import metrics
from tools.codex_assets.knowledge_hub.search import SearchFilters, record_search_telemetry, search


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
    assert payload["schema_version"] == 2
    assert payload["status"] == "pass"
    assert payload["index"]["mode"] == "local-index"
    assert payload["zero_hit"]["is_zero_hit"] is False


def test_structured_filter_excludes_unregistered_raw_file(tmp_path):
    root = _search_root(tmp_path)
    payload = search(root, "secret marker", limit=5, filters=SearchFilters(owners=("owner-a",)))
    assert payload["results"] == []
    assert payload["status"] == "zero-hit"
    assert payload["zero_hit"]["is_zero_hit"] is True
    assert payload["filter_diagnostics"]["by_reason"]["unregistered-structured-result"] >= 1


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
    assert captured["result_ids"] == ["item-a"]
    assert captured["index_rebuilt"] is False
    assert captured["index_updated"] is True
    assert captured["index_lock_wait_ms"] == 1.5
    assert captured["index_signature_ms"] == 12.5
    assert captured["index_transaction_ms"] == 8.5
    assert "private search query" not in json.dumps(captured)
