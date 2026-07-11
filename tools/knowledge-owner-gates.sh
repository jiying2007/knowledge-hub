#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Print a read-only owner-gate board from owner decision worksheets.")
parser.add_argument("--json", action="store_true")
parser.add_argument("--summary", action="store_true", help="Print a concise owner-facing summary for open rows.")
parser.add_argument("--forms", action="store_true", help="Print copyable owner decision JSONL skeletons for open rows.")
parser.add_argument("--forms-jsonl", action="store_true", help="Print only owner decision JSONL skeleton lines for open rows.")
parser.add_argument("--checklist", action="store_true", help="Print owner-facing closure checklists with intake questions and hard gates.")
parser.add_argument("--evidence-readiness", action="store_true", help="Print read-only evidence readiness and prefill candidates for open rows.")
parser.add_argument("--owner-inbox", action="store_true", help="Print a compact owner-facing inbox with grouped fields, routing and validation commands.")
parser.add_argument("--handoff-packet", action="store_true", help="Print one read-only owner handoff packet with inbox, evidence readiness, forms JSONL and command sequence.")
parser.add_argument("--validate-forms", default="", help="Validate a filled owner decision JSONL file without applying it.")
parser.add_argument("--landing-plan", action="store_true", help="With --validate-forms, print a read-only manual landing plan for valid forms.")
parser.add_argument("--landing-audit", action="store_true", help="With --validate-forms, print a read-only manual landing audit for worksheet/registry/index deltas.")
parser.add_argument("--source-id", default="")
parser.add_argument("--owner", default="", help="Limit output to one exact owner value.")
parser.add_argument("--worksheet-id", default="", help="Limit output to one owner decision worksheet id.")
parser.add_argument("--next-open", action="store_true", help="Limit output to the next open owner gate by review_after and worksheet id.")
parser.add_argument("--status", choices=["all", "open", "resolved"], default="open")
args = parser.parse_args(argv)

errors = []

if args.forms_jsonl:
    conflicts = []
    if args.json:
        conflicts.append("--json")
    if args.summary:
        conflicts.append("--summary")
    if args.forms:
        conflicts.append("--forms")
    if args.checklist:
        conflicts.append("--checklist")
    if args.evidence_readiness:
        conflicts.append("--evidence-readiness")
    if args.owner_inbox:
        conflicts.append("--owner-inbox")
    if args.handoff_packet:
        conflicts.append("--handoff-packet")
    if args.validate_forms:
        conflicts.append("--validate-forms")
    if args.landing_plan:
        conflicts.append("--landing-plan")
    if args.landing_audit:
        conflicts.append("--landing-audit")
    if conflicts:
        parser.error(f"cannot combine --forms-jsonl with {', '.join(conflicts)}")

if args.next_open and args.worksheet_id:
    errors.append("--next-open cannot be combined with --worksheet-id")

if args.handoff_packet and not args.json:
    parser.error("--handoff-packet requires --json")

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

def load_json(path):
    if not path.exists():
        errors.append(f"missing {path.relative_to(root)}")
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        errors.append(f"cannot load {path.relative_to(root)}: {exc}")
        return {}

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

def source_path_values(value):
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if value:
        return [str(value)]
    return []

def source_path_matches(value, expected):
    return str(expected) in source_path_values(value)

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

def compute_source_identity(row):
    source_id = str(row.get("source_id", ""))
    source_path = str(row.get("source_path", ""))
    expected_sha256 = str(row.get("source_sha256_expected", ""))
    expected_size = row.get("source_size_expected", "")
    source_root = source_roots.get(source_id, "")
    identity = {
        "source_identity_read_mode": "read-bytes-for-hash",
        "source_body_read_for_hash": True,
        "source_body_copied": False,
        "source_project_written": False,
        "source_root": source_root,
        "source_path": source_path,
        "source_file_exists": False,
        "expected_sha256": expected_sha256,
        "expected_size": expected_size,
        "observed_sha256": "",
        "observed_size": "",
        "identity_status": "unavailable",
        "notes_zh": "只读源文件身份提示；为计算 hash 会读取 source 文件字节，但不复制正文、不写源项目、不代表 owner 已签收，不自动填充 source_sha256/source_size，不关闭门禁。",
    }
    if not source_root or not source_path:
        return identity
    base = pathlib.Path(source_root).expanduser().resolve()
    candidate = (base / source_path).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        identity["identity_status"] = "path-outside-source-root"
        return identity
    if not candidate.is_file():
        identity["identity_status"] = "missing"
        return identity
    try:
        data = candidate.read_bytes()
    except Exception:
        identity["identity_status"] = "read-error"
        return identity
    observed_sha256 = hashlib.sha256(data).hexdigest()
    observed_size = len(data)
    identity["source_file_exists"] = True
    identity["observed_sha256"] = observed_sha256
    identity["observed_size"] = observed_size
    size_matches = str(expected_size) == str(observed_size) if expected_size != "" else False
    sha_matches = bool(expected_sha256) and expected_sha256 == observed_sha256
    if sha_matches and size_matches:
        identity["identity_status"] = "match"
    elif expected_sha256 or expected_size != "":
        identity["identity_status"] = "mismatch"
    else:
        identity["identity_status"] = "observed-no-expected"
    return identity

def make_decision_form(row):
    form = {
        "worksheet_id": row["id"],
        "source_id": row["source_id"],
        "source_path": row["source_path"],
        "worksheet": row["worksheet"],
        "owner": row["owner"],
        "status": row.get("status", ""),
        "worksheet_status": row.get("worksheet_status", ""),
        "owner_question_zh": row.get("owner_question_zh", ""),
        "default_state": row.get("default_state", ""),
        "allowed_next_status": row.get("allowed_next_status", []),
        "hard_gate_summary": row.get("hard_gate_summary", ""),
        "hard_gate": row.get("hard_gate", ""),
        "owner_route": row.get("owner_route", {}),
        "observed_source_identity": row.get("observed_source_identity", {}),
        "read_only_prefill_candidates": make_read_only_prefill_candidates(row),
        "source_execution_root": row.get("source_execution_root", ""),
        "verification_cwd": row.get("verification_cwd", ""),
        "verification_commands": row.get("verification_commands", []),
        "allowed_owner_decisions": row["decision_options"],
        "target_candidates": row.get("target_candidates", []),
        "required_owner_fields": row["required_owner_fields"],
        "must_not": row["must_not"],
        "notes_zh": "本骨架只供 owner 人工填写和复核；status、worksheet_status、owner_question_zh、default_state、allowed_next_status、hard_gate_summary、hard_gate、observed_source_identity、allowed_owner_decisions、target_candidates、required_owner_fields 和 must_not 是只读上下文；脚本不写文件、不关闭门禁、不提升 active。",
    }
    for field in row["required_owner_fields"]:
        form.setdefault(field, default_field_value(field, row))
    for field in ["owner_decision", "target_decision", "reviewed_by", "reviewed_at", "review_after", "source_status", "evidence_refs", "status_reason"]:
        form.setdefault(field, default_field_value(field, row))
    return form

def make_owner_checklist(row):
    return {
        "worksheet_id": row["id"],
        "source_id": row["source_id"],
        "source_path": row["source_path"],
        "owner": row["owner"],
        "owner_question_zh": row.get("owner_question_zh", ""),
        "default_state": row.get("default_state", ""),
        "allowed_owner_decisions": row["decision_options"],
        "target_candidates": row.get("target_candidates", []),
        "allowed_next_status": row.get("allowed_next_status", []),
        "required_owner_fields": row["required_owner_fields"],
        "hard_gate_summary": row.get("hard_gate_summary", ""),
        "hard_gate": row.get("hard_gate", ""),
        "owner_route": row.get("owner_route", {}),
        "observed_source_identity": row.get("observed_source_identity", {}),
        "source_execution_root": row.get("source_execution_root", ""),
        "verification_cwd": row.get("verification_cwd", ""),
        "verification_commands": row.get("verification_commands", []),
        "must_not": row["must_not"],
        "notes_zh": "本清单只把 owner intake、worksheet 和执行目录提示合并到一个只读视图；不能替代 owner 决策，不能关闭门禁。",
    }

def _row_ref(row):
    return {
        "worksheet_id": row["id"],
        "source_id": row["source_id"],
        "source_path": row["source_path"],
        "owner": row["owner"],
        "review_after": row["review_after"],
    }

def _display_path(path):
    text = str(path)
    for prefix in user_path_prefixes():
        if text == prefix:
            return "~"
        if text.startswith(prefix + "/"):
            return "~" + text[len(prefix):]
    try:
        return str(path.relative_to(root))
    except ValueError:
        return text

def user_path_prefixes():
    prefixes = [str(pathlib.Path.home())]
    user_name = os.environ.get("USER", "")
    if user_name:
        prefixes.append("/" + "vsdata" + "/" + user_name)
    return [prefix for prefix in prefixes if prefix and prefix != "/"]

def _read_jsonl_local(path):
    local_errors = []
    rows_local = []
    if not path.exists():
        return [], [f"missing {_display_path(path)}"]
    try:
        lines = path.read_text().splitlines()
    except Exception as exc:
        return [], [f"cannot read {_display_path(path)}: {exc}"]
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rows_local.append(json.loads(line))
        except Exception as exc:
            local_errors.append(f"{_display_path(path)}:{line_no}: invalid jsonl: {exc}")
    return rows_local, local_errors

