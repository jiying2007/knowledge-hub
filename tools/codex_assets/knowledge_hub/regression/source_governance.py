"""Time-safe source-governance regression contracts."""

from .support import *  # noqa: F401,F403


def test_status_source_governance_summary():
    result = run_cmd(root, ["rtk", "bash", "tools/knowledge-status.sh", "--json"])
    check_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-check.sh",
            "--dry-run",
            "--json",
            "--diagnostics",
        ],
    )
    expected_final_gate_command = (
        "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product"
    )
    if today_source != "system-date":
        expected_final_gate_command = (
            "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh "
            f"--as-of {today.isoformat()} --json --final-profile product"
        )
    parsed = {}
    check_parsed = {}
    parse_error = ""
    check_parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    try:
        check_parsed = json.loads(check_result["stdout"])
    except Exception as exc:
        check_parse_error = str(exc)
    sources = (
        parsed.get("sources", {})
        if isinstance(parsed.get("sources"), dict)
        else {}
    )
    registry = (
        parsed.get("registry", {})
        if isinstance(parsed.get("registry"), dict)
        else {}
    )
    owner_gates = (
        parsed.get("owner_gates", {})
        if isinstance(parsed.get("owner_gates"), dict)
        else {}
    )
    check_selection = (
        check_parsed.get("source_coverage_selection", {})
        if isinstance(check_parsed, dict)
        else {}
    )
    check_health = (
        check_parsed.get("source_coverage_health", {})
        if isinstance(check_parsed, dict)
        else {}
    )
    check_source_check_health = (
        check_parsed.get("source_check_health", {})
        if isinstance(check_parsed, dict)
        else {}
    )
    status_source_check_health = (
        sources.get("source_check_health", {})
        if isinstance(sources.get("source_check_health"), dict)
        else {}
    )
    status_source_runtime = (
        sources.get("source_runtime", {})
        if isinstance(sources.get("source_runtime"), dict)
        else {}
    )
    source_recovery_rows = (
        sources.get("source_recovery_rows", [])
        if isinstance(sources.get("source_recovery_rows"), list)
        else []
    )
    source_recovery_by_id = {
        row.get("source_id"): row
        for row in source_recovery_rows
        if isinstance(row, dict)
    }
    pcr02_docs_recovery = source_recovery_by_id.get("pcr02-project-docs", {})
    pcr02_tools_recovery = source_recovery_by_id.get("pcr02-project-tools", {})
    stale_review_after_count = registry.get("stale_review_after_count")
    expect(
        result["exit_code"] == 0
        and not parse_error
        and check_result["exit_code"] == 0
        and not check_parse_error
        and sources.get("registered_count") == 18
        and sources.get("latest_coverage_manifest")
        == "artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl"
        and sources.get("latest_coverage_selection", {}).get("strategy")
        == "filename-yyyymmdd-sort-last"
        and sources.get("latest_coverage_selection", {}).get("selected")
        == "artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl"
        and sources.get("latest_coverage_selection", {}).get("candidate_count", 0)
        >= 1
        and sources.get("latest_coverage_selection", {}).get(
            "dated_candidate_count", 0
        )
        >= 1
        and check_selection.get("selected")
        == "artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl"
        and check_selection.get("strategy") == "filename-yyyymmdd-sort-last"
        and check_health.get("registered_source_count") == 18
        and check_health.get("row_count") == 18
        and check_health.get("unique_source_count") == 18
        and check_health.get("missing_source_ids") == []
        and check_health.get("stale_source_ids") == []
        and check_health.get("duplicate_source_ids") == []
        and check_source_check_health.get("with_check_count") == 18
        and check_source_check_health.get("with_no_check_reason_count") == 0
        and check_source_check_health.get("missing_check_or_reason_ids") == []
        and check_source_check_health.get("non_rtk_check_ids") == []
        and status_source_check_health.get("with_check_count") == 18
        and status_source_check_health.get("executed") is False
        and status_source_runtime.get("status") == "pass"
        and status_source_runtime.get("scope") == "all"
        and status_source_runtime.get("registry_source_count") == 18
        and status_source_runtime.get("executed_count") == 18
        and status_source_runtime.get("source_check_health_executed") is True
        and len(source_recovery_rows) == 18
        and pcr02_docs_recovery.get("final_disposition") == "hub-canonical"
        and pcr02_docs_recovery.get("coverage_status") == "hub-canonical"
        and "hash-only-provenance"
        in pcr02_docs_recovery.get("coverage_classification", "")
        and "旧正文副本已按终态剪枝"
        in pcr02_docs_recovery.get("coverage_decision", "")
        and pcr02_docs_recovery.get("has_check") is True
        and pcr02_docs_recovery.get("has_no_check_reason") is False
        and pcr02_tools_recovery.get("check_contract_status") == "ok"
        and pcr02_tools_recovery.get("has_check") is True
        and pcr02_tools_recovery.get("coverage_status") == "hub-canonical"
        and isinstance(stale_review_after_count, int)
        and stale_review_after_count >= 0
        and registry.get("review_after_command")
        == "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date"
        and registry.get("review_after_near_due_command")
        == (
            "rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh "
            f"--as-of {today.isoformat()} --window-days 30 --json"
        )
        and sources.get("source_check_report_command")
        == (
            "rtk bash ~/knowledge-hub/tools/knowledge-source-check.sh "
            f"--scope all --as-of {today.isoformat()} --json"
        )
        and owner_gates.get("owner_ready_package_coverage") == "0/7"
        and parsed.get("final_gate_command") == expected_final_gate_command,
        "status-source-governance-summary",
        "status JSON exposes source coverage, review_after and final gate recovery summary without assuming stale count is permanently zero",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "check_exit_code": check_result["exit_code"],
            "check_parse_error": check_parse_error,
            "registered_count": sources.get("registered_count"),
            "latest_coverage_manifest": sources.get("latest_coverage_manifest"),
            "latest_coverage_selection": sources.get("latest_coverage_selection"),
            "check_source_coverage_selection": check_selection,
            "check_source_coverage_health": check_health,
            "check_source_check_health": check_source_check_health,
            "status_source_check_health": status_source_check_health,
            "status_source_runtime": status_source_runtime,
            "stale_review_after_count": stale_review_after_count,
            "review_after_command": registry.get("review_after_command"),
            "review_after_near_due_command": registry.get(
                "review_after_near_due_command"
            ),
            "source_check_report_command": sources.get(
                "source_check_report_command"
            ),
            "source_recovery_row_count": len(source_recovery_rows),
            "pcr02_docs_recovery": pcr02_docs_recovery,
            "pcr02_tools_recovery": pcr02_tools_recovery,
            "owner_ready_package_coverage": owner_gates.get(
                "owner_ready_package_coverage"
            ),
            "final_gate_command": parsed.get("final_gate_command"),
            "expected_final_gate_command": expected_final_gate_command,
            "status": parsed.get("status"),
            "stdout_sample": result["stdout"][:1200],
        },
    )
