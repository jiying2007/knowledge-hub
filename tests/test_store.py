import json
import fcntl
import multiprocessing

import pytest

import tools.codex_assets.knowledge_hub.store as store_module
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.store import RepositoryTransaction, audit_transactions, incomplete_transactions


def _hold_repository_lock(lock_path, ready, release):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        ready.set()
        release.wait(5)
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def test_transaction_apply_is_idempotent(tmp_path):
    transaction = RepositoryTransaction(tmp_path, "apply")
    transaction.add_text("nested/a.txt", "value\n")
    assert transaction.plan()["changed_count"] == 1
    assert transaction.apply().status == "applied"
    assert (tmp_path / "nested/a.txt").read_text() == "value\n"

    repeated = RepositoryTransaction(tmp_path, "repeat")
    repeated.add_text("nested/a.txt", "value\n")
    assert repeated.apply().status == "no-change"


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
