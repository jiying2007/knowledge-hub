import datetime as dt

from tools.codex_assets.knowledge_hub.common import load_json, project_rows, registry_items, repository_root, route_rows
from tools.codex_assets.knowledge_hub.context import TASK_TYPES, _query_route
from tools.codex_assets.knowledge_hub.project_readiness import (
    SLOT_NAMES,
    _preserve_existing_readiness_item,
    _project_paths,
    generate_project_readiness,
)
from tools.codex_assets.knowledge_hub.project_readiness_cli import main as project_readiness_main


OWNER_ATTESTATION_REF = {
    "kind": "owner-attestation",
    "ref": "artifacts/manifests/knowledge-hub-terminal-owner-attestation-20260716.md",
}


def test_all_registered_projects_have_four_reviewing_readiness_assets():
    root = repository_root()
    projects = project_rows(root)
    items = {row["id"]: row for row in registry_items(root)}
    assert len(projects) == 30
    for project in projects:
        paths = _project_paths(project)
        assert set(paths) == set(SLOT_NAMES)
        for slot, path in paths.items():
            item_id = "{}-readiness-{}-20260713".format(project["id"], slot)
            item = items[item_id]
            assert item["path"] == path
            assert item["status"] == "reviewing"
            assert item["decision_owner"] == "leiwenjun"
            assert item["manual_validation_pending"] is True
            assert item["promotion"] == "none"
            assert item["generated_by_ai"] is True
            if slot == "validation":
                assert item["evidence_contract"]["status"] == "pending"
                assert item["evidence_contract"]["owner_ref"] == OWNER_ATTESTATION_REF
            assert (root / path).is_file()


def test_project_query_route_matrix_is_complete_for_all_task_types():
    root = repository_root()
    projects = project_rows(root)
    routes = route_rows(root)
    assert len(routes) == len(projects) == 30
    checked = 0
    for project in projects:
        for task_type in sorted(TASK_TYPES):
            route, score, _ = _query_route("{} {}".format(project["id"], task_type), routes)
            assert route is not None
            assert route["project_id"] == project["id"]
            assert score > 0
            checked += 1
    assert checked == 30 * len(TASK_TYPES)


def test_project_routes_reference_only_current_registered_sources():
    root = repository_root()
    routes = route_rows(root)
    current_source_ids = {
        row["id"]
        for row in load_json(root / "registry/sources.json", {})["sources"]
        if row["status"] == "registered"
    }

    assert all("retired_route_ids" not in route for route in routes)
    assert all(set(route.get("default_source_ids", [])) <= current_source_ids for route in routes)


def test_project_readiness_generator_is_idempotent():
    root = repository_root()
    payload = generate_project_readiness(root, dt.date(2026, 7, 13), apply=False)
    assert payload["new_item_count"] == 0
    assert payload["new_document_count"] == 0
    assert payload["transaction"]["changed_count"] == 0


def test_project_readiness_check_returns_success_when_already_current(capsys):
    assert project_readiness_main(["--check", "--as-of", "2026-07-13", "--json"]) == 0
    assert '"status": "pass"' in capsys.readouterr().out


def test_project_readiness_never_rewrites_frozen_body_coverage():
    payload = generate_project_readiness(repository_root(), dt.date(2026, 7, 13), apply=False)
    assert "registry/body-coverage.json" not in payload["transaction"]["write_paths"]


def test_project_readiness_generator_does_not_rotate_ids_by_date():
    root = repository_root()
    payload = generate_project_readiness(root, dt.date(2027, 1, 2), apply=False)
    assert payload["new_item_count"] == 0
    assert payload["rendered_document_count"] == 0
    assert payload["transaction"]["changed_count"] == 0


def test_existing_owner_lifecycle_and_evidence_are_preserved():
    project = {"id": "demo"}
    existing = {
        "id": "demo-validation",
        "path": "projects/demo/validation/project-readiness.md",
        "status": "active",
        "decision_owner": "owner-123",
        "manual_validation_pending": False,
        "evidence_profile": "software-tool",
        "evidence_contract": {
            "schema_version": 1,
            "profile": "software-tool",
            "status": "ready",
            "owner_ref": {"kind": "owner-decision", "ref": "decision://123"},
            "source_refs": [{"kind": "git-commit", "ref": "0123456789abcdef"}],
            "validation_refs": [{"kind": "test-report", "ref": "artifact://test"}],
            "artifact_refs": [{"kind": "sha256", "ref": "abc"}],
            "device_refs": [],
            "release_ref": {"kind": "release", "ref": "release://1"},
            "rollback_ref": {"kind": "rollback", "ref": "artifact://rollback"},
            "not_applicable": {},
            "member_project_ids": [],
        },
    }
    preserved = _preserve_existing_readiness_item(
        existing,
        project,
        "validation",
        existing["path"],
        "software-tool",
    )
    assert preserved["status"] == "active"
    assert preserved["decision_owner"] == "owner-123"
    assert preserved["manual_validation_pending"] is False
    assert preserved["evidence_contract"] == existing["evidence_contract"]


def test_readiness_documents_do_not_persist_machine_local_workspace_state():
    root = repository_root()
    forbidden = (
        "/home/leiwenjun",
        "/vsdata/leiwenjun",
        "all-mapped-and-present",
        "partial-mapped",
        "none-mapped",
    )
    generated_paths = [root / "indexes/project-readiness.md"]
    for project in project_rows(root):
        generated_paths.extend(root / path for path in _project_paths(project).values())

    for path in generated_paths:
        text = path.read_text(encoding="utf-8")
        assert not any(value in text for value in forbidden), path
