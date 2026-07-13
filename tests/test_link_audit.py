import json

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.link_audit import audit_links


def _write_registry(root, status):
    (root / "registry").mkdir()
    row = {
        "id": "note",
        "path": "projects/p/current/note.md",
        "status": status,
        "tags": ["test"],
    }
    (root / "registry/items.jsonl").write_text(json.dumps(row) + "\n")


def test_reviewing_broken_link_is_blocking(tmp_path):
    _write_registry(tmp_path, "reviewing")
    path = tmp_path / "projects/p/current/note.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Note\n\n[missing](missing.md)\n")
    payload = audit_links(tmp_path)
    assert payload["status"] == "fail"
    assert payload["blocking_broken_count"] == 1


def test_archived_broken_link_is_only_a_warning(tmp_path):
    _write_registry(tmp_path, "archived")
    path = tmp_path / "projects/p/current/note.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Note\n\n[missing](missing.md)\n")
    payload = audit_links(tmp_path)
    assert payload["status"] == "pass"
    assert payload["historical_warning_count"] == 1


def test_reviewing_missing_anchor_is_blocking(tmp_path):
    _write_registry(tmp_path, "reviewing")
    path = tmp_path / "projects/p/current/note.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Note\n\n[missing](#not-present)\n")
    payload = audit_links(tmp_path)
    assert payload["status"] == "fail"
    assert payload["broken_anchor_count"] == 1


def test_reviewing_missing_attachment_is_blocking(tmp_path):
    _write_registry(tmp_path, "reviewing")
    path = tmp_path / "projects/p/current/note.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Note\n\n![scope](missing.png)\n")
    payload = audit_links(tmp_path)
    assert payload["status"] == "fail"
    assert payload["blocking_broken_count"] == 1


def test_repository_readiness_links_and_bases_are_valid():
    payload = audit_links(repository_root())
    assert payload["status"] == "pass"
    assert payload["readiness_document_count"] == 124
    assert payload["readiness_without_inbound_count"] == 0
    assert payload["base_failure_count"] == 0
    assert payload["managed_frontmatter_coverage_percent"] == 100.0
    assert payload["managed_property_error_count"] == 0
    assert payload["project_moc_orphan_count"] == 0
    assert payload["missing_moc_count"] == 0
