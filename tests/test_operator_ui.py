from __future__ import annotations

import json
import pathlib
import threading
import urllib.error
import urllib.request

from tools.codex_assets.knowledge_hub import operator_actions, operator_state, operator_ui


def _sample_state():
    return {
        "schema_version": 1,
        "projection": "knowledge-operator-state-v1",
        "generated_at": "2026-09-15T12:00:00Z",
        "read_only": True,
        "status": "needs-review",
        "status_summary": {
            "status": "needs-review",
            "next_actions_zh": ["处理 owner gate"],
        },
        "readiness": {
            "project_count": 2,
            "structural_ready_count": 2,
            "source_mapping_ready_count": 1,
            "owner_boundary_ready_count": 1,
            "evidence_field_complete_count": 1,
            "evidence_ready_count": 0,
            "human_attention_count": 1,
            "machine_candidate_project_count": 1,
            "projects": [
                {
                    "project_id": "demo",
                    "name": "<script>alert(1)</script>",
                    "evidence_profile": "software-tool",
                    "evidence_status": "contract-evidence-pending",
                    "evidence_field_status": "complete-awaiting-declaration",
                    "owner_boundary_status": "ready",
                    "source_mapping_ready": True,
                    "missing_fields": [],
                    "invalid_fields": [],
                    "attention": ["owner-declaration"],
                    "action_classes": ["human-authorization"],
                    "machine_candidate": False,
                    "needs_human_attention": True,
                }
            ],
        },
        "action_queue": {
            "read_only": True,
            "automatic_execution_enabled": False,
            "machine_candidate_count": 1,
            "machine_blocked_count": 1,
            "human_project_count": 1,
            "actions": [
                {
                    "id": "tool:missing:release_ref",
                    "scope": "project",
                    "project_id": "tool",
                    "field": "release_ref",
                    "execution_class": "machine-discovery",
                    "summary_zh": "先自动检索现有 release。",
                },
                {
                    "id": "demo:owner-declaration",
                    "scope": "project",
                    "project_id": "demo",
                    "field": "owner-declaration",
                    "execution_class": "human-authorization",
                    "summary_zh": "等待 owner 声明。",
                },
            ],
        },
        "external_closure": {
            "status": "needs-review",
            "open_count": 1,
            "open_gaps": [
                {
                    "id": "production-retrieval-eval",
                    "status": "open",
                    "owner": "production",
                }
            ],
        },
        "terminal_closure": {
            "status": "needs-review",
            "terminal": False,
            "blockers": ["external_closure"],
        },
        "next_actions_zh": ["处理 owner gate"],
    }


def test_project_projection_marks_owner_declaration_as_human_attention():
    row = {
        "project_id": "demo",
        "name": "Demo",
        "evidence_profile": "software-tool",
        "evidence_status": "contract-evidence-pending",
        "evidence_field_status": "complete-awaiting-declaration",
        "owner_boundary_status": "ready",
        "source_mapping_ready": True,
        "evidence_contract": {
            "missing_fields": [],
            "invalid_fields": [],
        },
    }
    projected = operator_state._project_projection(row)
    assert projected["needs_human_attention"] is True
    assert projected["action_classes"] == ["human-authorization"]
    assert projected["attention"] == ["owner-declaration"]


def test_machine_discovery_is_not_mislabeled_as_human_attention():
    row = {
        "project_id": "tool",
        "name": "Tool",
        "evidence_profile": "software-tool",
        "evidence_status": "contract-evidence-pending",
        "evidence_field_status": "incomplete",
        "owner_boundary_status": "ready",
        "source_mapping_ready": True,
        "evidence_contract": {
            "missing_fields": ["artifact_refs", "release_ref", "rollback_ref"],
            "invalid_fields": [],
        },
    }
    projected = operator_state._project_projection(row)
    assert projected["machine_candidate"] is True
    assert projected["needs_human_attention"] is False
    assert "machine-discovery" in projected["action_classes"]
    assert "machine-after-prerequisite" in projected["action_classes"]


def test_device_and_owner_gaps_remain_human_exceptions():
    row = {
        "project_id": "target",
        "evidence_field_status": "incomplete",
        "owner_boundary_status": "pending",
        "missing_fields": ["device_refs", "owner_ref"],
        "invalid_fields": [],
    }
    actions = operator_actions.project_actions(row)
    classes = {action["execution_class"] for action in actions}
    assert "real-world-evidence" in classes
    assert "human-authorization" in classes


