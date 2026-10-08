import json
import fcntl
import multiprocessing
import os

import pytest

import tools.codex_assets.knowledge_hub.store as store_module
import tools.codex_assets.knowledge_hub.recovery_cli as recovery_cli
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.recovery_cli import (
    project_recovery_payload,
    serialized_recovery_payload,
)
from tools.codex_assets.knowledge_hub.store import RepositoryTransaction, audit_transactions, incomplete_transactions


def _hold_repository_lock(lock_path, ready, release):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        ready.set()
        release.wait(5)
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _terminate_at_replace(root, phase):
    transaction = RepositoryTransaction(root, 'process-exit')
    transaction.add_text('one.txt', 'after\n')
    original = store_module.os.replace

    def replace(source, target):
        if str(target) == str(root / 'one.txt') and phase == 'before':
            os._exit(73)
        original(source, target)
        if str(target) == str(root / 'one.txt') and phase == 'after':
            os._exit(73)

    store_module.os.replace = replace
    transaction.apply()


@pytest.mark.parametrize('phase', ['before', 'after'])
def test_hard_exit_is_reconciled_and_later_user_changes_are_protected(tmp_path, phase):
    target = tmp_path / 'one.txt'
    target.write_text('before\n')
    child = multiprocessing.Process(target=_terminate_at_replace, args=(tmp_path, phase))
    child.start()
    child.join(10)
    assert child.exitcode == 73
    audit = audit_transactions(tmp_path)['rows'][0]
    assert audit['recoverable']
    assert audit['reconciliation'][0]['state'] == phase
    if phase == 'after':
        assert audit['applied_paths'] == ['one.txt']
        target.write_text('later-user-write\n')
        conflict = audit_transactions(tmp_path)['rows'][0]
        assert not conflict['recoverable'] and conflict['conflict_paths'] == ['one.txt']
        assert target.read_text() == 'later-user-write\n'


def test_transaction_apply_is_idempotent(tmp_path):
    transaction = RepositoryTransaction(tmp_path, "apply")
    transaction.add_text("nested/a.txt", "value\n")
    assert transaction.plan()["changed_count"] == 1
    assert transaction.apply().status == "applied"
    assert (tmp_path / "nested/a.txt").read_text() == "value\n"

    repeated = RepositoryTransaction(tmp_path, "repeat")
    repeated.add_text("nested/a.txt", "value\n")
    assert repeated.apply().status == "no-change"


def test_original_snapshot_cannot_be_replaced_by_late_hash(tmp_path):
    from tools.codex_assets.knowledge_hub.common import file_sha256

    target = tmp_path / 'registry/items.jsonl'
    target.parent.mkdir()
    target.write_text('old\n')
    snapshot = {'registry/items.jsonl':file_sha256(target)}
    target.write_text('another-successful-write\n')
    transaction = RepositoryTransaction(tmp_path, expected_inputs=snapshot)
    transaction.add_text('registry/items.jsonl', 'stale-snapshot\n', expected_sha256=file_sha256(target))
    with pytest.raises(KnowledgeHubError, match='snapshot changed'):
        transaction.apply()
    assert target.read_text() == 'another-successful-write\n'


def test_failure_after_replace_before_journal_is_rolled_back(tmp_path, monkeypatch):
    target = tmp_path / 'one.txt'
    target.write_text('before\n')
    transaction = RepositoryTransaction(tmp_path, 'replace-window')
    transaction.add_text('one.txt', 'after\n')
    original = store_module._fsync_directory
    injected = False

    def sync(path):
        nonlocal injected
        if path == tmp_path and not injected:
            injected = True
            raise OSError('failure after rename')
        return original(path)

    monkeypatch.setattr(store_module, '_fsync_directory', sync)
    with pytest.raises(KnowledgeHubError):
        transaction.apply()
    assert target.read_text() == 'before\n'
    assert incomplete_transactions(tmp_path) == []


@pytest.mark.parametrize('value', ['user-write\n', 'intended\n'])
def test_expected_missing_target_refuses_interleaved_creation(tmp_path, value):
    transaction = RepositoryTransaction(tmp_path, expected_inputs={})
    transaction.add_text('new.txt', 'intended\n')
    (tmp_path / 'new.txt').write_text(value)
    with pytest.raises(KnowledgeHubError, match='no longer missing'):
        transaction.apply()
    assert (tmp_path / 'new.txt').read_text() == value


def test_transaction_rolls_back_partial_apply(tmp_path, monkeypatch):
    (tmp_path / "one.txt").write_text("old-one\n")
    (tmp_path / "two.txt").write_text("old-two\n")
    transaction = RepositoryTransaction(tmp_path, "rollback")
    transaction.add_text("one.txt", "new-one\n")
    transaction.add_text("two.txt", "new-two\n")

    real_replace = store_module.os.replace

    def injected_replace(source, target):
        if str(target).endswith("two.txt"):
            raise OSError("injected apply failure")
        return real_replace(source, target)

    monkeypatch.setattr(store_module.os, "replace", injected_replace)
    with pytest.raises(KnowledgeHubError):
        transaction.apply()

    assert (tmp_path / "one.txt").read_text() == "old-one\n"
    assert (tmp_path / "two.txt").read_text() == "old-two\n"
    assert incomplete_transactions(tmp_path) == []
    journal = json.loads((tmp_path / ".tmp/transactions/rollback/journal.json").read_text())
    assert journal["status"] == "rolled-back"


