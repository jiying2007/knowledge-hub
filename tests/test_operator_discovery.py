from __future__ import annotations

import json
import pathlib

from tools.codex_assets.knowledge_hub import (
    operator_discovery,
    operator_state,
    operator_ui,
)


def _write_json(path: pathlib.Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _fixture_root(root: pathlib.Path) -> pathlib.Path:
    registry = root / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    _write_json(
        registry / "project-routes.json",
        {
            "schema_version": 2,
            "routes": [
                {
                    "project_id": "tool",
                    "repo_refs": ["tool-repo"],
                    "default_source_ids": ["tool-source"],
                    "validation_path": "projects/tool/validation",
                }
            ],
        },
    )
    _write_json(
        registry / "repositories.json",
        {
            "schema_version": 1,
            "repositories": [
                {
                    "repo_id": "tool-repo",
                    "project_id": "tool",
                    "remote_key": "example/tool",
                    "remote_kind": "github",
                    "workspace_ref": "workspace://tool",
                    "lifecycle": "first-party",
                    "status": "registered",
                }
            ],
        },
    )
    _write_json(
        registry / "sources.json",
        {
            "schema_version": 1,
            "sources": [
                {
                    "id": "tool-source",
                    "path": "projects/tool/current",
                    "status": "active",
                    "owner": "tool-owner",
                }
            ],
        },
    )
    (registry / "items.jsonl").write_text(
        json.dumps(
            {
                "id": "tool-validation-hosted",
                "path": "projects/tool/validation/hosted.md",
                "kind": "validation",
                "status": "active",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return root


def _action_queue() -> dict:
    rows = []
    for field in (
        "source_refs",
        "validation_refs",
        "artifact_refs",
        "release_ref",
    ):
        rows.append(
            {
                "id": "tool:missing:{}".format(field),
                "project_id": "tool",
                "field": field,
                "execution_class": "machine-discovery",
                "escalation_class": (
                    "human-authorization" if field == "release_ref" else ""
                ),
            }
        )
    rows.append(
        {
            "id": "tool:missing:owner_ref",
            "project_id": "tool",
            "field": "owner_ref",
            "execution_class": "human-authorization",
        }
    )
    return {"actions": rows}


def _by_field(projection: dict) -> dict:
    return {row["field"]: row for row in projection["rows"]}


def test_discovery_executes_local_registry_lookup_without_binding(
    tmp_path: pathlib.Path,
) -> None:
    root = _fixture_root(tmp_path)
    before = sorted(
        str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()
    )
    result = operator_discovery.build_discovery_projection(root, _action_queue())
    after = sorted(
        str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()
    )

    assert result["read_only"] is True
    assert result["network_performed"] is False
    assert result["canonical_write_performed"] is False
    assert result["automatic_binding_enabled"] is False
    assert result["action_count"] == 4
    assert result["candidate_found_count"] == 2
    assert result["provider_required_count"] == 2
    assert before == after

    rows = _by_field(result)
    source_refs = {row["ref"] for row in rows["source_refs"]["candidates"]}
    assert "repo://tool-repo" in source_refs
    assert "source://tool-source" in source_refs
    validation_refs = {
        row["ref"] for row in rows["validation_refs"]["candidates"]
    }
    assert "item://tool-validation-hosted" in validation_refs
    assert all(
        candidate["eligible_for_binding"] is False
        for row in result["rows"]
        for candidate in row["candidates"]
    )


def test_remote_release_and_artifact_discovery_stays_provider_owned(
    tmp_path: pathlib.Path,
) -> None:
    result = operator_discovery.build_discovery_projection(
        _fixture_root(tmp_path), _action_queue()
    )
    rows = _by_field(result)

    release = rows["release_ref"]
    assert release["status"] == "provider-required"
    assert release["escalation_class"] == "human-authorization"
    assert release["candidate_count"] == 0
    assert release["provider_queries"] == [
        {
            "provider": "github",
            "operation": "list-releases-and-tags",
            "target": "example/tool",
            "executed": False,
            "read_only": True,
            "transport_owned_by_provider": True,
        }
    ]

    artifact = rows["artifact_refs"]
    assert artifact["status"] == "provider-required"
    assert artifact["provider_queries"][0]["operation"] == (
        "list-release-assets-and-actions-artifacts"
    )
    assert result["provider_query_count"] == 4


def test_human_actions_are_not_executed_by_discovery(tmp_path: pathlib.Path) -> None:
    result = operator_discovery.build_discovery_projection(
        _fixture_root(tmp_path), _action_queue()
    )
    assert "owner_ref" not in _by_field(result)
    assert all(
        row["action_id"] != "tool:missing:owner_ref" for row in result["rows"]
    )


def test_unknown_project_is_not_guessed_and_preserves_escalation(
    tmp_path: pathlib.Path,
) -> None:
    root = _fixture_root(tmp_path)
    result = operator_discovery.build_discovery_projection(
        root,
        {
            "actions": [
                {
                    "id": "unknown:missing:release_ref",
                    "project_id": "unknown",
                    "field": "release_ref",
                    "execution_class": "machine-discovery",
                    "escalation_class": "human-authorization",
                }
            ]
        },
    )
    row = result["rows"][0]
    assert row["status"] == "no-candidate"
    assert row["candidates"] == []
    assert row["provider_queries"] == []
    assert row["escalation_class"] == "human-authorization"


def test_operator_state_includes_read_only_discovery_projection(
    monkeypatch, tmp_path: pathlib.Path
) -> None:
    root = _fixture_root(tmp_path)
    monkeypatch.setattr(
        operator_state,
        "_project_readiness",
        lambda value: {
            "project_count": 1,
            "structural_ready_count": 1,
            "source_mapping_ready_count": 0,
            "owner_boundary_ready_count": 1,
            "evidence_field_complete_count": 0,
            "evidence_ready_count": 0,
            "rows": [
                {
                    "project_id": "tool",
                    "name": "Tool",
                    "evidence_profile": "software-tool",
                    "evidence_status": "contract-evidence-pending",
                    "evidence_field_status": "incomplete",
                    "owner_boundary_status": "ready",
                    "source_mapping_ready": False,
                    "evidence_contract": {
                        "missing_fields": ["source_refs", "release_ref"],
                        "invalid_fields": [],
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        operator_state,
        "_status_summary",
        lambda value: {"status": "needs-review", "next_actions_zh": []},
    )
    monkeypatch.setattr(
        operator_state,
        "_external_state",
        lambda value: {"status": "pass", "open_count": 0, "open_gaps": []},
    )
    monkeypatch.setattr(
        operator_state,
        "_terminal_state",
        lambda value: {"status": "not-evaluated", "terminal": False},
    )

    state = operator_state.build_operator_state(root)
    assert state["discovery"]["read_only"] is True
    assert state["discovery"]["network_performed"] is False
    assert state["discovery"]["automatic_binding_enabled"] is False
    assert state["discovery"]["action_count"] == 2


def test_dashboard_escapes_discovery_provider_query() -> None:
    state = {
        "status": "needs-review",
        "readiness": {"project_count": 0, "projects": []},
        "action_queue": {"actions": []},
        "external_closure": {"open_count": 0, "open_gaps": []},
        "terminal_closure": {"terminal": False, "status": "needs-review"},
        "discovery": {
            "candidate_found_count": 0,
            "provider_required_count": 1,
            "rows": [
                {
                    "project_id": "tool",
                    "field": "release_ref",
                    "status": "provider-required",
                    "candidates": [],
                    "provider_queries": [
                        {
                            "provider": "github",
                            "operation": "list-releases-and-tags",
                            "target": "<unsafe>",
                        }
                    ],
                }
            ],
        },
    }
    page = operator_ui.render_dashboard(state)
    assert "<unsafe>" not in page
    assert "&lt;unsafe&gt;" in page
    assert "Discovery Queue" in page
    assert "provider-required" in page
