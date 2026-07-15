import errno
import json

from tools.codex_assets.knowledge_hub import context as context_module
from tools.codex_assets.knowledge_hub import metrics
from tools.codex_assets.knowledge_hub.common import repository_root, route_rows
from tools.codex_assets.knowledge_hub.context import (
    _git_head_from_config,
    _query_route_selection,
    assemble_context,
    record_context_telemetry,
)
from tools.codex_assets.knowledge_hub.context_cli import main as context_main


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
    assert st77912["route"]["project_id"] == "pcr02-ssc305"
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


def test_context_route_exposes_only_current_default_sources():
    root = repository_root()
    payload = assemble_context(root, str(root), "增强 Knowledge Hub 自举体验", "general")

    assert "retired_route_ids" not in payload["route"]
    assert set(payload["route"]["default_source_ids"]) == {"knowledge-hub-automation-runs"}


def test_small_budget_caps_search_limit(monkeypatch, tmp_path):
    root = _context_root(tmp_path)
    observed_limits = []

    def fake_search(root, query, limit, filters):
        observed_limits.append(limit)
        return {
            "status": "pass",
            "results": [{"path": "projects/p1/current/runbook.md"}],
            "count": 1,
            "total_matches": 1,
            "zero_hit": {"is_zero_hit": False, "reason": "", "degraded_terms": []},
        }

    monkeypatch.setattr(context_module, "search", fake_search)
    payload = assemble_context(root, str(root), "P1 发布", "release", 8, "small")

    assert payload["context"]["effective_limit"] == 4
    assert observed_limits == [4]


def test_summary_json_is_compact_deduplicated_and_traceable(tmp_path, capsys):
    root = _context_root(tmp_path)
    exit_code = context_main(
        [
            "--root",
            str(root),
            "--cwd",
            str(root),
            "--query",
            "P1 发布",
            "--task-type",
            "release",
            "--context-budget",
            "small",
            "--limit",
            "3",
            "--summary-json",
            "--no-telemetry",
        ]
    )
    output = capsys.readouterr().out.strip()
    parsed = json.loads(output)

    assert exit_code == 0
    assert "\n" not in output
    assert len(output.encode("utf-8")) <= 4096
    assert parsed["projection"] == "agent-summary-v1"
    assert "ranked_items" not in parsed
    assert "search" not in parsed
    assert parsed["search_summary"]["count"] <= 3
    assert parsed["context_contract"]["read_tier"] == "L1"
    assert parsed["context_contract"]["raw_evidence"]
    item_ids = [
        row["id"]
        for section in ("current", "recent", "related", "search_fallback")
        for row in parsed["context"][section]
        if row.get("id")
    ]
    assert len(item_ids) == len(set(item_ids))


def test_summary_json_enforces_byte_budget_with_dynamic_risks():
    rows = [
        {
            "id": "item-{}".format(index),
            "title": "很长的动态候选标题" * 60,
            "kind": "project-archive",
            "status": "reviewing",
            "path": "projects/p1/archive/item-{}.md".format(index),
            "why_selected": ["query-term:p1", "task-kind:archive", "status:reviewing"],
        }
        for index in range(8)
    ]
    payload = {
        "schema_version": 2,
        "read_only": True,
        "task_type": "archive",
        "context_budget": "small",
        "knowledge_preflight": {"required": True, "source_of_truth": "registry"},
        "route_selection": {"status": "selected", "selected_project_id": "p1"},
        "route": {"project_id": "p1", "name": "P1"},
        "context": {
            "budget": "small",
            "effective_limit": 4,
            "selection_order": ["current", "recent", "related", "risk"],
            "current": rows[:4],
            "recent": rows[4:],
            "related": [],
            "search_fallback": [],
            "risks": ["动态风险说明" * 80 for _ in range(5)],
        },
        "search": {
            "status": "pass",
            "count": 4,
            "total_matches": 8,
            "index": {"state": "warm", "mode": "local-index"},
            "zero_hit": {"is_zero_hit": False},
        },
        "telemetry": {"status": "disabled", "recorded": False},
    }

    summary = context_module.summarize_context(payload)
    encoded = json.dumps(summary, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    item_count = sum(
        len(summary["context"][section])
        for section in ("current", "recent", "related", "search_fallback")
    )

    assert len(encoded) <= context_module.SUMMARY_JSON_MAX_BYTES
    assert item_count <= context_module.SUMMARY_JSON_MAX_ITEMS
    assert summary["context_contract"]["raw_evidence"]


def test_context_telemetry_storage_failure_is_non_blocking(monkeypatch, tmp_path):
    def deny_write(path, row):
        raise PermissionError(errno.EACCES, "permission denied")

    monkeypatch.setenv("KNOWLEDGE_TELEMETRY", "1")
    monkeypatch.setattr(metrics, "_append_locked", deny_write)
    result = record_context_telemetry(
        tmp_path,
        {
            "query": "private preflight query",
            "task_type": "general",
            "route": None,
            "context": {"current": [], "recent": []},
            "latency_ms": 12,
        },
    )

    assert result["status"] == "degraded"
    assert result["reason"] == "read-only-or-permission-denied"
    assert result["error_code"] == "EACCES"
    assert "private preflight query" not in json.dumps(result)


def test_context_telemetry_binds_current_interaction_and_result_ids(monkeypatch, tmp_path):
    captured = {}

    def capture(path, row):
        captured.update(row)

    monkeypatch.setenv("KNOWLEDGE_TELEMETRY", "1")
    monkeypatch.setattr(metrics, "_append_locked", capture)
    result = record_context_telemetry(
        tmp_path,
        {
            "query": "private preflight query",
            "task_type": "validation",
            "route": {"project_id": "knowledge-hub"},
            "context": {
                "current": [{"id": "item-a"}],
                "recent": [],
                "related": [{"item_id": "item-b"}],
                "search_fallback": [],
            },
            "search": {"index": {"state": "warm", "rebuilt": False}},
            "latency_ms": 12,
        },
    )

    assert result["status"] == "recorded"
    assert captured["schema_version"] == metrics.INTERACTIVE_TELEMETRY_SCHEMA_VERSION
    assert captured["interaction_contract"] == metrics.INTERACTION_CONTRACT
    assert captured["result_ids"] == ["item-a", "item-b"]
    assert "private preflight query" not in json.dumps(captured)


def test_git_head_evidence_reads_current_ref(tmp_path):
    git_dir = tmp_path / ".git"
    (git_dir / "refs/heads").mkdir(parents=True)
    (git_dir / "config").write_text("[core]\n\trepositoryformatversion = 0\n")
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
    (git_dir / "refs/heads/main").write_text("b" * 40 + "\n")

    assert _git_head_from_config(git_dir / "config") == "b" * 40
