#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Print a read-only owner-gate board from owner decision worksheets.")
parser.add_argument("--json", action="store_true")
parser.add_argument("--forms", action="store_true", help="Print copyable owner decision JSONL skeletons for open rows.")
parser.add_argument("--validate-forms", default="", help="Validate a filled owner decision JSONL file without applying it.")
parser.add_argument("--landing-plan", action="store_true", help="With --validate-forms, print a read-only manual landing plan for valid forms.")
parser.add_argument("--source-id", default="")
parser.add_argument("--worksheet-id", default="", help="Limit output to one owner decision worksheet id.")
parser.add_argument("--status", choices=["all", "open", "resolved"], default="open")
args = parser.parse_args(argv)

errors = []

def load_jsonl(path):
    rows = []
    if not path.exists():
        errors.append(f"missing {path.relative_to(root)}")
        return rows
    try:
        lines = path.read_text().splitlines()
    except Exception as exc:
        errors.append(f"cannot read {path.relative_to(root)}: {exc}")
        return rows
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception as exc:
            errors.append(f"{path.relative_to(root)}:{line_no}: invalid jsonl: {exc}")
    return rows

def path_from_arg(value):
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path

def _is_filled(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True

def is_resolved(row):
    state_text = " ".join(
        str(row.get(field, ""))
        for field in ["worksheet_status", "row_status", "status", "default_state"]
    ).lower()
    has_resolution_state = any(token in state_text for token in ["resolved", "owner-approved", "approved", "closed"])
    if not has_resolution_state:
        return False
    required_fields = list(row.get("required_owner_fields", []))
    for field in ["owner_decision", "target_decision", "reviewed_by", "reviewed_at", "review_after", "source_status", "evidence_refs", "status_reason"]:
        if field not in required_fields:
            required_fields.append(field)
    return all(_is_filled(row.get(field)) for field in required_fields)

def default_field_value(field, row):
    if field == "review_after":
        return row.get("review_after", "")
    if field.endswith("_refs") or field in {"evidence_refs", "open_items"}:
        return []
    if field in {"automation_enabled", "writes_memory", "writes_team_active_index", "no_memory_write_gate", "not_active_source", "contains_memory_candidates"}:
        return None
    return ""

def make_decision_form(row):
    form = {
        "worksheet_id": row["id"],
        "source_id": row["source_id"],
        "source_path": row["source_path"],
        "worksheet": row["worksheet"],
        "owner": row["owner"],
        "allowed_owner_decisions": row["decision_options"],
        "must_not": row["must_not"],
        "notes_zh": "本骨架只供 owner 人工填写和复核；脚本不写文件、不关闭门禁、不提升 active。",
    }
    for field in row["required_owner_fields"]:
        form.setdefault(field, default_field_value(field, row))
    for field in ["owner_decision", "target_decision", "reviewed_by", "reviewed_at", "review_after", "source_status", "evidence_refs", "status_reason"]:
        form.setdefault(field, default_field_value(field, row))
    return form

def is_filled(value):
    return _is_filled(value)

def validate_date(value, label, errors_out):
    try:
        parts = str(value).split("-")
        if len(parts) != 3 or any(not part.isdigit() for part in parts):
            raise ValueError("not YYYY-MM-DD")
        year, month, day = (int(part) for part in parts)
        dt.date(year, month, day)
    except Exception:
        errors_out.append(f"{label} invalid date: {value}")

def validate_forms_file(path, rows):
    form_errors = []
    warnings = []
    forms = []
    if not path.exists():
        form_errors.append(f"{path}: missing owner decision forms file")
    else:
        try:
            lines = path.read_text().splitlines()
        except Exception as exc:
            form_errors.append(f"{path}: cannot read owner decision forms file: {exc}")
            lines = []
        for line_no, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                forms.append(json.loads(line))
            except Exception as exc:
                form_errors.append(f"{path}:{line_no}: invalid jsonl: {exc}")
    if not forms:
        form_errors.append(f"{path}: no owner decision forms found")
    open_by_id = {row["id"]: row for row in rows if row["status"] == "open"}
    seen = set()
    for index, form in enumerate(forms, 1):
        prefix = f"{path}:{index}"
        worksheet_id = str(form.get("worksheet_id", ""))
        if not worksheet_id:
            form_errors.append(f"{prefix}: missing worksheet_id")
            continue
        if worksheet_id in seen:
            form_errors.append(f"{prefix}: duplicate worksheet_id {worksheet_id}")
            continue
        seen.add(worksheet_id)
        row = open_by_id.get(worksheet_id)
        if not row:
            form_errors.append(f"{prefix}: worksheet_id {worksheet_id} does not match an open owner gate row")
            continue
        if form.get("source_id") != row["source_id"]:
            form_errors.append(f"{prefix}: source_id mismatch for {worksheet_id}")
        if form.get("source_path") != row["source_path"]:
            form_errors.append(f"{prefix}: source_path mismatch for {worksheet_id}")
        owner_decision = form.get("owner_decision", "")
        if not is_filled(owner_decision):
            form_errors.append(f"{prefix}: missing owner_decision")
        elif row["decision_options"] and owner_decision not in row["decision_options"]:
            form_errors.append(
                f"{prefix}: owner_decision {owner_decision!r} is not in allowed decisions {row['decision_options']}"
            )
        for field in row["required_owner_fields"]:
            if not is_filled(form.get(field)):
                form_errors.append(f"{prefix}: missing required field {field}")
        for field in ["target_decision", "reviewed_by", "reviewed_at", "review_after", "source_status", "evidence_refs", "status_reason"]:
            if not is_filled(form.get(field)):
                form_errors.append(f"{prefix}: missing required review field {field}")
        if is_filled(form.get("reviewed_at")):
            validate_date(form.get("reviewed_at"), f"{prefix}: reviewed_at", form_errors)
        if is_filled(form.get("review_after")):
            validate_date(form.get("review_after"), f"{prefix}: review_after", form_errors)
        if "must_not" in form and form.get("must_not") != row["must_not"]:
            warnings.append(f"{prefix}: must_not differs from worksheet; verify owner did not edit guardrails")
        if "allowed_owner_decisions" in form and form.get("allowed_owner_decisions") != row["decision_options"]:
            warnings.append(f"{prefix}: allowed_owner_decisions differs from worksheet; verify owner did not edit enum")
    status = "pass" if not form_errors else "fail"
    return {
        "status": status,
        "path": str(path),
        "form_count": len(forms),
        "checked_count": len(seen),
        "forms": forms,
        "error_count": len(form_errors),
        "warning_count": len(warnings),
        "errors": form_errors,
        "warnings": warnings,
    }

def make_landing_plan(form_validation, rows):
    open_by_id = {row["id"]: row for row in rows if row["status"] == "open"}
    blocked = form_validation is None or form_validation.get("status") != "pass"
    plan = {
        "status": "blocked" if blocked else "planned",
        "read_only": True,
        "source_form": form_validation.get("path", "") if form_validation else "",
        "reason": "form validation must pass before landing plan is usable" if blocked else "",
        "steps": [],
        "required_manual_files": [
            "artifacts/manifests/<owner-decision-landing-YYYYMMDD>.jsonl",
            "registry/items.jsonl",
            "registry/migrations.jsonl",
            "indexes/by-owner.md",
            "indexes/by-review-date.md",
            "indexes/by-status.md",
            "indexes/by-topic.md",
        ],
        "verification_commands": [
            "rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics",
            "rtk bash tools/knowledge-owner-gates.sh --status all --json",
            "rtk bash tools/knowledge-status.sh --strict --json",
        ],
        "must_not": [
            "do not treat this plan as owner approval",
            "do not auto-edit registry/index/migration",
            "do not promote project-specific content to domains/embedded/standards",
            "do not write ~/.codex/memories",
            "do not modify source project docs",
        ],
    }
    if blocked:
        return plan
    for form in form_validation.get("forms", []):
        worksheet_id = form.get("worksheet_id", "")
        row = open_by_id.get(worksheet_id, {})
        plan["steps"].append(
            {
                "worksheet_id": worksheet_id,
                "source_id": form.get("source_id", ""),
                "source_path": form.get("source_path", ""),
                "owner_decision": form.get("owner_decision", ""),
                "target_decision": form.get("target_decision", ""),
                "reviewed_by": form.get("reviewed_by", ""),
                "reviewed_at": form.get("reviewed_at", ""),
                "manual_actions_zh": [
                    "把已审 owner decision 追加到 owner decision landing JSONL 制品。",
                    "按 target_decision 更新或新增对应 registry item，状态不得越过 owner 决策允许范围。",
                    "同步 registry/migrations.jsonl，记录从 owner-gated 到目标状态的人工迁移决策。",
                    "同步 by-owner、by-review-date、by-status 和 by-topic 核心索引。",
                    "运行 verification_commands 中的命令；strict gate 只有所有 owner gates 闭环后才会返回 0。",
                ],
                "guardrails": row.get("must_not", []),
            }
        )
    return plan

items = load_jsonl(root / "registry" / "items.jsonl")
items_by_source_path = {}
active_by_source_path = {}
for item in items:
    source = item.get("source") if isinstance(item.get("source"), dict) else {}
    source_id = source.get("source_id")
    source_path = source.get("source_path")
    if not source_id or not source_path:
        continue
    key = (source_id, source_path)
    item_ref = {
        "id": item.get("id", ""),
        "status": item.get("status", ""),
        "path": item.get("path", ""),
        "review_status": item.get("review_status", ""),
    }
    items_by_source_path.setdefault(key, []).append(item_ref)
    if item.get("status") == "active":
        active_by_source_path.setdefault(key, []).append(item_ref)

worksheet_paths = sorted((root / "artifacts" / "manifests").glob("*owner-decision-worksheets-*.jsonl"))
if not worksheet_paths:
    errors.append("missing artifacts/manifests/*owner-decision-worksheets-*.jsonl")

rows = []
for worksheet_path in worksheet_paths:
    for row in load_jsonl(worksheet_path):
        row_id = str(row.get("id", ""))
        if args.worksheet_id and row_id != args.worksheet_id:
            continue
        source_id = str(row.get("source_id", ""))
        source_path = str(row.get("source_path", ""))
        if args.source_id and source_id != args.source_id:
            continue
        key = (source_id, source_path)
        resolved = is_resolved(row)
        row_status = "resolved" if resolved else "open"
        if args.status != "all" and row_status != args.status:
            continue
        rows.append(
            {
                "id": row_id,
                "source_id": source_id,
                "source_path": source_path,
                "owner": row.get("owner_required") or row.get("owner_candidate") or "",
                "status": row_status,
                "worksheet_status": row.get("worksheet_status") or row.get("status") or row.get("default_state") or "",
                "decision_options": row.get("decision_options", []),
                "required_owner_fields": row.get("required_owner_fields", []),
                "must_not": row.get("must_not", []),
                "review_after": row.get("review_after", ""),
                "worksheet": str(worksheet_path.relative_to(root)),
                "registry_items": items_by_source_path.get(key, []),
                "active_registry_items": active_by_source_path.get(key, []),
            }
        )

open_count = sum(1 for row in rows if row["status"] == "open")
resolved_count = sum(1 for row in rows if row["status"] == "resolved")
active_exposure_count = sum(len(row["active_registry_items"]) for row in rows)
result_status = "blocked" if errors else "needs-fix" if active_exposure_count else "ok"
exit_status = 1 if errors or active_exposure_count else 0

result = {
    "status": result_status,
    "root": str(root),
    "read_only": True,
    "source_id": args.source_id,
    "worksheet_id": args.worksheet_id,
    "filter_status": args.status,
    "worksheet_count": len(worksheet_paths),
    "row_count": len(rows),
    "open_count": open_count,
    "resolved_count": resolved_count,
    "active_exposure_count": active_exposure_count,
    "errors": errors,
    "rows": rows,
}

if args.forms:
    result["decision_forms"] = [make_decision_form(row) for row in rows if row["status"] == "open"]

form_validation = None
if args.validate_forms:
    form_validation = validate_forms_file(path_from_arg(args.validate_forms), rows)
    result["form_validation"] = form_validation
    if form_validation["status"] != "pass":
        result_status = "needs-fix"
        result["status"] = result_status
        exit_status = 1

landing_plan = None
if args.landing_plan:
    if not args.validate_forms:
        landing_plan = {
            "status": "blocked",
            "read_only": True,
            "reason": "--landing-plan requires --validate-forms <jsonl>",
            "steps": [],
        }
        result["landing_plan"] = landing_plan
        result_status = "needs-fix"
        result["status"] = result_status
        exit_status = 1
    else:
        landing_plan = make_landing_plan(form_validation, rows)
        result["landing_plan"] = landing_plan

if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(exit_status)

print("# Knowledge Owner Gates")
print()
print("本命令只读汇总 owner decision worksheets，不创建、不修改、不提交、不提升任何文件。")
print()
print(f"- status: {result['status']}")
print(f"- worksheets: {len(worksheet_paths)}")
print(f"- rows: {len(rows)}")
print(f"- open: {open_count}")
print(f"- resolved: {resolved_count}")
print(f"- active exposure: {active_exposure_count}")
if args.source_id:
    print(f"- source_id: {args.source_id}")
print(f"- filter: {args.status}")
for error in errors:
    print(f"- ERROR: {error}")
if active_exposure_count:
    print("- ERROR: active exposure exists; run knowledge-check and keep owner-gated rows out of active until owner decisions are closed.")

if form_validation:
    print()
    print("## Owner Decision Form Validation")
    print()
    print("本校验只读检查 owner 回填 JSONL，不写文件、不关闭门禁、不提升 active。")
    print(f"- status: {form_validation['status']}")
    print(f"- forms: {form_validation['form_count']}")
    print(f"- checked: {form_validation['checked_count']}")
    print(f"- errors: {form_validation['error_count']}")
    print(f"- warnings: {form_validation['warning_count']}")
    for item in form_validation["errors"][:20]:
        print(f"- ERROR: {item}")
    for item in form_validation["warnings"][:20]:
        print(f"- WARNING: {item}")

if landing_plan:
    print()
    print("## Owner Decision Landing Plan")
    print()
    print("本计划只读输出人工落地步骤，不写文件、不关闭门禁、不提升 active。")
    print(f"- status: {landing_plan['status']}")
    if landing_plan.get("reason"):
        print(f"- reason: {landing_plan['reason']}")
    if landing_plan.get("required_manual_files"):
        print("- required_manual_files:")
        for item in landing_plan["required_manual_files"]:
            print(f"  - `{item}`")
    if landing_plan.get("verification_commands"):
        print("- verification_commands:")
        for item in landing_plan["verification_commands"]:
            print(f"  - `{item}`")
    for step in landing_plan.get("steps", []):
        print()
        print(f"### {step['worksheet_id']}")
        print(f"- source_path: `{step['source_path']}`")
        print(f"- owner_decision: `{step['owner_decision']}`")
        print(f"- target_decision: `{step['target_decision']}`")
        print("- manual_actions:")
        for action in step["manual_actions_zh"]:
            print(f"  - {action}")

if args.forms:
    print()
    print("## Owner Decision JSONL Skeletons")
    print()
    print("以下骨架只供 owner 人工复制、填写和复核；本命令不写文件、不关闭门禁、不提升 active。")
    print("写入任何 owner decision 前，必须补齐证据引用、reviewed_by、reviewed_at、source hash/size 和 status_reason。")

for row in rows:
    active_marker = "YES" if row["active_registry_items"] else "no"
    print()
    print(f"## {row['source_path'] or row['id']}")
    print()
    print(f"- id: `{row['id']}`")
    print(f"- source_id: `{row['source_id']}`")
    print(f"- owner: {row['owner'] or '<missing-owner>'}")
    print(f"- status: {row['status']} ({row['worksheet_status'] or '<missing-worksheet-status>'})")
    print(f"- review_after: {row['review_after'] or '<missing-review_after>'}")
    print(f"- active exposure: {active_marker}")
    if row["decision_options"]:
        print(f"- decision_options: {', '.join(str(item) for item in row['decision_options'])}")
    if row["required_owner_fields"]:
        print(f"- required_owner_fields: {', '.join(str(item) for item in row['required_owner_fields'][:8])}")
    if row["must_not"]:
        print(f"- must_not: {', '.join(str(item) for item in row['must_not'][:5])}")
    if row["registry_items"]:
        print("- registry_items:")
        for item in row["registry_items"]:
            print(
                f"  - `{item['id']}` status={item['status'] or '<missing-status>'} "
                f"path={item['path'] or '<missing-path>'}"
            )
    if args.forms and row["status"] == "open":
        print()
        print("```json")
        print(json.dumps(make_decision_form(row), ensure_ascii=False, sort_keys=True))
        print("```")

print()
print("## 验证")
print()
print("```bash")
print("rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics")
print("```")

sys.exit(exit_status)
PY
