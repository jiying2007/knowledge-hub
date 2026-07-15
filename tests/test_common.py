import pathlib

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, normalize_relpath, render_markdown, split_frontmatter


def test_frontmatter_round_trip_handles_lists_and_booleans():
    metadata = {"id": "sample", "tags": ["a", "中文"], "generated_by_ai": False}
    rendered = render_markdown(metadata, "# 标题\n\n正文\n")
    parsed, body = split_frontmatter(rendered)
    assert parsed == metadata
    assert body.startswith("# 标题")


@pytest.mark.parametrize("value", ["/tmp/a", "../a", "a/../b", "./a", "~/a", ""])
def test_normalize_relpath_rejects_unsafe_paths(value):
    with pytest.raises(KnowledgeHubError):
        normalize_relpath(value)


def test_normalize_relpath_accepts_repository_path():
    assert normalize_relpath("projects/pcr02-ssc305/current/a.md") == "projects/pcr02-ssc305/current/a.md"
