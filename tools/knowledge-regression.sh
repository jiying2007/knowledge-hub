#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Run lightweight Knowledge Hub governance regression fixtures in /tmp.")
parser.add_argument("--json", action="store_true")
parser.add_argument("--keep-temp", action="store_true", help="Keep temporary fixture repositories for inspection.")
parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD", help="Use a fixed date for date-sensitive fixture commands.")
args = parser.parse_args(argv)

results = []
temp_roots = []
temp_dir = pathlib.Path(tempfile.gettempdir()).resolve()
min_tmp_free_bytes = int(os.environ.get("KNOWLEDGE_REGRESSION_MIN_TMP_FREE_BYTES", str(4 * 1024 * 1024)))

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
child_env = None
if today_source != "system-date":
    child_env = os.environ.copy()
    child_env["KNOWLEDGE_TODAY"] = today.isoformat()

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
    temp_roots.append(temp_root)
    repo = temp_root / "repo"
    shutil.copytree(root, repo, ignore=shutil.ignore_patterns(".git"))
    return repo

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
    rows = []
    for line in worksheet_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        row["worksheet_status"] = "owner-fill-required"
        for field_name in OWNER_DECISION_FIELD_NAMES:
            row.pop(field_name, None)
        rows.append(row)
    worksheet_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n"
    )
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
    while temp_roots:
        temp_root = temp_roots.pop()
        shutil.rmtree(temp_root, ignore_errors=True)

def run_test(fn):
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
        cleanup_temp_roots()

def record(test_id, title, status, details, repo=None):
    results.append(
        {
            "id": test_id,
            "title": title,
            "status": status,
            "details": details,
            "fixture_repo": str(repo) if repo and args.keep_temp else "",
        }
    )

def expect(condition, test_id, title, details, repo=None):
    record(test_id, title, "pass" if condition else "fail", details, repo)

def test_baseline():
    command = ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"]
    result = run_cmd(root, command)
    expect(
        result["exit_code"] == 0,
        "baseline-knowledge-check",
        "baseline knowledge-check passes",
        {"exit_code": result["exit_code"], "stderr": result["stderr"][:500]},
    )

def test_governance_goal_path_allowed():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-check.sh",
            "--dry-run",
            "--json",
            "--explain",
            "knowledge-hub-final-state-goal-20260620",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    explain = parsed.get("explain", {})
    registry = explain.get("registry", {})
    expect(
        result["exit_code"] == 0
        and parsed.get("status") == "pass"
        and explain.get("found") is True
        and registry.get("path") == "docs/goals/knowledge-hub-final-state.md"
        and registry.get("path_exists") is True,
        "governance-goal-path-allowed",
        "governance goal docs path is accepted and explainable",
        {
            "exit_code": result["exit_code"],
            "status": parsed.get("status"),
            "found": explain.get("found"),
            "path": registry.get("path"),
            "path_exists": registry.get("path_exists"),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_pcr02_level2_source_coverage():
    expected = {
        "pcr02-project-tools",
        "pcr02-project-knowledge",
        "pcr02-product-test",
        "pcr02-project-scratch",
        "pcr02-project-root-artifacts",
        "pcr02-module-agent-rules",
        "pcr02-project-agent-config",
    }
    sources_path = root / "registry" / "sources.json"
    by_source_path = root / "indexes" / "by-source.md"
    coverage_paths = sorted((root / "artifacts" / "manifests").glob("knowledge-hub-source-coverage-closeout-*.jsonl"))
    source_ids = set()
    by_source_ids = set()
    coverage_ids = set()
    coverage_path = coverage_paths[-1] if coverage_paths else None
    errors = []
    try:
        source_ids = {item.get("id", "") for item in json.loads(sources_path.read_text()).get("sources", [])}
    except Exception as exc:
        errors.append(f"sources parse: {exc}")
    try:
        in_table = False
        for line in by_source_path.read_text().splitlines():
            stripped = line.strip()
            if not stripped:
                if in_table:
                    break
                continue
            if not stripped.startswith("|"):
                continue
            cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
            if len(cells) < 3 or cells[0] in {"Source", "---"}:
                continue
            in_table = True
            by_source_ids.add(cells[0])
    except Exception as exc:
        errors.append(f"by-source parse: {exc}")
    if coverage_path:
        try:
            for line in coverage_path.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                coverage_ids.add(row.get("source_id", ""))
        except Exception as exc:
            errors.append(f"coverage parse: {exc}")
    else:
        errors.append("missing source coverage closeout jsonl")
    expect(
        not errors
        and coverage_path is not None
        and coverage_path.name == "knowledge-hub-source-coverage-closeout-20260620.jsonl"
        and expected <= source_ids
        and expected <= by_source_ids
        and expected <= coverage_ids,
        "pcr02-level2-source-coverage",
        "PCR02 Level 2 sources are registered, indexed and covered",
        {
            "errors": errors,
            "latest_coverage": str(coverage_path.relative_to(root)) if coverage_path else "",
            "missing_sources": sorted(expected - source_ids),
            "missing_by_source": sorted(expected - by_source_ids),
            "missing_coverage": sorted(expected - coverage_ids),
            "registered_count": len(source_ids),
            "coverage_count": len(coverage_ids),
        },
    )

def test_pcr02_level2_boundary_manifests():
    expected = {
        "pcr02-tools-boundary-20260620": {
            "md": "artifacts/manifests/pcr02-tools-boundary-20260620.md",
            "jsonl": "artifacts/manifests/pcr02-tools-boundary-20260620.jsonl",
            "source_id": "pcr02-project-tools",
            "required_text": "memory-candidate-automation-ref",
        },
        "pcr02-knowledge-secret-config-boundary-20260620": {
            "md": "artifacts/manifests/pcr02-knowledge-secret-config-boundary-20260620.md",
            "jsonl": "artifacts/manifests/pcr02-knowledge-secret-config-boundary-20260620.jsonl",
            "source_id": "pcr02-project-knowledge",
            "required_text": "project-local-standard-candidate",
        },
        "pcr02-product-test-artifact-config-interface-boundary-20260620": {
            "md": "artifacts/manifests/pcr02-product-test-artifact-config-interface-boundary-20260620.md",
            "jsonl": "artifacts/manifests/pcr02-product-test-artifact-config-interface-boundary-20260620.jsonl",
            "source_id": "pcr02-product-test",
            "required_text": "build-artifact-generated",
        },
        "pcr02-scratch-archive-boundary-20260620": {
            "md": "artifacts/manifests/pcr02-scratch-archive-boundary-20260620.md",
            "jsonl": "artifacts/manifests/pcr02-scratch-archive-boundary-20260620.jsonl",
            "source_id": "pcr02-project-scratch",
            "required_text": "historical-session-evidence",
        },
        "pcr02-root-artifacts-boundary-20260620": {
            "md": "artifacts/manifests/pcr02-root-artifacts-boundary-20260620.md",
            "jsonl": "artifacts/manifests/pcr02-root-artifacts-boundary-20260620.jsonl",
            "source_id": "pcr02-project-root-artifacts",
            "required_text": "source-coverage-evidence-drift",
        },
        "pcr02-module-agent-rules-boundary-20260620": {
            "md": "artifacts/manifests/pcr02-module-agent-rules-boundary-20260620.md",
            "jsonl": "artifacts/manifests/pcr02-module-agent-rules-boundary-20260620.jsonl",
            "source_id": "pcr02-module-agent-rules",
            "required_text": "module-local-owner-gated-control-entry-rule",
        },
        "pcr02-agent-config-boundary-20260620": {
            "md": "artifacts/manifests/pcr02-agent-config-boundary-20260620.md",
            "jsonl": "artifacts/manifests/pcr02-agent-config-boundary-20260620.jsonl",
            "source_id": "pcr02-project-agent-config",
            "required_text": "third-party-dependency-artifact",
        },
    }
    errors = []
    registry_ids = set()
    by_source_text = ""
    by_project_text = ""
    try:
        for line in (root / "registry" / "items.jsonl").read_text().splitlines():
            if line.strip():
                registry_ids.add(json.loads(line).get("id", ""))
    except Exception as exc:
        errors.append(f"registry parse: {exc}")
    try:
        by_source_text = (root / "indexes" / "by-source.md").read_text()
        by_project_text = (root / "indexes" / "by-project.md").read_text()
    except Exception as exc:
        errors.append(f"index read: {exc}")
    row_source_ids = {}
    row_counts = {}
    missing_files = []
    missing_required_text = []
    for item_id, spec in expected.items():
        md_path = root / spec["md"]
        jsonl_path = root / spec["jsonl"]
        if not md_path.exists():
            missing_files.append(spec["md"])
        if not jsonl_path.exists():
            missing_files.append(spec["jsonl"])
            continue
        rows = []
        try:
            for line in jsonl_path.read_text().splitlines():
                if line.strip():
                    rows.append(json.loads(line))
        except Exception as exc:
            errors.append(f"{spec['jsonl']} parse: {exc}")
        row_counts[item_id] = len(rows)
        row_source_ids[item_id] = sorted({row.get("source_id", "") for row in rows})
        if rows and set(row_source_ids[item_id]) != {spec["source_id"]}:
            errors.append(f"{item_id} source_id mismatch: {row_source_ids[item_id]}")
        try:
            md_text = md_path.read_text()
        except Exception as exc:
            errors.append(f"{spec['md']} read: {exc}")
            md_text = ""
        if spec["required_text"] not in md_text:
            missing_required_text.append(spec["required_text"])
    missing_registry = sorted(set(expected) - registry_ids)
    missing_by_source = [spec["md"] for spec in expected.values() if spec["md"] not in by_source_text]
    missing_by_project = [spec["md"] for spec in expected.values() if spec["md"] not in by_project_text]
    expect(
        not errors
        and not missing_files
        and not missing_registry
        and not missing_by_source
        and not missing_by_project
        and not missing_required_text
        and all(count > 0 for count in row_counts.values()),
        "pcr02-level2-boundary-manifests",
        "PCR02 Level 2 boundary manifests are registered and indexed",
        {
            "errors": errors,
            "missing_files": missing_files,
            "missing_registry": missing_registry,
            "missing_by_source": missing_by_source,
            "missing_by_project": missing_by_project,
            "missing_required_text": missing_required_text,
            "row_counts": row_counts,
            "row_source_ids": row_source_ids,
        },
    )

def test_boundary_health_internal_evidence():
    result = run_cmd(root, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    boundary_health = parsed.get("boundary_health", {}) if isinstance(parsed, dict) else {}

    repo = copy_repo("boundary-health-source-id-mismatch")
    boundary_path = repo / "artifacts" / "manifests" / "pcr02-tools-boundary-20260620.jsonl"
    rows = [json.loads(line) for line in boundary_path.read_text().splitlines() if line.strip()]
    if rows:
        rows[0]["source_id"] = "pcr02-wrong-source"
    boundary_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
    bad_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    bad_parsed = {}
    bad_parse_error = ""
    try:
        bad_parsed = json.loads(bad_result["stdout"])
    except Exception as exc:
        bad_parse_error = str(exc)
    bad_boundary_health = bad_parsed.get("boundary_health", {}) if isinstance(bad_parsed, dict) else {}
    expect(
        result["exit_code"] == 0
        and not parse_error
        and boundary_health.get("status") == "pass"
        and boundary_health.get("mode") == "read-only-internal-evidence"
        and boundary_health.get("scope") == "pcr02-level2-boundary-manifests"
        and boundary_health.get("source_project_read") is False
        and boundary_health.get("owner_gate_mutation") is False
        and boundary_health.get("memory_write") is False
        and boundary_health.get("expected_boundary_count") == 7
        and boundary_health.get("jsonl_manifest_count") == 7
        and boundary_health.get("md_manifest_count") == 7
        and boundary_health.get("row_count") == 78
        and boundary_health.get("summary", {}).get("registered_item_count") == 7
        and boundary_health.get("summary", {}).get("source_coverage_count") == 7
        and boundary_health.get("summary", {}).get("by_source_reference_count") == 7
        and boundary_health.get("summary", {}).get("by_project_reference_count") == 7
        and boundary_health.get("hard_failures") == []
        and bad_result["exit_code"] != 0
        and not bad_parse_error
        and bad_boundary_health.get("status") == "fail"
        and bad_boundary_health.get("source_id_mismatch_rows")
        and any("boundary-health:" in str(error) for error in bad_parsed.get("errors", [])),
        "boundary-health-internal-evidence",
        "boundary health is a read-only internal evidence gate for PCR02 Level 2 manifests",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "boundary_health": boundary_health,
            "bad_exit_code": bad_result["exit_code"],
            "bad_parse_error": bad_parse_error,
            "bad_boundary_health": bad_boundary_health,
            "bad_errors": bad_parsed.get("errors", [])[:5],
        },
    )

def test_status_wrong_bucket():
    repo = copy_repo("status-wrong-bucket")
    path = repo / "indexes" / "by-status.md"
    text = path.read_text()
    old = "- active: `knowledge-hub-root`"
    new = "- reviewing: `knowledge-hub-root`"
    if old not in text:
        expect(False, "status-wrong-bucket", "status bucket mismatch is rejected", {"setup_error": f"missing {old}"}, repo)
        return
    path.write_text(text.replace(old, new, 1))
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    expect(
        result["exit_code"] != 0 and "wrong status bucket" in result["stdout"],
        "status-wrong-bucket",
        "status bucket mismatch is rejected",
        {"exit_code": result["exit_code"], "expected": "wrong status bucket", "stdout_sample": result["stdout"][:1000]},
        repo,
    )

def test_status_noncanonical_only():
    repo = copy_repo("status-noncanonical-only")
    item_id = "knowledge-hub-owner-status-gate-hardening-20260619"
    path = repo / "indexes" / "by-status.md"
    text = path.read_text()
    old = f"- reviewing: `{item_id}`"
    new = f"- noncanonical-note: `{item_id}`"
    if old not in text:
        expect(False, "status-noncanonical-only", "noncanonical status mention is not enough", {"setup_error": f"missing {old}"}, repo)
        return
    path.write_text(text.replace(old, new, 1))
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    expect(
        result["exit_code"] != 0 and f"missing item {item_id}" in result["stdout"],
        "status-noncanonical-only",
        "noncanonical status mention is not enough",
        {"exit_code": result["exit_code"], "expected": f"missing item {item_id}", "stdout_sample": result["stdout"][:1000]},
        repo,
    )

def test_owner_partial_resolved():
    repo = copy_repo_with_open_owner_gates("owner-partial-resolved")
    worksheet_path = repo / "artifacts" / "manifests" / "pcr02-owner-decision-worksheets-20260618.jsonl"
    lines = worksheet_path.read_text().splitlines()
    if not lines:
        expect(False, "owner-partial-resolved", "partial owner resolution stays open", {"setup_error": "empty worksheet"}, repo)
        return
    row = json.loads(lines[0])
    row["worksheet_status"] = "owner-approved"
    row["owner_decision"] = row.get("decision_options", ["reference-only"])[0]
    lines[0] = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
    worksheet_path.write_text("\n".join(lines) + "\n")
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-owner-gates.sh", "--source-id", "pcr02-project-docs", "--json"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    expect(
        result["exit_code"] == 0 and parsed.get("open_count") == 7 and parsed.get("resolved_count") == 0,
        "owner-partial-resolved",
        "partial owner resolution stays open",
        {
            "exit_code": result["exit_code"],
            "open_count": parsed.get("open_count"),
            "resolved_count": parsed.get("resolved_count"),
            "stdout_sample": result["stdout"][:1000],
        },
        repo,
    )

def test_owner_single_form():
    repo = copy_repo_with_open_owner_gates("owner-single-form")
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
            "--forms",
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
        and parsed.get("row_count") == 1
        and parsed.get("open_count") == 1
        and len(parsed.get("decision_forms", [])) == 1,
        "owner-single-form",
        "single worksheet form output is focused",
        {
            "exit_code": result["exit_code"],
            "row_count": parsed.get("row_count"),
            "open_count": parsed.get("open_count"),
            "form_count": len(parsed.get("decision_forms", [])) if isinstance(parsed.get("decision_forms", []), list) else None,
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_forms_text_jsonl_output():
    repo = copy_repo_with_open_owner_gates("owner-forms-text-jsonl-output")
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
            "--forms",
        ],
    )
    jsonl_lines = []
    for line in result["stdout"].splitlines():
        if not line.startswith("{"):
            continue
        try:
            jsonl_lines.append(json.loads(line))
        except Exception:
            pass
    first = jsonl_lines[0] if jsonl_lines else {}
    expect(
        result["exit_code"] == 0
        and len(jsonl_lines) == 1
        and first.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and first.get("source_path") == "AGENTS.md"
        and "owner_decision" in first
        and "observed_source_identity" in first
        and "## Owner Decision JSONL Skeletons" in result["stdout"],
        "owner-forms-text-jsonl-output",
        "owner forms text mode prints copyable JSONL skeletons",
        {
            "exit_code": result["exit_code"],
            "jsonl_line_count": len(jsonl_lines),
            "worksheet_id": first.get("worksheet_id"),
            "source_path": first.get("source_path"),
            "has_owner_decision": "owner_decision" in first,
            "has_observed_source_identity": "observed_source_identity" in first,
            "stdout_sample": result["stdout"][:1200],
        },
    )

def test_owner_forms_jsonl_single_output():
    repo = copy_repo_with_open_owner_gates("owner-forms-jsonl-single-output")
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
            "--forms-jsonl",
        ],
    )
    lines = [line for line in result["stdout"].splitlines() if line.strip()]
    forms = []
    parse_errors = []
    for line in lines:
        try:
            forms.append(json.loads(line))
        except Exception as exc:
            parse_errors.append(str(exc))
    first = forms[0] if forms else {}
    identity = first.get("observed_source_identity", {}) if isinstance(first.get("observed_source_identity"), dict) else {}
    forbidden_fragments = ["# Knowledge Owner Gates", "## Owner Decision JSONL Skeletons", "```", "## 验证", "decision_forms", "\"rows\""]
    expect(
        result["exit_code"] == 0
        and len(lines) == 1
        and not parse_errors
        and first.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and first.get("source_id") == "pcr02-project-docs"
        and first.get("source_path") == "AGENTS.md"
        and first.get("status") == "open"
        and first.get("worksheet_status") == "owner-fill-required"
        and first.get("owner_decision") == ""
        and first.get("source_sha256") == ""
        and first.get("source_size") == ""
        and identity.get("identity_status") == "match"
        and identity.get("source_file_exists") is True
        and "owner_decision" in first.get("required_owner_fields", [])
        and bool(first.get("allowed_owner_decisions", []))
        and bool(first.get("target_candidates", []))
        and "reference-only" in first.get("target_candidates", [])
        and bool(first.get("must_not", []))
        and not any(fragment in result["stdout"] for fragment in forbidden_fragments),
        "owner-forms-jsonl-single-output",
        "owner forms JSONL-only mode prints one clean JSONL skeleton",
        {
            "exit_code": result["exit_code"],
            "line_count": len(lines),
            "parse_errors": parse_errors,
            "worksheet_id": first.get("worksheet_id"),
            "source_path": first.get("source_path"),
            "owner_decision": first.get("owner_decision"),
            "source_sha256": first.get("source_sha256"),
            "source_size": first.get("source_size"),
            "target_candidates": first.get("target_candidates", []),
            "identity_status": identity.get("identity_status"),
            "stdout_sample": result["stdout"][:1000],
            "stderr_sample": result["stderr"][:500],
        },
    )

def test_owner_forms_jsonl_all_open_output():
    repo = copy_repo_with_open_owner_gates("owner-forms-jsonl-all-open-output")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--forms-jsonl",
        ],
    )
    lines = [line for line in result["stdout"].splitlines() if line.strip()]
    forms = []
    parse_errors = []
    for line in lines:
        try:
            forms.append(json.loads(line))
        except Exception as exc:
            parse_errors.append(str(exc))
    worksheet_ids = {form.get("worksheet_id") for form in forms}
    identity_statuses = [
        form.get("observed_source_identity", {}).get("identity_status")
        if isinstance(form.get("observed_source_identity"), dict)
        else ""
        for form in forms
    ]
    forbidden_fragments = ["# Knowledge Owner Gates", "## Owner Decision JSONL Skeletons", "```", "## 验证", "Owner Closure Checklists", "Owner Gate Summary"]
    expect(
        result["exit_code"] == 0
        and len(lines) == 7
        and len(forms) == 7
        and not parse_errors
        and len(worksheet_ids) == 7
        and all(form.get("status") == "open" for form in forms)
        and all(status == "match" for status in identity_statuses)
        and all(form.get("owner_decision") == "" for form in forms)
        and all(form.get("source_sha256") == "" for form in forms)
        and all(form.get("source_size") == "" for form in forms)
        and all(form.get("target_candidates") for form in forms)
        and not any(fragment in result["stdout"] for fragment in forbidden_fragments),
        "owner-forms-jsonl-all-open-output",
        "owner forms JSONL-only mode prints all seven open skeletons",
        {
            "exit_code": result["exit_code"],
            "line_count": len(lines),
            "form_count": len(forms),
            "unique_worksheet_count": len(worksheet_ids),
            "parse_errors": parse_errors,
            "identity_statuses": identity_statuses,
            "target_candidate_counts": [len(form.get("target_candidates", [])) for form in forms],
            "stdout_sample": result["stdout"][:1000],
            "stderr_sample": result["stderr"][:500],
        },
    )

def test_owner_forms_jsonl_conflict_json_mode():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--forms-jsonl",
            "--json",
        ],
    )
    expect(
        result["exit_code"] != 0
        and result["stdout"] == ""
        and "cannot combine --forms-jsonl with --json" in result["stderr"],
        "owner-forms-jsonl-conflict-json-mode",
        "owner forms JSONL-only mode rejects JSON object mode",
        {
            "exit_code": result["exit_code"],
            "stdout_sample": result["stdout"][:500],
            "stderr_sample": result["stderr"][:1000],
        },
    )

