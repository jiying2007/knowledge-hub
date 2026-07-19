import datetime as dt
import json

import pytest

from tools.codex_assets.knowledge_hub.runtime_maintenance import (
    _delete_tree,
    _fchmod_identity_safe,
    _identity,
    apply_runtime_maintenance,
    plan_runtime_maintenance,
    runtime_maintenance_summary,
)
from tools.codex_assets.knowledge_hub.search import INDEX_SCHEMA_VERSION


def _journal(path, status, completed_at):
    path.mkdir(parents=True)
    (path / "journal.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "transaction_id": path.name,
                "status": status,
                "completed_at": completed_at,
            }
        )
        + "\n"
    )
    (path / "stage").mkdir()
    (path / "stage/data.txt").write_text("runtime\n")


def test_obsolete_search_cache_plan_and_apply_preserve_current_and_telemetry(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    old = cache / "search-index-v1.sqlite3"
    current = cache / "search-index-v{}.sqlite3".format(INDEX_SCHEMA_VERSION)
    telemetry = cache / "search-telemetry.jsonl"
    old.write_bytes(b"old")
    current.write_bytes(b"current")
    telemetry.write_text("{}\n")

    plan = plan_runtime_maintenance(
        tmp_path, dt.date(2026, 7, 18), scope="obsolete-search-index"
    )
    assert plan["status"] == "ready"
    assert [row["path"] for row in plan["candidates"]] == [
        ".cache/knowledge-hub/search-index-v1.sqlite3"
    ]
    assert plan["policy"]["telemetry_pruned"] is False

    applied = apply_runtime_maintenance(
        tmp_path, dt.date(2026, 7, 18), scope="obsolete-search-index"
    )
    assert applied["status"] == "applied"
    assert applied["deleted_count"] == 1
    assert not old.exists()
    assert current.exists()
    assert telemetry.exists()


def test_obsolete_search_cache_symlink_blocks_whole_plan(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    outside = tmp_path / "outside.sqlite3"
    outside.write_bytes(b"outside")
    (cache / "search-index-v1.sqlite3").symlink_to(outside)

    plan = plan_runtime_maintenance(
        tmp_path, dt.date(2026, 7, 18), scope="obsolete-search-index"
    )

    assert plan["status"] == "blocked"
    assert plan["candidate_count"] == 0
    assert plan["error_count"] == 1
    assert outside.read_bytes() == b"outside"


def test_terminal_transaction_retention_keeps_newest_and_incomplete(tmp_path):
    transactions = tmp_path / ".tmp/transactions"
    oldest = transactions / "oldest"
    newer = transactions / "newer"
    incomplete = transactions / "incomplete"
    _journal(oldest, "applied", "2026-01-01T00:00:00Z")
    _journal(newer, "rolled-back", "2026-02-01T00:00:00Z")
    _journal(incomplete, "applying", "2026-01-01T00:00:00Z")

    plan = plan_runtime_maintenance(
        tmp_path,
        dt.date(2026, 7, 18),
        scope="terminal-transactions",
        transaction_retention_days=30,
        transaction_min_keep=1,
    )
    assert plan["status"] == "ready"
    assert [row["path"] for row in plan["candidates"]] == [
        ".tmp/transactions/oldest"
    ]
    protected = {row["path"]: row["reason"] for row in plan["protected"]}
    assert protected[".tmp/transactions/newer"] == "minimum-newest-retention"
    assert protected[".tmp/transactions/incomplete"] == "non-terminal-transaction"

    applied = apply_runtime_maintenance(
        tmp_path,
        dt.date(2026, 7, 18),
        scope="terminal-transactions",
        transaction_retention_days=30,
        transaction_min_keep=1,
    )
    assert applied["status"] == "applied"
    assert not oldest.exists()
    assert newer.exists()
    assert incomplete.exists()


def test_transaction_tree_with_symlink_is_never_candidate(tmp_path):
    transaction = tmp_path / ".tmp/transactions/unsafe"
    _journal(transaction, "applied", "2026-01-01T00:00:00Z")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n")
    (transaction / "stage/link.txt").symlink_to(outside)

    plan = plan_runtime_maintenance(
        tmp_path,
        dt.date(2026, 7, 18),
        scope="terminal-transactions",
        transaction_retention_days=30,
        transaction_min_keep=1,
    )

    assert plan["status"] == "ready"
    assert plan["candidate_count"] == 0
    assert transaction.exists()
    assert outside.read_text() == "outside\n"


def test_fd_safe_tree_delete_never_follows_raced_internal_symlink(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_file = outside / "keep.txt"
    outside_file.write_text("keep\n")
    (target / "raced-link").symlink_to(outside, target_is_directory=True)

    _delete_tree(target)

    assert not target.exists()
    assert outside_file.read_text() == "keep\n"


def test_descriptor_bound_chmod_rejects_raced_symlink(tmp_path):
    target = tmp_path / "runtime.json"
    outside = tmp_path / "outside.json"
    target.write_text("runtime\n")
    outside.write_text("outside\n")
    outside.chmod(0o644)
    expected = _identity(target)
    target.unlink()
    target.symlink_to(outside)

    with pytest.raises(OSError):
        _fchmod_identity_safe(target, expected, 0o600)

    assert outside.stat().st_mode & 0o777 == 0o644


def test_runtime_permission_plan_and_apply_harden_directories_and_files(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    runtime_tmp = tmp_path / ".tmp/nested"
    cache.mkdir(parents=True)
    runtime_tmp.mkdir(parents=True)
    cache_file = cache / "telemetry.jsonl"
    runtime_file = runtime_tmp / "state.json"
    cache_file.write_text("{}\n")
    runtime_file.write_text("{}\n")
    for path in (cache, runtime_tmp.parent, runtime_tmp):
        path.chmod(0o755)
    for path in (cache_file, runtime_file):
        path.chmod(0o644)

    plan = plan_runtime_maintenance(
        tmp_path, dt.date(2026, 7, 18), scope="runtime-permissions"
    )
    assert plan["status"] == "ready"
    assert plan["candidate_count"] == 5
    assert {row["action"] for row in plan["candidates"]} == {"chmod"}

    applied = apply_runtime_maintenance(
        tmp_path, dt.date(2026, 7, 18), scope="runtime-permissions"
    )
    assert applied["status"] == "applied"
    assert applied["hardened_count"] == 5
    assert applied["deleted_count"] == 0
    assert cache.stat().st_mode & 0o777 == 0o700
    assert cache_file.stat().st_mode & 0o777 == 0o600
    assert runtime_tmp.stat().st_mode & 0o777 == 0o700
    assert runtime_file.stat().st_mode & 0o777 == 0o600


def test_runtime_maintenance_summary_aggregates_protected_rows():
    payload = {
        "action": "runtime-maintenance-plan",
        "status": "ready",
        "scope": "all",
        "candidate_count": 0,
        "candidates": [],
        "protected_count": 3,
        "protected": [
            {"path": "one", "reason": "minimum-newest-retention"},
            {"path": "two", "reason": "minimum-newest-retention"},
            {"path": "three", "reason": "current-schema-version"},
        ],
        "errors": [],
    }

    summary = runtime_maintenance_summary(payload)

    assert summary["projection"] == "runtime-maintenance-summary-v1"
    assert summary["protected_by_reason"] == {
        "current-schema-version": 1,
        "minimum-newest-retention": 2,
    }
    assert "protected" not in summary


def test_runtime_permission_plan_excludes_managed_engineering_venv(tmp_path):
    target = tmp_path / ".tmp/engineering/venv/bin/python"
    target.parent.mkdir(parents=True)
    outside = tmp_path / "python-base"
    outside.write_text("runtime\n")
    target.symlink_to(outside)

    plan = plan_runtime_maintenance(
        tmp_path, dt.date(2026, 7, 18), scope="runtime-permissions"
    )

    assert plan["status"] == "ready"
    assert not any(
        str(row["path"]).startswith(".tmp/engineering/venv")
        for row in plan["candidates"]
    )
