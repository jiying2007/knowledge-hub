#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import hashlib
import json
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
parser.add_argument("--validate-forms", default="", help="Validate a filled owner decision JSONL file without applying it.")
parser.add_argument("--landing-plan", action="store_true", help="With --validate-forms, print a read-only manual landing plan for valid forms.")
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
    if args.validate_forms:
        conflicts.append("--validate-forms")
    if args.landing_plan:
        conflicts.append("--landing-plan")
    if conflicts:
        parser.error(f"cannot combine --forms-jsonl with {', '.join(conflicts)}")

if args.next_open and args.worksheet_id:
    errors.append("--next-open cannot be combined with --worksheet-id")

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
        "source_root": source_root,
        "source_path": source_path,
        "source_file_exists": False,
        "expected_sha256": expected_sha256,
        "expected_size": expected_size,
        "observed_sha256": "",
        "observed_size": "",
        "identity_status": "unavailable",
        "notes_zh": "只读源文件身份提示；不代表 owner 已签收，不自动填充 source_sha256/source_size，不关闭门禁。",
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
        "observed_source_identity": row.get("observed_source_identity", {}),
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
        "observed_source_identity": row.get("observed_source_identity", {}),
        "must_not": row["must_not"],
        "notes_zh": "本清单只把 owner intake 与 worksheet 合并到一个只读视图；不能替代 owner 决策，不能关闭门禁。",
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
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)

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
    check("registry_source_path_match", source.get("source_path") == row["source_path"], "registry source_path must match worksheet")
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
    check("package_source_path_match", package.get("source_path") == row["source_path"], "package source_path must match worksheet")
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

def make_owner_summary(rows):
    summary_rows = []
    source_identity_counts = {}
    owner_counts = {}
    owner_ready_coverage = make_owner_ready_coverage(rows)
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
        "source_identity_counts": dict(sorted(source_identity_counts.items())),
        "owner_counts": dict(sorted(owner_counts.items())),
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
        target_decision = form.get("target_decision", "")
        if is_filled(target_decision) and row.get("target_candidates") and target_decision not in row["target_candidates"]:
            form_errors.append(
                f"{prefix}: target_decision {target_decision!r} is not in target candidates {row['target_candidates']}"
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
        identity = row.get("observed_source_identity", {})
        identity_status = str(identity.get("identity_status", "unavailable"))
        if identity_status != "match":
            form_errors.append(f"{prefix}: observed source identity is {identity_status}, expected match before owner landing")
        else:
            observed_sha256 = str(identity.get("observed_sha256", ""))
            observed_size = str(identity.get("observed_size", ""))
            if observed_sha256 and str(form.get("source_sha256", "")) != observed_sha256:
                form_errors.append(f"{prefix}: source_sha256 does not match observed source identity for {worksheet_id}")
            if observed_size and str(form.get("source_size", "")) != observed_size:
                form_errors.append(f"{prefix}: source_size does not match observed source identity for {worksheet_id}")
        if "must_not" in form and form.get("must_not") != row["must_not"]:
            form_errors.append(f"{prefix}: must_not differs from worksheet guardrails")
        if "allowed_owner_decisions" in form and form.get("allowed_owner_decisions") != row["decision_options"]:
            form_errors.append(f"{prefix}: allowed_owner_decisions differs from worksheet decision options")
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
        "owner_ready_gate": {
            "status": "blocked" if owner_ready_errors else "pass",
            "error_count": len(owner_ready_errors),
            "errors": owner_ready_errors,
            "notes_zh": "owner-ready package 只表示可交给 owner 签收；landing plan 仍不生成 owner decision、不关闭 gate、不写文件。",
        },
        "steps": [],
        "required_manual_files": [
            "artifacts/manifests/<owner-decision-landing-YYYYMMDD>.jsonl",
            "registry/items.jsonl",
            "registry/migrations.jsonl",
            "indexes/by-owner.md",
            "indexes/by-project.md",
            "indexes/by-review-date.md",
            "indexes/by-status.md",
            "indexes/by-topic.md",
        ],
        "verification_commands": [
            "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
            "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --status all --json",
            "rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json",
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
                "owner_ready_package_status": owner_ready_state(row)[0] if row else "",
                "owner_ready_packages": owner_ready_state(row)[1] if row else [],
                "worksheet_verification_commands": row.get("verification_commands", []),
                "manual_actions_zh": [
                    "把已审 owner decision 追加到 owner decision landing JSONL 制品。",
                    "按 target_decision 更新或新增对应 registry item，状态不得越过 owner 决策允许范围。",
                    "同步 registry/migrations.jsonl，记录从 owner-gated 到目标状态的人工迁移决策。",
                    "同步 by-project、by-status、by-owner、by-review-date 和 by-topic 索引。",
                    "按 worksheet_verification_commands 复核项目侧或 Knowledge Hub 侧证据；无法运行的命令必须记录原因。",
                    "运行 verification_commands 中的命令；strict gate 只有所有 owner gates 闭环后才会返回 0。",
                ],
                "guardrails": row.get("must_not", []),
            }
        )
    return plan

