"""External snapshot candidates may never stand in for origin/migration proof."""

import copy
import hashlib
import json
import os
import stat
import subprocess
import sys

import pytest

from tools.codex_assets.knowledge_hub import external_source_snapshot as snapshot


def _hub(tmp_path):
    hub = tmp_path / "hub"
    (hub / "registry").mkdir(parents=True)
    (hub / "registry/sources.json").write_text(
        json.dumps({"sources": [{"id": "demo"}]}) + "\n", encoding="utf-8")
    (hub / "registry/retired-sources.jsonl").write_text(
        json.dumps({"id": "legacy"}) + "\n", encoding="utf-8")
    return hub


def test_deterministic_private_manifest_and_unverified_boundaries(tmp_path):
    hub = _hub(tmp_path)
    origin = tmp_path / "origin"
    (origin / "nested").mkdir(parents=True)
    (origin / "a.md").write_text("first text", encoding="utf-8")
    (origin / "nested/b.md").write_text("中文", encoding="utf-8")
    (origin / ".git").mkdir()
    (origin / ".git/HEAD").write_text("ignored metadata", encoding="utf-8")
    before = sorted(str(x) for x in origin.rglob("*"))
    result = snapshot.capture_source_snapshot(hub, "demo", origin, "a" * 40)
    assert result == snapshot.capture_source_snapshot(hub, "demo", origin, "a" * 40)
    assert result["file_count"] == 2
    assert result["total_bytes"] == len("first text".encode()) + len("中文".encode())
    assert result["files"][0] == {
        "relative_path": "a.md", "size_bytes": 10,
        "sha256": hashlib.sha256(b"first text").hexdigest()}
    assert result["files"][1]["relative_path"] == "nested/b.md"
    assert result["claimed_revision_verified"] is False
    assert result["origin_binding_verified"] is False
    assert result["atomic_snapshot_verified"] is False
    assert result["target_disposition_verified"] is False
    assert result["full_external_migration_proven"] is False
    assert str(origin) not in json.dumps(result)
    name = snapshot.persist_private_snapshot(hub, result)
    assert name == snapshot.persist_private_snapshot(hub, result)
    target = hub / name
    assert not stat.S_IMODE(target.stat().st_mode) & 0o077
    assert "/.tmp/source-snapshots/demo/" in "/" + name
    assert "first text" not in target.read_text(encoding="utf-8")
    assert before == sorted(str(x) for x in origin.rglob("*"))


def test_single_file_and_retired_source(tmp_path):
    hub = _hub(tmp_path)
    one = tmp_path / "history.jsonl"
    one.write_text('{"event":"old"}\n', encoding="utf-8")
    result = snapshot.capture_source_snapshot(hub, "legacy", one)
    assert result["source_kind"] == "single-file"
    assert result["file_count"] == 1
    assert result["files"][0]["relative_path"] == "history.jsonl"
    assert result["claimed_revision"] == ""


def test_rejects_unregistered_and_untrusted_revision(tmp_path):
    hub = _hub(tmp_path)
    one = tmp_path / "a.txt"
    one.write_text("value", encoding="utf-8")
    with pytest.raises(snapshot.SourceSnapshotError, match="not registered"):
        snapshot.capture_source_snapshot(hub, "not-registered", one)
    with pytest.raises(snapshot.SourceSnapshotError, match="claimed revision"):
        snapshot.capture_source_snapshot(hub, "demo", one, "main")


def test_rejects_symlinks_instead_of_following(tmp_path):
    hub = _hub(tmp_path)
    origin = tmp_path / "origin"
    origin.mkdir()
    (origin / "link").symlink_to(tmp_path)
    with pytest.raises(snapshot.SourceSnapshotError, match="symlink"):
        snapshot.capture_source_snapshot(hub, "demo", origin)
    (origin / "link").unlink()
    link = tmp_path / "source-link"
    link.symlink_to(origin, target_is_directory=True)
    with pytest.raises(snapshot.SourceSnapshotError, match="symlink"):
        snapshot.capture_source_snapshot(hub, "demo", link)


def test_tampered_manifest_and_false_proof_fail_closed(tmp_path):
    hub = _hub(tmp_path)
    origin = tmp_path / "src.md"
    origin.write_text("one", encoding="utf-8")
    result = snapshot.capture_source_snapshot(hub, "demo", origin)
    for changed in (
        {"full_external_migration_proven": True},
        {"total_bytes": 0},
        {"capture_sha256": "0" * 64},
        {"claimed_revision_verified": True},
    ):
        mutated = copy.deepcopy(result)
        mutated.update(changed)
        with pytest.raises(snapshot.SourceSnapshotError):
            snapshot.validate_source_snapshot(mutated)


def test_source_budget_and_special_file_fail_closed(tmp_path, monkeypatch):
    hub = _hub(tmp_path)
    origin = tmp_path / "origin"
    origin.mkdir()
    (origin / "a.md").write_text("some data", encoding="utf-8")
    monkeypatch.setattr(snapshot, "MAX_TOTAL_BYTES", 2)
    with pytest.raises(snapshot.SourceSnapshotError, match="byte budget"):
        snapshot.capture_source_snapshot(hub, "demo", origin)
    monkeypatch.undo()
    if hasattr(os, "mkfifo"):
        os.mkfifo(origin / "pipe")
        with pytest.raises(snapshot.SourceSnapshotError, match="nonregular"):
            snapshot.capture_source_snapshot(hub, "demo", origin)


def test_private_output_does_not_follow_symlink(tmp_path):
    hub = _hub(tmp_path)
    origin = tmp_path / "a.txt"
    origin.write_text("some data", encoding="utf-8")
    result = snapshot.capture_source_snapshot(hub, "demo", origin)
    (hub / ".tmp").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(snapshot.SourceSnapshotError, match="symlink"):
        snapshot.persist_private_snapshot(hub, result)


def test_snapshot_rejects_unsafe_relative_path_even_with_valid_digest(tmp_path):
    hub = _hub(tmp_path)
    origin = tmp_path / "a.txt"
    origin.write_text("some data", encoding="utf-8")
    result = snapshot.capture_source_snapshot(hub, "demo", origin)
    result["files"][0]["relative_path"] = "../outside"
    intermediate = {k: v for k, v in result.items() if k != "capture_sha256"}
    result["capture_sha256"] = hashlib.sha256(snapshot._canonical(intermediate)).hexdigest()
    with pytest.raises(snapshot.SourceSnapshotError, match="relative path"):
        snapshot.validate_source_snapshot(result)


def test_inventory_public_entrypoint_snapshot_does_not_claim_closure(tmp_path):
    hub = _hub(tmp_path)
    origin = tmp_path / "origin"
    origin.mkdir()
    (origin / "a.md").write_text("content", encoding="utf-8")
    command = [sys.executable, "-m", "tools.codex_assets.knowledge_hub.inventory_cli",
               str(hub), "--snapshot-source-id", "demo",
               "--snapshot-source-path", str(origin), "--json"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "candidate"
    assert payload["file_count"] == 1
    assert payload["revision_verified"] is False
    assert payload["external_migration_proven"] is False
    assert payload["product_terminal_changed"] is False
    assert str(origin) not in result.stdout
    assert (hub / payload["private_local_manifest"]).is_file()