def test_release_discovery_escalates_without_auto_publish():
    actions = operator_actions.project_actions(
        {
            "project_id": "tool",
            "evidence_field_status": "incomplete",
            "owner_boundary_status": "ready",
            "missing_fields": ["release_ref"],
            "invalid_fields": [],
        }
    )
    assert len(actions) == 1
    assert actions[0]["execution_class"] == "machine-discovery"
    assert actions[0]["escalation_class"] == "human-authorization"
    assert actions[0]["automatic_execution_enabled"] is False


def test_external_gap_classification_is_fail_closed():
    queue = operator_actions.build_action_queue(
        [],
        {
            "open_gaps": [
                {"id": "production-retrieval-eval", "owner": "runtime-owner"},
                {"id": "repository-private-boundary", "owner": "repository-admin"},
            ]
        },
    )
    classes = {row["id"]: row["execution_class"] for row in queue["actions"]}
    assert classes["external:production-retrieval-eval"] == "real-world-evidence"
    assert classes["external:repository-private-boundary"] == "external-environment"
    assert queue["automatic_execution_enabled"] is False


def test_operator_state_stays_read_only(monkeypatch, tmp_path: pathlib.Path):
    monkeypatch.setattr(
        operator_state,
        "_status_summary",
        lambda root: {"status": "needs-review", "next_actions_zh": ["owner"]},
    )
    monkeypatch.setattr(
        operator_state,
        "_project_readiness",
        lambda root: {
            "project_count": 1,
            "structural_ready_count": 1,
            "source_mapping_ready_count": 1,
            "owner_boundary_ready_count": 1,
            "evidence_field_complete_count": 1,
            "evidence_ready_count": 0,
            "rows": [],
        },
    )
    monkeypatch.setattr(
        operator_state,
        "_external_state",
        lambda root: {"status": "needs-review", "open_count": 1, "open_gaps": []},
    )
    monkeypatch.setattr(
        operator_state,
        "_terminal_state",
        lambda root: {"status": "not-evaluated", "terminal": False},
    )
    state = operator_state.build_operator_state(tmp_path)
    assert state["read_only"] is True
    assert state["status"] == "needs-review"
    assert state["external_closure"]["open_count"] == 1
    assert state["action_queue"]["automatic_execution_enabled"] is False


def test_dashboard_escapes_dynamic_project_name_and_shows_split_queues():
    page = operator_ui.render_dashboard(_sample_state())
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "Machine Queue" in page
    assert "Human / External Queue" in page
    assert "machine-discovery" in page
    assert "human-authorization" in page
    assert "read-only" in page.lower()


def test_http_surface_is_loopback_and_rejects_write_methods(tmp_path: pathlib.Path):
    server = operator_ui.OperatorHTTPServer(
        (operator_ui.LOOPBACK_HOST, 0),
        tmp_path,
        state_builder=lambda root: _sample_state(),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        with urllib.request.urlopen("http://127.0.0.1:{}/api/state".format(port), timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert payload["read_only"] is True
            assert response.headers["Cache-Control"] == "no-store"

        request = urllib.request.Request(
            "http://127.0.0.1:{}/api/state".format(port),
            data=b"{}",
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as exc:
            assert exc.code == 405
            body = json.loads(exc.read().decode("utf-8"))
            assert body["status"] == "read-only"
        else:
            raise AssertionError("POST unexpectedly succeeded")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_live_private_fact_routes_stale_canonical_gap_to_machine_ratchet():
    queue = operator_actions.build_action_queue(
        [],
        {
            "open_gaps": [
                {"id": "repository-private-boundary", "owner": "repository-admin"}
            ]
        },
        terminal={
            "hosting_posture": {
                "status": "pass",
                "fact_drift": [
                    {
                        "id": "repository-private-boundary",
                        "type": "live-fact-ahead-of-canonical",
                    }
                ],
            }
        },
    )

    action = next(row for row in queue["actions"] if row["field"] == "repository-private-boundary")
    assert action["execution_class"] == "machine-after-prerequisite"
    assert action["automation_eligible"] is True
    assert action["automatic_execution_enabled"] is False
    assert queue["autonomous_candidate_count"] == 1