def test_owner_checklist_context():
    repo = copy_repo_with_open_owner_gates("owner-checklist-context")
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
            "--checklist",
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    checklists = parsed.get("owner_checklists", [])
    first = checklists[0] if checklists else {}
    expect(
        result["exit_code"] == 0
        and parsed.get("row_count") == 1
        and len(checklists) == 1
        and first.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and "是否确认" in first.get("owner_question_zh", "")
        and first.get("hard_gate_summary") == "门禁待补证"
        and "owner_decision" in first.get("required_owner_fields", []),
        "owner-checklist-context",
        "owner checklist merges intake context with worksheet row",
        {
            "exit_code": result["exit_code"],
            "row_count": parsed.get("row_count"),
            "checklist_count": len(checklists),
            "owner_question_zh": first.get("owner_question_zh", ""),
            "hard_gate_summary": first.get("hard_gate_summary", ""),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_form_context():
    repo = copy_repo_with_open_owner_gates("owner-form-context")
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
            "--forms",
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    forms = parsed.get("decision_forms", [])
    first = forms[0] if forms else {}
    expect(
        result["exit_code"] == 0
        and parsed.get("row_count") == 1
        and len(forms) == 1
        and first.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and first.get("status") == "open"
        and first.get("worksheet_status") == "owner-fill-required"
        and "是否确认" in first.get("owner_question_zh", "")
        and first.get("default_state") == "reference-only-pending-owner-gate"
        and "reference-only" in first.get("allowed_next_status", [])
        and first.get("hard_gate_summary") == "门禁待补证"
        and bool(first.get("hard_gate", ""))
        and "owner_decision" in first.get("required_owner_fields", [])
        and "owner_decision" in first
        and first.get("owner_decision") == "",
        "owner-form-context",
        "owner decision form carries read-only intake context",
        {
            "exit_code": result["exit_code"],
            "row_count": parsed.get("row_count"),
            "form_count": len(forms),
            "owner_question_zh": first.get("owner_question_zh", ""),
            "default_state": first.get("default_state", ""),
            "hard_gate_summary": first.get("hard_gate_summary", ""),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_source_identity_context():
    repo = copy_repo_with_open_owner_gates("owner-source-identity-context")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--next-open",
            "--forms",
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    forms = parsed.get("decision_forms", [])
    first = forms[0] if forms else {}
    identity = first.get("observed_source_identity", {})
    expect(
        result["exit_code"] == 0
        and len(forms) == 1
        and first.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and identity.get("identity_status") == "match"
        and identity.get("source_identity_read_mode") == "read-bytes-for-hash"
        and identity.get("source_body_read_for_hash") is True
        and identity.get("source_body_copied") is False
        and identity.get("source_project_written") is False
        and identity.get("source_file_exists") is True
        and identity.get("observed_sha256") == identity.get("expected_sha256")
        and identity.get("observed_size") == identity.get("expected_size")
        and first.get("source_sha256") == ""
        and first.get("source_size") == "",
        "owner-source-identity-context",
        "owner decision form carries read-only source identity without filling owner fields",
        {
            "exit_code": result["exit_code"],
            "form_count": len(forms),
            "worksheet_id": first.get("worksheet_id"),
            "identity_status": identity.get("identity_status"),
            "source_identity_read_mode": identity.get("source_identity_read_mode"),
            "source_body_read_for_hash": identity.get("source_body_read_for_hash"),
            "source_file_exists": identity.get("source_file_exists"),
            "source_sha256_field": first.get("source_sha256"),
            "source_size_field": first.get("source_size"),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_prefill_candidates_manual_fields():
    repo = copy_repo_with_open_owner_gates("owner-prefill-candidates-manual-fields")
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
            "--forms",
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    forms = parsed.get("decision_forms", [])
    first = forms[0] if forms else {}
    identity = first.get("observed_source_identity", {})
    prefill = first.get("read_only_prefill_candidates", {})
    field_readiness = prefill.get("field_readiness", [])
    readiness_by_field = {item.get("field"): item for item in field_readiness if isinstance(item, dict)}
    expect(
        result["exit_code"] == 0
        and len(forms) == 1
        and first.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and first.get("owner_decision") == ""
        and first.get("target_decision") == ""
        and first.get("reviewed_by") == ""
        and first.get("reviewed_at") == ""
        and first.get("source_sha256") == ""
        and first.get("source_size") == ""
        and first.get("evidence_refs") == []
        and prefill.get("read_only") is True
        and prefill.get("no_owner_decision_generated") is True
        and prefill.get("source_sha256_candidate") == identity.get("observed_sha256")
        and prefill.get("source_size_candidate") == identity.get("observed_size")
        and bool(prefill.get("evidence_ref_candidates", []))
        and "owner_decision" in prefill.get("formal_owner_fields_remain_manual", [])
        and readiness_by_field.get("owner_decision", {}).get("readiness") == "enum-choice-required"
        and readiness_by_field.get("source_sha256", {}).get("readiness") == "copy-from-source-identity"
        and readiness_by_field.get("evidence_refs", {}).get("readiness") == "owner-ready-evidence-ref-candidate",
        "owner-prefill-candidates-manual-fields",
        "owner form exposes read-only prefill candidates without filling owner fields",
        {
            "exit_code": result["exit_code"],
            "form_count": len(forms),
            "owner_decision": first.get("owner_decision"),
            "target_decision": first.get("target_decision"),
            "source_sha256_field": first.get("source_sha256"),
            "source_size_field": first.get("source_size"),
            "prefill": prefill,
            "stdout_sample": result["stdout"][:1200],
        },
    )

def test_owner_evidence_readiness():
    repo = copy_repo_with_open_owner_gates("owner-evidence-readiness")
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
            "--evidence-readiness",
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    readiness = parsed.get("evidence_readiness", {})
    rows = readiness.get("rows", [])
    first = rows[0] if rows else {}
    prefill = first.get("read_only_prefill_candidates", {})
    safe_commands = [item.get("command", "") for item in first.get("safe_command_candidates", [])]
    expect(
        result["exit_code"] == 0
        and parsed.get("row_count") == 1
        and readiness.get("status") == "ready-for-owner-review"
        and readiness.get("row_count") == 1
        and first.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and first.get("readiness_status") == "ready-for-owner-review-owner-input-required"
        and first.get("source_identity_status") == "match"
        and first.get("owner_ready_package_status") == "covered"
        and "source_sha256" in first.get("mechanical_known_fields", [])
        and "source_size" in first.get("mechanical_known_fields", [])
        and "owner_decision" in first.get("owner_answer_required_fields", [])
        and bool(first.get("owner_ready_evidence_refs", []))
        and bool(first.get("safe_command_candidates", []))
        and not any(str(command).startswith("rtk bash tools/") for command in safe_commands)
        and prefill.get("no_owner_decision_generated") is True,
        "owner-evidence-readiness",
        "owner gate helper emits read-only evidence readiness for one worksheet",
        {
            "exit_code": result["exit_code"],
            "readiness_status": readiness.get("status"),
            "row_count": readiness.get("row_count"),
            "safe_commands": safe_commands,
            "first": first,
            "stdout_sample": result["stdout"][:1200],
        },
    )

def test_owner_inbox_contract():
    repo = copy_repo_with_open_owner_gates("owner-inbox-contract")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--owner",
            "project-owner",
            "--owner-inbox",
            "--json",
        ],
    )
    text_result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--owner",
            "project-owner",
            "--owner-inbox",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    inbox = parsed.get("owner_inbox", {})
    rows = inbox.get("rows", [])
    first = rows[0] if rows else {}
    commands = first.get("commands", {})
    groups = first.get("required_field_groups", {})
    prefill = first.get("read_only_prefill_candidates", {})
    route = first.get("owner_route", {})
    expect(
        result["exit_code"] == 0
        and parsed.get("row_count") == 2
        and parsed.get("open_count") == 2
        and inbox.get("status") == "ready-for-owner-review"
        and inbox.get("read_only") is True
        and inbox.get("report_only") is True
        and inbox.get("no_owner_decision_generated") is True
        and inbox.get("no_owner_gate_closed") is True
        and inbox.get("routing_owner_is_not_reviewed_by") is True
        and inbox.get("row_count") == 2
        and inbox.get("owner_counts", {}).get("project-owner") == 2
        and first.get("worksheet_id") == "pcr02-owner-decision-worksheet-005"
        and first.get("owner") == "project-owner"
        and route.get("routing_owner") == "pcr02-registry-owner"
        and route.get("no_owner_decision_generated") is True
        and groups.get("field_count", 0) >= 10
        and "owner_decision" in groups.get("manual_decision_fields", [])
        and "target_decision" in groups.get("manual_decision_fields", [])
        and "source_sha256" in groups.get("copyable_candidate_fields", [])
        and "source_size" in groups.get("copyable_candidate_fields", [])
        and bool(groups.get("evidence_fields", []))
        and first.get("owner_ready_package_status") == "covered"
        and bool(first.get("owner_ready_package_ids", []))
        and prefill.get("read_only") is True
        and prefill.get("no_owner_decision_generated") is True
        and bool(prefill.get("source_sha256_candidate", ""))
        and "--worksheet-id pcr02-owner-decision-worksheet-005 --checklist --forms" in commands.get("focus_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-005 --forms-jsonl" in commands.get("forms_jsonl_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-005 --evidence-readiness --json" in commands.get("evidence_readiness_command", "")
        and "owner-decisions.jsonl" in commands.get("validate_forms_command_template", "")
        and "owner-decisions.jsonl" in commands.get("landing_plan_command_template", "")
        and "owner-decisions.jsonl" in commands.get("landing_audit_command_template", "")
        and any("不得把 routing_owner 当 reviewed_by" in item for item in first.get("must_not", []))
        and text_result["exit_code"] == 0
        and "### 字段分组和只读候选" in text_result["stdout"]
        and "manual=`" in text_result["stdout"]
        and "read_only_prefill=`" in text_result["stdout"]
        and "validate template:" in text_result["stdout"],
        "owner-inbox-contract",
        "owner gate helper emits compact read-only owner inbox with grouped fields and safe commands",
        {
            "exit_code": result["exit_code"],
            "text_exit_code": text_result["exit_code"],
            "row_count": parsed.get("row_count"),
            "open_count": parsed.get("open_count"),
            "inbox": inbox,
            "first": first,
            "stdout_sample": result["stdout"][:1200],
            "text_stdout_sample": text_result["stdout"][:1200],
        },
    )

def test_owner_summary_all_open():
    repo = copy_repo_with_open_owner_gates("owner-summary-all-open")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--summary",
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    summary = parsed.get("owner_summary", {})
    summary_rows = summary.get("rows", [])
    owner_dispatch = summary.get("owner_dispatch", [])
    dispatch_by_owner = {row.get("owner"): row for row in owner_dispatch}
    project_owner_dispatch = dispatch_by_owner.get("project-owner", {})
    project_owner_route = project_owner_dispatch.get("owner_route", {})
    first = summary_rows[0] if summary_rows else {}
    first_owner_route = first.get("owner_route", {})
    expect(
        result["exit_code"] == 0
        and parsed.get("row_count") == 7
        and parsed.get("open_count") == 7
        and parsed.get("status") == "ok"
        and parsed.get("status_scope") == "tool-health"
        and parsed.get("owner_review_status") == "needs-owner-review"
        and parsed.get("owner_gate_status") == "owner-gates-open"
        and summary.get("status") == "needs-owner-review"
        and summary.get("row_count") == 7
        and summary.get("open_count") == 7
        and summary.get("active_exposure_count") == 0
        and summary.get("owner_ready_package_count") == 7
        and summary.get("owner_ready_missing_count") == 0
        and summary.get("owner_ready_invalid_count") == 0
        and summary.get("owner_ready_duplicate_count") == 0
        and summary.get("owner_ready_package_coverage") == "7/7"
        and summary.get("source_identity_counts", {}).get("match") == 7
        and len(owner_dispatch) == 6
        and project_owner_dispatch.get("open_count") == 2
        and project_owner_route.get("routing_owner") == "pcr02-registry-owner"
        and project_owner_route.get("no_owner_decision_generated") is True
        and "pcr02-owner-decision-worksheet-005" in project_owner_dispatch.get("worksheet_ids", [])
        and "--owner project-owner --forms-jsonl" in project_owner_dispatch.get("forms_jsonl_command", "")
        and "--owner project-owner --validate-forms '<owner-decisions.jsonl>' --json" in project_owner_dispatch.get("validate_forms_command_template", "")
        and "--owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-plan --json" in project_owner_dispatch.get("landing_plan_command_template", "")
        and "--owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-audit --json" in project_owner_dispatch.get("landing_audit_command_template", "")
        and "--owner project-owner --worksheet-id pcr02-owner-decision-worksheet-005 --checklist --forms" in project_owner_dispatch.get("next_focus_command", "")
        and len(summary_rows) == 7
        and first.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and first_owner_route.get("decision_owner_role") == "team-core-or-pcr02-docs-owner"
        and first_owner_route.get("routing_owner") == "pcr02-registry-owner"
        and first_owner_route.get("no_owner_decision_generated") is True
        and first.get("owner_ready_package_status") == "covered"
        and first.get("owner_ready_package_count") == 1
        and first.get("owner_ready_packages", [{}])[0].get("status") == "valid"
        and first.get("owner_ready_packages", [{}])[0].get("decision") == "owner-ready-no-decision"
        and first.get("owner_ready_packages", [{}])[0].get("open_gate_remains") is True
        and first.get("owner_ready_packages", [{}])[0].get("identity_status") == "match"
        and first.get("required_owner_field_count") == 13
        and "--owner team-core-or-pcr02-docs-owner" in first.get("focus_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001 --checklist --forms" in first.get("focus_command", "")
        and "decision_forms" not in parsed
        and "owner_checklists" not in parsed,
        "owner-summary-all-open",
        "owner summary gives all open gates without emitting forms or closing gates",
        {
            "exit_code": result["exit_code"],
            "status": parsed.get("status"),
            "status_scope": parsed.get("status_scope"),
            "owner_review_status": parsed.get("owner_review_status"),
            "owner_gate_status": parsed.get("owner_gate_status"),
            "row_count": parsed.get("row_count"),
            "open_count": parsed.get("open_count"),
            "summary_status": summary.get("status"),
            "summary_row_count": summary.get("row_count"),
            "owner_ready_package_coverage": summary.get("owner_ready_package_coverage"),
            "owner_ready_missing_count": summary.get("owner_ready_missing_count"),
            "owner_ready_invalid_count": summary.get("owner_ready_invalid_count"),
            "owner_ready_duplicate_count": summary.get("owner_ready_duplicate_count"),
            "identity_counts": summary.get("source_identity_counts", {}),
            "owner_dispatch": owner_dispatch,
            "first": first,
            "has_decision_forms": "decision_forms" in parsed,
            "has_owner_checklists": "owner_checklists" in parsed,
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_summary_by_owner():
    repo = copy_repo_with_open_owner_gates("owner-summary-by-owner")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--owner",
            "project-owner",
            "--summary",
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    summary = parsed.get("owner_summary", {})
    summary_rows = summary.get("rows", [])
    owner_dispatch = summary.get("owner_dispatch", [])
    dispatch = owner_dispatch[0] if owner_dispatch else {}
    handoff_packet = dispatch.get("suggested_owner_packet", {})
    owners = {row.get("owner") for row in parsed.get("rows", [])}
    worksheet_ids = {row.get("worksheet_id") for row in summary_rows}
    expect(
        result["exit_code"] == 0
        and parsed.get("owner") == "project-owner"
        and parsed.get("row_count") == 2
        and parsed.get("open_count") == 2
        and summary.get("row_count") == 2
        and summary.get("open_count") == 2
        and summary.get("owner_counts", {}).get("project-owner") == 2
        and len(owner_dispatch) == 1
        and dispatch.get("owner") == "project-owner"
        and dispatch.get("open_count") == 2
        and handoff_packet.get("status") == "ready-for-owner-review"
        and handoff_packet.get("read_only") is True
        and handoff_packet.get("suggested_local_owner_decisions_path") == "artifacts/manifests/pcr02-project-docs-project-owner-owner-decisions-YYYYMMDD.local.jsonl"
        and len(handoff_packet.get("recommended_sequence", [])) == 7
        and any(step.get("step") == "1-open-owner-inbox" and "--owner-inbox --json" in step.get("command", "") for step in handoff_packet.get("recommended_sequence", []))
        and any(step.get("step") == "4-export-forms" and "--forms-jsonl" in step.get("command", "") for step in handoff_packet.get("recommended_sequence", []))
        and any("不得由工具或 AI 代签 owner decision" in rule for rule in handoff_packet.get("must_not", []))
        and "--owner project-owner --forms-jsonl" in dispatch.get("forms_jsonl_command", "")
        and "--owner project-owner --validate-forms '<owner-decisions.jsonl>' --json" in dispatch.get("validate_forms_command_template", "")
        and "--owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-plan --json" in dispatch.get("landing_plan_command_template", "")
        and "--owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-audit --json" in dispatch.get("landing_audit_command_template", "")
        and owners == {"project-owner"}
        and worksheet_ids == {
            "pcr02-owner-decision-worksheet-005",
            "pcr02-owner-decision-worksheet-007",
        }
        and all("--owner project-owner" in row.get("focus_command", "") for row in summary_rows),
        "owner-summary-by-owner",
        "owner summary can filter open gates by exact owner",
        {
            "exit_code": result["exit_code"],
            "owner": parsed.get("owner"),
            "row_count": parsed.get("row_count"),
            "open_count": parsed.get("open_count"),
            "owner_counts": summary.get("owner_counts", {}),
            "owner_dispatch": owner_dispatch,
            "handoff_packet": handoff_packet,
            "worksheet_ids": sorted(worksheet_ids),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_handoff_packet_json():
    repo = copy_repo_with_open_owner_gates("owner-handoff-packet-json")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--owner",
            "project-owner",
            "--handoff-packet",
            "--json",
        ],
    )
    text_result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--owner",
            "project-owner",
            "--handoff-packet",
        ],
    )
    status_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-status.sh", "--json"])
    parsed = {}
    status_parsed = {}
    parse_error = ""
    status_parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    try:
        status_parsed = json.loads(status_result["stdout"])
    except Exception as exc:
        status_parse_error = str(exc)
    packets = parsed.get("owner_handoff_packets", []) if isinstance(parsed, dict) else []
    packet = packets[0] if packets else {}
    status_dispatch = status_parsed.get("owner_gates", {}).get("owner_dispatch", []) if isinstance(status_parsed, dict) else []
    project_owner_dispatch = next(
        (
            row for row in status_dispatch
            if row.get("owner") == "project-owner" and row.get("source_id") == "pcr02-project-docs"
        ),
        {},
    )
    forms_jsonl_lines = packet.get("forms_jsonl_lines", [])
    parsed_forms = []
    form_parse_errors = []
    for line in forms_jsonl_lines:
        try:
            parsed_forms.append(json.loads(line))
        except Exception as exc:
            form_parse_errors.append(str(exc))
    owner_inbox = packet.get("owner_inbox", {})
    evidence_readiness = packet.get("evidence_readiness", {})
    commands = packet.get("commands", {})
    expect(
        result["exit_code"] == 0
        and text_result["exit_code"] == 2
        and status_result["exit_code"] == 0
        and not parse_error
        and not status_parse_error
        and len(packets) == 1
        and packet.get("packet_type") == "owner-handoff"
        and packet.get("status") == "ready-for-owner-review"
        and packet.get("read_only") is True
        and packet.get("report_only") is True
        and packet.get("owner") == "project-owner"
        and packet.get("source_id") == "pcr02-project-docs"
        and packet.get("dispatch_scope_id") == "pcr02-project-docs:project-owner"
        and packet.get("source_ids") == ["pcr02-project-docs"]
        and packet.get("mixed_source_owner") is False
        and packet.get("open_count") == 2
        and packet.get("no_owner_decision_generated") is True
        and packet.get("no_owner_gate_closed") is True
        and packet.get("routing_owner_is_not_reviewed_by") is True
        and owner_inbox.get("row_count") == 2
        and evidence_readiness.get("row_count") == 2
        and len(forms_jsonl_lines) == 2
        and not form_parse_errors
        and {form.get("worksheet_id") for form in parsed_forms} == {
            "pcr02-owner-decision-worksheet-005",
            "pcr02-owner-decision-worksheet-007",
        }
        and all(not form.get("owner_decision") for form in parsed_forms)
        and "--owner project-owner --owner-inbox --json" in commands.get("owner_inbox_json_command", "")
        and "--owner project-owner --forms-jsonl" in commands.get("forms_jsonl_command", "")
        and "--owner project-owner --validate-forms '<owner-decisions.jsonl>' --json" in commands.get("validate_forms_command_template", "")
        and "--owner project-owner --handoff-packet --json" in project_owner_dispatch.get("handoff_packet_json_command", "")
        and any("不得由工具或 AI 代签 owner decision" in rule for rule in packet.get("must_not", []))
        and "decision_forms" not in parsed
        and "form_validation" not in parsed,
        "owner-handoff-packet-json",
        "owner gate helper emits a one-shot read-only handoff packet without generating owner decisions",
        {
            "exit_code": result["exit_code"],
            "text_exit_code": text_result["exit_code"],
            "status_exit_code": status_result["exit_code"],
            "parse_error": parse_error,
            "status_parse_error": status_parse_error,
            "packet": packet,
            "project_owner_dispatch": project_owner_dispatch,
            "form_parse_errors": form_parse_errors,
            "stdout_sample": result["stdout"][:1000],
            "text_stderr_sample": text_result["stderr"][:1000],
        },
    )

def test_owner_dispatch_source_scope_isolation():
    repo = copy_repo_with_open_owner_gates("owner-dispatch-source-scope-isolation")
    worksheet_path = repo / "artifacts" / "manifests" / "pcr02-owner-decision-worksheets-20260618.jsonl"
    rows = []
    for line in worksheet_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("id") == "pcr02-owner-decision-worksheet-007":
            row["source_id"] = "pcr02-project-tools"
        rows.append(row)
    worksheet_path.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n")

    owner_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-owner-gates.sh", "--summary", "--json"])
    status_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-status.sh", "--json"])
    owner_parsed = {}
    status_parsed = {}
    try:
        owner_parsed = json.loads(owner_result["stdout"])
    except Exception:
        pass
    try:
        status_parsed = json.loads(status_result["stdout"])
    except Exception:
        pass
    owner_dispatch = owner_parsed.get("owner_summary", {}).get("owner_dispatch", [])
    status_dispatch = status_parsed.get("owner_gates", {}).get("owner_dispatch", [])
    owner_project_dispatches = [row for row in owner_dispatch if row.get("owner") == "project-owner"]
    status_project_dispatches = [row for row in status_dispatch if row.get("owner") == "project-owner"]
    expected_sources = {"pcr02-project-docs", "pcr02-project-tools"}

    def scoped_dispatch_ok(dispatch_rows):
        source_ids = {row.get("source_id") for row in dispatch_rows}
        commands_ok = all(
            row.get("source_id")
            and f"--source-id {row.get('source_id')}" in row.get("owner_inbox_json_command", "")
            and f"--source-id {row.get('source_id')}" in row.get("forms_jsonl_command", "")
            and row.get("dispatch_scope_id") == f"{row.get('source_id')}:project-owner"
            and row.get("source_ids") == [row.get("source_id")]
            and row.get("mixed_source_owner") is False
            for row in dispatch_rows
        )
        worksheet_scope_ok = all(
            (
                row.get("source_id") == "pcr02-project-docs"
                and row.get("worksheet_ids") == ["pcr02-owner-decision-worksheet-005"]
            )
            or (
                row.get("source_id") == "pcr02-project-tools"
                and row.get("worksheet_ids") == ["pcr02-owner-decision-worksheet-007"]
            )
            for row in dispatch_rows
        )
        return len(dispatch_rows) == 2 and source_ids == expected_sources and commands_ok and worksheet_scope_ok

    expect(
        owner_result["exit_code"] == 0
        and status_result["exit_code"] in {0, 1}
        and scoped_dispatch_ok(owner_project_dispatches)
        and scoped_dispatch_ok(status_project_dispatches),
        "owner-dispatch-source-scope-isolation",
        "owner dispatch keeps same-owner multi-source gates in separate executable source scopes",
        {
            "owner_exit_code": owner_result["exit_code"],
            "status_exit_code": status_result["exit_code"],
            "owner_project_dispatches": owner_project_dispatches,
            "status_project_dispatches": status_project_dispatches,
            "owner_stdout_sample": owner_result["stdout"][:1200],
            "status_stdout_sample": status_result["stdout"][:1200],
        },
        repo,
    )

def test_manifest_regression_count_capture_qualifier():
    manifests = sorted((root / "artifacts" / "manifests").glob("knowledge-hub-*20260623.md"))
    count_patterns = [
        re.compile(r"\d+\s*个\s*regression\s*场景"),
        re.compile(r"\d+\s*个\s*回归\s*场景"),
        re.compile(r"回归覆盖扩展到\s*\d+\s*项"),
        re.compile(r"回归覆盖说明更新到\s*\d+\s*项"),
    ]
    qualifier_patterns = [
        "历史捕获",
        "当次捕获",
        "本次运行",
        "以 live 输出为准",
        "以 live 回归输出为准",
        "以 `tools/knowledge-regression.sh --json`",
        "registry 实时派生值",
        "不应作为固定历史事实手工维护",
    ]
    violations = []
    for manifest in manifests:
        if manifest.name == "knowledge-hub-governance-regression-helper-20260619.md":
            continue
        for line_no, line in enumerate(manifest.read_text().splitlines(), start=1):
            if not any(pattern.search(line) for pattern in count_patterns):
                continue
            if any(qualifier in line for qualifier in qualifier_patterns):
                continue
            violations.append(
                {
                    "path": str(manifest.relative_to(root)),
                    "line": line_no,
                    "text": line.strip(),
                }
            )
    expect(
        not violations,
        "manifest-regression-count-capture-qualifier",
        "dated governance manifests qualify fixed regression counts as historical captures",
        {"violations": violations},
    )

def test_manifest_profile_boundary_advisory():
    json_result = run_cmd(root, ["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", "manifest", "--json"])
    text_result = run_cmd(root, ["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", "manifest"])
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(json_result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    manifest_index = parsed.get("indexes", {}).get("by_manifest", {}) if isinstance(parsed, dict) else {}
    summary = manifest_index.get("summary", {})
    profile_health = summary.get("profile_health", {})
    profile_next_actions = summary.get("profile_health_next_actions_zh", {})
    rows = manifest_index.get("rows", [])
    advisory_rows = [row for row in rows if row.get("profile_health") == "advisory-missing-boundary"]
    expect(
        json_result["exit_code"] == 0
        and text_result["exit_code"] == 0
        and not parse_error
        and profile_health.get("advisory-missing-boundary", 0) >= 1
        and "missing-boundary" not in profile_health
        and advisory_rows
        and "advisory-* 仅提示人工补强方向" in summary.get("profile_health_zh", "")
        and "不回填历史正文" in profile_next_actions.get("advisory-missing-boundary", "")
        and "后续新增治理 manifest" in profile_next_actions.get("advisory-missing-boundary", "")
        and "当前 profile 基础字段缺失" in profile_next_actions.get("missing-summary", "")
        and "advisory-missing-boundary" in text_result["stdout"]
        and "missing-summary/missing-evidence" in text_result["stdout"],
        "manifest-profile-boundary-advisory",
        "manifest profile reports missing boundaries as advisory rather than hard-failure-looking status",
        {
            "json_exit_code": json_result["exit_code"],
            "text_exit_code": text_result["exit_code"],
            "parse_error": parse_error,
            "profile_health": profile_health,
            "profile_health_next_actions_zh": profile_next_actions,
            "advisory_sample": advisory_rows[:3],
            "profile_health_zh": summary.get("profile_health_zh", ""),
            "stdout_sample": text_result["stdout"][:1200],
        },
    )

def test_owner_next_open_focus():
    repo = copy_repo_with_open_owner_gates("owner-next-open-focus")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--next-open",
            "--checklist",
            "--forms",
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    checklists = parsed.get("owner_checklists", [])
    forms = parsed.get("decision_forms", [])
    first_row = parsed.get("rows", [{}])[0] if parsed.get("rows") else {}
    first_form = forms[0] if forms else {}
    expect(
        result["exit_code"] == 0
        and parsed.get("next_open") is True
        and parsed.get("row_count") == 1
        and parsed.get("open_count") == 1
        and len(checklists) == 1
        and len(forms) == 1
        and first_row.get("id") == "pcr02-owner-decision-worksheet-001"
        and first_form.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and "是否确认" in first_form.get("owner_question_zh", ""),
        "owner-next-open-focus",
        "owner gate helper focuses next open worksheet without manual worksheet id",
        {
            "exit_code": result["exit_code"],
            "next_open": parsed.get("next_open"),
            "row_count": parsed.get("row_count"),
            "open_count": parsed.get("open_count"),
            "worksheet_id": first_row.get("id"),
            "form_count": len(forms),
            "checklist_count": len(checklists),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_status_next_owner_gate():
    repo = copy_repo_with_open_owner_gates("status-next-owner-gate")
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-status.sh", "--json"])
    strict_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-status.sh", "--strict", "--json"])
    expected_final_gate_command = "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json"
    if today_source != "system-date":
        expected_final_gate_command = f"rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --as-of {today.isoformat()} --json"
    parsed = {}
    strict_parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    try:
        strict_parsed = json.loads(strict_result["stdout"])
    except Exception:
        pass
    next_open = parsed.get("owner_gates", {}).get("next_open", {})
    owner_gates = parsed.get("owner_gates", {})
    owner_dispatch = parsed.get("owner_gates", {}).get("owner_dispatch", [])
    dispatch_by_owner = {row.get("owner"): row for row in owner_dispatch}
    project_owner_dispatch = dispatch_by_owner.get("project-owner", {})
    project_owner_handoff_packet = project_owner_dispatch.get("suggested_owner_packet", {})
    project_owner_route = project_owner_dispatch.get("owner_route", {})
    summary_commands = parsed.get("owner_gates", {}).get("summary_commands", [])
    owner_summary_commands = parsed.get("owner_gates", {}).get("owner_summary_commands", [])
    owner_forms_jsonl_commands = parsed.get("owner_gates", {}).get("owner_forms_jsonl_commands", [])
    owner_evidence_readiness_commands = parsed.get("owner_gates", {}).get("owner_evidence_readiness_commands", [])
    owner_validate_forms_command_templates = parsed.get("owner_gates", {}).get("owner_validate_forms_command_templates", [])
    owner_landing_plan_command_templates = parsed.get("owner_gates", {}).get("owner_landing_plan_command_templates", [])
    owner_landing_audit_command_templates = parsed.get("owner_gates", {}).get("owner_landing_audit_command_templates", [])
    forms_jsonl_commands = parsed.get("owner_gates", {}).get("forms_jsonl_commands", [])
    evidence_readiness_commands = parsed.get("owner_gates", {}).get("evidence_readiness_commands", [])
    validate_forms_command_templates = parsed.get("owner_gates", {}).get("validate_forms_command_templates", [])
    landing_plan_command_templates = parsed.get("owner_gates", {}).get("landing_plan_command_templates", [])
    landing_audit_command_templates = parsed.get("owner_gates", {}).get("landing_audit_command_templates", [])
    final_gate_command = parsed.get("final_gate_command", "")
    next_actions = parsed.get("next_actions_zh", [])
    owner_blocker_source = strict_parsed.get("owner_blocker_source", {})
    strict_blockers = strict_parsed.get("strict_blockers", [])
    owner_blocker = next(
        (blocker for blocker in strict_blockers if blocker.get("id") == "owner-gates-open"),
        {},
    )
    next_open_queue = owner_gates.get("next_open_queue", [])
    first_queue_row = next_open_queue[0] if next_open_queue else {}
    second_queue_row = next_open_queue[1] if len(next_open_queue) > 1 else {}
    queue_executable_commands = []
    for row in next_open_queue:
        for field in ["focus_command", "forms_jsonl_command", "evidence_readiness_command"]:
            queue_executable_commands.append(str(row.get(field, "")))
    queue_template_commands = []
    for row in next_open_queue:
        for field in ["validate_forms_command_template", "landing_plan_command_template", "landing_audit_command_template"]:
            queue_template_commands.append(str(row.get(field, "")))
    expect(
        result["exit_code"] == 0
        and strict_result["exit_code"] == 1
        and parsed.get("status") == "needs-owner-review"
        and strict_parsed.get("strict") is True
        and strict_parsed.get("status") == "needs-owner-review"
        and owner_blocker_source.get("status_source") == "knowledge-status --strict"
        and "owner-gates-open" in owner_blocker_source.get("strict_blocker_ids", [])
        and owner_blocker_source.get("owner_gate_open_count_field") == "owner_gates.open_count"
        and owner_blocker_source.get("open_count") == 7
        and owner_blocker_source.get("owner_ready_package_coverage") == "7/7"
        and owner_blocker_source.get("owner_ready_row_status_source") == "knowledge-owner-gates.rows[].owner_ready_package_status"
        and owner_blocker_source.get("owner_ready_row_schema_error_count") == 0
        and owner_blocker_source.get("active_exposure_count") == 0
        and owner_gates.get("owner_ready_package_count") == 7
        and owner_gates.get("owner_ready_missing_count") == 0
        and owner_gates.get("owner_ready_invalid_count") == 0
        and owner_gates.get("owner_ready_duplicate_count") == 0
        and owner_gates.get("owner_ready_package_coverage") == "7/7"
        and owner_gates.get("owner_ready_row_status_source") == "knowledge-owner-gates.rows[].owner_ready_package_status"
        and owner_gates.get("owner_ready_row_schema_errors") == []
        and len(owner_dispatch) == 6
        and project_owner_dispatch.get("open_count") == 2
        and project_owner_handoff_packet.get("status") == "ready-for-owner-review"
        and project_owner_handoff_packet.get("read_only") is True
        and owner_gates.get("source_identity_read_policy", {}).get("source_body_read_for_hash") is True
        and owner_gates.get("source_identity_read_policy", {}).get("source_body_copied") is False
        and owner_gates.get("source_identity_read_policy", {}).get("source_project_written") is False
        and project_owner_handoff_packet.get("suggested_local_owner_decisions_path") == "artifacts/manifests/pcr02-project-docs-project-owner-owner-decisions-YYYYMMDD.local.jsonl"
        and project_owner_handoff_packet.get("source_identity_read_policy", {}).get("source_body_read_for_hash") is True
        and len(project_owner_handoff_packet.get("recommended_sequence", [])) == 7
        and all(step.get("notes_zh") for step in project_owner_handoff_packet.get("recommended_sequence", []))
        and any(step.get("step") == "1-open-owner-inbox" and "--owner-inbox --json" in step.get("command", "") for step in project_owner_handoff_packet.get("recommended_sequence", []))
        and any(step.get("step") == "5-validate-filled-forms" and "owner-decisions.jsonl" in step.get("command_template", "") for step in project_owner_handoff_packet.get("recommended_sequence", []))
        and project_owner_route.get("routing_owner") == "pcr02-registry-owner"
        and project_owner_route.get("no_owner_decision_generated") is True
        and "pcr02-owner-decision-worksheet-005" in project_owner_dispatch.get("worksheet_ids", [])
        and "--owner project-owner --owner-inbox --json" in project_owner_dispatch.get("owner_inbox_json_command", "")
        and "--owner project-owner --forms-jsonl" in project_owner_dispatch.get("forms_jsonl_command", "")
        and "--owner project-owner --evidence-readiness --json" in project_owner_dispatch.get("evidence_readiness_command", "")
        and "--owner project-owner --validate-forms '<owner-decisions.jsonl>' --json" in project_owner_dispatch.get("validate_forms_command_template", "")
        and "--owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-plan --json" in project_owner_dispatch.get("landing_plan_command_template", "")
        and "--owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-audit --json" in project_owner_dispatch.get("landing_audit_command_template", "")
        and "--owner project-owner --worksheet-id pcr02-owner-decision-worksheet-005 --checklist --forms" in project_owner_dispatch.get("next_focus_command", "")
        and any("--summary" in str(command) for command in summary_commands)
        and any("--owner project-owner" in str(command) and "--summary" in str(command) for command in owner_summary_commands)
        and any("--owner project-owner" in str(command) and "--forms-jsonl" in str(command) for command in owner_forms_jsonl_commands)
        and any("--owner project-owner" in str(command) and "--evidence-readiness --json" in str(command) for command in owner_evidence_readiness_commands)
        and any("--owner project-owner" in str(command) and "--validate-forms" in str(command) and "owner-decisions.jsonl" in str(command) for command in owner_validate_forms_command_templates)
        and any("--owner project-owner" in str(command) and "--landing-plan" in str(command) and "owner-decisions.jsonl" in str(command) for command in owner_landing_plan_command_templates)
        and any("--owner project-owner" in str(command) and "--landing-audit" in str(command) and "owner-decisions.jsonl" in str(command) for command in owner_landing_audit_command_templates)
        and any("--forms-jsonl" in str(command) for command in forms_jsonl_commands)
        and any("--evidence-readiness --json" in str(command) for command in evidence_readiness_commands)
        and any("--validate-forms" in str(command) and "owner-decisions.jsonl" in str(command) and "--json" in str(command) for command in validate_forms_command_templates)
        and any("--validate-forms" in str(command) and "owner-decisions.jsonl" in str(command) and "--landing-plan" in str(command) and "--json" in str(command) for command in landing_plan_command_templates)
        and any("--validate-forms" in str(command) and "owner-decisions.jsonl" in str(command) and "--landing-audit" in str(command) and "--json" in str(command) for command in landing_audit_command_templates)
        and final_gate_command == expected_final_gate_command
        and next_open.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and next_open.get("owner_route", {}).get("routing_owner") == "pcr02-registry-owner"
        and next_open.get("owner_route", {}).get("no_owner_decision_generated") is True
        and "--next-open" in next_open.get("next_open_command", "")
        and "--checklist" in next_open.get("next_open_command", "")
        and "--forms" in next_open.get("next_open_command", "")
        and "--next-open" in next_open.get("next_open_forms_jsonl_command", "")
        and "--forms-jsonl" in next_open.get("next_open_forms_jsonl_command", "")
        and "--next-open" in next_open.get("next_open_evidence_readiness_command", "")
        and "--evidence-readiness" in next_open.get("next_open_evidence_readiness_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001" in next_open.get("focus_command", "")
        and "--checklist" in next_open.get("focus_command", "")
        and "--forms" in next_open.get("focus_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001" in next_open.get("focus_forms_jsonl_command", "")
        and "--forms-jsonl" in next_open.get("focus_forms_jsonl_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001" in next_open.get("focus_evidence_readiness_command", "")
        and "--evidence-readiness" in next_open.get("focus_evidence_readiness_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001" in next_open.get("focus_validate_forms_command_template", "")
        and "--validate-forms" in next_open.get("focus_validate_forms_command_template", "")
        and "owner-decisions.jsonl" in next_open.get("focus_validate_forms_command_template", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001" in next_open.get("focus_landing_plan_command_template", "")
        and "--validate-forms" in next_open.get("focus_landing_plan_command_template", "")
        and "--landing-plan" in next_open.get("focus_landing_plan_command_template", "")
        and "owner-decisions.jsonl" in next_open.get("focus_landing_plan_command_template", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001" in next_open.get("focus_landing_audit_command_template", "")
        and "--validate-forms" in next_open.get("focus_landing_audit_command_template", "")
        and "--landing-audit" in next_open.get("focus_landing_audit_command_template", "")
        and "owner-decisions.jsonl" in next_open.get("focus_landing_audit_command_template", "")
        and owner_gates.get("next_open_queue_count") == 7
        and owner_gates.get("next_open_queue_selection_order") == "review_after, worksheet_id"
        and len(next_open_queue) == 7
        and first_queue_row.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and first_queue_row.get("source_path") == "AGENTS.md"
        and first_queue_row.get("owner_ready_package_status") == "covered"
        and first_queue_row.get("owner_ready_source") == "knowledge-owner-gates.rows[].owner_ready_package_status"
        and first_queue_row.get("owner_ready_package_status_source") == "knowledge-owner-gates.owner_ready_state"
        and first_queue_row.get("owner_ready_package_count") == 1
        and "pcr02-agents-owner-ready-package-20260620" in first_queue_row.get("owner_ready_package_ids", [])
        and "--worksheet-id pcr02-owner-decision-worksheet-001 --checklist --forms" in first_queue_row.get("focus_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001 --forms-jsonl" in first_queue_row.get("forms_jsonl_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001 --evidence-readiness --json" in first_queue_row.get("evidence_readiness_command", "")
        and "owner-decisions.jsonl" in first_queue_row.get("validate_forms_command_template", "")
        and second_queue_row.get("worksheet_id") == "pcr02-owner-decision-worksheet-002"
        and second_queue_row.get("source_path") == "standards/diag-command-metadata-standard.md"
        and second_queue_row.get("owner") == "pcr02-diag-owner-or-team-core"
        and second_queue_row.get("owner_ready_package_status") == "covered"
        and second_queue_row.get("owner_ready_source") == "knowledge-owner-gates.rows[].owner_ready_package_status"
        and second_queue_row.get("owner_ready_package_status_source") == "knowledge-owner-gates.owner_ready_state"
        and second_queue_row.get("owner_ready_package_count") == 1
        and not any("owner-decisions.jsonl" in command for command in queue_executable_commands)
        and any("owner-decisions.jsonl" in command and "--landing-plan" in command for command in queue_template_commands)
        and any("owner-decisions.jsonl" in command and "--landing-audit" in command for command in queue_template_commands)
        and any("--summary" in str(action) for action in next_actions)
        and any("--owner" in str(action) and "--summary" in str(action) for action in next_actions)
        and any("owner_gates.owner_dispatch[]" in str(action) for action in next_actions)
        and any("--owner" in str(action) and "--forms-jsonl" in str(action) for action in next_actions)
        and any("--owner" in str(action) and "--evidence-readiness" in str(action) for action in next_actions)
        and any("--owner" in str(action) and "--validate-forms" in str(action) for action in next_actions)
        and any("--owner" in str(action) and "--landing-plan" in str(action) for action in next_actions)
        and any("--owner" in str(action) and "--landing-audit" in str(action) for action in next_actions)
        and any("knowledge-final-gate.sh" in str(action) and "--json" in str(action) for action in next_actions)
        and any("--next-open --checklist --forms" in str(action) for action in next_actions)
        and any("--next-open --forms-jsonl" in str(action) for action in next_actions)
        and any("--next-open --evidence-readiness --json" in str(action) for action in next_actions)
        and any("--validate-forms" in str(action) and "owner-decisions.jsonl" in str(action) for action in next_actions)
        and any("--landing-plan" in str(action) for action in next_actions)
        and any("--landing-audit" in str(action) for action in next_actions)
        and owner_blocker.get("count") == 7
        and any("--summary" in str(command) for command in owner_blocker.get("commands", []))
        and any("--owner project-owner" in str(command) and "--summary" in str(command) for command in owner_blocker.get("commands", []))
        and any("--owner project-owner" in str(command) and "--forms-jsonl" in str(command) for command in owner_blocker.get("commands", []))
        and any("--owner project-owner" in str(command) and "--evidence-readiness --json" in str(command) for command in owner_blocker.get("commands", []))
        and any("--next-open --checklist --forms" in str(command) for command in owner_blocker.get("commands", []))
        and any("--next-open --forms-jsonl" in str(command) for command in owner_blocker.get("commands", []))
        and any("--next-open --evidence-readiness --json" in str(command) for command in owner_blocker.get("commands", []))
        and not any("owner-decisions.jsonl" in str(command) for command in owner_blocker.get("commands", []))
        and any("--owner project-owner" in str(command) and "--validate-forms" in str(command) and "owner-decisions.jsonl" in str(command) for command in owner_blocker.get("command_templates", []))
        and any("--owner project-owner" in str(command) and "--landing-plan" in str(command) and "owner-decisions.jsonl" in str(command) for command in owner_blocker.get("command_templates", []))
        and any("--owner project-owner" in str(command) and "--landing-audit" in str(command) and "owner-decisions.jsonl" in str(command) for command in owner_blocker.get("command_templates", []))
        and any("--validate-forms" in str(command) and "owner-decisions.jsonl" in str(command) for command in owner_blocker.get("command_templates", []))
        and any("--landing-plan" in str(command) for command in owner_blocker.get("command_templates", []))
        and any("--landing-audit" in str(command) for command in owner_blocker.get("command_templates", []))
        and owner_blocker.get("owner_blocker_source", {}).get("open_count") == 7,
        "status-next-owner-gate",
        "status dashboard separates executable owner commands from validation and landing templates",
        {
            "exit_code": result["exit_code"],
            "strict_exit_code": strict_result["exit_code"],
            "status": parsed.get("status"),
            "strict_status": strict_parsed.get("status"),
            "owner_ready_package_coverage": owner_gates.get("owner_ready_package_coverage"),
            "owner_ready_missing_count": owner_gates.get("owner_ready_missing_count"),
            "owner_ready_invalid_count": owner_gates.get("owner_ready_invalid_count"),
            "owner_ready_duplicate_count": owner_gates.get("owner_ready_duplicate_count"),
            "owner_dispatch": owner_dispatch,
            "project_owner_handoff_packet": project_owner_handoff_packet,
            "worksheet_id": next_open.get("worksheet_id"),
            "summary_commands": summary_commands,
            "owner_summary_commands": owner_summary_commands,
            "owner_forms_jsonl_commands": owner_forms_jsonl_commands,
            "owner_evidence_readiness_commands": owner_evidence_readiness_commands,
            "owner_validate_forms_command_templates": owner_validate_forms_command_templates,
            "owner_landing_plan_command_templates": owner_landing_plan_command_templates,
            "owner_landing_audit_command_templates": owner_landing_audit_command_templates,
            "forms_jsonl_commands": forms_jsonl_commands,
            "evidence_readiness_commands": evidence_readiness_commands,
            "validate_forms_command_templates": validate_forms_command_templates,
            "landing_plan_command_templates": landing_plan_command_templates,
            "landing_audit_command_templates": landing_audit_command_templates,
            "final_gate_command": final_gate_command,
            "expected_final_gate_command": expected_final_gate_command,
            "next_open_command": next_open.get("next_open_command", ""),
            "next_open_forms_jsonl_command": next_open.get("next_open_forms_jsonl_command", ""),
            "next_open_evidence_readiness_command": next_open.get("next_open_evidence_readiness_command", ""),
            "focus_command": next_open.get("focus_command", ""),
            "focus_forms_jsonl_command": next_open.get("focus_forms_jsonl_command", ""),
            "focus_evidence_readiness_command": next_open.get("focus_evidence_readiness_command", ""),
            "focus_validate_forms_command_template": next_open.get("focus_validate_forms_command_template", ""),
            "focus_landing_plan_command_template": next_open.get("focus_landing_plan_command_template", ""),
            "focus_landing_audit_command_template": next_open.get("focus_landing_audit_command_template", ""),
            "next_open_queue_count": owner_gates.get("next_open_queue_count"),
            "next_open_queue": next_open_queue,
            "owner_blocker_source": owner_blocker_source,
            "strict_blockers": strict_blockers,
            "next_actions_zh": next_actions,
            "stdout_sample": result["stdout"][:1000],
            "strict_stdout_sample": strict_result["stdout"][:1000],
        },
    )

def test_status_owner_ready_source_no_registry_fallback():
    source = (root / "tools" / "knowledge-status.sh").read_text()
    banned_fragments = [
        "covered\" if owner_ready_packages or registry_items else \"missing",
        "owner_ready_package_ids = [str(item.get(\"id\", \"\")) for item in registry_items",
        "owner_ready_package_count\": len(owner_ready_packages) if owner_ready_packages else len(registry_items)",
    ]
    required_fragments = [
        "OWNER_READY_ROW_STATUS_SOURCE = \"knowledge-owner-gates.rows[].owner_ready_package_status\"",
        "\"owner_ready_source\": OWNER_READY_ROW_STATUS_SOURCE",
        "\"id\": \"owner-ready-row-schema-missing\"",
    ]
    present_banned = [fragment for fragment in banned_fragments if fragment in source]
    missing_required = [fragment for fragment in required_fragments if fragment not in source]
    expect(
        not present_banned and not missing_required,
        "status-owner-ready-source-no-registry-fallback",
        "status next_open_queue owner-ready state comes from owner-gates row validation, not registry_items fallback",
        {
            "present_banned_fragments": present_banned,
            "missing_required_fragments": missing_required,
        },
    )

def test_final_gate_maintenance_entry_wording_no_section_drift():
    source = (root / "tools" / "knowledge-final-gate.sh").read_text()
    banned_fragments = [
        "第七节 8 类长期维护入口",
        "第七节长期维护入口",
    ]
    required_fragments = [
        "docs/goals 中列出的 8 类长期维护入口和 1 个离线维护包均有文档、工具或回归证据。",
        "docs/goals 中列出的 8 类长期维护入口和 1 个离线维护包均可恢复；只证明入口存在，不代表人工动作已完成。",
    ]
    present_banned = [fragment for fragment in banned_fragments if fragment in source]
    missing_required = [fragment for fragment in required_fragments if fragment not in source]
    expect(
        not present_banned and not missing_required,
        "final-gate-maintenance-entry-wording-no-section-drift",
        "final gate maintenance entry wording points to docs/goals instead of stale section numbering",
        {
            "present_banned_fragments": present_banned,
            "missing_required_fragments": missing_required,
        },
    )

def test_stable_governance_command_examples():
    scan_paths = [
        "README.md",
        "tools/README.md",
        "templates/README.md",
        "governance",
        "indexes",
    ]
    banned_patterns = [
        ("repo-relative-tool-command", "rtk bash tools/"),
        ("short-knowledge-check-command", "`knowledge-check --dry-run"),
        ("bare-knowledge-check-command", "knowledge-check --dry-run --json --diagnostics"),
        ("weak-validation-ref", 'validation_refs":["tools/knowledge-check.sh --dry-run'),
    ]
    findings = []
    for relative in scan_paths:
        path = root / relative
        paths = [path]
        if path.is_dir():
            paths = sorted(child for child in path.rglob("*") if child.is_file())
        for file_path in paths:
            try:
                text = file_path.read_text()
            except Exception as exc:
                findings.append({
                    "file": str(file_path.relative_to(root)),
                    "pattern_id": "read-error",
                    "line": 0,
                    "sample": str(exc),
                })
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                for pattern_id, needle in banned_patterns:
                    if needle not in line:
                        continue
                    if needle == "knowledge-check --dry-run --json --diagnostics" and "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics" in line:
                        continue
                    findings.append({
                        "file": str(file_path.relative_to(root)),
                        "pattern_id": pattern_id,
                        "line": line_no,
                        "sample": line.strip()[:240],
                    })
    expect(
        not findings,
        "stable-governance-command-examples",
        "governance docs and templates use cwd-stable rtk command examples",
        {
            "scan_paths": scan_paths,
            "banned_patterns": [row[0] for row in banned_patterns],
            "findings": findings,
        },
    )

def test_status_text_owner_summary_commands():
    repo = copy_repo_with_open_owner_gates("status-text-owner-summary-commands")
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-status.sh"])
    expect(
        result["exit_code"] == 0
        and "- owner summary commands:" in result["stdout"]
        and "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary" in result["stdout"]
        and "- owner forms-jsonl commands:" in result["stdout"]
        and "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --forms-jsonl" in result["stdout"]
        and "- owner validate-forms command templates:" in result["stdout"]
        and "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --json" in result["stdout"]
        and "- owner landing plan command templates:" in result["stdout"]
        and "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-plan --json" in result["stdout"]
        and "- owner landing audit command templates:" in result["stdout"]
        and "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-audit --json" in result["stdout"]
        and "- review_after command: `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date`" in result["stdout"]
        and "- review_after near-due command: `rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of " in result["stdout"]
        and " --window-days 30 --json`" in result["stdout"]
        and "- source check report command: `rtk bash ~/knowledge-hub/tools/knowledge-source-check.sh --scope pcr02-level2 --as-of " in result["stdout"],
        "status-text-owner-summary-commands",
        "status text mode exposes owner dispatch, owner validation templates, review_after and source-check report commands",
        {
            "exit_code": result["exit_code"],
            "has_owner_summary_heading": "- owner summary commands:" in result["stdout"],
            "has_project_owner_summary": "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary" in result["stdout"],
            "has_project_owner_forms_jsonl": "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --forms-jsonl" in result["stdout"],
            "has_project_owner_validate_forms": "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --json" in result["stdout"],
            "has_project_owner_landing_plan": "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-plan --json" in result["stdout"],
            "has_project_owner_landing_audit": "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-audit --json" in result["stdout"],
            "has_review_after_command": "- review_after command: `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date`" in result["stdout"],
            "has_review_after_near_due_command": "- review_after near-due command: `rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of " in result["stdout"],
            "has_source_check_report_command": "- source check report command: `rtk bash ~/knowledge-hub/tools/knowledge-source-check.sh --scope pcr02-level2 --as-of " in result["stdout"],
            "stdout_sample": result["stdout"][:1200],
        },
    )

def test_status_owner_gates_exit_code_blocker():
    repo = copy_repo("status-owner-gates-exit-code-blocker")
    owner_gates_path = repo / "tools" / "knowledge-owner-gates.sh"
    owner_gates_path.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' '{\"schema_version\":1,\"row_count\":0,\"open_count\":0,\"active_exposure_count\":0,\"owner_ready_package_count\":0}'\n"
        "printf '%s\\n' 'fixture owner-gates failure' >&2\n"
        "exit 1\n"
    )
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-status.sh", "--strict", "--json"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    blocker = next(
        (
            item
            for item in parsed.get("strict_blockers", [])
            if item.get("id") == "owner-gates-command-failed"
        ),
        {},
    )
    expect(
        result["exit_code"] == 1
        and parsed.get("status") == "needs-fix"
        and blocker.get("severity") == "blocker"
        and blocker.get("exit_code") == 1
        and "fixture owner-gates failure" in blocker.get("stderr_sample", ""),
        "status-owner-gates-exit-code-blocker",
        "status dashboard blocks non-zero owner-gates child command even when JSON is parseable",
        {
            "exit_code": result["exit_code"],
            "status": parsed.get("status"),
            "strict_blockers": parsed.get("strict_blockers", []),
            "owner_gates": parsed.get("owner_gates", {}),
            "stdout_sample": result["stdout"][:1200],
            "stderr_sample": result["stderr"][:500],
        },
        repo,
    )

def test_final_gate_owner_review_blocker():
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
        expect(
            True,
            "final-gate-owner-review-blocker",
            "final gate includes check, regression and strict owner blockers",
            {"skipped_in_inner_final_gate": True},
        )
        return
    repo = copy_repo_with_open_owner_gates("final-gate-owner-review-blocker")
    setup_error = init_temp_git_repo(repo)
    if setup_error:
        expect(False, "final-gate-owner-review-blocker", "final gate includes check, regression and strict owner blockers", setup_error, repo)
        return
    result = run_cmd(repo, ["rtk", "bash", "-lc", "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    final_gate_summary = parsed.get("summary", {})
    checks = parsed.get("checks", {})
    blockers = parsed.get("blockers", [])
    automatic_governance = parsed.get("automatic_governance", {})
    owner_recovery = parsed.get("owner_recovery", {})
    review_queue_recovery = parsed.get("review_queue_recovery", {})
    review_queue_summary = review_queue_recovery.get("summary", {})
    review_queue_commands = review_queue_recovery.get("commands", {})
    owner_dispatch = owner_recovery.get("owner_dispatch", [])
    dispatch_by_owner = {row.get("owner"): row for row in owner_dispatch}
    project_owner_dispatch = dispatch_by_owner.get("project-owner", {})
    project_owner_route = project_owner_dispatch.get("owner_route", {})
    next_open_recovery = owner_recovery.get("next_open", {})
    owner_recovery_queue = owner_recovery.get("next_open_queue", [])
    first_recovery_queue_row = owner_recovery_queue[0] if owner_recovery_queue else {}
    second_recovery_queue_row = owner_recovery_queue[1] if len(owner_recovery_queue) > 1 else {}
    recovery_queue_executable_commands = []
    for row in owner_recovery_queue:
        for field in ["focus_command", "forms_jsonl_command", "evidence_readiness_command"]:
            recovery_queue_executable_commands.append(str(row.get(field, "")))
    final_state_audit = parsed.get("final_state_audit", {})
    maintenance_entry_audit = parsed.get("maintenance_entry_audit", {})
    maintenance_entries = maintenance_entry_audit.get("entries", [])
    maintenance_entry_ids = [row.get("entry_id") for row in maintenance_entries]
    maintenance_entries_by_id = {row.get("entry_id"): row for row in maintenance_entries}
    linking_audit = parsed.get("linking_audit", {})
    linking_summary = linking_audit.get("summary", {})
    proof_artifacts = parsed.get("proof_artifacts", {})
    legacy_proof_artifacts = parsed.get("proof_artifacts_20260622", {})
    source_check_snapshot = parsed.get("source_check_execution_snapshot_20260621", {})
    source_check_runtime = parsed.get("source_check_runtime", {})
    highest_priority_rules_audit = parsed.get("highest_priority_rules_audit", [])
    rules_by_id = {row.get("rule_id"): row for row in highest_priority_rules_audit}
    evidence_index = parsed.get("evidence_index", [])
    evidence_by_artifact = {row.get("related_artifact"): row for row in evidence_index}
    level1 = final_state_audit.get("level1_pcr02_docs", {})
    level2 = final_state_audit.get("level2_pcr02_candidate_sources", {})
    level3 = final_state_audit.get("level3_registered_sources", {})
    proof_rows = proof_artifacts.get("rows", [])
    proof_seed_ids = proof_artifacts.get("seed_ids", [])
    proof_dynamic_ids = proof_artifacts.get("dynamic_ids", [])
    proof_expected_ids = proof_artifacts.get("expected_ids", [])
    proof_baseline_dynamic_ids = proof_artifacts.get("baseline_dynamic_ids", [])
    proof_selection_dynamic_ids = proof_artifacts.get("selection_dynamic_ids", [])
    proof_baseline_selection_overlap_ids = proof_artifacts.get("baseline_selection_overlap_ids", [])
    expected_source_check_runtime_command = (
        f"rtk bash tools/knowledge-source-check.sh --scope pcr02-level2 --json --as-of {parsed.get('today')}"
    )
    level2_boundary_health = level2.get("boundary_health", {})
    level2_source_check_snapshot = level2.get("source_check_execution_snapshot", {})
    level2_source_check_runtime = level2.get("source_check_runtime", {})
    level3_source_check_health = level3.get("source_check_health", {})
    level3_source_coverage_selection = level3.get("source_coverage_selection", {})
    gap_map = parsed.get("gap_map", [])
    owner_blocker = next(
        (blocker for blocker in blockers if blocker.get("id") == "owner-gates-open"),
        {},
    )
    owner_gap = next(
        (gap for gap in gap_map if gap.get("gap_id") == "owner-gates-open"),
        {},
    )
    expect(
        result["exit_code"] == 1
        and parsed.get("final_status") == "needs-owner-review"
        and automatic_governance.get("status") == "complete-except-owner-review"
        and automatic_governance.get("complete") is True
        and automatic_governance.get("core_checks_pass") is True
        and automatic_governance.get("only_owner_review_blockers") is True
        and automatic_governance.get("remaining_owner_gate_count") == 7
        and automatic_governance.get("owner_ready_package_coverage") == "7/7"
        and automatic_governance.get("active_exposure_count") == 0
        and automatic_governance.get("no_owner_decision_generated") is True
        and automatic_governance.get("owner_blocker_source", {}).get("status_source") == "knowledge-status --strict"
        and "owner-gates-open" in automatic_governance.get("owner_blocker_source", {}).get("strict_blocker_ids", [])
        and automatic_governance.get("owner_blocker_source", {}).get("owner_gate_open_count_field") == "owner_gates.open_count"
        and final_gate_summary.get("final_status") == "needs-owner-review"
        and final_gate_summary.get("automatic_governance_status") == "complete-except-owner-review"
        and final_gate_summary.get("level1_status") == "complete-except-owner-review"
        and final_gate_summary.get("level2_status") == "complete"
        and final_gate_summary.get("level3_status") == "complete"
        and final_gate_summary.get("level1_owner_gate_open_count") == 7
        and final_gate_summary.get("proof_artifacts_status") == "pass"
        and final_gate_summary.get("maintenance_entry_audit_status") == "pass"
        and final_gate_summary.get("linking_audit_status") == "pass"
        and final_gate_summary.get("cross_session_status") == "pass"
        and final_gate_summary.get("cross_project_status") == "pass"
        and final_gate_summary.get("markdown_index_recovery_status") == "pass"
        and "Level 1" in final_gate_summary.get("section_refs", [])
        and "七.2" in final_gate_summary.get("section_refs", [])
        and "九" in final_gate_summary.get("section_refs", [])
        and owner_recovery.get("open_count") == 7
        and owner_recovery.get("owner_ready_package_coverage") == "7/7"
        and owner_recovery.get("active_exposure_count") == 0
        and review_queue_recovery.get("read_only") is True
        and review_queue_recovery.get("report_only") is True
        and review_queue_summary.get("total_pending_count", 0) >= 1
        and review_queue_summary.get("ai_generated_pending_count", 0) >= 1
        and review_queue_summary.get("active_or_promotion_blocker_count") == 0
        and review_queue_commands.get("index_plan") == "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --json"
        and review_queue_commands.get("recommended_batch_json") == "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --queue-type ai-human-review --queue-owner leiwenjun --queue-limit 20 --json"
        and review_queue_commands.get("recommended_forms_jsonl") == "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --queue-type ai-human-review --queue-owner leiwenjun --queue-limit 20 --queue-forms-jsonl"
        and review_queue_commands.get("recommended_validate_queue_forms") == "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --queue-type ai-human-review --queue-owner leiwenjun --queue-limit 20 --json --validate-queue-forms '<review-queue-forms.jsonl>'"
        and "不得写 ~/.codex/memories" in " ".join(review_queue_recovery.get("must_not", []))
        and "普通 AI/外部资料待复核项不阻断 final gate" in review_queue_recovery.get("notes_zh", "")
        and len(owner_dispatch) == 6
        and project_owner_dispatch.get("open_count") == 2
        and project_owner_route.get("routing_owner") == "pcr02-registry-owner"
        and project_owner_route.get("no_owner_decision_generated") is True
        and "pcr02-owner-decision-worksheet-005" in project_owner_dispatch.get("worksheet_ids", [])
        and next_open_recovery.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and next_open_recovery.get("owner_route", {}).get("routing_owner") == "pcr02-registry-owner"
        and next_open_recovery.get("owner_route", {}).get("no_owner_decision_generated") is True
        and owner_recovery.get("next_open_queue_count") == 7
        and owner_recovery.get("next_open_queue_selection_order") == "review_after, worksheet_id"
        and len(owner_recovery_queue) == 7
        and first_recovery_queue_row.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and first_recovery_queue_row.get("source_path") == "AGENTS.md"
        and first_recovery_queue_row.get("owner_ready_package_status") == "covered"
        and first_recovery_queue_row.get("owner_ready_package_count") == 1
        and second_recovery_queue_row.get("worksheet_id") == "pcr02-owner-decision-worksheet-002"
        and second_recovery_queue_row.get("source_path") == "standards/diag-command-metadata-standard.md"
        and second_recovery_queue_row.get("owner") == "pcr02-diag-owner-or-team-core"
        and not any("owner-decisions.jsonl" in command for command in recovery_queue_executable_commands)
        and level1.get("status") == "complete-except-owner-review"
        and level1.get("source_id") == "pcr02-project-docs"
        and level1.get("expected_owner_gate_count") == 7
        and "pcr02-owner-decision-worksheets-20260618.jsonl" in level1.get("expected_owner_gate_count_source", "")
        and level1.get("worksheet_count") == 1
        and level1.get("worksheet_row_count") == 7
        and level1.get("owner_gate_open_count") == 7
        and level1.get("owner_gate_count_matches_expected") is True
        and level1.get("owner_ready_package_count") == 7
        and level1.get("owner_ready_expected_count") == 7
        and level1.get("owner_ready_package_coverage") == "7/7"
        and level1.get("active_exposure_count") == 0
        and level1.get("no_owner_decision_generated") is True
        and "artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl" in level1.get("evidence_refs", [])
        and level2.get("status") == "complete"
        and level2.get("registered_count") == 7
        and level2.get("covered_count") == 7
        and level2.get("missing_source_ids") == []
        and level2.get("missing_coverage_ids") == []
        and level2_boundary_health.get("status") == "pass"
        and level2_boundary_health.get("mode") == "read-only-internal-evidence"
        and level2_boundary_health.get("summary", {}).get("registered_item_count") == 7
        and level2_boundary_health.get("source_project_read") is False
        and level2_boundary_health.get("owner_gate_mutation") is False
        and level2_boundary_health.get("memory_write") is False
        and level2_source_check_snapshot.get("status") == "pass"
        and level2_source_check_snapshot.get("runtime_execution") is False
        and level2_source_check_snapshot.get("source_check_health_contract") == "static-registry-only"
        and level2_source_check_snapshot.get("row_count") == 7
        and level2_source_check_snapshot.get("passed_count") == 7
        and level2_source_check_snapshot.get("missing_source_ids") == []
        and level2_source_check_snapshot.get("failed_rows") == []
        and level2_source_check_runtime.get("status") == "pass"
        and level2_source_check_runtime.get("runtime_execution") is True
        and level2_source_check_runtime.get("read_only") is True
        and level2_source_check_runtime.get("report_only") is True
        and level2_source_check_runtime.get("source_body_read") is False
        and level2_source_check_runtime.get("owner_gate_mutation") is False
        and level2_source_check_runtime.get("memory_write") is False
        and level2_source_check_runtime.get("automation_write") is False
        and level2_source_check_runtime.get("source_check_health_executed") is False
        and level2_source_check_runtime.get("row_count") == 7
        and level2_source_check_runtime.get("passed_count") == 7
        and level2_source_check_runtime.get("failed_count") == 0
        and "registry/sources.json" in level2.get("evidence_refs", [])
        and "artifacts/manifests/pcr02-level2-source-check-execution-snapshot-20260621.md" in level2.get("evidence_refs", [])
        and "runtime:checks.source_check_runtime" in level2.get("evidence_refs", [])
        and level3.get("status") == "complete"
        and level3.get("registered_count") == level3.get("covered_count")
        and level3.get("registered_count") == 13
        and level3_source_coverage_selection.get("selected") == level3.get("latest_coverage_manifest")
        and level3.get("missing_coverage_ids") == []
        and level3.get("missing_final_state_fields") == []
        and level3_source_check_health.get("executed") is False
        and level3_source_check_health.get("with_check_count") == 9
        and level3_source_check_health.get("with_no_check_reason_count") == 4
        and level3_source_check_health.get("missing_check_or_reason_ids") == []
        and level3_source_check_health.get("non_rtk_check_ids") == []
        and "tools/knowledge-check.sh --dry-run --json --diagnostics" in level3.get("evidence_refs", [])
        and legacy_proof_artifacts == proof_artifacts
        and proof_artifacts.get("status") == "pass"
        and proof_artifacts.get("selection_mode") == "seed-plus-dynamic-governance-by-as-of-date"
        and proof_artifacts.get("coverage_sections") == ["Level 1", "Level 2", "Level 3", "七", "七.2", "八", "九"]
        and "七.2" in proof_artifacts.get("section_refs", [])
        and any("七.2" in ref for ref in proof_artifacts.get("requirement_refs", []))
        and proof_artifacts.get("selection_date") == parsed.get("today")
        and proof_artifacts.get("dynamic_selector", {}).get("date") == parsed.get("today")
        and proof_artifacts.get("expected_count") == len(proof_expected_ids)
        and proof_artifacts.get("expected_count") == len(set(proof_seed_ids + proof_dynamic_ids))
        and proof_artifacts.get("dynamic_count") == len(proof_dynamic_ids)
        and proof_artifacts.get("baseline_dynamic_count") == len(proof_baseline_dynamic_ids)
        and proof_artifacts.get("selection_dynamic_count") == len(proof_selection_dynamic_ids)
        and proof_artifacts.get("baseline_selection_overlap_count") == len(proof_baseline_selection_overlap_ids)
        and proof_baseline_selection_overlap_ids == []
        and proof_artifacts.get("baseline_dynamic_count", 0) >= 17
        and "knowledge-hub-review-after-topic-owner-hardening-20260622" in proof_expected_ids
        and proof_artifacts.get("registered_count") == proof_artifacts.get("expected_count")
        and proof_artifacts.get("paired_count") == proof_artifacts.get("expected_count")
        and proof_artifacts.get("migration_covered_count") == proof_artifacts.get("expected_count")
        and proof_artifacts.get("indexed_count") == proof_artifacts.get("expected_count")
        and proof_artifacts.get("missing_registry") == []
        and proof_artifacts.get("missing_md") == []
        and proof_artifacts.get("missing_jsonl") == []
        and proof_artifacts.get("missing_migration") == []
        and proof_artifacts.get("missing_indexes") == {}
        and len(proof_rows) == proof_artifacts.get("expected_count")
        and all(row.get("status") == "pass" for row in proof_rows)
        and source_check_snapshot.get("status") == "pass"
        and source_check_snapshot.get("artifact_id") == "pcr02-level2-source-check-execution-snapshot-20260621"
        and source_check_snapshot.get("execution_mode") == "report-only-manual-snapshot"
        and source_check_snapshot.get("runtime_execution") is False
        and source_check_snapshot.get("source_check_health_contract") == "static-registry-only"
        and source_check_snapshot.get("expected_count") == 7
        and source_check_snapshot.get("row_count") == 7
        and source_check_snapshot.get("passed_count") == 7
        and source_check_snapshot.get("registry_present") is True
        and source_check_snapshot.get("md_exists") is True
        and source_check_snapshot.get("jsonl_exists") is True
        and source_check_snapshot.get("migration_md_ref") is True
        and source_check_snapshot.get("migration_jsonl_ref") is True
        and source_check_snapshot.get("missing_indexes") == []
        and source_check_snapshot.get("missing_source_ids") == []
        and source_check_snapshot.get("unexpected_source_ids") == []
        and source_check_snapshot.get("failed_rows") == []
        and source_check_runtime.get("status") == "pass"
        and source_check_runtime.get("command") == expected_source_check_runtime_command
        and source_check_runtime.get("runtime_execution") is True
        and source_check_runtime.get("read_only") is True
        and source_check_runtime.get("report_only") is True
        and source_check_runtime.get("scope") == "pcr02-level2"
        and source_check_runtime.get("source_check_health_contract") == "static-registry-only"
        and source_check_runtime.get("source_check_health_executed") is False
        and source_check_runtime.get("source_body_read") is False
        and source_check_runtime.get("owner_gate_mutation") is False
        and source_check_runtime.get("memory_write") is False
        and source_check_runtime.get("automation_write") is False
        and source_check_runtime.get("row_count") == 7
        and source_check_runtime.get("passed_count") == 7
        and source_check_runtime.get("failed_count") == 0
        and source_check_runtime.get("unsupported_count") == 0
        and source_check_runtime.get("rejected_count") == 0
        and source_check_runtime.get("failed_rows") == []
        and maintenance_entry_audit.get("status") == "pass"
        and "七" in maintenance_entry_audit.get("section_refs", [])
        and "七.1" in maintenance_entry_audit.get("section_refs", [])
        and "七.2" in maintenance_entry_audit.get("section_refs", [])
        and any("长期维护能力" in ref for ref in maintenance_entry_audit.get("requirement_refs", []))
        and maintenance_entry_audit.get("expected_entry_count") == 9
        and maintenance_entry_audit.get("passed_entry_count") == 9
        and maintenance_entry_audit.get("missing_entry_ids") == []
        and maintenance_entry_ids == [
            "manual-knowledge-entry",
            "source-coverage-entry",
            "manual-review-entry",
            "manual-search-entry",
            "owner-signoff-entry",
            "automation-boundary-entry",
            "quality-gate-entry",
            "chinese-readability-entry",
            "offline-maintenance-package",
        ]
        and all(row.get("evidence_refs") for row in maintenance_entries)
        and all(row.get("requirement_refs") for row in maintenance_entries)
        and all(row.get("section_refs") for row in maintenance_entries)
        and all(row.get("limitations_zh") for row in maintenance_entries)
        and "七.2" in maintenance_entries_by_id.get("offline-maintenance-package", {}).get("section_refs", [])
        and linking_audit.get("status") == "pass"
        and linking_audit.get("section_refs") == ["八", "九"]
        and linking_summary.get("status") == "pass"
        and linking_summary.get("registered_source_count") == 13
        and linking_summary.get("pcr02_level2_source_ids_present") is True
        and linking_summary.get("provenance_fields_present") is True
        and linking_summary.get("project_specific_not_team_promoted") is True
        and linking_summary.get("missing_anchors") == []
        and linking_summary.get("section_refs") == ["八", "九"]
        and linking_audit.get("read_only") is True
        and linking_audit.get("source_body_read") is False
        and linking_audit.get("owner_gate_mutation") is False
        and linking_audit.get("cross_session", {}).get("status") == "pass"
        and linking_audit.get("cross_session", {}).get("missing") == []
        and linking_audit.get("cross_project", {}).get("status") == "pass"
        and linking_audit.get("cross_project", {}).get("registered_source_count") == 13
        and linking_audit.get("cross_project", {}).get("pcr02_level2_source_ids_present") is True
        and linking_audit.get("cross_project", {}).get("provenance_fields_present") is True
        and linking_audit.get("cross_project", {}).get("project_specific_not_team_promoted") is True
        and linking_audit.get("markdown_index_recovery", {}).get("status") == "pass"
        and linking_audit.get("markdown_index_recovery", {}).get("missing_anchors") == []
        and "runtime:index_plan.indexes.by_decision" in linking_audit.get("evidence_refs", [])
        and checks.get("knowledge_check", {}).get("status") == "pass"
        and checks.get("knowledge_check", {}).get("exit_code") == 0
        and checks.get("knowledge_check", {}).get("source_check_health", {}).get("with_check_count") == 9
        and checks.get("knowledge_check", {}).get("boundary_health", {}).get("status") == "pass"
        and checks.get("git_diff_check", {}).get("status") == "pass"
        and checks.get("git_diff_check", {}).get("exit_code") == 0
        and checks.get("git_diff_check", {}).get("command") == "rtk git diff --check"
        and checks.get("knowledge_regression", {}).get("status") == "pass"
        and checks.get("knowledge_regression", {}).get("exit_code") == 0
        and checks.get("knowledge_regression", {}).get("skipped_for_self_test") is False
        and checks.get("knowledge_status_strict", {}).get("status") == "needs-owner-review"
        and checks.get("knowledge_status_strict", {}).get("exit_code") == 1
        and checks.get("source_check_runtime", {}).get("status") == "pass"
        and checks.get("source_check_runtime", {}).get("row_count") == 7
        and checks.get("index_plan_linking", {}).get("status") == "planned"
        and checks.get("index_plan_linking", {}).get("exit_code") == 0
        and checks.get("index_plan_linking", {}).get("linking_audit_status") == "pass"
        and len(evidence_index) == 10
        and all(row.get("requirement_refs") for row in evidence_index)
        and all(row.get("section_refs") for row in evidence_index)
        and evidence_by_artifact.get("knowledge-check", {}).get("status") == "pass"
        and "Level 1" in evidence_by_artifact.get("knowledge-check", {}).get("section_refs", [])
        and evidence_by_artifact.get("knowledge-regression", {}).get("status") == "pass"
        and evidence_by_artifact.get("git-diff-check", {}).get("status") == "pass"
        and evidence_by_artifact.get("knowledge-status", {}).get("status") == "owner-review"
        and "六" in evidence_by_artifact.get("knowledge-status", {}).get("section_refs", [])
        and evidence_by_artifact.get("knowledge-status", {}).get("evidence_path") == "runtime:checks.knowledge_status_strict"
        and evidence_by_artifact.get("owner-blocker-provenance", {}).get("status") == "owner-review"
        and evidence_by_artifact.get("owner-blocker-provenance", {}).get("evidence_path") == "runtime:automatic_governance.owner_blocker_source"
        and evidence_by_artifact.get("pcr02-level2-source-check-execution-snapshot-20260621", {}).get("status") == "pass"
        and evidence_by_artifact.get("pcr02-level2-source-check-execution-snapshot-20260621", {}).get("layer") == "source-check-snapshot"
        and "Level 2" in evidence_by_artifact.get("pcr02-level2-source-check-execution-snapshot-20260621", {}).get("section_refs", [])
        and evidence_by_artifact.get("knowledge-source-check-runtime", {}).get("status") == "pass"
        and evidence_by_artifact.get("knowledge-source-check-runtime", {}).get("layer") == "source-check-runtime"
        and evidence_by_artifact.get("maintenance-entry-audit", {}).get("status") == "pass"
        and evidence_by_artifact.get("maintenance-entry-audit", {}).get("evidence_path") == "runtime:maintenance_entry_audit"
        and "七.2" in evidence_by_artifact.get("maintenance-entry-audit", {}).get("section_refs", [])
        and evidence_by_artifact.get("linking-audit", {}).get("status") == "pass"
        and evidence_by_artifact.get("linking-audit", {}).get("evidence_path") == "runtime:linking_audit"
        and evidence_by_artifact.get("linking-audit", {}).get("section_refs") == ["八", "九"]
        and evidence_by_artifact.get("review-queue-recovery", {}).get("status") == "pass"
        and evidence_by_artifact.get("review-queue-recovery", {}).get("evidence_path") == "runtime:review_queue_recovery"
        and len(highest_priority_rules_audit) == 11
        and rules_by_id.get("shell-through-rtk", {}).get("status") == "pass"
        and rules_by_id.get("manual-write-apply-patch", {}).get("status") == "process-audited"
        and rules_by_id.get("no-memory-write", {}).get("status") == "pass"
        and rules_by_id.get("no-source-project-modification", {}).get("status") == "pass"
        and rules_by_id.get("no-project-specific-standards-promotion", {}).get("status") == "pass"
        and rules_by_id.get("automation-report-only", {}).get("status") == "pass"
        and rules_by_id.get("single-canonical-body", {}).get("status") == "pass"
        and rules_by_id.get("session-archive-not-active-facts", {}).get("status") == "pass"
        and rules_by_id.get("respect-existing-worktree-changes", {}).get("status") == "process-audited"
        and rules_by_id.get("subagent-single-writer-readonly", {}).get("status") == "process-audited"
        and rules_by_id.get("evidence-before-completion", {}).get("status") == "pass"
        and owner_blocker.get("count") == 7
        and len(gap_map) == 1
        and owner_gap.get("gap_type") == "owner-review"
        and owner_gap.get("source_id") == "pcr02-project-docs"
        and owner_gap.get("codex_auto_can_complete") is False
        and owner_gap.get("requires_owner_decision") is True
        and owner_gap.get("status") == "open",
        "final-gate-owner-review-blocker",
        "final gate includes automatic governance state and owner gap map",
        {
            "exit_code": result["exit_code"],
            "final_status": parsed.get("final_status"),
            "summary": final_gate_summary,
            "automatic_governance": automatic_governance,
            "owner_recovery": owner_recovery,
            "final_state_audit": final_state_audit,
            "proof_artifacts": proof_artifacts,
            "proof_artifacts_20260622": legacy_proof_artifacts,
            "source_check_execution_snapshot_20260621": source_check_snapshot,
            "source_check_runtime": source_check_runtime,
            "maintenance_entry_audit": maintenance_entry_audit,
            "linking_audit": linking_audit,
            "highest_priority_rules_audit": highest_priority_rules_audit,
            "level3_source_coverage_selection": level3_source_coverage_selection,
            "checks": checks,
            "evidence_index": evidence_index,
            "blockers": blockers,
            "gap_map": gap_map,
            "stdout_sample": result["stdout"][:1200],
        },
    )

def test_final_gate_skip_regression_blocker():
    result = run_cmd(root, ["rtk", "bash", "-lc", "KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    checks = parsed.get("checks", {})
    evidence_index = parsed.get("evidence_index", [])
    evidence_by_artifact = {row.get("related_artifact"): row for row in evidence_index}
    blocker = next(
        (
            item
            for item in parsed.get("blockers", [])
            if item.get("id") == "knowledge-regression-skipped"
        ),
        {},
    )
    gap = next(
        (
            item
            for item in parsed.get("gap_map", [])
            if item.get("gap_id") == "knowledge-regression-skipped"
        ),
        {},
    )
    expect(
        result["exit_code"] == 1
        and parsed.get("final_status") == "needs-fix"
        and parsed.get("automatic_governance", {}).get("status") == "needs-fix"
        and parsed.get("automatic_governance", {}).get("core_checks_pass") is False
        and checks.get("knowledge_regression", {}).get("skipped_for_self_test") is True
        and evidence_by_artifact.get("knowledge-regression", {}).get("status") == "skipped"
        and blocker.get("severity") == "blocker"
        and gap.get("gap_type") == "regression"
        and gap.get("codex_auto_can_complete") is True,
        "final-gate-skip-regression-blocker",
        "final gate rejects regression self-test skip as terminal completion evidence",
        {
            "exit_code": result["exit_code"],
            "final_status": parsed.get("final_status"),
            "automatic_governance": parsed.get("automatic_governance", {}),
            "checks": checks,
            "evidence_index": evidence_index,
            "blockers": parsed.get("blockers", []),
            "gap_map": parsed.get("gap_map", []),
            "stdout_sample": result["stdout"][:1200],
        },
    )

def test_final_gate_empty_child_json_blocker():
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
        expect(
            True,
            "final-gate-empty-child-json-blocker",
            "final gate empty child JSON fixture is skipped inside nested regression",
            {"skipped_in_inner_final_gate": True},
        )
        return
    repo = copy_repo("final-gate-empty-child-json-blocker")
    check_path = repo / "tools" / "knowledge-check.sh"
    check_path.write_text("#!/usr/bin/env bash\nexit 0\n")
    result = run_cmd(
        repo,
        ["rtk", "bash", "-lc", "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json"],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    checks = parsed.get("checks", {})
    blocker = next(
        (
            item
            for item in parsed.get("blockers", [])
            if item.get("id") == "knowledge-check-unparseable"
        ),
        {},
    )
    expect(
        result["exit_code"] == 1
        and parsed.get("final_status") == "needs-fix"
        and checks.get("knowledge_check", {}).get("parse_error") == "empty JSON output"
        and blocker.get("severity") == "blocker",
        "final-gate-empty-child-json-blocker",
        "final gate rejects empty child JSON output even when child exits zero",
        {
            "exit_code": result["exit_code"],
            "final_status": parsed.get("final_status"),
            "checks": checks,
            "blockers": parsed.get("blockers", []),
            "stdout_sample": result["stdout"][:1200],
            "stderr_sample": result["stderr"][:500],
        },
        repo,
    )

def test_final_gate_default_regression_path():
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
        expect(
            True,
            "final-gate-default-regression-path",
            "final gate default path is skipped inside nested regression",
            {"skipped_in_inner_final_gate": True},
        )
        return
    result = run_cmd(root, ["rtk", "bash", "-lc", "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    checks = parsed.get("checks", {})
    regression_command = checks.get("knowledge_regression", {}).get("command", "")
    expect(
        result["exit_code"] == 0
        and parsed.get("final_status") == "ok"
        and checks.get("knowledge_regression", {}).get("status") == "pass"
        and checks.get("knowledge_regression", {}).get("exit_code") == 0
        and checks.get("knowledge_regression", {}).get("result_count", 0) >= 1
        and checks.get("knowledge_regression", {}).get("skipped_for_self_test") is False
        and "knowledge-regression.sh --json --as-of" in regression_command
        and checks.get("git_diff_check", {}).get("status") == "pass"
        and checks.get("knowledge_status_strict", {}).get("status") == "ok"
        and checks.get("knowledge_status_strict", {}).get("exit_code") == 0,
        "final-gate-default-regression-path",
        "final gate default path executes regression and reaches ok after owner decisions land",
        {
            "exit_code": result["exit_code"],
            "final_status": parsed.get("final_status"),
            "regression_command": regression_command,
            "checks": checks,
            "stdout_sample": result["stdout"][:1200],
            "stderr_sample": result["stderr"][:500],
        },
    )

def test_final_gate_source_final_state_field_gap():
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
        expect(
            True,
            "final-gate-source-final-state-field-gap",
            "final gate source final-state fixture is skipped inside nested regression",
            {"skipped_in_inner_final_gate": True},
        )
        return
    repo = copy_repo("final-gate-source-field-gap")
    sources_path = repo / "registry" / "sources.json"
    data = json.loads(sources_path.read_text())
    target_found = False
    for source in data.get("sources", []):
        if source.get("id") == "pcr02-project-tools":
            source.pop("final_disposition", None)
            target_found = True
            break
    if not target_found:
        expect(
            False,
            "final-gate-source-final-state-field-gap",
            "final gate exposes typed source final-state field gaps",
            {"setup_error": "pcr02-project-tools source fixture not found"},
            repo,
        )
        return
    sources_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    run_cmd(repo, ["rtk", "git", "init"])
    result = run_cmd(
        repo,
        ["rtk", "bash", "-lc", "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json"],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    gap_map = parsed.get("gap_map", [])
    typed_gap = next(
        (
            gap
            for gap in gap_map
            if gap.get("gap_id") == "source-final-state-field-missing:pcr02-project-tools:final_disposition"
        ),
        {},
    )
    expect(
        result["exit_code"] == 1
        and parsed.get("final_status") == "needs-fix"
        and typed_gap.get("gap_type") == "registry"
        and typed_gap.get("source_id") == "pcr02-project-tools"
        and typed_gap.get("field") == "final_disposition"
        and typed_gap.get("codex_auto_can_complete") is True
        and typed_gap.get("requires_owner_decision") is False,
        "final-gate-source-final-state-field-gap",
        "final gate exposes typed source final-state field gaps",
        {
            "exit_code": result["exit_code"],
            "final_status": parsed.get("final_status"),
            "gap_map": gap_map,
            "stdout_sample": result["stdout"][:1200],
            "stderr_sample": result["stderr"][:500],
        },
        repo,
    )

def test_final_gate_strict_status_nonowner_blocker():
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
        expect(
            True,
            "final-gate-strict-status-nonowner-blocker",
            "final gate strict status non-owner blocker fixture is skipped inside nested regression",
            {"skipped_in_inner_final_gate": True},
        )
        return
    repo = copy_repo("final-gate-strict-status-nonowner-blocker")
    status_path = repo / "tools" / "knowledge-status.sh"
    status_path.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' '{\"schema_version\":1,\"status\":\"needs-fix\",\"strict\":true,\"knowledge_check\":{\"exit_code\":0,\"status\":\"pass\"},\"owner_gates\":{\"open_count\":7,\"owner_ready_package_coverage\":\"7/7\",\"active_exposure_count\":0},\"sources\":{\"latest_coverage_manifest\":\"artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.jsonl\",\"latest_coverage_selection\":{\"selected\":\"artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.jsonl\"}},\"strict_blockers\":[{\"id\":\"owner-gates-command-failed\",\"severity\":\"blocker\",\"count\":1,\"summary_zh\":\"fixture non-owner blocker\"}]}'\n"
        "exit 1\n"
    )
    result = run_cmd(
        repo,
        ["rtk", "bash", "-lc", "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json"],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    blockers = parsed.get("blockers", [])
    blocker = next((item for item in blockers if item.get("id") == "owner-gates-command-failed"), {})
    owner_gap = next((item for item in parsed.get("gap_map", []) if item.get("gap_type") == "owner-review"), {})
    expect(
        result["exit_code"] == 1
        and parsed.get("final_status") == "needs-fix"
        and parsed.get("automatic_governance", {}).get("status") == "needs-fix"
        and parsed.get("automatic_governance", {}).get("only_owner_review_blockers") is False
        and blocker.get("severity") == "blocker"
        and owner_gap == {},
        "final-gate-strict-status-nonowner-blocker",
        "final gate keeps parseable strict non-owner blockers as needs-fix",
        {
            "exit_code": result["exit_code"],
            "final_status": parsed.get("final_status"),
            "automatic_governance": parsed.get("automatic_governance", {}),
            "blockers": blockers,
            "gap_map": parsed.get("gap_map", []),
            "stdout_sample": result["stdout"][:1200],
        },
        repo,
    )

def test_final_gap_readability_positive_contracts():
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
        expect(
            True,
            "final-gap-readability-positive-contracts",
            "final gap readability contract is skipped inside nested regression",
            {"skipped_in_inner_final_gate": True},
        )
        return
    check_result = run_cmd(root, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    final_result = run_cmd(
        root,
        ["rtk", "bash", "-lc", "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json"],
    )
    check_parsed = {}
    final_parsed = {}
    try:
        check_parsed = json.loads(check_result["stdout"])
    except Exception:
        pass
    try:
        final_parsed = json.loads(final_result["stdout"])
    except Exception:
        pass
    items_path = root / "registry" / "items.jsonl"
    migrations_path = root / "registry" / "migrations.jsonl"
    sources_path = root / "registry" / "sources.json"
    readability_fields = [
        "summary_zh",
        "primary_language",
        "source_language",
        "translation_status",
        "terminology_status",
    ]
    missing_readability_fields = []
    missing_notes_zh = []
    missing_source_fields = []
    try:
        for row in [json.loads(line) for line in items_path.read_text().splitlines() if line.strip()]:
            created_at = str(row.get("created_at", ""))
            if (
                created_at >= "2026-06-21"
                and row.get("domain") == "governance"
                and row.get("kind") == "audit"
            ):
                for field in readability_fields:
                    if not str(row.get(field, "")).strip():
                        missing_readability_fields.append(f"{row.get('id')}:{field}")
    except Exception as exc:
        missing_readability_fields.append(f"parse-error:{exc}")
    try:
        for row in [json.loads(line) for line in migrations_path.read_text().splitlines() if line.strip()]:
            if str(row.get("checked_at", "")) >= "2026-06-21" and not str(row.get("notes_zh", "")).strip():
                missing_notes_zh.append(str(row.get("mode", row.get("to", "<unknown>"))))
    except Exception as exc:
        missing_notes_zh.append(f"parse-error:{exc}")
    try:
        source_required_fields = ["owner", "review_after", "migration_strategy", "final_disposition"]
        source_data = json.loads(sources_path.read_text())
        for source in source_data.get("sources", []):
            source_id = str(source.get("id", ""))
            for field in source_required_fields:
                if not str(source.get(field, "")).strip():
                    missing_source_fields.append(f"{source_id}:{field}")
            if not str(source.get("check", "")).strip() and not str(source.get("no_check_reason", "")).strip():
                missing_source_fields.append(f"{source_id}:check_or_no_check_reason")
    except Exception as exc:
        missing_source_fields.append(f"parse-error:{exc}")
    gap_map = final_parsed.get("gap_map", [])
    non_owner_gaps = [
        gap
        for gap in gap_map
        if gap.get("requires_owner_decision") is not True
        and gap.get("gap_type") not in {"owner-review"}
    ]
    expect(
        check_result["exit_code"] == 0
        and check_parsed.get("status") == "pass"
        and final_result["exit_code"] == 0
        and final_parsed.get("final_status") == "ok"
        and not missing_readability_fields
        and not missing_notes_zh
        and not missing_source_fields
        and not non_owner_gaps,
        "final-gap-readability-positive-contracts",
        "current repository satisfies final gap and readability positive contracts after owner decisions land",
        {
            "knowledge_check_exit_code": check_result["exit_code"],
            "knowledge_check_status": check_parsed.get("status"),
            "final_gate_exit_code": final_result["exit_code"],
            "final_status": final_parsed.get("final_status"),
            "missing_readability_fields": missing_readability_fields,
            "missing_notes_zh": missing_notes_zh,
            "missing_source_fields": missing_source_fields,
            "non_owner_gaps": non_owner_gaps,
            "final_stdout_sample": final_result["stdout"][:1200],
        },
    )

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
    form["status_reason"] = "Regression fixture for owner decision compatibility."
    for field in form.get("required_owner_fields", []):
        value = form.get(field)
        if value in (None, "") or value == [] or value == {}:
            form[field] = f"fixture-{field}"
    return form, {}

def test_owner_validate_forms_partial_coverage_warning():
    repo = copy_repo_with_open_owner_gates("owner-validate-forms-partial-coverage")
    form, setup_error = make_valid_owner_decision_form(repo)
    if setup_error:
        expect(False, "owner-validate-forms-partial-coverage-warning", "owner validate-forms reports partial coverage without blocking valid subset forms", setup_error, repo)
        return
    form_path = repo / "partial-owner-decisions.jsonl"
    form_path.write_text(json.dumps(form, ensure_ascii=False, separators=(",", ":")) + "\n")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--validate-forms",
            str(form_path),
            "--landing-plan",
            "--landing-audit",
            "--json",
        ],
    )
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    validation = parsed.get("form_validation", {}) if isinstance(parsed, dict) else {}
    coverage = validation.get("coverage", {}) if isinstance(validation, dict) else {}
    landing_plan = parsed.get("landing_plan", {}) if isinstance(parsed, dict) else {}
    landing_audit = parsed.get("landing_audit", {}) if isinstance(parsed, dict) else {}
    expect(
        result["exit_code"] == 0
        and not parse_error
        and validation.get("status") == "pass"
        and validation.get("coverage_status") == "partial"
        and coverage.get("filtered_open_count") == 7
        and coverage.get("submitted_open_count") == 1
        and form.get("worksheet_id") in coverage.get("submitted_worksheet_ids", [])
        and len(coverage.get("missing_open_worksheet_ids", [])) == 6
        and validation.get("warning_count") == 1
        and landing_plan.get("status") == "planned"
        and landing_plan.get("landing_scope", {}).get("coverage_status") == "partial"
        and len(landing_plan.get("remaining_open_after_this_batch", [])) == 6
        and landing_audit.get("status") == "ready-for-manual-landing"
        and landing_audit.get("landing_scope", {}).get("coverage_status") == "partial"
        and len(landing_audit.get("remaining_open_after_this_batch", [])) == 6,
        "owner-validate-forms-partial-coverage-warning",
        "owner validate-forms reports partial coverage without blocking valid subset forms",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "form_status": validation.get("status"),
            "coverage": coverage,
            "warning_count": validation.get("warning_count"),
            "landing_plan_status": landing_plan.get("status"),
            "landing_scope": landing_plan.get("landing_scope", {}),
            "remaining_open_after_this_batch": landing_plan.get("remaining_open_after_this_batch", []),
            "landing_audit_status": landing_audit.get("status"),
            "stdout_sample": result["stdout"][:1200],
            "stderr_sample": result["stderr"][:1000],
        },
        repo,
    )

def test_owner_archive_only_target_path_compatibility():
    repo = copy_repo_with_open_owner_gates("owner-archive-only-target-path")
    form, setup_error = make_owner_decision_form_for_worksheet(repo, "pcr02-owner-decision-worksheet-007")
    if setup_error:
        expect(False, "owner-archive-only-target-path-compatibility", "owner archive-only forms can target explicit archive paths", setup_error, repo)
        return
    archive_target = "domains/projects/pcr02/archive/reports/2026-06-16-dvr-record-replay-session-archive.md"
    form["owner_decision"] = "archive-only"
    form["target_decision"] = archive_target
    form_path = repo / "archive-owner-decisions.jsonl"
    form_path.write_text(json.dumps(form, ensure_ascii=False, separators=(",", ":")) + "\n")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--worksheet-id",
            "pcr02-owner-decision-worksheet-007",
            "--validate-forms",
            str(form_path),
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    diagnostics = parsed.get("form_validation", {}).get("diagnostics", [])
    expect(
        result["exit_code"] == 0
        and parsed.get("form_validation", {}).get("status") == "pass"
        and not any(row.get("code") == "owner-decision-target-mismatch" for row in diagnostics),
        "owner-archive-only-target-path-compatibility",
        "owner archive-only forms can target explicit archive paths",
        {
            "exit_code": result["exit_code"],
            "validation_status": parsed.get("form_validation", {}).get("status"),
            "diagnostics": diagnostics,
            "target_decision": archive_target,
            "stdout_sample": result["stdout"][:1000],
        },
        repo,
    )

def test_owner_archive_only_rejects_non_archive_target():
    repo = copy_repo_with_open_owner_gates("owner-archive-only-rejects-non-archive")
    form, setup_error = make_owner_decision_form_for_worksheet(repo, "pcr02-owner-decision-worksheet-007")
    if setup_error:
        expect(False, "owner-archive-only-rejects-non-archive-target", "owner archive-only forms reject validation or decision targets", setup_error, repo)
        return
    form["owner_decision"] = "archive-only"
    form["target_decision"] = "domains/projects/pcr02/validation/"
    form_path = repo / "archive-owner-decisions.jsonl"
    form_path.write_text(json.dumps(form, ensure_ascii=False, separators=(",", ":")) + "\n")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-owner-gates.sh",
            "--source-id",
            "pcr02-project-docs",
            "--worksheet-id",
            "pcr02-owner-decision-worksheet-007",
            "--validate-forms",
            str(form_path),
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
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
        and mismatch_diagnostic.get("worksheet_id") == "pcr02-owner-decision-worksheet-007"
        and "/archive/" in str(mismatch_diagnostic.get("expected", "")),
        "owner-archive-only-rejects-non-archive-target",
        "owner archive-only forms reject validation or decision targets",
        {
            "exit_code": result["exit_code"],
            "validation_status": parsed.get("form_validation", {}).get("status"),
            "diagnostics": diagnostics,
            "mismatch_diagnostic": mismatch_diagnostic,
            "stdout_sample": result["stdout"][:1000],
        },
        repo,
    )

def test_owner_landing_plan_project_index():
    repo = copy_repo_with_open_owner_gates("owner-landing-plan-project-index")
    form, setup_error = make_valid_owner_decision_form(repo)
    if setup_error:
        expect(False, "owner-landing-plan-project-index", "owner landing plan requires by-project index", setup_error, repo)
        return
    temp_root = pathlib.Path(tempfile.mkdtemp(prefix="kh-regression-owner-landing-plan-"))
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
            "--landing-plan",
            "--landing-audit",
            "--json",
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    required_files = parsed.get("landing_plan", {}).get("required_manual_files", [])
    landing_audit = parsed.get("landing_audit", {})
    owner_ready_gate = parsed.get("landing_plan", {}).get("owner_ready_gate", {})
    steps = parsed.get("landing_plan", {}).get("steps", [])
    audit_rows = landing_audit.get("rows", [])
    first_audit = audit_rows[0] if audit_rows else {}
    worksheet_resolution = first_audit.get("worksheet_resolution_status", {})
    first_step = steps[0] if steps else {}
    worksheet_cwd = first_step.get("worksheet_verification_cwd", "")
    worksheet_commands = first_step.get("worksheet_verification_commands", [])
    expect(
        result["exit_code"] == 0
        and parsed.get("landing_plan", {}).get("status") == "planned"
        and owner_ready_gate.get("status") == "pass"
        and owner_ready_gate.get("error_count") == 0
        and "artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl" in required_files
        and "artifacts/manifests/*owner-decision-worksheets-*.jsonl" not in required_files
        and "indexes/by-project.md" in required_files
        and "indexes/by-source.md" in required_files
        and "indexes/by-status.md" in required_files
        and "indexes/by-decision.md" in required_files
        and landing_audit.get("status") == "ready-for-manual-landing"
        and landing_audit.get("read_only") is True
        and "artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl" in landing_audit.get("required_manual_files", [])
        and "artifacts/manifests/*owner-decision-worksheets-*.jsonl" not in landing_audit.get("required_manual_files", [])
        and "indexes/by-source.md" in landing_audit.get("required_manual_files", [])
        and "indexes/by-decision.md" in landing_audit.get("required_manual_files", [])
        and worksheet_resolution.get("must_update_worksheet_row") is True
        and "owner_decision" in worksheet_resolution.get("required_fields", [])
        and "reviewed_by" in worksheet_resolution.get("required_fields", [])
        and first_audit.get("expected_manual_deltas", {}).get("worksheet_jsonl")
        and "indexes/by-source.md" in first_audit.get("expected_manual_deltas", {}).get("indexes", [])
        and "indexes/by-decision.md" in first_audit.get("expected_manual_deltas", {}).get("indexes", [])
        and any("knowledge-final-gate.sh" in str(command) for command in first_audit.get("post_landing_commands", []))
        and worksheet_cwd.endswith("/xcrz_sigmastar_demo")
        and bool(worksheet_commands)
        and any("knowledge-check.sh" in str(command) for command in worksheet_commands),
        "owner-landing-plan-project-index",
        "owner landing plan requires worksheet/index manual deltas and carries worksheet verification cwd and commands",
        {
            "exit_code": result["exit_code"],
            "landing_status": parsed.get("landing_plan", {}).get("status"),
            "landing_audit": landing_audit,
            "owner_ready_gate": owner_ready_gate,
            "required_manual_files": required_files,
            "worksheet_verification_cwd": worksheet_cwd,
            "worksheet_verification_commands": worksheet_commands,
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_form_target_decision_candidate_gate():
    repo = copy_repo_with_open_owner_gates("owner-form-target-decision-candidate-gate")
    form, setup_error = make_valid_owner_decision_form(repo)
    if setup_error:
        expect(False, "owner-form-target-decision-candidate-gate", "owner form rejects target decisions outside worksheet candidates", setup_error, repo)
        return
    form["target_decision"] = "domains/embedded/standards/invalid-owner-target.md"
    temp_root = pathlib.Path(tempfile.mkdtemp(prefix="kh-regression-owner-target-decision-"))
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
    target_diagnostic = next(
        (
            row for row in diagnostics
            if row.get("code") == "target-decision-not-candidate"
            and row.get("field") == "target_decision"
        ),
        {},
    )
    expect(
        result["exit_code"] == 1
        and parsed.get("form_validation", {}).get("status") == "fail"
        and any("target_decision" in error and "target candidates" in error for error in errors)
        and target_diagnostic.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and target_diagnostic.get("actual") == "domains/embedded/standards/invalid-owner-target.md"
        and target_diagnostic.get("expected") == form.get("target_candidates", [])
        and "重新填写" in target_diagnostic.get("action_zh", ""),
        "owner-form-target-decision-candidate-gate",
        "owner form rejects target decisions outside worksheet candidates",
        {
            "exit_code": result["exit_code"],
            "validation_status": parsed.get("form_validation", {}).get("status"),
            "errors": errors,
            "diagnostics": diagnostics,
            "target_candidates": form.get("target_candidates", []),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def run_owner_decision_target_pair_gate(case_id, owner_decision, target_decision, expected_fragment):
    repo = copy_repo_with_open_owner_gates(case_id)
    form, setup_error = make_valid_owner_decision_form(repo)
    if setup_error:
        expect(False, case_id, "owner form rejects incompatible owner_decision and target_decision pairs", setup_error, repo)
        return
    if owner_decision not in form.get("allowed_owner_decisions", []):
        expect(False, case_id, "owner form rejects incompatible owner_decision and target_decision pairs", {"setup_error": "owner_decision fixture not allowed", "owner_decision": owner_decision, "allowed_owner_decisions": form.get("allowed_owner_decisions", [])}, repo)
        return
    if target_decision not in form.get("target_candidates", []):
        expect(False, case_id, "owner form rejects incompatible owner_decision and target_decision pairs", {"setup_error": "target_decision fixture not a candidate", "target_decision": target_decision, "target_candidates": form.get("target_candidates", [])}, repo)
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
        and "成对兼容" in mismatch_diagnostic.get("action_zh", ""),
        case_id,
        "owner form rejects incompatible owner_decision and target_decision pairs",
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

def test_owner_form_decision_target_pair_gate():
    repo = copy_repo_with_open_owner_gates("owner-form-decision-target-pair-gate")
    form, setup_error = make_valid_owner_decision_form(repo)
    if setup_error:
        expect(False, "owner-form-decision-target-pair-gate", "owner form rejects incompatible owner_decision and target_decision pairs", setup_error, repo)
        return
    project_target = next(
        (
            target for target in form.get("target_candidates", [])
            if str(target).startswith("domains/projects/")
        ),
        "",
    )
    if not project_target:
        expect(False, "owner-form-decision-target-pair-gate", "owner form rejects incompatible owner_decision and target_decision pairs", {"setup_error": "missing project target candidate", "target_candidates": form.get("target_candidates", [])}, repo)
        return
    run_owner_decision_target_pair_gate(
        "owner-form-decision-target-pair-reference-only-project-path",
        "reference-only",
        project_target,
        "owner_decision 'reference-only' is not compatible",
    )
    run_owner_decision_target_pair_gate(
        "owner-form-decision-target-pair-no-migration-project-path",
        "no-migration",
        project_target,
        "owner_decision 'no-migration' is not compatible",
    )
    run_owner_decision_target_pair_gate(
        "owner-form-decision-target-pair-project-rule-reference-only",
        "project-local-rule",
        "reference-only",
        "owner_decision 'project-local-rule' is not compatible",
    )

def run_owner_decision_target_pair_positive(case_id, owner_decision, target_decision):
    repo = copy_repo_with_open_owner_gates(case_id)
    form, setup_error = make_valid_owner_decision_form(repo)
    if setup_error:
        expect(False, case_id, "owner form accepts compatible owner_decision and target_decision pairs", setup_error, repo)
        return
    if owner_decision not in form.get("allowed_owner_decisions", []):
        expect(False, case_id, "owner form accepts compatible owner_decision and target_decision pairs", {"setup_error": "owner_decision fixture not allowed", "owner_decision": owner_decision, "allowed_owner_decisions": form.get("allowed_owner_decisions", [])}, repo)
        return
    if target_decision not in form.get("target_candidates", []):
        expect(False, case_id, "owner form accepts compatible owner_decision and target_decision pairs", {"setup_error": "target_decision fixture not a candidate", "target_decision": target_decision, "target_candidates": form.get("target_candidates", [])}, repo)
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
        "owner form accepts compatible owner_decision and target_decision pairs",
        {
            "exit_code": result["exit_code"],
            "validation_status": parsed.get("form_validation", {}).get("status"),
            "errors": parsed.get("form_validation", {}).get("errors", []),
            "owner_decision": owner_decision,
            "target_decision": target_decision,
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_form_decision_target_pair_positive_gate():
    run_owner_decision_target_pair_positive(
        "owner-form-decision-target-pair-positive-reference-only",
        "reference-only",
        "reference-only",
    )
    run_owner_decision_target_pair_positive(
        "owner-form-decision-target-pair-positive-no-migration",
        "no-migration",
        "no-migration",
    )

def test_owner_form_routing_owner_reviewed_by_gate():
    repo = copy_repo_with_open_owner_gates("owner-form-routing-owner-reviewed-by-gate")
    form, setup_error = make_valid_owner_decision_form(repo)
    if setup_error:
        expect(False, "owner-form-routing-owner-reviewed-by-gate", "owner form rejects routing_owner as reviewed_by", setup_error, repo)
        return
    form["reviewed_by"] = "pcr02-registry-owner"
    temp_root = pathlib.Path(tempfile.mkdtemp(prefix="kh-regression-owner-routing-reviewed-by-"))
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
        and any("reviewed_by must be a real owner" in error and "routing_owner" in error for error in errors),
        "owner-form-routing-owner-reviewed-by-gate",
        "owner form rejects routing_owner as reviewed_by",
        {
            "exit_code": result["exit_code"],
            "validation_status": parsed.get("form_validation", {}).get("status"),
            "errors": errors,
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

def test_owner_form_must_not_tamper_gate():
    def mutate(form):
        form["must_not"] = list(form.get("must_not", [])) + ["fixture-invalid-extra-guardrail"]

    run_owner_form_tamper_gate(
        "owner-form-must-not-tamper-gate",
        mutate,
        "must_not differs from worksheet guardrails",
    )

def test_owner_form_allowed_decisions_tamper_gate():
    def mutate(form):
        form["allowed_owner_decisions"] = list(form.get("allowed_owner_decisions", [])) + ["fixture-invalid-decision"]

    run_owner_form_tamper_gate(
        "owner-form-allowed-decisions-tamper-gate",
        mutate,
        "allowed_owner_decisions differs from worksheet decision options",
    )

def test_owner_form_target_candidates_tamper_gate():
    def mutate(form):
        form["target_candidates"] = list(form.get("target_candidates", [])) + ["domains/projects/pcr02/current/invalid-target-candidate-fixture.md"]

    run_owner_form_tamper_gate(
        "owner-form-target-candidates-tamper-gate",
        mutate,
        "target_candidates differs from worksheet target candidates",
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

def test_owner_landing_plan_requires_owner_ready_package_missing():
    def mutate(repo):
        items_path = repo / "registry" / "items.jsonl"
        lines = items_path.read_text().splitlines()
        filtered = [
            line
            for line in lines
            if '"id":"pcr02-agents-owner-ready-package-20260620"' not in line
        ]
        if len(filtered) == len(lines):
            return {"setup_error": "missing owner-ready registry fixture line"}
        items_path.write_text("\n".join(filtered) + "\n")
        return None

    run_owner_landing_ready_block_fixture("missing", "missing", mutate)

def test_owner_landing_plan_requires_owner_ready_package_invalid():
    def mutate(repo):
        package_path = repo / "artifacts" / "manifests" / "pcr02-agents-owner-ready-package-20260620.jsonl"
        if not package_path.exists():
            return {"setup_error": "missing owner-ready package jsonl"}
        rows = [json.loads(line) for line in package_path.read_text().splitlines() if line.strip()]
        if len(rows) != 1:
            return {"setup_error": "owner-ready package jsonl should contain one row", "row_count": len(rows)}
        rows[0]["decision"] = "owner-approved-fixture"
        package_path.write_text(json.dumps(rows[0], ensure_ascii=False, separators=(",", ":")) + "\n")
        return None

    run_owner_landing_ready_block_fixture("invalid", "invalid", mutate)

def test_owner_landing_plan_requires_owner_ready_package_repo_relative_command():
    def mutate(repo):
        package_path = repo / "artifacts" / "manifests" / "pcr02-agents-owner-ready-package-20260620.md"
        if not package_path.exists():
            return {"setup_error": "missing owner-ready package markdown"}
        text = package_path.read_text()
        stable_command = "rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh"
        if stable_command not in text:
            return {"setup_error": "stable owner-ready command fixture missing"}
        package_path.write_text(text.replace(stable_command, "rtk bash tools/knowledge-owner-gates.sh", 1))
        return None

    run_owner_landing_ready_block_fixture("repo-relative-command", "invalid", mutate)

def test_owner_landing_plan_requires_owner_ready_package_duplicate():
    def mutate(repo):
        items_path = repo / "registry" / "items.jsonl"
        lines = items_path.read_text().splitlines()
        for line in lines:
            if '"id":"pcr02-agents-owner-ready-package-20260620"' in line:
                item = json.loads(line)
                item["id"] = "pcr02-agents-owner-ready-package-duplicate-fixture"
                item["title"] = "PCR02 AGENTS owner ready package duplicate fixture"
                lines.append(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
                items_path.write_text("\n".join(lines) + "\n")
                return None
        return {"setup_error": "missing owner-ready registry fixture line"}

    run_owner_landing_ready_block_fixture("duplicate", "duplicate", mutate)

def test_owner_form_source_identity_mismatch():
    repo = copy_repo_with_open_owner_gates("owner-form-source-identity-mismatch")
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
        expect(
            False,
            "owner-form-source-identity-mismatch",
            "owner form rejects stale source identity",
            {"setup_error": "missing decision form", "stdout_sample": forms_result["stdout"][:1000]},
            repo,
        )
        return
    form = forms[0]
    identity = form.get("observed_source_identity", {})
    for key, value in {
        "owner_decision": form.get("allowed_owner_decisions", ["project-local-rule"])[0],
        "target_decision": form.get("target_candidates", ["project-local-rule"])[0],
        "reviewed_by": "regression-fixture-owner",
        "reviewed_at": "2026-06-19",
        "review_after": "2026-09-19",
        "source_status": "owner-reviewed-fixture",
        "source_sha256": "0" * 64,
        "source_size": identity.get("observed_size", ""),
        "current_validity": "fixture-only",
        "scope_statement": "PCR02 project-local only",
        "applicable_project_version": "fixture-version",
        "evidence_refs": ["artifacts/manifests/pcr02-owner-resolution-playbook-20260618.md"],
        "status_reason": "Regression fixture for stale source identity rejection.",
    }.items():
        form[key] = value
    temp_root = pathlib.Path(tempfile.mkdtemp(prefix="kh-regression-owner-source-identity-"))
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
        and any("source_sha256 does not match observed source identity" in error for error in errors),
        "owner-form-source-identity-mismatch",
        "owner form rejects stale source identity",
        {
            "exit_code": result["exit_code"],
            "validation_status": parsed.get("form_validation", {}).get("status"),
            "errors": errors,
            "observed_sha256": identity.get("observed_sha256", ""),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_manual_entry_project_index_hint():
    project_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "runbook",
            "--domain",
            "projects/pcr02",
            "--project",
            "pcr02",
            "--id",
            "pcr02-regression-runbook",
            "--path",
            "domains/projects/pcr02/current/runbooks/regression.md",
        ],
    )
    governance_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "decision",
            "--domain",
            "governance",
            "--id",
            "governance-regression-decision",
            "--path",
            "governance/regression-decision.md",
        ],
    )
    expect(
        project_result["exit_code"] == 0
        and governance_result["exit_code"] == 0
        and "indexes/by-project.md" in project_result["stdout"]
        and "indexes/by-source.md" in project_result["stdout"]
        and "未知来源不要同步 by-source" in project_result["stdout"]
        and "- <source-id>:" not in project_result["stdout"]
        and "# - <真实-source-id>:" in project_result["stdout"]
        and "domains/projects/pcr02/current/runbooks/regression.md" in project_result["stdout"]
        and "indexes/by-decision.md" in governance_result["stdout"]
        and "governance-regression-decision: governance/regression-decision.md" in governance_result["stdout"]
        and "indexes/by-project.md" not in governance_result["stdout"],
        "manual-entry-project-index-hint",
        "manual entries mention project/source/decision conditional index hints",
        {
            "project_exit_code": project_result["exit_code"],
            "governance_exit_code": governance_result["exit_code"],
            "project_has_by_project": "indexes/by-project.md" in project_result["stdout"],
            "project_has_by_source": "indexes/by-source.md" in project_result["stdout"],
            "project_has_unsafe_source_placeholder": "- <source-id>:" in project_result["stdout"],
            "governance_has_by_decision": "indexes/by-decision.md" in governance_result["stdout"],
            "governance_has_by_project": "indexes/by-project.md" in governance_result["stdout"],
            "project_stdout_sample": project_result["stdout"][:1200],
            "governance_stdout_sample": governance_result["stdout"][:1200],
        },
    )

def test_manual_entry_registered_source_binding():
    bound_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "runbook",
            "--domain",
            "projects/pcr02",
            "--owner",
            "team-core",
            "--id",
            "pcr02-source-bound-runbook",
            "--path",
            "domains/projects/pcr02/current/runbooks/source-bound.md",
            "--item-source-id",
            "pcr02-project-docs",
            "--item-source-path",
            "runbooks/source-bound.md",
        ],
    )
    unknown_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "runbook",
            "--domain",
            "projects/pcr02",
            "--id",
            "pcr02-unknown-source-runbook",
            "--path",
            "domains/projects/pcr02/current/runbooks/unknown-source.md",
            "--item-source-id",
            "not-registered-source",
        ],
    )
    expect(
        bound_result["exit_code"] == 0
        and '"source":{"type":"registered","source_id":"pcr02-project-docs","source_path":"runbooks/source-bound.md","from":"manual-entry:knowledge-new.sh"}' in bound_result["stdout"]
        and "- pcr02-project-docs: `pcr02-source-bound-runbook`" in bound_result["stdout"]
        and 'knowledge-search.sh "pcr02-source-bound-runbook" --source-id pcr02-project-docs --json' in bound_result["stdout"]
        and "未知来源不要同步 by-source" not in bound_result["stdout"]
        and unknown_result["exit_code"] != 0
        and "--item-source-id is not registered" in unknown_result["stderr"],
        "manual-entry-registered-source-binding",
        "manual entry guide can bind a normal item to a registered source without forging unknown source ids",
        {
            "bound_exit_code": bound_result["exit_code"],
            "unknown_exit_code": unknown_result["exit_code"],
            "has_registered_source_json": '"source":{"type":"registered","source_id":"pcr02-project-docs","source_path":"runbooks/source-bound.md","from":"manual-entry:knowledge-new.sh"}' in bound_result["stdout"],
            "has_by_source_draft": "- pcr02-project-docs: `pcr02-source-bound-runbook`" in bound_result["stdout"],
            "has_source_search_command": 'knowledge-search.sh "pcr02-source-bound-runbook" --source-id pcr02-project-docs --json' in bound_result["stdout"],
            "unknown_stderr": unknown_result["stderr"][:500],
            "bound_stdout_sample": bound_result["stdout"][:1600],
        },
    )

def test_manual_entry_project_from_domain():
    derived_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "runbook",
            "--domain",
            "projects/pcr02",
            "--id",
            "pcr02-derived-project-runbook",
            "--path",
            "domains/projects/pcr02/current/runbooks/derived.md",
        ],
    )
    mismatch_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "runbook",
            "--domain",
            "projects/pcr02",
            "--project",
            "wrong-project",
            "--id",
            "pcr02-mismatch-runbook",
            "--path",
            "domains/projects/pcr02/current/runbooks/mismatch.md",
        ],
    )
    expect(
        derived_result["exit_code"] == 0
        and "- pcr02: domains/projects/pcr02/current/runbooks/derived.md" in derived_result["stdout"]
        and mismatch_result["exit_code"] == 0
        and "WARNING: --project `wrong-project`" in mismatch_result["stdout"],
        "manual-entry-project-derived-from-domain",
        "manual project entries derive project id from domain and warn on mismatch",
        {
            "derived_exit_code": derived_result["exit_code"],
            "mismatch_exit_code": mismatch_result["exit_code"],
            "derived_has_project": "- pcr02: domains/projects/pcr02/current/runbooks/derived.md" in derived_result["stdout"],
            "mismatch_has_warning": "WARNING: --project `wrong-project`" in mismatch_result["stdout"],
            "derived_stdout_sample": derived_result["stdout"][:1200],
            "mismatch_stdout_sample": mismatch_result["stdout"][:1200],
        },
    )

def test_manual_entry_default_dates():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "decision",
            "--domain",
            "governance",
            "--id",
            "governance-date-defaults",
            "--path",
            "governance/date-defaults.md",
        ],
    )
    current_today = today.isoformat()
    expect(
        result["exit_code"] == 0
        and f'"created_at":"{current_today}"' in result["stdout"]
        and f'"updated_at":"{current_today}"' in result["stdout"]
        and f'"checked_at":"{current_today}"' in result["stdout"]
        and '"review_after":"<YYYY-MM-DD>"' not in result["stdout"]
        and "checked_at\":\"<YYYY-MM-DD>" not in result["stdout"],
        "manual-entry-default-dates",
        "manual entry skeleton fills default ISO dates",
        {
            "exit_code": result["exit_code"],
            "today": current_today,
            "has_created_at": f'"created_at":"{current_today}"' in result["stdout"],
            "has_updated_at": f'"updated_at":"{current_today}"' in result["stdout"],
            "has_checked_at": f'"checked_at":"{current_today}"' in result["stdout"],
            "stdout_sample": result["stdout"][:1200],
        },
    )

def test_manual_entry_owner_override():
    default_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "decision",
            "--domain",
            "governance",
            "--id",
            "governance-owner-default",
            "--path",
            "governance/owner-default.md",
        ],
    )
    override_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "decision",
            "--domain",
            "governance",
            "--owner",
            "team-core",
            "--id",
            "governance-owner-override",
            "--path",
            "governance/owner-override.md",
        ],
    )
    expect(
        default_result["exit_code"] == 0
        and override_result["exit_code"] == 0
        and '"owner":"leiwenjun"' in default_result["stdout"]
        and '"owner":"team-core"' in override_result["stdout"]
        and "- owner: team-core" in override_result["stdout"],
        "manual-entry-owner-override",
        "manual entry skeleton supports owner override",
        {
            "default_exit_code": default_result["exit_code"],
            "override_exit_code": override_result["exit_code"],
            "default_has_owner": '"owner":"leiwenjun"' in default_result["stdout"],
            "override_has_owner": '"owner":"team-core"' in override_result["stdout"],
            "override_stdout_sample": override_result["stdout"][:1200],
        },
    )

def test_manual_entry_owner_registry_and_personal_defaults():
    registered_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "decision",
            "--domain",
            "governance",
            "--owner",
            "team-core",
            "--id",
            "governance-owner-registered",
            "--path",
            "governance/owner-registered.md",
        ],
    )
    unknown_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "decision",
            "--domain",
            "governance",
            "--owner",
            "unknown-item-owner",
            "--id",
            "governance-owner-warning",
            "--path",
            "governance/owner-warning.md",
        ],
    )
    personal_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "personal-note",
            "--domain",
            "personal",
            "--id",
            "personal-defaults",
            "--path",
            "domains/personal/defaults.md",
        ],
    )
    inferred_personal_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "personal-note",
            "--id",
            "personal-path-defaults",
            "--path",
            "domains/personal/path-defaults.md",
        ],
    )
    mismatch_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "runbook",
            "--domain",
            "governance",
            "--id",
            "personal-path-mismatch",
            "--path",
            "domains/personal/path-mismatch.md",
        ],
    )
    expect(
        registered_result["exit_code"] == 0
        and unknown_result["exit_code"] == 0
        and personal_result["exit_code"] == 0
        and inferred_personal_result["exit_code"] == 0
        and mismatch_result["exit_code"] == 0
        and "- owner_registry_status: registered" in registered_result["stdout"]
        and "owner_warning_zh" not in registered_result["stdout"]
        and "- owner_registry_status: unknown-owner" in unknown_result["stdout"]
        and "item owner 未在 registry/owners.json 登记" in unknown_result["stdout"]
        and '"owner":"unknown-item-owner"' in unknown_result["stdout"]
        and '"domain":"personal"' in personal_result["stdout"]
        and '"scope":"team-general"' in personal_result["stdout"]
        and '"visibility":"personal-local"' in personal_result["stdout"]
        and '"status":"personal"' in personal_result["stdout"]
        and "- personal: `personal-defaults`" in personal_result["stdout"]
        and '"domain":"personal"' in inferred_personal_result["stdout"]
        and '"visibility":"personal-local"' in inferred_personal_result["stdout"]
        and '"status":"personal"' in inferred_personal_result["stdout"]
        and "该组合会被 domain/path invariant 拦截，不可直接落盘" in mismatch_result["stdout"],
        "manual-entry-owner-registry-and-personal-defaults",
        "manual entry guide exposes item owner registry status and personal-local safe defaults",
        {
            "registered_exit_code": registered_result["exit_code"],
            "unknown_exit_code": unknown_result["exit_code"],
            "personal_exit_code": personal_result["exit_code"],
            "inferred_personal_exit_code": inferred_personal_result["exit_code"],
            "mismatch_exit_code": mismatch_result["exit_code"],
            "registered_stdout_sample": registered_result["stdout"][:1200],
            "unknown_stdout_sample": unknown_result["stdout"][:1200],
            "personal_stdout_sample": personal_result["stdout"][:1600],
            "inferred_personal_stdout_sample": inferred_personal_result["stdout"][:1600],
            "mismatch_stdout_sample": mismatch_result["stdout"][:1600],
        },
    )

def test_manual_entry_docs_owner_option():
    readme_path = root / "README.md"
    tools_readme_path = root / "tools" / "README.md"
    try:
        readme = readme_path.read_text()
        tools_readme = tools_readme_path.read_text()
        help_result = run_cmd(root, ["rtk", "bash", "tools/knowledge-new.sh", "--help"])
        read_error = ""
    except Exception as exc:
        readme = ""
        tools_readme = ""
        help_result = {"exit_code": 1, "stdout": "", "stderr": str(exc)}
        read_error = str(exc)
    readme_has_owner = "knowledge-new.sh" in readme and "--owner" in readme
    tools_readme_has_owner = "knowledge-new.sh" in tools_readme and "--owner" in tools_readme
    help_has_owner_example = (
        help_result["exit_code"] == 0
        and "--owner team-core" in help_result["stdout"]
        and "--domain projects/pcr02 --owner" in help_result["stdout"]
    )
    expect(
        not read_error and readme_has_owner and tools_readme_has_owner and help_has_owner_example,
        "manual-entry-docs-owner-option",
        "manual entry docs mention owner option",
        {
            "read_error": read_error,
            "readme_has_owner": readme_has_owner,
            "tools_readme_has_owner": tools_readme_has_owner,
            "help_exit_code": help_result["exit_code"],
            "help_has_owner_example": help_has_owner_example,
            "help_stdout_sample": help_result["stdout"][:800],
        },
    )

def test_manual_entry_offline_docs():
    readme_path = root / "README.md"
    templates_readme_path = root / "templates" / "README.md"
    try:
        readme = readme_path.read_text()
        templates_readme = templates_readme_path.read_text()
        read_error = ""
    except Exception as exc:
        readme = ""
        templates_readme = ""
        read_error = str(exc)
    expect(
        not read_error
        and "manual_validation_pending: true" in readme
        and '"type": "manual"' in readme
        and '"from": "field-debug / meeting / code-review / lab-test / owner-decision / design-review"' in readme
        and '"status": "reviewing"' in readme
        and '"review_status": "manual-entry-pending-review"' in readme
        and "registry/migrations.jsonl" in templates_readme
        and "迁移、引用或归档" in templates_readme,
        "manual-entry-offline-docs",
        "manual and offline maintenance docs state default registry values and conditional migration records",
        {
            "read_error": read_error,
            "readme_has_manual_validation_pending": "manual_validation_pending: true" in readme,
            "readme_has_manual_source_type": '"type": "manual"' in readme,
            "readme_has_reviewing_default": '"status": "reviewing"' in readme,
            "templates_has_conditional_migration": "registry/migrations.jsonl" in templates_readme and "迁移、引用或归档" in templates_readme,
        },
    )

def test_readme_offline_shortest_paths():
    readme_path = root / "README.md"
    gitignore_path = root / ".gitignore"
    try:
        readme = readme_path.read_text()
        read_error = ""
    except Exception as exc:
        readme = ""
        read_error = str(exc)
    try:
        gitignore = gitignore_path.read_text()
        gitignore_read_error = ""
    except Exception as exc:
        gitignore = ""
        gitignore_read_error = str(exc)
    required_fragments = [
        "## 人工维护 5 条最短路径",
        "### 1. 新增一条知识",
        "### 2. 新增一个 source",
        "### 3. 归档一条历史记录",
        "### 4. owner 签收一个 gate",
        "### 5. 跑一次终态检查",
        "manual_validation_pending: true",
        "required_followup",
        "rtk git diff --check",
        "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json",
        "artifacts/manifests/<source-id>-owner-decisions-YYYYMMDD.local.jsonl",
        "不登记 registry/index，不作为 landing artifact",
        "使用 subagents 时",
        "默认把子代理当并行只读审查者",
        "主线程负责唯一写入",
        "owner decision 草稿泄漏 warning",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in readme]
    gitignore_required_fragments = ["artifacts/manifests/*.local.jsonl"]
    gitignore_missing_fragments = [
        fragment
        for fragment in gitignore_required_fragments
        if fragment not in gitignore
    ]
    expect(
        not read_error and not gitignore_read_error and not missing_fragments and not gitignore_missing_fragments,
        "readme-offline-shortest-paths",
        "README keeps the five shortest manual maintenance paths and terminal-gate offline fallback",
        {
            "read_error": read_error,
            "gitignore_read_error": gitignore_read_error,
            "missing_fragments": missing_fragments,
            "gitignore_missing_fragments": gitignore_missing_fragments,
        },
    )

def test_owner_decision_draft_leak_warning():
    repo = copy_repo("owner-decision-draft-leak-warning")
    draft_path = repo / "artifacts" / "manifests" / "fixture-owner-decision-landing-29990101.jsonl"
    draft_path.write_text(
        json.dumps(
            {
                "worksheet_id": "fixture-owner-decision-worksheet-001",
                "owner_decision": "reference-only",
                "target_decision": "no-local-copy",
                "reviewed_by": "fixture-owner",
                "reviewed_at": "2999-01-01",
                "status_reason": "fixture warning only",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ) + "\n"
    )
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics", "--as-of", "2026-06-23"])
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    warnings = parsed.get("warnings", []) if isinstance(parsed.get("warnings"), list) else []
    expect(
        result["exit_code"] == 0
        and parsed.get("status") == "pass"
        and not parse_error
        and any("owner-decision-draft:artifacts/manifests/fixture-owner-decision-landing-29990101.jsonl" in warning for warning in warnings),
        "owner-decision-draft-leak-warning",
        "knowledge-check warns about non-local owner decision drafts without closing owner gates",
        {
            "exit_code": result["exit_code"],
            "status": parsed.get("status"),
            "parse_error": parse_error,
            "warnings": warnings,
            "diagnostics": parsed.get("diagnostics", {}),
        },
        repo,
    )

def test_manual_entry_offline_package_consistency():
    files = {
        "README.md": root / "README.md",
        "indexes/README.md": root / "indexes" / "README.md",
        "docs/goals/knowledge-hub-final-state.md": root / "docs" / "goals" / "knowledge-hub-final-state.md",
    }
    texts = {}
    read_errors = {}
    for rel, path in files.items():
        try:
            texts[rel] = path.read_text()
            read_errors[rel] = ""
        except Exception as exc:
            texts[rel] = ""
            read_errors[rel] = str(exc)

    diagnostics_command = "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"
    index_plan_command = "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all"
    weak_followup = "required_followup: run knowledge-check and update registry/index"
    per_file_missing = {}
    for rel, text in texts.items():
        required = [
            "manual_validation_pending: true",
            "required_followup",
            diagnostics_command,
            index_plan_command,
        ]
        per_file_missing[rel] = [fragment for fragment in required if fragment not in text]

    expect(
        not any(read_errors.values())
        and not any(per_file_missing.values())
        and weak_followup not in texts.get("docs/goals/knowledge-hub-final-state.md", ""),
        "manual-entry-offline-package-consistency",
        "offline manual maintenance package keeps complete rtk follow-up commands across README, indexes and goal docs",
        {
            "read_errors": read_errors,
            "per_file_missing": per_file_missing,
            "weak_followup_present_in_goal": weak_followup in texts.get("docs/goals/knowledge-hub-final-state.md", ""),
        },
    )

def test_manual_entry_validation_diagnostics_default():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "decision",
            "--domain",
            "governance",
            "--id",
            "governance-validation-diagnostics",
            "--path",
            "governance/validation-diagnostics.md",
        ],
    )
    diagnostics_command = "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"
    expect(
        result["exit_code"] == 0
        and f'"validation_refs":["{diagnostics_command}"]' in result["stdout"]
        and f"| `{diagnostics_command}` |" in result["stdout"],
        "manual-entry-validation-diagnostics-default",
        "manual entry drafts default validation refs and Evidence Index to diagnostics check",
        {
            "exit_code": result["exit_code"],
            "has_validation_ref": f'"validation_refs":["{diagnostics_command}"]' in result["stdout"],
            "has_evidence_index_command": f"| `{diagnostics_command}` |" in result["stdout"],
            "stdout_sample": result["stdout"][:1600],
        },
    )

def test_manual_entry_readability_fields():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "runbook",
            "--domain",
            "projects/pcr02",
            "--owner",
            "team-core",
            "--id",
            "pcr02-readable-runbook",
            "--path",
            "domains/projects/pcr02/current/runbooks/readable.md",
            "--manual-source-reason",
            "field-debug",
            "--manual-validation-pending",
            "--manual-validation-reason",
            "offline lab note awaiting rtk validation",
            "--generated-by-ai",
            "--ai-role",
            "drafted",
        ],
    )
    required_fragments = [
        '"from":"field-debug"',
        '"summary_zh":"<中文 1-3 句摘要>"',
        '"primary_language":"zh-CN"',
        '"source_language":"zh-CN"',
        '"translation_status":"not-required"',
        '"terminology_status":"pending-review"',
        '"review_status":"manual-entry-pending-review"',
        '"evidence_strength":"manual-entry-pending-validation"',
        '"evidence_refs":[]',
        '"promotion_decision":"none"',
        '"generated_by_ai":true',
        '"ai_role":"drafted"',
        '"ai_model_or_tool":"Codex"',
        '"ai_generated_at":"',
        '"human_reviewed_by":""',
        '"review_basis":""',
        "manual_validation_pending: true",
        "offline lab note awaiting rtk validation",
        "required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in result["stdout"]]
    expect(
        result["exit_code"] == 0 and not missing_fragments,
        "manual-entry-readability-fields",
        "manual entry skeleton exposes Chinese readability, evidence and AI provenance fields",
        {
            "exit_code": result["exit_code"],
            "missing_fragments": missing_fragments,
            "stdout_sample": result["stdout"][:1600],
        },
    )

def test_manual_entry_archive_default_status():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "project-archive",
            "--domain",
            "projects/pcr02",
            "--owner",
            "team-core",
            "--id",
            "pcr02-archive-status-default",
            "--path",
            "domains/projects/pcr02/archive/status-default.md",
        ],
    )
    required_fragments = [
        "- 推荐 registry status: archived",
        '"status":"archived"',
        "- archived: `pcr02-archive-status-default`",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in result["stdout"]]
    expect(
        result["exit_code"] == 0 and not missing_fragments,
        "manual-entry-archive-default-status",
        "project archive manual entry guide defaults registry and status index drafts to archived",
        {
            "exit_code": result["exit_code"],
            "missing_fragments": missing_fragments,
            "stdout_sample": result["stdout"][:1600],
        },
    )

