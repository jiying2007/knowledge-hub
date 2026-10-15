"""Single-canonical content evidence is bounded, read-only, non-authoritative."""

import hashlib
import json

import pytest

from tools.codex_assets.knowledge_hub import content_convergence as convergence
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


def _fixture(tmp_path):
    current = tmp_path / "registry/sources.json"
    _write_json(current, {"schema_version": 1, "sources": [{"id": "runtime-input"}]})
    retired = tmp_path / "registry/retired-sources.jsonl"
    retired.write_text(json.dumps({"id": "old-extract"}) + "\n", encoding="utf-8")

    runtime = tmp_path / "sources/runtime-input/inventory.jsonl"
    _write_json(runtime, {
        "source_id": "runtime-input", "origin_path": "~/.codex/sessions",
        "id": "runtime-input-root", "sha256": "", "size_bytes": 0,
        "status": "covered", "hub_disposition": "reference-only",
    })
    older = tmp_path / "sources/old-extract/inventory.jsonl"
    _write_json(older, {
        "source_id": "old-extract", "origin_path": "~/old/file.md",
        "id": "old-extract-file", "sha256": "a" * 64, "size_bytes": 12,
        "status": "covered", "hub_disposition": "copy-body",
    })
    files = {
        "projects/demo/current/a.md": "The exact canonical fact.\n",
        "projects/demo/current/b.md": "The exact canonical fact.\n",
        "domains/demo/archive/history.md": "Only historical evidence.\n",
    }
    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return list(reversed(list(files)))


def _scan(root, paths):
    return convergence.build_content_convergence(
        root, paths,
        {"projects/demo/current/a.md": ["item-active-1"]},
        {"domains/demo/archive/history.md": "frozen-archive-1"},
    )


def test_deterministic_file_level_hashes_and_duplicate_candidates(tmp_path):
    paths = _fixture(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix()
                    for path in tmp_path.rglob("*") if path.is_file())
    result = _scan(tmp_path, paths)
    assert result == _scan(tmp_path, list(reversed(paths)))
    assert result["contract"] == "knowledge-hub-content-convergence-observation-v1"
    assert result["body_count"] == 3
    assert result["exact_registry_count"] == 1
    assert result["frozen_collection_count"] == 1
    assert result["uncovered_count"] == 1
    assert result["exact_duplicate_candidate_count"] == 1
    assert result["exact_duplicate_candidates"][0]["paths"] == [
        "projects/demo/current/a.md",
        "projects/demo/current/b.md",
    ]
    digest = hashlib.sha256(b"The exact canonical fact.\n").hexdigest()
    assert result["exact_duplicate_candidates"][0]["sha256"] == digest
    assert result["read_only"] is True
    assert result["canonical_mutations"] == 0
    assert result["new_status_source"] is False
    assert result["full_external_migration_proven"] is False
    assert result["full_content_review_proven"] is False
    after = sorted(path.relative_to(tmp_path).as_posix()
                   for path in tmp_path.rglob("*") if path.is_file())
    assert before == after


def test_source_root_records_do_not_establish_external_file_completeness(tmp_path):
    paths = _fixture(tmp_path)
    sources = _scan(tmp_path, paths)["source_controls"]
    assert sources["current_source_count"] == 1
    assert sources["retired_source_count"] == 1
    assert sources["inventory_rows"] == 2
    assert sources["root_or_batch_rows"] == 1
    assert sources["rows_without_sha256"] == 1
    assert sources["file_level_candidate_rows"] == 1
    assert sources["file_level_sha256_rows"] == 1
    assert sources["external_source_snapshot_observed"] is False
    assert sources["full_external_migration_proven"] is False
    assert "Root/batch hashes never prove" in sources["proof_boundary"]


def test_rejects_duplicated_body_or_registry_authority(tmp_path):
    paths = _fixture(tmp_path)
    with pytest.raises(KnowledgeHubError, match="duplicate canonical body"):
        _scan(tmp_path, paths + [paths[0]])
    with pytest.raises(KnowledgeHubError, match="duplicate exact registry"):
        convergence.build_content_convergence(
            tmp_path, paths,
            {"projects/demo/current/a.md": ["a", "b"]}, {},
        )
    with pytest.raises(KnowledgeHubError, match="duplicate registry and collection"):
        convergence.build_content_convergence(
            tmp_path, paths,
            {"projects/demo/current/a.md": ["a"]},
            {"projects/demo/current/a.md": "collection"},
        )


def test_symlink_and_budget_fail_closed(tmp_path, monkeypatch):
    paths = _fixture(tmp_path)
    external = tmp_path.parent / "outside-canonical-body.md"
    external.write_text("Not in the repository.", encoding="utf-8")
    link = tmp_path / "projects/demo/current/link.md"
    link.symlink_to(external)
    with pytest.raises(KnowledgeHubError, match="symlinked"):
        _scan(tmp_path, paths + ["projects/demo/current/link.md"])
    monkeypatch.setattr(convergence, "MAX_HASH_BYTES", 5)
    with pytest.raises(KnowledgeHubError, match="byte budget"):
        _scan(tmp_path, paths)


def test_source_inventory_identity_and_digest_fail_closed(tmp_path):
    paths = _fixture(tmp_path)
    source_file = tmp_path / "sources/runtime-input/inventory.jsonl"
    row = json.loads(source_file.read_text())
    row["source_id"] = "mismatched"
    _write_json(source_file, row)
    with pytest.raises(KnowledgeHubError, match="identity mismatch"):
        _scan(tmp_path, paths)
    row["source_id"] = "runtime-input"
    row["sha256"] = "not-a-real-digest"
    _write_json(source_file, row)
    with pytest.raises(KnowledgeHubError, match="invalid source inventory SHA256"):
        _scan(tmp_path, paths)