def test_single_writer_lock_rejects_concurrent_apply_without_partial_write(tmp_path):
    target = tmp_path / "registry/items.jsonl"
    target.parent.mkdir(parents=True)
    target.write_text("before\n")
    transaction = RepositoryTransaction(tmp_path, "concurrent-writer")
    transaction.add_text("registry/items.jsonl", "after\n")
    ready = multiprocessing.Event()
    release = multiprocessing.Event()
    holder = multiprocessing.Process(
        target=_hold_repository_lock,
        args=(tmp_path / ".tmp/locks/knowledge-hub.lock", ready, release),
    )
    holder.start()
    assert ready.wait(5)
    try:
        with pytest.raises(KnowledgeHubError, match="another Knowledge Hub write transaction is active"):
            transaction.apply()
        assert target.read_text() == "before\n"
        assert incomplete_transactions(tmp_path) == []
    finally:
        release.set()
        holder.join(5)
        if holder.is_alive():
            holder.terminate()


def test_recovery_audit_reports_interrupted_transaction_without_writing(tmp_path):
    journal_dir = tmp_path / ".tmp/transactions/interrupted"
    backup = journal_dir / "before/registry/items.jsonl"
    backup.parent.mkdir(parents=True)
    backup.write_text("before\n")
    journal = {
        "schema_version": 1,
        "transaction_id": "interrupted",
        "status": "applying",
        "writes": [{"path": "registry/items.jsonl"}],
        "applied_paths": ["registry/items.jsonl"],
        "rollback_paths": [],
    }
    (journal_dir / "journal.json").write_text(json.dumps(journal))

    result = audit_transactions(tmp_path)

    assert result["status"] == "needs-recovery-review"
    assert result["attention_count"] == 1
    assert result["rows"][0]["recoverable"] is True
    assert backup.read_text() == "before\n"


def test_recovery_audit_treats_invalid_journal_as_attention_required(tmp_path):
    journal_dir = tmp_path / ".tmp/transactions/broken"
    journal_dir.mkdir(parents=True)
    (journal_dir / "journal.json").write_text("{not-json")

    result = audit_transactions(tmp_path)

    assert result["status"] == "needs-recovery-review"
    assert result["attention_count"] == 1
    assert result["rows"][0]["requires_attention"] is True
    assert result["rows"][0]["recoverable"] is False


def test_recovery_projection_is_bounded_and_has_summary_mode():
    payload = {
        "schema_version": 1,
        "status": "pass",
        "transaction_count": 3,
        "attention_count": 0,
        "rows": [{"transaction_id": str(index)} for index in range(3)],
    }

    page = project_recovery_payload(payload, limit=2, offset=0)
    summary = project_recovery_payload(payload, limit=2, offset=0, include_rows=False)

    assert [row["transaction_id"] for row in page["rows"]] == ["0", "1"]
    assert page["pagination"]["has_next"] is True
    assert page["pagination"]["next_offset"] == 2
    assert summary["projection"] == "knowledge-recovery-audit-summary-v1"
    assert "rows" not in summary


def test_recovery_cli_summary_uses_full_status_and_omits_rows(monkeypatch, tmp_path, capsys):
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "items.jsonl").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        recovery_cli,
        "audit_transactions",
        lambda _root, _transaction_id: {
            "schema_version": 1,
            "read_only": True,
            "status": "pass",
            "transaction_count": 2,
            "attention_count": 0,
            "rows": [
                {"transaction_id": "a"},
                {"transaction_id": "b"},
            ],
            "must_not": [],
        },
    )

    assert recovery_cli.main(
        ["--root", str(tmp_path), "--summary-json", "--limit", "1"]
    ) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["projection"] == "knowledge-recovery-audit-summary-v1"
    assert payload["pagination"]["total_count"] == 2
    assert "rows" not in payload


def test_recovery_serialization_fails_closed_when_projection_exceeds_budget():
    with pytest.raises(ValueError, match="output budget exceeded"):
        serialized_recovery_payload(
            {"schema_version": 1, "status": "pass", "rows": ["x" * 256]},
            maximum_bytes=64,
        )


def test_transaction_rejects_symlink_target_even_when_it_resolves_inside_root(tmp_path):
    real_target = tmp_path / "real.txt"
    real_target.write_text("before\n")
    link = tmp_path / "linked.txt"
    link.symlink_to(real_target)
    transaction = RepositoryTransaction(tmp_path, "symlink-target")
    transaction.add_text("linked.txt", "after\n")

    with pytest.raises(KnowledgeHubError, match="symlink"):
        transaction.plan()

    assert real_target.read_text() == "before\n"


def test_transaction_runtime_journal_lock_and_backups_are_private(tmp_path):
    target = tmp_path / "registry/items.jsonl"
    target.parent.mkdir(parents=True)
    target.write_text("before\n")
    transaction = RepositoryTransaction(tmp_path, "private-runtime")
    transaction.add_text("registry/items.jsonl", "after\n")

    transaction.apply()

    assert (tmp_path / ".tmp").stat().st_mode & 0o777 == 0o700
    assert (tmp_path / ".tmp/transactions/private-runtime").stat().st_mode & 0o777 == 0o700
    assert transaction.stage_root.stat().st_mode & 0o777 == 0o700
    assert (transaction.backup_root / "registry").stat().st_mode & 0o777 == 0o700
    assert transaction.journal_path.stat().st_mode & 0o777 == 0o600
    assert (transaction.backup_root / "registry/items.jsonl").stat().st_mode & 0o777 == 0o600
    assert transaction.lock_path.stat().st_mode & 0o777 == 0o600
