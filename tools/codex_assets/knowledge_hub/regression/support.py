import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Run lightweight Knowledge Hub governance regression fixtures in /tmp.")
parser.add_argument("--json", action="store_true")
parser.add_argument("--keep-temp", action="store_true", help="Keep temporary fixture repositories for inspection.")
parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD", help="Use a fixed date for date-sensitive fixture commands.")
parser.add_argument(
    "--test",
    action="append",
    default=[],
    metavar="FUNCTION",
    help="Run only the named test function; repeat to select multiple functions.",
)
parser.add_argument(
    "--suite",
    choices=["quick", "full"],
    default="full",
    help="Run quick smoke coverage for day-to-day gates or the full fixture suite for terminal proof.",
)
args = parser.parse_args(argv)

results = []
temp_roots = []
test_context = threading.local()
temp_dir = pathlib.Path(tempfile.gettempdir()).resolve()
min_tmp_free_bytes = int(os.environ.get("KNOWLEDGE_REGRESSION_MIN_TMP_FREE_BYTES", str(4 * 1024 * 1024)))
default_jobs = min(4, os.cpu_count() or 1) if args.suite == "full" else 1
regression_jobs = max(1, int(os.environ.get("KNOWLEDGE_REGRESSION_JOBS", str(default_jobs))))

def resolve_today():
    if args.as_of:
        raw_value = args.as_of
        source = "arg:--as-of"
    else:
        raw_value = os.environ.get("KNOWLEDGE_TODAY", "")
        source = "env:KNOWLEDGE_TODAY" if raw_value else "system-date"
    if raw_value:
        try:
            return dt.date.fromisoformat(raw_value), source
        except Exception:
            parser.error(f"invalid date for {source}: {raw_value}")
    return dt.datetime.utcnow().date(), source

today, today_source = resolve_today()
child_env = os.environ.copy()
child_env["KNOWLEDGE_TELEMETRY"] = "0"
if today_source != "system-date":
    child_env["KNOWLEDGE_TODAY"] = today.isoformat()

def user_path_prefixes():
    prefixes = [str(pathlib.Path.home())]
    user_name = os.environ.get("USER", "")
    if user_name:
        prefixes.append("/" + "vsdata" + "/" + user_name)
    return [prefix for prefix in prefixes if prefix and prefix != "/"]

def display_path(value):
    text = str(value)
    for prefix in user_path_prefixes():
        if text == prefix:
            text = "~"
        elif text.startswith(prefix + "/"):
            text = "~" + text[len(prefix):]
        else:
            text = text.replace(prefix, "~")
    return text

def run_cmd(repo, command):
    completed = subprocess.run(
        command,
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=child_env,
    )
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }

def copy_repo(label):
    free_bytes = shutil.disk_usage(temp_dir).free
    if free_bytes < min_tmp_free_bytes:
        raise RuntimeError(
            f"insufficient temp space in {temp_dir}: free={free_bytes} required={min_tmp_free_bytes}"
        )
    temp_root = pathlib.Path(tempfile.mkdtemp(prefix=f"kh-regression-{label}-"))
    current_temp_roots = getattr(test_context, "temp_roots", temp_roots)
    current_temp_roots.append(temp_root)
    repo = temp_root / "repo"

    def ignore_fixture_paths(directory, names):
        ignored = set()
        directory_path = pathlib.Path(directory).resolve()
        if directory_path == root:
            ignored.update({".git", ".tmp", ".codex"})
        if directory_path == root / "artifacts":
            ignored.add("vault")
        ignored.update(name for name in names if name in {"__pycache__", ".pytest_cache"})
        return ignored

    shutil.copytree(root, repo, ignore=ignore_fixture_paths)
    vault_source = root / "artifacts" / "vault"
    vault_target = repo / "artifacts" / "vault"
    if vault_source.exists():
        def hardlink_or_copy(source, target):
            try:
                os.link(source, target)
            except OSError:
                shutil.copy2(source, target)

        shutil.copytree(vault_source, vault_target, copy_function=hardlink_or_copy)
    return repo