def inspect_owner_ready_item(row, item):
    tags = item.get("tags", [])
    source = item.get("source", {}) if isinstance(item.get("source"), dict) else {}
    path_value = str(item.get("path", "") or "")
    md_path = root / path_value if path_value else root / "__missing_owner_ready_path__"
    jsonl_path = root / str(pathlib.Path(path_value).with_suffix(".jsonl")) if path_value else root / "__missing_owner_ready_path__.jsonl"
    checks = {}
    errors_local = []

    def check(name, condition, message):
        checks[name] = bool(condition)
        if not condition:
            errors_local.append(message)

    check("registry_kind_audit", item.get("kind") == "audit", "registry kind must be audit")
    check("registry_status_reviewing", item.get("status") == "reviewing", "registry status must be reviewing")
    check("registry_review_status_owner_ready", item.get("review_status") == "owner-ready-no-decision", "registry review_status must be owner-ready-no-decision")
    check("registry_tags_owner_gate_ready", "owner-gate" in tags and "owner-ready" in tags, "registry tags must include owner-gate and owner-ready")
    check("registry_source_type_generated", source.get("type") == "generated", "registry source.type must be generated")
    check("registry_source_id_match", source.get("source_id") == row["source_id"], "registry source_id must match worksheet")
    check("registry_source_path_match", source_path_matches(source.get("source_path"), row["source_path"]), "registry source_path must match worksheet")
    check("artifact_path_owner_ready_package", path_value.startswith("artifacts/manifests/") and "owner-ready-package" in pathlib.Path(path_value).name, "artifact path must point to an owner-ready package manifest")
    check("artifact_markdown_exists", md_path.is_file(), "owner-ready package markdown must exist")
    check("artifact_jsonl_exists", jsonl_path.is_file(), "owner-ready package jsonl must exist")

    md_text = ""
    if md_path.is_file():
        try:
            md_text = md_path.read_text()
        except Exception as exc:
            errors_local.append(f"cannot read {_display_path(md_path)}: {exc}")
    check(
        "package_markdown_commands_cwd_stable",
        "rtk bash tools/" not in md_text,
        "owner-ready package markdown must use ~/knowledge-hub/tools commands instead of rtk bash tools/...",
    )

    package_rows, package_errors = _read_jsonl_local(jsonl_path)
    errors_local.extend(package_errors)
    check("package_jsonl_single_row", len(package_rows) == 1, "owner-ready package jsonl must contain exactly one row")
    package = package_rows[0] if len(package_rows) == 1 else {}
    identity = package.get("observed_source_identity", {}) if isinstance(package.get("observed_source_identity"), dict) else {}
    evidence_refs = package.get("evidence_refs", [])
    evidence_ref_commands_are_stable = True
    if not isinstance(evidence_refs, list):
        evidence_ref_commands_are_stable = False
    else:
        for ref in evidence_refs:
            if not isinstance(ref, str):
                evidence_ref_commands_are_stable = False
                break
            stripped = ref.strip()
            if stripped.startswith("tools/") or "rtk bash tools/" in stripped:
                evidence_ref_commands_are_stable = False
                break
    check("package_classification_match", package.get("classification") == "single-owner-ready-package", "package classification must be single-owner-ready-package")
    check("package_worksheet_id_match", package.get("worksheet_id") == row["id"], "package worksheet_id must match worksheet")
    check("package_source_id_match", package.get("source_id") == row["source_id"], "package source_id must match worksheet")
    check("package_source_path_match", source_path_matches(package.get("source_path"), row["source_path"]), "package source_path must match worksheet")
    check("package_decision_owner_ready", package.get("decision") == "owner-ready-no-decision", "package decision must be owner-ready-no-decision")
    check("package_status_reviewing", package.get("status") == "reviewing", "package status must be reviewing")
    check("package_open_gate_remains", package.get("open_gate_remains") is True, "package open_gate_remains must be true")
    check("package_identity_match", identity.get("status") == "match", "package observed_source_identity.status must be match")
    check(
        "package_evidence_refs_cwd_stable",
        evidence_ref_commands_are_stable,
        "owner-ready package evidence_refs must use stable rtk bash ~/knowledge-hub/tools commands or non-command artifact refs",
    )

    return {
        "id": item.get("id", ""),
        "path": path_value,
        "jsonl_path": _display_path(jsonl_path),
        "review_status": item.get("review_status", ""),
        "decision": package.get("decision", ""),
        "open_gate_remains": package.get("open_gate_remains", None),
        "identity_status": identity.get("status", ""),
        "package_evidence_refs": evidence_refs if isinstance(evidence_refs, list) else [],
        "status": "valid" if not errors_local else "invalid",
        "coverage_checks": checks,
        "errors": errors_local,
    }

def owner_ready_items(row):
    candidates = [
        item
        for item in row.get("registry_items", [])
        if item.get("review_status") == "owner-ready-no-decision" or "owner-ready" in item.get("tags", [])
    ]
    return [inspect_owner_ready_item(row, item) for item in candidates]

def owner_ready_state(row):
    packages = owner_ready_items(row)
    valid_packages = [item for item in packages if item["status"] == "valid"]
    if not packages:
        return "missing", packages
    if len(packages) > 1:
        return "duplicate", packages
    if len(valid_packages) == 1:
        return "covered", packages
    return "invalid", packages

def owner_ready_evidence_refs(row):
    refs = []
    for item in owner_ready_items(row):
        for ref in item.get("package_evidence_refs", []):
            if ref not in refs:
                refs.append(ref)
    return refs

def _is_evidence_field(field):
    field_text = str(field)
    return (
        field_text == "evidence_refs"
        or field_text == "gate_evidence"
        or field_text.endswith("_evidence")
        or field_text.endswith("_evidence_refs")
        or "evidence" in field_text
    )

def _classify_evidence_command(command):
    text = str(command).strip()
    if not text:
        return {
            "command": text,
            "bucket": "empty",
            "notes_zh": "空命令不能作为证据候选。",
        }
    stable_prefixes = [
        "rtk bash ~/knowledge-hub/tools/",
        "rtk git -C ~/knowledge-hub ",
        "rtk git -C ~/knowledge-hub ",
    ]
    if any(text.startswith(prefix) for prefix in stable_prefixes):
        return {
            "command": text,
            "bucket": "safe-command-candidate",
            "notes_zh": "Knowledge Hub 只读或本仓状态命令；仍需人工运行并引用输出，不自动写入表单。",
        }
    return {
        "command": text,
        "bucket": "project-command-needs-owner-or-lab-run",
        "notes_zh": "项目侧、构建、硬件、分支状态或上下文相关命令；需要 owner 或实验环境人工运行后再引用。",
    }

def _field_readiness(field, row, evidence_refs):
    identity = row.get("observed_source_identity", {}) if isinstance(row.get("observed_source_identity"), dict) else {}
    identity_matches = identity.get("identity_status") == "match"
    if field == "source_sha256":
        return {
            "field": field,
            "readiness": "copy-from-source-identity" if identity_matches else "source-identity-not-ready",
            "candidate": identity.get("observed_sha256", "") if identity_matches else "",
            "notes_zh": "候选值只来自 observed_source_identity；正式 source_sha256 字段仍必须由 owner 人工复制和签收。",
        }
    if field == "source_size":
        return {
            "field": field,
            "readiness": "copy-from-source-identity" if identity_matches else "source-identity-not-ready",
            "candidate": identity.get("observed_size", "") if identity_matches else "",
            "notes_zh": "候选值只来自 observed_source_identity；正式 source_size 字段仍必须由 owner 人工复制和签收。",
        }
    if field == "review_after":
        return {
            "field": field,
            "readiness": "copy-from-worksheet",
            "candidate": row.get("review_after", ""),
            "notes_zh": "候选值来自 worksheet 排期；owner 可按实际复核周期调整。",
        }
    if field == "owner_decision":
        return {
            "field": field,
            "readiness": "enum-choice-required",
            "candidate": row.get("decision_options", []),
            "notes_zh": "必须由真实 owner 从 allowed_owner_decisions 中选择，工具不代选。",
        }
    if field == "target_decision":
        return {
            "field": field,
            "readiness": "enum-choice-required",
            "candidate": row.get("target_candidates", []),
            "notes_zh": "必须由真实 owner 从 target_candidates 中选择，不能写到候选目标之外。",
        }
    if _is_evidence_field(field):
        return {
            "field": field,
            "readiness": "owner-ready-evidence-ref-candidate" if evidence_refs else "command-evidence-required",
            "candidate": evidence_refs,
            "notes_zh": "owner-ready package 的 evidence_refs 只是引用候选；owner 仍需确认是否足以支撑该字段。",
        }
    return {
        "field": field,
        "readiness": "owner-input-required",
        "candidate": "",
        "notes_zh": "需要真实 owner 填写或确认；工具不自动推断。",
    }

def make_read_only_prefill_candidates(row):
    evidence_refs = owner_ready_evidence_refs(row)
    identity = row.get("observed_source_identity", {}) if isinstance(row.get("observed_source_identity"), dict) else {}
    identity_matches = identity.get("identity_status") == "match"
    field_readiness = [
        _field_readiness(field, row, evidence_refs)
        for field in row.get("required_owner_fields", [])
    ]
    return {
        "read_only": True,
        "no_owner_decision_generated": True,
        "formal_owner_fields_remain_manual": [
            "owner_decision",
            "target_decision",
            "reviewed_by",
            "reviewed_at",
            "source_sha256",
            "source_size",
            "evidence_refs",
            "status_reason",
        ],
        "source_sha256_candidate": identity.get("observed_sha256", "") if identity_matches else "",
        "source_size_candidate": identity.get("observed_size", "") if identity_matches else "",
        "review_after_candidate": row.get("review_after", ""),
        "evidence_ref_candidates": evidence_refs,
        "field_readiness": field_readiness,
        "notes_zh": "这些值只用于减少 owner 查找成本，不写入正式字段、不代表签收、不关闭 owner gate。",
    }

def make_evidence_readiness(rows):
    readiness_rows = []
    status_counts = {}
    for row in rows:
        evidence_refs = owner_ready_evidence_refs(row)
        field_readiness = [
            _field_readiness(field, row, evidence_refs)
            for field in row.get("required_owner_fields", [])
        ]
        mechanical_known_fields = [
            item["field"]
            for item in field_readiness
            if item["readiness"] in {"copy-from-source-identity", "copy-from-worksheet"}
        ]
        owner_answer_required_fields = [
            item["field"]
            for item in field_readiness
            if item["readiness"] in {"owner-input-required", "enum-choice-required"}
        ]
        command_evidence_required_fields = [
            item["field"]
            for item in field_readiness
            if item["readiness"] == "command-evidence-required"
        ]
        command_candidates = [_classify_evidence_command(command) for command in row.get("verification_commands", [])]
        safe_command_candidates = [item for item in command_candidates if item["bucket"] == "safe-command-candidate"]
        project_command_candidates = [
            item for item in command_candidates
            if item["bucket"] == "project-command-needs-owner-or-lab-run"
        ]
        source_identity_status = row.get("observed_source_identity", {}).get("identity_status", "unavailable")
        owner_ready_status, owner_ready_packages = owner_ready_state(row)
        if row.get("active_registry_items"):
            readiness_status = "blocked-active-exposure"
        elif source_identity_status != "match":
            readiness_status = "blocked-source-identity"
        elif owner_ready_status != "covered":
            readiness_status = "blocked-owner-ready-package"
        else:
            readiness_status = "ready-for-owner-review-owner-input-required"
        status_counts[readiness_status] = status_counts.get(readiness_status, 0) + 1
        readiness_rows.append(
            {
                "worksheet_id": row["id"],
                "source_id": row["source_id"],
                "source_path": row["source_path"],
                "owner": row["owner"],
                "owner_route": row.get("owner_route", {}),
                "status": row["status"],
                "readiness_status": readiness_status,
                "source_identity_status": source_identity_status,
                "owner_ready_package_status": owner_ready_status,
                "owner_ready_packages": owner_ready_packages,
                "mechanical_known_fields": mechanical_known_fields,
                "owner_answer_required_fields": owner_answer_required_fields,
                "command_evidence_required_fields": command_evidence_required_fields,
                "owner_ready_evidence_refs": evidence_refs,
                "safe_command_candidates": safe_command_candidates,
                "project_command_candidates": project_command_candidates,
                "field_readiness": field_readiness,
                "read_only_prefill_candidates": make_read_only_prefill_candidates(row),
                "notes_zh": "只读证据准备度；帮助 owner 找候选值和命令，不生成 owner decision，不写文件，不关闭 gate。",
            }
        )
    return {
        "status": "ready-for-owner-review" if rows and all(
            row["readiness_status"] == "ready-for-owner-review-owner-input-required"
            for row in readiness_rows
        ) else "needs-attention" if rows else "empty",
        "read_only": True,
        "row_count": len(readiness_rows),
        "status_counts": dict(sorted(status_counts.items())),
        "rows": readiness_rows,
        "notes_zh": "evidence readiness 只汇总候选证据和人工动作，不自动填 owner 字段、不关闭 gate、不提升 active。",
    }

