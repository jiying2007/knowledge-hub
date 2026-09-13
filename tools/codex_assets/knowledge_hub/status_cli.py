import argparse
import json
import pathlib
import sys

from .output_contract import status_contract
from .source_coverage import select_source_coverage_closeout
from .status_common import (
    load_json,
    load_jsonl,
    parse_date,
    resolve_today,
    run_json,
    shell_command,
)
from .status_owner_projection import OWNER_READY_ROW_STATUS_SOURCE, build_owner_projection
from .status_product_audit import build_product_noncanonical_residue_audit, build_product_source_inventory_audit
from .status_projection import status_summary
from .status_result import build_status_result
from .status_review import build_review_queues

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Print a read-only Knowledge Hub status dashboard.")
output_mode = parser.add_mutually_exclusive_group()
output_mode.add_argument("--json", action="store_true")
output_mode.add_argument("--summary-json", action="store_true")
parser.add_argument("--strict", action="store_true", help="Return non-zero unless the final status is ok.")
parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD", help="Use a fixed date for review_after checks.")
parser.add_argument("--review-queue-limit", type=int, default=20, help="Maximum rows per review queue sample in JSON/text output.")
args = parser.parse_args(argv)
args.final_profile = "product"
if args.review_queue_limit < 1:
    parser.error("--review-queue-limit must be a positive integer")

today, today_source = resolve_today(args, parser)

errors = []
DISPLAY_TOOL_ROOT = "~/knowledge-hub/tools"
PRODUCT_COPY_TARGET_PREFIXES = ("projects/", "domains/", "notes/")
PRODUCT_COPY_ALLOWED_OBJECT_TYPES = {"markdown"}
REVIEW_CONTENT_BOUND_DECISIONS = {"accept-as-review-record", "archive-only", "reject"}


items = load_jsonl(root, errors, root / "registry" / "items.jsonl")
sources_payload = load_json(root, errors, root / "registry" / "sources.json")
current_sources = sources_payload.get("sources", [])
retired_sources = load_jsonl(root, errors, root / "registry" / "retired-sources.jsonl")
sources = current_sources + retired_sources


review_queues = build_review_queues(root, items, sources, today, args.final_profile, args.review_queue_limit)

