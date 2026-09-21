"""Focused diagnostics for the product owner-review regression contract."""

from .product_gates import _run_product_gate, _skip_inside_product_gate
from .support import *  # noqa: F401,F403


def _owner_review_predicates(payload):
    owner = payload.get("owner_and_real_evidence", {})
    owner_gap = next(
        (
            row
            for row in payload.get("gap_map", [])
            if row.get("gap_type") == "owner-review"
            and row.get("requires_owner_decision") is True
            and row.get("codex_auto_can_complete") is False
        ),
        {},
    )
    platform = payload.get("platform_status", {})
    checks = payload.get("checks", {})
    predicates = {
        "product-profile": payload.get("final_profile") == "product",
        "strict-status-needs-review": checks.get("knowledge_status_strict", {}).get("status") == "needs-review",
        "product-status-hard-check": platform.get("hard_checks", {}).get("product_status") is True,
        "owner-needs-review": owner.get("status") == "needs-review",
        "owner-gap-classification": owner_gap.get("gap_type") == "owner-review",
        "owner-gap-not-auto": owner_gap.get("codex_auto_can_complete") is False,
        "owner-gap-requires-decision": owner_gap.get("requires_owner_decision") is True,
        "platform-does-not-block-product-status": "product_status" not in platform.get("blockers", []),
    }
    return owner, owner_gap, platform, predicates


def _owner_review_actuals(result, payload):
    owner, owner_gap, platform, predicates = _owner_review_predicates(payload)
    return {
        "exit_code": result["exit_code"],
        "status": payload.get("status"),
        "owner_status": owner.get("status"),
        "owner_gap": owner_gap,
        "strict_status": payload.get("checks", {}).get("knowledge_status_strict", {}).get("status"),
        "product_status_hard_check": platform.get("hard_checks", {}).get("product_status"),
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
    actuals = _owner_review_actuals(result, payload)
    expect(
        not actuals["failed_assertions"],
        result_id,
        title,
        actuals,
        repo,
    )
