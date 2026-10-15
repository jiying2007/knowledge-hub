"""Candidate source reconciliation is private, bounded and never closes gates."""

import hashlib
import json
import subprocess
import sys

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.external_source_snapshot import (
    SourceSnapshotError, capture_source_snapshot, persist_private_snapshot,
)
from tools.codex_assets.knowledge_hub.source_snapshot_reconcile import (
    reconcile_private_snapshot,
)


def _fixture(tmp_path):
    root = tmp_path / "hub"
    (root / "registry").mkdir(parents=True)
    (root / "registry/sources.json").write_text(json.dumps({
        "sources": [{"id": "demo", "origin_path": "~/source"}]
    }) + "\n", encoding="utf-8")
    (root / "registry/retired-sources.jsonl").write_text(
        json.dumps({"id": "old", "origin_path": "~/old/item.md"}) + "\n",
        encoding="utf-8")
    (root / "sources/demo").mkdir(parents=True)
    (root / "sources/demo/inventory.jsonl").write_text("", encoding="utf-8")
    (root / "sources/old").mkdir()
    (root / "sources/old/inventory.jsonl").write_text("", encoding="utf-8")
    origin = tmp_path / "source"
    origin.mkdir()
    (origin / "a.md").write_text("real bytes", encoding="utf-8")
    manifest = persist_private_snapshot(root, capture_source_snapshot(root, "demo", origin))
    return root, origin, manifest