def group_owner_required_fields(row):
    manual_fields = []
    copyable_candidate_fields = []
    evidence_fields = []
    verification_fields = []
    automation_boundary_fields = []
    other_manual_fields = []
    copyable_names = {"source_sha256", "source_size", "review_after"}
    automation_names = {
        "automation_enabled",
        "writes_memory",
        "writes_team_active_index",
        "no_memory_write_gate",
        "not_active_source",
        "contains_memory_candidates",
    }
    verification_markers = ("verification", "test", "validation", "command", "branch", "commit", "tag")
    core_manual = {"owner_decision", "target_decision", "reviewed_by", "reviewed_at", "source_status", "status_reason"}
    for field in row.get("required_owner_fields", []):
        field_text = str(field)
        if field_text in core_manual:
            manual_fields.append(field_text)
        elif field_text in copyable_names:
            copyable_candidate_fields.append(field_text)
        elif _is_evidence_field(field_text):
            evidence_fields.append(field_text)
        elif field_text in automation_names:
            automation_boundary_fields.append(field_text)
        elif any(marker in field_text for marker in verification_markers):
            verification_fields.append(field_text)
        else:
            other_manual_fields.append(field_text)
    return {
        "manual_decision_fields": manual_fields,
        "other_manual_owner_fields": other_manual_fields,
        "copyable_candidate_fields": copyable_candidate_fields,
        "evidence_fields": evidence_fields,
        "verification_context_fields": verification_fields,
        "automation_boundary_fields": automation_boundary_fields,
        "field_count": len(row.get("required_owner_fields", [])),
        "notes_zh": "字段分组只降低 owner 复核成本；manual 字段必须由真实 owner 填写，copyable 候选也必须人工签收后才可落地。",
    }

def make_owner_inbox(rows):
    inbox_rows = []
    owner_counts = {}
    for row in rows:
        if row["status"] != "open":
            continue
        owner = row.get("owner", "") or "<missing-owner>"
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
        ready_status, ready_packages = owner_ready_state(row)
        owner_arg = shlex_quote(owner)
        source_id = row["source_id"]
        worksheet_id = row["id"]
        inbox_rows.append(
            {
                "worksheet_id": worksheet_id,
                "source_id": source_id,
                "source_path": row["source_path"],
                "owner": owner,
                "review_after": row.get("review_after", ""),
                "owner_question_zh": row.get("owner_question_zh", ""),
                "allowed_owner_decisions": row.get("decision_options", []),
                "target_candidates": row.get("target_candidates", []),
                "owner_route": row.get("owner_route", {}),
                "required_field_groups": group_owner_required_fields(row),
                "read_only_prefill_candidates": make_read_only_prefill_candidates(row),
                "observed_source_identity": row.get("observed_source_identity", {}),
                "owner_ready_package_status": ready_status,
                "owner_ready_package_ids": [item.get("id", "") for item in ready_packages if item.get("id")],
                "owner_ready_package_paths": [item.get("path", "") for item in ready_packages if item.get("path")],
                "verification_cwd": row.get("verification_cwd", ""),
                "verification_commands": row.get("verification_commands", []),
                "commands": {
                    "focus_command": (
                        "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                        f"--source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --checklist --forms"
                    ),
                    "forms_jsonl_command": (
                        "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                        f"--source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --forms-jsonl"
                    ),
                    "evidence_readiness_command": (
                        "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                        f"--source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --evidence-readiness --json"
                    ),
                    "validate_forms_command_template": (
                        "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                        f"--source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --validate-forms '<owner-decisions.jsonl>' --json"
                    ),
                    "landing_plan_command_template": (
                        "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                        f"--source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --validate-forms '<owner-decisions.jsonl>' --landing-plan --json"
                    ),
                    "landing_audit_command_template": (
                        "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                        f"--source-id {source_id} --owner {owner_arg} --worksheet-id {worksheet_id} --validate-forms '<owner-decisions.jsonl>' --landing-audit --json"
                    ),
                },
                "must_not": [
                    "不得把 routing_owner 当 reviewed_by",
                    "不得由工具或 AI 代签 owner decision",
                    "不得把 owner-ready package 当成已批准决策",
                    "不得关闭未签收 owner gate",
                    "不得把 project-specific 内容提升到 domains/embedded/standards/",
                    "不得修改 PCR02 源项目 docs",
                    "不得写 ~/.codex/memories",
                ],
                "notes_zh": "单条 owner inbox 只做人工复核入口；命令和候选字段均为只读上下文，不生成、不保存、不应用 owner decision。",
            }
        )
    return {
        "status": "ready-for-owner-review" if inbox_rows else "empty",
        "read_only": True,
        "report_only": True,
        "no_owner_decision_generated": True,
        "no_owner_gate_closed": True,
        "routing_owner_is_not_reviewed_by": True,
        "row_count": len(inbox_rows),
        "owner_counts": dict(sorted(owner_counts.items())),
        "rows": inbox_rows,
        "notes_zh": "owner inbox 是单屏人工复核队列；只汇总 owner 问题、路由、字段分组、候选证据和校验命令，不写文件、不关闭 gate、不提升 active。",
    }

def make_owner_ready_coverage(rows):
    coverage = {
        "owner_ready_package_count": 0,
        "owner_ready_missing_count": 0,
        "owner_ready_invalid_count": 0,
        "owner_ready_duplicate_count": 0,
        "owner_ready_missing": [],
        "owner_ready_invalid": [],
        "owner_ready_duplicate": [],
    }
    for row in rows:
        status, packages = owner_ready_state(row)
        if status == "covered":
            coverage["owner_ready_package_count"] += 1
        elif status == "missing":
            coverage["owner_ready_missing_count"] += 1
            coverage["owner_ready_missing"].append(_row_ref(row))
        elif status == "invalid":
            coverage["owner_ready_invalid_count"] += 1
            entry = _row_ref(row)
            entry["owner_ready_packages"] = packages
            coverage["owner_ready_invalid"].append(entry)
        elif status == "duplicate":
            coverage["owner_ready_duplicate_count"] += 1
            entry = _row_ref(row)
            entry["owner_ready_packages"] = packages
            coverage["owner_ready_duplicate"].append(entry)
    coverage["owner_ready_package_coverage"] = f"{coverage['owner_ready_package_count']}/{len(rows)}"
    return coverage

def make_owner_ready_blocking_context(rows):
    open_rows = [row for row in rows if row.get("status") == "open"]
    open_coverage = make_owner_ready_coverage(open_rows)
    blocking_missing = open_coverage["owner_ready_missing_count"]
    blocking_invalid = open_coverage["owner_ready_invalid_count"]
    blocking_duplicate = open_coverage["owner_ready_duplicate_count"]
    has_blocking = bool(blocking_missing or blocking_invalid or blocking_duplicate)
    if not open_rows:
        status = "not-applicable-no-open-owner-gates"
        note = (
            "owner-ready package 覆盖只阻断 open owner gate；当前没有 open owner gate，"
            "历史 owner-ready package 缺失或被 owner decision landing 取代不再阻断。"
        )
    elif has_blocking:
        status = "blocked-open-owner-gates"
        note = (
            "owner-ready package 覆盖只阻断 open owner gate；当前仍有 open owner gate 缺少、"
            "无效或重复 owner-ready package，landing 前必须先修复。"
        )
    else:
        status = "pass-open-owner-gates"
        note = (
            "owner-ready package 覆盖只阻断 open owner gate；当前 open owner gate 的"
            " owner-ready package 覆盖有效。"
        )
    return {
        "owner_ready_blocking_scope": "open-owner-gates-only",
        "owner_ready_blocking_status": status,
        "owner_ready_missing_blocking": bool(blocking_missing),
        "owner_ready_invalid_blocking": bool(blocking_invalid),
        "owner_ready_duplicate_blocking": bool(blocking_duplicate),
        "owner_ready_blocking_counts": {
            "open_row_count": len(open_rows),
            "missing": blocking_missing,
            "invalid": blocking_invalid,
            "duplicate": blocking_duplicate,
            "coverage": open_coverage["owner_ready_package_coverage"],
        },
        "owner_ready_status_note_zh": note,
    }

def _safe_slug(value):
    text = str(value).strip().lower()
    chars = []
    for char in text:
        if char.isalnum() or char in {"-", "_"}:
            chars.append(char)
        else:
            chars.append("-")
    slug = "".join(chars).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "owner"

def make_owner_handoff_packet(owner, source_id, owner_open_rows, next_row, commands):
    owner_ready_statuses = {}
    required_fields = []
    must_not = []
    for row in owner_open_rows:
        status, _packages = owner_ready_state(row)
        owner_ready_statuses[status] = owner_ready_statuses.get(status, 0) + 1
        for field in row.get("required_owner_fields", []):
            if field not in required_fields:
                required_fields.append(field)
        for rule in row.get("must_not", []):
            if rule not in must_not:
                must_not.append(rule)
    local_path = (
        f"artifacts/manifests/{source_id}-{_safe_slug(owner)}-owner-decisions-YYYYMMDD.local.jsonl"
        if source_id
        else "artifacts/manifests/<source-id>-<owner>-owner-decisions-YYYYMMDD.local.jsonl"
    )
    return {
        "status": "ready-for-owner-review" if owner_open_rows else "empty",
        "read_only": True,
        "owner": owner,
        "source_id": source_id,
        "open_count": len(owner_open_rows),
        "worksheet_ids": [row["id"] for row in owner_open_rows],
        "next_worksheet_id": next_row.get("id", "") if next_row else "",
        "suggested_local_owner_decisions_path": local_path,
        "owner_ready_status_counts": dict(sorted(owner_ready_statuses.items())),
        "manual_owner_fields": required_fields,
        "recommended_sequence": [
            {
                "step": "1-open-owner-inbox",
                "command": commands.get("owner_inbox_json_command", ""),
                "notes_zh": "先用单屏 owner inbox 查看问题、字段分组、候选证据和后续命令；这一步不生成 owner decision。",
            },
            {
                "step": "2-review-summary",
                "command": commands.get("summary_command", ""),
                "notes_zh": "先确认 owner 角色、open worksheet、source path 和 owner_route；这一步不生成 owner decision。",
            },
            {
                "step": "3-check-evidence-readiness",
                "command": commands.get("evidence_readiness_command", ""),
                "notes_zh": "只读查看 source identity、owner-ready evidence ref 候选和仍需人工回答的字段。",
            },
            {
                "step": "4-export-forms",
                "command": commands.get("forms_jsonl_command", ""),
                "output_path_hint": local_path,
                "notes_zh": "owner 可把骨架复制到本地临时 JSONL 后手工填写；工具不写该文件。",
            },
            {
                "step": "5-validate-filled-forms",
                "command_template": commands.get("validate_forms_command_template", ""),
                "replace_placeholder_with": local_path,
                "notes_zh": "只读校验 owner 填写结果；不通过时不得进入 landing plan。",
            },
            {
                "step": "6-plan-manual-landing",
                "command_template": commands.get("landing_plan_command_template", ""),
                "replace_placeholder_with": local_path,
                "notes_zh": "生成 no-write 人工落地计划；仍不写 registry、worksheet、migration 或 index。",
            },
            {
                "step": "7-audit-manual-landing",
                "command_template": commands.get("landing_audit_command_template", ""),
                "replace_placeholder_with": local_path,
                "notes_zh": "人工落地后复核 worksheet、registry、source policy 和 index 是否同步；不能把 audit 当 owner approval。",
            },
        ],
        "must_not": [
            "不得把 routing_owner 当 reviewed_by",
            "不得由工具或 AI 代签 owner decision",
            "不得关闭未签收 owner gate",
            "不得把 owner-ready package 当作已批准决策",
        ] + [rule for rule in must_not if rule not in {
            "不得把 routing_owner 当 reviewed_by",
            "不得由工具或 AI 代签 owner decision",
            "不得关闭未签收 owner gate",
            "不得把 owner-ready package 当作已批准决策",
        }],
        "notes_zh": "只读 owner handoff 包；把已有命令排成可交给 owner 的顺序，不生成、不保存、不应用 owner decision。",
    }

