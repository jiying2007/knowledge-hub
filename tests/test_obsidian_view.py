import json
import shutil

import pytest

from tools.codex_assets.knowledge_hub import obsidian_view
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root, registry_items, resolve_inside
from tools.codex_assets.knowledge_hub.obsidian_view import (
    build_obsidian_views,
    obsidian_runtime_acceptance,
)


def test_repository_obsidian_views_are_idempotent(tmp_path):
    root = repository_root()
    payload = build_obsidian_views(root)
    assert payload["status"] == "planned"
    assert payload["content_mirror_drift_count"] == 0
    assert payload["missing_file_count"] == 0
    assert payload["transaction"]["changed_count"] == 0
    for field in ("title", "summary_zh", "tags", "id", "status", "owner", "aliases", "related"):
        assert payload["property_coverage"][field]["coverage_percent"] == 100.0
    assert payload["obsidian_runtime_status"] == "not-validated"
    assert payload["moc_count"] == 4

    # The real repository is read-only even for a no-change apply. Freeze only
    # the declared registry/views/bodies into an owned fixture for writer tests.
    fixture = tmp_path / 'hub'
    for directory in ('registry', 'indexes'):
        shutil.copytree(root / directory, fixture / directory)
    for item in registry_items(root):
        if not item.get('path'):
            continue
        source = resolve_inside(root, item['path'])
        if source.is_file():
            target = fixture / item['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    applied = build_obsidian_views(fixture, apply=True)
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