def test_offline_validation_template_placeholders():
    template_names = [
        "item.md",
        "archive-note.md",
        "debug-record.md",
        "external-source-note.md",
        "validation-report.md",
    ]
    missing = {}
    for name in template_names:
        text = (root / "templates" / name).read_text()
        required = [
            "manual_validation_pending: true",
            "manual_validation_reason:",
            "required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
            "owner:",
            "review_after:",
        ]
        gaps = [fragment for fragment in required if fragment not in text]
        if gaps:
            missing[name] = gaps
    expect(
        not missing,
        "offline-validation-template-placeholders",
        "high-frequency templates carry optional manual_validation_pending placeholders for offline maintenance",
        {
            "missing": missing,
            "template_count": len(template_names),
        },
    )

def test_governance_audit_readability_gate():
    repo = copy_repo("governance-audit-readability-gate")
    items_path = repo / "registry" / "items.jsonl"
    rows = [json.loads(line) for line in items_path.read_text().splitlines() if line.strip()]
    target_found = False
    for row in rows:
        if row.get("id") == "knowledge-hub-owner-ready-command-stability-20260621":
            row.pop("summary_zh", None)
            target_found = True
            break
    if not target_found:
        expect(
            False,
            "governance-audit-readability-gate",
            "knowledge-check requires Chinese readability fields for new governance audits",
            {"setup_error": "governance audit fixture not found"},
            repo,
        )
        return
    items_path.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n")
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    errors = parsed.get("errors", [])
    expect(
        result["exit_code"] == 1
        and parsed.get("status") == "fail"
        and any("missing summary_zh for post-2026-06-21 governance audit readability gate" in error for error in errors),
        "governance-audit-readability-gate",
        "knowledge-check requires Chinese readability fields for new governance audits",
        {
            "exit_code": result["exit_code"],
            "status": parsed.get("status"),
            "errors": errors,
            "stdout_sample": result["stdout"][:1200],
        },
        repo,
    )

