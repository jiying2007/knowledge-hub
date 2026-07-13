import json

from tools.codex_assets.knowledge_hub.common import repository_root, route_rows
from tools.codex_assets.knowledge_hub.context import (
    _query_route_selection,
    assemble_context,
)


def _jsonl(rows):
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)


def _context_root(tmp_path):
    (tmp_path / "registry").mkdir()
    (tmp_path / "projects/p1/current").mkdir(parents=True)
    (tmp_path / "projects/p1/archive").mkdir(parents=True)
    (tmp_path / "projects/p1/current/runbook.md").write_text("# P1 发布手册\n")
    (tmp_path / "projects/p1/archive/history.md").write_text("# P1 历史发布\n")
    (tmp_path / "projects/p1/current/audit.md").write_text("# P1 发布审计\n")
    items = [
        {
            "id": "p1-active-audit",
            "title": "P1 发布审计",
            "kind": "audit",
            "domain": "projects/p1",
            "path": "projects/p1/current/audit.md",
            "status": "active",
            "owner": "owner-a",
            "source": {"type": "manual"},
            "summary_zh": "发布审计 provenance",
            "review_after": "2026-10-13",
            "tags": ["p1", "release", "provenance"],
        },
        {
            "id": "p1-runbook",
            "title": "P1 发布手册",
            "kind": "runbook",
            "domain": "projects/p1",
            "path": "projects/p1/current/runbook.md",
            "status": "reviewing",
            "owner": "owner-a",
            "source": {"type": "manual"},
            "summary_zh": "当前发布候选手册",
            "review_after": "2026-10-13",
            "tags": ["p1", "release"],
        },
        {
            "id": "p1-archived-current",
            "title": "P1 旧当前文档",
            "kind": "project-current",
            "domain": "projects/p1",
            "path": "projects/p1/archive/history.md",
            "status": "archived",
            "owner": "owner-a",
            "source": {"type": "manual"},
            "summary_zh": "历史发布证据",
            "review_after": "2026-10-13",
            "tags": ["p1", "release"],
        },
    ]
    (tmp_path / "registry/items.jsonl").write_text(_jsonl(items))
    (tmp_path / "registry/sources.json").write_text('{"sources": []}\n')
    (tmp_path / "registry/retired-sources.jsonl").write_text("")
    (tmp_path / "registry/projects.json").write_text(
        json.dumps(
            {
                "projects": [
                    {
                        "id": "p1",
                        "name": "P1",
                        "domain": "projects/p1",
                        "groups": ["p1"],
                    }
                ]
            }
        )
    )
    (tmp_path / "registry/repositories.json").write_text('{"repositories": []}\n')
    (tmp_path / "registry/project-groups.json").write_text(
        '{"groups": [{"id": "p1", "member_project_ids": ["p1"]}]}\n'
    )
    (tmp_path / "registry/project-routes.json").write_text(
        json.dumps(
            {
                "routes": [
                    {
                        "project_id": "p1",
                        "group_id": "p1",
                        "name": "P1",
                        "aliases": ["P1"],
                        "repo_refs": [],
                        "workspace_refs": [],
                        "hub_entry": "projects/p1/README.md",
                        "current_path": "projects/p1/current",
                        "archive_path": "projects/p1/archive",
                        "decisions_path": "projects/p1/decisions",
                        "validation_path": "projects/p1/validation",
                        "default_source_ids": [],
                    }
                ]
            }
        )
    )
    return tmp_path


def test_context_keeps_archived_project_current_out_of_current(tmp_path):
    root = _context_root(tmp_path)
    payload = assemble_context(root, str(tmp_path), "P1 发布", "release", 8, "normal")
    assert payload["route"]["project_id"] == "p1"
    assert any(row["id"] == "p1-runbook" for row in payload["context"]["current"])
    assert all(row["status"] not in {"archived", "superseded", "rejected"} for row in payload["context"]["current"])
    assert all(row["kind"] != "audit" for row in payload["context"]["current"])
    assert any(row["id"] == "p1-archived-current" for row in payload["context"]["recent"])
    assert any(row["id"] == "p1-active-audit" for row in payload["context"]["related"])
    assert any(row["id"] == "p1-active-audit" for row in payload["context"]["current_exclusions"])


def test_natural_query_route_handles_topic_exact_and_ambiguity():
    routes = route_rows(repository_root())
    st77912 = _query_route_selection("ST77912 display", routes)
    llm_tools = _query_route_selection("llm_tools GUI build", routes)
    adk = _query_route_selection("ADK skill routing", routes)
    assert st77912["status"] == "selected"
    assert st77912["route"]["project_id"] == "pcr02"
    assert llm_tools["status"] == "selected"
    assert llm_tools["route"]["project_id"] == "llm-tools"
    assert adk["status"] == "ambiguous"
    assert {row["project_id"] for row in adk["candidates"]} >= {"codex", "llm-agent"}


def test_control_plane_ambiguous_query_uses_global_context():
    root = repository_root()
    payload = assemble_context(root, str(root), "ADK skill routing", "general")
    assert payload["route_selection"]["status"] == "ambiguous"
    assert payload["route_selection"]["selected_project_id"] is None
    assert len(
        [
            row
            for row in payload["context"]["current"]
            if "project-readiness" in row.get("tags", [])
        ]
    ) <= 1


def test_control_plane_keeps_explicit_self_query_but_not_unknown_query():
    root = repository_root()
    self_query = assemble_context(root, str(root), "增强 Knowledge Hub 自举体验", "general")
    unknown_query = assemble_context(root, str(root), "completely unknown project phrase", "general")
    assert self_query["route"]["project_id"] == "knowledge-hub"
    assert self_query["route_selection"]["status"] == "selected"
    assert unknown_query["route"] is None
    assert unknown_query["route_selection"]["status"] == "unresolved"
