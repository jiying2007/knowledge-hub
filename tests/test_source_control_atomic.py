"""Atomic source control creation fails closed on interrupted writes and races."""
import errno
from concurrent.futures import ThreadPoolExecutor

import pytest

from tools.codex_assets.knowledge_hub import source_control_files as source_files


def test_short_write_failure_never_publishes_partial_target(tmp_path, monkeypatch):
    original = source_files.os.write
    calls = 0

    def interrupted(fd, data):
        nonlocal calls
        calls += 1
        if calls == 1:
            return original(fd, data[:2])
        raise OSError(errno.ENOSPC, "SYNTHETIC_DISK_FULL")

    monkeypatch.setattr(source_files.os, "write", interrupted)
    content = "# Complete control\n" * 100
    with pytest.raises(ValueError, match="unsafe-source-control-path"):
        source_files.materialize_source_file(tmp_path, "example", "coverage.md", content,
                                            apply=True)
    folder = tmp_path / "sources/example"
    assert list(folder.iterdir()) == []
    monkeypatch.setattr(source_files.os, "write", original)
    assert source_files.materialize_source_file(tmp_path, "example", "coverage.md", content,
                                                apply=True) == "created"
    assert (folder / "coverage.md").read_text() == content


def test_contending_creators_publish_only_complete_content(tmp_path):
    values = ["x" * n for n in (17, 293, 1015, 4096)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda content: source_files.materialize_source_file(
            tmp_path, "example", "README.md", content, apply=True), values))
    assert results.count("created") == 1
    assert results.count("preserved") == 3
    folder = tmp_path / "sources/example"
    assert (folder / "README.md").read_text() in values
    assert [p.name for p in folder.iterdir()] == ["README.md"]


def test_existing_regular_file_is_never_replaced(tmp_path):
    folder = tmp_path / "sources/example"
    folder.mkdir(parents=True)
    target = folder / "coverage.md"
    target.write_bytes(b"# historical manual evidence\n")
    original_stat = target.stat()
    assert source_files.materialize_source_file(tmp_path, "example", "coverage.md",
                                                "# generated\n", apply=True) == "preserved"
    assert target.read_bytes() == b"# historical manual evidence\n"
    assert target.stat().st_mtime_ns == original_stat.st_mtime_ns
    assert len(list(folder.iterdir())) == 1


def test_preexisting_symbolic_link_is_never_read_or_overwritten(tmp_path):
    folder = tmp_path / "sources/example"
    folder.mkdir(parents=True)
    (folder / "README.md").symlink_to(tmp_path / "missing-private-target")
    with pytest.raises(ValueError):
        source_files.materialize_source_file(tmp_path, "example", "README.md",
                                            "not allowed", apply=True)
    assert (folder / "README.md").is_symlink()
    assert not (tmp_path / "missing-private-target").exists()
    assert len(list(folder.iterdir())) == 1


def test_budget_checked_before_any_creation(tmp_path):
    with pytest.raises(ValueError, match="source-control-content-budget"):
        source_files.materialize_source_file(tmp_path, "example", "coverage.md",
                                            "a" * (source_files.MAX_CONTROL_BYTES + 1), apply=True)
    assert list(tmp_path.iterdir()) == []


def test_empty_body_is_atomic_and_replay_safe(tmp_path):
    assert source_files.materialize_source_file(tmp_path, "example", "inventory.jsonl", "",
                                                apply=True) == "created"
    assert source_files.materialize_source_file(tmp_path, "example", "inventory.jsonl", "x",
                                                apply=True) == "preserved"
    assert (tmp_path / "sources/example/inventory.jsonl").read_bytes() == b""


def test_source_id_validation_precedes_directory_creation(tmp_path):
    with pytest.raises(ValueError, match="invalid-source-control-id"):
        source_files.materialize_source_file(tmp_path, "../private", "README.md", "x",
                                            apply=True)
    assert list(tmp_path.iterdir()) == []