def make_owner_dispatch(rows):
    dispatch_rows = []
    rows_by_scope = {}
    for row in rows:
        owner = row.get("owner", "") or "<missing-owner>"
        source_id = row.get("source_id", "") or ""
        rows_by_scope.setdefault((source_id, owner), []).append(row)
    for (source_id, owner), owner_rows in sorted(rows_by_scope.items()):
        owner_open_rows = [row for row in owner_rows if row["status"] == "open"]
        next_row = (
            sorted(
                owner_open_rows,
                key=lambda row: (
                    str(row.get("review_after", "") or "9999-12-31"),
                    str(row.get("id", "")),
                ),
            )[0]
            if owner_open_rows
            else {}
        )
        owner_arg = shlex_quote(owner)
        owner_routes = [row.get("owner_route", {}) for row in owner_open_rows if row.get("owner_route")]
        unique_owner_routes = []
        seen_routes = set()
        for route in owner_routes:
            key = (route.get("decision_owner_role", ""), route.get("source_id", ""))
            if key in seen_routes:
                continue
            seen_routes.add(key)
            unique_owner_routes.append(route)
        commands = {
            "owner_inbox_json_command": (
                "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                f"--source-id {source_id} --owner {owner_arg} --owner-inbox --json"
            )
            if source_id
            else "",
            "summary_command": (
                "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                f"--source-id {source_id} --owner {owner_arg} --summary"
            )
            if source_id
            else "",
            "forms_jsonl_command": (
                "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                f"--source-id {source_id} --owner {owner_arg} --forms-jsonl"
            )
            if source_id
            else "",
            "evidence_readiness_command": (
                "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                f"--source-id {source_id} --owner {owner_arg} --evidence-readiness --json"
            )
            if source_id
            else "",
            "validate_forms_command_template": (
                "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                f"--source-id {source_id} --owner {owner_arg} --validate-forms '<owner-decisions.jsonl>' --json"
            )
            if source_id
            else "",
            "landing_plan_command_template": (
                "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                f"--source-id {source_id} --owner {owner_arg} --validate-forms '<owner-decisions.jsonl>' --landing-plan --json"
            )
            if source_id
            else "",
            "landing_audit_command_template": (
                "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                f"--source-id {source_id} --owner {owner_arg} --validate-forms '<owner-decisions.jsonl>' --landing-audit --json"
            )
            if source_id
            else "",
        }
        dispatch_rows.append(
            {
                "owner": owner,
                "source_id": source_id,
                "source_ids": [source_id] if source_id else [],
                "dispatch_scope_id": f"{source_id or '<missing-source>'}:{owner}",
                "mixed_source_owner": False,
                "owner_route": unique_owner_routes[0] if len(unique_owner_routes) == 1 else {},
                "owner_routes": unique_owner_routes,
                "row_count": len(owner_rows),
                "open_count": len(owner_open_rows),
                "resolved_count": sum(1 for row in owner_rows if row["status"] == "resolved"),
                "worksheet_ids": [row["id"] for row in owner_open_rows],
                "source_paths": [row["source_path"] for row in owner_open_rows],
                **commands,
                "next_focus_command": (
                    "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                    f"--source-id {next_row['source_id']} --owner {owner_arg} "
                    f"--worksheet-id {next_row['id']} --checklist --forms"
                )
                if next_row
                else "",
                "suggested_owner_packet": make_owner_handoff_packet(owner, source_id, owner_open_rows, next_row, commands),
                "notes_zh": "只读 owner 分派包；按 source_id + owner 分派，避免同一 owner 跨 source 时丢失 source scope。用于人工领取、导出骨架、校验和生成 no-write landing plan。owner_route 只说明分派路由，不生成 owner decision，不关闭 gate。",
            }
        )
    return dispatch_rows

def make_owner_handoff_packets(rows):
    packets = []
    dispatch_rows = make_owner_dispatch(rows)
    for dispatch in dispatch_rows:
        owner = dispatch.get("owner", "")
        source_id = dispatch.get("source_id", "")
        owner_open_rows = [
            row
            for row in rows
            if row.get("status") == "open"
            and (row.get("owner", "") or "<missing-owner>") == owner
            and (row.get("source_id", "") or "") == source_id
        ]
        base_packet = dict(dispatch.get("suggested_owner_packet", {}))
        command_fields = [
            "owner_inbox_json_command",
            "summary_command",
            "forms_jsonl_command",
            "evidence_readiness_command",
            "validate_forms_command_template",
            "landing_plan_command_template",
            "landing_audit_command_template",
            "next_focus_command",
        ]
        base_packet.update(
            {
                "packet_type": "owner-handoff",
                "dispatch_scope_id": dispatch.get("dispatch_scope_id", ""),
                "source_ids": dispatch.get("source_ids", []),
                "mixed_source_owner": dispatch.get("mixed_source_owner", False),
                "owner_route": dispatch.get("owner_route", {}),
                "owner_routes": dispatch.get("owner_routes", []),
                "source_paths": dispatch.get("source_paths", []),
                "commands": {field: dispatch.get(field, "") for field in command_fields},
                "owner_inbox": make_owner_inbox(owner_open_rows),
                "evidence_readiness": make_evidence_readiness(owner_open_rows),
                "forms_jsonl_lines": [
                    json.dumps(make_decision_form(row), ensure_ascii=False, separators=(",", ":"))
                    for row in owner_open_rows
                ],
                "owner_checklists": [make_owner_checklist(row) for row in owner_open_rows],
                "no_owner_decision_generated": True,
                "no_owner_gate_closed": True,
                "routing_owner_is_not_reviewed_by": True,
                "report_only": True,
                "notes_zh": "只读 owner handoff packet；一次性聚合 inbox、证据准备度、JSONL 骨架和命令序列，方便人工 owner 离线签收。不写文件、不代签、不关闭 gate。",
            }
        )
        packets.append(base_packet)
    return packets

def make_owner_summary(rows):
    summary_rows = []
    source_identity_counts = {}
    owner_counts = {}
    owner_ready_coverage = make_owner_ready_coverage(rows)
    owner_ready_blocking_context = make_owner_ready_blocking_context(rows)
    for row in rows:
        identity_status = row.get("observed_source_identity", {}).get("identity_status", "unavailable")
        source_identity_counts[identity_status] = source_identity_counts.get(identity_status, 0) + 1
        owner = row.get("owner", "") or "<missing-owner>"
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
        ready_status, ready_items = owner_ready_state(row)
        summary_rows.append(
            {
                "worksheet_id": row["id"],
                "source_id": row["source_id"],
                "source_path": row["source_path"],
                "owner": row["owner"],
                "owner_route": row.get("owner_route", {}),
                "status": row["status"],
                "worksheet_status": row["worksheet_status"],
                "review_after": row["review_after"],
                "source_identity_status": identity_status,
                "required_owner_field_count": len(row["required_owner_fields"]),
                "allowed_owner_decisions": row["decision_options"],
                "active_exposure_count": len(row["active_registry_items"]),
                "owner_ready_package_status": ready_status,
                "owner_ready_package_count": len(ready_items),
                "owner_ready_packages": ready_items,
                "focus_command": (
                    "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh "
                    f"--source-id {row['source_id']} --owner {shlex_quote(row['owner'])} "
                    f"--worksheet-id {row['id']} --checklist --forms"
                ),
            }
        )
    return {
        "status": "needs-owner-review" if any(row["status"] == "open" for row in rows) else "ok",
        "read_only": True,
        "row_count": len(rows),
        "open_count": sum(1 for row in rows if row["status"] == "open"),
        "resolved_count": sum(1 for row in rows if row["status"] == "resolved"),
        "active_exposure_count": sum(len(row["active_registry_items"]) for row in rows),
        **owner_ready_coverage,
        **owner_ready_blocking_context,
        "source_identity_counts": dict(sorted(source_identity_counts.items())),
        "owner_counts": dict(sorted(owner_counts.items())),
        "owner_dispatch": make_owner_dispatch(rows),
        "rows": summary_rows,
        "notes_zh": "只读 owner gate 总览；用于人工分派和收口，不生成 owner decision，不写文件，不关闭门禁，不提升 active。",
    }

def shlex_quote(value):
    text = str(value)
    if not text:
        return "''"
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_@%+=:,./-"
    if all(char in safe_chars for char in text):
        return text
    return "'" + text.replace("'", "'\"'\"'") + "'"

def is_filled(value):
    return _is_filled(value)

