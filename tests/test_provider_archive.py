import argparse
import json

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, load_jsonl
from tools.codex_assets.knowledge_hub.provider_archive import archive, main
from test_lifecycle import _root


def setup(tmp_path):
    (tmp_path / "hub").mkdir()
    root = _root(tmp_path / "hub")
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