def sync_status_index_entries(repo, item_ids, target_status):
    status_path = repo / "indexes" / "by-status.md"
    try:
        lines = status_path.read_text().splitlines()
    except Exception:
        return
    ids = {str(item_id) for item_id in item_ids if item_id}
    if not ids:
        return
    kept_lines = []
    present = set()
    insert_at = None
    status_prefix = f"- {target_status}: `"
    for index, line in enumerate(lines):
        matched_id = ""
        for item_id in ids:
            if re.match(rf"^- [a-z0-9_-]+: `{re.escape(item_id)}`$", line):
                matched_id = item_id
                break
        if matched_id:
            if line.startswith(status_prefix):
                present.add(matched_id)
                kept_lines.append(line)
            continue
        kept_lines.append(line)
        if line.startswith(status_prefix):
            insert_at = len(kept_lines)
    additions = [f"- {target_status}: `{item_id}`" for item_id in sorted(ids - present)]
    if additions:
        if insert_at is None:
            insert_at = 0
        kept_lines[insert_at:insert_at] = additions
    status_path.write_text("\n".join(kept_lines) + "\n")

def sync_owner_index_entries(repo, item_ids, owner):
    owner_path = repo / "indexes" / "by-owner.md"
    try:
        lines = owner_path.read_text().splitlines()
    except Exception:
        return
    ids = {str(item_id) for item_id in item_ids if item_id}
    if not ids:
        return
    heading = f"## {owner}"
    try:
        section_start = lines.index(heading) + 1
    except ValueError:
        if lines and lines[-1]:
            lines.append("")
        lines.extend([heading, ""])
        section_start = len(lines)
    section_end = next(
        (index for index in range(section_start, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    present = {
        match.group(1)
        for line in lines[section_start:section_end]
        if (match := re.fullmatch(r"- `([^`]+)`", line))
    }
    additions = [f"- `{item_id}`" for item_id in sorted(ids - present)]
    if additions:
        insert_at = section_end
        while insert_at > section_start and not lines[insert_at - 1]:
            insert_at -= 1
        lines[insert_at:insert_at] = additions
    owner_path.write_text("\n".join(lines) + "\n")

def sync_review_date_index_entries(repo, item_ids, review_after):
    review_path = repo / "indexes" / "by-review-date.md"
    try:
        lines = review_path.read_text().splitlines()
    except Exception:
        return
    ids = {str(item_id) for item_id in item_ids if item_id}
    if not ids:
        return
    present = {
        match.group(1)
        for line in lines
        if (match := re.search(r"`([^`]+)`", line))
    }
    lines.extend(
        f"- {review_after}: `{item_id}`"
        for item_id in sorted(ids - present)
    )
    review_path.write_text("\n".join(lines) + "\n")

def update_source_registry_entry(repo, source_id, updates):
    sources_path = repo / "registry" / "sources.json"
    retired_sources_path = repo / "registry" / "retired-sources.jsonl"
    source_id = str(source_id)
    try:
        sources_doc = json.loads(sources_path.read_text())
    except Exception:
        sources_doc = {"sources": []}
    for source in sources_doc.get("sources", []):
        if isinstance(source, dict) and source.get("id") == source_id:
            source.update(updates)
            sources_path.write_text(json.dumps(sources_doc, ensure_ascii=False, indent=2) + "\n")
            return True
    try:
        retired_rows = [
            json.loads(line)
            for line in retired_sources_path.read_text().splitlines()
            if line.strip()
        ]
    except Exception:
        retired_rows = []
    for source in retired_rows:
        if isinstance(source, dict) and source.get("id") == source_id:
            source.update(updates)
            retired_sources_path.write_text(
                "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in retired_rows) + "\n"
            )
            return True
    return False

def seed_review_after_near_due_fixture(repo):
    reviewing_fixture_ids = {
        "pcr02-diag-command-architecture-final",
        "pcr02-hdi-api-app-functional-overview",
        "pcr02-module-catalog",
        "pcr02-core-module-design",
        "pcr02-project-detailed-design",
        "pcr02-project-overview-design",
        "pcr02-diag-v4-hybrid-refcount-discovery-spec",
        "pcr02-third-party-libraries-reference",
        "pcr02-diag-usage-guide",
        "pcr02-irlight-sw-threshold-calibration",
        "pcr02-prog-tool-usage-guide",
        "pcr02-build-and-deploy-guide",
        "pcr02-debug-tools-guide",
    }
    fixture_dates = {
        "2026-07-16": {
            "pcr02-diag-command-architecture-final",
            "pcr02-hdi-api-app-functional-overview",
            "pcr02-module-catalog",
            "pcr02-core-module-design",
            "pcr02-project-detailed-design",
            "pcr02-project-overview-design",
            "pcr02-diag-v4-hybrid-refcount-discovery-spec",
            "pcr02-third-party-libraries-reference",
            "pcr02-diag-usage-guide",
            "pcr02-irlight-sw-threshold-calibration",
            "pcr02-prog-tool-usage-guide",
            "pcr02-build-and-deploy-guide",
            "pcr02-debug-tools-guide",
            "pcr02-v1-deep-analysis-plan-archive-20260506",
            "pcr02-v1-migration-execution-plan-archive-20260506",
            "pcr02-irlight-optimization-plan-archive-20260508",
            "pcr02-diag-v4-hybrid-refcount-discovery-plan-archive-20260510",
            "pcr02-diag-ut-hard-switch-progress-archive-20260513",
            "pcr02-v1-deep-analysis-validation-report-20260506",
            "pcr02-v1-migration-final-validation-report-20260507",
            "pcr02-aov-lightsensor-analysis-validation-report-20260508",
            "pcr02-prog-tool-terminal-release-validation-report-20260514",
            "pcr02-session-archive-report-20260517",
        },
        "2026-07-17": {
            "pcr02-review-required-resolution-20260617",
        },
        "2026-07-18": {
            "pcr02-owner-review-package-20260618",
            "pcr02-owner-review-follow-up-20260618",
            "pcr02-owner-decision-worksheets-20260618",
        },
    }
    date_by_id = {
        item_id: review_after
        for review_after, item_ids in fixture_dates.items()
        for item_id in item_ids
    }
    items_path = repo / "registry" / "items.jsonl"
    rows = []
    updated = set()
    for line in items_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        item_id = row.get("id")
        if item_id in date_by_id:
            row["review_after"] = date_by_id[item_id]
            row["status"] = "reviewing" if item_id in reviewing_fixture_ids else "archived"
            row["updated_at"] = "2026-07-01"
            updated.add(item_id)
        rows.append(row)
    missing = sorted(set(date_by_id) - updated)
    if missing:
        raise RuntimeError("near-due fixture target ids missing: " + ",".join(missing))
    items_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n"
    )
    sync_status_index_entries(repo, reviewing_fixture_ids, "reviewing")
    sync_status_index_entries(repo, set(date_by_id) - reviewing_fixture_ids, "archived")
    return len(updated)

def seed_pending_review_queue_items(repo, count=2):
    items_path = repo / "registry" / "items.jsonl"
    fixture_path = "artifacts/manifests/knowledge-hub-review-queue-forms-jsonl-hardening-20260623.md"
    rows = []
    for index in range(count):
        suffix = index + 1
        rows.append({
            "id": f"regression-review-queue-pending-{suffix}",
            "title": f"Regression review queue pending fixture {suffix}",
            "kind": "audit",
            "domain": "governance",
            "path": fixture_path,
            "scope": "team-general",
            "visibility": "team-internal",
            "status": "reviewing",
            "owner": "leiwenjun",
            "source": {
                "type": "generated",
                "from": "knowledge-regression pending review queue fixture",
            },
            "review_after": today.isoformat(),
            "validation_refs": [
                "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --json"
            ],
            "summary_zh": "回归夹具：模拟等待人工复核的 AI 生成治理审计条目。",
            "primary_language": "zh-CN",
            "source_language": "zh-CN",
            "translation_status": "not-required",
            "terminology_status": "pending-review",
            "review_status": "ai-generated-pending-human-review",
            "created_at": today.isoformat(),
            "updated_at": today.isoformat(),
            "promotion": "none",
            "tags": ["regression", "review-queue"],
            "generated_by_ai": True,
            "ai_role": "drafted",
            "ai_model_or_tool": "regression-fixture",
            "ai_generated_at": today.isoformat(),
        })
    with items_path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    item_ids = [row["id"] for row in rows]
    sync_owner_index_entries(repo, item_ids, "leiwenjun")
    sync_review_date_index_entries(repo, item_ids, today.isoformat())
    sync_status_index_entries(repo, item_ids, "reviewing")
    return item_ids

OWNER_DECISION_FIELD_NAMES = {
    "owner_decision",
    "target_decision",
    "split_approval",
    "reviewed_by",
    "reviewed_at",
    "source_status",
    "source_sha256",
    "source_size",
    "current_validity",
    "scope_statement",
    "applicable_project_version",
    "project_only_source_of_truth",
    "applicable_branch_firmware_version",
    "implementation_match",
    "gate_evidence",
    "applicable_branch_or_sdk_version",
    "target_binary",
    "team_level_status",
    "governance_mode",
    "automation_enabled",
    "writes_memory",
    "writes_team_active_index",
    "no_memory_write_gate",
    "manual_approval_owner",
    "manual_approval_cadence",
    "final_branch_commit_or_tag_refs",
    "proto_generation_evidence",
    "build_evidence",
    "api_dvr_refcount_evidence",
    "targeted_grep_evidence",
    "task_iot_dependency_status",
    "replay_data_channel_status",
    "LIST_FETCH_pagination_or_limit_decision",
    "RecordSetEvent_contract_extract_decision",
    "firmware_version_refs",
    "protection_parameter_table",
    "serial_waveform_or_protocol_logs",
    "hardware_start_evidence",
    "field_retest_records",
    "calibration_before_after_data",
    "fault_code_or_protocol_field_definitions",
    "whole_device_validation_records",
    "unresolved_items_acknowledgement",
    "source_status_at_capture",
    "contains_memory_candidates",
    "not_active_source",
    "extracts_require_owner_review",
    "commit_branch_dirty_state_evidence",
    "proto_generation_evidence_refs",
    "build_evidence_refs",
    "refcount_evidence_refs",
    "grep_evidence_refs",
    "final_ready_evidence_refs",
    "task_iot_status",
    "LIST_FETCH_pagination_risk_status",
    "memory_candidates_exclusion_confirmation",
    "evidence_refs",
    "open_items",
    "status_reason",
}

def reopen_owner_decision_worksheets(repo):
    worksheet_path = repo / "artifacts" / "manifests" / "pcr02-owner-decision-worksheets-20260618.jsonl"
    items_path = repo / "registry" / "items.jsonl"
    sources_path = repo / "registry" / "sources.json"
    retired_sources_path = repo / "registry" / "retired-sources.jsonl"
    try:
        sources_doc = json.loads(sources_path.read_text())
    except Exception:
        sources_doc = {}
    try:
        retired_sources = [
            json.loads(line)
            for line in retired_sources_path.read_text().splitlines()
            if line.strip()
        ]
    except Exception:
        retired_sources = []
    source_roots = {
        str(source.get("id", "")): str(source.get("path", ""))
        for source in list(sources_doc.get("sources", [])) + retired_sources
        if isinstance(source, dict)
    }
    rows = []
    for line in worksheet_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        row["worksheet_status"] = "owner-fill-required"
        row.pop("status", None)
        row.pop("row_status", None)
        row.pop("resolved_at", None)
        row.pop("resolved_by", None)
        for field_name in OWNER_DECISION_FIELD_NAMES:
            row.pop(field_name, None)
        source_id = str(row.get("source_id", ""))
        source_path = str(row.get("source_path", ""))
        source_root = source_roots.get(source_id, "")
        if source_root and source_path and not pathlib.PurePosixPath(source_root).is_absolute() and ".." not in pathlib.PurePosixPath(source_root).parts and ".." not in pathlib.PurePosixPath(source_path).parts:
            source_file = (repo / source_root / source_path).resolve()
            repo_root = repo.resolve()
            try:
                source_file.relative_to(repo_root)
            except ValueError:
                source_file = None
            if source_file is not None:
                source_file.parent.mkdir(parents=True, exist_ok=True)
                body = (
                    f"Regression owner source identity fixture\n"
                    f"worksheet_id: {row.get('id', '')}\n"
                    f"source_id: {source_id}\n"
                    f"source_path: {source_path}\n"
                ).encode("utf-8")
                source_file.write_bytes(body)
                row["source_sha256_expected"] = hashlib.sha256(body).hexdigest()
                row["source_size_expected"] = len(body)
        rows.append(row)
    worksheet_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n"
    )
    owner_ready_keys = {(str(row.get("source_id", "")), str(row.get("source_path", ""))) for row in rows}
    item_rows = [json.loads(line) for line in items_path.read_text().splitlines() if line.strip()]
    reopened_owner_ready_ids = []
    for item in item_rows:
        source = item.get("source", {}) if isinstance(item.get("source"), dict) else {}
        key = (str(source.get("source_id", "")), str(source.get("source_path", "")))
        if key not in owner_ready_keys or "owner-ready-package" not in str(item.get("path", "")):
            continue
        tags = [
            str(tag)
            for tag in item.get("tags", [])
            if tag not in {"historical-signoff-package", "owner-decision-evidence", "superseded"}
        ]
        for required_tag in ["owner-gate", "owner-ready"]:
            if required_tag not in tags:
                tags.append(required_tag)
        item["status"] = "reviewing"
        item["review_status"] = "owner-ready-no-decision"
        item["tags"] = tags
        reopened_owner_ready_ids.append(str(item.get("id", "")))
    items_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) for item in item_rows) + "\n"
    )
    sync_status_index_entries(repo, reopened_owner_ready_ids, "reviewing")
    return repo