def owner_decision_target_mismatch(owner_decision, target_decision):
    owner_decision = str(owner_decision or "")
    target_decision = str(target_decision or "")
    if target_decision.startswith("domains/projects/") or target_decision.startswith("domains/personal/"):
        return {
            "expected": "projects/<project>/...、notes/personal/... 或终止类字面目标",
            "reason_zh": "硬切换后 owner target 不再兼容 domains/projects 或 domains/personal 旧入口。",
        }
    if owner_decision == "archive-only":
        if target_decision == "archive-only" or "/archive/" in target_decision:
            return None
        return {
            "expected": ["archive-only", "target path containing /archive/"],
            "reason_zh": "archive-only 只能搭配 archive-only 字面目标或明确的 archive 路径，不能指向 current、validation 或 decisions 目标。",
        }
    terminal_targets = {
        "reference-only": {"reference-only"},
        "no-migration": {"no-migration"},
        "rejected": {"no-migration"},
    }
    if owner_decision in terminal_targets and target_decision not in terminal_targets[owner_decision]:
        return {
            "expected": sorted(terminal_targets[owner_decision]),
            "reason_zh": "终止类 owner_decision 只能搭配同语义的 target_decision，不能指向项目落地路径。",
        }
    if owner_decision not in terminal_targets and target_decision in {"reference-only", "no-migration"}:
        return {
            "expected": "与 owner_decision 成对兼容的落地目标",
            "reason_zh": "落地类 owner_decision 不能搭配 reference-only 或 no-migration 目标。",
        }
    return None

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
    diagnostics = []
    warnings = []
    forms = []
    def add_form_error(code, message, worksheet_id="", field="", actual="", expected="", action_zh="", line_no=None):
        form_errors.append(message)
        diagnostics.append(
            {
                "code": code,
                "severity": "error",
                "worksheet_id": worksheet_id,
                "field": field,
                "actual": actual,
                "expected": expected,
                "line_no": line_no,
                "message_zh": message,
                "action_zh": action_zh or "请按 owner worksheet 重新填写该字段后再运行 validate-forms。",
            }
        )
    def date_error_message(prefix, field, value):
        return f"{prefix}: {field} invalid date: {value}"
    def add_invalid_date(prefix, worksheet_id, field, value, line_no):
        add_form_error(
            "invalid-date",
            date_error_message(prefix, field, value),
            worksheet_id=worksheet_id,
            field=field,
            actual=str(value),
            expected="YYYY-MM-DD",
            line_no=line_no,
            action_zh="请使用 YYYY-MM-DD 格式填写日期字段。",
        )
    def is_valid_date(value):
        try:
            parts = str(value).split("-")
            if len(parts) != 3 or any(not part.isdigit() for part in parts):
                raise ValueError("not YYYY-MM-DD")
            year, month, day = (int(part) for part in parts)
            dt.date(year, month, day)
            return True
        except Exception:
            return False
    if not path.exists():
        add_form_error(
            "forms-file-missing",
            f"{path}: missing owner decision forms file",
            field="path",
            expected="existing-jsonl-file",
            action_zh="请先由人工 owner 提供 owner decision JSONL 文件。",
        )
    else:
        try:
            lines = path.read_text().splitlines()
        except Exception as exc:
            add_form_error("forms-file-unreadable", f"{path}: cannot read owner decision forms file: {exc}", field="path", actual=str(path), expected="readable-jsonl-file")
            lines = []
        for line_no, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                forms.append(json.loads(line))
            except Exception as exc:
                add_form_error("invalid-jsonl", f"{path}:{line_no}: invalid jsonl: {exc}", field="jsonl", actual=line[:200], expected="valid-json-object", line_no=line_no, action_zh="请修复该行 JSON 语法后再运行 validate-forms。")
    if not forms:
        add_form_error("forms-empty", f"{path}: no owner decision forms found", field="jsonl", expected="at-least-one-owner-decision-form")
    open_by_id = {row["id"]: row for row in rows if row["status"] == "open"}
    seen = set()
    for index, form in enumerate(forms, 1):
        prefix = f"{path}:{index}"
        worksheet_id = str(form.get("worksheet_id", ""))
        if not worksheet_id:
            add_form_error("missing-worksheet-id", f"{prefix}: missing worksheet_id", field="worksheet_id", expected="open-owner-gate-worksheet-id", line_no=index)
            continue
        if worksheet_id in seen:
            add_form_error("duplicate-worksheet-id", f"{prefix}: duplicate worksheet_id {worksheet_id}", worksheet_id=worksheet_id, field="worksheet_id", actual=worksheet_id, expected="unique-owner-gate-worksheet-id", line_no=index)
            continue
        seen.add(worksheet_id)
        row = open_by_id.get(worksheet_id)
        if not row:
            add_form_error("worksheet-not-open", f"{prefix}: worksheet_id {worksheet_id} does not match an open owner gate row", worksheet_id=worksheet_id, field="worksheet_id", actual=worksheet_id, expected="open-owner-gate-row", line_no=index)
            continue
        if form.get("source_id") != row["source_id"]:
            add_form_error("source-id-mismatch", f"{prefix}: source_id mismatch for {worksheet_id}", worksheet_id=worksheet_id, field="source_id", actual=str(form.get("source_id", "")), expected=row["source_id"], line_no=index)
        if form.get("source_path") != row["source_path"]:
            add_form_error("source-path-mismatch", f"{prefix}: source_path mismatch for {worksheet_id}", worksheet_id=worksheet_id, field="source_path", actual=str(form.get("source_path", "")), expected=row["source_path"], line_no=index)
        owner_decision = form.get("owner_decision", "")
        if not is_filled(owner_decision):
            add_form_error("missing-owner-decision", f"{prefix}: missing owner_decision", worksheet_id=worksheet_id, field="owner_decision", expected="one-of-decision_options", line_no=index)
        elif row["decision_options"] and owner_decision not in row["decision_options"]:
            add_form_error(
                "owner-decision-not-allowed",
                f"{prefix}: owner_decision {owner_decision!r} is not in allowed decisions {row['decision_options']}",
                worksheet_id=worksheet_id,
                field="owner_decision",
                actual=str(owner_decision),
                expected=row["decision_options"],
                line_no=index,
            )
        target_decision = form.get("target_decision", "")
        if is_filled(target_decision) and row.get("target_candidates") and target_decision not in row["target_candidates"]:
            add_form_error(
                "target-decision-not-candidate",
                f"{prefix}: target_decision {target_decision!r} is not in target candidates {row['target_candidates']}",
                worksheet_id=worksheet_id,
                field="target_decision",
                actual=str(target_decision),
                expected=row["target_candidates"],
                line_no=index,
            )
        if is_filled(owner_decision) and is_filled(target_decision):
            mismatch = owner_decision_target_mismatch(owner_decision, target_decision)
            if mismatch:
                add_form_error(
                    "owner-decision-target-mismatch",
                    f"{prefix}: owner_decision {owner_decision!r} is not compatible with target_decision {target_decision!r}: {mismatch['reason_zh']}",
                    worksheet_id=worksheet_id,
                    field="target_decision",
                    actual={"owner_decision": owner_decision, "target_decision": target_decision},
                    expected=mismatch["expected"],
                    line_no=index,
                    action_zh="请保持 owner_decision 与 target_decision 成对一致；不要使用旧 domains/projects/domains/personal 入口，也不要把 reference-only/no-migration 与项目落地路径混用。",
                )
        for field in row["required_owner_fields"]:
            if not is_filled(form.get(field)):
                add_form_error("missing-required-owner-field", f"{prefix}: missing required field {field}", worksheet_id=worksheet_id, field=field, expected="filled-owner-field", line_no=index)
        for field in ["target_decision", "reviewed_by", "reviewed_at", "review_after", "source_status", "evidence_refs", "status_reason"]:
            if not is_filled(form.get(field)):
                add_form_error("missing-required-review-field", f"{prefix}: missing required review field {field}", worksheet_id=worksheet_id, field=field, expected="filled-review-field", line_no=index)
        owner_route = row.get("owner_route", {})
        routing_status = str(owner_route.get("routing_status", ""))
        routing_owner = str(owner_route.get("routing_owner", ""))
        reviewed_by = str(form.get("reviewed_by", ""))
        if (
            routing_status == "needs-human-assignment"
            and routing_owner
            and reviewed_by == routing_owner
        ):
            add_form_error(
                "reviewed-by-routing-owner",
                f"{prefix}: reviewed_by must be a real owner, not routing_owner {routing_owner!r} for {worksheet_id}",
                worksheet_id=worksheet_id,
                field="reviewed_by",
                actual=reviewed_by,
                expected="real-human-owner",
                line_no=index,
                action_zh="reviewed_by 必须由真实人工 owner 填写，不能使用路由占位 owner。",
            )
        if is_filled(form.get("reviewed_at")):
            if not is_valid_date(form.get("reviewed_at")):
                add_invalid_date(prefix, worksheet_id, "reviewed_at", form.get("reviewed_at"), index)
        if is_filled(form.get("review_after")):
            if not is_valid_date(form.get("review_after")):
                add_invalid_date(prefix, worksheet_id, "review_after", form.get("review_after"), index)
        identity = row.get("observed_source_identity", {})
        identity_status = str(identity.get("identity_status", "unavailable"))
        if identity_status != "match":
            add_form_error("source-identity-not-match", f"{prefix}: observed source identity is {identity_status}, expected match before owner landing", worksheet_id=worksheet_id, field="observed_source_identity", actual=identity_status, expected="match", line_no=index)
        else:
            observed_sha256 = str(identity.get("observed_sha256", ""))
            observed_size = str(identity.get("observed_size", ""))
            if observed_sha256 and str(form.get("source_sha256", "")) != observed_sha256:
                add_form_error("source-sha256-mismatch", f"{prefix}: source_sha256 does not match observed source identity for {worksheet_id}", worksheet_id=worksheet_id, field="source_sha256", actual=str(form.get("source_sha256", "")), expected=observed_sha256, line_no=index)
            if observed_size and str(form.get("source_size", "")) != observed_size:
                add_form_error("source-size-mismatch", f"{prefix}: source_size does not match observed source identity for {worksheet_id}", worksheet_id=worksheet_id, field="source_size", actual=str(form.get("source_size", "")), expected=observed_size, line_no=index)
        if "must_not" in form and form.get("must_not") != row["must_not"]:
            add_form_error("must-not-tampered", f"{prefix}: must_not differs from worksheet guardrails", worksheet_id=worksheet_id, field="must_not", actual=form.get("must_not", ""), expected=row["must_not"], line_no=index, action_zh="请恢复 worksheet 原始 guardrails；owner 表单不得修改 must_not。")
        if "allowed_owner_decisions" in form and form.get("allowed_owner_decisions") != row["decision_options"]:
            add_form_error("allowed-decisions-tampered", f"{prefix}: allowed_owner_decisions differs from worksheet decision options", worksheet_id=worksheet_id, field="allowed_owner_decisions", actual=form.get("allowed_owner_decisions", ""), expected=row["decision_options"], line_no=index, action_zh="请恢复 worksheet 原始 decision options；owner 表单不得修改 allowed_owner_decisions。")
        if "target_candidates" in form and form.get("target_candidates") != row["target_candidates"]:
            add_form_error("target-candidates-tampered", f"{prefix}: target_candidates differs from worksheet target candidates", worksheet_id=worksheet_id, field="target_candidates", actual=form.get("target_candidates", ""), expected=row["target_candidates"], line_no=index, action_zh="请恢复 worksheet 原始 target candidates；owner 表单不得修改 target_candidates。")
    submitted_open_ids = sorted(worksheet_id for worksheet_id in seen if worksheet_id in open_by_id)
    missing_open_ids = sorted(worksheet_id for worksheet_id in open_by_id if worksheet_id not in seen)
    if len(open_by_id) <= 1:
        coverage_status = "single-worksheet"
    elif missing_open_ids:
        coverage_status = "partial"
    else:
        coverage_status = "complete"
    coverage = {
        "filtered_open_count": len(open_by_id),
        "submitted_form_count": len(forms),
        "submitted_open_count": len(submitted_open_ids),
        "submitted_worksheet_ids": submitted_open_ids,
        "missing_open_worksheet_ids": missing_open_ids,
        "coverage_status": coverage_status,
        "notes_zh": "本字段只说明 validate-forms 覆盖了当前过滤范围内哪些 open worksheet；partial 不阻断分批签收，但 landing 后仍需继续处理 missing_open_worksheet_ids。",
    }
    if missing_open_ids:
        warnings.append(
            "validate-forms covers a subset of current open owner gates; remaining open worksheets: "
            + ", ".join(missing_open_ids)
        )
    status = "pass" if not form_errors else "fail"
    return {
        "status": status,
        "path": str(path),
        "form_count": len(forms),
        "checked_count": len(seen),
        "coverage": coverage,
        "filtered_open_count": coverage["filtered_open_count"],
        "submitted_form_count": coverage["submitted_form_count"],
        "submitted_worksheet_ids": coverage["submitted_worksheet_ids"],
        "missing_open_worksheet_ids": coverage["missing_open_worksheet_ids"],
        "coverage_status": coverage["coverage_status"],
        "forms": forms,
        "error_count": len(form_errors),
        "warning_count": len(warnings),
        "errors": form_errors,
        "warnings": warnings,
        "diagnostics": diagnostics,
    }

def owner_ready_landing_errors(form_validation, rows):
    open_by_id = {row["id"]: row for row in rows if row["status"] == "open"}
    owner_ready_errors = []
    if form_validation and form_validation.get("status") == "pass":
        for form in form_validation.get("forms", []):
            worksheet_id = str(form.get("worksheet_id", ""))
            row = open_by_id.get(worksheet_id)
            if not row:
                continue
            ready_status, ready_packages = owner_ready_state(row)
            if ready_status != "covered":
                owner_ready_errors.append(
                    {
                        "worksheet_id": worksheet_id,
                        "source_id": row.get("source_id", ""),
                        "source_path": row.get("source_path", ""),
                        "owner_ready_package_status": ready_status,
                        "owner_ready_packages": ready_packages,
                    }
                )
    return owner_ready_errors

