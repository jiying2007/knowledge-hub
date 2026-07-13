from tools.codex_assets.knowledge_hub.common import repository_root
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