def copy_repo_with_open_owner_gates(label):
    return reopen_owner_decision_worksheets(copy_repo(label))

def init_temp_git_repo(repo):
    result = run_cmd(repo, ["rtk", "git", "init"])
    if result["exit_code"] != 0:
        return {"setup_error": "git init failed", "stderr": result["stderr"][:1000]}
    return {}

def cleanup_temp_roots():
    if args.keep_temp:
        return
    current_temp_roots = getattr(test_context, "temp_roots", temp_roots)
    while current_temp_roots:
        temp_root = current_temp_roots.pop()
        shutil.rmtree(temp_root, ignore_errors=True)

def run_test(fn):
    started_at = time.monotonic()
    test_context.records = []
    test_context.temp_roots = []
    try:
        fn()
    except Exception as exc:
        record(
            fn.__name__.replace("test_", "").replace("_", "-"),
            f"{fn.__name__} raised an exception",
            "fail",
            {
                "exception": str(exc),
                "temp_dir": str(temp_dir),
                "temp_free_bytes": shutil.disk_usage(temp_dir).free,
                "min_tmp_free_bytes": min_tmp_free_bytes,
            },
        )
    finally:
        duration_sec = round(time.monotonic() - started_at, 3)
        records = list(getattr(test_context, "records", []))
        for result in records:
            result["duration_sec"] = duration_sec
            result["test_fn"] = fn.__name__
        cleanup_temp_roots()
        test_context.records = []
        test_context.temp_roots = []
    return records