def required_manual_files_for_forms(form_validation, rows):
    open_by_id = {row["id"]: row for row in rows if row["status"] == "open"}
    worksheet_files = []
    if form_validation:
        for form in form_validation.get("forms", []):
            row = open_by_id.get(str(form.get("worksheet_id", "")))
            worksheet = str(row.get("worksheet", "")) if row else ""
            if worksheet and worksheet not in worksheet_files:
                worksheet_files.append(worksheet)
    if not worksheet_files:
        worksheet_files = ["artifacts/manifests/*owner-decision-worksheets-*.jsonl"]
    return [
        "artifacts/manifests/<owner-decision-landing-YYYYMMDD>.jsonl",
        *sorted(worksheet_files),
        "registry/items.jsonl",
        "indexes/by-owner.md",
        "indexes/by-project.md",
        "indexes/by-review-date.md",
        "indexes/by-source.md",
        "indexes/by-status.md",
        "indexes/by-topic.md",
        "indexes/by-decision.md",
    ]

def make_landing_plan(form_validation, rows):
    open_by_id = {row["id"]: row for row in rows if row["status"] == "open"}
    blocked = form_validation is None or form_validation.get("status") != "pass"
    owner_ready_errors = owner_ready_landing_errors(form_validation, rows)
    if owner_ready_errors:
        blocked = True
    reason = ""
    if form_validation is None or form_validation.get("status") != "pass":
        reason = "form validation must pass before landing plan is usable"
    elif owner_ready_errors:
        reason = "owner-ready package strong validation must be covered before landing plan is usable"
    plan = {
        "status": "blocked" if blocked else "planned",
        "read_only": True,
        "source_form": form_validation.get("path", "") if form_validation else "",
        "reason": reason,
        "landing_scope": form_validation.get("coverage", {}) if form_validation else {},
        "remaining_open_after_this_batch": (
            form_validation.get("coverage", {}).get("missing_open_worksheet_ids", [])
            if form_validation else []
        ),
        "owner_ready_gate": {
            "status": "blocked" if owner_ready_errors else "pass",
            "error_count": len(owner_ready_errors),
            "errors": owner_ready_errors,
            "notes_zh": "owner-ready package 只表示可交给 owner 签收；landing plan 仍不生成 owner decision、不关闭 gate、不写文件。",
        },
        "steps": [],
        "required_manual_files": required_manual_files_for_forms(form_validation, rows),
        "verification_commands": [
            "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
            "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json",
            "rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json",
        ],
        "must_not": [
            "do not treat this plan as owner approval",
            "do not auto-edit registry/index",
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
                "owner_ready_package_status": owner_ready_state(row)[0] if row else "",
                "owner_ready_packages": owner_ready_state(row)[1] if row else [],
                "worksheet_verification_cwd": row.get("verification_cwd", ""),
                "worksheet_verification_commands": row.get("verification_commands", []),
                "manual_actions_zh": [
                    "把已审 owner decision 追加到 owner decision landing JSONL 制品。",
                    "按 target_decision 更新或新增对应 registry item，状态不得越过 owner 决策允许范围。",
                    "同步 by-project、by-status、by-owner、by-review-date、by-topic、by-source 和 by-decision 索引。",
                    "按 worksheet_verification_commands 复核项目侧或 Knowledge Hub 侧证据；无法运行的命令必须记录原因。",
                    "运行 verification_commands 中的命令；strict gate 只有所有 owner gates 闭环后才会返回 0。",
                ],
                "guardrails": row.get("must_not", []),
            }
        )
    return plan

def make_landing_audit(form_validation, rows, blocked, owner_ready_errors):
    open_by_id = {row["id"]: row for row in rows if row["status"] == "open"}
    forms = form_validation.get("forms", []) if form_validation else []
    audit_rows = []
    for form in forms:
        worksheet_id = str(form.get("worksheet_id", ""))
        row = open_by_id.get(worksheet_id, {})
        worksheet_file = row.get("worksheet", "artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl")
        required_fields = []
        for field in list(row.get("required_owner_fields", [])) + [
            "owner_decision",
            "target_decision",
            "reviewed_by",
            "reviewed_at",
            "review_after",
            "source_status",
            "evidence_refs",
            "status_reason",
        ]:
            if field not in required_fields:
                required_fields.append(field)
        missing_fields = [field for field in required_fields if not is_filled(form.get(field))]
        row_status = "blocked" if blocked or missing_fields or not row else "ready-for-manual-landing"
        audit_rows.append(
            {
                "worksheet_id": worksheet_id,
                "source_id": form.get("source_id", ""),
                "source_path": form.get("source_path", ""),
                "status": row_status,
                "worksheet_resolution_status": {
                    "current_status": row.get("status", "missing-open-row"),
                    "worksheet_file": worksheet_file,
                    "must_update_worksheet_row": bool(row),
                    "required_resolution_state_hint": "设置 worksheet_status/row_status/status/default_state 中至少一个为 resolved、owner-approved、approved 或 closed，并保留完整 owner 字段。",
                    "required_fields": required_fields,
                    "missing_fields_in_form": missing_fields,
                    "notes_zh": "worksheet 是否关闭由 worksheet 行和必填 owner 字段共同决定；landing plan 不会自动改 worksheet 或关闭 gate。",
                },
                "expected_manual_deltas": {
                    "landing_jsonl": "追加已人工签收的 owner decision JSONL；保留 reviewed_by、reviewed_at、source_sha256/source_size、evidence_refs 和 status_reason。",
                    "worksheet_jsonl": "把对应 worksheet 行更新为已签收状态，并写入同一组 owner decision 字段；不得由工具代签。",
                    "registry_items": "按 target_decision 更新或新增 registry item，状态不得越过 owner 决策允许范围。",
                    "registry_source_policy": "记录 owner-gated 到目标状态的人工迁移/引用/归档决策。",
                    "indexes": [
                        "indexes/by-owner.md",
                        "indexes/by-project.md",
                        "indexes/by-review-date.md",
                        "indexes/by-source.md",
                        "indexes/by-status.md",
                        "indexes/by-topic.md",
                        "indexes/by-decision.md",
                    ],
                },
                "post_landing_commands": [
                    "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json",
                    "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
                    "rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json",
                    "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json",
                ],
                "must_not": [
                    "不得把本 audit 当作 owner approval",
                    "不得自动写 worksheet、registry、source policy 或 index",
                    "不得关闭未签收 owner gate",
                    "不得把 project-specific 内容提升为团队标准",
                ],
            }
        )
    return {
        "status": "blocked" if blocked else "ready-for-manual-landing" if audit_rows else "empty",
        "read_only": True,
        "row_count": len(audit_rows),
        "landing_scope": form_validation.get("coverage", {}) if form_validation else {},
        "remaining_open_after_this_batch": (
            form_validation.get("coverage", {}).get("missing_open_worksheet_ids", [])
            if form_validation else []
        ),
        "owner_ready_error_count": len(owner_ready_errors),
        "required_manual_files": required_manual_files_for_forms(form_validation, rows),
        "rows": audit_rows,
        "notes_zh": "landing_audit 只描述人工落点和复核命令，避免 owner JSONL 合法但 worksheet 仍 open；不写文件、不生成 owner decision、不关闭 gate。",
    }

sources_payload = load_json(root / "registry" / "sources.json")
sources_rows = list(sources_payload.get("sources", [])) + load_jsonl(root / "registry" / "retired-sources.jsonl")
source_roots = {
    str(source.get("id", "")): str(source.get("path", ""))
    for source in sources_rows
    if isinstance(source, dict)
}

owner_routing_payload = load_json(root / "registry" / "owner-routing.json")
owner_route_map = {}
for route in owner_routing_payload.get("routes", []):
    key = (str(route.get("source_id", "")), str(route.get("decision_owner_role", "")))
    if key == ("", ""):
        continue
    owner_route_map[key] = {
        "decision_owner_role": str(route.get("decision_owner_role", "")),
        "source_id": str(route.get("source_id", "")),
        "routing_status": str(route.get("routing_status", "")),
        "routing_owner": str(route.get("routing_owner", "")),
        "candidate_registry_owners": route.get("candidate_registry_owners", []),
        "required_real_owner_zh": str(route.get("required_real_owner_zh", "")),
        "escalation_zh": str(route.get("escalation_zh", "")),
        "must_not": route.get("must_not", []),
        "notes_zh": str(route.get("notes_zh", "")),
        "no_owner_decision_generated": True,
    }

def owner_route_for(source_id, owner_role):
    route = owner_route_map.get((source_id, owner_role), {})
    if route:
        return route
    return {
        "decision_owner_role": owner_role,
        "source_id": source_id,
        "routing_status": "unmapped",
        "routing_owner": "",
        "candidate_registry_owners": [],
        "required_real_owner_zh": "缺少 owner-routing.json 路由；需要人工补充分派责任人后再签收。",
        "escalation_zh": "保持 owner gate open，不得代签。",
        "must_not": ["不得把 unmapped owner role 当作已签收"],
        "notes_zh": "只读缺省路由；不生成 owner decision，不关闭 gate。",
        "no_owner_decision_generated": True,
    }

def source_execution_root(source_id):
    source_root = str(source_roots.get(source_id, "") or "")
    if not source_root:
        return ""
    path = pathlib.Path(source_root).expanduser()
    if source_id == "pcr02-project-docs" and path.name == "docs":
        return _display_path(path.parent)
    return _display_path(path)

def effective_verification_commands(row, source_id):
    commands = list(row.get("verification_commands", []))
    execution_root = source_execution_root(source_id)
    required_fields = set(row.get("required_owner_fields", []))
    if execution_root and (
        "commit_branch_dirty_state_evidence" in required_fields
        or "final_branch_commit_or_tag_refs" in required_fields
    ):
        git_status_command = f"rtk git -C {execution_root} status --short --branch"
        git_head_command = f"rtk git -C {execution_root} rev-parse HEAD"
        if git_status_command not in commands:
            commands.append(git_status_command)
        if git_head_command not in commands:
            commands.append(git_head_command)
    return commands

items = load_jsonl(root / "registry" / "items.jsonl")
items_by_source_path = {}
active_by_source_path = {}
for item in items:
    source = item.get("source") if isinstance(item.get("source"), dict) else {}
    source_id = source.get("source_id")
    source_paths = source_path_values(source.get("source_path"))
    if not source_id or not source_paths:
        continue
    item_ref = {
        "id": item.get("id", ""),
        "kind": item.get("kind", ""),
        "status": item.get("status", ""),
        "path": item.get("path", ""),
        "review_status": item.get("review_status", ""),
        "tags": item.get("tags", []),
        "source": source,
    }
    for source_path in source_paths:
        key = (source_id, source_path)
        items_by_source_path.setdefault(key, []).append(item_ref)
        if item.get("status") == "active":
            active_by_source_path.setdefault(key, []).append(item_ref)

worksheet_paths = sorted((root / "artifacts" / "manifests").glob("*owner-decision-worksheets-*.jsonl"))
if not worksheet_paths:
    errors.append("missing artifacts/manifests/*owner-decision-worksheets-*.jsonl")

