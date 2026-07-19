import json

import pytest

from tools.codex_assets.knowledge_hub import obsidian_view
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub.obsidian_view import (
    build_obsidian_views,
    obsidian_runtime_acceptance,
)


def test_repository_obsidian_views_are_idempotent():
    payload = build_obsidian_views(repository_root())
    assert payload["status"] == "planned"
    assert payload["content_mirror_drift_count"] == 0
    assert payload["missing_file_count"] == 0
    assert payload["transaction"]["changed_count"] == 0
    for field in ("title", "summary_zh", "tags", "id", "status", "owner", "aliases", "related"):
        assert payload["property_coverage"][field]["coverage_percent"] == 100.0
    assert payload["obsidian_runtime_status"] == "not-validated"

    applied = build_obsidian_views(repository_root(), apply=True)
    assert applied["status"] == "no-change"
    assert applied["transaction"]["changed_count"] == 0


def test_obsidian_runtime_acceptance_requires_real_gui_evidence(tmp_path):
    (tmp_path / "local").mkdir()
    assert obsidian_runtime_acceptance(tmp_path)["status"] == "not-validated"
    (tmp_path / "local/obsidian-runtime-acceptance.json").write_text(
        """{
  "obsidian_version": "1.9.0",
  "validated_at": "2026-07-13",
  "validated_by": "owner",
  "bases_rendered": true,
  "properties_visible": true,
  "backlinks_working": true,
  "moc_navigation_working": true,
  "screenshot_refs": ["artifact://obsidian/gui"]
}
"""
    )
    assert obsidian_runtime_acceptance(tmp_path)["status"] == "pass"


def test_obsidian_builder_fails_closed_when_managed_markdown_exceeds_budget(
    tmp_path, monkeypatch
):
    (tmp_path / "registry").mkdir()
    item = {
        "id": "managed-note",
        "title": "Managed note",
        "kind": "runbook",
        "domain": "projects/p",
        "path": "projects/p/current/note.md",
        "status": "reviewing",
        "visibility": "team-internal",
    }
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(item) + "\n")
    (tmp_path / "registry/projects.json").write_text('{"projects": []}\n')
    path = tmp_path / item["path"]
    path.parent.mkdir(parents=True)
    path.write_text("# Note\n\n" + "x" * 64)
    monkeypatch.setattr(obsidian_view, "OBSIDIAN_MAX_FILE_BYTES", 16)

    with pytest.raises(KnowledgeHubError, match="exceeds 16 bytes"):
        build_obsidian_views(tmp_path)
