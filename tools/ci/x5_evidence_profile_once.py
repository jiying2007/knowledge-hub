import json
from pathlib import Path


PROJECT_ID = "x5-rdk"
ITEM_ID = "x5-rdk-readiness-validation-20260713"


def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit("unexpected {}".format(label))
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


projects_path = Path("registry/projects.json")
projects_doc = json.loads(projects_path.read_text(encoding="utf-8"))
project = next(row for row in projects_doc["projects"] if row.get("id") == PROJECT_ID)
expected_project = {
    "type": "product-group",
    "repo_boundary": "group",
    "evidence_profile": "aggregate-group",
    "groups": ["x5-rdk"],
    "status": "registered",
}
for key, expected in expected_project.items():
    if project.get(key) != expected:
        raise SystemExit("unexpected X5 project {}: {!r}".format(key, project.get(key)))
project["evidence_profile"] = "embedded-target"
projects_path.write_text(
    json.dumps(projects_doc, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
    encoding="utf-8",
)

items_path = Path("registry/items.jsonl")
items = [
    json.loads(line)
    for line in items_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]
matches = [row for row in items if row.get("id") == ITEM_ID]
if len(matches) != 1:
    raise SystemExit("expected exactly one X5 readiness item")
item = matches[0]
if item.get("evidence_profile") != "aggregate-group":
    raise SystemExit("unexpected X5 item evidence profile")
if item.get("decision_owner") != "unassigned" or item.get("status") != "reviewing":
    raise SystemExit("X5 item owner/lifecycle unexpectedly changed")
contract = item.get("evidence_contract", {})
expected_contract = {
    "schema_version": 1,
    "profile": "aggregate-group",
    "status": "pending",
    "owner_ref": None,
    "source_refs": [],
    "validation_refs": [],
    "artifact_refs": [],
    "device_refs": [],
    "release_ref": None,
    "rollback_ref": None,
    "not_applicable": {},
    "member_project_ids": [],
}
if contract != expected_contract:
    raise SystemExit("X5 evidence contract contains facts that require manual migration")
item["evidence_profile"] = "embedded-target"
contract["profile"] = "embedded-target"
items_path.write_text(
    "\n".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
        for row in items
    )
    + "\n",
    encoding="utf-8",
)

readiness_path = Path("tools/codex_assets/knowledge_hub/project_readiness.py")
old = '''        member_project_ids = (
            [
                str(value)
                for value in group.get("member_project_ids", [])
                if str(value) != project_id
            ]
            if evidence_profile == "aggregate-group"
            else []
        )
        paths = _project_paths(project)'''
new = '''        member_project_ids = (
            [
                str(value)
                for value in group.get("member_project_ids", [])
                if str(value) != project_id
            ]
            if evidence_profile == "aggregate-group"
            else []
        )
        if evidence_profile == "aggregate-group" and not member_project_ids:
            raise KnowledgeHubError(
                "aggregate-group project must declare at least one non-self member project: {}".format(
                    project_id
                )
            )
        paths = _project_paths(project)'''
replace_once(readiness_path, old, new, "aggregate member generation block")

tests_path = Path("tests/test_project_readiness.py")
text = tests_path.read_text(encoding="utf-8")
old_import = '''from tools.codex_assets.knowledge_hub.common import (
    load_json,
    project_rows,
    registry_items,
    repository_root,
    route_rows,
)'''
new_import = '''from tools.codex_assets.knowledge_hub.common import (
    KnowledgeHubError,
    load_json,
    project_rows,
    registry_items,
    repository_root,
    repository_rows,
    route_rows,
)'''
if text.count(old_import) != 1:
    raise SystemExit("unexpected project readiness common import")
text = text.replace(old_import, new_import, 1)
addition = r'''


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
'''
if "test_x5_multi_repository_project_uses_embedded_target_evidence" in text:
    raise SystemExit("X5 profile regression tests already present")
tests_path.write_text(text.rstrip() + addition + "\n", encoding="utf-8")