intake_paths = sorted((root / "artifacts" / "manifests").glob("*owner-intake-package-*.jsonl"))
intake_by_worksheet = {}
intake_by_source_path = {}
for intake_path in intake_paths:
    for intake in load_jsonl(intake_path):
        worksheet_id = str(intake.get("next_worksheet", ""))
        if worksheet_id:
            intake_by_worksheet[worksheet_id] = intake
        for source_path in source_path_values(intake.get("source_path", "")):
            intake_by_source_path[source_path] = intake

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
        owner = row.get("owner_required") or row.get("owner_candidate") or ""
        if args.owner and owner != args.owner:
            continue
        key = (source_id, source_path)
        resolved = is_resolved(row)
        row_status = "resolved" if resolved else "open"
        if args.status != "all" and row_status != args.status:
            continue
        intake = intake_by_worksheet.get(row_id) or intake_by_source_path.get(source_path, {})
        execution_root = source_execution_root(source_id)
        row_entry = {
            "id": row_id,
            "source_id": source_id,
            "source_path": source_path,
            "owner": owner,
            "owner_route": owner_route_for(source_id, owner),
            "status": row_status,
            "worksheet_status": row.get("worksheet_status") or row.get("status") or row.get("default_state") or "",
            "decision_options": row.get("decision_options", []),
            "target_candidates": row.get("target_candidates", []),
            "required_owner_fields": row.get("required_owner_fields", []),
            "must_not": row.get("must_not", []),
            "review_after": row.get("review_after", ""),
            "worksheet": str(worksheet_path.relative_to(root)),
            "registry_items": items_by_source_path.get(key, []),
            "active_registry_items": active_by_source_path.get(key, []),
            "source_execution_root": execution_root,
            "verification_cwd": execution_root,
            "verification_commands": effective_verification_commands(row, source_id),
            "owner_question_zh": intake.get("owner_question_zh", ""),
            "default_state": intake.get("default_state", ""),
            "allowed_next_status": intake.get("allowed_next_status", []),
            "hard_gate_summary": intake.get("hard_gate_summary", ""),
            "hard_gate": intake.get("hard_gate", ""),
            "observed_source_identity": compute_source_identity(row),
        }
        ready_status, ready_packages = owner_ready_state(row_entry)
        row_entry["owner_ready_package_status"] = ready_status
        row_entry["owner_ready_package_status_source"] = "knowledge-owner-gates.owner_ready_state"
        row_entry["owner_ready_strong_validation"] = True
        row_entry["owner_ready_package_count"] = len(ready_packages)
        row_entry["owner_ready_packages"] = ready_packages
        row_entry["owner_ready_package_ids"] = [
            str(item.get("id", ""))
            for item in ready_packages
            if isinstance(item, dict) and item.get("id")
        ]
        row_entry["owner_ready_package_paths"] = [
            str(item.get("path", ""))
            for item in ready_packages
            if isinstance(item, dict) and item.get("path")
        ]
        rows.append(row_entry)

if args.next_open and not errors:
    rows = sorted(
        [row for row in rows if row["status"] == "open"],
        key=lambda row: (
            str(row.get("review_after", "") or "9999-12-31"),
            str(row.get("id", "")),
        ),
    )[:1]

open_count = sum(1 for row in rows if row["status"] == "open")
resolved_count = sum(1 for row in rows if row["status"] == "resolved")
active_exposure_count = sum(len(row["active_registry_items"]) for row in rows)
owner_ready_coverage = make_owner_ready_coverage(rows)
owner_ready_blocking_context = make_owner_ready_blocking_context(rows)
owner_review_status = "needs-owner-review" if open_count else "complete"
owner_gate_status = "owner-gates-open" if open_count else "owner-gates-complete"
result_status = "blocked" if errors else "needs-fix" if active_exposure_count else "ok"
exit_status = 1 if errors or active_exposure_count else 0

result = {
    "status": result_status,
    "status_scope": "tool-health",
    "owner_review_status": owner_review_status,
    "owner_gate_status": owner_gate_status,
    "root": _display_path(root),
    "read_only": True,
    "source_id": args.source_id,
    "owner": args.owner,
    "worksheet_id": args.worksheet_id,
    "next_open": args.next_open,
    "filter_status": args.status,
    "source_identity_read_policy": {
        "source_identity_read_mode": "read-bytes-for-hash",
        "source_body_read_for_hash": True,
        "source_body_copied": False,
        "source_project_written": False,
        "owner_gate_mutation": False,
        "notes_zh": "owner-gates 为 source identity/hash 匹配会只读读取 source 文件字节；不会复制 source 正文、不会写源项目、不会生成 owner decision、不会关闭 gate。",
    },
    "worksheet_count": len(worksheet_paths),
    "row_count": len(rows),
    "open_count": open_count,
    "resolved_count": resolved_count,
    "active_exposure_count": active_exposure_count,
    **owner_ready_coverage,
    **owner_ready_blocking_context,
    "errors": errors,
    "rows": rows,
}

if args.summary:
    result["owner_summary"] = make_owner_summary(rows)

if args.forms:
    result["decision_forms"] = [make_decision_form(row) for row in rows if row["status"] == "open"]

if args.evidence_readiness:
    result["evidence_readiness"] = make_evidence_readiness([row for row in rows if row["status"] == "open"])

if args.owner_inbox:
    result["owner_inbox"] = make_owner_inbox([row for row in rows if row["status"] == "open"])

if args.handoff_packet:
    result["owner_handoff_packets"] = make_owner_handoff_packets(rows)

if args.checklist:
    result["owner_checklists"] = [make_owner_checklist(row) for row in rows if row["status"] == "open"]

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

landing_audit = None
if args.landing_audit:
    if not args.validate_forms:
        landing_audit = {
            "status": "blocked",
            "read_only": True,
            "reason": "--landing-audit requires --validate-forms <jsonl>",
            "rows": [],
        }
        result["landing_audit"] = landing_audit
        result_status = "needs-fix"
        result["status"] = result_status
        exit_status = 1
    else:
        audit_blocked = form_validation is None or form_validation.get("status") != "pass"
        owner_ready_errors = owner_ready_landing_errors(form_validation, rows)
        if owner_ready_errors:
            audit_blocked = True
        landing_audit = make_landing_audit(form_validation, rows, audit_blocked, owner_ready_errors)
        result["landing_audit"] = landing_audit
        if landing_audit.get("status") == "blocked":
            result_status = "needs-fix"
            result["status"] = result_status
            exit_status = 1

if args.forms_jsonl:
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(exit_status)
    if active_exposure_count:
        print("ERROR: active exposure exists; owner-gated rows must stay out of active until owner decisions are closed.", file=sys.stderr)
        sys.exit(exit_status)
    forms_jsonl_rows = [row for row in rows if row["status"] == "open"]
    if not forms_jsonl_rows and (args.source_id or args.owner or args.worksheet_id):
        hint_source_id = args.source_id or "<source-id>"
        print("WARNING: no open owner decision forms matched the current filters.", file=sys.stderr)
        print(f"WARNING: matched_row_count={len(rows)} matched_open_count=0", file=sys.stderr)
        print(f"WARNING: hint_command=rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id {hint_source_id} --summary --json", file=sys.stderr)
    for form in [make_decision_form(row) for row in forms_jsonl_rows]:
        print(json.dumps(form, ensure_ascii=False, separators=(",", ":")))
    sys.exit(exit_status)

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
print(f"- owner-ready packages: {owner_ready_coverage['owner_ready_package_coverage']}")
print(f"- owner-ready missing: {owner_ready_coverage['owner_ready_missing_count']}")
print(f"- owner-ready invalid: {owner_ready_coverage['owner_ready_invalid_count']}")
print(f"- owner-ready duplicate: {owner_ready_coverage['owner_ready_duplicate_count']}")
print(f"- owner-ready blocking status: {owner_ready_blocking_context['owner_ready_blocking_status']}")
print(f"- owner-ready note: {owner_ready_blocking_context['owner_ready_status_note_zh']}")
if args.source_id:
    print(f"- source_id: {args.source_id}")
if args.owner:
    print(f"- owner: {args.owner}")
print(f"- filter: {args.status}")
for error in errors:
    print(f"- ERROR: {error}")
if active_exposure_count:
    print("- ERROR: active exposure exists; run knowledge-check and keep owner-gated rows out of active until owner decisions are closed.")

if args.summary:
    summary = make_owner_summary(rows)
    print()
    print("## Owner Gate Summary")
    print()
    print("本摘要只读输出 owner gate 总览，供人工分派、排期和收口；不生成 owner decision，不写文件、不关闭门禁、不提升 active。")
    print(f"- summary_status: {summary['status']}")
    print(f"- rows: {summary['row_count']}")
    print(f"- open: {summary['open_count']}")
    print(f"- resolved: {summary['resolved_count']}")
    print(f"- active_exposure: {summary['active_exposure_count']}")
    print(f"- owner_ready_packages: {summary['owner_ready_package_count']}/{summary['row_count']}")
    print(f"- owner_ready_missing: {summary['owner_ready_missing_count']}")
    if summary["source_identity_counts"]:
        identity_parts = [f"{key}={value}" for key, value in summary["source_identity_counts"].items()]
        print(f"- source_identity: {', '.join(identity_parts)}")
    if summary["owner_counts"]:
        owner_parts = [f"{key}={value}" for key, value in summary["owner_counts"].items()]
        print(f"- owners: {', '.join(owner_parts)}")
    routed = [
        f"{item['owner']}=>{item.get('owner_route', {}).get('routing_owner', '<unmapped>') or '<unmapped>'}"
        for item in summary["owner_dispatch"]
    ]
    if routed:
        print(f"- owner_routes: {', '.join(routed)}")
    print()
    print("### Owner Dispatch")
    print()
    print("| owner | route | open | evidence readiness | forms-jsonl | validate | landing plan | landing audit | next focus |")
    print("|---|---|---:|---|---|---|---|---|---|")
    for item in summary["owner_dispatch"]:
        route = item.get("owner_route", {})
        route_text = route.get("routing_owner") or route.get("routing_status") or "<unmapped>"
        print(
            f"| {item['owner']} | {route_text} | {item['open_count']} | "
            f"`{item['evidence_readiness_command']}` | `{item['forms_jsonl_command']}` | `{item['validate_forms_command_template']}` | "
            f"`{item['landing_plan_command_template']}` | `{item['landing_audit_command_template']}` | `{item['next_focus_command']}` |"
        )
    print()
    print("| worksheet | source path | owner | identity | owner-ready | required fields | focus command |")
    print("|---|---|---|---|---|---:|---|")
    for item in summary["rows"]:
        print(
            f"| `{item['worksheet_id']}` | `{item['source_path']}` | "
            f"{item['owner'] or '<missing-owner>'} | {item['source_identity_status']} | "
            f"{item['owner_ready_package_status']} | {item['required_owner_field_count']} | `{item['focus_command']}` |"
        )