def test_ai_generated_item_provenance_gate():
    repo = copy_repo("ai-generated-item-provenance-gate")
    items_path = repo / "registry" / "items.jsonl"
    rows = [json.loads(line) for line in items_path.read_text().splitlines() if line.strip()]
    target_found = False
    for row in rows:
        if row.get("id") == "knowledge-hub-owner-ready-command-stability-20260621":
            row.pop("ai_model_or_tool", None)
            row.pop("ai_generated_at", None)
            target_found = True
            break
    if not target_found:
        expect(
            False,
            "ai-generated-item-provenance-gate",
            "knowledge-check requires AI provenance fields for new AI generated items",
            {"setup_error": "ai generated item fixture not found"},
            repo,
        )
        return
    items_path.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n")
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    errors = parsed.get("errors", [])
    expect(
        result["exit_code"] == 1
        and parsed.get("status") == "fail"
        and any("ai-generated item missing provenance fields" in error for error in errors),
        "ai-generated-item-provenance-gate",
        "knowledge-check requires AI provenance fields for new AI generated items",
        {
            "exit_code": result["exit_code"],
            "status": parsed.get("status"),
            "errors": errors,
            "stdout_sample": result["stdout"][:1200],
        },
        repo,
    )

def test_migration_notes_zh_gate():
    repo = copy_repo("migration-notes-zh-gate")
    migrations_path = repo / "registry" / "migrations.jsonl"
    rows = [json.loads(line) for line in migrations_path.read_text().splitlines() if line.strip()]
    target_found = False
    for row in rows:
        if row.get("mode") == "owner-ready-command-stability":
            row.pop("notes_zh", None)
            target_found = True
            break
    if not target_found:
        expect(
            False,
            "migration-notes-zh-gate",
            "knowledge-check requires notes_zh for new migration records",
            {"setup_error": "migration fixture not found"},
            repo,
        )
        return
    migrations_path.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n")
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    errors = parsed.get("errors", [])
    expect(
        result["exit_code"] == 1
        and parsed.get("status") == "fail"
        and any("missing notes_zh for post-2026-06-21 readability gate" in error for error in errors),
        "migration-notes-zh-gate",
        "knowledge-check requires notes_zh for new migration records",
        {
            "exit_code": result["exit_code"],
            "status": parsed.get("status"),
            "errors": errors,
            "stdout_sample": result["stdout"][:1200],
        },
        repo,
    )

