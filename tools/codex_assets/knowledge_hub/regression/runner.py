"""Regression suite selection and execution."""

import concurrent.futures

from . import support as _support

# A full regression suite can span midnight. Freeze one resolved calendar date
# into every child command so parent assertions and public Hub CLIs evaluate the
# same deterministic snapshot for the lifetime of this run.
_support.child_env["KNOWLEDGE_TODAY"] = _support.today.isoformat()
if _support.today_source == "system-date":
    _support.today_source = "captured-system-date"

from .model import *  # noqa: F401,F403,E402
from .model_index import *  # noqa: F401,F403,E402
from .lifecycle import *  # noqa: F401,F403,E402
from .lifecycle_2 import *  # noqa: F401,F403,E402
from .lifecycle_3 import *  # noqa: F401,F403,E402
from .lifecycle_4 import *  # noqa: F401,F403,E402
from .retrieval import *  # noqa: F401,F403,E402
from .obsidian import *  # noqa: F401,F403,E402
from .governance import *  # noqa: F401,F403,E402
from .terminal_gates import *  # noqa: F401,F403,E402
# Override the legacy generated status-source-governance case with the extracted
# time-safe contract. The result id and full-suite position remain unchanged.
from .source_governance import test_status_source_governance_summary  # noqa: E402
from .product_gates import *  # noqa: F401,F403,E402
# Preserve the owner-review result id and suite position while exposing the
# exact failing predicate when this product contract drifts.
from .owner_review_contract import test_final_gate_owner_review_blocker  # noqa: E402