sources_payload = load_json(root / "registry" / "sources.json")
source_roots = {
    str(source.get("id", "")): str(source.get("path", ""))
    for source in sources_payload.get("sources", [])
    if isinstance(source, dict)
}

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
        "kind": item.get("kind", ""),
        "status": item.get("status", ""),
        "path": item.get("path", ""),
        "review_status": item.get("review_status", ""),
        "tags": item.get("tags", []),
        "source": source,
    }
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
        source_path = str(intake.get("source_path", ""))
        if worksheet_id:
            intake_by_worksheet[worksheet_id] = intake
        if source_path:
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
        rows.append(
            {
                "id": row_id,
                "source_id": source_id,
                "source_path": source_path,
                "owner": owner,
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
                "verification_commands": row.get("verification_commands", []),
                "owner_question_zh": intake.get("owner_question_zh", ""),
                "default_state": intake.get("default_state", ""),
                "allowed_next_status": intake.get("allowed_next_status", []),
                "hard_gate_summary": intake.get("hard_gate_summary", ""),
                "hard_gate": intake.get("hard_gate", ""),
                "observed_source_identity": compute_source_identity(row),
            }
        )

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
result_status = "blocked" if errors else "needs-fix" if active_exposure_count else "ok"
exit_status = 1 if errors or active_exposure_count else 0

result = {
    "status": result_status,
    "root": str(root),
    "read_only": True,
    "source_id": args.source_id,
    "owner": args.owner,
    "worksheet_id": args.worksheet_id,
    "next_open": args.next_open,
    "filter_status": args.status,
    "worksheet_count": len(worksheet_paths),
    "row_count": len(rows),
    "open_count": open_count,
    "resolved_count": resolved_count,
    "active_exposure_count": active_exposure_count,
    **owner_ready_coverage,
    "errors": errors,
    "rows": rows,
}

if args.summary:
    result["owner_summary"] = make_owner_summary(rows)

if args.forms:
    result["decision_forms"] = [make_decision_form(row) for row in rows if row["status"] == "open"]

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

if args.forms_jsonl:
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(exit_status)
    if active_exposure_count:
        print("ERROR: active exposure exists; owner-gated rows must stay out of active until owner decisions are closed.", file=sys.stderr)
        sys.exit(exit_status)
    for form in [make_decision_form(row) for row in rows if row["status"] == "open"]:
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
    print()
    print("| worksheet | source path | owner | identity | owner-ready | required fields | focus command |")
    print("|---|---|---|---|---|---:|---|")
    for item in summary["rows"]:
        print(
            f"| `{item['worksheet_id']}` | `{item['source_path']}` | "
            f"{item['owner'] or '<missing-owner>'} | {item['source_identity_status']} | "
            f"{item['owner_ready_package_status']} | {item['required_owner_field_count']} | `{item['focus_command']}` |"
        )

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
