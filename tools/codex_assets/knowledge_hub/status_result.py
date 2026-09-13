import datetime as dt
from typing import Any, Dict

from .status_common import count_by, display_path, shell_command

OWNER_READY_ROW_STATUS_SOURCE = "knowledge-owner-gates.rows[].owner_ready_package_status"


def _knowledge_projection(s: Dict[str, Any]) -> Dict[str, Any]:
    check = s["knowledge_check"]
    payload = s["check_payload"]
    return {
        "exit_code": check["exit_code"],
        "status": payload.get("status", "<missing>"),
        "error_count": len(payload.get("errors", [])),
        "warning_count": len(payload.get("warnings", [])),
        "diagnostic_categories": [category.get("id", "") for category in payload.get("diagnostics", {}).get("categories", [])],
    }


def _registry_projection(s: Dict[str, Any]) -> Dict[str, Any]:
    items = s["items"]
    return {
        "item_count": len(items),
        "by_status": count_by(items, "status"),
        "by_domain": count_by(items, "domain"),
        "stale_review_after_count": len(s["stale_items"]),
        "stale_review_after_sample": s["stale_items"][:10],
        "review_after_command": s["review_after_command"],
        "review_after_near_due_command": s["review_after_near_due_command"],
    }


def _sources_projection(s: Dict[str, Any]) -> Dict[str, Any]:
    runtime = s["source_runtime"]
    runtime_payload = s["source_runtime_payload"]
    return {
        "registered_count": len(s["sources"]),
        "latest_coverage_manifest": s["latest_source_coverage"],
        "latest_coverage_selection": s["latest_source_coverage_selection"],
        "source_coverage_health": s["check_payload"].get("source_coverage_health", {}),
        "source_check_health": s["source_check_health"],
        "source_runtime": dict(runtime_payload, exit_code=runtime["exit_code"], command=shell_command(runtime["command"]), parse_error=runtime.get("parse_error", "")),
        "source_recovery_rows": s["source_recovery_rows"],
        "stale_review_after_count": len(s["stale_sources"]),
        "stale_review_after_sample": s["stale_sources"][:10],
        "review_after_command": s["source_review_after_command"],
        "source_check_report_command": s["source_check_report_command"],
        "product_source_inventory_audit": s["product_source_inventory_audit"],
        "product_noncanonical_residue_audit": s["product_noncanonical_residue_audit"],
    }


def _owner_projection(s: Dict[str, Any]) -> Dict[str, Any]:
    payload = s["owner_payload"]
    projection = s["owner_projection"]
    return {
        "command": shell_command(s["owner_gates"]["command"]), "exit_code": s["owner_gates"]["exit_code"],
        "stderr_sample": s["owner_gates"]["stderr"][:1000], "parse_error": s["owner_gates"].get("parse_error", ""),
        "worksheet_count": payload.get("worksheet_count", 0), "row_count": payload.get("row_count", 0), "open_count": s["open_owner_gate_count"],
        "resolved_count": payload.get("resolved_count", 0), "active_exposure_count": s["active_exposure_count"],
        "owner_ready_package_count": s["owner_ready_package_count"], "owner_ready_missing_count": s["owner_ready_missing_count"],
        "owner_ready_invalid_count": s["owner_ready_invalid_count"], "owner_ready_duplicate_count": s["owner_ready_duplicate_count"],
        "owner_ready_package_coverage": s["owner_ready_package_coverage"], "owner_ready_missing": payload.get("owner_ready_missing", []),
        "owner_ready_invalid": payload.get("owner_ready_invalid", []), "owner_ready_duplicate": payload.get("owner_ready_duplicate", []),
        "owner_ready_row_status_source": OWNER_READY_ROW_STATUS_SOURCE, "owner_ready_row_schema_errors": s["owner_ready_row_schema_errors"],
        "source_identity_read_policy": payload.get("source_identity_read_policy", {"source_identity_read_mode": "read-bytes-for-hash", "source_body_read_for_hash": True, "source_body_copied": False, "source_project_written": False, "owner_gate_mutation": False, "notes_zh": "status 通过 knowledge-owner-gates 获取 owner gate source identity；不复制正文、不写源项目、不生成 owner decision、不关闭 gate。"}),
        "owner_dispatch": projection["owner_dispatch"], "summary_commands": projection["summary_commands"],
        "owner_summary_commands": projection["owner_summary_commands"], "owner_forms_jsonl_commands": projection["owner_forms_jsonl_commands"],
        "owner_evidence_readiness_commands": projection["owner_evidence_readiness_commands"], "owner_validate_forms_command_templates": projection["owner_validate_forms_command_templates"],
        "owner_landing_plan_command_templates": projection["owner_landing_plan_command_templates"], "owner_landing_audit_command_templates": projection["owner_landing_audit_command_templates"],
        "forms_jsonl_commands": projection["forms_jsonl_commands"], "evidence_readiness_commands": projection["evidence_readiness_commands"],
        "validate_forms_command_templates": projection["validate_forms_command_templates"], "landing_plan_command_templates": projection["landing_plan_command_templates"],
        "landing_audit_command_templates": projection["landing_audit_command_templates"], "next_open": projection["next_owner_gate"],
        "next_open_queue": projection["next_open_queue"], "next_open_queue_count": len(projection["next_open_queue"]), "next_open_queue_selection_order": "review_after, worksheet_id",
    }


def build_status_result(s: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "root": display_path(s["root"]),
        "read_only": True,
        "strict": s["args"].strict,
        "final_profile": s["args"].final_profile,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": s["status"],
        "status_contract": s["public_status_contract"],
        "technical_readiness": {"status": "not-evaluated-by-status", "product_ready_claimed": False, "live_checks": ["knowledge-check", "source-runtime-all"], "required_authority": "knowledge-final-gate --final-profile product", "notes_zh": "本 dashboard 只声明控制面与 source runtime 状态；unit/link/Obsidian/retrieval/restore/CI 等技术就绪必须读取 product final gate。"},
        "today": s["today"].isoformat(),
        "as_of_source": s["today_source"],
        "owner_blocker_source": s["owner_blocker_source"],
        "knowledge_check": _knowledge_projection(s),
        "registry": _registry_projection(s),
        "sources": _sources_projection(s),
        "review_queues": s["review_queues"],
        "owner_gates": _owner_projection(s),
        "errors": s["errors"],
        "strict_blockers": s["strict_blockers"],
        "final_gate_command": s["final_gate_command"],
        "next_actions_zh": s["next_actions"],
    }