def test_manual_entry_migration_conditional_guide():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--kind",
            "decision",
            "--domain",
            "governance",
            "--id",
            "governance-conditional-migration",
            "--path",
            "governance/conditional-migration.md",
        ],
    )
    expect(
        result["exit_code"] == 0
        and "普通新知识不强制新增 migration" in result["stdout"]
        and "registry/migrations.jsonl（仅迁移、引用或归档时使用）" in result["stdout"]
        and '"notes_zh":"人工新增条目已按唯一正文' in result["stdout"],
        "manual-entry-migration-conditional-guide",
        "manual entry guide treats migration record as conditional and includes notes_zh when used",
        {
            "exit_code": result["exit_code"],
            "has_conditional_step": "普通新知识不强制新增 migration" in result["stdout"],
            "has_conditional_heading": "registry/migrations.jsonl（仅迁移、引用或归档时使用）" in result["stdout"],
            "has_notes_zh": '"notes_zh":"人工新增条目已按唯一正文' in result["stdout"],
            "stdout_sample": result["stdout"][:1600],
        },
    )

def test_manual_entry_template_selection():
    cases = [
        ("runbook", "templates/runbook.md", "runbook"),
        ("decision", "templates/decision.md", "decision"),
        ("validation", "templates/validation-report.md", "validation"),
        ("validation-report", "templates/validation-report.md", "validation"),
        ("project-archive", "templates/archive-note.md", "project-archive"),
        ("archive-note", "templates/archive-note.md", "project-archive"),
        ("debug-record", "templates/debug-record.md", "debug-record"),
        ("external-source-note", "templates/external-source-note.md", "external-source-note"),
        ("external-source", "templates/external-source-note.md", "external-source-note"),
        ("owner-decision-worksheet", "templates/owner-decision-worksheet.md", "owner-decision-worksheet"),
        ("owner-worksheet", "templates/owner-decision-worksheet.md", "owner-decision-worksheet"),
        ("patent-disclosure", "templates/patent-disclosure.md", "patent-disclosure"),
        ("patent", "templates/patent-disclosure.md", "patent"),
        ("migration-record", "templates/migration-record.md", "migration-record"),
        ("migration", "templates/migration-record.md", "migration-record"),
        ("artifact-ref", "templates/artifact-ref.md", "artifact-ref"),
        ("audit", "templates/item.md", "audit"),
    ]
    failures = []
    for kind, template, registry_kind in cases:
        result = run_cmd(
            root,
            [
                "rtk",
                "bash",
                "tools/knowledge-new.sh",
                "--kind",
                kind,
                "--domain",
                "governance",
                "--id",
                f"governance-template-{kind}",
                "--path",
                f"artifacts/manifests/governance-template-{kind}.md",
            ],
        )
        if (
            result["exit_code"] != 0
            or f"推荐模板: {template}" not in result["stdout"]
            or f"- registry_kind: {registry_kind}" not in result["stdout"]
            or f'"kind":"{registry_kind}"' not in result["stdout"]
        ):
            failures.append(
                {
                    "kind": kind,
                    "expected_template": template,
                    "expected_registry_kind": registry_kind,
                    "exit_code": result["exit_code"],
                    "stdout_sample": result["stdout"][:1000],
                }
            )
    expect(
        not failures,
        "manual-entry-template-selection",
        "manual entry guide keeps stable kind-to-template and registry-kind mapping",
        {
            "failures": failures,
            "case_count": len(cases),
        },
    )

def test_templates_required_sections():
    template_paths = [
        root / "templates" / "item.md",
        root / "templates" / "runbook.md",
        root / "templates" / "decision.md",
    ]
    required_fields = [
        "summary_zh:",
        "review_status:",
        "primary_language:",
        "source_language:",
        "translation_status:",
        "terminology_status:",
        "evidence_strength:",
        "evidence_refs:",
        "promotion_decision:",
        "generated_by_ai:",
        "ai_role:",
        "human_reviewed_by:",
        "human_reviewed_at:",
        "review_basis:",
    ]
    required_sections = [
        "## 适用范围",
        "## 权威来源",
        "## 当前结论",
        "## 风险与限制",
        "## Review",
        "| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |",
    ]
    missing_by_file = {}
    for path in template_paths:
        try:
            text = path.read_text()
        except Exception as exc:
            missing_by_file[str(path.relative_to(root))] = [f"read_error: {exc}"]
            continue
        missing = [fragment for fragment in required_fields + required_sections if fragment not in text]
        if missing:
            missing_by_file[str(path.relative_to(root))] = missing
    expect(
        not missing_by_file,
        "templates-required-sections",
        "core templates carry canonical readability fields and long-term evidence sections",
        {
            "missing_by_file": missing_by_file,
            "template_count": len(template_paths),
        },
    )

def test_index_readme_maintenance_coverage():
    readme_path = root / "indexes" / "README.md"
    try:
        readme = readme_path.read_text()
        read_error = ""
    except Exception as exc:
        readme = ""
        read_error = str(exc)
    required_fragments = [
        "registry/items.jsonl",
        "registry/sources.json",
        "registry/migrations.jsonl",
        "indexes/by-owner.md",
        "indexes/by-review-date.md",
        "indexes/by-status.md",
        "indexes/by-project.md",
        "indexes/by-source.md",
        "indexes/by-topic.md",
        "indexes/by-decision.md",
        "knowledge-index-plan.sh --section all",
        "knowledge-check.sh --dry-run --json --diagnostics",
        "profile_health",
        "summary_source",
        "evidence_source",
        "manual_validation_pending: true",
        "不得覆盖人工结论",
        "自动改 active",
        "关闭 owner gate",
        "写 memory",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in readme]
    expect(
        not read_error and not missing_fragments,
        "index-readme-maintenance-coverage",
        "indexes README documents manual maintenance paths and AI safety limits",
        {
            "read_error": read_error,
            "missing_fragments": missing_fragments,
            "has_source_registry": "registry/sources.json" in readme,
            "has_core_indexes": all(fragment in readme for fragment in ["indexes/by-owner.md", "indexes/by-review-date.md", "indexes/by-status.md"]),
            "has_extended_indexes": all(fragment in readme for fragment in ["indexes/by-project.md", "indexes/by-source.md", "indexes/by-topic.md", "indexes/by-decision.md"]),
            "has_ai_limits": all(fragment in readme for fragment in ["不得覆盖人工结论", "自动改 active", "关闭 owner gate", "写 memory"]),
        },
    )

def test_by_topic_first_screen_readability_contract():
    by_topic_path = root / "indexes" / "by-topic.md"
    try:
        by_topic = by_topic_path.read_text()
        read_error = ""
    except Exception as exc:
        by_topic = ""
        read_error = str(exc)
    required_first_screen_topics = [
        "migration",
        "owner gate",
        "PCR02",
        "tools",
        "knowledge",
        "product-test",
        "scratch",
        "diag",
        "ASAN",
        "memory auto-curation",
        "DVR",
        "motor MCU",
        "governance",
        "automation",
        "regression",
        "patent",
        "Codex archive",
    ]
    first_screen_marker = "## 优先恢复主题速查"
    domain_marker = "## 领域入口"
    history_marker = "## 历史治理台账"
    first_screen_index = by_topic.find(first_screen_marker)
    domain_index = by_topic.find(domain_marker)
    history_index = by_topic.find(history_marker)
    first_screen_text = by_topic[first_screen_index:history_index] if first_screen_index >= 0 and history_index >= 0 else ""
    missing_topics = [topic for topic in required_first_screen_topics if topic not in first_screen_text]
    unexpected_history_before_ledger = [
        path for path in re.findall(r"artifacts/manifests/knowledge-hub-[^`]+", first_screen_text)
        if "knowledge-hub-source-coverage-closeout" not in path
        and "knowledge-hub-governance-regression-helper" not in path
    ]
    missing_manifest_paths = []
    for match in re.finditer(r"`([^`]+\.md)`", by_topic):
        candidate = match.group(1)
        if candidate.startswith("artifacts/manifests/") and not (root / candidate).exists():
            missing_manifest_paths.append(candidate)
    expect(
        not read_error
        and first_screen_index >= 0
        and domain_index > first_screen_index
        and history_index > domain_index
        and not missing_topics
        and not unexpected_history_before_ledger
        and not missing_manifest_paths,
        "by-topic-first-screen-readability-contract",
        "by-topic keeps recovery topics before historical governance ledger",
        {
            "read_error": read_error,
            "first_screen_index": first_screen_index,
            "domain_index": domain_index,
            "history_index": history_index,
            "missing_topics": missing_topics,
            "unexpected_history_before_ledger": unexpected_history_before_ledger,
            "missing_manifest_paths": sorted(set(missing_manifest_paths)),
        },
    )

def test_review_queue_json_contract():
    status_result = run_cmd(
        root,
        ["rtk", "bash", "tools/knowledge-status.sh", "--json", "--as-of", today.isoformat()],
    )
    index_result = run_cmd(
        root,
        ["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", "review-queue", "--json"],
    )
    parse_errors = []
    try:
        status_payload = json.loads(status_result["stdout"])
    except Exception as exc:
        status_payload = {}
        parse_errors.append(f"status: {exc}")
    try:
        index_payload = json.loads(index_result["stdout"])
    except Exception as exc:
        index_payload = {}
        parse_errors.append(f"index-plan: {exc}")
    review_queues = status_payload.get("review_queues", {}) if isinstance(status_payload.get("review_queues", {}), dict) else {}
    status_summary = review_queues.get("summary", {}) if isinstance(review_queues.get("summary", {}), dict) else {}
    by_review_queue = (
        index_payload.get("indexes", {}).get("by_review_queue", {})
        if isinstance(index_payload.get("indexes", {}), dict)
        else {}
    )
    index_summary = by_review_queue.get("summary", {}) if isinstance(by_review_queue.get("summary", {}), dict) else {}
    rows = by_review_queue.get("rows", []) if isinstance(by_review_queue.get("rows", []), list) else []
    first_row = rows[0] if rows else {}
    filtered_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-index-plan.sh",
            "--section",
            "review-queue",
            "--json",
            "--queue-type",
            str(first_row.get("queue_type", "ai-human-review")),
            "--queue-owner",
            str(first_row.get("owner", "leiwenjun")),
            "--queue-review-after",
            str(first_row.get("review_after", "2026-09-17")),
            "--queue-limit",
            "3",
        ],
    )
    try:
        filtered_payload = json.loads(filtered_result["stdout"])
    except Exception as exc:
        filtered_payload = {}
        parse_errors.append(f"filtered-index-plan: {exc}")
    filtered_queue = (
        filtered_payload.get("indexes", {}).get("by_review_queue", {})
        if isinstance(filtered_payload.get("indexes", {}), dict)
        else {}
    )
    filtered_summary = filtered_queue.get("summary", {}) if isinstance(filtered_queue.get("summary", {}), dict) else {}
    filtered_pagination = filtered_queue.get("pagination", {}) if isinstance(filtered_queue.get("pagination", {}), dict) else {}
    filtered_batch_packet = filtered_queue.get("review_batch_packet", {}) if isinstance(filtered_queue.get("review_batch_packet", {}), dict) else {}
    filtered_rows = filtered_queue.get("rows", []) if isinstance(filtered_queue.get("rows", []), list) else []
    forms_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-index-plan.sh",
            "--section",
            "review-queue",
            "--queue-forms-jsonl",
            "--queue-type",
            str(first_row.get("queue_type", "ai-human-review")),
            "--queue-owner",
            str(first_row.get("owner", "leiwenjun")),
            "--queue-review-after",
            str(first_row.get("review_after", "2026-09-17")),
            "--queue-limit",
            "3",
        ],
    )
    forms_conflict_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-index-plan.sh",
            "--section",
            "review-queue",
            "--queue-forms-jsonl",
            "--json",
        ],
    )
    form_parse_errors = []
    forms = []
    for line in forms_result["stdout"].splitlines():
        if not line.strip():
            continue
        try:
            forms.append(json.loads(line))
        except Exception as exc:
            form_parse_errors.append(str(exc))
    first_form = forms[0] if forms else {}
    first_form_text = forms_result["stdout"]
    temp_form_paths = []

    def write_review_queue_forms_jsonl(form_rows):
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".jsonl", delete=False)
        temp_form_paths.append(pathlib.Path(handle.name))
        with handle:
            for form_row in form_rows:
                handle.write(json.dumps(form_row, ensure_ascii=False, separators=(",", ":")) + "\n")
        return handle.name

    filled_form = dict(first_form)
    filled_form.update({
        "human_reviewed_by": "regression-fixture-human",
        "human_reviewed_at": today.isoformat(),
        "review_basis": "Regression fixture for review queue validation.",
        "review_decision": "accept-as-review-record",
    })
    duplicate_form = dict(filled_form)
    unknown_form = dict(filled_form)
    unknown_form["queue_id"] = "item:unknown-review-queue-form:ai-human-review"
    invalid_decision_form = dict(filled_form)
    invalid_decision_form["review_decision"] = "owner-approved"
    missing_human_field_form = dict(filled_form)
    missing_human_field_form["review_basis"] = ""
    forbidden_owner_field_form = dict(filled_form)
    forbidden_owner_field_form["owner_decision"] = "approved"
    identity_mismatch_form = dict(filled_form)
    identity_mismatch_form["id"] = "tampered-review-queue-id"
    guardrail_mismatch_form = dict(filled_form)
    guardrail_mismatch_form["read_only"] = False
    valid_forms_path = write_review_queue_forms_jsonl([filled_form])
    duplicate_forms_path = write_review_queue_forms_jsonl([filled_form, duplicate_form])
    unknown_forms_path = write_review_queue_forms_jsonl([unknown_form])
    invalid_decision_forms_path = write_review_queue_forms_jsonl([invalid_decision_form])
    missing_human_field_forms_path = write_review_queue_forms_jsonl([missing_human_field_form])
    forbidden_owner_field_forms_path = write_review_queue_forms_jsonl([forbidden_owner_field_form])
    identity_mismatch_forms_path = write_review_queue_forms_jsonl([identity_mismatch_form])
    guardrail_mismatch_forms_path = write_review_queue_forms_jsonl([guardrail_mismatch_form])
    validate_base_command = [
        "rtk",
        "bash",
        "tools/knowledge-index-plan.sh",
        "--section",
        "review-queue",
        "--json",
        "--queue-type",
        str(first_row.get("queue_type", "ai-human-review")),
        "--queue-owner",
        str(first_row.get("owner", "leiwenjun")),
        "--queue-review-after",
        str(first_row.get("review_after", "2026-09-17")),
        "--queue-limit",
        "3",
        "--validate-queue-forms",
    ]
    validate_result = run_cmd(root, validate_base_command + [valid_forms_path])
    duplicate_validate_result = run_cmd(root, validate_base_command + [duplicate_forms_path])
    unknown_validate_result = run_cmd(root, validate_base_command + [unknown_forms_path])
    invalid_decision_validate_result = run_cmd(root, validate_base_command + [invalid_decision_forms_path])
    missing_human_field_validate_result = run_cmd(root, validate_base_command + [missing_human_field_forms_path])
    forbidden_owner_field_validate_result = run_cmd(root, validate_base_command + [forbidden_owner_field_forms_path])
    identity_mismatch_validate_result = run_cmd(root, validate_base_command + [identity_mismatch_forms_path])
    guardrail_mismatch_validate_result = run_cmd(root, validate_base_command + [guardrail_mismatch_forms_path])
    validate_without_json_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-index-plan.sh",
            "--section",
            "review-queue",
            "--validate-queue-forms",
            valid_forms_path,
        ],
    )
    validate_wrong_section_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-index-plan.sh",
            "--section",
            "owner",
            "--json",
            "--validate-queue-forms",
            valid_forms_path,
        ],
    )
    validate_forms_conflict_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-index-plan.sh",
            "--section",
            "review-queue",
            "--queue-forms-jsonl",
            "--validate-queue-forms",
            valid_forms_path,
        ],
    )
    validate_parse_errors = []
    try:
        validate_payload = json.loads(validate_result["stdout"])
    except Exception as exc:
        validate_payload = {}
        validate_parse_errors.append(f"valid-forms: {exc}")
    try:
        duplicate_validate_payload = json.loads(duplicate_validate_result["stdout"])
    except Exception as exc:
        duplicate_validate_payload = {}
        validate_parse_errors.append(f"duplicate-forms: {exc}")
    try:
        unknown_validate_payload = json.loads(unknown_validate_result["stdout"])
    except Exception as exc:
        unknown_validate_payload = {}
        validate_parse_errors.append(f"unknown-forms: {exc}")
    try:
        invalid_decision_validate_payload = json.loads(invalid_decision_validate_result["stdout"])
    except Exception as exc:
        invalid_decision_validate_payload = {}
        validate_parse_errors.append(f"invalid-decision-forms: {exc}")
    try:
        missing_human_field_validate_payload = json.loads(missing_human_field_validate_result["stdout"])
    except Exception as exc:
        missing_human_field_validate_payload = {}
        validate_parse_errors.append(f"missing-human-field-forms: {exc}")
    try:
        forbidden_owner_field_validate_payload = json.loads(forbidden_owner_field_validate_result["stdout"])
    except Exception as exc:
        forbidden_owner_field_validate_payload = {}
        validate_parse_errors.append(f"forbidden-owner-field-forms: {exc}")
    try:
        identity_mismatch_validate_payload = json.loads(identity_mismatch_validate_result["stdout"])
    except Exception as exc:
        identity_mismatch_validate_payload = {}
        validate_parse_errors.append(f"identity-mismatch-forms: {exc}")
    try:
        guardrail_mismatch_validate_payload = json.loads(guardrail_mismatch_validate_result["stdout"])
    except Exception as exc:
        guardrail_mismatch_validate_payload = {}
        validate_parse_errors.append(f"guardrail-mismatch-forms: {exc}")
    for temp_form_path in temp_form_paths:
        try:
            temp_form_path.unlink()
        except FileNotFoundError:
            pass
    form_validation = validate_payload.get("form_validation", {}) if isinstance(validate_payload.get("form_validation", {}), dict) else {}
    duplicate_diagnostic_codes = [
        row.get("code")
        for row in duplicate_validate_payload.get("form_validation", {}).get("diagnostics", [])
        if isinstance(row, dict)
    ]
    unknown_diagnostic_codes = [
        row.get("code")
        for row in unknown_validate_payload.get("form_validation", {}).get("diagnostics", [])
        if isinstance(row, dict)
    ]
    invalid_decision_diagnostic_codes = [
        row.get("code")
        for row in invalid_decision_validate_payload.get("form_validation", {}).get("diagnostics", [])
        if isinstance(row, dict)
    ]
    missing_human_field_diagnostic_codes = [
        row.get("code")
        for row in missing_human_field_validate_payload.get("form_validation", {}).get("diagnostics", [])
        if isinstance(row, dict)
    ]
    forbidden_owner_field_diagnostic_codes = [
        row.get("code")
        for row in forbidden_owner_field_validate_payload.get("form_validation", {}).get("diagnostics", [])
        if isinstance(row, dict)
    ]
    identity_mismatch_diagnostic_codes = [
        row.get("code")
        for row in identity_mismatch_validate_payload.get("form_validation", {}).get("diagnostics", [])
        if isinstance(row, dict)
    ]
    guardrail_mismatch_diagnostic_codes = [
        row.get("code")
        for row in guardrail_mismatch_validate_payload.get("form_validation", {}).get("diagnostics", [])
        if isinstance(row, dict)
    ]
    required_first_row_fields = [
        "queue_id",
        "queue_type",
        "object_type",
        "id",
        "owner",
        "status",
        "review_after",
        "priority",
        "missing_fields",
        "evidence_refs",
        "ai_role",
        "ai_model_or_tool",
        "ai_generated_at",
        "promotion_decision",
        "next_commands",
        "must_not",
        "read_only",
        "report_only",
        "owner_gate_mutation",
        "memory_write",
        "source_project_write",
    ]
    missing_first_row_fields = [field for field in required_first_row_fields if field not in first_row]
    expect(
        status_result["exit_code"] == 0
        and index_result["exit_code"] == 0
        and not parse_errors
        and review_queues.get("read_only") is True
        and review_queues.get("report_only") is True
        and status_summary.get("total_pending_count", 0) == index_summary.get("row_count", -1)
        and status_summary.get("ai_generated_pending_count", 0) == index_summary.get("ai_generated_pending_count", -1)
        and status_summary.get("external_source_pending_count", 0) == index_summary.get("external_source_pending_count", -1)
        and index_summary.get("active_or_promotion_blocker_count", -1) == status_summary.get("active_or_promotion_blocker_count", -2)
        and index_summary.get("active_or_promotion_blocker_count", 1) == 0
        and rows
        and not missing_first_row_fields
        and first_row.get("read_only") is True
        and first_row.get("report_only") is True
        and first_row.get("owner_gate_mutation") is False
        and first_row.get("memory_write") is False
        and first_row.get("source_project_write") is False
        and "ai-human-review" in by_review_queue.get("by_type", {})
        and "不写 memory" in " ".join(by_review_queue.get("must_not", []))
        and first_row.get("next_commands")
        and first_row.get("id", "") in first_row.get("next_commands", [""])[0]
        and "--explain" in first_row.get("next_commands", [""])[0]
        and "不自动提升 active" in " ".join(first_row.get("must_not", []))
        and filtered_result["exit_code"] == 0
        and filtered_summary.get("matched_count", 0) >= len(filtered_rows)
        and filtered_summary.get("shown_count") == len(filtered_rows)
        and len(filtered_rows) <= 3
        and filtered_pagination.get("limit") == 3
        and all(row.get("queue_type") == first_row.get("queue_type") for row in filtered_rows)
        and all(row.get("owner") == first_row.get("owner") for row in filtered_rows)
        and all(row.get("review_after") == first_row.get("review_after") for row in filtered_rows)
        and filtered_summary.get("read_only") is True
        and filtered_summary.get("report_only") is True
        and filtered_summary.get("memory_write") is False
        and filtered_batch_packet.get("packet_type") == "review-queue-batch"
        and filtered_batch_packet.get("read_only") is True
        and filtered_batch_packet.get("report_only") is True
        and filtered_batch_packet.get("shown_count") == len(filtered_rows)
        and filtered_batch_packet.get("row_ids") == [row.get("queue_id") for row in filtered_rows]
        and "human_reviewed_by" in filtered_batch_packet.get("required_human_fields", [])
        and len(filtered_batch_packet.get("next_commands", [])) == len(filtered_rows)
        and all("--explain" in command for command in filtered_batch_packet.get("next_commands", []))
        and "不把 review queue 当 owner gate 签收结果" in " ".join(filtered_batch_packet.get("must_not", []))
        and "knowledge-index-plan.sh --section review-queue" in filtered_batch_packet.get("recommended_batch_json", "")
        and "--json" in filtered_batch_packet.get("recommended_batch_json", "")
        and "--queue-forms-jsonl" in filtered_batch_packet.get("recommended_forms_jsonl", "")
        and "--validate-queue-forms" in filtered_batch_packet.get("validate_queue_forms_command_template", "")
        and "review-queue-forms.jsonl" in filtered_batch_packet.get("validate_queue_forms_command_template", "")
        and filtered_batch_packet.get("forms_jsonl_command", "").endswith("--queue-limit 3 --queue-offset 0")
        and "--queue-forms-jsonl" in filtered_batch_packet.get("forms_jsonl_command", "")
        and forms_result["exit_code"] == 0
        and not form_parse_errors
        and len(forms) == len(filtered_rows)
        and len(forms) <= 3
        and "# Knowledge Index Plan" not in first_form_text
        and "## 验证" not in first_form_text
        and first_form.get("form_type") == "review-queue-human-review"
        and first_form.get("status") == "human-fill-required"
        and first_form.get("read_only") is True
        and first_form.get("report_only") is True
        and first_form.get("owner_gate_mutation") is False
        and first_form.get("memory_write") is False
        and first_form.get("source_project_write") is False
        and first_form.get("human_reviewed_by") == ""
        and first_form.get("human_reviewed_at") == ""
        and first_form.get("review_basis") == ""
        and "owner" not in first_form
        and "owner_decision" not in first_form
        and "reviewed_by" not in first_form
        and "human_reviewed_by" in first_form.get("required_human_fields", [])
        and "不写 registry" in " ".join(first_form.get("must_not", []))
        and first_form.get("read_only_context", {}).get("registry_owner") == first_row.get("owner")
        and forms_conflict_result["exit_code"] != 0
        and "--queue-forms-jsonl cannot be combined with --json" in forms_conflict_result["stderr"]
        and validate_result["exit_code"] == 0
        and not validate_parse_errors
        and form_validation.get("status") == "pass"
        and form_validation.get("read_only") is True
        and form_validation.get("report_only") is True
        and form_validation.get("no_registry_write") is True
        and form_validation.get("no_owner_decision_generated") is True
        and form_validation.get("owner_gate_mutation") is False
        and form_validation.get("accepted_count") == 1
        and form_validation.get("coverage_status") == "partial"
        and "review_decision" in form_validation.get("required_submission_fields", [])
        and duplicate_validate_result["exit_code"] != 0
        and "duplicate-queue-id" in duplicate_diagnostic_codes
        and unknown_validate_result["exit_code"] != 0
        and "unknown-queue-id" in unknown_diagnostic_codes
        and invalid_decision_validate_result["exit_code"] != 0
        and "invalid-review-decision" in invalid_decision_diagnostic_codes
        and missing_human_field_validate_result["exit_code"] != 0
        and "missing-required-human-field" in missing_human_field_diagnostic_codes
        and forbidden_owner_field_validate_result["exit_code"] != 0
        and "forbidden-owner-field" in forbidden_owner_field_diagnostic_codes
        and identity_mismatch_validate_result["exit_code"] != 0
        and "field-mismatch" in identity_mismatch_diagnostic_codes
        and guardrail_mismatch_validate_result["exit_code"] != 0
        and "guardrail-field-mismatch" in guardrail_mismatch_diagnostic_codes
        and validate_without_json_result["exit_code"] != 0
        and "--validate-queue-forms requires --json" in validate_without_json_result["stderr"]
        and validate_wrong_section_result["exit_code"] != 0
        and "--validate-queue-forms requires --section review-queue" in validate_wrong_section_result["stderr"]
        and validate_forms_conflict_result["exit_code"] != 0
        and "--validate-queue-forms cannot be combined with --queue-forms-jsonl" in validate_forms_conflict_result["stderr"],
        "review-queue-json-contract",
        "status and index-plan expose report-only human review queue from registry",
        {
            "status_exit_code": status_result["exit_code"],
            "index_exit_code": index_result["exit_code"],
            "parse_errors": parse_errors,
            "status_total_pending_count": status_summary.get("total_pending_count"),
            "index_row_count": index_summary.get("row_count"),
            "status_ai_generated_pending_count": status_summary.get("ai_generated_pending_count"),
            "index_ai_generated_pending_count": index_summary.get("ai_generated_pending_count"),
            "active_or_promotion_blocker_count": index_summary.get("active_or_promotion_blocker_count"),
            "missing_first_row_fields": missing_first_row_fields,
            "filtered_exit_code": filtered_result["exit_code"],
            "filtered_summary": filtered_summary,
            "filtered_row_count": len(filtered_rows),
            "filtered_pagination": filtered_pagination,
            "filtered_batch_packet": filtered_batch_packet,
            "forms_exit_code": forms_result["exit_code"],
            "forms_line_count": len(forms),
            "form_parse_errors": form_parse_errors,
            "first_form": first_form,
            "forms_conflict_exit_code": forms_conflict_result["exit_code"],
            "forms_conflict_stderr": forms_conflict_result["stderr"][:500],
            "validate_exit_code": validate_result["exit_code"],
            "validate_parse_errors": validate_parse_errors,
            "form_validation": form_validation,
            "duplicate_validate_exit_code": duplicate_validate_result["exit_code"],
            "duplicate_diagnostic_codes": duplicate_diagnostic_codes,
            "unknown_validate_exit_code": unknown_validate_result["exit_code"],
            "unknown_diagnostic_codes": unknown_diagnostic_codes,
            "invalid_decision_validate_exit_code": invalid_decision_validate_result["exit_code"],
            "invalid_decision_diagnostic_codes": invalid_decision_diagnostic_codes,
            "missing_human_field_validate_exit_code": missing_human_field_validate_result["exit_code"],
            "missing_human_field_diagnostic_codes": missing_human_field_diagnostic_codes,
            "forbidden_owner_field_validate_exit_code": forbidden_owner_field_validate_result["exit_code"],
            "forbidden_owner_field_diagnostic_codes": forbidden_owner_field_diagnostic_codes,
            "identity_mismatch_validate_exit_code": identity_mismatch_validate_result["exit_code"],
            "identity_mismatch_diagnostic_codes": identity_mismatch_diagnostic_codes,
            "guardrail_mismatch_validate_exit_code": guardrail_mismatch_validate_result["exit_code"],
            "guardrail_mismatch_diagnostic_codes": guardrail_mismatch_diagnostic_codes,
            "validate_without_json_exit_code": validate_without_json_result["exit_code"],
            "validate_without_json_stderr": validate_without_json_result["stderr"][:500],
            "validate_wrong_section_exit_code": validate_wrong_section_result["exit_code"],
            "validate_wrong_section_stderr": validate_wrong_section_result["stderr"][:500],
            "validate_forms_conflict_exit_code": validate_forms_conflict_result["exit_code"],
            "validate_forms_conflict_stderr": validate_forms_conflict_result["stderr"][:500],
        },
    )

