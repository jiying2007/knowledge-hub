import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys

from .common import bytes_sha256, file_sha256, load_markdown, render_markdown
from .model import merge_frontmatter_mirror
from .store import RepositoryTransaction

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(prog="knowledge-review-queue-apply.sh", description="Apply filled review queue forms to registry/items.jsonl after strict validation.")
parser.add_argument("--forms", required=True, metavar="JSONL", help="Filled review queue JSONL forms.")
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument("--dry-run", action="store_true", help="Validate and print the planned registry updates without writing.")
mode.add_argument("--apply", action="store_true", help="Apply validated registry updates.")
parser.add_argument("--json", action="store_true")
args = parser.parse_args(argv)

items_path = root / "registry" / "items.jsonl"
forms_path = pathlib.Path(args.forms).expanduser()
if not forms_path.is_absolute():
    forms_path = root / forms_path

REQUIRED_HUMAN_FIELDS = ["human_reviewed_by", "human_reviewed_at", "review_basis"]
EXTERNAL_REVIEW_FIELDS = ["retrieved_at", "read_status", "source_license"]
VALID_REVIEW_DECISIONS = {"accept-as-review-record", "needs-edits", "archive-only", "reject", "defer"}
REVIEW_CONTENT_BOUND_DECISIONS = {"accept-as-review-record", "archive-only", "reject"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_FIELDS = {
    "owner",
    "owner_decision",
    "target_decision",
    "reviewed_by",
    "reviewed_at",
}
REQUIRED_GUARDRAILS = {
    "read_only": True,
    "report_only": True,
    "owner_gate_mutation": False,
    "memory_write": False,
    "source_project_write": False,
    "no_registry_write": True,
    "no_owner_decision_generated": True,
    "no_active_promotion": True,
}

def load_items():
    rows = []
    for line_no, line in enumerate(items_path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except Exception as exc:
            raise SystemExit(f"registry/items.jsonl:{line_no}: invalid JSON: {exc}") from exc
        rows.append(item)
    return rows

def load_forms():
    forms = []
    try:
        lines = forms_path.read_text().splitlines()
    except Exception as exc:
        raise SystemExit(f"cannot read forms JSONL: {exc}") from exc
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            form = json.loads(line)
        except Exception as exc:
            forms.append((line_no, {"__invalid_json__": str(exc)}))
            continue
        forms.append((line_no, form))
    return forms

def item_content_sha256(item):
    path_text = str(item.get("path", ""))
    if not path_text:
        return "", "missing-item-path"
    candidate = pathlib.Path(path_text)
    if candidate.is_absolute():
        return "", "absolute-item-path"
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return "", "item-path-outside-root"
    if not resolved.is_file():
        return "", "item-content-missing"
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest(), ""

def is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())

def review_status_for_decision(review_decision):
    return {
        "needs-edits": "human-review-needs-edits",
        "defer": "human-review-deferred",
        "archive-only": "human-reviewed-archive-only",
        "reject": "human-reviewed-rejected",
        "accept-as-review-record": "human-reviewed-accepted",
    }.get(review_decision, "")

def matches_applied_review(item, form, queue_type, current_content_sha256, allowed_review_bases):
    review_decision = str(form.get("review_decision", ""))
    expected_fields = {
        "human_reviewed_by": str(form.get("human_reviewed_by", "")).strip(),
        "human_reviewed_at": str(form.get("human_reviewed_at", "")).strip(),
        "human_review_decision": review_decision,
        "human_review_content_sha256": current_content_sha256,
        "updated_at": str(form.get("human_reviewed_at", "")).strip(),
        "review_status": review_status_for_decision(review_decision),
    }
    if queue_type == "external-source-review":
        expected_fields.update({
            field: str(form.get(field, "")).strip()
            for field in EXTERNAL_REVIEW_FIELDS
        })
    return (
        str(item.get("review_basis", "")) in allowed_review_bases
        and all(str(item.get(field, "")) == str(value) for field, value in expected_fields.items())
    )

def make_diag(code, message_zh, line_no=None, queue_id="", field="", actual=None, expected=None):
    row = {
        "code": code,
        "message_zh": message_zh,
        "line_no": line_no,
        "queue_id": queue_id,
        "field": field,
    }
    if actual is not None:
        row["actual"] = actual
    if expected is not None:
        row["expected"] = expected
    return row

items = load_items()
items_by_id = {str(item.get("id", "")): item for item in items if item.get("id")}
forms = load_forms()
diagnostics = []
planned_updates = []
seen_queue_ids = {}
review_signature_by_item = {}
review_bases_by_item = {}
for _line_no, candidate_form in forms:
    if not isinstance(candidate_form, dict):
        continue
    candidate_parts = str(candidate_form.get("queue_id", "")).split(":")
    if len(candidate_parts) != 3 or candidate_parts[0] != "item":
        continue
    candidate_basis = str(candidate_form.get("review_basis", "")).strip()
    if candidate_basis:
        review_bases_by_item.setdefault(candidate_parts[1], set()).add(candidate_basis)

if not forms:
    diagnostics.append(make_diag("empty-forms-jsonl", "表单 JSONL 没有可应用的对象行。"))

for line_no, form in forms:
    if "__invalid_json__" in form:
        diagnostics.append(make_diag("invalid-jsonl", f"第 {line_no} 行不是合法 JSON。", line_no=line_no, actual=form["__invalid_json__"]))
        continue
    if not isinstance(form, dict):
        diagnostics.append(make_diag("invalid-form-object", "每一行必须是 JSON object。", line_no=line_no, actual=type(form).__name__, expected="object"))
        continue

    queue_id = str(form.get("queue_id", ""))
    if not queue_id:
        diagnostics.append(make_diag("missing-queue-id", "表单缺少 queue_id。", line_no=line_no, field="queue_id"))
        continue
    if queue_id in seen_queue_ids:
        diagnostics.append(make_diag("duplicate-queue-id", "同一个 queue_id 在表单中出现多次。", line_no=line_no, queue_id=queue_id, actual=[seen_queue_ids[queue_id], line_no], expected="unique queue_id"))
        continue
    seen_queue_ids[queue_id] = line_no

    queue_parts = queue_id.split(":")
    if len(queue_parts) != 3 or queue_parts[0] != "item":
        diagnostics.append(make_diag("unsupported-queue-id", "当前工具只支持 registry item review queue。", line_no=line_no, queue_id=queue_id, expected="item:<id>:<queue_type>"))
        continue
    item_id = queue_parts[1]
    queue_type = queue_parts[2]
    if queue_type not in {"ai-human-review", "external-source-review"}:
        diagnostics.append(make_diag("unsupported-queue-type", "当前工具只支持 AI 或外部资料普通复核队列。", line_no=line_no, queue_id=queue_id, actual=queue_type))
        continue

    item = items_by_id.get(item_id)
    if not item:
        diagnostics.append(make_diag("unknown-item", "registry/items.jsonl 中不存在该 queue_id 对应条目。", line_no=line_no, queue_id=queue_id, field="id", actual=item_id))
        continue

    current_content_sha256, content_hash_error = item_content_sha256(item)
    submitted_content_sha256 = str(form.get("content_sha256", ""))
    if content_hash_error:
        diagnostics.append(make_diag(
            "item-content-sha256-unavailable",
            "当前 registry item 正文无法生成 SHA256，不能应用人工复核表单。",
            line_no=line_no,
            queue_id=queue_id,
            field="content_sha256",
            actual=content_hash_error,
            expected="可读取的仓内正文",
        ))
    elif not SHA256_RE.fullmatch(submitted_content_sha256):
        diagnostics.append(make_diag(
            "invalid-content-sha256",
            "表单 content_sha256 必须是当前正文的 64 位小写 SHA256。",
            line_no=line_no,
            queue_id=queue_id,
            field="content_sha256",
            actual=submitted_content_sha256,
            expected=current_content_sha256,
        ))
    elif submitted_content_sha256 != current_content_sha256:
        diagnostics.append(make_diag(
            "content-sha256-mismatch",
            "表单绑定的正文 SHA256 与当前文件不一致；旧人工判断不得落地。",
            line_no=line_no,
            queue_id=queue_id,
            field="content_sha256",
            actual=submitted_content_sha256,
            expected=current_content_sha256,
        ))

    expected_missing_fields = []
    if queue_type == "ai-human-review":
        if item.get("generated_by_ai") is not True:
            diagnostics.append(make_diag("item-no-longer-ai-generated", "当前条目不再是 generated_by_ai=true，表单已过期。", line_no=line_no, queue_id=queue_id, field="generated_by_ai"))
        expected_missing_fields = [
            field for field in REQUIRED_HUMAN_FIELDS
            if not is_nonempty_string(item.get(field, ""))
        ]
        current_review_decision = str(item.get("human_review_decision", ""))
        stored_review_sha256 = str(item.get("human_review_content_sha256", ""))
        review_content_drifted = (
            current_review_decision in REVIEW_CONTENT_BOUND_DECISIONS
            and bool(stored_review_sha256)
            and stored_review_sha256 != current_content_sha256
        )
        if not expected_missing_fields and (current_review_decision in {"needs-edits", "defer"} or review_content_drifted):
            expected_missing_fields = ["review_resolution"]
    if queue_type == "external-source-review":
        expected_missing_fields = [
            field for field in ["retrieved_at", "read_status", "source_license", "review_basis"]
            if not is_nonempty_string(item.get(field, ""))
        ]
    repair_replay = (
        not expected_missing_fields
        and submitted_content_sha256 == current_content_sha256
        and matches_applied_review(
            item,
            form,
            queue_type,
            current_content_sha256,
            review_bases_by_item.get(item_id, set()),
        )
    )
    if not expected_missing_fields and not repair_replay:
        diagnostics.append(make_diag("queue-item-no-longer-pending", "当前条目已不在待复核队列中，表单已过期或已应用。", line_no=line_no, queue_id=queue_id))

    for field in ["form_type", "schema_version", "queue_type", "object_type", "id", "content_hash_required"]:
        expected = {
            "form_type": "review-queue-human-review",
            "schema_version": 2,
            "queue_type": queue_type,
            "object_type": "registry-item",
            "id": item_id,
            "content_hash_required": True,
        }[field]
        if form.get(field) != expected:
            diagnostics.append(make_diag("field-mismatch", f"表单字段 {field} 与当前 registry 队列不一致。", line_no=line_no, queue_id=queue_id, field=field, actual=form.get(field), expected=expected))

    for field in REQUIRED_HUMAN_FIELDS:
        if not is_nonempty_string(form.get(field, "")):
            diagnostics.append(make_diag("missing-required-human-field", f"人工字段 {field} 不能为空。", line_no=line_no, queue_id=queue_id, field=field))
    if queue_type == "external-source-review":
        for field in EXTERNAL_REVIEW_FIELDS:
            if not is_nonempty_string(form.get(field, "")):
                diagnostics.append(make_diag(
                    "missing-required-external-review-field",
                    f"外部资料复核字段 {field} 不能为空。",
                    line_no=line_no,
                    queue_id=queue_id,
                    field=field,
                ))

    reviewed_at = str(form.get("human_reviewed_at", ""))
    if reviewed_at:
        try:
            reviewed_at_date = dt.date.fromisoformat(reviewed_at)
        except Exception:
            diagnostics.append(make_diag("invalid-human-reviewed-at", "human_reviewed_at 必须是 YYYY-MM-DD。", line_no=line_no, queue_id=queue_id, field="human_reviewed_at", actual=reviewed_at))
        else:
            created_at = str(item.get("created_at", ""))
            try:
                created_at_date = dt.date.fromisoformat(created_at)
            except Exception:
                created_at_date = None
            if created_at_date and reviewed_at_date < created_at_date:
                diagnostics.append(make_diag("human-reviewed-at-before-created-at", "human_reviewed_at 不得早于条目 created_at，否则会写出非法 updated_at。", line_no=line_no, queue_id=queue_id, field="human_reviewed_at", actual=reviewed_at, expected=f">= {created_at}"))

    review_decision = str(form.get("review_decision", ""))
    if review_decision not in VALID_REVIEW_DECISIONS:
        diagnostics.append(make_diag("invalid-review-decision", "review_decision 必须来自候选枚举。", line_no=line_no, queue_id=queue_id, field="review_decision", actual=review_decision, expected=sorted(VALID_REVIEW_DECISIONS)))

    review_signature = tuple(
        str(form.get(field, "")).strip()
        for field in ["human_reviewed_by", "human_reviewed_at", "review_decision", "content_sha256"]
    )
    previous_signature = review_signature_by_item.get(item_id)
    if previous_signature is not None and previous_signature != review_signature:
        diagnostics.append(make_diag(
            "conflicting-item-review-forms",
            "同一 registry item 的多个复核队列表单必须使用相同 reviewer、日期、结论和正文 SHA256。",
            line_no=line_no,
            queue_id=queue_id,
            field="id",
            actual=item_id,
            expected="同一 item 的复核字段完全一致",
        ))
    review_signature_by_item[item_id] = review_signature

    for field in FORBIDDEN_FIELDS:
        if field in form:
            diagnostics.append(make_diag("forbidden-owner-field", f"普通 review queue 表单不得包含 owner gate 字段 {field}。", line_no=line_no, queue_id=queue_id, field=field))

    for field, expected in REQUIRED_GUARDRAILS.items():
        if form.get(field) is not expected:
            diagnostics.append(make_diag("guardrail-field-mismatch", f"guardrail 字段 {field} 不符合只读边界。", line_no=line_no, queue_id=queue_id, field=field, actual=form.get(field), expected=expected))

    target_status = str(item.get("status", ""))

    update_fields = REQUIRED_HUMAN_FIELDS + [
        "human_review_decision",
        "human_review_content_sha256",
        "updated_at",
    ]
    if queue_type == "external-source-review":
        update_fields += EXTERNAL_REVIEW_FIELDS
    planned_updates.append({
        "line_no": line_no,
        "queue_id": queue_id,
        "id": item_id,
        "queue_type": queue_type,
        "review_decision": review_decision,
        "status_before": str(item.get("status", "")),
        "status_after": target_status,
        "lifecycle_mutation": False,
        "will_remain_blocking": review_decision in {"needs-edits", "defer"},
        "content_sha256": current_content_sha256,
        "repair_replay": repair_replay,
        "fields": update_fields,
    })

if diagnostics:
    result = {
        "status": "invalid",
        "read_only": not args.apply,
        "applied": False,
        "forms_path": str(forms_path),
        "diagnostic_count": len(diagnostics),
        "diagnostics": diagnostics,
        "planned_update_count": len(planned_updates),
        "planned_updates": planned_updates,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"invalid: {len(diagnostics)} diagnostics")
    sys.exit(1)

updated_by_id = {}
for update in planned_updates:
    form = next(form for line_no, form in forms if line_no == update["line_no"])
    item = dict(updated_by_id.get(update["id"], items_by_id[update["id"]]))
    item["human_reviewed_by"] = str(form.get("human_reviewed_by", "")).strip()
    item["human_reviewed_at"] = str(form.get("human_reviewed_at", "")).strip()
    item["review_basis"] = str(form.get("review_basis", "")).strip()
    if update["queue_type"] == "external-source-review":
        for field in EXTERNAL_REVIEW_FIELDS:
            item[field] = str(form.get(field, "")).strip()
    item["human_review_decision"] = update["review_decision"]
    item["human_review_content_sha256"] = update["content_sha256"]
    item["updated_at"] = str(form.get("human_reviewed_at", "")).strip()
    item["status"] = update["status_after"]
    item["review_status"] = review_status_for_decision(update["review_decision"])
    updated_by_id[update["id"]] = item

rendered_by_path = {}
for item_id, item in updated_by_id.items():
    relative_path = str(item.get("path", ""))
    target_path = root / relative_path
    metadata, body = load_markdown(target_path)
    rendered = render_markdown(merge_frontmatter_mirror(metadata, item), body)
    final_content_sha256 = bytes_sha256(rendered.encode("utf-8"))
    item["human_review_content_sha256"] = final_content_sha256
    rendered_by_path[relative_path] = rendered
    for update in planned_updates:
        if update["id"] == item_id:
            update["final_content_sha256"] = final_content_sha256

rewritten = []
for item in items:
    item_id = str(item.get("id", ""))
    rewritten.append(updated_by_id.get(item_id, item))
encoded = "\n".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) for item in rewritten) + "\n"

