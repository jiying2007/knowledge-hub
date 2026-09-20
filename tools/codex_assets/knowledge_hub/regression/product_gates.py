"""Product-profile final gate regression contracts."""

from .support import *  # noqa: F401,F403


def _run_product_gate(repo, extra_args="", extra_env=""):
    command = "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1"
    if extra_env:
        command += " " + extra_env
    command += " rtk bash tools/knowledge-final-gate.sh --json"
    if extra_args:
        command += " " + extra_args
    result = run_cmd(repo, ["rtk", "bash", "-lc", command])
    try:
        payload = json.loads(result["stdout"])
    except Exception as exc:
        payload = {"parse_error": str(exc)}
    return result, payload


def _skip_inside_product_gate(result_id, title):
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") != "1":
        return False
    expect(True, result_id, title, {"skipped_in_inner_final_gate": True})
    return True


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
    owner = payload.get("owner_and_real_evidence", {})
    project_count = int(owner.get("project_count", 0) or 0)
    owner_gap = next(
        (row for row in payload.get("gap_map", []) if row.get("gap_id") == "owner-and-real-evidence-pending"),
        {},
    )
    expect(
        result["exit_code"] == 0
        and terminal_result["exit_code"] == 2
        and payload.get("final_profile") == "product"
        and payload.get("status") == "needs-review"
        and payload.get("platform_status", {}).get("status") == "pass"
        and payload.get("terminal") is False
        and owner.get("status") == "needs-review"
        and owner.get("project_boundary_owner_ready") is True
        and project_count > 0
        and owner.get("decision_owner_ready_count") == project_count
        and owner.get("owner_ref_ready_count") == project_count
        and owner.get("owner_boundary_ready_count") == project_count
        and owner.get("specialized_owner_ready_candidate_count") == 3
        and owner.get("pending_specialized_owner_candidate_count") == 0
        and owner.get("owner_gate_open_count") == 7
        and owner_gap.get("gap_type") == "owner-review"
        and owner_gap.get("codex_auto_can_complete") is False
        and owner_gap.get("requires_owner_decision") is True
        and payload.get("checks", {}).get("knowledge_status_strict", {}).get("status") == "needs-review"
        and "product_status" not in payload.get("platform_status", {}).get("blockers", [])
        and terminal_payload.get("status") == "needs-review",
        result_id,
        title,
        {
            "exit_code": result["exit_code"],
            "terminal_exit_code": terminal_result["exit_code"],
            "status": payload.get("status"),
            "owner_and_real_evidence": owner,
            "platform_status": payload.get("platform_status", {}),
            "gap_map": payload.get("gap_map", []),
        },
        repo,
    )


def test_final_gate_quick_regression_evidence_boundary():
    result_id = "final-gate-quick-regression-evidence-boundary"
    title = "quick product gate cannot be mistaken for full terminal regression evidence"
    if _skip_inside_product_gate(result_id, title):
        return
    result, payload = _run_product_gate(root)
    regression = payload.get("checks", {}).get("knowledge_regression", {})
    expect(
        result["exit_code"] == 0
        and payload.get("final_profile") == "product"
        and payload.get("regression_suite") == "quick"
        and regression.get("status") == "not-run"
        and regression.get("full_regression_executed") is False
        and payload.get("delivery_readiness", {}).get("full_regression_ready") is False
        and payload.get("terminal") is False,
        result_id,
        title,
        {
            "exit_code": result["exit_code"],
            "regression": regression,
            "delivery_readiness": payload.get("delivery_readiness", {}),
        },
    )


def test_final_gate_product_review_queue_owner_review_blocker():
    result_id = "final-gate-product-review-queue-owner-review-blocker"
    title = "product gate classifies pending human review as owner review instead of technical failure"
    if _skip_inside_product_gate(result_id, title):
        return
    repo = copy_repo(result_id)
    seed_pending_review_queue_items(repo, count=2)
    setup_error = init_temp_git_repo(repo)
    if setup_error:
        expect(False, result_id, title, setup_error, repo)
        return
    result, payload = _run_product_gate(repo)
    owner = payload.get("owner_and_real_evidence", {})
    expect(
        result["exit_code"] == 0
        and payload.get("final_profile") == "product"
        and payload.get("status") == "needs-review"
        and payload.get("platform_status", {}).get("status") == "pass"
        and owner.get("review_queue_pending_count", 0) >= 2
        and owner.get("status") == "needs-review"
        and "product_status" not in payload.get("platform_status", {}).get("blockers", []),
        result_id,
        title,
        {
            "exit_code": result["exit_code"],
            "status": payload.get("status"),
            "owner_and_real_evidence": owner,
            "platform_status": payload.get("platform_status", {}),
        },
        repo,
    )