def test_final_proof_artifact_discoverability():
    selector_date = today.isoformat()
    selector_suffix = selector_date.replace("-", "")
    seed_ids = [
        "knowledge-hub-owner-handoff-final-gate-hardening-20260622",
        "knowledge-hub-final-gate-evidence-recovery-20260622",
        "knowledge-hub-recovery-search-manual-hardening-20260622",
        "knowledge-hub-final-proof-maintenance-hardening-20260622",
        "knowledge-hub-owner-queue-command-hardening-20260622",
        "knowledge-hub-final-recovery-discoverability-hardening-20260622",
        "knowledge-hub-final-proof-summary-readability-hardening-20260622",
        "knowledge-hub-source-check-snapshot-evidence-readability-20260622",
        "knowledge-hub-report-only-maintenance-tools-20260622",
        "knowledge-hub-owner-inbox-final-gate-audit-20260622",
    ]
    errors = []
    items_by_id = {}
    try:
        for line in (root / "registry" / "items.jsonl").read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            items_by_id[str(row.get("id", ""))] = row
    except Exception as exc:
        errors.append(f"registry/items.jsonl read/parse failed: {exc}")
    migration_text = ""
    try:
        migration_text = (root / "registry" / "migrations.jsonl").read_text()
    except Exception as exc:
        errors.append(f"registry/migrations.jsonl read failed: {exc}")
    index_texts = {}
    for relative in [
        "indexes/by-owner.md",
        "indexes/by-status.md",
        "indexes/by-review-date.md",
        "indexes/by-topic.md",
        "indexes/by-decision.md",
    ]:
        try:
            index_texts[relative] = (root / relative).read_text()
        except Exception as exc:
            index_texts[relative] = ""
            errors.append(f"{relative} read failed: {exc}")
    missing_registry = []
    missing_md = []
    missing_jsonl = []
    missing_migration_md = []
    missing_migration_jsonl = []
    missing_indexes = {}
    missing_documented_by_paths = []
    missing_topic_paths = []
    dynamic_ids = []
    for item_id, row in items_by_id.items():
        tags = row.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        path_text = str(row.get("path", ""))
        review_status = str(row.get("review_status", ""))
        if (
            row.get("domain") == "governance"
            and row.get("kind") == "audit"
            and (row.get("created_at") == selector_date or row.get("updated_at") == selector_date)
            and "governance" in tags
            and path_text.startswith("artifacts/manifests/knowledge-hub-")
            and path_text.endswith(f"-{selector_suffix}.md")
            and (review_status.endswith("-applied") or review_status.endswith("-registered"))
        ):
            dynamic_ids.append(item_id)
    required_ids = []
    for item_id in seed_ids + dynamic_ids:
        if item_id not in required_ids:
            required_ids.append(item_id)
    for item_id in required_ids:
        row = items_by_id.get(item_id)
        if not row:
            missing_registry.append(item_id)
            continue
        path_text = str(row.get("path", ""))
        md_path = root / path_text
        jsonl_path = md_path.with_suffix(".jsonl")
        if not path_text or not md_path.is_file():
            missing_md.append({"id": item_id, "path": path_text})
        if not jsonl_path.is_file():
            missing_jsonl.append({"id": item_id, "path": str(jsonl_path.relative_to(root))})
        md_relative = str(md_path.relative_to(root)) if path_text else ""
        jsonl_relative = str(jsonl_path.relative_to(root)) if path_text else ""
        if md_relative and md_relative not in migration_text:
            missing_migration_md.append({"id": item_id, "path": md_relative})
        if jsonl_relative and jsonl_relative not in migration_text:
            missing_migration_jsonl.append({"id": item_id, "path": jsonl_relative})
        per_index_missing = []
        for relative, text in index_texts.items():
            if item_id in text or (md_relative and md_relative in text) or (jsonl_relative and jsonl_relative in text):
                continue
            per_index_missing.append(relative)
        if per_index_missing:
            missing_indexes[item_id] = per_index_missing
    by_status = index_texts.get("indexes/by-status.md", "")
    for match in re.finditer(r"documented by `([^`]+)`", by_status):
        candidate = match.group(1)
        if not (root / candidate).exists():
            missing_documented_by_paths.append(candidate)
    by_topic = index_texts.get("indexes/by-topic.md", "")
    for match in re.finditer(r"`([^`]+\.md)`", by_topic):
        candidate = match.group(1)
        if candidate.startswith("artifacts/manifests/") and not (root / candidate).exists():
            missing_topic_paths.append(candidate)
    expect(
        not errors
        and (selector_date != "2026-06-22" or len(dynamic_ids) >= 17)
        and (selector_date != "2026-06-22" or len(required_ids) == len(dynamic_ids))
        and set(seed_ids) <= set(required_ids)
        and (selector_date != "2026-06-22" or "knowledge-hub-review-after-topic-owner-hardening-20260622" in required_ids)
        and not missing_registry
        and not missing_md
        and not missing_jsonl
        and not missing_migration_md
        and not missing_migration_jsonl
        and not missing_indexes
        and not missing_documented_by_paths
        and not missing_topic_paths,
        "final-proof-artifact-discoverability",
        "final proof artifacts are discoverable from registry, migration and core indexes",
        {
            "required_ids": required_ids,
            "seed_ids": seed_ids,
            "selector_date": selector_date,
            "dynamic_ids": dynamic_ids,
            "required_count": len(required_ids),
            "dynamic_count": len(dynamic_ids),
            "errors": errors,
            "missing_registry": missing_registry,
            "missing_md": missing_md,
            "missing_jsonl": missing_jsonl,
            "missing_migration_md": missing_migration_md,
            "missing_migration_jsonl": missing_migration_jsonl,
            "missing_indexes": missing_indexes,
            "missing_documented_by_paths": sorted(set(missing_documented_by_paths)),
            "missing_topic_paths": sorted(set(missing_topic_paths)),
        },
    )

def test_final_proof_decision_index_recovery_contract():
    final_gate_text = ""
    decision_index_text = ""
    errors = []
    try:
        final_gate_text = (root / "tools" / "knowledge-final-gate.sh").read_text()
    except Exception as exc:
        errors.append(f"tools/knowledge-final-gate.sh read failed: {exc}")
    try:
        decision_index_text = (root / "indexes" / "by-decision.md").read_text()
    except Exception as exc:
        errors.append(f"indexes/by-decision.md read failed: {exc}")
    required_ids = [
        "knowledge-hub-final-proof-date-rollover-hardening-20260623",
        "knowledge-hub-owner-inbox-linking-maintenance-hardening-20260623",
        "knowledge-hub-manual-entry-owner-personal-source-recommendation-20260623",
        "knowledge-hub-proof-alias-owner-coverage-hardening-20260623",
        "knowledge-hub-owner-ready-status-source-hardening-20260623",
        "knowledge-hub-owner-archive-form-readability-hardening-20260623",
        "knowledge-hub-final-state-handoff-supersede-20260623",
    ]
    missing_tool_fragments = [
        fragment for fragment in [
            "FINAL_PROOF_INDEX_PATHS",
            '"indexes/by-decision.md"',
        ]
        if fragment not in final_gate_text
    ]
    missing_decision_ids = [
        item_id for item_id in required_ids
        if item_id not in decision_index_text
    ]
    missing_guardrail_fragments = [
        fragment for fragment in [
            "不生成 owner decision",
            "不关闭 owner gate",
            "不写 memory",
        ]
        if fragment not in decision_index_text
    ]
    expect(
        not errors
        and not missing_tool_fragments
        and not missing_decision_ids
        and not missing_guardrail_fragments,
        "final-proof-decision-index-recovery-contract",
        "final proof discoverability includes by-decision recovery anchors",
        {
            "errors": errors,
            "missing_tool_fragments": missing_tool_fragments,
            "missing_decision_ids": missing_decision_ids,
            "missing_guardrail_fragments": missing_guardrail_fragments,
            "required_ids": required_ids,
        },
    )

def test_final_proof_artifact_as_of_date_selector():
    repo = copy_repo("final-proof-artifact-as-of-date-selector")
    artifact_id = "knowledge-hub-proof-date-selector-fixture-20260623"
    md_rel = "artifacts/manifests/knowledge-hub-proof-date-selector-fixture-20260623.md"
    jsonl_rel = "artifacts/manifests/knowledge-hub-proof-date-selector-fixture-20260623.jsonl"
    md_path = repo / md_rel
    jsonl_path = repo / jsonl_rel
    md_path.write_text(
        "# Knowledge Hub proof 日期选择器 fixture 2026-06-23\n\n"
        "## 结论\n\n"
        "该临时 fixture 只用于回归测试：证明 final gate 按 `--as-of 2026-06-23` 选择当天治理 proof，"
        "同时保留 2026-06-22 seed 基线。\n\n"
        "## 边界\n\n"
        "- 不生成 owner decision。\n"
        "- 不关闭 owner gate。\n"
        "- 不修改源项目。\n"
        "- 不写 memory。\n"
    )
    item_rows = []
    for line in (repo / "registry" / "items.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        item_rows.append(json.loads(line))
    base_item = next(
        (row for row in item_rows if row.get("id") == "knowledge-hub-owner-status-review-proof-hardening-20260622"),
        {},
    )
    fixture_item = dict(base_item)
    fixture_item.update({
        "id": artifact_id,
        "title": "Knowledge Hub proof 日期选择器 fixture 2026-06-23",
        "path": md_rel,
        "source": {"type": "generated", "from": "temporary regression fixture for final proof as-of date selector"},
        "validation_refs": [jsonl_rel, "rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23"],
        "tags": ["knowledge-hub", "final-gate", "proof-discoverability", "regression", "governance"],
        "review_after": "2026-09-23",
        "summary_zh": "临时回归 fixture，用于证明 final gate 按 --as-of 日期发现新治理 proof，同时保留 2026-06-22 seed 基线。",
        "review_status": "proof-date-selector-applied",
        "evidence_strength": "temporary-regression-fixture-for-dynamic-as-of-date-proof-selector",
        "evidence_refs": ["tools/knowledge-final-gate.sh --json --as-of 2026-06-23"],
        "created_at": "2026-06-23",
        "updated_at": "2026-06-23",
    })
    with (repo / "registry" / "items.jsonl").open("a") as fh:
        fh.write(json.dumps(fixture_item, ensure_ascii=False, separators=(",", ":")) + "\n")
    manifest_row = {
        key: fixture_item.get(key)
        for key in [
            "id",
            "title",
            "kind",
            "domain",
            "path",
            "status",
            "owner",
            "summary_zh",
            "primary_language",
            "source_language",
            "translation_status",
            "terminology_status",
            "review_status",
            "evidence_strength",
            "evidence_refs",
            "generated_by_ai",
            "ai_role",
            "ai_model_or_tool",
            "ai_generated_at",
            "human_reviewed_by",
            "promotion_decision",
            "created_at",
            "updated_at",
        ]
    }
    manifest_row["must_not"] = ["不得生成 owner decision", "不得关闭 owner gate", "不得修改源项目", "不得写 memory"]
    jsonl_path.write_text(json.dumps(manifest_row, ensure_ascii=False, separators=(",", ":")) + "\n")
    migration_row = {
        "from": "temporary regression fixture for final proof as-of date selector",
        "to": f"{md_rel}; {jsonl_rel}",
        "mode": "proof-date-selector-fixture",
        "status": "applied",
        "checked_at": "2026-06-23",
        "notes": "Temporary fixture proving final proof dynamic selector follows --as-of date and preserves 2026-06-22 seed baseline.",
        "notes_zh": "临时 fixture：证明 final proof 动态选择器跟随 --as-of 日期，同时保留 2026-06-22 seed 基线；不生成 owner decision、不关闭 owner gate、不修改源项目、不写 memory。",
    }
    with (repo / "registry" / "migrations.jsonl").open("a") as fh:
        fh.write(json.dumps(migration_row, ensure_ascii=False, separators=(",", ":")) + "\n")
    index_appends = {
        "indexes/by-owner.md": f"\n- `{artifact_id}`\n",
        "indexes/by-status.md": f"\n- reviewing: `{artifact_id}`\n- proof-date-selector-applied: proof 日期选择器 fixture 已登记；证据：`{jsonl_rel}`.\n",
        "indexes/by-review-date.md": f"\n- 2026-09-23: `{artifact_id}`\n",
        "indexes/by-topic.md": f"\n- Knowledge Hub proof 日期选择器 fixture: `{md_rel}`\n",
        "indexes/by-decision.md": f"\n- `{artifact_id}`: proof 日期选择器 fixture；证据：`{md_rel}`；不生成 owner decision、不关闭 owner gate、不写 memory。\n",
    }
    for relative, text in index_appends.items():
        with (repo / relative).open("a") as fh:
            fh.write(text)
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "-lc",
            "KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23",
        ],
    )
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    proof_artifacts = parsed.get("proof_artifacts", {}) if isinstance(parsed, dict) else {}
    legacy_proof_artifacts = parsed.get("proof_artifacts_20260622", {}) if isinstance(parsed, dict) else {}
    expect(
        not parse_error
        and result["exit_code"] == 1
        and legacy_proof_artifacts == proof_artifacts
        and proof_artifacts.get("status") == "pass"
        and proof_artifacts.get("selection_mode") == "seed-plus-dynamic-governance-by-as-of-date"
        and proof_artifacts.get("selection_date") == "2026-06-23"
        and artifact_id in proof_artifacts.get("dynamic_ids", [])
        and artifact_id in proof_artifacts.get("expected_ids", [])
        and set(proof_artifacts.get("seed_ids", [])) <= set(proof_artifacts.get("expected_ids", [])),
        "final-proof-artifact-as-of-date-selector",
        "final proof dynamic selector follows --as-of date and preserves baseline seed ids",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "final_status": parsed.get("final_status") if isinstance(parsed, dict) else "",
            "selection_mode": proof_artifacts.get("selection_mode"),
            "selection_date": proof_artifacts.get("selection_date"),
            "alias_equal": legacy_proof_artifacts == proof_artifacts,
            "dynamic_ids": proof_artifacts.get("dynamic_ids", []),
            "expected_ids": proof_artifacts.get("expected_ids", []),
            "missing_registry": proof_artifacts.get("missing_registry", []),
            "missing_md": proof_artifacts.get("missing_md", []),
            "missing_jsonl": proof_artifacts.get("missing_jsonl", []),
            "missing_migration": proof_artifacts.get("missing_migration", []),
            "missing_indexes": proof_artifacts.get("missing_indexes", {}),
            "stdout_sample": result["stdout"][:1000],
            "stderr_sample": result["stderr"][:1000],
        },
        repo,
    )

def test_final_proof_artifacts_stable_alias():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "-lc",
            "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23",
        ],
    )
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    stable = parsed.get("proof_artifacts", {}) if isinstance(parsed, dict) else {}
    legacy = parsed.get("proof_artifacts_20260622", {}) if isinstance(parsed, dict) else {}
    expect(
        not parse_error
        and result["exit_code"] == 0
        and parsed.get("final_status") == "ok"
        and stable
        and legacy
        and stable == legacy
        and stable.get("status") == "pass"
        and stable.get("selection_date") == "2026-06-23"
        and stable.get("selection_mode") == "seed-plus-dynamic-governance-by-as-of-date",
        "final-proof-artifacts-stable-alias",
        "final gate exposes stable proof_artifacts alias while keeping legacy date key compatible",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "final_status": parsed.get("final_status") if isinstance(parsed, dict) else "",
            "stable_present": bool(stable),
            "legacy_present": bool(legacy),
            "alias_equal": stable == legacy,
            "stable_status": stable.get("status"),
            "selection_date": stable.get("selection_date"),
            "stdout_sample": result["stdout"][:1000],
            "stderr_sample": result["stderr"][:1000],
        },
    )

def test_index_plan_extended_sections():
    section_results = {}
    parsed_by_section = {}
    parse_errors = {}
    for section in ["project", "source", "topic", "decision", "manifest", "linking", "review-queue"]:
        result = run_cmd(root, ["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", section, "--json"])
        section_results[section] = result
        try:
            parsed_by_section[section] = json.loads(result["stdout"])
        except Exception as exc:
            parsed_by_section[section] = {}
            parse_errors[section] = str(exc)
    manifest_text_result = run_cmd(root, ["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", "manifest"])

    project_index = parsed_by_section.get("project", {}).get("indexes", {}).get("by_project", {})
    source_index = parsed_by_section.get("source", {}).get("indexes", {}).get("by_source", {})
    source_selection = parsed_by_section.get("source", {}).get("source_coverage_selection", {})
    topic_index = parsed_by_section.get("topic", {}).get("indexes", {}).get("by_topic", {})
    decision_index = parsed_by_section.get("decision", {}).get("indexes", {}).get("by_decision", {})
    manifest_index = parsed_by_section.get("manifest", {}).get("indexes", {}).get("by_manifest", {})
    linking_audit = parsed_by_section.get("linking", {}).get("linking_audit", {})
    review_queue_index = parsed_by_section.get("review-queue", {}).get("indexes", {}).get("by_review_queue", {})
    review_queue_summary = review_queue_index.get("summary", {})
    registry_decisions = decision_index.get("registry_decisions", [])
    owner_worksheets = decision_index.get("owner_worksheets", [])
    migration_decisions = decision_index.get("migration_decisions", [])
    pcr02_source = source_index.get("pcr02-project-tools", {})
    source_coverage = pcr02_source.get("coverage", {})
    source_coverage_decision = source_coverage.get("decision", "")
    source_coverage_risk = source_coverage.get("risk", "")
    first_owner_worksheet = next(
        (row for row in owner_worksheets if row.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"),
        {},
    )
    manifest_summary = manifest_index.get("summary", {})
    manifest_unpaired = manifest_index.get("unpaired", [])
    manifest_unpaired_expected = manifest_index.get("unpaired_expected", [])
    manifest_unpaired_needs_review = manifest_index.get("unpaired_needs_review", [])
    latest_manifests = manifest_index.get("latest", [])
    current_owner_route_manifest = next(
        (row for row in manifest_index.get("rows", []) if row.get("id") == "knowledge-hub-owner-routing-recovery-20260621"),
        {},
    )
    current_manifest_profile = next(
        (row for row in manifest_index.get("rows", []) if row.get("id") == "knowledge-hub-manifest-profile-index-plan-20260621"),
        {},
    )
    current_runtime_recovery_profile = next(
        (row for row in manifest_index.get("rows", []) if row.get("id") == "knowledge-hub-final-proof-runtime-recovery-hardening-20260622"),
        {},
    )
    manifest_profile_health = manifest_summary.get("profile_health", {})
    latest_manifest_ids = [row.get("id") for row in latest_manifests]

    expect(
        not parse_errors
        and all(result["exit_code"] == 0 for result in section_results.values())
        and all(parsed_by_section.get(section, {}).get("status") == "planned" for section in section_results)
        and "pcr02" in project_index
        and project_index.get("pcr02", {}).get("domain") == "domains/projects/pcr02"
        and "pcr02-project-tools" in source_index
        and pcr02_source.get("owner") == "pcr02-registry-owner"
        and pcr02_source.get("review_after") == "2026-09-20"
        and pcr02_source.get("final_disposition") == "mixed-terminal-coverage"
        and pcr02_source.get("check", "").startswith("rtk bash -lc")
        and source_selection.get("strategy") == "filename-yyyymmdd-sort-last"
        and source_selection.get("selected") == "artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.jsonl"
        and source_selection.get("candidate_count", 0) >= 1
        and source_selection.get("dated_candidate_count", 0) >= 1
        and bool(source_coverage)
        and source_coverage.get("checked_at") == "2026-06-20"
        and bool(source_coverage_decision)
        and bool(source_coverage_risk)
        and "project-current" in topic_index
        and any(row.get("decision_id") == "knowledge-hub-root-path" for row in registry_decisions)
        and manifest_summary.get("jsonl_count", 0) >= 100
        and manifest_summary.get("markdown_count", 0) >= 100
        and manifest_summary.get("latest_strategy") == "filename-date-only"
        and "文件名中的 YYYYMMDD" in manifest_summary.get("latest_strategy_zh", "")
        and manifest_profile_health.get("pass", 0) >= 1
        and manifest_profile_health.get("legacy-missing-profile", 0) >= 1
        and manifest_summary.get("unpaired_count") == 6
        and manifest_summary.get("unpaired_expected_count") == 6
        and manifest_summary.get("unpaired_needs_review_count") == 0
        and len(manifest_unpaired_expected) == 6
        and len(manifest_unpaired_needs_review) == 0
        and all(row.get("review_status") == "expected" for row in manifest_unpaired)
        and all(row.get("pairing_status") in {"jsonl-only", "markdown-only"} for row in manifest_unpaired)
        and all(row.get("reasons_zh") and row.get("notes_zh") for row in manifest_unpaired)
        and manifest_text_result["exit_code"] == 0
        and "unpaired_expected_count: 6" in manifest_text_result["stdout"]
        and "unpaired_needs_review_count: 0" in manifest_text_result["stdout"]
        and "profile_health:" in manifest_text_result["stdout"]
        and "summary_source=`summary_zh`" in manifest_text_result["stdout"]
        and "evidence_source=`evidence_refs`" in manifest_text_result["stdout"]
        and "review_status=`expected`" in manifest_text_result["stdout"]
        and "pairing=`" in manifest_text_result["stdout"]
        and bool(latest_manifests)
        and all(row.get("date_source") in {"filename-YYYYMMDD", "missing-filename-date"} for row in latest_manifests)
        and all("row_date" in row for row in latest_manifests)
        and current_owner_route_manifest.get("paired") is True
        and current_owner_route_manifest.get("evidence_count", 0) >= 1
        and current_manifest_profile.get("paired") is True
        and current_manifest_profile.get("row_count") == 1
        and current_manifest_profile.get("evidence_count", 0) >= 1
        and current_manifest_profile.get("derived_evidence_count") == current_manifest_profile.get("evidence_count")
        and current_manifest_profile.get("derived_summary_zh") == current_manifest_profile.get("summary_zh")
        and current_manifest_profile.get("summary_source") in {"summary_zh", "notes_zh", "notes"}
        and current_manifest_profile.get("evidence_source") in {"evidence", "evidence_refs", "validation_refs", "verification_commands", "source_refs"}
        and current_manifest_profile.get("profile_health") in {"pass", "advisory-missing-boundary", "legacy-missing-profile"}
        and current_runtime_recovery_profile.get("paired") is True
        and current_runtime_recovery_profile.get("derived_summary_zh") == current_runtime_recovery_profile.get("summary_zh")
        and current_runtime_recovery_profile.get("summary_source") == "summary_zh"
        and current_runtime_recovery_profile.get("evidence_source") == "evidence_refs"
        and current_runtime_recovery_profile.get("profile_health") == "pass"
        and linking_audit.get("status") == "pass"
        and linking_audit.get("read_only") is True
        and linking_audit.get("source_body_read") is False
        and linking_audit.get("owner_gate_mutation") is False
        and linking_audit.get("cross_session", {}).get("status") == "pass"
        and linking_audit.get("cross_project", {}).get("status") == "pass"
        and linking_audit.get("cross_project", {}).get("registered_source_count") == 13
        and linking_audit.get("markdown_index_recovery", {}).get("status") == "pass"
        and linking_audit.get("markdown_index_recovery", {}).get("missing_anchors") == []
        and review_queue_summary.get("status") in {"needs-human-review", "empty"}
        and review_queue_summary.get("read_only") is True
        and review_queue_summary.get("report_only") is True
        and review_queue_summary.get("owner_gate_mutation") is False
        and review_queue_summary.get("memory_write") is False
        and review_queue_summary.get("active_or_promotion_blocker_count") == 0
        and review_queue_summary.get("ai_generated_pending_count", 0) >= 1
        and any(row.get("queue_type") == "ai-human-review" for row in review_queue_index.get("rows", []))
        and (
            "owner_route" in str(current_owner_route_manifest.get("summary_zh", "")).lower()
            or "路由" in str(current_owner_route_manifest.get("summary_zh", ""))
        )
        and first_owner_worksheet.get("owner") == "team-core-or-pcr02-docs-owner"
        and first_owner_worksheet.get("status") == "owner-approved"
        and first_owner_worksheet.get("review_after") == "2026-09-17"
        and first_owner_worksheet.get("decision_state") == "owner_decision:reference-only"
        and any(row.get("status") == "owner-approved" for row in owner_worksheets)
        and bool(migration_decisions),
        "index-plan-extended-sections",
        "index planner covers project/source/topic/decision/manifest sections",
        {
            "exit_codes": {section: result["exit_code"] for section, result in section_results.items()},
            "parse_errors": parse_errors,
            "statuses": {section: parsed_by_section.get(section, {}).get("status") for section in section_results},
            "project_keys_sample": sorted(project_index.keys())[:10],
            "source_has_pcr02_project_tools": "pcr02-project-tools" in source_index,
            "source_coverage_status": source_coverage.get("status", ""),
            "source_coverage_selection": source_selection,
            "source_coverage_decision": source_coverage_decision,
            "source_coverage_risk": source_coverage_risk,
            "source_owner": pcr02_source.get("owner", ""),
            "source_review_after": pcr02_source.get("review_after", ""),
            "source_final_disposition": pcr02_source.get("final_disposition", ""),
            "topic_keys_sample": sorted(topic_index.keys())[:10],
            "registry_decision_count": len(registry_decisions),
            "manifest_summary": manifest_summary,
            "manifest_profile_health": manifest_profile_health,
            "manifest_unpaired": manifest_unpaired,
            "manifest_text_stdout_sample": manifest_text_result["stdout"][:1200],
            "latest_manifest_count": len(latest_manifests),
            "latest_manifest_ids": latest_manifest_ids[:20],
            "current_owner_route_manifest": current_owner_route_manifest,
            "current_manifest_profile": current_manifest_profile,
            "current_runtime_recovery_profile": current_runtime_recovery_profile,
            "linking_audit": linking_audit,
            "review_queue_summary": review_queue_summary,
            "review_queue_row_count": len(review_queue_index.get("rows", [])),
            "owner_worksheet_count": len(owner_worksheets),
            "first_owner_worksheet": first_owner_worksheet,
            "migration_decision_count": len(migration_decisions),
        },
    )

def test_manifest_latest_filename_date_only():
    repo = copy_repo("manifest-latest-filename-date-only")
    manifests_dir = repo / "artifacts" / "manifests"
    old_by_filename = manifests_dir / "fixture-row-date-newer-20200101.jsonl"
    old_by_filename.write_text(
        '{"id":"fixture-row-date-newer","status":"applied","checked_at":"2099-01-01","summary_zh":"row 日期很新但文件名日期很旧，不能抢占 latest。","evidence_refs":["fixture"]}\n'
    )
    new_by_filename = manifests_dir / "fixture-filename-newer-20260624.jsonl"
    new_by_filename.write_text(
        '{"id":"fixture-filename-newer","status":"applied","checked_at":"2020-01-01","summary_zh":"文件名日期更新，应排在旧文件名前。","evidence_refs":["fixture"]}\n'
    )
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", "manifest", "--json"])
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    manifest_index = parsed.get("indexes", {}).get("by_manifest", {}) if isinstance(parsed, dict) else {}
    latest = manifest_index.get("latest", [])
    rows = manifest_index.get("rows", [])
    old_row = next((row for row in rows if row.get("id") == "fixture-row-date-newer"), {})
    new_row = next((row for row in rows if row.get("id") == "fixture-filename-newer"), {})
    expect(
        not parse_error
        and result["exit_code"] == 0
        and latest
        and latest[0].get("id") == "fixture-filename-newer"
        and old_row.get("date") == "2020-01-01"
        and old_row.get("row_date") == "2099-01-01"
        and old_row.get("date_source") == "filename-YYYYMMDD"
        and new_row.get("date") == "2026-06-24"
        and new_row.get("row_date") == "2020-01-01",
        "manifest-latest-filename-date-only",
        "manifest latest view sorts only by filename date, not JSONL row dates",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "latest_first": latest[0] if latest else {},
            "old_row": old_row,
            "new_row": new_row,
        },
        repo,
    )