transaction = RepositoryTransaction(root)
for relative_path, rendered in rendered_by_path.items():
    target_path = root / relative_path
    transaction.add_text(
        relative_path,
        rendered,
        expected_sha256=file_sha256(target_path),
    )
transaction.add_text(
    str(items_path.relative_to(root)),
    encoded,
    expected_sha256=file_sha256(items_path),
)
transaction_plan = transaction.plan()
transaction_result = transaction.apply().to_dict() if args.apply else None

result = {
    "status": "applied" if args.apply else "planned",
    "read_only": not args.apply,
    "applied": bool(args.apply),
    "forms_path": str(forms_path),
    "planned_update_count": len(planned_updates),
    "planned_updates": planned_updates,
    "transaction_plan": transaction_plan,
    "transaction_result": transaction_result,
    "guardrails": {
        "owner_gate_mutation": False,
        "lifecycle_mutation": False,
        "memory_write": False,
        "source_project_write": False,
        "active_promotion": False,
    },
    "notes_zh": "本工具只机械落地真实人工填写且与当前整文件 SHA256 一致的普通 review queue 表单；正文漂移会拒绝应用。registry 与正文 frontmatter 在同一可恢复事务中更新，人工复核哈希绑定事务后的正文。archive-only/reject 也只记录普通复核结论，不改变 lifecycle status；生命周期变更必须另走 attestation、授权和 promote/retire 工具。",
}
print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"{result['status']}: {len(planned_updates)} updates")