def _write_inventory(root, rows, source_id="demo"):
    (root / "sources" / source_id / "inventory.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _file_row(content="real bytes", **kwargs):
    return {"id": "demo-file", "source_id": "demo",
            "origin_path": "~/source/a.md", "hub_disposition": "copy-body",
            "target_path": "projects/example/a.md",
            "size_bytes": len(content.encode()),
            "sha256": hashlib.sha256(content.encode()).hexdigest(), **kwargs}


def test_exact_candidate_is_not_external_migration_proof(tmp_path):
    root, origin, manifest = _fixture(tmp_path)
    _write_inventory(root, [_file_row()])
    before = (origin / "a.md").read_bytes()
    result = reconcile_private_snapshot(root, root / manifest)
    assert result["status"] == "needs-review"
    assert result["exact_hash_size_candidates"] == 1
    assert result["all_candidate_files_have_exact_inventory_hash"] is True
    assert result["full_external_migration_proven"] is False
    assert result["source_revision_verified"] is False
    assert result["atomic_source_snapshot_verified"] is False
    assert result["snapshot_rechecked_against_live_source"] is False
    assert result["target_disposition_verified"] is False
    assert result["raw_paths_exposed"] is False
    assert "a.md" not in json.dumps(result)
    assert (origin / "a.md").read_bytes() == before


def test_root_batch_record_cannot_match_a_real_file(tmp_path):
    root, _, manifest = _fixture(tmp_path)
    _write_inventory(root, [{
        "id": "root", "source_id": "demo", "origin_path": "~/source",
        "status": "covered", "sha256": "a" * 64, "size_bytes": 100,
    }])
    result = reconcile_private_snapshot(root, root / manifest)
    assert result["source_inventory_row_count"] == 1
    assert result["file_scoped_inventory_row_count"] == 0
    assert result["root_batch_or_out_of_scope_row_count"] == 1
    assert result["no_file_row"] == 1
    assert result["all_candidate_files_have_exact_inventory_hash"] is False


def test_missing_digest_and_mismatch_both_remain_unverified(tmp_path):
    root, _, manifest = _fixture(tmp_path)
    row = _file_row()
    row["sha256"] = ""
    _write_inventory(root, [row])
    result = reconcile_private_snapshot(root, root / manifest)
    assert result["file_row_without_digest"] == 1
    assert result["status"] == "needs-review"
    _write_inventory(root, [_file_row("not the same")])
    result = reconcile_private_snapshot(root, root / manifest)
    assert result["hash_or_size_mismatch"] == 1
    assert result["status"] == "needs-fix"
    assert result["full_external_migration_proven"] is False


def test_duplicate_source_rows_do_not_match_candidate(tmp_path):
    root, _, manifest = _fixture(tmp_path)
    row = _file_row()
    _write_inventory(root, [row, dict(row, id="duplicate")])
    result = reconcile_private_snapshot(root, root / manifest)
    assert result["ambiguous_file_rows"] == 1
    assert result["exact_hash_size_candidates"] == 0
    assert result["status"] == "needs-fix"


def test_extra_scoped_file_in_inventory_is_visible(tmp_path):
    root, _, manifest = _fixture(tmp_path)
    extra = dict(_file_row(), id="extra", origin_path="~/source/old.md")
    _write_inventory(root, [_file_row(), extra])
    result = reconcile_private_snapshot(root, root / manifest)
    assert result["file_scoped_inventory_rows_not_in_snapshot"] == 1
    assert result["all_candidate_files_have_exact_inventory_hash"] is False


def test_single_file_retired_source_is_scoped_without_owner_promotion(tmp_path):
    root, _, _ = _fixture(tmp_path)
    source = tmp_path / "old-item.md"
    source.write_text("old evidence", encoding="utf-8")
    digest = hashlib.sha256(b"old evidence").hexdigest()
    _write_inventory(root, [{
        "id": "old", "source_id": "old", "origin_path": "~/old/item.md",
        "sha256": digest, "size_bytes": 12, "hub_disposition": "reference-only",
    }], source_id="old")
    manifest = persist_private_snapshot(root, capture_source_snapshot(root, "old", source))
    result = reconcile_private_snapshot(root, root / manifest)
    assert result["source_registry_bucket"] == "retired"
    assert result["exact_hash_size_candidates"] == 1
    assert result["full_content_review_proven"] is False


def test_private_snapshot_path_and_symlink_are_rejected(tmp_path):
    root, _, manifest = _fixture(tmp_path)
    _write_inventory(root, [_file_row()])
    with pytest.raises(SourceSnapshotError, match="private snapshots"):
        reconcile_private_snapshot(root, tmp_path / "arbitrary.json")
    link = root / ".tmp/source-snapshots/demo/not-a-snapshot.json"
    link.symlink_to(root / manifest)
    with pytest.raises(SourceSnapshotError):
        reconcile_private_snapshot(root, link)
    candidate = root / manifest
    candidate.unlink()
    candidate.symlink_to(root / "registry/sources.json")
    with pytest.raises(SourceSnapshotError, match="linked"):
        reconcile_private_snapshot(root, candidate)


def test_invalid_manifest_and_inventory_are_fail_closed(tmp_path):
    root, _, manifest = _fixture(tmp_path)
    path = root / manifest
    path.write_text('{"full_external_migration_proven":true}', encoding="utf-8")
    with pytest.raises(SourceSnapshotError):
        reconcile_private_snapshot(root, path)
    path.unlink()
    manifest = persist_private_snapshot(
        root, capture_source_snapshot(root, "demo", tmp_path / "source"))
    inventory = root / "sources/demo/inventory.jsonl"
    inventory.unlink()
    inventory.symlink_to(tmp_path / "source/a.md")
    with pytest.raises(KnowledgeHubError):
        reconcile_private_snapshot(root, root / manifest)


def test_cli_reuses_existing_inventory_wrapper_without_second_authority(tmp_path):
    root, _, manifest = _fixture(tmp_path)
    _write_inventory(root, [_file_row()])
    run = subprocess.run([
        sys.executable, "-m", "tools.codex_assets.knowledge_hub.inventory_cli",
        str(root), "--reconcile-snapshot", manifest, "--json",
    ], capture_output=True, text=True, timeout=15, check=False)
    assert run.returncode == 0, run.stderr
    result = json.loads(run.stdout)
    assert result["status"] == "needs-review"
    assert result["exact_hash_size_candidates"] == 1
    assert result["full_external_migration_proven"] is False
    assert "real bytes" not in run.stdout
    assert str(tmp_path) not in run.stdout
