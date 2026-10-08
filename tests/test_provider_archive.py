import argparse
import json
import shutil
import pathlib

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, load_jsonl
from tools.codex_assets.knowledge_hub.provider_archive import archive, main
from test_lifecycle import _root


def setup(tmp_path):
    (tmp_path / "hub").mkdir()
    root = _root(tmp_path / "hub")
    shutil.copytree(pathlib.Path(__file__).resolve().parents[1] / "schemas", root / "schemas")
    (root / "registry/owners.json").write_text('{"owners":[{"id":"leiwenjun"}]}')
    (root / "registry/project-routes.json").write_text(json.dumps({"schema_version": 2, "routes": [{
        "project_id": "test", "archive_path": "projects/test/archive", "validation_path": "projects/test/validation",
    }]}))
    (root / "registry/provider-archive-policy.json").write_text(json.dumps({
        "schema_version": 1, "enabled": True, "mode": "candidate-only", "owner_id": "leiwenjun",
        "allowed_kinds": ["validation", "runbook"], "maximum_bytes": 131072,
    }))
    source = tmp_path / "input.md"
    source.write_text("# 验证记录\n\n结论：事务和索引同步验证通过。\n")
    args = argparse.Namespace(source=str(source), project="test", kind="validation", title="",
                              sanitized=True, apply=True, as_of="2026-10-05")
    return root, source, args


def test_archive_atomic_receipt_and_retry(tmp_path):
    root, source, args = setup(tmp_path)
    first = archive(root, args)
    assert first["status"] == "ARCHIVED"
    assert first["persisted"] and first["write_performed"]
    item = load_jsonl(root / "registry/items.jsonl")[0]
    assert item["status"] == "reviewing" and item["promotion"] == "none"
    assert item["generated_by_ai"] and item["manual_validation_pending"]
    assert first["item_id"] in (root / "indexes/by-status.md").read_text()
    before = (root / "registry/items.jsonl").read_bytes()
    retry = archive(root, args)
    assert retry["status"] == "ALREADY_ARCHIVED" and not retry["write_performed"]
    assert retry["content_sha256"] == first["content_sha256"]
    assert (root / "registry/items.jsonl").read_bytes() == before
    (root / first["target"]).write_text("# changed\n")
    with pytest.raises(KnowledgeHubError, match="content drift"):
        archive(root, args)


def test_dry_run_never_claims_persistence(tmp_path):
    root, _, args = setup(tmp_path)
    args.apply = False
    result = archive(root, args)
    assert result["status"] == "PLANNED" and not result["persisted"]
    assert (root / "registry/items.jsonl").read_text() == ""
    assert not (root / result["target"]).exists()


@pytest.mark.parametrize("change", ["secret", "route", "kind", "owner", "metadata", "sanitized", "disabled", "symlink", "size", "session"])
def test_negative_paths_do_not_write(tmp_path, change):
    root, source, args = setup(tmp_path)
    policy = json.loads((root / "registry/provider-archive-policy.json").read_text())
    if change == "secret":
        source.write_text("# 秘密\n\npassword=" + "a" * 20)
    elif change == "route":
        args.project = "unknown"
    elif change == "kind":
        args.kind = "decision"
    elif change == "owner":
        policy["owner_id"] = "unknown"
    elif change == "metadata":
        source.write_text("---\nhuman_reviewed_by: somebody\n---\n\n# 不可代签\n")
    elif change == "sanitized":
        args.sanitized = False
    elif change == "disabled":
        policy["enabled"] = False
    elif change == "symlink":
        link = tmp_path / "link.md"
        link.symlink_to(source)
        args.source = str(link)
    elif change == "size":
        source.write_text("a" * 131073)
    elif change == "session":
        source.write_text('# 原始会话\n{"type":"response_item"}\n')
    (root / "registry/provider-archive-policy.json").write_text(json.dumps(policy))
    with pytest.raises(KnowledgeHubError):
        archive(root, args)
    assert (root / "registry/items.jsonl").read_text() == ""