def record(test_id, title, status, details, repo=None):
    row = {
        "id": test_id,
        "title": title,
        "status": status,
        "details": details,
        "fixture_repo": str(repo) if repo and args.keep_temp else "",
    }
    records = getattr(test_context, "records", None)
    if records is None:
        results.append(row)
    else:
        records.append(row)

def expect(condition, test_id, title, details, repo=None):
    record(test_id, title, "pass" if condition else "fail", details, repo)

def make_valid_owner_decision_form(repo):
    forms_result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--worksheet-id",
            "pcr02-owner-decision-worksheet-001",
            "--forms",
            "--json",
        ],
    )
    parsed_forms = {}
    try:
        parsed_forms = json.loads(forms_result["stdout"])
    except Exception:
        pass
    forms = parsed_forms.get("decision_forms", [])
    if not forms:
        return {}, {"setup_error": "missing decision form", "stdout_sample": forms_result["stdout"][:1000]}
    form = forms[0]
    identity = form.get("observed_source_identity", {})
    for key, value in {
        "owner_decision": form.get("allowed_owner_decisions", ["project-local-rule"])[0],
        "target_decision": form.get("target_candidates", ["project-local-rule"])[0],
        "reviewed_by": "regression-fixture-owner",
        "reviewed_at": "2026-06-19",
        "review_after": "2026-09-19",
        "source_status": "owner-reviewed-fixture",
        "source_sha256": identity.get("observed_sha256", ""),
        "source_size": identity.get("observed_size", ""),
        "current_validity": "fixture-only",
        "scope_statement": "PCR02 project-local only",
        "applicable_project_version": "fixture-version",
        "evidence_refs": ["artifacts/manifests/pcr02-owner-resolution-playbook-20260618.md"],
        "status_reason": "Regression fixture for landing-plan required files.",
    }.items():
        form[key] = value
    return form, {}