full_tests = [
    test_baseline,
    test_governance_goal_path_allowed,
    test_status_wrong_bucket,
    test_status_noncanonical_only,
    test_owner_partial_resolved,
    test_owner_ready_missing_nonblocking_after_resolution,
    test_owner_single_form,
    test_owner_forms_text_jsonl_output,
    test_owner_forms_jsonl_single_output,
    test_owner_forms_jsonl_all_open_output,
    test_owner_forms_jsonl_conflict_json_mode,
    test_owner_checklist_context,
    test_owner_form_context,
    test_owner_source_identity_context,
    test_owner_prefill_candidates_manual_fields,
    test_owner_evidence_readiness,
    test_owner_inbox_contract,
    test_owner_summary_all_open,
    test_owner_summary_by_owner,
    test_owner_handoff_packet_json,
    test_owner_dispatch_source_scope_isolation,
    test_manifest_regression_count_capture_qualifier,
    test_manifest_profile_boundary_advisory,
    test_owner_next_open_focus,
    test_status_next_owner_gate,
    test_status_owner_ready_source_no_registry_fallback,
    test_final_gate_maintenance_entry_wording_no_section_drift,
    test_status_text_owner_summary_commands,
    test_status_owner_gates_exit_code_blocker,
    test_final_gate_owner_review_blocker,
    test_final_gate_quick_regression_evidence_boundary,
    test_status_product_profile_blocks_noncanonical_residue,
    test_final_gate_product_review_queue_owner_review_blocker,
    test_final_gate_empty_child_json_blocker,
    test_final_gate_default_regression_path,
    test_final_gate_source_final_state_field_gap,
    test_final_gate_strict_status_nonowner_blocker,
    test_final_gap_readability_positive_contracts,
    test_owner_landing_plan_project_index,
    test_owner_validate_forms_partial_coverage_warning,
    test_owner_archive_only_explicit_path_contract,
    test_owner_archive_only_rejects_non_archive_target,
    test_owner_landing_plan_requires_owner_ready_package_missing,
    test_owner_landing_plan_requires_owner_ready_package_invalid,
    test_owner_landing_plan_requires_owner_ready_package_repo_relative_command,
    test_owner_landing_plan_requires_owner_ready_package_duplicate,
    test_owner_form_target_decision_candidate_gate,
    test_owner_form_decision_target_pair_gate,
    test_owner_form_decision_target_pair_positive_gate,
    test_owner_form_routing_owner_reviewed_by_gate,
    test_owner_form_must_not_tamper_gate,
    test_owner_form_allowed_decisions_tamper_gate,
    test_owner_form_target_candidates_tamper_gate,
    test_owner_form_source_identity_mismatch,
    test_manual_entry_project_index_hint,
    test_manual_entry_registered_source_binding,
    test_manual_entry_project_from_domain,
    test_manual_entry_default_dates,
    test_manual_entry_owner_override,
    test_manual_entry_owner_registry_and_personal_defaults,
    test_manual_entry_docs_owner_option,
    test_manual_entry_offline_docs,
    test_readme_offline_shortest_paths,
    test_no_user_absolute_path_persisted,
    test_user_path_redaction_in_tool_outputs,
    test_source_control_directory_gate,
    test_source_control_raw_copy_body_gate,
    test_owner_target_existence_gate,
    test_owner_target_materialization_read_only_no_source_dependency,
    test_owner_decision_draft_leak_warning,
    test_manual_entry_offline_package_consistency,
    test_manual_entry_validation_diagnostics_default,
    test_manual_entry_readability_fields,
    test_manual_entry_archive_default_status,
    test_offline_validation_template_placeholders,
    test_governance_audit_readability_gate,
    test_ai_generated_item_provenance_gate,
    test_manual_entry_no_migration_ledger_guide,
    test_manual_entry_template_selection,
    test_templates_required_sections,
    test_index_readme_maintenance_coverage,
    test_by_topic_first_screen_readability_contract,
    test_review_queue_json_contract,
    test_review_queue_apply_tool_contract,
    test_external_review_queue_apply_persists_source_metadata,
    test_summary_backfill_archived_only_contract,
    test_orphan_files_advisory_contract,
    test_reviewing_triage_json_contract,
    test_regression_trend_from_json_contract,
    test_health_summary_operational_fields,
    test_index_plan_extended_sections,
    test_manifest_latest_filename_date_only,
    test_manifest_jsonl_profile_gate,
    test_template_readability_field_gate,
    test_index_plan_topic_schema_health,
    test_registry_canonical_topic_retention_paths,
    test_index_plan_decision_registry_health,
    test_index_decision_registry_gate,
    test_index_topic_zero_bucket_allowed,
    test_status_source_governance_summary,
    test_source_check_health_contract,
    test_source_check_report_only_helper,
    test_source_check_rejects_unsafe_runtime_command,
    test_final_gate_source_check_runtime_failed_blocker,
    test_review_after_near_due_json_contract,
    test_automation_report_only_safety_gate,
    test_source_coverage_date_filename_selection,
    test_source_coverage_duplicate_source_id_warning,
    test_review_after_as_of_deterministic,
    test_stale_review_after_warning_surface,
    test_source_review_after_stale_surface,
    test_source_manual_entry_guide,
    test_source_manual_entry_enum_guide,
    test_source_manual_entry_guide_check_command,
    test_source_manual_entry_status_coverage_sync,
    test_source_manual_entry_unknown_owner_warning,
    test_source_manual_entry_requires_check_or_reason,
    test_source_manual_entry_docs_check_preferred,
    test_source_manual_entry_role_aware_recommendations,
    test_knowledge_search_structured_filters,
    test_knowledge_search_structured_filters_exclude_unregistered_raw,
    test_knowledge_search_kind_alias_filters,
    test_knowledge_search_rejects_metadata_only_item,
    test_knowledge_search_invalid_filters,
    test_knowledge_context_budget_explainability,
    test_knowledge_context_self_route,
    test_knowledge_context_control_plane_query_override,
    test_knowledge_context_control_plane_alias_ambiguity,
    test_embedded_asan_methodology_deprojectized,
    test_stable_governance_command_examples,
]

quick_test_names = {
    "test_baseline",
    "test_governance_goal_path_allowed",
    "test_status_wrong_bucket",
    "test_source_control_directory_gate",
    "test_owner_target_existence_gate",
    "test_owner_target_materialization_read_only_no_source_dependency",
    "test_review_queue_json_contract",
    "test_orphan_files_advisory_contract",
    "test_reviewing_triage_json_contract",
    "test_regression_trend_from_json_contract",
    "test_health_summary_operational_fields",
    "test_source_check_health_contract",
    "test_knowledge_search_structured_filters",
    "test_knowledge_search_invalid_filters",
    "test_knowledge_context_budget_explainability",
    "test_knowledge_context_self_route",
    "test_knowledge_context_control_plane_query_override",
    "test_knowledge_context_control_plane_alias_ambiguity",
    "test_embedded_asan_methodology_deprojectized",
    "test_no_user_absolute_path_persisted",
    "test_user_path_redaction_in_tool_outputs",
    "test_stable_governance_command_examples",
    "test_status_product_profile_blocks_noncanonical_residue",
}

