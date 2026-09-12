"""Focused diagnostics for the product owner-review regression contract."""

from .product_gates import _run_product_gate, _skip_inside_product_gate
from .support import *  # noqa: F401,F403


def _owner_review_predicates(result, payload, terminal_result, terminal_payload):
    owner = payload.get("owner_and_real_evidence", {})
    project_count = int(owner.get("project_count", 0) or 0)
    owner_gap = next(
        (
            row
            for row in payload.get("gap_map", [])
            if row.get("gap_id") == "owner-and-real-evidence-pending"
        ),
        {},
    )
    platform = payload.get("platform_status", {})
    checks = payload.get("checks", {})
    predicates = {
        "nonterminal-exit-zero": result["exit_code"] == 0,
        "terminal-exit-two": terminal_result["exit_code"] == 2,
        "product-profile": payload.get("final_profile") == "product",
        "product-needs-review": payload.get("status") == "needs-review",
        "platform-pass": platform.get("status") == "pass",
        "nonterminal": payload.get("terminal") is False,
        "owner-needs-review": owner.get("status") == "needs-review",
        "project-boundary-owner-ready": owner.get("project_boundary_owner_ready") is True,
        "project-count-positive": project_count > 0,
        "decision-owner-cardinality": owner.get("decision_owner_ready_count") == project_count,
        "owner-ref-cardinality": owner.get("owner_ref_ready_count") == project_count,
        "owner-boundary-cardinality": owner.get("owner_boundary_ready_count") == project_count,
        "specialized-owner-ready-three": owner.get("specialized_owner_ready_candidate_count") == 3,
        "specialized-owner-pending-zero": owner.get("pending_specialized_owner_candidate_count") == 0,
        "owner-gates-open-seven": owner.get("owner_gate_open_count") == 7,
        "owner-gap-classification": owner_gap.get("gap_type") == "owner-review",
        "owner-gap-not-auto": owner_gap.get("codex_auto_can_complete") is False,
        "owner-gap-requires-decision": owner_gap.get("requires_owner_decision") is True,
        "strict-status-needs-review": checks.get("knowledge_status_strict", {}).get("status") == "needs-review",
        "platform-does-not-block-product-status": "product_status" not in platform.get("blockers", []),
        "terminal-payload-needs-review": terminal_payload.get("status") == "needs-review",
    }
    return owner, owner_gap, project_count, platform, predicates


def _owner_review_actuals(result, payload, terminal_result, terminal_payload):
    owner, owner_gap, project_count, platform, predicates = _owner_review_predicates(
        result, payload, terminal_result, terminal_payload
    )
    return {
        "exit_code": result["exit_code"],
        "terminal_exit_code": terminal_result["exit_code"],
        "status": payload.get("status"),
        "terminal_status": terminal_payload.get("status"),
        "project_count": project_count,
        "owner_status": owner.get("status"),
        "project_boundary_owner_ready": owner.get("project_boundary_owner_ready"),
        "decision_owner_ready_count": owner.get("decision_owner_ready_count"),
        "owner_ref_ready_count": owner.get("owner_ref_ready_count"),
        "owner_boundary_ready_count": owner.get("owner_boundary_ready_count"),
        "specialized_owner_ready_candidate_count": owner.get("specialized_owner_ready_candidate_count"),
        "pending_specialized_owner_candidate_count": owner.get("pending_specialized_owner_candidate_count"),
        "owner_gate_open_count": owner.get("owner_gate_open_count"),
        "owner_gap": owner_gap,
        "strict_status": payload.get("checks", {}).get("knowledge_status_strict", {}).get("status"),
        "platform_status": platform.get("status"),
        "platform_blockers": platform.get("blockers", []),
        "failed_assertions": [name for name, passed in predicates.items() if not passed],
    }


def test_final_gate_owner_review_blocker():
    result_id = "final-gate-owner-review-blocker"
    title = "product gate separates owner evidence gaps from technical blockers"
    if _skip_inside_product_gate(result_id, title):
        return
    repo = copy_repo_with_open_owner_gates(result_id)
    readiness_refresh = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-project-readiness.sh",
            "--apply",
            "--json",
            "--as-of",
            today.isoformat(),
        ],
    )
    if readiness_refresh["exit_code"] != 0:
        expect(
            False,
            result_id,
            title,
            {
                "setup_error": "project readiness refresh failed",
                "exit_code": readiness_refresh["exit_code"],
                "stderr": readiness_refresh["stderr"][:1000],
            },
            repo,
        )
        return
    setup_error = init_temp_git_repo(repo)
    if setup_error:
        expect(False, result_id, title, setup_error, repo)
        return
    result, payload = _run_product_gate(repo)
    terminal_result, terminal_payload = _run_product_gate(repo, "--require-terminal")
    actuals = _owner_review_actuals(result, payload, terminal_result, terminal_payload)
    expect(
        not actuals["failed_assertions"],
        result_id,
        title,
        actuals,
        repo,
    )