def test_manifest_jsonl_profile_gate():
    repo = copy_repo("manifest-jsonl-profile-gate")
    manifest_paths = [
        repo / "artifacts" / "manifests" / "knowledge-hub-manifest-profile-index-plan-20260621.jsonl",
        repo / "artifacts" / "manifests" / "knowledge-hub-manual-source-kind-contract-20260622.jsonl",
    ]
    setup_errors = []
    try:
        for manifest_path in manifest_paths:
            rows = []
            for line in manifest_path.read_text().splitlines():
                if not line.strip():
                    continue
                rows.append(json.loads(line))
            rows[0].pop("summary_zh", None)
            rows[0].pop("notes_zh", None)
            rows[0].pop("evidence", None)
            rows[0].pop("evidence_refs", None)
            rows[0].pop("validation_refs", None)
            rows[0].pop("verification_commands", None)
            rows[0].pop("source_refs", None)
            manifest_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
    except Exception as exc:
        setup_errors.append(str(exc))
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    errors = parsed.get("errors", [])
    expect(
        not setup_errors
        and result["exit_code"] != 0
        and any("manifest-profile:knowledge-hub-manifest-profile-index-plan-20260621 missing summary_zh or notes_zh" in error for error in errors)
        and any("manifest-profile:knowledge-hub-manifest-profile-index-plan-20260621 missing evidence field" in error for error in errors)
        and any("manifest-profile:knowledge-hub-manual-source-kind-contract-20260622 missing summary_zh or notes_zh" in error for error in errors)
        and any("manifest-profile:knowledge-hub-manual-source-kind-contract-20260622 missing evidence field" in error for error in errors),
        "manifest-jsonl-profile-gate",
        "knowledge-check requires lightweight profile fields for governance manifest JSONL rows dated 2026-06-21 or later",
        {
            "setup_errors": setup_errors,
            "exit_code": result["exit_code"],
            "errors": errors[:10],
        },
    )

def test_template_readability_field_gate():
    repo = copy_repo("template-readability-field-gate")
    template_path = repo / "templates" / "runbook.md"
    try:
        text = template_path.read_text()
        text = "\n".join(line for line in text.splitlines() if not line.startswith("summary_zh:"))
        template_path.write_text(text + "\n")
        setup_error = ""
    except Exception as exc:
        setup_error = str(exc)
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    errors = parsed.get("errors", [])
    expect(
        not setup_error
        and result["exit_code"] != 0
        and any("template:templates/runbook.md missing readability field summary_zh" in error for error in errors),
        "template-readability-field-gate",
        "knowledge-check requires long-term readability fields in maintained templates",
        {
            "setup_error": setup_error,
            "exit_code": result["exit_code"],
            "errors": errors[:10],
        },
    )

def test_index_plan_topic_schema_health():
    result = run_cmd(root, ["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", "topic", "--json"])
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    topics_doc = json.loads((root / "registry" / "topics.json").read_text())
    registry_topic_ids = sorted(topic.get("id", "") for topic in topics_doc.get("topics", []) if topic.get("id"))
    planner_topic_ids = sorted(parsed.get("indexes", {}).get("by_topic", {}).keys())
    expect(
        result["exit_code"] == 0
        and not parse_error
        and parsed.get("status") == "planned"
        and planner_topic_ids == registry_topic_ids,
        "index-plan-topic-schema-health",
        "index planner topic section mirrors registry/topics.json ids",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "registry_topic_ids": registry_topic_ids,
            "planner_topic_ids": planner_topic_ids,
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_index_plan_decision_registry_health():
    result = run_cmd(root, ["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", "decision", "--json"])
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    registry_decision_ids = []
    for line in (root / "registry" / "decisions.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        registry_decision_ids.append(json.loads(line).get("decision_id", ""))
    planner_decision_ids = [
        decision.get("decision_id", "")
        for decision in parsed.get("indexes", {}).get("by_decision", {}).get("registry_decisions", [])
    ]
    expect(
        result["exit_code"] == 0
        and not parse_error
        and parsed.get("status") == "planned"
        and sorted(planner_decision_ids) == sorted(registry_decision_ids)
        and len(planner_decision_ids) == len(set(planner_decision_ids)),
        "index-plan-decision-registry-health",
        "index planner decision section covers registry decisions exactly once",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "registry_decision_ids": sorted(registry_decision_ids),
            "planner_decision_ids": sorted(planner_decision_ids),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_index_decision_registry_gate():
    repo = copy_repo("index-decision-registry-gate")
    index_path = repo / "indexes" / "by-decision.md"
    text = index_path.read_text()
    index_path.write_text(text.replace("`automation-report-only-default`", "`automation-report-only-default-stale`", 1))
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    expect(
        result["exit_code"] != 0
        and "index:indexes/by-decision.md missing registry decision automation-report-only-default" in result["stdout"],
        "index-decision-registry-subsection-gate",
        "by-decision hard gate protects registry decisions without locking owner worksheet rows",
        {
            "exit_code": result["exit_code"],
            "stdout_sample": result["stdout"][:1200],
            "stderr_sample": result["stderr"][:500],
        },
        repo,
    )

def test_index_topic_zero_bucket_allowed():
    result = run_cmd(root, ["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", "topic", "--json"])
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    by_topic = parsed.get("indexes", {}).get("by_topic", {}) if isinstance(parsed, dict) else {}
    empty_topics = sorted(topic_id for topic_id, detail in by_topic.items() if not detail.get("items"))
    expect(
        result["exit_code"] == 0
        and not parse_error
        and parsed.get("status") == "planned"
        and set(empty_topics) <= set(by_topic.keys()),
        "index-topic-zero-bucket-allowed",
        "topic planner treats empty topics as health data instead of hard failure",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "empty_topics": empty_topics,
            "topic_count": len(by_topic),
        },
    )

def test_status_source_governance_summary():
    result = run_cmd(root, ["rtk", "bash", "tools/knowledge-status.sh", "--json"])
    check_result = run_cmd(root, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    expected_final_gate_command = "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json"
    if today_source != "system-date":
        expected_final_gate_command = f"rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --as-of {today.isoformat()} --json"
    parsed = {}
    check_parsed = {}
    parse_error = ""
    check_parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    try:
        check_parsed = json.loads(check_result["stdout"])
    except Exception as exc:
        check_parse_error = str(exc)
    sources = parsed.get("sources", {}) if isinstance(parsed.get("sources"), dict) else {}
    registry = parsed.get("registry", {}) if isinstance(parsed.get("registry"), dict) else {}
    owner_gates = parsed.get("owner_gates", {}) if isinstance(parsed.get("owner_gates"), dict) else {}
    check_selection = check_parsed.get("source_coverage_selection", {}) if isinstance(check_parsed, dict) else {}
    check_health = check_parsed.get("source_coverage_health", {}) if isinstance(check_parsed, dict) else {}
    check_source_check_health = check_parsed.get("source_check_health", {}) if isinstance(check_parsed, dict) else {}
    check_boundary_health = check_parsed.get("boundary_health", {}) if isinstance(check_parsed, dict) else {}
    status_source_check_health = sources.get("source_check_health", {}) if isinstance(sources.get("source_check_health"), dict) else {}
    status_source_check_snapshot = sources.get("source_check_execution_snapshot", {}) if isinstance(sources.get("source_check_execution_snapshot"), dict) else {}
    status_boundary_health = sources.get("boundary_health", {}) if isinstance(sources.get("boundary_health"), dict) else {}
    source_recovery_rows = sources.get("source_recovery_rows", []) if isinstance(sources.get("source_recovery_rows"), list) else []
    source_recovery_by_id = {
        row.get("source_id"): row
        for row in source_recovery_rows
        if isinstance(row, dict)
    }
    pcr02_docs_recovery = source_recovery_by_id.get("pcr02-project-docs", {})
    pcr02_tools_recovery = source_recovery_by_id.get("pcr02-project-tools", {})
    expect(
        result["exit_code"] == 0
        and not parse_error
        and check_result["exit_code"] == 0
        and not check_parse_error
        and sources.get("registered_count") == 13
        and sources.get("latest_coverage_manifest") == "artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.jsonl"
        and sources.get("latest_coverage_selection", {}).get("strategy") == "filename-yyyymmdd-sort-last"
        and sources.get("latest_coverage_selection", {}).get("selected") == "artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.jsonl"
        and sources.get("latest_coverage_selection", {}).get("candidate_count", 0) >= 1
        and sources.get("latest_coverage_selection", {}).get("dated_candidate_count", 0) >= 1
        and check_selection.get("selected") == "artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.jsonl"
        and check_selection.get("strategy") == "filename-yyyymmdd-sort-last"
        and check_health.get("registered_source_count") == 13
        and check_health.get("row_count") == 13
        and check_health.get("unique_source_count") == 13
        and check_health.get("missing_source_ids") == []
        and check_health.get("stale_source_ids") == []
        and check_health.get("duplicate_source_ids") == []
        and check_source_check_health.get("with_check_count") == 9
        and check_source_check_health.get("with_no_check_reason_count") == 4
        and check_source_check_health.get("missing_check_or_reason_ids") == []
        and check_source_check_health.get("non_rtk_check_ids") == []
        and check_boundary_health.get("status") == "pass"
        and check_boundary_health.get("summary", {}).get("source_coverage_count") == 7
        and status_source_check_health.get("with_check_count") == 9
        and status_source_check_health.get("executed") is False
        and status_source_check_snapshot.get("status") == "pass"
        and status_source_check_snapshot.get("artifact_id") == "pcr02-level2-source-check-execution-snapshot-20260621"
        and status_source_check_snapshot.get("scope") == "pcr02-level2-only"
        and status_source_check_snapshot.get("execution_mode") == "report-only-manual-snapshot"
        and status_source_check_snapshot.get("runtime_execution") is False
        and status_source_check_snapshot.get("source_check_health_contract") == "static-registry-only"
        and status_source_check_snapshot.get("row_count") == 7
        and status_source_check_snapshot.get("passed_count") == 7
        and status_source_check_snapshot.get("all_executed") is True
        and status_source_check_snapshot.get("all_exit_0") is True
        and status_source_check_snapshot.get("missing_source_ids") == []
        and status_source_check_snapshot.get("unexpected_source_ids") == []
        and status_source_check_snapshot.get("failed_rows") == []
        and status_boundary_health.get("status") == "pass"
        and status_boundary_health.get("source_project_read") is False
        and len(source_recovery_rows) == 13
        and pcr02_docs_recovery.get("final_disposition") == "mixed-terminal-coverage"
        and pcr02_docs_recovery.get("coverage_status") == "covered-control-plane"
        and "owner-gated" in pcr02_docs_recovery.get("coverage_classification", "")
        and "owner" in pcr02_docs_recovery.get("coverage_decision", "")
        and pcr02_docs_recovery.get("has_no_check_reason") is True
        and pcr02_tools_recovery.get("check_contract_status") == "ok"
        and pcr02_tools_recovery.get("has_check") is True
        and pcr02_tools_recovery.get("coverage_status") == "registered-reference-tool-boundary"
        and registry.get("stale_review_after_count") == 0
        and registry.get("review_after_command") == "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date"
        and registry.get("review_after_near_due_command") == f"rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of {today.isoformat()} --window-days 30 --json"
        and sources.get("source_check_report_command") == f"rtk bash ~/knowledge-hub/tools/knowledge-source-check.sh --scope pcr02-level2 --as-of {today.isoformat()} --json"
        and owner_gates.get("owner_ready_package_coverage") == "7/7"
        and parsed.get("final_gate_command") == expected_final_gate_command,
        "status-source-governance-summary",
        "status JSON exposes source coverage, review_after and final gate recovery summary",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "check_exit_code": check_result["exit_code"],
            "check_parse_error": check_parse_error,
            "registered_count": sources.get("registered_count"),
            "latest_coverage_manifest": sources.get("latest_coverage_manifest"),
            "latest_coverage_selection": sources.get("latest_coverage_selection"),
            "check_source_coverage_selection": check_selection,
            "check_source_coverage_health": check_health,
            "check_source_check_health": check_source_check_health,
            "check_boundary_health": check_boundary_health,
            "status_source_check_health": status_source_check_health,
            "status_source_check_execution_snapshot": status_source_check_snapshot,
            "status_boundary_health": status_boundary_health,
            "stale_review_after_count": registry.get("stale_review_after_count"),
            "review_after_command": registry.get("review_after_command"),
            "review_after_near_due_command": registry.get("review_after_near_due_command"),
            "source_check_report_command": sources.get("source_check_report_command"),
            "source_recovery_row_count": len(source_recovery_rows),
            "pcr02_docs_recovery": pcr02_docs_recovery,
            "pcr02_tools_recovery": pcr02_tools_recovery,
            "owner_ready_package_coverage": owner_gates.get("owner_ready_package_coverage"),
            "final_gate_command": parsed.get("final_gate_command"),
            "expected_final_gate_command": expected_final_gate_command,
            "status": parsed.get("status"),
            "stdout_sample": result["stdout"][:1200],
        },
    )

def test_source_check_health_contract():
    result = run_cmd(root, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    source_check_health = parsed.get("source_check_health", {}) if isinstance(parsed, dict) else {}

    repo = copy_repo("source-check-health-non-rtk")
    sources_path = repo / "registry" / "sources.json"
    sources_doc = json.loads(sources_path.read_text())
    for source in sources_doc.get("sources", []):
        if source.get("id") == "pcr02-project-tools":
            source["check"] = str(source.get("check", "")).replace("rtk ", "bash ", 1)
            break
    sources_path.write_text(json.dumps(sources_doc, ensure_ascii=False, indent=2) + "\n")
    bad_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    bad_parsed = {}
    bad_parse_error = ""
    try:
        bad_parsed = json.loads(bad_result["stdout"])
    except Exception as exc:
        bad_parse_error = str(exc)
    bad_source_check_health = bad_parsed.get("source_check_health", {}) if isinstance(bad_parsed, dict) else {}
    expect(
        result["exit_code"] == 0
        and not parse_error
        and source_check_health.get("mode") == "static-registry-only"
        and source_check_health.get("executed") is False
        and source_check_health.get("registered_source_count") == 13
        and source_check_health.get("with_check_count") == 9
        and source_check_health.get("with_no_check_reason_count") == 4
        and source_check_health.get("missing_check_or_reason_ids") == []
        and source_check_health.get("non_rtk_check_ids") == []
        and source_check_health.get("missing_source_path_ids") == []
        and len(source_check_health.get("rows", [])) == 13
        and all(row.get("execution_status") == "not-run" for row in source_check_health.get("rows", []))
        and bad_result["exit_code"] != 0
        and not bad_parse_error
        and "pcr02-project-tools" in bad_source_check_health.get("non_rtk_check_ids", [])
        and any("check must start with rtk" in str(error) for error in bad_parsed.get("errors", [])),
        "source-check-health-contract",
        "source check health statically validates check/no-check contracts without executing commands",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "source_check_health": source_check_health,
            "bad_exit_code": bad_result["exit_code"],
            "bad_parse_error": bad_parse_error,
            "bad_source_check_health": bad_source_check_health,
            "bad_errors": bad_parsed.get("errors", [])[:5],
        },
    )

def test_source_check_report_only_helper():
    result = run_cmd(root, ["rtk", "bash", "tools/knowledge-source-check.sh", "--scope", "pcr02-level2", "--json", "--as-of", today.isoformat()])
    check_result = run_cmd(root, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    parsed = {}
    check_parsed = {}
    parse_error = ""
    check_parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    try:
        check_parsed = json.loads(check_result["stdout"])
    except Exception as exc:
        check_parse_error = str(exc)
    source_check_health = check_parsed.get("source_check_health", {}) if isinstance(check_parsed, dict) else {}
    rows = parsed.get("rows", []) if isinstance(parsed.get("rows"), list) else []
    expect(
        result["exit_code"] == 0
        and not parse_error
        and parsed.get("status") == "pass"
        and parsed.get("read_only") is True
        and parsed.get("report_only") is True
        and parsed.get("scope") == "pcr02-level2"
        and parsed.get("source_check_health_contract") == "static-registry-only"
        and parsed.get("source_check_health_executed") is False
        and parsed.get("source_body_read") is False
        and parsed.get("owner_gate_mutation") is False
        and parsed.get("memory_write") is False
        and parsed.get("row_count") == 7
        and parsed.get("executed_count") == 7
        and parsed.get("passed_count") == 7
        and parsed.get("failed_count") == 0
        and parsed.get("unsupported_count") == 0
        and parsed.get("rejected_count") == 0
        and all(row.get("executed") is True and row.get("exit_code") == 0 for row in rows)
        and check_result["exit_code"] == 0
        and not check_parse_error
        and source_check_health.get("mode") == "static-registry-only"
        and source_check_health.get("executed") is False,
        "source-check-report-only-helper",
        "source check helper executes only allowlisted PCR02 Level 2 availability checks",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "status": parsed.get("status"),
            "row_count": parsed.get("row_count"),
            "executed_count": parsed.get("executed_count"),
            "passed_count": parsed.get("passed_count"),
            "failed_count": parsed.get("failed_count"),
            "unsupported_count": parsed.get("unsupported_count"),
            "rejected_count": parsed.get("rejected_count"),
            "check_exit_code": check_result["exit_code"],
            "check_parse_error": check_parse_error,
            "source_check_health": source_check_health,
        },
    )

def test_source_check_rejects_unsafe_runtime_command():
    repo = copy_repo("source-check-rejects-unsafe-runtime-command")
    sources_path = repo / "registry" / "sources.json"
    try:
        payload = json.loads(sources_path.read_text())
        for source in payload.get("sources", []):
            if source.get("id") == "pcr02-project-tools":
                source["check"] = "rtk bash -lc 'test -d /tmp && echo unsafe'"
                break
        sources_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    except Exception as exc:
        expect(False, "source-check-rejects-unsafe-runtime-command", "source check helper rejects shell control payloads", {"setup_error": str(exc)}, repo)
        return
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-source-check.sh", "--scope", "pcr02-level2", "--source-id", "pcr02-project-tools", "--json", "--as-of", today.isoformat()])
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    first = parsed.get("rows", [{}])[0] if parsed.get("rows") else {}
    expect(
        result["exit_code"] == 1
        and not parse_error
        and parsed.get("status") == "fail"
        and parsed.get("row_count") == 1
        and parsed.get("executed_count") == 0
        and first.get("result") in {"unsupported-runtime-check", "rejected-runtime-check"}
        and first.get("executed") is False,
        "source-check-rejects-unsafe-runtime-command",
        "source check helper rejects shell control payloads",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "status": parsed.get("status"),
            "first_row": first,
            "stderr_sample": result["stderr"][:500],
        },
        repo,
    )

def test_final_gate_source_check_runtime_failed_blocker():
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
        expect(
            True,
            "final-gate-source-check-runtime-failed-blocker",
            "final gate blocks failed source-check runtime evidence",
            {"skipped_in_inner_final_gate": True},
        )
        return
    repo = copy_repo("final-gate-source-check-runtime-failed-blocker")
    sources_path = repo / "registry" / "sources.json"
    missing_suffix = "__kh_missing_source_check_fixture__"
    try:
        payload = json.loads(sources_path.read_text())
        updated = False
        for source in payload.get("sources", []):
            if source.get("id") == "pcr02-project-tools":
                source_path = str(source.get("path", "")).rstrip("/")
                source["check"] = f"rtk bash -lc 'test -d {source_path}/{missing_suffix}'"
                updated = True
                break
        if not updated:
            raise RuntimeError("pcr02-project-tools source not found")
        sources_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    except Exception as exc:
        expect(False, "final-gate-source-check-runtime-failed-blocker", "final gate blocks failed source-check runtime evidence", {"setup_error": str(exc)}, repo)
        return

    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "-lc",
            "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22",
        ],
    )
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    blockers = parsed.get("blockers", [])
    blocker = next((row for row in blockers if row.get("id") == "source-check-runtime-failed"), {})
    source_check_runtime = parsed.get("source_check_runtime", {})
    checks_source_check_runtime = parsed.get("checks", {}).get("source_check_runtime", {})
    gap_map = parsed.get("gap_map", [])
    source_gap = next((row for row in gap_map if row.get("gap_id") == "source-check-runtime-failed"), {})
    expect(
        result["exit_code"] == 1
        and not parse_error
        and parsed.get("final_status") == "needs-fix"
        and blocker.get("severity") == "blocker"
        and blocker.get("gap_type") == "source-coverage"
        and source_gap.get("gap_type") == "source-coverage"
        and source_check_runtime.get("status") == "fail"
        and source_check_runtime.get("runtime_execution") is True
        and source_check_runtime.get("read_only") is True
        and source_check_runtime.get("report_only") is True
        and source_check_runtime.get("source_body_read") is False
        and source_check_runtime.get("owner_gate_mutation") is False
        and source_check_runtime.get("memory_write") is False
        and source_check_runtime.get("failed_count") == 1
        and checks_source_check_runtime.get("status") == "fail",
        "final-gate-source-check-runtime-failed-blocker",
        "final gate blocks failed source-check runtime evidence",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "final_status": parsed.get("final_status"),
            "blocker": blocker,
            "source_gap": source_gap,
            "source_check_runtime": source_check_runtime,
            "checks_source_check_runtime": checks_source_check_runtime,
            "stdout_sample": result["stdout"][:1200],
            "stderr_sample": result["stderr"][:500],
        },
        repo,
    )

def test_review_after_near_due_json_contract():
    repo = copy_repo_with_open_owner_gates("review-after-near-due-json-contract")
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-review-after.sh", "--json", "--as-of", "2026-06-22", "--window-days", "30"])
    owner_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-review-after.sh", "--json", "--as-of", "2026-06-22", "--window-days", "30", "--include-owner-gates"])
    parsed = {}
    owner_parsed = {}
    parse_error = ""
    owner_parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    try:
        owner_parsed = json.loads(owner_result["stdout"])
    except Exception as exc:
        owner_parse_error = str(exc)
    counts = parsed.get("counts", {}) if isinstance(parsed.get("counts"), dict) else {}
    groups = parsed.get("groups", {}) if isinstance(parsed.get("groups"), dict) else {}
    rows = parsed.get("rows", []) if isinstance(parsed.get("rows"), list) else []
    owner_counts = owner_parsed.get("counts", {}) if isinstance(owner_parsed.get("counts"), dict) else {}
    owner_rows = owner_parsed.get("rows", []) if isinstance(owner_parsed.get("rows"), list) else []
    owner_gate_rows = [row for row in owner_rows if row.get("row_type") == "open_owner_gate"]
    archived_rows = [row for row in rows if row.get("status") == "archived"]
    expect(
        result["exit_code"] == 0
        and owner_result["exit_code"] == 0
        and not parse_error
        and not owner_parse_error
        and parsed.get("status") == "report-only"
        and owner_parsed.get("status") == "report-only"
        and parsed.get("read_only") is True
        and parsed.get("report_only") is True
        and parsed.get("today") == "2026-06-22"
        and parsed.get("item_window_end") == "2026-07-22"
        and counts.get("stale_items") == 0
        and counts.get("near_due_items") == 32
        and counts.get("stale_sources") == 0
        and counts.get("near_due_sources") == 0
        and counts.get("owner_gate_open_count") == 7
        and counts.get("detail_row_count") == 32
        and counts.get("missing_source_id_count") == 9
        and owner_counts.get("owner_gate_open_count") == 7
        and owner_counts.get("detail_row_count") == 39
        and len(owner_gate_rows) == 7
        and all(row.get("worksheet_file", "").endswith("owner-decision-worksheets-20260618.jsonl") for row in owner_gate_rows)
        and groups.get("grouping_contract_version") == 1
        and groups.get("by_owner", {}).get("team-core", {}).get("count") == 23
        and groups.get("by_owner", {}).get("leiwenjun", {}).get("count") == 9
        and groups.get("by_status", {}).get("reviewing", {}).get("count") == 26
        and groups.get("by_status", {}).get("archived", {}).get("count") == 6
        and groups.get("by_domain", {}).get("projects/pcr02", {}).get("count") == 31
        and groups.get("by_source_id", {}).get("pcr02-project-docs", {}).get("count") == 23
        and groups.get("by_source_id", {}).get("<missing-source-id>", {}).get("count") == 9
        and len(archived_rows) >= 1
        and all("source_status" in row for row in rows)
        and any("archive-only" in str(row.get("suggested_action_zh", "")) for row in archived_rows)
        and "不得把 near-due warning 当作 blocking error" in parsed.get("must_not", []),
        "review-after-near-due-json-contract",
        "review_after helper reports 30-day near-due items without creating a blocking gate",
        {
            "exit_code": result["exit_code"],
            "owner_exit_code": owner_result["exit_code"],
            "parse_error": parse_error,
            "owner_parse_error": owner_parse_error,
            "status": parsed.get("status"),
            "counts": counts,
            "owner_counts": owner_counts,
            "groups": groups,
            "archived_row_count": len(archived_rows),
            "owner_gate_row_count": len(owner_gate_rows),
            "stderr_sample": result["stderr"][:500],
            "owner_stderr_sample": owner_result["stderr"][:500],
        },
    )

def test_automation_report_only_safety_gate():
    repo = copy_repo("automation-report-only-safety-gate")
    maintenance_path = repo / "registry" / "maintenance-runs.jsonl"
    rows = []
    try:
        for line in maintenance_path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("automation_id") == "memory-auto-curation-report-only":
                row["enabled"] = True
                row["mode"] = "apply"
                row["writes_memory"] = True
                row["writes_team_active_index"] = True
                row.pop("no_memory_write_gate", None)
            rows.append(row)
        maintenance_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n"
        )
        setup_error = ""
    except Exception as exc:
        setup_error = str(exc)
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-check.sh",
            "--dry-run",
            "--json",
            "--diagnostics",
            "--as-of",
            today.isoformat(),
        ],
    )
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    errors = parsed.get("errors", [])
    health = parsed.get("automation_safety_health", {})
    expect(
        not setup_error
        and result["exit_code"] == 1
        and parsed.get("status") == "fail"
        and "memory-auto-curation-20260618-definition" in health.get("unsafe_run_ids", [])
        and any("enabled must be false" in error for error in errors)
        and any("mode must be report-only" in error for error in errors)
        and any("writes_memory must be false" in error for error in errors)
        and any("writes_team_active_index must be false" in error for error in errors)
        and any("no_memory_write_gate is required" in error for error in errors),
        "automation-report-only-safety-gate",
        "knowledge-check rejects enabled or memory-writing automation records",
        {
            "setup_error": setup_error,
            "exit_code": result["exit_code"],
            "status": parsed.get("status"),
            "automation_safety_health": health,
            "errors": errors,
            "stdout_sample": result["stdout"][:1200],
        },
        repo,
    )

def test_source_coverage_date_filename_selection():
    repo = copy_repo("source-coverage-date-filename-selection")
    bad_candidate = repo / "artifacts" / "manifests" / "knowledge-hub-source-coverage-closeout-latest.jsonl"
    bad_candidate.write_text(
        '{"id":"fixture-bad-latest","source_id":"fixture-stale","status":"bad","classification":"bad","decision":"bad","risk":"bad","owner":"bad","checked_at":"2026-06-21"}\n'
    )
    check_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    status_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-status.sh", "--json"])
    index_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", "source", "--json"])
    final_result = run_cmd(repo, ["rtk", "bash", "-lc", "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json"])
    parse_errors = []
    parsed = {}
    status_parsed = {}
    index_parsed = {}
    final_parsed = {}
    for label, result, target in [
        ("check", check_result, "parsed"),
        ("status", status_result, "status_parsed"),
        ("index", index_result, "index_parsed"),
        ("final", final_result, "final_parsed"),
    ]:
        try:
            value = json.loads(result["stdout"])
        except Exception as exc:
            parse_errors.append(f"{label}: {exc}")
            value = {}
        if target == "parsed":
            parsed = value
        elif target == "status_parsed":
            status_parsed = value
        elif target == "index_parsed":
            index_parsed = value
        else:
            final_parsed = value
    expected_selected = "artifacts/manifests/knowledge-hub-source-coverage-closeout-20260620.jsonl"
    expected_ignored = "artifacts/manifests/knowledge-hub-source-coverage-closeout-latest.jsonl"
    check_selection = parsed.get("source_coverage_selection", {}) if isinstance(parsed, dict) else {}
    status_selection = (
        status_parsed.get("sources", {}).get("latest_coverage_selection", {})
        if isinstance(status_parsed.get("sources", {}), dict)
        else {}
    )
    index_selection = index_parsed.get("source_coverage_selection", {}) if isinstance(index_parsed, dict) else {}
    final_selection = (
        final_parsed.get("final_state_audit", {}).get("level3_registered_sources", {}).get("source_coverage_selection", {})
        if isinstance(final_parsed.get("final_state_audit", {}), dict)
        else {}
    )
    expect(
        check_result["exit_code"] == 0
        and status_result["exit_code"] == 0
        and index_result["exit_code"] == 0
        and final_result["exit_code"] == 1
        and not parse_errors
        and check_selection.get("selected") == expected_selected
        and status_selection.get("selected") == expected_selected
        and index_selection.get("selected") == expected_selected
        and final_selection.get("selected") == expected_selected
        and expected_ignored in check_selection.get("ignored_non_date_candidates", [])
        and expected_ignored in status_selection.get("ignored_non_date_candidates", [])
        and expected_ignored in index_selection.get("ignored_non_date_candidates", [])
        and expected_ignored in final_selection.get("ignored_non_date_candidates", [])
        and any(expected_ignored in warning for warning in parsed.get("warnings", [])),
        "source-coverage-date-filename-selection",
        "source coverage latest selection ignores non-YYYYMMDD closeout candidates",
        {
            "check_exit_code": check_result["exit_code"],
            "status_exit_code": status_result["exit_code"],
            "index_exit_code": index_result["exit_code"],
            "final_exit_code": final_result["exit_code"],
            "parse_errors": parse_errors,
            "check_selection": check_selection,
            "status_selection": status_selection,
            "index_selection": index_selection,
            "final_selection": final_selection,
            "check_warnings": parsed.get("warnings", []),
        },
        repo,
    )

def test_source_coverage_duplicate_source_id_warning():
    repo = copy_repo("source-coverage-duplicate-source-id-warning")
    coverage_path = repo / "artifacts" / "manifests" / "knowledge-hub-source-coverage-closeout-20260620.jsonl"
    rows = [line for line in coverage_path.read_text().splitlines() if line.strip()]
    first = json.loads(rows[0])
    duplicate = dict(first)
    duplicate["id"] = "SCC-20260620-duplicate-fixture"
    duplicate["status"] = "fixture-duplicate-should-not-overwrite"
    duplicate["decision"] = "duplicate fixture should be warned and ignored for recovery view"
    coverage_path.write_text("\n".join(rows + [json.dumps(duplicate, ensure_ascii=False, separators=(",", ":"))]) + "\n")
    result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-index-plan.sh", "--section", "source", "--json"])
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    selection = parsed.get("source_coverage_selection", {}) if isinstance(parsed, dict) else {}
    source_id = first.get("source_id", "")
    source_view = parsed.get("indexes", {}).get("by_source", {}).get(source_id, {}) if isinstance(parsed, dict) else {}
    coverage = source_view.get("coverage", {}) if isinstance(source_view, dict) else {}
    warnings_text = "\n".join(parsed.get("warnings", [])) if isinstance(parsed, dict) else ""
    expect(
        not parse_error
        and result["exit_code"] == 0
        and source_id in selection.get("duplicate_source_ids", [])
        and selection.get("duplicate_policy") == "first-row-kept-duplicates-warned"
        and source_id in selection.get("duplicate_rows", {})
        and "duplicate source_id rows" in warnings_text
        and coverage.get("status") == first.get("status")
        and coverage.get("status") != "fixture-duplicate-should-not-overwrite",
        "source-coverage-duplicate-source-id-warning",
        "index plan warns on duplicate source coverage rows and keeps first recovery row",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "source_id": source_id,
            "selection": selection,
            "coverage": coverage,
            "warnings": parsed.get("warnings", []) if isinstance(parsed, dict) else [],
        },
        repo,
    )

def test_review_after_as_of_deterministic():
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
        expect(
            True,
            "review-after-as-of-deterministic",
            "review-after as-of fixture is skipped inside nested regression",
            {"skipped_in_inner_final_gate": True},
        )
        return
    repo = copy_repo("review-after-as-of")
    setup_error = init_temp_git_repo(repo)
    if setup_error:
        expect(False, "review-after-as-of-deterministic", "--as-of fixes review_after warning semantics for check/status/final-gate", setup_error, repo)
        return
    item_id = "knowledge-hub-final-maintenance-closure-20260620"
    path = repo / "registry" / "items.jsonl"
    lines = path.read_text().splitlines()
    updated_lines = []
    mutated = False
    for line in lines:
        if not line.strip():
            updated_lines.append(line)
            continue
        row = json.loads(line)
        if row.get("id") == item_id:
            row["review_after"] = "2026-06-30"
            row["status"] = "reviewing"
            mutated = True
            updated_lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
        else:
            updated_lines.append(line)
    if not mutated:
        expect(False, "review-after-as-of-deterministic", "--as-of fixes review_after warning semantics for check/status/final-gate", {"setup_error": f"missing {item_id}"}, repo)
        return
    path.write_text("\n".join(updated_lines) + "\n")

    past_check = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics", "--as-of", "2026-06-01"])
    future_check = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics", "--as-of", "2026-07-01"])
    past_status = run_cmd(repo, ["rtk", "bash", "tools/knowledge-status.sh", "--json", "--as-of", "2026-06-01"])
    future_status = run_cmd(repo, ["rtk", "bash", "tools/knowledge-status.sh", "--json", "--as-of", "2026-07-01"])
    final_result = run_cmd(repo, ["rtk", "bash", "-lc", "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-01"])
    parsed = {}
    parse_errors = {}
    for name, result in [
        ("past_check", past_check),
        ("future_check", future_check),
        ("past_status", past_status),
        ("future_status", future_status),
        ("final_gate", final_result),
    ]:
        try:
            parsed[name] = json.loads(result["stdout"])
        except Exception as exc:
            parse_errors[name] = str(exc)
    past_warnings = "\n".join(parsed.get("past_check", {}).get("warnings", []))
    future_warnings = "\n".join(parsed.get("future_check", {}).get("warnings", []))
    past_registry = parsed.get("past_status", {}).get("registry", {})
    future_registry = parsed.get("future_status", {}).get("registry", {})
    past_actions_text = "\n".join(parsed.get("past_status", {}).get("next_actions_zh", []))
    expect(
        not parse_errors
        and past_check["exit_code"] == 0
        and future_check["exit_code"] == 0
        and item_id not in past_warnings
        and item_id in future_warnings
        and parsed.get("past_check", {}).get("today") == "2026-06-01"
        and parsed.get("past_check", {}).get("as_of_source") == "arg:--as-of"
        and parsed.get("past_status", {}).get("today") == "2026-06-01"
        and parsed.get("past_status", {}).get("as_of_source") == "arg:--as-of"
        and parsed.get("past_status", {}).get("final_gate_command") == "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --as-of 2026-06-01 --json"
        and (
            "knowledge-final-gate.sh --as-of 2026-06-01 --json" in past_actions_text
            or parsed.get("past_status", {}).get("status") == "ok"
        )
        and not any(row.get("id") == item_id for row in past_registry.get("stale_review_after_sample", []) if isinstance(row, dict))
        and any(row.get("id") == item_id for row in future_registry.get("stale_review_after_sample", []) if isinstance(row, dict))
        and parsed.get("final_gate", {}).get("today") == "2026-06-01"
        and parsed.get("final_gate", {}).get("checks", {}).get("knowledge_check", {}).get("status") == "pass",
        "review-after-as-of-deterministic",
        "--as-of fixes review_after warning semantics for check/status/final-gate",
        {
            "parse_errors": parse_errors,
            "past_check_exit": past_check["exit_code"],
            "future_check_exit": future_check["exit_code"],
            "past_status_exit": past_status["exit_code"],
            "future_status_exit": future_status["exit_code"],
            "final_gate_exit": final_result["exit_code"],
            "past_check_today": parsed.get("past_check", {}).get("today"),
            "past_status_today": parsed.get("past_status", {}).get("today"),
            "past_status_final_gate_command": parsed.get("past_status", {}).get("final_gate_command"),
            "final_gate_today": parsed.get("final_gate", {}).get("today"),
            "future_warning_sample": parsed.get("future_check", {}).get("warnings", [])[:5],
            "past_stale_count": past_registry.get("stale_review_after_count"),
            "future_stale_count": future_registry.get("stale_review_after_count"),
        },
        repo,
    )

