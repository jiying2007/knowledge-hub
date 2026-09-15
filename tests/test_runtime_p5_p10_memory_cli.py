import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.runtime_p5_p10_cli import (
    _dispatch,
    _load_summary,
    _parser,
)


def _args(*values):
    return _parser().parse_args(list(values))


def _record(root, summary_file, scope, source_ref):
    return _dispatch(
        root,
        _args(
            "memory-record",
            "--principal-id",
            "user:alice",
            "--agent-id",
            "embedded-expert",
            "--scope-ref",
            scope,
            "--level",
            "semantic",
            "--summary-file",
            str(summary_file),
            "--source-ref",
            source_ref,
        ),
    )


def _list(root, scope):
    return _dispatch(
        root,
        _args(
            "memory-list",
            "--principal-id",
            "user:alice",
            "--agent-id",
            "embedded-expert",
            "--scope-ref",
            scope,
        ),
    )


def test_memory_cli_runs_receipted_lifecycle_without_canonical_write(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir()
    canonical = registry / "knowledge-platform-p5-p10.json"
    canonical.write_text('{"sentinel":"unchanged"}\n', encoding="utf-8")
    canonical_before = canonical.read_bytes()

    first_summary = tmp_path / "first.txt"
    first_summary.write_text("First production-like observation.", encoding="utf-8")
    second_summary = tmp_path / "second.txt"
    second_summary.write_text("Second production-like observation.", encoding="utf-8")
    other_summary = tmp_path / "other.txt"
    other_summary.write_text("Other scope observation.", encoding="utf-8")

    first = _record(tmp_path, first_summary, "projects/pcr02", "receipt:1")
    second = _record(tmp_path, second_summary, "projects/pcr02", "receipt:2")
    other = _record(tmp_path, other_summary, "projects/other", "receipt:3")

    for result in (first, second, other):
        assert result["status"] == "recorded"
        assert len(result["receipt_sha256"]) == 64
        assert result["canonical_write_performed"] is False

    target = _list(tmp_path, "projects/pcr02")
    assert len(target["memories"]) == 2
    first_memory_id = first["record"]["memory_id"]

    superseded = _dispatch(
        tmp_path,
        _args(
            "memory-supersede",
            "--principal-id",
            "user:alice",
            "--agent-id",
            "embedded-expert",
            "--scope-ref",
            "projects/pcr02",
            "--memory-id",
            first_memory_id,
        ),
    )
    assert superseded["status"] == "recorded"
    assert len(superseded["receipt_sha256"]) == 64
    assert {row["memory_id"] for row in _list(tmp_path, "projects/pcr02")["memories"]} == {
        second["record"]["memory_id"]
    }

    deleted = _dispatch(
        tmp_path,
        _args(
            "memory-forget-scope",
            "--principal-id",
            "user:alice",
            "--agent-id",
            "embedded-expert",
            "--scope-ref",
            "projects/pcr02",
        ),
    )
    assert deleted["status"] == "pass"
    assert deleted["scope_deleted"] is True
    assert deleted["deleted_count"] == 1
    assert len(deleted["receipt_sha256"]) == 64
    assert deleted["canonical_write_performed"] is False
    assert _list(tmp_path, "projects/pcr02")["memories"] == []
    assert len(_list(tmp_path, "projects/other")["memories"]) == 1
    assert canonical.read_bytes() == canonical_before


def test_memory_forget_command_is_exact_identity_and_scope(tmp_path):
    summary = tmp_path / "memory.txt"
    summary.write_text("Scoped memory.", encoding="utf-8")
    recorded = _record(tmp_path, summary, "projects/pcr02", "receipt:1")
    memory_id = recorded["record"]["memory_id"]

    forgotten = _dispatch(
        tmp_path,
        _args(
            "memory-forget",
            "--principal-id",
            "user:alice",
            "--agent-id",
            "embedded-expert",
            "--scope-ref",
            "projects/pcr02",
            "--memory-id",
            memory_id,
        ),
    )

    assert forgotten["status"] == "recorded"
    assert len(forgotten["receipt_sha256"]) == 64
    assert _list(tmp_path, "projects/pcr02")["memories"] == []


def test_memory_summary_file_rejects_symlink(tmp_path):
    target = tmp_path / "secret.txt"
    target.write_text("Do not follow this symlink.", encoding="utf-8")
    link = tmp_path / "summary.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")

    with pytest.raises(KnowledgeHubError, match="summary file is unavailable"):
        _load_summary(str(link))


def test_memory_record_requires_file_not_raw_summary_argument():
    with pytest.raises(SystemExit):
        _parser().parse_args(
            [
                "memory-record",
                "--principal-id",
                "user:alice",
                "--agent-id",
                "embedded-expert",
                "--scope-ref",
                "projects/pcr02",
                "--level",
                "semantic",
                "--summary",
                "raw secret on argv",
            ]
        )