def make_owner_decision_form_for_worksheet(repo, worksheet_id):
    forms_result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--worksheet-id",
            worksheet_id,
            "--forms",
            "--json",
        ],
    )
    parsed_forms = {}
    try:
        parsed_forms = json.loads(forms_result["stdout"])
    except Exception:
        pass
    forms = parsed_forms.get("decision_forms", [])
    if not forms:
        return {}, {"setup_error": "missing decision form", "worksheet_id": worksheet_id, "stdout_sample": forms_result["stdout"][:1000]}
    form = forms[0]
    identity = form.get("observed_source_identity", {})
    form["reviewed_by"] = "regression-fixture-owner"
    form["reviewed_at"] = "2026-06-23"
    form["review_after"] = "2026-09-23"
    form["source_status"] = "owner-reviewed-fixture"
    form["source_sha256"] = identity.get("observed_sha256", "")
    form["source_size"] = identity.get("observed_size", "")
    form["evidence_refs"] = ["artifacts/manifests/pcr02-owner-resolution-playbook-20260618.md"]
    form["status_reason"] = "Regression fixture for the explicit owner-decision contract."
    for field in form.get("required_owner_fields", []):
        value = form.get(field)
        if value in (None, "") or value == [] or value == {}:
            form[field] = f"fixture-{field}"
    return form, {}

