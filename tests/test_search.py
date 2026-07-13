import json
import sqlite3

from tools.codex_assets.knowledge_hub.search import SearchFilters, search


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
