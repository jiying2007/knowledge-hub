import pathlib

import pytest

from tools.codex_assets.knowledge_hub.common import (
    KnowledgeHubError,
    iter_text_file_records,
    iter_text_files,
    normalize_relpath,
    render_markdown,
    split_frontmatter,
)


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


def test_iter_text_files_prunes_cache_and_non_text_files(tmp_path):
    expected = {
        "README.md",
        "notes/keep.txt",
        "registry/items.jsonl",
        "tools/help.md",
        "artifacts/report.json",
    }
    for relative in expected:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")
    for relative in (
        ".cache/hidden.md",
        ".git/hidden.txt",
        ".tmp/hidden.json",
        "notes/__pycache__/hidden.txt",
        "notes/.pytest_cache/hidden.csv",
        "notes/ignored.bin",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")

    actual = {path.relative_to(tmp_path).as_posix() for path in iter_text_files(tmp_path)}
    records = {
        relative: (path, file_stat)
        for path, relative, file_stat in iter_text_file_records(tmp_path)
    }

    assert actual == expected
    assert set(records) == expected
    assert all(path.relative_to(tmp_path).as_posix() == relative for relative, (path, _) in records.items())
    assert all(file_stat.st_size == len(relative.encode("utf-8")) for relative, (_, file_stat) in records.items())


def test_iter_text_files_can_exclude_control_roots(tmp_path):
    for relative in (
        "notes/keep.md",
        "registry/items.jsonl",
        "tools/help.md",
        "artifacts/report.json",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")

    actual = {
        path.relative_to(tmp_path).as_posix()
        for path in iter_text_files(tmp_path, include_control=False)
    }

    assert actual == {"notes/keep.md"}