def run_owner_decision_target_pair_gate(case_id, owner_decision, target_decision, expected_fragment):
    repo = copy_repo_with_open_owner_gates(case_id)
    form, setup_error = make_valid_owner_decision_form(repo)
    if setup_error:
        expect(False, case_id, "owner form rejects invalid owner_decision and target_decision pairs", setup_error, repo)
        return
    if owner_decision not in form.get("allowed_owner_decisions", []):
        expect(False, case_id, "owner form rejects invalid owner_decision and target_decision pairs", {"setup_error": "owner_decision fixture not allowed", "owner_decision": owner_decision, "allowed_owner_decisions": form.get("allowed_owner_decisions", [])}, repo)
        return
    if target_decision not in form.get("target_candidates", []):
        expect(False, case_id, "owner form rejects invalid owner_decision and target_decision pairs", {"setup_error": "target_decision fixture not a candidate", "target_decision": target_decision, "target_candidates": form.get("target_candidates", [])}, repo)
        return
    form["owner_decision"] = owner_decision
    form["target_decision"] = target_decision
    temp_root = pathlib.Path(tempfile.mkdtemp(prefix=f"kh-regression-{case_id}-"))
    temp_roots.append(temp_root)
    forms_path = temp_root / "owner-decisions.jsonl"
    forms_path.write_text(json.dumps(form, ensure_ascii=False, separators=(",", ":")) + "\n")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--worksheet-id",
            "pcr02-owner-decision-worksheet-001",
            "--validate-forms",
            str(forms_path),
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    errors = parsed.get("form_validation", {}).get("errors", [])
    diagnostics = parsed.get("form_validation", {}).get("diagnostics", [])
    mismatch_diagnostic = next(
        (
            row for row in diagnostics
            if row.get("code") == "owner-decision-target-mismatch"
            and row.get("field") == "target_decision"
        ),
        {},
    )
    expect(
        result["exit_code"] == 1
        and parsed.get("form_validation", {}).get("status") == "fail"
        and any(expected_fragment in error for error in errors)
        and mismatch_diagnostic.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and mismatch_diagnostic.get("actual") == {"owner_decision": owner_decision, "target_decision": target_decision}
        and "成对一致" in mismatch_diagnostic.get("action_zh", ""),
        case_id,
        "owner form rejects invalid owner_decision and target_decision pairs",
        {
            "exit_code": result["exit_code"],
            "validation_status": parsed.get("form_validation", {}).get("status"),
            "errors": errors,
            "diagnostics": diagnostics,
            "owner_decision": owner_decision,
            "target_decision": target_decision,
            "stdout_sample": result["stdout"][:1000],
        },
    )