if args.owner_inbox:
    inbox = make_owner_inbox([row for row in rows if row["status"] == "open"])
    print()
    print("## Owner Inbox")
    print()
    print("本视图只读汇总 owner 待办，不生成 owner decision，不写文件，不关闭 gate。")
    print(f"- inbox_status: {inbox['status']}")
    print(f"- rows: {inbox['row_count']}")
    if inbox["owner_counts"]:
        owner_parts = [f"{key}={value}" for key, value in inbox["owner_counts"].items()]
        print(f"- owners: {', '.join(owner_parts)}")
    print()
    print("| worksheet | owner | route | source path | fields | owner-ready | focus |")
    print("|---|---|---|---|---:|---|---|")
    for item in inbox["rows"]:
        route = item.get("owner_route", {})
        route_text = route.get("routing_owner") or route.get("routing_status") or "<unmapped>"
        fields = item.get("required_field_groups", {}).get("field_count", 0)
        print(
            f"| `{item['worksheet_id']}` | {item['owner']} | {route_text} | "
            f"`{item['source_path']}` | {fields} | {item['owner_ready_package_status']} | "
            f"`{item['commands']['focus_command']}` |"
        )
    print()
    print("### 字段分组和只读候选")
    print()
    for item in inbox["rows"]:
        groups = item.get("required_field_groups", {})
        prefill = item.get("read_only_prefill_candidates", {})
        manual = ", ".join(groups.get("manual_decision_fields", [])[:8]) or "-"
        candidates = ", ".join(groups.get("copyable_candidate_fields", [])[:8]) or "-"
        evidence = ", ".join(groups.get("evidence_fields", [])[:8]) or "-"
        candidate_keys = [
            key
            for key in ["source_sha256_candidate", "source_size_candidate", "review_after_candidate"]
            if prefill.get(key)
        ]
        candidate_text = ", ".join(candidate_keys) or "-"
        print(f"- `{item['worksheet_id']}`: manual=`{manual}`; candidates=`{candidates}`; evidence=`{evidence}`; read_only_prefill=`{candidate_text}`")
        print(f"  - forms-jsonl: `{item['commands']['forms_jsonl_command']}`")
        print(f"  - evidence-readiness: `{item['commands']['evidence_readiness_command']}`")
        print(f"  - validate template: `{item['commands']['validate_forms_command_template']}`")
    print()
    print("### 使用边界")
    print()
    print("- routing_owner 只是分派提示，不能填入 reviewed_by。")
    print("- source_sha256/source_size/review_after 只是候选值，必须由真实 owner 人工签收。")
    print("- validate / landing plan / landing audit 都是只读命令；人工落地前不得关闭 owner gate。")

if form_validation:
    print()
    print("## Owner Decision Form Validation")
    print()
    print("本校验只读检查 owner 回填 JSONL，不写文件、不关闭门禁、不提升 active。")
    print(f"- status: {form_validation['status']}")
    print(f"- forms: {form_validation['form_count']}")
    print(f"- checked: {form_validation['checked_count']}")
    print(f"- coverage_status: {form_validation['coverage_status']}")
    print(f"- filtered_open_count: {form_validation['filtered_open_count']}")
    print(f"- missing_open_worksheet_ids: {', '.join(form_validation['missing_open_worksheet_ids']) or '-'}")
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
    if landing_plan.get("landing_scope"):
        scope = landing_plan["landing_scope"]
        print(f"- landing_scope: {scope.get('coverage_status', '<missing>')} submitted={scope.get('submitted_open_count', 0)}/{scope.get('filtered_open_count', 0)}")
        print(f"- remaining_open_after_this_batch: {', '.join(landing_plan.get('remaining_open_after_this_batch', [])) or '-'}")
    owner_ready_gate = landing_plan.get("owner_ready_gate", {})
    if owner_ready_gate:
        print(f"- owner_ready_gate: {owner_ready_gate.get('status', '<missing-status>')}")
        print(f"- owner_ready_gate_errors: {owner_ready_gate.get('error_count', 0)}")
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
        if step.get("worksheet_verification_commands"):
            print("- worksheet_verification_commands:")
            for command in step["worksheet_verification_commands"]:
                print(f"  - `{command}`")

if landing_audit:
    print()
    print("## Owner Decision Landing Audit")
    print()
    print("本审计只读列出人工落地后必须核对的 worksheet、registry、source policy 和 index 变化；不写文件、不关闭门禁。")
    print(f"- status: {landing_audit['status']}")
    print(f"- rows: {landing_audit['row_count']}")
    if landing_audit.get("landing_scope"):
        scope = landing_audit["landing_scope"]
        print(f"- landing_scope: {scope.get('coverage_status', '<missing>')} submitted={scope.get('submitted_open_count', 0)}/{scope.get('filtered_open_count', 0)}")
        print(f"- remaining_open_after_this_batch: {', '.join(landing_audit.get('remaining_open_after_this_batch', [])) or '-'}")
    print(f"- owner_ready_errors: {landing_audit['owner_ready_error_count']}")
    if landing_audit.get("required_manual_files"):
        print("- required_manual_files:")
        for item in landing_audit["required_manual_files"]:
            print(f"  - `{item}`")
    for row in landing_audit.get("rows", []):
        print()
        print(f"### {row['worksheet_id']}")
        print(f"- source_path: `{row['source_path']}`")
        print(f"- audit_status: {row['status']}")
        worksheet_resolution = row.get("worksheet_resolution_status", {})
        print(f"- worksheet_file: `{worksheet_resolution.get('worksheet_file', '')}`")
        print(f"- must_update_worksheet_row: {worksheet_resolution.get('must_update_worksheet_row', False)}")
        if worksheet_resolution.get("missing_fields_in_form"):
            print(f"- missing_fields_in_form: {', '.join(worksheet_resolution['missing_fields_in_form'])}")
        deltas = row.get("expected_manual_deltas", {})
        if deltas:
            print("- expected_manual_deltas:")
            for key, value in deltas.items():
                if isinstance(value, list):
                    print(f"  - {key}: {', '.join(value)}")
                else:
                    print(f"  - {key}: {value}")
        if row.get("post_landing_commands"):
            print("- post_landing_commands:")
            for command in row["post_landing_commands"]:
                print(f"  - `{command}`")

if args.evidence_readiness:
    readiness = make_evidence_readiness([row for row in rows if row["status"] == "open"])
    print()
    print("## Owner Evidence Readiness")
    print()
    print("本视图只读展示 owner 签收前的候选证据和值，不写正式字段、不关闭门禁。")
    print(f"- status: {readiness['status']}")
    print(f"- rows: {readiness['row_count']}")
    if readiness["status_counts"]:
        parts = [f"{key}={value}" for key, value in readiness["status_counts"].items()]
        print(f"- status_counts: {', '.join(parts)}")
    for item in readiness["rows"]:
        print()
        print(f"### {item['worksheet_id']}")
        print(f"- source_path: `{item['source_path']}`")
        print(f"- owner: {item['owner'] or '<missing-owner>'}")
        print(f"- readiness_status: {item['readiness_status']}")
        print(f"- source_identity_status: {item['source_identity_status']}")
        print(f"- owner_ready_package_status: {item['owner_ready_package_status']}")
        if item["mechanical_known_fields"]:
            print(f"- mechanical_known_fields: {', '.join(item['mechanical_known_fields'])}")
        if item["owner_answer_required_fields"]:
            print(f"- owner_answer_required_fields: {', '.join(item['owner_answer_required_fields'])}")
        if item["command_evidence_required_fields"]:
            print(f"- command_evidence_required_fields: {', '.join(item['command_evidence_required_fields'])}")
        if item["owner_ready_evidence_refs"]:
            print("- owner_ready_evidence_refs:")
            for ref in item["owner_ready_evidence_refs"]:
                print(f"  - `{ref}`")
        if item["safe_command_candidates"]:
            print("- safe_command_candidates:")
            for command in item["safe_command_candidates"]:
                print(f"  - `{command['command']}`")
        if item["project_command_candidates"]:
            print("- project_command_candidates:")
            for command in item["project_command_candidates"]:
                print(f"  - `{command['command']}`")

if args.forms:
    print()
    print("## Owner Decision JSONL Skeletons")
    print()
    print("以下骨架只供 owner 人工复制、填写和复核；本命令不写文件、不关闭门禁、不提升 active。")
    print("写入任何 owner decision 前，必须补齐证据引用、reviewed_by、reviewed_at、source hash/size 和 status_reason。")
    for form in [make_decision_form(row) for row in rows if row["status"] == "open"]:
        print(json.dumps(form, ensure_ascii=False, separators=(",", ":")))

if args.checklist:
    print()
    print("## Owner Closure Checklists")
    print()
    print("以下清单把 owner intake 与 worksheet 合并到一个只读视图；不能替代 owner 决策，不能关闭门禁。")
    for checklist in [make_owner_checklist(row) for row in rows if row["status"] == "open"]:
        print()
        print(f"### {checklist['worksheet_id']}")
        print(f"- source_path: `{checklist['source_path']}`")
        print(f"- owner: {checklist['owner'] or '<missing-owner>'}")
        if checklist["owner_question_zh"]:
            print(f"- owner_question: {checklist['owner_question_zh']}")
        if checklist["default_state"]:
            print(f"- default_state: {checklist['default_state']}")
        if checklist["hard_gate_summary"]:
            print(f"- hard_gate_summary: {checklist['hard_gate_summary']}")
        if checklist["hard_gate"]:
            print(f"- hard_gate: {checklist['hard_gate']}")
        owner_route = checklist.get("owner_route", {})
        if owner_route:
            print(f"- owner_route: {owner_route.get('routing_status', '<missing-status>')} via {owner_route.get('routing_owner', '<missing-routing-owner>')}")
            if owner_route.get("required_real_owner_zh"):
                print(f"- required_real_owner: {owner_route['required_real_owner_zh']}")
            if owner_route.get("escalation_zh"):
                print(f"- escalation: {owner_route['escalation_zh']}")
        source_identity = checklist.get("observed_source_identity", {})
        if source_identity:
            print(
                "- observed_source_identity: "
                f"{source_identity.get('identity_status', '<missing-status>')} "
                f"sha256={source_identity.get('observed_sha256', '<missing-sha256>')} "
                f"size={source_identity.get('observed_size', '<missing-size>')}"
            )
        if checklist["allowed_owner_decisions"]:
            print(f"- allowed_owner_decisions: {', '.join(str(item) for item in checklist['allowed_owner_decisions'])}")
        if checklist["required_owner_fields"]:
            print(f"- required_owner_fields: {', '.join(str(item) for item in checklist['required_owner_fields'])}")
        if checklist["must_not"]:
            print(f"- must_not: {', '.join(str(item) for item in checklist['must_not'])}")

detail_rows = [] if args.summary or args.forms else rows
for row in detail_rows:
    active_marker = "YES" if row["active_registry_items"] else "no"
    print()
    print(f"## {row['source_path'] or row['id']}")
    print()
    print(f"- id: `{row['id']}`")
    print(f"- source_id: `{row['source_id']}`")
    print(f"- owner: {row['owner'] or '<missing-owner>'}")
    owner_route = row.get("owner_route", {})
    if owner_route:
        print(f"- owner_route: {owner_route.get('routing_status', '<missing-status>')} via {owner_route.get('routing_owner', '<missing-routing-owner>')}")
    print(f"- status: {row['status']} ({row['worksheet_status'] or '<missing-worksheet-status>'})")
    print(f"- review_after: {row['review_after'] or '<missing-review_after>'}")
    print(f"- active exposure: {active_marker}")
    ready_items = owner_ready_items(row)
    ready_status, _ = owner_ready_state(row)
    print(f"- owner-ready package: {ready_status}")
    if row["decision_options"]:
        print(f"- decision_options: {', '.join(str(item) for item in row['decision_options'])}")
    if row["required_owner_fields"]:
        print(f"- required_owner_fields: {', '.join(str(item) for item in row['required_owner_fields'][:8])}")
    if row["must_not"]:
        print(f"- must_not: {', '.join(str(item) for item in row['must_not'][:5])}")
    source_identity = row.get("observed_source_identity", {})
    if source_identity:
        print(
            "- observed_source_identity: "
            f"{source_identity.get('identity_status', '<missing-status>')} "
            f"sha256={source_identity.get('observed_sha256', '<missing-sha256>')} "
            f"size={source_identity.get('observed_size', '<missing-size>')}"
        )
    if row["registry_items"]:
        print("- registry_items:")
        for item in row["registry_items"]:
            print(
                f"  - `{item['id']}` status={item['status'] or '<missing-status>'} "
                f"review_status={item['review_status'] or '<missing-review-status>'} "
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
print("rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics")
print("```")

sys.exit(exit_status)
PY
