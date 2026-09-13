"""Human review form validation and filtering for index-plan."""

import argparse
import collections
import datetime as dt
import json
import pathlib
import re
from typing import Counter

from .index_plan_review_queue import as_list, build_review_queue_command

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
root = pathlib.Path(".")
args = argparse.Namespace()
review_sla_date = dt.date.today()

def configure_review_forms(root_value, args_value, review_sla_date_value):
    global root, args, review_sla_date
    root = root_value
    args = args_value
    review_sla_date = review_sla_date_value

REVIEW_QUEUE_FORM_DECISIONS = {"accept-as-review-record", "needs-edits", "archive-only", "reject", "defer"}
REVIEW_QUEUE_REQUIRED_HUMAN_FIELDS = ["human_reviewed_by", "human_reviewed_at", "review_basis"]
REVIEW_QUEUE_FORBIDDEN_OWNER_FIELDS = ["owner", "owner_decision", "target_decision", "reviewed_by", "reviewed_at"]
REVIEW_QUEUE_REQUIRED_GUARDRAILS = [
    ("read_only", True),
    ("report_only", True),
    ("owner_gate_mutation", False),
    ("memory_write", False),
    ("source_project_write", False),
    ("no_registry_write", True),
    ("no_owner_decision_generated", True),
    ("no_active_promotion", True),
]
REVIEW_QUEUE_REQUIRED_MUST_NOT = [
    "不写 registry",
    "不得把本表单当 owner decision",
    "不得由 Codex 自动回填 human_reviewed_by/human_reviewed_at/review_basis",
]


def is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())

def make_queue_form_diagnostic(code, message_zh, line_no=None, queue_id="", field="", actual=None, expected=None, action_zh=""):
    diagnostic = {
        "code": code,
        "message_zh": message_zh,
        "line_no": line_no,
        "queue_id": queue_id,
        "field": field,
        "action_zh": action_zh,
    }
    if actual is not None:
        diagnostic["actual"] = actual
    if expected is not None:
        diagnostic["expected"] = expected
    return diagnostic

def resolve_input_path(raw_path):
    path = pathlib.Path(raw_path).expanduser()
    if not path.is_absolute():
        path = root / path
    return path