knowledge_check = run_json(root, errors, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics", "--as-of", today.isoformat()])
owner_gates = run_json(root, errors, ["rtk", "bash", "tools/knowledge-owner-gates.sh", "--status", "all", "--json"])
source_runtime = run_json(root, errors, ["rtk", "bash", "tools/knowledge-source-check.sh", "--scope", "all", "--json", "--as-of", today.isoformat()])

stale_items = []
for item in items:
    review_after = parse_date(item.get("review_after", ""))
    if review_after and review_after < today and item.get("status") in {"active", "reviewing"}:
        stale_items.append({
            "id": item.get("id", ""),
            "status": item.get("status", ""),
            "review_after": item.get("review_after", ""),
            "owner": item.get("owner", ""),
        })

latest_source_coverage = ""
latest_source_coverage_selection, latest_source_coverage_path = select_source_coverage_closeout(root)
if latest_source_coverage_path:
    latest_source_coverage = str(latest_source_coverage_path.relative_to(root))

owner_payload = owner_gates["payload"]
check_payload = knowledge_check["payload"]
source_runtime_payload = source_runtime["payload"]
active_exposure_count = int(owner_payload.get("active_exposure_count", 0) or 0)
open_owner_gate_count = int(owner_payload.get("open_count", 0) or 0)
owner_ready_package_count = int(owner_payload.get("owner_ready_package_count", 0) or 0)
owner_ready_missing_count = int(owner_payload.get("owner_ready_missing_count", 0) or 0)
owner_ready_invalid_count = int(owner_payload.get("owner_ready_invalid_count", 0) or 0)
owner_ready_duplicate_count = int(owner_payload.get("owner_ready_duplicate_count", 0) or 0)
owner_ready_package_coverage = str(owner_payload.get("owner_ready_package_coverage", ""))
owner_rows = owner_payload.get("rows", [])
open_owner_rows = sorted(
    [row for row in owner_rows if row.get("status") == "open"],
    key=lambda row: (
        str(row.get("review_after", "") or "9999-12-31"),
        str(row.get("id", "")),
    ),
)
owner_ready_row_schema_errors = [
    {
        "worksheet_id": str(row.get("id", "")),
        "source_id": str(row.get("source_id", "")),
        "source_path": str(row.get("source_path", "")),
        "missing_field": "owner_ready_package_status",
        "expected_source": OWNER_READY_ROW_STATUS_SOURCE,
        "summary_zh": "open owner row 缺少 owner-ready 逐行强校验状态；status dashboard 不再从 registry_items 静默推断 covered。",
    }
    for row in open_owner_rows
    if "owner_ready_package_status" not in row
]
owner_projection = build_owner_projection(open_owner_rows)
next_owner_gate = owner_projection["next_owner_gate"]
next_open_queue = owner_projection["next_open_queue"]
owner_dispatch = owner_projection["owner_dispatch"]
summary_commands = owner_projection["summary_commands"]
owner_summary_commands = owner_projection["owner_summary_commands"]
owner_forms_jsonl_commands = owner_projection["owner_forms_jsonl_commands"]
owner_evidence_readiness_commands = owner_projection["owner_evidence_readiness_commands"]
owner_validate_forms_command_templates = owner_projection["owner_validate_forms_command_templates"]
owner_landing_plan_command_templates = owner_projection["owner_landing_plan_command_templates"]
owner_landing_audit_command_templates = owner_projection["owner_landing_audit_command_templates"]
forms_jsonl_commands = owner_projection["forms_jsonl_commands"]
evidence_readiness_commands = owner_projection["evidence_readiness_commands"]
validate_forms_command_templates = owner_projection["validate_forms_command_templates"]
landing_plan_command_templates = owner_projection["landing_plan_command_templates"]
landing_audit_command_templates = owner_projection["landing_audit_command_templates"]

product_source_inventory_audit = build_product_source_inventory_audit(root, errors, sources)

owner_gates_failed = owner_gates["exit_code"] != 0
review_queue_blocking_count = int(review_queues.get("summary", {}).get("active_or_promotion_blocker_count", 0) or 0)
review_queue_product_blocking_count = int(review_queues.get("summary", {}).get("total_pending_count", 0) or 0)
product_source_inventory_blocking_count = int(product_source_inventory_audit.get("blocker_count", 0) or 0)
product_noncanonical_residue_audit = build_product_noncanonical_residue_audit(root, items, current_sources)
product_noncanonical_blocking_count = int(product_noncanonical_residue_audit.get("blocker_count", 0) or 0)

fix_blocking = (
    knowledge_check["exit_code"] != 0
    or source_runtime["exit_code"] != 0
    or source_runtime_payload.get("status") != "pass"
    or source_runtime_payload.get("scope") != "all"
    or source_runtime_payload.get("source_check_health_executed") is not True
    or int(source_runtime_payload.get("row_count", 0) or 0)
    != int(source_runtime_payload.get("registry_source_count", 0) or 0)
    or owner_gates_failed
    or active_exposure_count
    or owner_ready_row_schema_errors
    or review_queue_blocking_count
    or product_source_inventory_blocking_count
    or product_noncanonical_blocking_count
)
owner_review_blocking = open_owner_gate_count or review_queue_product_blocking_count

if errors:
    status = "blocked"
elif fix_blocking:
    status = "needs-fix"
elif owner_review_blocking:
    status = "needs-review"
else:
    status = "pass"

public_status_contract = status_contract(status)
exit_code = (
    public_status_contract["strict_exit_code"]
    if args.strict
    else public_status_contract["default_exit_code"]
)
if today_source == "system-date":
    final_gate_command = "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product"
else:
    final_gate_command = f"rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --as-of {today.isoformat()} --json --final-profile product"
review_after_command = "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date"
source_review_after_command = "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source"
review_after_near_due_command = f"rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of {today.isoformat()} --window-days 30 --json"
source_check_report_command = f"rtk bash ~/knowledge-hub/tools/knowledge-source-check.sh --scope all --as-of {today.isoformat()} --json"
source_check_health = check_payload.get("source_check_health", {}) if isinstance(check_payload.get("source_check_health", {}), dict) else {}
source_stale_review_after_ids = set(source_check_health.get("stale_review_after_ids", []) or [])
source_check_rows = {
    str(row.get("source_id", "")): row
    for row in source_check_health.get("rows", [])
    if isinstance(row, dict)
}
source_coverage_rows = load_jsonl(root, errors, latest_source_coverage_path) if latest_source_coverage_path else []
source_coverage_by_id = {
    str(row.get("source_id", "")): row
    for row in source_coverage_rows
    if isinstance(row, dict)
}
source_recovery_rows = []
for source in sorted(sources, key=lambda row: str(row.get("id", ""))):
    source_id = str(source.get("id", ""))
    check_row = source_check_rows.get(source_id, {})
    coverage_row = source_coverage_by_id.get(source_id, {})
    source_recovery_rows.append({
        "source_id": source_id,
        "status": str(source.get("status", "")),
        "owner": str(source.get("owner", "")),
        "review_after": str(source.get("review_after", "")),
        "review_after_stale": bool(check_row.get("review_after_stale", source_id in source_stale_review_after_ids)),
        "final_disposition": str(source.get("final_disposition", "")),
        "source_strategy": str(source.get("source_strategy", "")),
        "check_contract_status": str(check_row.get("check_contract_status", "")),
        "has_check": bool(check_row.get("has_check", bool(source.get("check", "")))),
        "has_no_check_reason": bool(check_row.get("has_no_check_reason", bool(source.get("no_check_reason", "")))),
        "check": str(source.get("check", "")),
        "no_check_reason": str(source.get("no_check_reason", "")),
        "coverage_status": str(coverage_row.get("status", "")),
        "coverage_classification": str(coverage_row.get("classification", "")),
        "coverage_decision": str(coverage_row.get("decision", "")),
        "coverage_risk": str(coverage_row.get("risk", "")),
        "coverage_checked_at": str(coverage_row.get("checked_at", "")),
        "coverage_owner": str(coverage_row.get("owner", "")),
    })
stale_sources = sorted(
    [
        {
            "id": str(source.get("id", "")),
            "status": str(source.get("status", "")),
            "review_after": str(source.get("review_after", "")),
            "owner": str(source.get("owner", "")),
            "final_disposition": str(source.get("final_disposition", "")),
        }
        for source in sources
        if source.get("id") in source_stale_review_after_ids
    ],
    key=lambda row: (row["review_after"], row["id"]),
)

next_actions = []
if knowledge_check["exit_code"] != 0:
    next_actions.append("先按 knowledge-check diagnostics 的 action_zh 修复阻断错误。")
if owner_gates_failed:
    next_actions.append("先修复 knowledge-owner-gates 子命令失败；status dashboard 不能在 owner gate 工具失败时作为终态证据。")
if active_exposure_count:
    next_actions.append("立即移除 owner-gated active exposure，owner 决策闭环前不得 active。")
if open_owner_gate_count:
    next_actions.append(
        "需要确认是否只剩 owner 语义门禁时，运行最终门禁："
        f"{final_gate_command}。"
    )
    if owner_ready_missing_count or owner_ready_invalid_count or owner_ready_duplicate_count:
        next_actions.append(
            "先补齐 owner-ready package 强校验覆盖，再分派 owner 决策；"
            f"当前缺失 {owner_ready_missing_count} 条、无效 {owner_ready_invalid_count} 条、重复 {owner_ready_duplicate_count} 条。"
        )
    if summary_commands:
        next_actions.append(
            "先查看 owner gate 总览以分派全部 open gate；运行："
            f"{summary_commands[0]}。"
        )
    if owner_summary_commands:
        next_actions.append(
            "需要按责任人分派 owner gate 时，先读取 JSON 中的 `owner_gates.owner_dispatch[]`；默认先打开 owner-inbox 单屏入口，再看 owner 过滤总览，例如："
            f"{owner_dispatch[0].get('owner_inbox_json_command', '') if owner_dispatch else ''}；{owner_summary_commands[0]}。"
        )
    if owner_forms_jsonl_commands:
        next_actions.append(
            "需要按责任人导出纯 JSONL owner 表单时，运行："
            f"{owner_forms_jsonl_commands[0]}。"
        )
    if owner_evidence_readiness_commands:
        next_actions.append(
            "需要按责任人查看只读证据准备度和候选值时，运行："
            f"{owner_evidence_readiness_commands[0]}。"
        )
    if owner_validate_forms_command_templates:
        next_actions.append(
            "责任人填完 JSONL 后，按 owner 范围先只读校验："
            f"{owner_validate_forms_command_templates[0]}。"
        )
    if owner_landing_plan_command_templates:
        next_actions.append(
            "责任人表单校验通过后，按 owner 范围生成无写入 landing plan："
            f"{owner_landing_plan_command_templates[0]}。"
        )
    if owner_landing_audit_command_templates:
        next_actions.append(
            "责任人表单校验通过后，按 owner 范围审计 worksheet、registry、source policy 和 index 人工落点："
            f"{owner_landing_audit_command_templates[0]}。"
        )
    if next_owner_gate:
        next_actions.append(
            "继续处理 owner decision worksheet；下一条是 "
            f"{next_owner_gate['worksheet_id']} ({next_owner_gate['source_path']})；运行："
            f"{next_owner_gate['next_open_command']}。"
        )
        if next_owner_gate.get("next_open_forms_jsonl_command"):
            next_actions.append(
                "需要保存或交给脚本处理纯 JSONL owner 表单时，运行："
                f"{next_owner_gate['next_open_forms_jsonl_command']}。"
            )
        if next_owner_gate.get("next_open_evidence_readiness_command"):
            next_actions.append(
                "需要先查看下一条 owner gate 的证据准备度时，运行："
                f"{next_owner_gate['next_open_evidence_readiness_command']}。"
            )
        if validate_forms_command_templates:
            next_actions.append(
                "owner 填完 JSONL 后，先只读校验："
                f"{validate_forms_command_templates[0]}。"
            )
        if landing_plan_command_templates:
            next_actions.append(
                "owner 表单校验通过后，生成无写入人工 landing plan："
                f"{landing_plan_command_templates[0]}。"
            )
        if landing_audit_command_templates:
            next_actions.append(
                "owner 表单校验通过后，运行人工落点审计，确认 worksheet 不会继续 open："
                f"{landing_audit_command_templates[0]}。"
            )
    else:
        next_actions.append("继续处理 owner decision worksheet；本状态表示语义决策未闭环，不是工具失败。")
if stale_items:
    next_actions.append(
        "复核 review_after 已过期的 active/reviewing 条目；先运行："
        f"{review_after_command}。"
    )
if stale_sources:
    next_actions.append(
        "复核 review_after 已过期的 registered source；先运行："
        f"{source_review_after_command}。"
    )
if review_queues.get("summary", {}).get("total_pending_count", 0):
    next_actions.append(
        "复核 AI 生成和外部资料的人工复核队列；先运行："
        f"{review_queues.get('commands', {}).get('index_plan', '')}。"
    )
if review_queue_product_blocking_count:
    next_actions.append(
        "product 终态要求 AI/外部资料复核队列清零；这是人工复核阻断，不是工具失败。先导出表单、人工填写、校验，再用 review queue apply 工具落地。"
    )
if product_source_inventory_blocking_count:
    next_actions.append(
        "product 终态要求 source inventory 无 pending，且 copy-body 仅限 canonical Markdown 正文；先查看 `product_source_inventory_audit.blockers`。"
    )
if product_noncanonical_blocking_count:
    next_actions.append(
        "product 终态要求当前 registry、manifest、source 主列表和工具入口只包含 canonical 资产；先查看 `product_noncanonical_residue_audit.blockers`。"
    )
if not next_actions:
    next_actions.append("控制面无阻断；新增内容仍按 README 人工最短路径登记、索引和验证。")

strict_blockers = []
owner_blocker_source = {
    "status_source": "knowledge-status --strict",
    "strict_blocker_ids": ["owner-gates-open"] if open_owner_gate_count else [],
    "owner_gate_open_count_field": "owner_gates.open_count",
    "owner_ready_package_coverage_field": "owner_gates.owner_ready_package_coverage",
    "active_exposure_count_field": "owner_gates.active_exposure_count",
    "open_count": open_owner_gate_count,
    "owner_ready_package_coverage": owner_ready_package_coverage,
    "active_exposure_count": active_exposure_count,
    "owner_ready_row_status_source": OWNER_READY_ROW_STATUS_SOURCE,
    "owner_ready_row_schema_error_count": len(owner_ready_row_schema_errors),
    "notes_zh": "owner gate 数量、owner-ready 覆盖和 active exposure 均来自本 status 输出的 owner_gates；next_open_queue 的逐行 owner-ready 状态只消费 knowledge-owner-gates 的强校验字段，不从 registry_items 推断 covered；本结构只解释 blocker 来源，不生成 owner decision，不关闭 gate。",
}
if errors:
    strict_blockers.append({
        "id": "status-dashboard-errors",
        "severity": "blocker",
        "count": len(errors),
        "summary_zh": "status dashboard 自身读取或解析失败，不能作为终态证据。",
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json"],
    })
if source_runtime["exit_code"] != 0 or source_runtime_payload.get("status") != "pass":
    strict_blockers.append({
        "id": "source-runtime-check-failed",
        "severity": "blocker",
        "count": int(source_runtime_payload.get("failed_count", 0) or 0),
        "summary_zh": "全部登记 source 的只读 runtime availability check 未通过，status 不得声明控制面 ready。",
        "commands": [source_check_report_command],
        "exit_code": source_runtime["exit_code"],
        "parse_error": source_runtime.get("parse_error", ""),
    })
if knowledge_check["exit_code"] != 0:
    strict_blockers.append({
        "id": "knowledge-check-failed",
        "severity": "blocker",
        "count": len(check_payload.get("errors", [])),
        "summary_zh": "knowledge-check 存在阻断错误，必须先按 diagnostics 修复。",
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"],
    })
if owner_gates_failed:
    strict_blockers.append({
        "id": "owner-gates-command-failed",
        "severity": "blocker",
        "count": 1,
        "summary_zh": "knowledge-owner-gates 子命令返回非零，不能把 owner gate 状态当作可信终态证据。",
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json"],
        "command": shell_command(owner_gates["command"]),
        "exit_code": owner_gates["exit_code"],
        "stderr_sample": owner_gates["stderr"][:1000],
        "parse_error": owner_gates.get("parse_error", ""),
    })
if active_exposure_count:
    strict_blockers.append({
        "id": "owner-gated-active-exposure",
        "severity": "blocker",
        "count": active_exposure_count,
        "summary_zh": "存在 unresolved owner-gated 内容暴露为 active，必须先移除 active exposure。",
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json"],
    })
if owner_ready_row_schema_errors:
    strict_blockers.append({
        "id": "owner-ready-row-schema-missing",
        "severity": "blocker",
        "count": len(owner_ready_row_schema_errors),
        "summary_zh": "owner-gates open rows 缺少逐行 owner-ready 强校验字段；不能用 registry_items presence 代替 covered。",
        "errors": owner_ready_row_schema_errors,
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json"],
    })
if review_queue_blocking_count:
    strict_blockers.append({
        "id": "review-queue-active-or-promotion-without-human-review",
        "severity": "blocker",
        "count": review_queue_blocking_count,
        "summary_zh": "存在 active 或 promotion 类条目缺少人工复核闭环；必须先补 human_reviewed_by/human_reviewed_at/review_basis，或降级为 reviewing/report-only。",
        "commands": [review_queues.get("commands", {}).get("index_plan", "")],
    })
if review_queue_product_blocking_count:
    strict_blockers.append({
        "id": "review-queue-pending-product",
        "severity": "owner-review",
        "count": review_queue_product_blocking_count,
        "summary_zh": "product 终态要求 AI/外部资料人工复核队列清零；普通待复核项属于 owner-review 阻断，不能由工具代签或自动清零。",
        "commands": [
            review_queues.get("commands", {}).get("recommended_batch_json", ""),
            review_queues.get("commands", {}).get("recommended_forms_jsonl", ""),
            review_queues.get("commands", {}).get("recommended_validate_queue_forms", ""),
            "rtk bash ~/knowledge-hub/tools/knowledge-review-queue-apply.sh --forms '<review-queue-forms.jsonl>' --dry-run",
        ],
    })
if product_source_inventory_blocking_count:
    strict_blockers.append({
        "id": "source-inventory-product-blockers",
        "severity": "blocker",
        "count": product_source_inventory_blocking_count,
        "summary_zh": "product source inventory 仍有 pending、非法 copy-body 或缺失 canonical target。",
        "blockers": product_source_inventory_audit.get("blockers", []),
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json"],
    })
if product_noncanonical_blocking_count:
    strict_blockers.append({
        "id": "product-noncanonical-residue-blockers",
        "severity": "blocker",
        "count": product_noncanonical_blocking_count,
        "summary_zh": "product 运行模型仍发现非规范 registry、manifest、source 或工具入口残留。",
        "blockers": product_noncanonical_residue_audit.get("blockers", []),
        "commands": ["rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json"],
    })
if open_owner_gate_count:
    owner_commands = list(summary_commands)
    owner_commands.extend(owner_summary_commands)
    owner_commands.extend(owner_forms_jsonl_commands)
    owner_commands.extend(owner_evidence_readiness_commands)
    if next_owner_gate.get("next_open_command"):
        owner_commands.append(next_owner_gate["next_open_command"])
    if next_owner_gate.get("next_open_forms_jsonl_command"):
        owner_commands.append(next_owner_gate["next_open_forms_jsonl_command"])
    if next_owner_gate.get("next_open_evidence_readiness_command"):
        owner_commands.append(next_owner_gate["next_open_evidence_readiness_command"])
    owner_command_templates = []
    owner_command_templates.extend(owner_validate_forms_command_templates)
    owner_command_templates.extend(owner_landing_plan_command_templates)
    owner_command_templates.extend(owner_landing_audit_command_templates)
    owner_command_templates.extend(validate_forms_command_templates)
    owner_command_templates.extend(landing_plan_command_templates)
    owner_command_templates.extend(landing_audit_command_templates)
    strict_blockers.append({
        "id": "owner-gates-open",
        "severity": "owner-review",
        "count": open_owner_gate_count,
        "summary_zh": "仍有 owner decision worksheet 未签收；这是语义门禁，不是工具失败。",
        "owner_blocker_source": owner_blocker_source,
        "commands": owner_commands,
        "command_templates": owner_command_templates,
    })

owner_review_strict_blocker_ids = [
    str(blocker.get("id", ""))
    for blocker in strict_blockers
    if isinstance(blocker, dict)
    and blocker.get("severity") == "owner-review"
    and blocker.get("id")
]
owner_blocker_source["strict_blocker_ids"] = owner_review_strict_blocker_ids
owner_blocker_source["review_queue_pending_count_field"] = "review_queues.summary.total_pending_count"
owner_blocker_source["review_queue_blocking_final_gate_field"] = "review_queues.blocking_final_gate"
owner_blocker_source["review_queue_profile_field"] = "review_queues.final_profile"
owner_blocker_source["notes_zh"] = "owner-review blocker 来源于本 status 输出的 owner_gates 与 review_queues；owner gate 数量、owner-ready 覆盖和 active exposure 来自 owner_gates，review queue 按唯一 product 终态语义判定。本结构只解释 blocker 来源，不生成 owner decision，不关闭 gate，不代签人工复核。"

status_state = {
    "root": root, "args": args, "status": status, "public_status_contract": public_status_contract,
    "today": today, "today_source": today_source, "owner_blocker_source": owner_blocker_source,
    "knowledge_check": knowledge_check, "check_payload": check_payload, "items": items, "stale_items": stale_items,
    "review_after_command": review_after_command, "review_after_near_due_command": review_after_near_due_command,
    "sources": sources, "latest_source_coverage": latest_source_coverage, "latest_source_coverage_selection": latest_source_coverage_selection,
    "source_check_health": source_check_health, "source_runtime": source_runtime, "source_runtime_payload": source_runtime_payload,
    "source_recovery_rows": source_recovery_rows, "stale_sources": stale_sources, "source_review_after_command": source_review_after_command,
    "source_check_report_command": source_check_report_command, "product_source_inventory_audit": product_source_inventory_audit,
    "product_noncanonical_residue_audit": product_noncanonical_residue_audit, "review_queues": review_queues,
    "owner_payload": owner_payload, "owner_projection": owner_projection, "owner_gates": owner_gates,
    "open_owner_gate_count": open_owner_gate_count, "active_exposure_count": active_exposure_count,
    "owner_ready_package_count": owner_ready_package_count, "owner_ready_missing_count": owner_ready_missing_count,
    "owner_ready_invalid_count": owner_ready_invalid_count, "owner_ready_duplicate_count": owner_ready_duplicate_count,
    "owner_ready_package_coverage": owner_ready_package_coverage, "owner_ready_row_schema_errors": owner_ready_row_schema_errors,
    "errors": errors, "strict_blockers": strict_blockers, "final_gate_command": final_gate_command, "next_actions": next_actions,
}
result = build_status_result(status_state)

if args.json or args.summary_json:
    projection = status_summary(result) if args.summary_json else result
    print(json.dumps(projection, ensure_ascii=False, indent=2))
    sys.exit(exit_code)

print("# Knowledge Hub Status")
print()
print("本命令只读汇总 Knowledge Hub 当前控制面状态，不创建、不修改、不提交、不提升任何文件。")
print()
print(f"- status: {status}")
print(f"- strict: {str(args.strict).lower()}")
print(f"- final_profile: {args.final_profile}")
print(f"- today: {today.isoformat()}")
print(f"- knowledge-check: {result['knowledge_check']['status']} (exit={knowledge_check['exit_code']}, errors={result['knowledge_check']['error_count']}, warnings={result['knowledge_check']['warning_count']})")
print(f"- registry items: {len(items)}")
print(f"- registered sources: {len(sources)}")
print(f"- source runtime: {source_runtime_payload.get('status', '<missing>')} executed={source_runtime_payload.get('executed_count', 0)}/{source_runtime_payload.get('registry_source_count', 0)}")
print(f"- review queues: pending={review_queues['summary']['total_pending_count']}, ai={review_queues['summary']['ai_generated_pending_count']}, external={review_queues['summary']['external_source_pending_count']}, active_or_promotion={review_queue_blocking_count}, product_blocking={review_queue_product_blocking_count}")
print(f"- product source inventory: {product_source_inventory_audit['status']} blockers={product_source_inventory_audit['blocker_count']}")
print(f"- owner gates: open={open_owner_gate_count}, resolved={owner_payload.get('resolved_count', 0)}, active_exposure={active_exposure_count}")
print(
    f"- owner-ready packages: {owner_ready_package_coverage or str(owner_ready_package_count) + '/' + str(owner_payload.get('row_count', 0))}, "
    f"missing={owner_ready_missing_count}, invalid={owner_ready_invalid_count}, duplicate={owner_ready_duplicate_count}"
)
if latest_source_coverage:
    print(f"- source coverage: `{latest_source_coverage}`")
print()
print("## Registry")
print()
for key, value in result["registry"]["by_status"].items():
    print(f"- status `{key}`: {value}")
print(f"- stale review_after: {len(stale_items)}")
print(f"- review_after command: `{review_after_command}`")
print(f"- review_after near-due command: `{review_after_near_due_command}`")
if stale_items:
    for item in stale_items[:10]:
        print(f"  - `{item['id']}` status={item['status']} review_after={item['review_after']} owner={item['owner']}")
print()
print("## Sources")
print()
print(f"- stale source review_after: {len(stale_sources)}")
print(f"- source review_after command: `{source_review_after_command}`")
print(f"- source check report command: `{source_check_report_command}`")
if stale_sources:
    for source in stale_sources[:10]:
        print(
            f"  - `{source['id']}` status={source['status']} "
            f"review_after={source['review_after']} owner={source['owner']}"
        )
print()
print("## Review Queues")
print()
print(f"- status: {review_queues['status']}")
print(f"- pending: {review_queues['summary']['total_pending_count']}")
print(f"- ai generated pending: {review_queues['summary']['ai_generated_pending_count']}")
print(f"- external source pending: {review_queues['summary']['external_source_pending_count']}")
print(f"- active or promotion blockers: {review_queue_blocking_count}")
print(f"- index plan command: `{review_queues['commands']['index_plan']}`")
for row in review_queues.get("ai_generated_pending", [])[:5]:
    print(f"- ai: `{row['id']}` priority={row['priority']} owner={row['owner']} review_after={row['review_after']}")
for row in review_queues.get("external_source_pending", [])[:5]:
    print(f"- external: `{row['id']}` priority={row['priority']} owner={row['owner']} review_after={row['review_after']}")
print()
print("## Owner Gates")
print()
print(f"- worksheets: {result['owner_gates']['worksheet_count']}")
print(f"- rows: {result['owner_gates']['row_count']}")
print(f"- open: {open_owner_gate_count}")
print(f"- resolved: {owner_payload.get('resolved_count', 0)}")
print(f"- active exposure: {active_exposure_count}")
print(f"- owner-ready packages: {owner_ready_package_coverage or str(owner_ready_package_count) + '/' + str(result['owner_gates']['row_count'])}")
print(f"- owner-ready missing: {owner_ready_missing_count}")
print(f"- owner-ready invalid: {owner_ready_invalid_count}")
print(f"- owner-ready duplicate: {owner_ready_duplicate_count}")
if summary_commands:
    print("- summary commands:")
    for command in summary_commands:
        print(f"  - `{command}`")
if owner_summary_commands:
    print("- owner summary commands:")
    for command in owner_summary_commands:
        print(f"  - `{command}`")
if forms_jsonl_commands:
    print("- forms-jsonl commands:")
    for command in forms_jsonl_commands:
        print(f"  - `{command}`")
if owner_forms_jsonl_commands:
    print("- owner forms-jsonl commands:")
    for command in owner_forms_jsonl_commands:
        print(f"  - `{command}`")
if owner_validate_forms_command_templates:
    print("- owner validate-forms command templates:")
    for command in owner_validate_forms_command_templates:
        print(f"  - `{command}`")
if owner_landing_plan_command_templates:
    print("- owner landing plan command templates:")
    for command in owner_landing_plan_command_templates:
        print(f"  - `{command}`")
if owner_landing_audit_command_templates:
    print("- owner landing audit command templates:")
    for command in owner_landing_audit_command_templates:
        print(f"  - `{command}`")
if validate_forms_command_templates:
    print("- validate-forms command templates:")
    for command in validate_forms_command_templates:
        print(f"  - `{command}`")
if landing_plan_command_templates:
    print("- landing plan command templates:")
    for command in landing_plan_command_templates:
        print(f"  - `{command}`")
if landing_audit_command_templates:
    print("- landing audit command templates:")
    for command in landing_audit_command_templates:
        print(f"  - `{command}`")
if next_owner_gate:
    print(f"- next open: `{next_owner_gate['worksheet_id']}` ({next_owner_gate['source_path']})")
    print(f"- next-open command: `{next_owner_gate['next_open_command']}`")
    print(f"- next-open forms-jsonl command: `{next_owner_gate['next_open_forms_jsonl_command']}`")
    print(f"- focus command: `{next_owner_gate['focus_command']}`")
    print(f"- focus forms-jsonl command: `{next_owner_gate['focus_forms_jsonl_command']}`")
    print(f"- focus validate-forms command template: `{next_owner_gate['focus_validate_forms_command_template']}`")
    print(f"- focus landing-plan command template: `{next_owner_gate['focus_landing_plan_command_template']}`")
    print(f"- focus landing-audit command template: `{next_owner_gate['focus_landing_audit_command_template']}`")
if next_open_queue:
    print(f"- next open queue: {len(next_open_queue)} item(s), order=`review_after, worksheet_id`")
    for row in next_open_queue:
        print(f"  - `{row['worksheet_id']}` ({row['source_path']}) owner=`{row['owner']}` ready=`{row['owner_ready_package_status']}`")
        print(f"    - focus: `{row['focus_command']}`")
        print(f"    - forms-jsonl: `{row['forms_jsonl_command']}`")
        print(f"    - evidence-readiness: `{row['evidence_readiness_command']}`")
print()
if strict_blockers:
    print("## Strict Blockers")
    print()
    for blocker in strict_blockers:
        print(f"- `{blocker['id']}` ({blocker['severity']}): {blocker['summary_zh']} count={blocker['count']}")
        for command in blocker.get("commands", []):
            print(f"  - `{command}`")
        for command in blocker.get("command_templates", []):
            print(f"  - template: `{command}`")
    print()
print("## 下一步")
print()
for action in next_actions:
    print(f"- {action}")
print(f"- 最终门禁命令：{final_gate_command}")
if errors:
    print()
    print("## Errors")
    print()
    for error in errors:
        print(f"- {error}")
print()
print("## 复核命令")
print()
print("```bash")
print("rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics")
print("rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json")
print("rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict")
print(final_gate_command)
print("```")

sys.exit(exit_code)