def run_owner_decision_target_pair_positive(case_id, owner_decision, target_decision):
    repo = copy_repo_with_open_owner_gates(case_id)
    form, setup_error = make_valid_owner_decision_form(repo)
    if setup_error:
        expect(False, case_id, "owner form accepts valid owner_decision and target_decision pairs", setup_error, repo)
        return
    if owner_decision not in form.get("allowed_owner_decisions", []):
        expect(False, case_id, "owner form accepts valid owner_decision and target_decision pairs", {"setup_error": "owner_decision fixture not allowed", "owner_decision": owner_decision, "allowed_owner_decisions": form.get("allowed_owner_decisions", [])}, repo)
        return
    if target_decision not in form.get("target_candidates", []):
        expect(False, case_id, "owner form accepts valid owner_decision and target_decision pairs", {"setup_error": "target_decision fixture not a candidate", "target_decision": target_decision, "target_candidates": form.get("target_candidates", [])}, repo)
        return
    form["owner_decision"] = owner_decision
    form["target_decision"] = target_decision
    temp_root = pathlib.Path(tempfile.mkdtemp(prefix=f"kh-regression-{case_id}-"))
    temp_roots.append(temp_root)
    forms_path = temp_root / "owner-decisions.jsonl"
    forms_path.write_text(json.dumps(form, ensure_ascii=False, separators=(",", ":")) + "\n")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--worksheet-id",
            "pcr02-owner-decision-worksheet-001",
            "--validate-forms",
            str(forms_path),
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    expect(
        result["exit_code"] == 0
        and parsed.get("form_validation", {}).get("status") == "pass"
        and parsed.get("form_validation", {}).get("error_count") == 0,
        case_id,
        "owner form accepts valid owner_decision and target_decision pairs",
        {
            "exit_code": result["exit_code"],
            "validation_status": parsed.get("form_validation", {}).get("status"),
            "errors": parsed.get("form_validation", {}).get("errors", []),
            "owner_decision": owner_decision,
            "target_decision": target_decision,
            "stdout_sample": result["stdout"][:1000],
        },
    )