def validate_review_queue_forms(view, all_view):
    form_path = resolve_input_path(args.validate_queue_forms)
    rows = view.get("rows", []) if isinstance(view.get("rows", []), list) else []
    all_rows = all_view.get("rows", []) if isinstance(all_view.get("rows", []), list) else []
    current_rows_by_queue_id = {str(row.get("queue_id", "")): row for row in rows if row.get("queue_id")}
    all_queue_ids = {str(row.get("queue_id", "")) for row in all_rows if row.get("queue_id")}
    diagnostics = []
    warnings_out = []
    forms = []
    queue_id_lines = collections.defaultdict(list)

    try:
        raw_lines = form_path.read_text().splitlines()
    except Exception as exc:
        diagnostics.append(make_queue_form_diagnostic(
            "cannot-read-forms-jsonl",
            f"无法读取 review queue 表单 JSONL: {exc}",
            action_zh="确认路径存在且可读；本命令只读，不会创建或修改文件。",
        ))
        raw_lines = []

    for line_no, line in enumerate(raw_lines, start=1):
        if not line.strip():
            continue
        try:
            form = json.loads(line)
        except Exception as exc:
            diagnostics.append(make_queue_form_diagnostic(
                "invalid-jsonl",
                f"第 {line_no} 行不是合法 JSON: {exc}",
                line_no=line_no,
                action_zh="修正该行 JSON 后重新运行校验。",
            ))
            continue
        if not isinstance(form, dict):
            diagnostics.append(make_queue_form_diagnostic(
                "invalid-form-object",
                f"第 {line_no} 行不是 JSON object。",
                line_no=line_no,
                actual=type(form).__name__,
                expected="object",
                action_zh="每一行必须是一个 review queue 表单对象。",
            ))
            continue
        forms.append((line_no, form))
        queue_id_lines[str(form.get("queue_id", ""))].append(line_no)

    if not forms and not diagnostics:
        diagnostics.append(make_queue_form_diagnostic(
            "empty-forms-jsonl",
            "表单 JSONL 没有可校验的对象行。",
            action_zh="先用相同过滤条件运行 --queue-forms-jsonl 导出骨架，再由人工填写后校验。",
        ))

    duplicate_queue_ids = sorted(queue_id for queue_id, line_numbers in queue_id_lines.items() if queue_id and len(line_numbers) > 1)
    for queue_id in duplicate_queue_ids:
        diagnostics.append(make_queue_form_diagnostic(
            "duplicate-queue-id",
            f"同一个 queue_id 在表单中出现多次: {queue_id}",
            line_no=queue_id_lines[queue_id][0],
            queue_id=queue_id,
            field="queue_id",
            actual=queue_id_lines[queue_id],
            expected="unique queue_id",
            action_zh="每个待复核条目只保留一行人工填写结果。",
        ))

    accepted_queue_ids = []
    submitted_queue_ids = []
    unknown_queue_ids = []
    outside_filter_queue_ids = []
    for line_no, form in forms:
        queue_id = str(form.get("queue_id", ""))
        submitted_queue_ids.append(queue_id)
        row = current_rows_by_queue_id.get(queue_id)
        if not queue_id:
            diagnostics.append(make_queue_form_diagnostic(
                "missing-queue-id",
                "表单缺少 queue_id。",
                line_no=line_no,
                field="queue_id",
                action_zh="重新导出表单骨架，保留原始 queue_id。",
            ))
            continue
        if row is None:
            if queue_id in all_queue_ids:
                outside_filter_queue_ids.append(queue_id)
                diagnostics.append(make_queue_form_diagnostic(
                    "queue-id-outside-current-filter",
                    f"queue_id 存在于全量队列，但不在当前过滤/分页范围内: {queue_id}",
                    line_no=line_no,
                    queue_id=queue_id,
                    field="queue_id",
                    action_zh="使用导出表单时相同的 queue filter/limit/offset 重新校验，或重新导出当前批次表单。",
                ))
            else:
                unknown_queue_ids.append(queue_id)
                diagnostics.append(make_queue_form_diagnostic(
                    "unknown-queue-id",
                    f"当前 review queue 中不存在 queue_id: {queue_id}",
                    line_no=line_no,
                    queue_id=queue_id,
                    field="queue_id",
                    action_zh="确认表单来自当前 Knowledge Hub registry 派生队列；过期表单需要重新导出。",
                ))
            continue

        for field in ["form_type", "schema_version", "queue_type", "object_type", "id", "content_hash_required"]:
            expected = {
                "form_type": "review-queue-human-review",
                "schema_version": 2,
                "queue_type": row.get("queue_type", ""),
                "object_type": row.get("object_type", ""),
                "id": row.get("id", ""),
                "content_hash_required": bool(row.get("content_hash_required", False)),
            }[field]
            if form.get(field) != expected:
                diagnostics.append(make_queue_form_diagnostic(
                    "field-mismatch",
                    f"表单字段 {field} 与当前队列不一致。",
                    line_no=line_no,
                    queue_id=queue_id,
                    field=field,
                    actual=form.get(field),
                    expected=expected,
                    action_zh="不要手改表单身份字段；重新导出当前批次表单后只填写人工字段。",
                ))

        if row.get("content_hash_required"):
            expected_content_sha256 = str(row.get("content_sha256", ""))
            submitted_content_sha256 = str(form.get("content_sha256", ""))
            if not SHA256_RE.fullmatch(expected_content_sha256):
                diagnostics.append(make_queue_form_diagnostic(
                    "content-sha256-unavailable",
                    "当前 registry item 正文无法生成有效 SHA256，表单不能进入人工复核。",
                    line_no=line_no,
                    queue_id=queue_id,
                    field="content_sha256",
                    actual=expected_content_sha256,
                    expected="当前正文的 64 位小写 SHA256",
                    action_zh="修复 registry path 或缺失正文后重新导出表单。",
                ))
            elif submitted_content_sha256 != expected_content_sha256:
                diagnostics.append(make_queue_form_diagnostic(
                    "content-sha256-mismatch",
                    "表单绑定的正文 SHA256 与当前文件不一致，正文可能已漂移。",
                    line_no=line_no,
                    queue_id=queue_id,
                    field="content_sha256",
                    actual=submitted_content_sha256,
                    expected=expected_content_sha256,
                    action_zh="重新阅读当前正文并重新导出表单；不得沿用旧判断。",
                ))

        for field in REVIEW_QUEUE_REQUIRED_HUMAN_FIELDS:
            if not is_nonempty_string(form.get(field, "")):
                diagnostics.append(make_queue_form_diagnostic(
                    "missing-required-human-field",
                    f"人工字段 {field} 不能为空。",
                    line_no=line_no,
                    queue_id=queue_id,
                    field=field,
                    expected="non-empty string",
                    action_zh="由真实人工复核者填写该字段；Codex 不得代填。",
                ))

        reviewed_at = str(form.get("human_reviewed_at", ""))
        if reviewed_at:
            try:
                dt.date.fromisoformat(reviewed_at)
            except Exception:
                diagnostics.append(make_queue_form_diagnostic(
                    "invalid-human-reviewed-at",
                    "human_reviewed_at 必须是 YYYY-MM-DD 日期。",
                    line_no=line_no,
                    queue_id=queue_id,
                    field="human_reviewed_at",
                    actual=reviewed_at,
                    expected="YYYY-MM-DD",
                    action_zh="使用真实人工复核日期。",
                ))

        review_decision = str(form.get("review_decision", ""))
        if review_decision not in REVIEW_QUEUE_FORM_DECISIONS:
            diagnostics.append(make_queue_form_diagnostic(
                "invalid-review-decision",
                "review_decision 必须来自候选枚举。",
                line_no=line_no,
                queue_id=queue_id,
                field="review_decision",
                actual=review_decision,
                expected=sorted(REVIEW_QUEUE_FORM_DECISIONS),
                action_zh="选择表单 review_decision_candidates 中的一个值；不得使用 owner decision 值。",
            ))

        for field in REVIEW_QUEUE_FORBIDDEN_OWNER_FIELDS:
            if field in form:
                diagnostics.append(make_queue_form_diagnostic(
                    "forbidden-owner-field",
                    f"普通 review queue 表单不得包含 owner gate 字段 {field}。",
                    line_no=line_no,
                    queue_id=queue_id,
                    field=field,
                    action_zh="删除该字段；owner decision 只能走 knowledge-owner-gates.sh 的 owner 表单链路。",
                ))

        for field, expected in REVIEW_QUEUE_REQUIRED_GUARDRAILS:
            if form.get(field) is not expected:
                diagnostics.append(make_queue_form_diagnostic(
                    "guardrail-field-mismatch",
                    f"guardrail 字段 {field} 不符合只读边界。",
                    line_no=line_no,
                    queue_id=queue_id,
                    field=field,
                    actual=form.get(field),
                    expected=expected,
                    action_zh="重新导出表单骨架，不要手改 guardrail 字段。",
                ))

        must_not = " ".join(as_list(form.get("must_not", [])))
        for fragment in REVIEW_QUEUE_REQUIRED_MUST_NOT:
            if fragment not in must_not:
                diagnostics.append(make_queue_form_diagnostic(
                    "missing-must-not",
                    "must_not 缺少必要边界说明。",
                    line_no=line_no,
                    queue_id=queue_id,
                    field="must_not",
                    actual=must_not,
                    expected=fragment,
                    action_zh="重新导出表单骨架并保留 must_not 边界。",
                ))

        accepted_queue_ids.append(queue_id)

    error_count = len(diagnostics)
    current_queue_ids = [str(row.get("queue_id", "")) for row in rows if row.get("queue_id")]
    submitted_unique = {queue_id for queue_id in submitted_queue_ids if queue_id}
    missing_queue_ids = sorted(queue_id for queue_id in current_queue_ids if queue_id not in submitted_unique)
    if forms and missing_queue_ids:
        warnings_out.append({
            "code": "partial-coverage",
            "message_zh": "本次表单只覆盖当前过滤/分页队列的一部分；这是允许的人工分批处理状态。",
            "missing_queue_ids": missing_queue_ids,
            "action_zh": "继续按相同过滤条件导出/填写剩余队列，或确认本批只处理部分条目。",
        })

    coverage_status = (
        "empty" if not forms else
        "complete" if not missing_queue_ids and not outside_filter_queue_ids and not unknown_queue_ids else
        "partial"
    )
    validation_status = "pass" if error_count == 0 else "fail"
    return {
        "status": validation_status,
        "validation_type": "review-queue-form-validation",
        "read_only": True,
        "report_only": True,
        "no_registry_write": True,
        "no_owner_decision_generated": True,
        "no_active_promotion": True,
        "owner_gate_mutation": False,
        "memory_write": False,
        "source_project_write": False,
        "landing_supported": False,
        "form_path": str(form_path),
        "filter": view.get("filter", {}),
        "queue_row_count": len(rows),
        "submitted_count": len(forms),
        "accepted_count": len(forms) - len({line_no for item in diagnostics for line_no in [item.get("line_no")] if line_no}),
        "error_count": error_count,
        "warning_count": len(warnings_out),
        "coverage_status": coverage_status,
        "submitted_queue_ids": submitted_queue_ids,
        "duplicate_queue_ids": duplicate_queue_ids,
        "unknown_queue_ids": sorted(set(unknown_queue_ids)),
        "outside_filter_queue_ids": sorted(set(outside_filter_queue_ids)),
        "missing_queue_ids": missing_queue_ids,
        "required_submission_fields": REVIEW_QUEUE_REQUIRED_HUMAN_FIELDS + ["review_decision"],
        "required_binding_fields": ["content_sha256"],
        "review_decision_candidates": sorted(REVIEW_QUEUE_FORM_DECISIONS),
        "diagnostics": diagnostics,
        "warnings": warnings_out,
        "must_not": [
            "不写 registry",
            "不生成 owner decision",
            "不关闭 owner gate",
            "不自动回填 human review 字段",
            "不提升 active",
            "不把普通 review queue 当 final gate blocker",
        ],
        "notes_zh": "只读校验人工填写的 review queue JSONL 表单；通过只表示结构、字段和边界有效，不代表 registry 已更新或 owner gate 已关闭。",
    }