def test_final_gate_empty_child_json_blocker():
    result_id = "final-gate-empty-child-json-blocker"
    title = "product gate rejects empty child JSON even when the child exits zero"
    if _skip_inside_product_gate(result_id, title):
        return
    repo = copy_repo(result_id)
    (repo / "tools" / "knowledge-check.sh").write_text("#!/usr/bin/env bash\nexit 0\n")
    setup_error = init_temp_git_repo(repo)
    if setup_error:
        expect(False, result_id, title, setup_error, repo)
        return
    result, payload = _run_product_gate(repo)
    knowledge_check = payload.get("checks", {}).get("knowledge_check", {})
    blocker = next(
        (row for row in payload.get("blockers", []) if row.get("id") == "knowledge-check-unparseable"),
        {},
    )
    expect(
        result["exit_code"] == 1
        and payload.get("status") == "needs-fix"
        and knowledge_check.get("status") == "unparseable"
        and "empty JSON output" in knowledge_check.get("parse_error", "")
        and blocker.get("severity") == "blocker",
        result_id,
        title,
        {
            "exit_code": result["exit_code"],
            "status": payload.get("status"),
            "knowledge_check": knowledge_check,
            "blockers": payload.get("blockers", []),
        },
        repo,
    )


def test_final_gate_default_regression_path():
    result_id = "final-gate-default-regression-path"
    title = "full product gate consumes the selected modular regression contract"
    if _skip_inside_product_gate(result_id, title):
        return
    repo = copy_repo(result_id)
    fixture_module = (
        repo
        / "tools"
        / "codex_assets"
        / "knowledge_hub"
        / "regression_fixture_cli.py"
    )
    fixture_module.write_text(
        "import json\n"
        "print(json.dumps({!r}, separators=(',', ':')))\n".format(
            {
                "status": "pass",
                "suite": "full",
                "full_regression_executed": True,
                "selected_test_count": 1,
                "full_test_count": 1,
                "result_count": 1,
                "slowest_results": [],
            }
        ),
        encoding="utf-8",
    )
    (repo / "tools" / "knowledge-regression.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "SCRIPT_DIR=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
        "ROOT=\"$(cd \"$SCRIPT_DIR/..\" && pwd)\"\n"
        "cd \"$ROOT\"\n"
        "export PYTHONPATH=\"$ROOT${PYTHONPATH:+:$PYTHONPATH}\"\n"
        "exec \"$ROOT/tools/ci/python-runtime.sh\" -m "
        "tools.codex_assets.knowledge_hub.regression_fixture_cli \"$ROOT\" \"$@\"\n",
        encoding="utf-8",
    )
    setup_error = init_temp_git_repo(repo)
    if setup_error:
        expect(False, result_id, title, setup_error, repo)
        return
    result, payload = _run_product_gate(
        repo,
        "--regression-suite full --as-of {}".format(today.isoformat()),
    )
    regression = payload.get("checks", {}).get("knowledge_regression", {})
    expect(
        regression.get("exit_code") == 0
        and payload.get("final_profile") == "product"
        and payload.get("regression_suite") == "full"
        and regression.get("status") == "pass"
        and regression.get("full_regression_executed") is True
        and regression.get("result_count") == 1
        and "--summary-json --suite full --as-of {}".format(today.isoformat())
        in regression.get("command", "")
        and payload.get("platform_status", {}).get("hard_checks", {}).get("full_regression") is True
        and payload.get("delivery_readiness", {}).get("full_regression_ready") is True,
        result_id,
        title,
        {
            "exit_code": result["exit_code"],
            "status": payload.get("status"),
            "regression": regression,
            "delivery_readiness": payload.get("delivery_readiness", {}),
            "hard_checks": payload.get("platform_status", {}).get(
                "hard_checks", {}
            ),
            "blockers": payload.get("blockers", []),
        },
        repo,
    )


