"""CAS revisions preserve candidate identity, immutable body and audit history."""

import pytest

from test_provider_subjects import subject_root
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, load_jsonl, load_markdown, render_markdown
from tools.codex_assets.knowledge_hub.provider_operations import archive, reconcile
from tools.codex_assets.knowledge_hub.provider_cli import validate_arguments
from tools.codex_assets.knowledge_hub.store import audit_transactions


def revision(tmp_path):
    root, source, args = subject_root(tmp_path)
    first = archive(root, args)
    before = load_jsonl(root / "registry/items.jsonl")[0]
    _, body = load_markdown(root / before["path"])
    source.write_text(
        render_markdown(
            {"title": before["title"], "summary_zh": "中文用途：创建模板滤波任务，结果和参数须绑定版本核验。"}, body
        )
    )
    args.item_id = first["item_id"]
    args.expected_before_sha256 = first["content_sha256"]
    args.apply = False
    return root, source, args, first, before, body


def test_revision_plan_apply_replay_and_reconcile(tmp_path):
    root, _, args, first, before, body = revision(tmp_path)
    validate_arguments(args)
    original_ledger = load_jsonl(root / "registry/provider-operations.jsonl")
    original_registry = (root / "registry/items.jsonl").read_bytes()
    plan = archive(root, args)
    assert plan["status"] == "PLANNED" and plan["persisted"] is False
    assert (root / "registry/items.jsonl").read_bytes() == original_registry
    args.expected_content_sha256 = plan["content_sha256"]
    args.apply = True
    done = archive(root, args)
    assert done["status"] == "ARCHIVED" and done["persisted"] is True
    assert done["item_id"] == first["item_id"] and done["operation_id"] == plan["operation_id"]
    after = load_jsonl(root / "registry/items.jsonl")[0]
    for key in (
        "id",
        "path",
        "subject_ref",
        "created_subject_ref",
        "owner",
        "source",
        "status",
        "promotion",
        "provider_operation_id",
    ):
        assert after[key] == before[key]
    assert load_markdown(root / after["path"])[1] == body
    assert "中文用途" in after["summary_zh"]
    ledger = load_jsonl(root / "registry/provider-operations.jsonl")
    assert ledger[:-1] == original_ledger and ledger[-1]["action"] == "metadata"
    assert ledger[-1]["before_content_sha256"] == first["content_sha256"]
    assert reconcile(root, done["operation_id"], done["content_sha256"])["status"] == "VERIFIED"
    assert reconcile(root, first["operation_id"], first["content_sha256"])["status"] == "CONFLICT"
    assert archive(root, args)["status"] == "ALREADY_ARCHIVED"
    assert load_jsonl(root / "registry/provider-operations.jsonl") == ledger
    assert audit_transactions(root)["attention_count"] == 0


@pytest.mark.parametrize(
    "change", ["before", "after", "body", "title", "subject", "promotion", "secret", "provenance", "active"]
)
def test_revision_denials_are_zero_write(tmp_path, change):
    root, source, args, first, before, body = revision(tmp_path)
    if change == "before":
        args.expected_before_sha256 = "0" * 64
    elif change == "after":
        args.expected_content_sha256 = "0" * 64
    elif change == "body":
        source.write_text(render_markdown({"title": before["title"], "summary_zh": "新摘要"}, body + "\n额外正文\n"))
    elif change == "title":
        source.write_text(render_markdown({"title": "更换标题", "summary_zh": "新摘要"}, body))
    elif change == "subject":
        args.subject = "domain:embedded"
    elif change == "secret":
        source.write_text('---\nsummary_zh: "token=sk-1234567890123456789012345678901234567890"\n---\n# X\n')
    elif change == "provenance":
        args.provenance_file = str(source)
    else:
        # Frontmatter ownership is never accepted from a source file.
        source.write_text(render_markdown({"title": before["title"], "summary_zh": "新摘要", change: "active"}, body))
    snapshot = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    args.apply = True
    with pytest.raises(KnowledgeHubError):
        archive(root, args)
    for relative, raw in snapshot.items():
        assert (root / relative).read_bytes() == raw
    assert len(load_jsonl(root / "registry/provider-operations.jsonl")) == 1


def test_revision_requires_frozen_before_hash_and_cannot_repeat_with_other_stale_hash(tmp_path):
    root, _, args, _, _, _ = revision(tmp_path)
    args.expected_before_sha256 = ""
    with pytest.raises(KnowledgeHubError, match="CONTENT_HASH_REQUIRED"):
        archive(root, args)
    args.expected_before_sha256 = load_jsonl(root / "registry/provider-operations.jsonl")[0]["content_sha256"]
    args.apply = True
    archive(root, args)
    args.expected_before_sha256 = "f" * 64
    with pytest.raises(KnowledgeHubError, match="CONTENT_DRIFT"):
        archive(root, args)


def test_revision_rejects_interleaved_registry_change_before_writing(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub.store import RepositoryTransaction, WriteConflict

    root, _, args, _, before, _ = revision(tmp_path)
    original = RepositoryTransaction.apply
    document = (root / before["path"]).read_bytes()
    ledger = (root / "registry/provider-operations.jsonl").read_bytes()

    def interleave(transaction):
        path = root / "registry/items.jsonl"
        path.write_bytes(path.read_bytes() + b"\n")
        return original(transaction)

    monkeypatch.setattr(RepositoryTransaction, "apply", interleave)
    args.apply = True
    with pytest.raises(WriteConflict):
        archive(root, args)
    assert (root / before["path"]).read_bytes() == document
    assert (root / "registry/provider-operations.jsonl").read_bytes() == ledger