def test_stale_review_after_warning_surface():
    repo = copy_repo("stale-review-after")
    item_id = "knowledge-hub-final-maintenance-closure-20260620"
    path = repo / "registry" / "items.jsonl"
    lines = path.read_text().splitlines()
    updated_lines = []
    mutated = False
    for line in lines:
        if not line.strip():
            updated_lines.append(line)
            continue
        row = json.loads(line)
        if row.get("id") == item_id:
            row["review_after"] = "2026-01-01"
            row["status"] = "reviewing"
            mutated = True
            updated_lines.append(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
        else:
            updated_lines.append(line)
    if not mutated:
        expect(False, "stale-review-after-warning-surface", "stale review_after is surfaced as warning and status action", {"setup_error": f"missing {item_id}"}, repo)
        return
    path.write_text("\n".join(updated_lines) + "\n")

    check_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    status_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-status.sh", "--json"])
    check_payload = {}
    status_payload = {}
    parse_errors = {}
    try:
        check_payload = json.loads(check_result["stdout"])
    except Exception as exc:
        parse_errors["knowledge_check"] = str(exc)
    try:
        status_payload = json.loads(status_result["stdout"])
    except Exception as exc:
        parse_errors["knowledge_status"] = str(exc)
    warnings_text = "\n".join(check_payload.get("warnings", []))
    registry = status_payload.get("registry", {}) if isinstance(status_payload.get("registry"), dict) else {}
    stale_sample = registry.get("stale_review_after_sample", [])
    next_actions_text = "\n".join(status_payload.get("next_actions_zh", []))
    expect(
        not parse_errors
        and check_result["exit_code"] == 0
        and check_payload.get("status") == "pass"
        and item_id in warnings_text
        and "review_after is stale" in warnings_text
        and status_result["exit_code"] == 0
        and registry.get("stale_review_after_count", 0) >= 1
        and any(row.get("id") == item_id for row in stale_sample if isinstance(row, dict))
        and "review_after" in next_actions_text
        and "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date" in next_actions_text,
        "stale-review-after-warning-surface",
        "stale review_after is warning/status surface, not a blocking check failure",
        {
            "parse_errors": parse_errors,
            "knowledge_check_exit": check_result["exit_code"],
            "knowledge_check_status": check_payload.get("status"),
            "warning_count": len(check_payload.get("warnings", [])),
            "warning_sample": check_payload.get("warnings", [])[:5],
            "knowledge_status_exit": status_result["exit_code"],
            "status": status_payload.get("status"),
            "stale_review_after_count": registry.get("stale_review_after_count"),
            "stale_sample": stale_sample[:3] if isinstance(stale_sample, list) else stale_sample,
            "next_actions_sample": status_payload.get("next_actions_zh", [])[:5],
        },
        repo,
    )

def test_source_review_after_stale_surface():
    repo = copy_repo("source-review-after-stale")
    source_id = "pcr02-project-tools"
    path = repo / "registry" / "sources.json"
    try:
        sources_doc = json.loads(path.read_text())
        mutated = False
        for source in sources_doc.get("sources", []):
            if source.get("id") == source_id:
                source["review_after"] = "2026-01-01"
                mutated = True
                break
        path.write_text(json.dumps(sources_doc, ensure_ascii=False, indent=2) + "\n")
        setup_error = "" if mutated else f"missing {source_id}"
    except Exception as exc:
        setup_error = str(exc)
    if setup_error:
        expect(False, "source-review-after-stale-surface", "stale source review_after is surfaced as warning and status action", {"setup_error": setup_error}, repo)
        return

    check_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics"])
    status_result = run_cmd(repo, ["rtk", "bash", "tools/knowledge-status.sh", "--json"])
    check_payload = {}
    status_payload = {}
    parse_errors = {}
    try:
        check_payload = json.loads(check_result["stdout"])
    except Exception as exc:
        parse_errors["knowledge_check"] = str(exc)
    try:
        status_payload = json.loads(status_result["stdout"])
    except Exception as exc:
        parse_errors["knowledge_status"] = str(exc)
    warnings_text = "\n".join(check_payload.get("warnings", []))
    source_check_health = check_payload.get("source_check_health", {}) if isinstance(check_payload.get("source_check_health"), dict) else {}
    sources_status = status_payload.get("sources", {}) if isinstance(status_payload.get("sources"), dict) else {}
    stale_sample = sources_status.get("stale_review_after_sample", [])
    next_actions_text = "\n".join(status_payload.get("next_actions_zh", []))
    expect(
        not parse_errors
        and check_result["exit_code"] == 0
        and check_payload.get("status") == "pass"
        and f"sources:{source_id}" in warnings_text
        and "review_after is stale" in warnings_text
        and source_id in source_check_health.get("stale_review_after_ids", [])
        and status_result["exit_code"] == 0
        and sources_status.get("stale_review_after_count", 0) >= 1
        and any(row.get("id") == source_id for row in stale_sample if isinstance(row, dict))
        and sources_status.get("review_after_command") == "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source"
        and "registered source" in next_actions_text
        and "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source" in next_actions_text,
        "source-review-after-stale-surface",
        "stale source review_after is warning/status surface, not a blocking check failure",
        {
            "parse_errors": parse_errors,
            "knowledge_check_exit": check_result["exit_code"],
            "knowledge_check_status": check_payload.get("status"),
            "warning_sample": check_payload.get("warnings", [])[:5],
            "source_check_health": source_check_health,
            "knowledge_status_exit": status_result["exit_code"],
            "sources_status": sources_status,
            "next_actions_sample": status_payload.get("next_actions_zh", [])[:8],
        },
        repo,
    )

def test_source_manual_entry_guide():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--source",
            "--source-id",
            "example-source",
            "--source-path",
            "/tmp/example",
            "--role",
            "project-current-docs-source",
            "--authority",
            "legacy-project-current-docs",
            "--write-policy",
            "read-only-unless-explicitly-approved",
            "--no-check-reason",
            "classify-first pending source coverage",
        ],
    )
    required_fragments = [
        "Knowledge Hub Source 登记向导",
        "registry/sources.json object",
        "indexes/by-source.md 主表行",
        "source coverage JSONL row",
        '"source_id":"example-source"',
        '"no_check_reason":"classify-first pending source coverage"',
        '"migration_strategy":"classify-first"',
        '"final_disposition":"owner-gated-pending-decision"',
        "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in result["stdout"]]
    today_compact = today.strftime("%Y%m%d")
    review_after_matches_today = f'"review_after":"{today.isoformat()}"' in result["stdout"]
    expect(
        result["exit_code"] == 0
        and not missing_fragments
        and f'"id":"SCC-{today_compact}-example-source"' in result["stdout"]
        and not review_after_matches_today,
        "source-manual-entry-guide",
        "source manual entry guide prints registry, index and coverage drafts",
        {
            "exit_code": result["exit_code"],
            "missing_fragments": missing_fragments,
            "today_compact": today_compact,
            "review_after_matches_today": review_after_matches_today,
            "stdout_sample": result["stdout"][:1400],
        },
    )

def test_source_manual_entry_enum_guide():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--source",
            "--source-id",
            "example-source-enum",
            "--source-path",
            "/tmp/example-enum",
            "--role",
            "project-current-docs-source",
            "--authority",
            "legacy-project-current-docs",
            "--write-policy",
            "read-only-unless-explicitly-approved",
            "--no-check-reason",
            "classify-first pending source coverage",
        ],
    )
    invalid = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--source",
            "--source-id",
            "bad-source-enum",
            "--source-path",
            "/tmp/bad-enum",
            "--role",
            "bad-role",
            "--authority",
            "legacy-project-current-docs",
            "--write-policy",
            "read-only-unless-explicitly-approved",
            "--no-check-reason",
            "classify-first pending source coverage",
        ],
    )
    required_fragments = [
        "## 枚举速查",
        "role: team-knowledge-source",
        "authority: legacy-team-ssot",
        "write_policy: do-not-write-through-knowledge-hub",
        "final_disposition 常用值",
        "脚本会对已传入的 role、authority、status 和 write_policy 做预校验",
    ]
    missing_fragments = [fragment for fragment in required_fragments if fragment not in result["stdout"]]
    expect(
        result["exit_code"] == 0
        and not missing_fragments
        and invalid["exit_code"] != 0
        and "source role value is not allowed" in invalid["stderr"],
        "source-manual-entry-enum-guide",
        "source manual entry guide prints source enum quick reference and rejects invalid provided enums",
        {
            "exit_code": result["exit_code"],
            "missing_fragments": missing_fragments,
            "invalid_exit_code": invalid["exit_code"],
            "invalid_stderr": invalid["stderr"][:500],
            "stdout_sample": result["stdout"][:1800],
        },
    )

def test_source_manual_entry_guide_check_command():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--source",
            "--source-id",
            "example-source-check",
            "--source-path",
            "/tmp/example-check",
            "--role",
            "project-current-docs-source",
            "--authority",
            "legacy-project-current-docs",
            "--write-policy",
            "read-only-unless-explicitly-approved",
            "--check",
            "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run",
        ],
    )
    registry_object_has_check = '"final_disposition":"owner-gated-pending-decision","check":"rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run"}' in result["stdout"]
    coverage_row_has_check = '"checked_at":"' in result["stdout"] and '"check":"rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run","source_identity"' in result["stdout"]
    json_no_check_reason_absent = '"no_check_reason":' not in result["stdout"]
    expect(
        result["exit_code"] == 0
        and registry_object_has_check
        and coverage_row_has_check
        and json_no_check_reason_absent
        and '"source_id":"example-source-check"' in result["stdout"]
        and "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source" in result["stdout"],
        "source-manual-entry-guide-check-command",
        "source manual entry guide uses check fields consistently for registry and coverage drafts",
        {
            "exit_code": result["exit_code"],
            "registry_object_has_check": registry_object_has_check,
            "coverage_row_has_check": coverage_row_has_check,
            "json_no_check_reason_absent": json_no_check_reason_absent,
            "stdout_sample": result["stdout"][:1600],
        },
    )

def test_source_manual_entry_status_coverage_sync():
    retired_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--source",
            "--source-id",
            "example-source-retired",
            "--source-path",
            "/tmp/example-retired",
            "--role",
            "project-current-docs-source",
            "--authority",
            "legacy-project-current-docs",
            "--write-policy",
            "read-only-unless-explicitly-approved",
            "--source-status",
            "retired",
            "--no-check-reason",
            "classify-first pending source coverage",
        ],
    )
    deprecated_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--source",
            "--source-id",
            "example-source-deprecated",
            "--source-path",
            "/tmp/example-deprecated",
            "--role",
            "project-current-docs-source",
            "--authority",
            "legacy-project-current-docs",
            "--write-policy",
            "read-only-unless-explicitly-approved",
            "--source-status",
            "deprecated",
            "--no-check-reason",
            "classify-first pending source coverage",
        ],
    )
    expect(
        retired_result["exit_code"] == 0
        and deprecated_result["exit_code"] == 0
        and '"status":"retired"' in retired_result["stdout"]
        and '"status":"retired-pending-classification"' in retired_result["stdout"]
        and '"status":"registered-pending-classification"' not in retired_result["stdout"]
        and '"status":"deprecated"' in deprecated_result["stdout"]
        and '"status":"deprecated-pending-classification"' in deprecated_result["stdout"],
        "source-manual-entry-status-coverage-sync",
        "source manual entry coverage row follows provided source status",
        {
            "retired_exit_code": retired_result["exit_code"],
            "deprecated_exit_code": deprecated_result["exit_code"],
            "retired_stdout_sample": retired_result["stdout"][:1800],
            "deprecated_stdout_sample": deprecated_result["stdout"][:1800],
        },
    )

def test_source_manual_entry_unknown_owner_warning():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--source",
            "--source-id",
            "example-source-owner-warning",
            "--source-path",
            "/tmp/example-owner-warning",
            "--role",
            "project-current-docs-source",
            "--authority",
            "legacy-project-current-docs",
            "--write-policy",
            "read-only-unless-explicitly-approved",
            "--check",
            "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run",
            "--owner",
            "unknown-source-owner",
        ],
    )
    expect(
        result["exit_code"] == 0
        and "- owner_registry_status: unknown-owner" in result["stdout"]
        and "owner_warning_zh" in result["stdout"]
        and "registry/owners.json" in result["stdout"]
        and '"owner":"unknown-source-owner"' in result["stdout"],
        "source-manual-entry-unknown-owner-warning",
        "source manual entry guide warns when source registry owner is not registered",
        {
            "exit_code": result["exit_code"],
            "stdout_sample": result["stdout"][:1600],
            "stderr_sample": result["stderr"][:500],
        },
    )

def test_source_manual_entry_requires_check_or_reason():
    common_args = [
        "rtk",
        "bash",
        "tools/knowledge-new.sh",
        "--source",
        "--source-id",
        "example-source-required",
        "--source-path",
        "/tmp/example-required",
        "--role",
        "project-current-docs-source",
        "--authority",
        "legacy-project-current-docs",
        "--write-policy",
        "read-only-unless-explicitly-approved",
    ]
    missing = run_cmd(root, common_args)
    conflict = run_cmd(
        root,
        common_args
        + [
            "--check",
            "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run",
            "--no-check-reason",
            "classify-first pending source coverage",
        ],
    )
    expect(
        missing["exit_code"] != 0
        and conflict["exit_code"] != 0
        and "requires either --check" in missing["stderr"]
        and "cannot combine --check with --no-check-reason" in conflict["stderr"],
        "source-manual-entry-requires-check-or-reason",
        "source manual entry guide requires exactly one check or no-check reason",
        {
            "missing_exit_code": missing["exit_code"],
            "conflict_exit_code": conflict["exit_code"],
            "missing_stderr": missing["stderr"][:500],
            "conflict_stderr": conflict["stderr"][:500],
        },
    )

def test_source_manual_entry_docs_check_preferred():
    readme_path = root / "README.md"
    tools_readme_path = root / "tools" / "README.md"
    help_result = run_cmd(root, ["rtk", "bash", "tools/knowledge-new.sh", "--help"])
    try:
        readme = readme_path.read_text()
        tools_readme = tools_readme_path.read_text()
        read_error = ""
    except Exception as exc:
        readme = ""
        tools_readme = ""
        read_error = str(exc)
    required_fragments = [
        '--check "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"',
        "--no-check-reason",
        "要求 `--check` 或 `--no-check-reason` 二选一",
        "优先使用稳定只读",
        "registry source object 和 source coverage JSONL row 草稿都应记录 `check`",
        "不再补 JSON 形式的 `no_check_reason`",
    ]
    readme_missing = [fragment for fragment in required_fragments if fragment not in readme]
    tools_readme_missing = [fragment for fragment in required_fragments if fragment not in tools_readme]
    help_has_check_example = (
        help_result["exit_code"] == 0
        and '--check "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"' in help_result["stdout"]
        and "--no-check-reason" in help_result["stdout"]
    )
    expect(
        not read_error
        and not readme_missing
        and not tools_readme_missing
        and help_has_check_example,
        "source-manual-entry-docs-check-preferred",
        "source manual entry docs prefer check commands and preserve no-check fallback",
        {
            "read_error": read_error,
            "readme_missing": readme_missing,
            "tools_readme_missing": tools_readme_missing,
            "help_exit_code": help_result["exit_code"],
            "help_has_check_example": help_has_check_example,
            "help_stdout_sample": help_result["stdout"][:1000],
        },
    )

def test_source_manual_entry_role_aware_recommendations():
    agent_config_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--source",
            "--source-id",
            "example-agent-config-source",
            "--source-path",
            "/tmp/example-agent-config",
            "--role",
            "project-agent-config-source",
            "--authority",
            "legacy-project-agent-config",
            "--write-policy",
            "do-not-write-through-knowledge-hub",
            "--check",
            "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run",
        ],
    )
    auxiliary_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--source",
            "--source-id",
            "example-aux-memory-source",
            "--source-path",
            "/tmp/example-aux-memory",
            "--role",
            "auxiliary-memory-source",
            "--authority",
            "auxiliary-recall-only",
            "--write-policy",
            "read-only-unless-explicitly-approved",
            "--no-check-reason",
            "auxiliary recall source without stable check",
        ],
    )
    no_check_current_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-new.sh",
            "--source",
            "--source-id",
            "example-current-no-check-source",
            "--source-path",
            "/tmp/example-current-no-check",
            "--role",
            "project-current-docs-source",
            "--authority",
            "legacy-project-current-docs",
            "--write-policy",
            "read-only-unless-explicitly-approved",
            "--no-check-reason",
            "classify-first pending source coverage",
        ],
    )
    expect(
        agent_config_result["exit_code"] == 0
        and auxiliary_result["exit_code"] == 0
        and no_check_current_result["exit_code"] == 0
        and "recommended_final_disposition: artifact-ref-registered" in agent_config_result["stdout"]
        and "recommended_migration_strategy: artifact-ref" in agent_config_result["stdout"]
        and '"final_disposition":"owner-gated-pending-decision"' in agent_config_result["stdout"]
        and "recommendation_scope_zh: 以上只是人工填写提示，不代表 owner decision，不关闭 owner gate" in agent_config_result["stdout"]
        and "recommended_final_disposition: auxiliary-recall-only" in auxiliary_result["stdout"]
        and "不写 memory" in auxiliary_result["stdout"]
        and "recommended_final_disposition: owner-gated-pending-decision" in no_check_current_result["stdout"]
        and "没有稳定 check" in no_check_current_result["stdout"]
        and '"final_disposition":"owner-gated-pending-decision"' in no_check_current_result["stdout"],
        "source-manual-entry-role-aware-recommendations",
        "source manual entry guide gives role-aware recommendations without replacing conservative copyable JSON",
        {
            "agent_config_exit_code": agent_config_result["exit_code"],
            "auxiliary_exit_code": auxiliary_result["exit_code"],
            "no_check_current_exit_code": no_check_current_result["exit_code"],
            "agent_config_stdout_sample": agent_config_result["stdout"][:1800],
            "auxiliary_stdout_sample": auxiliary_result["stdout"][:1800],
            "no_check_current_stdout_sample": no_check_current_result["stdout"][:1800],
        },
    )

def test_knowledge_search_structured_filters():
    active_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-search.sh",
            "Knowledge Hub",
            "--owner",
            "leiwenjun",
            "--status",
            "active",
            "--json",
            "--limit",
            "5",
        ],
    )
    pcr02_result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-search.sh",
            "diag",
            "--source-id",
            "pcr02-project-docs",
            "--json",
            "--limit",
            "5",
        ],
    )
    parsed_active = {}
    parsed_pcr02 = {}
    parse_errors = {}
    try:
        parsed_active = json.loads(active_result["stdout"])
    except Exception as exc:
        parse_errors["active"] = str(exc)
    try:
        parsed_pcr02 = json.loads(pcr02_result["stdout"])
    except Exception as exc:
        parse_errors["pcr02"] = str(exc)
    active_results = parsed_active.get("results", []) if isinstance(parsed_active, dict) else []
    pcr02_results = parsed_pcr02.get("results", []) if isinstance(parsed_pcr02, dict) else []
    expect(
        not parse_errors
        and active_result["exit_code"] == 0
        and pcr02_result["exit_code"] == 0
        and parsed_active.get("filters", {}).get("owner") == ["leiwenjun"]
        and parsed_active.get("filters", {}).get("status") == ["active"]
        and active_results
        and all(row.get("owner") == "leiwenjun" for row in active_results)
        and all(row.get("status") == "active" for row in active_results)
        and all(row.get("item_id") for row in active_results)
        and parsed_pcr02.get("filters", {}).get("source_id") == ["pcr02-project-docs"]
        and pcr02_results
        and all(row.get("source_id") == "pcr02-project-docs" for row in pcr02_results)
        and all(row.get("item_id") for row in pcr02_results),
        "knowledge-search-structured-filters",
        "knowledge search supports registry-backed structured filters",
        {
            "parse_errors": parse_errors,
            "active_exit_code": active_result["exit_code"],
            "pcr02_exit_code": pcr02_result["exit_code"],
            "active_count": parsed_active.get("count"),
            "pcr02_count": parsed_pcr02.get("count"),
            "active_first": active_results[0] if active_results else {},
            "pcr02_first": pcr02_results[0] if pcr02_results else {},
        },
    )

def test_knowledge_search_structured_filters_exclude_unregistered_raw():
    repo = copy_repo("knowledge-search-structured-filter-excludes-unregistered-raw")
    raw_path = repo / "domains" / "projects" / "pcr02" / "current" / "unregistered-diag-raw-fixture.md"
    raw_path.write_text(
        "# Unregistered diag raw fixture\n\n"
        "diag owner decision source_id pcr02-project-docs raw handoff text.\n"
        "This file is intentionally not present in registry/items.jsonl.\n"
    )
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-search.sh",
            "diag",
            "--source",
            "knowledge-hub",
            "--source-id",
            "pcr02-project-docs",
            "--json",
            "--limit",
            "50",
        ],
    )
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    results = parsed.get("results", []) if isinstance(parsed, dict) else []
    fixture_path = str(raw_path)
    expect(
        not parse_error
        and result["exit_code"] == 0
        and results
        and all(row.get("item_id") for row in results)
        and all(row.get("source_id") == "pcr02-project-docs" for row in results)
        and not any(row.get("path") == fixture_path for row in results),
        "knowledge-search-structured-filters-exclude-unregistered-raw",
        "structured source-id search excludes unregistered raw files with matching text",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "count": parsed.get("count") if isinstance(parsed, dict) else None,
            "fixture_path": fixture_path,
            "paths": [row.get("path") for row in results[:10]],
            "first_result": results[0] if results else {},
        },
        repo,
    )

def test_knowledge_search_kind_alias_filters():
    result = run_cmd(
        root,
        [
            "rtk",
            "bash",
            "tools/knowledge-search.sh",
            "prog_tool",
            "--kind",
            "validation-report",
            "--json",
            "--limit",
            "5",
        ],
    )
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    results = parsed.get("results", []) if isinstance(parsed, dict) else []
    expect(
        not parse_error
        and result["exit_code"] == 0
        and parsed.get("filters", {}).get("kind") == ["validation-report"]
        and parsed.get("filters", {}).get("kind_normalized") == ["validation"]
        and results
        and all(row.get("kind") == "validation" for row in results),
        "knowledge-search-kind-alias-filters",
        "knowledge search normalizes template kind aliases to registry kind filters",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "filters": parsed.get("filters") if isinstance(parsed, dict) else {},
            "count": parsed.get("count") if isinstance(parsed, dict) else None,
            "first_result": results[0] if results else {},
        },
    )

def test_knowledge_search_registry_metadata_fallback():
    repo = copy_repo("knowledge-search-registry-metadata-fallback")
    token = "metadata-only-search-fixture-20260622"
    fixture_item = {
        "id": token,
        "title": "Metadata only search fixture",
        "kind": "audit",
        "domain": "governance",
        "path": "README.md",
        "status": "reviewing",
        "owner": "leiwenjun",
        "source": {"type": "generated", "source_id": "metadata-only-fixture-source", "from": "temporary regression fixture"},
        "tags": ["metadata-only-fixture", "knowledge-search", "governance"],
        "summary_zh": "只存在于 registry metadata 的搜索回归关键词，正文不包含该 token。",
        "review_after": "2026-09-22",
        "review_status": "metadata-search-fallback-applied",
        "created_at": "2026-06-22",
        "updated_at": "2026-06-22",
    }
    with (repo / "registry" / "items.jsonl").open("a") as fh:
        fh.write(json.dumps(fixture_item, ensure_ascii=False, separators=(",", ":")) + "\n")
    result = run_cmd(
        repo,
        [
            "rtk",
            "bash",
            "tools/knowledge-search.sh",
            token,
            "--source-id",
            "metadata-only-fixture-source",
            "--json",
            "--limit",
            "5",
        ],
    )
    parsed = {}
    parse_error = ""
    try:
        parsed = json.loads(result["stdout"])
    except Exception as exc:
        parse_error = str(exc)
    results = parsed.get("results", []) if isinstance(parsed, dict) else []
    first = results[0] if results else {}
    expect(
        not parse_error
        and result["exit_code"] == 0
        and parsed.get("count") == 1
        and first.get("item_id") == token
        and first.get("match") == "registry-metadata"
        and first.get("source_id") == "metadata-only-fixture-source",
        "knowledge-search-registry-metadata-fallback",
        "knowledge search returns registry metadata-only matches with structured filters",
        {
            "exit_code": result["exit_code"],
            "parse_error": parse_error,
            "count": parsed.get("count") if isinstance(parsed, dict) else None,
            "first_result": first,
            "stdout_sample": result["stdout"][:1000],
            "stderr_sample": result["stderr"][:1000],
        },
        repo,
    )

def test_knowledge_search_invalid_filters():
    bad_status = run_cmd(root, ["rtk", "bash", "tools/knowledge-search.sh", "Knowledge Hub", "--status", "not-a-status"])
    bad_kind = run_cmd(root, ["rtk", "bash", "tools/knowledge-search.sh", "Knowledge Hub", "--kind", "not-a-kind"])
    bad_limit = run_cmd(root, ["rtk", "bash", "tools/knowledge-search.sh", "Knowledge Hub", "--limit", "0"])
    expect(
        bad_status["exit_code"] != 0
        and bad_kind["exit_code"] != 0
        and bad_limit["exit_code"] != 0
        and "invalid --status value" in bad_status["stderr"]
        and "invalid --kind value" in bad_kind["stderr"]
        and "--limit must be >= 1" in bad_limit["stderr"],
        "knowledge-search-invalid-filters",
        "knowledge search rejects invalid enum filters and non-positive limits",
        {
            "bad_status_exit_code": bad_status["exit_code"],
            "bad_kind_exit_code": bad_kind["exit_code"],
            "bad_limit_exit_code": bad_limit["exit_code"],
            "bad_status_stderr": bad_status["stderr"][:500],
            "bad_kind_stderr": bad_kind["stderr"][:500],
            "bad_limit_stderr": bad_limit["stderr"][:500],
        },
    )

def test_regression_manifest_coverage():
    manifest_path = root / "artifacts" / "manifests" / "knowledge-hub-governance-regression-helper-20260619.md"
    try:
        manifest_text = manifest_path.read_text()
    except Exception as exc:
        manifest_text = ""
        read_error = str(exc)
    else:
        read_error = ""
    required_ids = [
        "baseline-knowledge-check",
        "governance-goal-path-allowed",
        "pcr02-level2-source-coverage",
        "pcr02-level2-boundary-manifests",
        "boundary-health-internal-evidence",
        "status-wrong-bucket",
        "status-noncanonical-only",
        "owner-partial-resolved",
        "owner-single-form",
        "owner-forms-text-jsonl-output",
        "owner-forms-jsonl-single-output",
        "owner-forms-jsonl-all-open-output",
        "owner-forms-jsonl-conflict-json-mode",
        "owner-checklist-context",
        "owner-form-context",
        "owner-source-identity-context",
        "owner-prefill-candidates-manual-fields",
        "owner-evidence-readiness",
        "owner-inbox-contract",
        "owner-summary-all-open",
        "owner-summary-by-owner",
        "owner-handoff-packet-json",
        "owner-dispatch-source-scope-isolation",
        "manifest-regression-count-capture-qualifier",
        "manifest-profile-boundary-advisory",
        "owner-next-open-focus",
        "status-next-owner-gate",
        "status-owner-ready-source-no-registry-fallback",
        "final-gate-maintenance-entry-wording-no-section-drift",
        "status-text-owner-summary-commands",
        "status-owner-gates-exit-code-blocker",
        "final-gate-owner-review-blocker",
        "final-gate-skip-regression-blocker",
        "final-gate-empty-child-json-blocker",
        "final-gate-default-regression-path",
        "final-gate-source-final-state-field-gap",
        "final-gate-strict-status-nonowner-blocker",
        "final-gap-readability-positive-contracts",
        "owner-landing-plan-project-index",
        "owner-validate-forms-partial-coverage-warning",
        "owner-archive-only-target-path-compatibility",
        "owner-archive-only-rejects-non-archive-target",
        "owner-landing-plan-requires-owner-ready-missing",
        "owner-landing-plan-requires-owner-ready-invalid",
        "owner-landing-plan-requires-owner-ready-repo-relative-command",
        "owner-landing-plan-requires-owner-ready-duplicate",
        "owner-form-target-decision-candidate-gate",
        "owner-form-decision-target-pair-reference-only-project-path",
        "owner-form-decision-target-pair-no-migration-project-path",
        "owner-form-decision-target-pair-project-rule-reference-only",
        "owner-form-decision-target-pair-positive-reference-only",
        "owner-form-decision-target-pair-positive-no-migration",
        "owner-form-routing-owner-reviewed-by-gate",
        "owner-form-must-not-tamper-gate",
        "owner-form-allowed-decisions-tamper-gate",
        "owner-form-target-candidates-tamper-gate",
        "owner-form-source-identity-mismatch",
        "manual-entry-project-index-hint",
        "manual-entry-registered-source-binding",
        "manual-entry-project-derived-from-domain",
        "manual-entry-default-dates",
        "manual-entry-owner-override",
        "manual-entry-owner-registry-and-personal-defaults",
        "manual-entry-docs-owner-option",
        "manual-entry-offline-docs",
        "readme-offline-shortest-paths",
        "owner-decision-draft-leak-warning",
        "manual-entry-offline-package-consistency",
        "manual-entry-validation-diagnostics-default",
        "manual-entry-readability-fields",
        "manual-entry-archive-default-status",
        "offline-validation-template-placeholders",
        "governance-audit-readability-gate",
        "ai-generated-item-provenance-gate",
        "migration-notes-zh-gate",
        "manual-entry-migration-conditional-guide",
        "manual-entry-template-selection",
        "templates-required-sections",
        "index-readme-maintenance-coverage",
        "by-topic-first-screen-readability-contract",
        "review-queue-json-contract",
        "final-proof-artifact-discoverability",
        "final-proof-decision-index-recovery-contract",
        "final-proof-artifact-as-of-date-selector",
        "final-proof-artifacts-stable-alias",
        "index-plan-extended-sections",
        "manifest-latest-filename-date-only",
        "manifest-jsonl-profile-gate",
        "template-readability-field-gate",
        "index-plan-topic-schema-health",
        "index-plan-decision-registry-health",
        "index-decision-registry-subsection-gate",
        "index-topic-zero-bucket-allowed",
        "status-source-governance-summary",
        "source-check-health-contract",
        "source-check-report-only-helper",
        "source-check-rejects-unsafe-runtime-command",
        "final-gate-source-check-runtime-failed-blocker",
        "review-after-near-due-json-contract",
        "automation-report-only-safety-gate",
        "source-coverage-date-filename-selection",
        "source-coverage-duplicate-source-id-warning",
        "review-after-as-of-deterministic",
        "stale-review-after-warning-surface",
        "source-review-after-stale-surface",
        "source-manual-entry-guide",
        "source-manual-entry-enum-guide",
        "source-manual-entry-guide-check-command",
        "source-manual-entry-status-coverage-sync",
        "source-manual-entry-unknown-owner-warning",
        "source-manual-entry-requires-check-or-reason",
        "source-manual-entry-docs-check-preferred",
        "source-manual-entry-role-aware-recommendations",
        "knowledge-search-structured-filters",
        "knowledge-search-structured-filters-exclude-unregistered-raw",
        "knowledge-search-kind-alias-filters",
        "knowledge-search-registry-metadata-fallback",
        "knowledge-search-invalid-filters",
        "stable-governance-command-examples",
        "regression-manifest-coverage",
    ]
    def parse_coverage_rows(text):
        rows = {}
        duplicate_rows = []
        in_table = False
        for line in text.splitlines():
            if line.strip() == "## 覆盖范围":
                in_table = True
                continue
            if in_table and line.startswith("## "):
                break
            if not in_table or not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3 or cells[0] in {"ID", "---"} or set(cells[0]) <= {"-"}:
                continue
            row_id = cells[0]
            if row_id in rows:
                duplicate_rows.append(row_id)
            rows[row_id] = {
                "scenario": cells[1] if len(cells) > 1 else "",
                "expected": cells[2] if len(cells) > 2 else "",
            }
        return rows, sorted(set(duplicate_rows))

    actual_ids = [result.get("id", "") for result in results] + ["regression-manifest-coverage"]
    coverage_rows, duplicate_manifest_rows = parse_coverage_rows(manifest_text)
    missing_ids = [test_id for test_id in required_ids if test_id not in manifest_text]
    missing_from_required = [test_id for test_id in actual_ids if test_id not in required_ids]
    missing_table_rows = [test_id for test_id in actual_ids if test_id not in coverage_rows]
    table_rows_without_scenario = [
        test_id for test_id in actual_ids
        if test_id in coverage_rows and not coverage_rows[test_id].get("scenario", "")
    ]
    table_rows_without_expected = [
        test_id for test_id in actual_ids
        if test_id in coverage_rows and not coverage_rows[test_id].get("expected", "")
    ]
    duplicate_actual_ids = sorted({test_id for test_id in actual_ids if actual_ids.count(test_id) > 1})
    expected_count_text = f"{len(actual_ids)} 个回归场景"
    expect(
        not read_error
        and not missing_ids
        and not missing_from_required
        and not missing_table_rows
        and not duplicate_manifest_rows
        and not table_rows_without_scenario
        and not table_rows_without_expected
        and not duplicate_actual_ids
        and expected_count_text in manifest_text,
        "regression-manifest-coverage",
        "regression helper manifest covers current regression ids with structured table rows",
        {
            "manifest": str(manifest_path.relative_to(root)),
            "read_error": read_error,
            "missing_ids": missing_ids,
            "missing_from_required": missing_from_required,
            "missing_table_rows": missing_table_rows,
            "duplicate_manifest_rows": duplicate_manifest_rows,
            "table_rows_without_scenario": table_rows_without_scenario,
            "table_rows_without_expected": table_rows_without_expected,
            "duplicate_actual_ids": duplicate_actual_ids,
            "actual_count": len(actual_ids),
            "required_count": len(required_ids),
            "manifest_table_count": len(coverage_rows),
            "expected_count_text": expected_count_text,
        },
    )

for test_fn in [
    test_baseline,
    test_governance_goal_path_allowed,
    test_pcr02_level2_source_coverage,
    test_pcr02_level2_boundary_manifests,
    test_boundary_health_internal_evidence,
    test_status_wrong_bucket,
    test_status_noncanonical_only,
    test_owner_partial_resolved,
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
    test_final_gate_skip_regression_blocker,
    test_final_gate_empty_child_json_blocker,
    test_final_gate_default_regression_path,
    test_final_gate_source_final_state_field_gap,
    test_final_gate_strict_status_nonowner_blocker,
    test_final_gap_readability_positive_contracts,
    test_owner_landing_plan_project_index,
    test_owner_validate_forms_partial_coverage_warning,
    test_owner_archive_only_target_path_compatibility,
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
    test_owner_decision_draft_leak_warning,
    test_manual_entry_offline_package_consistency,
    test_manual_entry_validation_diagnostics_default,
    test_manual_entry_readability_fields,
    test_manual_entry_archive_default_status,
    test_offline_validation_template_placeholders,
    test_governance_audit_readability_gate,
    test_ai_generated_item_provenance_gate,
    test_migration_notes_zh_gate,
    test_manual_entry_migration_conditional_guide,
    test_manual_entry_template_selection,
    test_templates_required_sections,
    test_index_readme_maintenance_coverage,
    test_by_topic_first_screen_readability_contract,
    test_review_queue_json_contract,
    test_final_proof_artifact_discoverability,
    test_final_proof_decision_index_recovery_contract,
    test_final_proof_artifact_as_of_date_selector,
    test_final_proof_artifacts_stable_alias,
    test_index_plan_extended_sections,
    test_manifest_latest_filename_date_only,
    test_manifest_jsonl_profile_gate,
    test_template_readability_field_gate,
    test_index_plan_topic_schema_health,
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
    test_knowledge_search_registry_metadata_fallback,
    test_knowledge_search_invalid_filters,
    test_stable_governance_command_examples,
    test_regression_manifest_coverage,
]:
    run_test(test_fn)

status = "pass" if all(result["status"] == "pass" for result in results) else "fail"
output = {
    "status": status,
    "root": str(root),
    "read_only": True,
    "writes_real_repo": False,
    "today": today.isoformat(),
    "as_of_source": today_source,
    "kept_temp": args.keep_temp,
    "result_count": len(results),
    "results": results,
}

if args.json:
    print(json.dumps(output, ensure_ascii=False, indent=2))
else:
    print("# Knowledge Regression")
    print()
    print(f"- status: {status}")
    print(f"- results: {len(results)}")
    print(f"- writes real repo: false")
    for result in results:
        print(f"- {result['status']}: {result['id']} - {result['title']}")
        if result.get("fixture_repo"):
            print(f"  fixture: {result['fixture_repo']}")

sys.exit(0 if status == "pass" else 1)
PY
