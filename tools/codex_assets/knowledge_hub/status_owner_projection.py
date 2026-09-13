import json
from collections import defaultdict
from typing import Any, Dict, List, Sequence, Tuple

from .status_common import display_tool, shell_command

OWNER_READY_ROW_STATUS_SOURCE = "knowledge-owner-gates.rows[].owner_ready_package_status"


def safe_slug(value: Any) -> str:
    chars = [char if char.isalnum() or char in {"-", "_"} else "-" for char in str(value).strip().lower()]
    slug = "".join(chars).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "owner"


def _base(source_id: str, owner: str = "", worksheet_id: str = "") -> List[str]:
    parts = ["rtk", "bash", display_tool("knowledge-owner-gates.sh"), "--source-id", source_id]
    if owner:
        parts.extend(["--owner", owner])
    if worksheet_id:
        parts.extend(["--worksheet-id", worksheet_id])
    return parts


def _command(source_id: str, owner: str = "", worksheet_id: str = "", suffix: Sequence[str] = ()) -> str:
    return shell_command(_base(source_id, owner, worksheet_id) + list(suffix)) if source_id else ""


def make_status_owner_handoff_packet(owner: str, source_id: str, owner_rows: Sequence[Dict[str, Any]], next_owner_row: Dict[str, Any]) -> Dict[str, Any]:
    local_path = "artifacts/manifests/{}-{}-owner-decisions-YYYYMMDD.local.jsonl".format(source_id, safe_slug(owner)) if source_id else "artifacts/manifests/<source-id>-<owner>-owner-decisions-YYYYMMDD.local.jsonl"
    required_fields: List[str] = []
    must_not: List[str] = []
    for row in owner_rows:
        for field in row.get("required_owner_fields", []):
            if field not in required_fields:
                required_fields.append(field)
        for rule in row.get("must_not", []):
            if rule not in must_not:
                must_not.append(rule)
    fixed_rules = ["不得把 routing_owner 当 reviewed_by", "不得由工具或 AI 代签 owner decision", "不得关闭未签收 owner gate", "不得把 owner-ready package 当作已批准决策"]
    return {
        "status": "ready-for-owner-review" if owner_rows else "empty", "read_only": True,
        "source_identity_read_policy": {"source_identity_read_mode": "read-bytes-for-hash", "source_body_read_for_hash": True, "source_body_copied": False, "source_project_written": False, "owner_gate_mutation": False, "notes_zh": "status 通过 knowledge-owner-gates 读取 source identity；为计算 hash 会只读读取 source 文件字节，但不复制正文、不写源项目、不生成 owner decision、不关闭 gate。"},
        "owner": owner, "source_id": source_id, "open_count": len(owner_rows), "worksheet_ids": [str(row.get("id", "")) for row in owner_rows],
        "next_worksheet_id": str(next_owner_row.get("id", "")) if next_owner_row else "", "suggested_local_owner_decisions_path": local_path,
        "manual_owner_fields": required_fields,
        "recommended_sequence": [
            {"step": "1-open-owner-inbox", "command": _command(source_id, owner, suffix=["--owner-inbox", "--json"]), "notes_zh": "单屏查看 owner 问题、字段分组、候选证据和后续命令；不生成 owner decision。"},
            {"step": "2-review-summary", "command": _command(source_id, owner, suffix=["--summary"]), "notes_zh": "确认 owner 角色、open worksheet、source path 和 owner_route；这一步不生成 owner decision。"},
            {"step": "3-check-evidence-readiness", "command": _command(source_id, owner, suffix=["--evidence-readiness", "--json"]), "notes_zh": "只读查看 source identity、owner-ready evidence ref 候选和仍需人工回答的字段；source identity 为 hash 会读取 source 字节但不复制正文。"},
            {"step": "4-export-forms", "command": _command(source_id, owner, suffix=["--forms-jsonl"]), "output_path_hint": local_path, "notes_zh": "导出表单骨架到 stdout；owner 可另存为 .local.jsonl 后手工填写，工具不写该文件。"},
            {"step": "5-validate-filled-forms", "command_template": _command(source_id, owner, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--json"]), "replace_placeholder_with": local_path, "notes_zh": "只读校验 owner 填写结果；不通过时不得进入 landing plan。"},
            {"step": "6-plan-manual-landing", "command_template": _command(source_id, owner, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-plan", "--json"]), "replace_placeholder_with": local_path, "notes_zh": "生成 no-write 人工落地计划；仍不写 registry、worksheet、migration 或 index。"},
            {"step": "7-audit-manual-landing", "command_template": _command(source_id, owner, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-audit", "--json"]), "replace_placeholder_with": local_path, "notes_zh": "人工落地后复核 worksheet、registry、source policy 和 index 是否同步；不能把 audit 当 owner approval。"},
        ],
        "must_not": fixed_rules + [rule for rule in must_not if rule not in set(fixed_rules)],
        "notes_zh": "只读 owner handoff 包；用于跨会话恢复人工领取顺序，不生成、不保存、不应用 owner decision。",
    }


def make_next_open_queue_entry(row: Dict[str, Any]) -> Dict[str, Any]:
    source_id = str(row.get("source_id", ""))
    worksheet_id = str(row.get("id", ""))
    packages = row.get("owner_ready_packages", []) if isinstance(row.get("owner_ready_packages", []), list) else []
    package_ids = [str(item.get("id", "")) for item in packages if isinstance(item, dict) and item.get("id")]
    package_status = str(row.get("owner_ready_package_status", "")) or "unknown-owner-ready-status"
    return {
        "worksheet_id": worksheet_id, "source_id": source_id, "source_path": str(row.get("source_path", "")), "owner": str(row.get("owner", "")),
        "owner_route": row.get("owner_route", {}), "review_after": str(row.get("review_after", "")), "owner_question_zh": str(row.get("owner_question_zh", "")),
        "owner_ready_package_status": package_status, "owner_ready_package_status_source": str(row.get("owner_ready_package_status_source", OWNER_READY_ROW_STATUS_SOURCE)),
        "owner_ready_source": OWNER_READY_ROW_STATUS_SOURCE, "owner_ready_package_ids": package_ids,
        "owner_ready_package_count": int(row.get("owner_ready_package_count", len(package_ids)) or 0), "selection_order": "review_after, worksheet_id",
        "focus_command": _command(source_id, worksheet_id=worksheet_id, suffix=["--checklist", "--forms"]),
        "forms_jsonl_command": _command(source_id, worksheet_id=worksheet_id, suffix=["--forms-jsonl"]),
        "evidence_readiness_command": _command(source_id, worksheet_id=worksheet_id, suffix=["--evidence-readiness", "--json"]),
        "validate_forms_command_template": _command(source_id, worksheet_id=worksheet_id, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--json"]),
        "landing_plan_command_template": _command(source_id, worksheet_id=worksheet_id, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-plan", "--json"]),
        "landing_audit_command_template": _command(source_id, worksheet_id=worksheet_id, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-audit", "--json"]),
        "notes_zh": "只读下一批 owner gate 恢复队列；按 review_after 和 worksheet_id 排序，不生成 owner decision，不关闭 gate。",
    }


def _unique_routes(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    routes: List[Dict[str, Any]] = []
    seen = set()
    for row in rows:
        route = row.get("owner_route", {})
        if not route:
            continue
        key = json.dumps(route, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            seen.add(key)
            routes.append(route)
    return routes


def _dispatch_row(source_id: str, owner: str, rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    next_row = sorted(rows, key=lambda row: (str(row.get("review_after", "") or "9999-12-31"), str(row.get("id", ""))))[0]
    routes = _unique_routes(rows)
    return {
        "owner": owner, "source_id": source_id, "source_ids": [source_id] if source_id else [], "dispatch_scope_id": "{}:{}".format(source_id or "<missing-source>", owner),
        "mixed_source_owner": False, "owner_route": routes[0] if len(routes) == 1 else {}, "owner_routes": routes, "row_count": len(rows), "open_count": len(rows),
        "worksheet_ids": [str(row.get("id", "")) for row in rows], "source_paths": [str(row.get("source_path", "")) for row in rows],
        "owner_inbox_json_command": _command(source_id, owner, suffix=["--owner-inbox", "--json"]), "summary_command": _command(source_id, owner, suffix=["--summary"]),
        "forms_jsonl_command": _command(source_id, owner, suffix=["--forms-jsonl"]), "evidence_readiness_command": _command(source_id, owner, suffix=["--evidence-readiness", "--json"]),
        "handoff_packet_json_command": _command(source_id, owner, suffix=["--handoff-packet", "--json"]),
        "validate_forms_command_template": _command(source_id, owner, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--json"]),
        "landing_plan_command_template": _command(source_id, owner, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-plan", "--json"]),
        "landing_audit_command_template": _command(source_id, owner, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-audit", "--json"]),
        "next_focus_command": _command(str(next_row.get("source_id", "")), owner, str(next_row.get("id", "")), ["--checklist", "--forms"]),
        "suggested_owner_packet": make_status_owner_handoff_packet(owner, source_id, rows, next_row),
        "notes_zh": "status dashboard 只读 owner 分派摘要；按 source_id + owner 分派，避免同一 owner 跨 source 时丢失 source scope。用于跨会话恢复 owner 领取、表单导出、校验和 landing-plan 入口，不生成 owner decision，不关闭 gate。",
    }


def _scope_command_sets(open_rows: Sequence[Dict[str, Any]]) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {name: [] for name in ["summary_commands", "owner_summary_commands", "owner_forms_jsonl_commands", "owner_evidence_readiness_commands", "owner_validate_forms_command_templates", "owner_landing_plan_command_templates", "owner_landing_audit_command_templates", "forms_jsonl_commands", "evidence_readiness_commands", "validate_forms_command_templates", "landing_plan_command_templates", "landing_audit_command_templates"]}
    source_ids = sorted({str(row.get("source_id", "")) for row in open_rows if row.get("source_id")})
    owner_scopes = sorted({(str(row.get("source_id", "")), str(row.get("owner", ""))) for row in open_rows if row.get("source_id") and row.get("owner")})
    for source_id in source_ids:
        result["summary_commands"].append(_command(source_id, suffix=["--summary"]))
        result["forms_jsonl_commands"].append(_command(source_id, suffix=["--forms-jsonl"]))
        result["evidence_readiness_commands"].append(_command(source_id, suffix=["--evidence-readiness", "--json"]))
        result["validate_forms_command_templates"].append(_command(source_id, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--json"]))
        result["landing_plan_command_templates"].append(_command(source_id, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-plan", "--json"]))
        result["landing_audit_command_templates"].append(_command(source_id, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-audit", "--json"]))
    for source_id, owner in owner_scopes:
        result["owner_summary_commands"].append(_command(source_id, owner, suffix=["--summary"]))
        result["owner_forms_jsonl_commands"].append(_command(source_id, owner, suffix=["--forms-jsonl"]))
        result["owner_evidence_readiness_commands"].append(_command(source_id, owner, suffix=["--evidence-readiness", "--json"]))
        result["owner_validate_forms_command_templates"].append(_command(source_id, owner, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--json"]))
        result["owner_landing_plan_command_templates"].append(_command(source_id, owner, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-plan", "--json"]))
        result["owner_landing_audit_command_templates"].append(_command(source_id, owner, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-audit", "--json"]))
    return result


def _next_owner_gate(first: Dict[str, Any]) -> Dict[str, Any]:
    source_id = str(first.get("source_id", ""))
    worksheet_id = str(first.get("id", ""))
    return {
        "worksheet_id": worksheet_id, "source_id": source_id, "source_path": first.get("source_path", ""), "owner": first.get("owner", ""),
        "owner_route": first.get("owner_route", {}), "review_after": first.get("review_after", ""), "selection_order": "review_after, worksheet_id",
        "next_open_command": _command(source_id, suffix=["--next-open", "--checklist", "--forms"]),
        "next_open_forms_jsonl_command": _command(source_id, suffix=["--next-open", "--forms-jsonl"]),
        "next_open_evidence_readiness_command": _command(source_id, suffix=["--next-open", "--evidence-readiness", "--json"]),
        "focus_command": _command(source_id, worksheet_id=worksheet_id, suffix=["--checklist", "--forms"]),
        "focus_forms_jsonl_command": _command(source_id, worksheet_id=worksheet_id, suffix=["--forms-jsonl"]),
        "focus_evidence_readiness_command": _command(source_id, worksheet_id=worksheet_id, suffix=["--evidence-readiness", "--json"]),
        "focus_validate_forms_command_template": _command(source_id, worksheet_id=worksheet_id, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--json"]),
        "focus_landing_plan_command_template": _command(source_id, worksheet_id=worksheet_id, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-plan", "--json"]),
        "focus_landing_audit_command_template": _command(source_id, worksheet_id=worksheet_id, suffix=["--validate-forms", "<owner-decisions.jsonl>", "--landing-audit", "--json"]),
    }


def build_owner_projection(open_rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    empty: Dict[str, Any] = {"next_owner_gate": {}, "next_open_queue": [], "owner_dispatch": []}
    empty.update({name: [] for name in ["summary_commands", "owner_summary_commands", "owner_forms_jsonl_commands", "owner_evidence_readiness_commands", "owner_validate_forms_command_templates", "owner_landing_plan_command_templates", "owner_landing_audit_command_templates", "forms_jsonl_commands", "evidence_readiness_commands", "validate_forms_command_templates", "landing_plan_command_templates", "landing_audit_command_templates"]})
    if not open_rows:
        return empty
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in open_rows:
        grouped[(str(row.get("source_id", "") or ""), str(row.get("owner", "") or "<missing-owner>"))].append(row)
    empty["next_open_queue"] = [make_next_open_queue_entry(row) for row in open_rows]
    empty["owner_dispatch"] = [_dispatch_row(source_id, owner, rows) for (source_id, owner), rows in sorted(grouped.items())]
    empty.update(_scope_command_sets(open_rows))
    empty["next_owner_gate"] = _next_owner_gate(open_rows[0])
    return empty