if args.test:
    requested_test_names = set(args.test)
    known_test_names = {test_fn.__name__ for test_fn in full_tests}
    unknown_test_names = sorted(requested_test_names - known_test_names)
    if unknown_test_names:
        parser.error("unknown regression test function(s): {}".format(", ".join(unknown_test_names)))
    selected_tests = [test_fn for test_fn in full_tests if test_fn.__name__ in requested_test_names]
else:
    selected_tests = (
        [test_fn for test_fn in full_tests if test_fn.__name__ in quick_test_names]
        if args.suite == "quick"
        else full_tests
    )

full_test_names = [test_fn.__name__ for test_fn in full_tests]
duplicate_test_names = sorted(
    name for name in set(full_test_names) if full_test_names.count(name) > 1
)
if duplicate_test_names:
    parser.error(
        "duplicate regression test function(s): {}".format(
            ", ".join(duplicate_test_names)
        )
    )

serial_tail_test_names = {"test_user_path_redaction_in_tool_outputs"}
parallel_tests = [test_fn for test_fn in selected_tests if test_fn.__name__ not in serial_tail_test_names]
serial_tail_tests = [test_fn for test_fn in selected_tests if test_fn.__name__ in serial_tail_test_names]

if regression_jobs == 1:
    for test_fn in selected_tests:
        results.extend(run_test(test_fn))
else:
    with concurrent.futures.ThreadPoolExecutor(max_workers=regression_jobs) as executor:
        for test_results in executor.map(run_test, parallel_tests):
            results.extend(test_results)
    for test_fn in serial_tail_tests:
        results.extend(run_test(test_fn))

result_ids = [str(result.get("id", "")) for result in results]
duplicate_result_ids = sorted(
    result_id for result_id in set(result_ids) if result_ids.count(result_id) > 1
)
status = (
    "pass"
    if not duplicate_result_ids
    and all(result["status"] == "pass" for result in results)
    else "fail"
)
output = {
    "status": status,
    "root": display_path(root),
    "read_only": True,
    "writes_real_repo": False,
    "today": today.isoformat(),
    "as_of_source": today_source,
    "suite": args.suite,
    "jobs": regression_jobs,
    "selected_test_count": len(selected_tests),
    "full_test_count": len(full_tests),
    "duplicate_result_ids": duplicate_result_ids,
    "slowest_results": sorted(
        [
            {
                "id": result.get("id", ""),
                "test_fn": result.get("test_fn", ""),
                "duration_sec": result.get("duration_sec", 0),
                "status": result.get("status", ""),
            }
            for result in results
        ],
        key=lambda row: row["duration_sec"],
        reverse=True,
    )[:10],
    "kept_temp": args.keep_temp,
    "result_count": len(results),
    "results": results,
}

if args.summary_json:
    failed_results = [
        result for result in results if result.get("status") != "pass"
    ]
    summary_output = {
        key: value for key, value in output.items() if key != "results"
    }
    summary_output.update(
        {
            "projection": "knowledge-regression-summary-v1",
            "passed_result_count": sum(
                1 for result in results if result.get("status") == "pass"
            ),
            "failed_result_count": len(failed_results),
            "failure_ids": [
                str(result.get("id", "")) for result in failed_results
            ],
            "failures": failed_results[:20],
            "failures_truncated": len(failed_results) > 20,
        }
    )
    print(json.dumps(summary_output, ensure_ascii=False, indent=2))
elif args.json:
    print(json.dumps(output, ensure_ascii=False, indent=2))
else:
    print("# Knowledge Regression")
    print()
    print(f"- status: {status}")
    print(f"- results: {len(results)}")
    print("- writes real repo: false")
    for result in results:
        print(f"- {result['status']}: {result['id']} - {result['title']}")
        if result.get("fixture_repo"):
            print(f"  fixture: {result['fixture_repo']}")

sys.exit(0 if status == "pass" else 1)