def apply_review_queue_filters(view):
    rows = [dict(row) for row in view.get("rows", [])]
    total_row_count = len(rows)
    filters = {
        "queue_type": args.queue_type or "",
        "owner": args.queue_owner or "",
        "review_after": args.queue_review_after or "",
        "priority": args.queue_priority or "",
    }
    for field, expected in filters.items():
        if expected:
            rows = [row for row in rows if str(row.get(field, "")) == expected]
    sla_counts: Counter[str] = collections.Counter()
    by_domain: Counter[str] = collections.Counter()
    for row in rows:
        review_after = str(row.get("review_after", ""))
        by_domain[str(row.get("domain", "") or "<missing-domain>")] += 1
        if not review_after:
            sla_status = "missing-date"
            days_until_review = None
        else:
            try:
                days_until_review = (dt.date.fromisoformat(review_after) - review_sla_date).days
            except ValueError:
                days_until_review = None
                sla_status = "invalid-date"
            else:
                if days_until_review < 0:
                    sla_status = "overdue"
                elif days_until_review <= 7:
                    sla_status = "due-within-7-days"
                elif days_until_review <= 30:
                    sla_status = "due-within-30-days"
                else:
                    sla_status = "future"
        row["sla_status"] = sla_status
        row["days_until_review"] = days_until_review
        sla_counts[sla_status] += 1
    matched_count = len(rows)
    offset = args.queue_offset
    limit = args.queue_limit
    shown_rows = rows[offset:] if not limit else rows[offset:offset + limit]
    next_offset = offset + len(shown_rows)
    has_next = next_offset < matched_count
    current_batch_command = build_review_queue_command(include_json=True)
    next_page_command = build_review_queue_command(include_json=True, next_offset=next_offset) if has_next else ""
    current_forms_command = build_review_queue_command(include_forms_jsonl=True)
    validate_forms_command = build_review_queue_command(include_json=True, validate_queue_forms_path="'<review-queue-forms.jsonl>'")
    sla_priority = {
        "overdue": 0,
        "missing-date": 1,
        "invalid-date": 2,
        "due-within-7-days": 3,
        "due-within-30-days": 4,
        "future": 5,
    }
    recommended_rows = sorted(
        rows,
        key=lambda row: (
            sla_priority.get(str(row.get("sla_status", "")), 9),
            str(row.get("priority", "P9")),
            str(row.get("review_after", "") or "9999-12-31"),
            str(row.get("queue_id", "")),
        ),
    )[:10]

    filtered = dict(view)
    by_type = collections.defaultdict(list)
    by_owner = collections.defaultdict(list)
    by_review_date = collections.defaultdict(list)
    for row in rows:
        row_id = str(row.get("queue_id", ""))
        by_type[str(row.get("queue_type", ""))].append(row_id)
        by_owner[str(row.get("owner", "") or "<missing-owner>")].append(row_id)
        by_review_date[str(row.get("review_after", "") or "<missing-review_after>")].append(row_id)
    filtered_summary = dict(filtered.get("summary", {}))
    filtered_summary.update({
        "total_row_count": total_row_count,
        "matched_count": matched_count,
        "shown_count": len(shown_rows),
        "offset": offset,
        "limit": limit,
        "has_next": has_next,
        "next_offset": next_offset if has_next else None,
        "next_command": next_page_command,
        "review_sla": {
            "as_of": review_sla_date.isoformat(),
            "overdue_count": sla_counts["overdue"],
            "due_within_7_days_count": sla_counts["due-within-7-days"],
            "due_within_30_days_count": sla_counts["due-within-30-days"],
            "missing_date_count": sla_counts["missing-date"],
            "invalid_date_count": sla_counts["invalid-date"],
        },
    })
    review_batch_packet = {
        "packet_type": "review-queue-batch",
        "read_only": True,
        "report_only": True,
        "filter": filters,
        "offset": offset,
        "limit": limit,
        "matched_count": matched_count,
        "shown_count": len(shown_rows),
        "row_ids": [str(row.get("queue_id", "")) for row in shown_rows],
        "recommended_batch": [
            {
                "queue_id": str(row.get("queue_id", "")),
                "owner": str(row.get("owner", "") or "<missing-owner>"),
                "domain": str(row.get("domain", "") or "<missing-domain>"),
                "review_after": str(row.get("review_after", "")),
                "sla_status": str(row.get("sla_status", "")),
            }
            for row in recommended_rows
        ],
        "required_human_fields": ["human_reviewed_by", "human_reviewed_at", "review_basis"],
        "next_commands": [
            command
            for row in shown_rows
            for command in row.get("next_commands", [])
        ],
        "recommended_batch_json": current_batch_command,
        "recommended_forms_jsonl": current_forms_command,
        "validate_queue_forms_command_template": validate_forms_command,
        "forms_jsonl_command": current_forms_command,
        "next_page_command": next_page_command,
        "must_not": [
            "不生成 owner decision",
            "不关闭 owner gate",
            "不写 memory",
            "不自动提升 active",
            "不把 review queue 当 owner gate 签收结果",
        ],
        "notes_zh": "只读人工复核批次包；用于按当前过滤和分页领取一批 AI/外部资料待复核条目。它只给诊断命令和必填人工字段，不写 registry，不回填 human_reviewed_by，不提升 active。",
    }
    filtered["summary"] = filtered_summary
    filtered["filter"] = filters
    filtered["by_type"] = {
        key: {"count": len(values)} for key, values in sorted(by_type.items())
    }
    filtered["by_owner"] = {
        key: {"count": len(values)} for key, values in sorted(by_owner.items())
    }
    filtered["by_domain"] = {
        key: {"count": value} for key, value in sorted(by_domain.items())
    }
    filtered["by_review_date"] = {
        key: {"count": len(values)}
        for key, values in sorted(by_review_date.items())
    }
    filtered["pagination"] = {
        "offset": offset,
        "limit": limit,
        "matched_count": matched_count,
        "shown_count": len(shown_rows),
        "has_next": has_next,
        "next_offset": next_offset if has_next else None,
        "next_command": next_page_command,
        "forms_jsonl_command": current_forms_command,
        "validate_queue_forms_command_template": validate_forms_command,
        "notes_zh": "只过滤 registry 派生视图；不生成人工复核结论，不回填 human_reviewed_by，不改变 registry。",
    }
    filtered["review_batch_packet"] = review_batch_packet
    filtered["rows"] = shown_rows
    return filtered