def run_owner_form_tamper_gate(case_id, mutate_form, expected_fragment):
    repo = copy_repo_with_open_owner_gates(case_id)
    form, setup_error = make_valid_owner_decision_form(repo)
    if setup_error:
        expect(False, case_id, "owner form rejects worksheet guardrail tampering", setup_error, repo)
        return
    mutate_form(form)
    temp_root = pathlib.Path(tempfile.mkdtemp(prefix=f"kh-regression-{case_id}-"))
    temp_roots.append(temp_root)
    forms_path = temp_root / "owner-decisions.jsonl"
    forms_path.write_text(json.dumps(form, ensure_ascii=False, separators=(",", ":")) + "\n")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--worksheet-id",
            "pcr02-owner-decision-worksheet-001",
            "--validate-forms",
            str(forms_path),
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    errors = parsed.get("form_validation", {}).get("errors", [])
    expect(
        result["exit_code"] == 1
        and parsed.get("form_validation", {}).get("status") == "fail"
        and any(expected_fragment in error for error in errors),
        case_id,
        "owner form rejects worksheet guardrail tampering",
        {
            "exit_code": result["exit_code"],
            "validation_status": parsed.get("form_validation", {}).get("status"),
            "errors": errors,
            "stdout_sample": result["stdout"][:1000],
        },
    )

def run_owner_landing_ready_block_fixture(case_id, expected_status, mutate_repo):
    repo = copy_repo_with_open_owner_gates(f"owner-landing-plan-owner-ready-{case_id}")
    form, setup_error = make_valid_owner_decision_form(repo)
    if setup_error:
        expect(
            False,
            f"owner-landing-plan-requires-owner-ready-{case_id}",
            f"owner landing plan blocks {expected_status} owner-ready package state",
            setup_error,
            repo,
        )
        return

    mutation_error = mutate_repo(repo)
    if mutation_error:
        expect(
            False,
            f"owner-landing-plan-requires-owner-ready-{case_id}",
            f"owner landing plan blocks {expected_status} owner-ready package state",
            mutation_error,
            repo,
        )
        return

    forms_path = repo.parent / "owner-decisions.jsonl"
    forms_path.write_text(json.dumps(form, ensure_ascii=False, separators=(",", ":")) + "\n")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--worksheet-id",
            "pcr02-owner-decision-worksheet-001",
            "--validate-forms",
            str(forms_path),
            "--landing-plan",
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    landing_plan = parsed.get("landing_plan", {})
    owner_ready_gate = landing_plan.get("owner_ready_gate", {})
    errors = owner_ready_gate.get("errors", [])
    expect(
        result["exit_code"] == 0
        and parsed.get("form_validation", {}).get("status") == "pass"
        and landing_plan.get("status") == "blocked"
        and owner_ready_gate.get("status") == "blocked"
        and owner_ready_gate.get("error_count") == 1
        and errors
        and errors[0].get("owner_ready_package_status") == expected_status
        and not landing_plan.get("steps"),
        f"owner-landing-plan-requires-owner-ready-{case_id}",
        f"owner landing plan blocks {expected_status} owner-ready package state",
        {
            "exit_code": result["exit_code"],
            "form_validation_status": parsed.get("form_validation", {}).get("status"),
            "landing_status": landing_plan.get("status"),
            "expected_owner_ready_package_status": expected_status,
            "owner_ready_gate": owner_ready_gate,
            "stdout_sample": result["stdout"][:1200],
        },
        repo,
    )
