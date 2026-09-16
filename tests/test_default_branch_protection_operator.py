from __future__ import annotations

from tools.codex_assets.knowledge_hub import operator_actions, operator_state, operator_ui


def _terminal(status="needs-review", reason="default-branch-unprotected"):
    return {
        "status": "needs-review" if status != "pass" else "pass",
        "terminal": False,
        "blockers": [] if status == "pass" else ["default_branch_protection"],
        "default_branch_protection": {
            "required": True,
            "status": status,
            "branch": "master",
            "owner": "repository-admin",
            "protected": status == "pass",
            "protection_observed": True,
            "reason": reason,
        },
    }


def test_unprotected_default_branch_enters_existing_external_queue():
    queue = operator_actions.build_action_queue([], {}, terminal=_terminal())

    actions = [
        row
        for row in queue["actions"]
        if row["id"] == "governance:default-branch-protection:master"
    ]
    assert len(actions) == 1
    action = actions[0]
    assert action["execution_class"] == "external-environment"
    assert action["scope"] == "external"
    assert action["field"] == "default-branch-protection"
    assert action["owner"] == "repository-admin"
    assert action["automatic_execution_enabled"] is False
    assert queue["automatic_execution_enabled"] is False


def test_protected_default_branch_does_not_create_governance_action():
    queue = operator_actions.build_action_queue([], {}, terminal=_terminal(status="pass", reason=""))

    assert not any(
        row["id"].startswith("governance:default-branch-protection")
        for row in queue["actions"]
    )


def test_operator_state_exposes_machine_posture_and_routes_action(monkeypatch, tmp_path):
    monkeypatch.setattr(
        operator_state,
        "_project_readiness",
        lambda root: {
            "project_count": 0,
            "structural_ready_count": 0,
            "source_mapping_ready_count": 0,
            "owner_boundary_ready_count": 0,
            "evidence_field_complete_count": 0,
            "evidence_ready_count": 0,
            "rows": [],
        },
    )
    monkeypatch.setattr(
        operator_state,
        "_status_summary",
        lambda root: {"status": "needs-review", "next_actions_zh": []},
    )
    monkeypatch.setattr(
        operator_state,
        "_external_state",
        lambda root: {"status": "pass", "open_count": 0, "open_gaps": []},
    )
    monkeypatch.setattr(operator_state, "_terminal_state", lambda root: _terminal())
    monkeypatch.setattr(
        operator_state,
        "build_binding_lifecycle_projection",
        lambda root, inputs=None: {
            "status": "not-observed",
            "next_execution_class": "",
            "next_summary_zh": "",
        },
    )
    monkeypatch.setattr(
        operator_state,
        "build_discovery_projection",
        lambda root, queue: {
            "status": "pass",
            "candidate_found_count": 0,
            "provider_required_count": 0,
            "rows": [],
        },
    )

    state = operator_state.build_operator_state(tmp_path)

    posture = state["terminal_closure"]["default_branch_protection"]
    assert posture["status"] == "needs-review"
    assert posture["protected"] is False
    assert any(
        row["id"] == "governance:default-branch-protection:master"
        for row in state["action_queue"]["actions"]
    )


def test_dashboard_surfaces_branch_protection_action_without_write_control():
    state = {
        "status": "needs-review",
        "readiness": {"project_count": 0, "projects": []},
        "external_closure": {"open_count": 0, "open_gaps": []},
        "terminal_closure": _terminal(),
        "binding_lifecycle": {"status": "not-observed", "stages": []},
        "discovery": {"candidate_found_count": 0, "provider_required_count": 0, "rows": []},
        "action_queue": operator_actions.build_action_queue([], {}, terminal=_terminal()),
        "next_actions_zh": [],
    }

    page = operator_ui.render_dashboard(state)

    assert "default-branch-protection" in page
    assert "repository administrator" in page
    assert "<form" not in page.lower()
    assert 'method="post"' not in page.lower()
