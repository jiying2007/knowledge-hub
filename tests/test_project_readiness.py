import datetime as dt
import json
import re
import shutil

import pytest

from tools.codex_assets.knowledge_hub.common import (
    KnowledgeHubError,
    load_json,
    project_rows,
    registry_items,
    repository_root,
    repository_rows,
    route_rows,
)
from tools.codex_assets.knowledge_hub.context import TASK_TYPES, _query_route
from tools.codex_assets.knowledge_hub.project_readiness import (
    RETIRED_PROJECTION_SLOTS,
    SLOT_NAMES,
    _preserve_existing_readiness_item,
    _project_paths,
    generate_project_readiness,
)
from tools.codex_assets.knowledge_hub.project_readiness_validation import (
    PROFILE_VALIDATION_EXPECTATIONS,
    validate_existing_validation_body,
)
from tools.codex_assets.knowledge_hub.project_readiness_cli import main as project_readiness_main


OWNER_ATTESTATION_REF = {
    "kind": "owner-attestation",
    "ref": "artifacts/manifests/knowledge-hub-terminal-owner-attestation-20260716.md",
}


def test_all_registered_projects_have_one_reviewing_evidence_contract():
    root = repository_root()
    projects = project_rows(root)
    items = {row["id"]: row for row in registry_items(root)}
    assert projects
    for project in projects:
        paths = _project_paths(project)
        assert set(paths) == set(SLOT_NAMES)
        for slot, path in paths.items():
            item_id = "{}-readiness-{}-20260713".format(project["id"], slot)
            item = items[item_id]
            assert item["path"] == path
            assert item["status"] == "reviewing"
            assert item["decision_owner"]
            assert item["manual_validation_pending"] is True
            assert item["promotion"] == "none"
            assert item["generated_by_ai"] is True
            assert item["searchable"] is (
                project["id"] == "knowledge-hub" and slot == "validation"
            )
            assert slot == "validation"
            assert item["evidence_contract"]["status"] == "pending"
            if item["decision_owner"] == "unassigned":
                assert item["evidence_contract"]["owner_ref"] is None
            else:
                assert item["evidence_contract"]["owner_ref"] == OWNER_ATTESTATION_REF
            assert (root / path).is_file()


def test_retired_readiness_projections_are_absent_and_fully_ledgered():
    root = repository_root()
    projects = project_rows(root)
    items = registry_items(root)
    ledger_path = (
        root
        / "artifacts/manifests/project-readiness-projection-retirement-20260719.jsonl"
    )
    ledger = [json.loads(line) for line in ledger_path.read_text().splitlines() if line]

    assert not {
        str(item.get("readiness_slot", "")) for item in items
    }.intersection(RETIRED_PROJECTION_SLOTS)
    registered_project_ids = {str(project["id"]) for project in projects}
    retired_project_ids = {row["project_id"] for row in ledger}
    assert retired_project_ids <= registered_project_ids
    assert len(ledger) == len(retired_project_ids) * len(RETIRED_PROJECTION_SLOTS)
    assert len({row["retired_id"] for row in ledger}) == len(ledger)
    assert len({row["retired_path"] for row in ledger}) == len(ledger)
    for project_id in retired_project_ids:
        assert {
            row["retired_slot"] for row in ledger if row["project_id"] == project_id
        } == RETIRED_PROJECTION_SLOTS
    assert all(row["status"] == "retired-generated-projection" for row in ledger)
    assert all(not (root / row["retired_path"]).exists() for row in ledger)


def test_project_query_route_matrix_is_complete_for_all_task_types():
    root = repository_root()
    projects = project_rows(root)
    routes = route_rows(root)
    assert len(routes) == len(projects)
    checked = 0
    for project in projects:
        for task_type in sorted(TASK_TYPES):
            route, score, _ = _query_route("{} {}".format(project["id"], task_type), routes)
            assert route is not None
            assert route["project_id"] == project["id"]
            assert score > 0
            checked += 1
    assert checked == len(projects) * len(TASK_TYPES)


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
    assert preserved["searchable"] is False
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


def test_generator_accepts_an_additional_registry_project_without_core_code_changes(tmp_path):
    source_root = repository_root()
    fixture_root = tmp_path / "hub"
    shutil.copytree(
        source_root,
        fixture_root,
        ignore=shutil.ignore_patterns(".git", ".cache", ".tmp", "__pycache__"),
    )
    projects_path = fixture_root / "registry/projects.json"
    projects_payload = json.loads(projects_path.read_text())
    baseline_project_count = len(projects_payload["projects"])
    projects_payload["projects"].append(
        {
            "id": "scalable-project-31",
            "name": "Scalable Project 31",
            "type": "git-repository",
            "domain": "projects/scalable-project-31",
            "entry": "projects/scalable-project-31/README.md",
            "current": "projects/scalable-project-31/current",
            "archive": "projects/scalable-project-31/archive",
            "decisions": "projects/scalable-project-31/decisions",
            "validation": "projects/scalable-project-31/validation",
            "groups": [],
            "repo_boundary": "tooling",
            "status": "registered",
            "evidence_profile": "software-tool",
        }
    )
    projects_path.write_text(json.dumps(projects_payload, ensure_ascii=False, indent=2) + "\n")
    repositories_path = fixture_root / "registry/repositories.json"
    repositories_payload = json.loads(repositories_path.read_text())
    repositories_payload["repositories"].append(
        {
            "repo_id": "scalable-project-31",
            "project_id": "scalable-project-31",
            "remote_key": "example/scalable-project-31",
            "remote_kind": "github",
            "workspace_ref": "workspace://scalable-project-31",
            "groups": [],
            "aliases": ["scalable-project-31"],
            "lifecycle": "first-party",
            "status": "registered",
        }
    )
    repositories_path.write_text(
        json.dumps(repositories_payload, ensure_ascii=False, indent=2) + "\n"
    )
    entry = fixture_root / "projects/scalable-project-31/README.md"
    entry.parent.mkdir(parents=True)
    entry.write_text("# Scalable Project 31\n")

    payload = generate_project_readiness(
        fixture_root, dt.date(2026, 7, 18), apply=True
    )

    assert payload["status"] == "applied"
    expected_project_count = baseline_project_count + 1
    assert payload["project_count"] == expected_project_count
    assert payload["route_count"] == expected_project_count
    assert payload["new_item_count"] == 1
    assert payload["slot_count"] == expected_project_count
    assert payload["evidence_contract_count"] == expected_project_count
    validation = fixture_root / "projects/scalable-project-31/validation/project-readiness.md"
    assert validation.is_file()
    assert (
        "- [x] 项目 route matrix 能将 `scalable-project-31` 稳定解析为本项目。"
        in validation.read_text()
    )


