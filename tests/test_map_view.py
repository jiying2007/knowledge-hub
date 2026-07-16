import json

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, compact_json
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.map_cli import main as map_main
from tools.codex_assets.knowledge_hub.map_view import build_knowledge_map
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def _root(tmp_path):
    (tmp_path / "registry").mkdir()
    rows = [
        {
            "id": "active-rule",
            "title": "Active rule",
            "kind": "standard",
            "domain": "governance",
            "path": "governance/active.md",
            "status": "active",
            "owner": "owner-a",
            "updated_at": "2026-07-16",
            "summary_zh": "active summary",
        },
        {
            "id": "reviewing-decision",
            "title": "Reviewing decision",
            "kind": "decision",
            "domain": "governance",
            "path": "governance/reviewing.md",
            "status": "reviewing",
            "owner": "owner-a",
            "updated_at": "2026-07-16",
            "summary_zh": "reviewing summary",
        },
        {
            "id": "old-note",
            "title": "Old note",
            "kind": "project-archive",
            "domain": "projects/p1",
            "path": "projects/p1/archive/old.md",
            "status": "archived",
            "owner": "owner-b",
            "updated_at": "2026-07-16",
            "summary_zh": "archived summary",
        },
    ]
    (tmp_path / "registry/items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    return tmp_path


def test_map_is_bounded_navigation_and_separates_authority_lanes(tmp_path):
    root = _root(tmp_path)
    payload = build_knowledge_map(root, limit=10, max_bytes=8192)

    assert payload["schema_version"] == "knowledge-hub.map.v1"
    assert payload["navigation_only"] is True
    assert [row["id"] for row in payload["items"]] == [
        "active-rule",
        "reviewing-decision",
    ]
    assert [row["authority_lane"] for row in payload["items"]] == [
        "active",
        "provisional",
    ]
    assert payload["summary"]["terminal_items"] == 1
    assert len(compact_json(payload).encode("utf-8")) <= 8192
    assert payload["encoded_bytes"] == len(compact_json(payload).encode("utf-8"))
    assert validate_instance(repository_root(), "knowledge-map-v1", payload)["status"] == "pass"

    all_statuses = build_knowledge_map(root, limit=10, max_bytes=8192, all_statuses=True)
    assert [row["authority_lane"] for row in all_statuses["items"]] == [
        "active",
        "provisional",
        "terminal",
    ]


def test_map_cursor_binds_source_and_filters(tmp_path):
    root = _root(tmp_path)
    first = build_knowledge_map(root, limit=1, max_bytes=8192)
    assert first["truncated"] is True
    second = build_knowledge_map(
        root, limit=1, max_bytes=8192, cursor=first["next_cursor"]
    )
    assert [row["id"] for row in second["items"]] == ["reviewing-decision"]

    with pytest.raises(KnowledgeHubError, match="cursor_mismatch"):
        build_knowledge_map(
            root,
            limit=1,
            max_bytes=8192,
            cursor=first["next_cursor"],
            statuses=("active",),
        )

    path = root / "registry/items.jsonl"
    path.write_text(path.read_text() + json.dumps({
        "id": "new-item",
        "title": "New item",
        "kind": "runbook",
        "domain": "governance",
        "path": "governance/new.md",
        "status": "active",
        "owner": "owner-a",
        "updated_at": "2026-07-16",
    }) + "\n")
    with pytest.raises(KnowledgeHubError, match="cursor_stale"):
        build_knowledge_map(
            root, limit=1, max_bytes=8192, cursor=first["next_cursor"]
        )


def test_map_cursor_detects_projection_change_without_updated_at_change(tmp_path):
    root = _root(tmp_path)
    first = build_knowledge_map(root, limit=1, max_bytes=8192)
    path = root / "registry/items.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    rows[0]["owner"] = "owner-changed-without-date"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    with pytest.raises(KnowledgeHubError, match="cursor_stale"):
        build_knowledge_map(
            root, limit=1, max_bytes=8192, cursor=first["next_cursor"]
        )


def test_repository_map_fits_default_budget_with_cursor():
    payload = build_knowledge_map(repository_root())
    assert payload["encoded_bytes"] <= 8192
    assert payload["encoded_bytes"] == len(compact_json(payload).encode("utf-8"))


def test_map_cli_summary_json_is_compact(tmp_path, capsys):
    root = _root(tmp_path)
    exit_code = map_main(["--root", str(root), "--summary-json"])
    output = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert "\n" not in output
    assert json.loads(output)["schema_version"] == "knowledge-hub.map.v1"


def test_map_rejects_ambiguous_all_statuses_filter(tmp_path):
    with pytest.raises(KnowledgeHubError, match="cannot be combined"):
        build_knowledge_map(
            _root(tmp_path), all_statuses=True, statuses=("active",)
        )


def test_map_domain_filter_uses_boundary_and_personal_metadata_is_opt_in(tmp_path):
    root = _root(tmp_path)
    path = root / "registry/items.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    rows.extend(
        [
            {
                "id": "p10-item",
                "title": "P10 item",
                "kind": "project-current",
                "domain": "projects/p10",
                "path": "projects/p10/current/item.md",
                "status": "reviewing",
                "owner": "owner-c",
                "updated_at": "2026-07-16",
            },
            {
                "id": "personal-item",
                "title": "Private item",
                "kind": "personal-note",
                "domain": "notes",
                "path": "notes/personal/private.md",
                "status": "personal",
                "visibility": "personal-local",
                "owner": "private-owner",
                "updated_at": "2026-07-16",
            },
        ]
    )
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    filtered = build_knowledge_map(root, domains=("projects/p1",), all_statuses=True)
    assert [row["id"] for row in filtered["items"]] == ["old-note"]
    default_all = build_knowledge_map(root, all_statuses=True)
    serialized = json.dumps(default_all)
    assert "personal-item" not in serialized
    assert "private-owner" not in serialized
    personal = build_knowledge_map(root, statuses=("personal",))
    assert [row["id"] for row in personal["items"]] == ["personal-item"]


def test_map_rejects_oversized_cursor_and_filter_inputs(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(KnowledgeHubError, match="cursor exceeds"):
        build_knowledge_map(root, cursor="x" * 4097)
    with pytest.raises(KnowledgeHubError, match="filter values"):
        build_knowledge_map(root, owners=tuple("owner-{}".format(i) for i in range(33)))
    with pytest.raises(KnowledgeHubError, match="filter value exceeds"):
        build_knowledge_map(root, domains=("d" * 257,))