def test_final_gate_source_final_state_field_gap():
    result_id = "final-gate-source-final-state-field-gap"
    title = "product gate exposes typed source final-state field gaps"
    if _skip_inside_product_gate(result_id, title):
        return
    repo = copy_repo(result_id)
    sources_path = repo / "registry" / "retired-sources.jsonl"
    rows = [json.loads(line) for line in sources_path.read_text().splitlines() if line.strip()]
    target = next((row for row in rows if row.get("id") == "pcr02-project-tools"), None)
    if target is None:
        expect(False, result_id, title, {"setup_error": "pcr02-project-tools source not found"}, repo)
        return
    target.pop("final_disposition", None)
    sources_path.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n")
    setup_error = init_temp_git_repo(repo)
    if setup_error:
        expect(False, result_id, title, setup_error, repo)
        return
    result, payload = _run_product_gate(repo)
    gap = next(
        (
            row
            for row in payload.get("gap_map", [])
            if row.get("gap_id") == "source-final-state-field-missing:pcr02-project-tools:final_disposition"
        ),
        {},
    )
    expect(
        result["exit_code"] == 1
        and payload.get("status") == "needs-fix"
        and gap.get("gap_type") == "registry"
        and gap.get("source_id") == "pcr02-project-tools"
        and gap.get("field") == "final_disposition"
        and gap.get("codex_auto_can_complete") is True
        and gap.get("requires_owner_decision") is False,
        result_id,
        title,
        {
            "exit_code": result["exit_code"],
            "status": payload.get("status"),
            "gap_map": payload.get("gap_map", []),
        },
        repo,
    )


def test_final_gate_strict_status_nonowner_blocker():
    result_id = "final-gate-strict-status-nonowner-blocker"
    title = "product gate preserves parseable non-owner status blockers as technical failures"
    if _skip_inside_product_gate(result_id, title):
        return
    repo = copy_repo(result_id)
    (repo / "tools" / "knowledge-status.sh").write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' '{\"schema_version\":2,\"status\":\"needs-fix\",\"strict\":true,"
        "\"owner_gates\":{\"open_count\":0},\"review_queues\":{\"summary\":{\"total_pending_count\":0}},"
        "\"strict_blockers\":[{\"id\":\"owner-gates-command-failed\",\"severity\":\"blocker\"}]}'\n"
        "exit 1\n"
    )
    setup_error = init_temp_git_repo(repo)
    if setup_error:
        expect(False, result_id, title, setup_error, repo)
        return
    result, payload = _run_product_gate(repo)
    blocker_ids = {row.get("id") for row in payload.get("blockers", [])}
    expect(
        result["exit_code"] == 1
        and payload.get("status") == "needs-fix"
        and "product-status-failed" in blocker_ids
        and "owner-gates-command-failed" in blocker_ids
        and payload.get("platform_status", {}).get("status") == "needs-fix",
        result_id,
        title,
        {
            "exit_code": result["exit_code"],
            "status": payload.get("status"),
            "blockers": payload.get("blockers", []),
        },
        repo,
    )


def test_final_gate_source_check_runtime_failed_blocker():
    result_id = "final-gate-source-check-runtime-failed-blocker"
    title = "product gate blocks failed read-only source runtime evidence"
    if _skip_inside_product_gate(result_id, title):
        return
    repo = copy_repo(result_id)
    missing_suffix = "__kh_missing_source_check_fixture__"
    source_path = "sources/pcr02-project-tools"
    updated = update_source_registry_entry(
        repo,
        "pcr02-project-tools",
        {"check": "rtk bash -lc 'test -d {}/{}'".format(source_path, missing_suffix)},
    )
    if not updated:
        expect(False, result_id, title, {"setup_error": "pcr02-project-tools source not found"}, repo)
        return
    setup_error = init_temp_git_repo(repo)
    if setup_error:
        expect(False, result_id, title, setup_error, repo)
        return
    result, payload = _run_product_gate(repo, "--as-of 2026-06-22")
    source_runtime = payload.get("source_check_runtime", {})
    blocker = next(
        (row for row in payload.get("blockers", []) if row.get("id") == "source-check-runtime-failed"),
        {},
    )
    gap = next(
        (row for row in payload.get("gap_map", []) if row.get("gap_id") == "source-check-runtime-failed"),
        {},
    )
    expect(
        result["exit_code"] == 1
        and payload.get("status") == "needs-fix"
        and blocker.get("severity") == "blocker"
        and blocker.get("gap_type") == "source-coverage"
        and gap.get("gap_type") == "source-coverage"
        and source_runtime.get("status") == "fail"
        and source_runtime.get("runtime_execution") is True
        and source_runtime.get("read_only") is True
        and source_runtime.get("report_only") is True
        and source_runtime.get("source_body_read") is False
        and source_runtime.get("owner_gate_mutation") is False
        and source_runtime.get("memory_write") is False
        and source_runtime.get("failed_count") == 1,
        result_id,
        title,
        {
            "exit_code": result["exit_code"],
            "status": payload.get("status"),
            "blocker": blocker,
            "gap": gap,
            "source_check_runtime": source_runtime,
        },
        repo,
    )