def test_public_error_does_not_echo_secret(tmp_path, capsys):
    root, source, _ = setup(tmp_path)
    source.write_text("password=" + "a" * 20)
    assert main(["--root", str(root), "--project", "test", "--source", str(source),
                 "--kind", "validation", "--sanitized", "--apply"]) == 2
    output = capsys.readouterr().out
    assert "a" * 20 not in output
    assert json.loads(output)["persisted"] is False


@pytest.mark.parametrize('invalid', [None, 'validation', {}, ['validation', 'validation']])
def test_malformed_policy_returns_public_json_without_writing(tmp_path, capsys, invalid):
    root, source, _ = setup(tmp_path)
    policy_path = root / 'registry/provider-archive-policy.json'
    policy = json.loads(policy_path.read_text())
    policy['allowed_kinds'] = invalid
    policy_path.write_text(json.dumps(policy))
    assert main(['--root', str(root), '--project', 'test', '--source', str(source),
                 '--kind', 'validation', '--sanitized', '--apply']) == 2
    receipt = json.loads(capsys.readouterr().out)
    assert receipt['reason_code'] == 'policy-invalid'
    assert (root / 'registry/items.jsonl').read_text() == ''


def test_archive_preserves_descriptive_metadata(tmp_path):
    root, source, args = setup(tmp_path)
    source.write_text('---\nsummary_zh: 精确中文摘要\ntags: [事务, 验证]\n---\n# 验证记录\n\n另一段正文。\n')
    receipt = archive(root, args)
    item = load_jsonl(root / 'registry/items.jsonl')[0]
    assert item['summary_zh'] == '精确中文摘要'
    assert item['tags'] == ['provider-archive', 'validation', '事务', '验证']
    from tools.codex_assets.knowledge_hub.schemas import validate_instance
    assert validate_instance(root, 'provider-archive-receipt-v1', receipt)['status'] == 'pass'


def test_interleaved_capture_cannot_lose_successful_registry_update(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import lifecycle

    root, source, args = setup(tmp_path)
    other_source = tmp_path / 'other.md'
    other_source.write_text('# 独立候选\n\n独立结论。\n')
    other_args = argparse.Namespace(**vars(args))
    other_args.source = str(other_source)
    original = lifecycle.registry_items
    nested = {}

    def interleaved(root_arg):
        snapshot = original(root_arg)
        monkeypatch.setattr(lifecycle, 'registry_items', original)
        nested.update(archive(root, other_args))
        return snapshot

    monkeypatch.setattr(lifecycle, 'registry_items', interleaved)
    from tools.codex_assets.knowledge_hub.store import WriteConflict
    with pytest.raises(WriteConflict):
        archive(root, args)
    rows = original(root)
    assert len(rows) == 1 and rows[0]['id'] == nested['item_id']
    assert archive(root, args)['status'] == 'ARCHIVED'
    assert len(original(root)) == 2


def test_public_archive_retries_only_prewrite_conflicts_with_frozen_input(tmp_path, monkeypatch, capsys):
    from tools.codex_assets.knowledge_hub import provider_archive
    from tools.codex_assets.knowledge_hub.store import WriteConflict

    root, source, _ = setup(tmp_path)
    original = provider_archive.archive
    seen = []
    content = source.read_text()

    def conflict_once(root_arg, args):
        seen.append(pathlib.Path(args.source).read_text())
        if len(seen) == 1:
            source.write_text('# 后续用户改动\n')
            raise WriteConflict('another Knowledge Hub write transaction is active')
        return original(root_arg, args)

    monkeypatch.setattr(provider_archive, 'archive', conflict_once)
    assert main(['--root', str(root), '--project', 'test', '--source', str(source),
                 '--kind', 'validation', '--sanitized', '--apply']) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt['attempt_count'] == 2 and receipt['persisted']
    assert seen == [content, content]
    assert source.read_text() == '# 后续用户改动\n'
