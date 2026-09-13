from tools.codex_assets.knowledge_hub import search as search_module
from tools.codex_assets.knowledge_hub import search_core
from tools.codex_assets.knowledge_hub import search_index
from tools.codex_assets.knowledge_hub import search_query
from tools.codex_assets.knowledge_hub import search_query_support
from tools.codex_assets.knowledge_hub.common import repository_root


def test_search_split_keeps_facade_identity_and_module_budget():
    assert search_module.SearchFilters is search_core.SearchFilters
    assert search_module.SearchIndex is search_index.SearchIndex
    assert search_module.search is search_query.search
    assert search_module._score is search_query_support._score

    root = repository_root()
    for relative in (
        "tools/codex_assets/knowledge_hub/search.py",
        "tools/codex_assets/knowledge_hub/search_core.py",
        "tools/codex_assets/knowledge_hub/search_index.py",
        "tools/codex_assets/knowledge_hub/search_query_support.py",
        "tools/codex_assets/knowledge_hub/search_query.py",
    ):
        assert len((root / relative).read_text(encoding="utf-8").splitlines()) <= 800


def test_search_facade_monkeypatches_reach_split_implementation(monkeypatch):
    def replacement_tokens(value, maximum=20000):
        return ["patched", str(maximum), value[:1]]

    def replacement_reader(*args, **kwargs):
        return b"patched"

    monkeypatch.setattr(search_module, "_index_tokens", replacement_tokens)
    monkeypatch.setattr(search_module, "SEARCH_MAX_FILE_BYTES", 12345)
    monkeypatch.setattr(
        search_module,
        "read_repository_bytes_bounded",
        replacement_reader,
    )

    assert search_core._index_tokens is replacement_tokens
    assert search_core.SEARCH_MAX_FILE_BYTES == 12345
    assert search_core.read_repository_bytes_bounded is replacement_reader
    assert search_index._index_tokens is replacement_tokens
    assert search_index.SEARCH_MAX_FILE_BYTES == 12345
    assert search_index.read_repository_bytes_bounded is replacement_reader
    assert search_query_support.SEARCH_MAX_FILE_BYTES == 12345
    assert search_query_support.read_repository_bytes_bounded is replacement_reader