def test_x5_multi_repository_project_uses_embedded_target_evidence():
    root = repository_root()
    project = next(row for row in project_rows(root) if row["id"] == "x5-rdk")
    item = next(
        row
        for row in registry_items(root)
        if row["id"] == "x5-rdk-readiness-validation-20260713"
    )
    repos = [row for row in repository_rows(root) if row.get("project_id") == "x5-rdk"]

    assert project["type"] == "product-group"
    assert project["repo_boundary"] == "group"
    assert project["evidence_profile"] == "embedded-target"
    assert {row["repo_id"] for row in repos} == {
        "x5-integration",
        "x5-manifest",
        "x5-vendor-docs",
    }
    assert item["evidence_profile"] == "embedded-target"
    assert item["evidence_contract"]["profile"] == "embedded-target"
    assert item["evidence_contract"]["status"] == "pending"
    assert item["evidence_contract"]["member_project_ids"] == []


def test_aggregate_group_requires_a_non_self_member_project(tmp_path):
    source_root = repository_root()
    fixture_root = tmp_path / "hub"
    shutil.copytree(
        source_root,
        fixture_root,
        ignore=shutil.ignore_patterns(".git", ".cache", ".tmp", "__pycache__"),
    )
    projects_path = fixture_root / "registry/projects.json"
    projects_payload = json.loads(projects_path.read_text(encoding="utf-8"))
    project = next(
        row for row in projects_payload["projects"] if row["id"] == "x5-rdk"
    )
    project["evidence_profile"] = "aggregate-group"
    projects_path.write_text(
        json.dumps(projects_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        KnowledgeHubError,
        match="aggregate-group project must declare at least one non-self member project",
    ):
        generate_project_readiness(
            fixture_root,
            dt.date(2026, 7, 13),
            apply=False,
        )


def test_readiness_documents_are_count_neutral_and_profile_aligned():
    root = repository_root()
    numeric_route = re.compile(r"^- \[x\] \d+ 项目 route matrix", re.M)
    for project in project_rows(root):
        path = root / _project_paths(project)["validation"]
        text = path.read_text(encoding="utf-8")
        assert not numeric_route.search(text), project["id"]
        validate_existing_validation_body(project, text)


def test_validation_expectations_follow_evidence_profile_not_repo_topology():
    root = repository_root()
    projects = {row["id"]: row for row in project_rows(root)}
    for project_id in ("llm-agent", "agent-dev-kit", "digital-worker"):
        project = projects[project_id]
        assert project["evidence_profile"] == "software-tool"
        text = (root / _project_paths(project)["validation"]).read_text(encoding="utf-8")
        for expected in PROFILE_VALIDATION_EXPECTATIONS["software-tool"]:
            assert expected.split("：", 1)[0] + "：" in text
    x5 = projects["x5-rdk"]
    assert x5["repo_boundary"] == "group"
    assert x5["evidence_profile"] == "embedded-target"
    x5_text = (root / _project_paths(x5)["validation"]).read_text(encoding="utf-8")
    for expected in PROFILE_VALIDATION_EXPECTATIONS["embedded-target"]:
        assert expected.split("：", 1)[0] + "：" in x5_text


def test_existing_manual_readiness_evidence_is_preserved():
    root = repository_root()
    project = next(row for row in project_rows(root) if row["id"] == "llm-agent")
    text = (root / _project_paths(project)["validation"]).read_text(encoding="utf-8")
    assert "check-all.sh --full` 均为 62/62" in text
    assert "313 篇 corpus" in text
    assert "- [x] 工程验证：" in text
    validate_existing_validation_body(project, text)


def test_existing_readiness_body_profile_drift_fails_closed():
    root = repository_root()
    project = dict(next(row for row in project_rows(root) if row["id"] == "x5-rdk"))
    text = (root / _project_paths(project)["validation"]).read_text(encoding="utf-8")
    project["evidence_profile"] = "software-tool"
    with pytest.raises(
        KnowledgeHubError,
        match="existing readiness evidence-profile statement drift: x5-rdk",
    ):
        validate_existing_validation_body(project, text)

