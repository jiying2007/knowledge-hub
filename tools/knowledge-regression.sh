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
import shutil
import subprocess
import sys
import tempfile

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Run lightweight Knowledge Hub governance regression fixtures in /tmp.")
parser.add_argument("--json", action="store_true")
parser.add_argument("--keep-temp", action="store_true", help="Keep temporary fixture repositories for inspection.")
args = parser.parse_args(argv)

results = []
temp_roots = []
temp_dir = pathlib.Path(tempfile.gettempdir()).resolve()
min_tmp_free_bytes = int(os.environ.get("KNOWLEDGE_REGRESSION_MIN_TMP_FREE_BYTES", str(4 * 1024 * 1024)))

def run_cmd(repo, command):
    completed = subprocess.run(
        command,
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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
    repo = copy_repo("owner-partial-resolved")
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
    result = run_cmd(
        root,
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
    result = run_cmd(
        root,
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
    result = run_cmd(
        root,
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
            "identity_status": identity.get("identity_status"),
            "stdout_sample": result["stdout"][:1000],
            "stderr_sample": result["stderr"][:500],
        },
    )

def test_owner_forms_jsonl_all_open_output():
    result = run_cmd(
        root,
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
    result = run_cmd(
        root,
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
    result = run_cmd(
        root,
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
    result = run_cmd(
        root,
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
            "source_file_exists": identity.get("source_file_exists"),
            "source_sha256_field": first.get("source_sha256"),
            "source_size_field": first.get("source_size"),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_summary_all_open():
    result = run_cmd(
        root,
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
    first = summary_rows[0] if summary_rows else {}
    expect(
        result["exit_code"] == 0
        and parsed.get("row_count") == 7
        and parsed.get("open_count") == 7
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
        and len(summary_rows) == 7
        and first.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
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
            "row_count": parsed.get("row_count"),
            "open_count": parsed.get("open_count"),
            "summary_status": summary.get("status"),
            "summary_row_count": summary.get("row_count"),
            "owner_ready_package_coverage": summary.get("owner_ready_package_coverage"),
            "owner_ready_missing_count": summary.get("owner_ready_missing_count"),
            "owner_ready_invalid_count": summary.get("owner_ready_invalid_count"),
            "owner_ready_duplicate_count": summary.get("owner_ready_duplicate_count"),
            "identity_counts": summary.get("source_identity_counts", {}),
            "first": first,
            "has_decision_forms": "decision_forms" in parsed,
            "has_owner_checklists": "owner_checklists" in parsed,
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_summary_by_owner():
    result = run_cmd(
        root,
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
            "worksheet_ids": sorted(worksheet_ids),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_next_open_focus():
    result = run_cmd(
        root,
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
    result = run_cmd(root, ["rtk", "bash", "tools/knowledge-status.sh", "--json"])
    strict_result = run_cmd(root, ["rtk", "bash", "tools/knowledge-status.sh", "--strict", "--json"])
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
    summary_commands = parsed.get("owner_gates", {}).get("summary_commands", [])
    owner_summary_commands = parsed.get("owner_gates", {}).get("owner_summary_commands", [])
    forms_jsonl_commands = parsed.get("owner_gates", {}).get("forms_jsonl_commands", [])
    validate_forms_command_templates = parsed.get("owner_gates", {}).get("validate_forms_command_templates", [])
    landing_plan_command_templates = parsed.get("owner_gates", {}).get("landing_plan_command_templates", [])
    next_actions = parsed.get("next_actions_zh", [])
    strict_blockers = strict_parsed.get("strict_blockers", [])
    owner_blocker = next(
        (blocker for blocker in strict_blockers if blocker.get("id") == "owner-gates-open"),
        {},
    )
    expect(
        result["exit_code"] == 0
        and strict_result["exit_code"] == 1
        and parsed.get("status") == "needs-owner-review"
        and strict_parsed.get("strict") is True
        and strict_parsed.get("status") == "needs-owner-review"
        and owner_gates.get("owner_ready_package_count") == 7
        and owner_gates.get("owner_ready_missing_count") == 0
        and owner_gates.get("owner_ready_invalid_count") == 0
        and owner_gates.get("owner_ready_duplicate_count") == 0
        and owner_gates.get("owner_ready_package_coverage") == "7/7"
        and any("--summary" in str(command) for command in summary_commands)
        and any("--owner project-owner" in str(command) and "--summary" in str(command) for command in owner_summary_commands)
        and any("--forms-jsonl" in str(command) for command in forms_jsonl_commands)
        and any("--validate-forms" in str(command) and "owner-decisions.jsonl" in str(command) and "--json" in str(command) for command in validate_forms_command_templates)
        and any("--validate-forms" in str(command) and "owner-decisions.jsonl" in str(command) and "--landing-plan" in str(command) and "--json" in str(command) for command in landing_plan_command_templates)
        and next_open.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and "--next-open" in next_open.get("next_open_command", "")
        and "--checklist" in next_open.get("next_open_command", "")
        and "--forms" in next_open.get("next_open_command", "")
        and "--next-open" in next_open.get("next_open_forms_jsonl_command", "")
        and "--forms-jsonl" in next_open.get("next_open_forms_jsonl_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001" in next_open.get("focus_command", "")
        and "--checklist" in next_open.get("focus_command", "")
        and "--forms" in next_open.get("focus_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001" in next_open.get("focus_forms_jsonl_command", "")
        and "--forms-jsonl" in next_open.get("focus_forms_jsonl_command", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001" in next_open.get("focus_validate_forms_command_template", "")
        and "--validate-forms" in next_open.get("focus_validate_forms_command_template", "")
        and "owner-decisions.jsonl" in next_open.get("focus_validate_forms_command_template", "")
        and "--worksheet-id pcr02-owner-decision-worksheet-001" in next_open.get("focus_landing_plan_command_template", "")
        and "--validate-forms" in next_open.get("focus_landing_plan_command_template", "")
        and "--landing-plan" in next_open.get("focus_landing_plan_command_template", "")
        and "owner-decisions.jsonl" in next_open.get("focus_landing_plan_command_template", "")
        and any("--summary" in str(action) for action in next_actions)
        and any("--owner" in str(action) and "--summary" in str(action) for action in next_actions)
        and any("--next-open --checklist --forms" in str(action) for action in next_actions)
        and any("--next-open --forms-jsonl" in str(action) for action in next_actions)
        and any("--validate-forms" in str(action) and "owner-decisions.jsonl" in str(action) for action in next_actions)
        and any("--landing-plan" in str(action) for action in next_actions)
        and owner_blocker.get("count") == 7
        and any("--summary" in str(command) for command in owner_blocker.get("commands", []))
        and any("--owner project-owner" in str(command) and "--summary" in str(command) for command in owner_blocker.get("commands", []))
        and any("--next-open --checklist --forms" in str(command) for command in owner_blocker.get("commands", []))
        and any("--next-open --forms-jsonl" in str(command) for command in owner_blocker.get("commands", []))
        and not any("owner-decisions.jsonl" in str(command) for command in owner_blocker.get("commands", []))
        and any("--validate-forms" in str(command) and "owner-decisions.jsonl" in str(command) for command in owner_blocker.get("command_templates", []))
        and any("--landing-plan" in str(command) for command in owner_blocker.get("command_templates", [])),
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
            "worksheet_id": next_open.get("worksheet_id"),
            "summary_commands": summary_commands,
            "owner_summary_commands": owner_summary_commands,
            "forms_jsonl_commands": forms_jsonl_commands,
            "validate_forms_command_templates": validate_forms_command_templates,
            "landing_plan_command_templates": landing_plan_command_templates,
            "next_open_command": next_open.get("next_open_command", ""),
            "next_open_forms_jsonl_command": next_open.get("next_open_forms_jsonl_command", ""),
            "focus_command": next_open.get("focus_command", ""),
            "focus_forms_jsonl_command": next_open.get("focus_forms_jsonl_command", ""),
            "focus_validate_forms_command_template": next_open.get("focus_validate_forms_command_template", ""),
            "focus_landing_plan_command_template": next_open.get("focus_landing_plan_command_template", ""),
            "strict_blockers": strict_blockers,
            "next_actions_zh": next_actions,
            "stdout_sample": result["stdout"][:1000],
            "strict_stdout_sample": strict_result["stdout"][:1000],
        },
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
    result = run_cmd(root, ["rtk", "bash", "-lc", "KNOWLEDGE_FINAL_GATE_SKIP_REGRESSION=1 rtk bash tools/knowledge-final-gate.sh --json"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    checks = parsed.get("checks", {})
    blockers = parsed.get("blockers", [])
    owner_blocker = next(
        (blocker for blocker in blockers if blocker.get("id") == "owner-gates-open"),
        {},
    )
    expect(
        result["exit_code"] == 1
        and parsed.get("final_status") == "needs-owner-review"
        and checks.get("knowledge_check", {}).get("status") == "pass"
        and checks.get("knowledge_check", {}).get("exit_code") == 0
        and checks.get("knowledge_regression", {}).get("status") == "pass"
        and checks.get("knowledge_regression", {}).get("exit_code") == 0
        and checks.get("knowledge_regression", {}).get("skipped_for_self_test") is True
        and checks.get("knowledge_status_strict", {}).get("status") == "needs-owner-review"
        and checks.get("knowledge_status_strict", {}).get("exit_code") == 1
        and owner_blocker.get("count") == 7,
        "final-gate-owner-review-blocker",
        "final gate includes check, regression and strict owner blockers",
        {
            "exit_code": result["exit_code"],
            "final_status": parsed.get("final_status"),
            "checks": checks,
            "blockers": blockers,
            "stdout_sample": result["stdout"][:1200],
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
        "target_decision": "project-local-rule",
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

def test_owner_landing_plan_project_index():
    form, setup_error = make_valid_owner_decision_form(root)
    if setup_error:
        expect(False, "owner-landing-plan-project-index", "owner landing plan requires by-project index", setup_error)
        return
    temp_root = pathlib.Path(tempfile.mkdtemp(prefix="kh-regression-owner-landing-plan-"))
    temp_roots.append(temp_root)
    forms_path = temp_root / "owner-decisions.jsonl"
    forms_path.write_text(json.dumps(form, ensure_ascii=False, separators=(",", ":")) + "\n")
    result = run_cmd(
        root,
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
    required_files = parsed.get("landing_plan", {}).get("required_manual_files", [])
    owner_ready_gate = parsed.get("landing_plan", {}).get("owner_ready_gate", {})
    expect(
        result["exit_code"] == 0
        and parsed.get("landing_plan", {}).get("status") == "planned"
        and owner_ready_gate.get("status") == "pass"
        and owner_ready_gate.get("error_count") == 0
        and "indexes/by-project.md" in required_files
        and "indexes/by-status.md" in required_files,
        "owner-landing-plan-project-index",
        "owner landing plan requires by-project index",
        {
            "exit_code": result["exit_code"],
            "landing_status": parsed.get("landing_plan", {}).get("status"),
            "owner_ready_gate": owner_ready_gate,
            "required_manual_files": required_files,
            "stdout_sample": result["stdout"][:1000],
        },
    )

def run_owner_landing_ready_block_fixture(case_id, expected_status, mutate_repo):
    repo = copy_repo(f"owner-landing-plan-owner-ready-{case_id}")
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
    forms_result = run_cmd(
        root,
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
        )
        return
    form = forms[0]
    identity = form.get("observed_source_identity", {})
    for key, value in {
        "owner_decision": form.get("allowed_owner_decisions", ["project-local-rule"])[0],
        "target_decision": "project-local-rule",
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
        root,
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
        and "domains/projects/pcr02/current/runbooks/regression.md" in project_result["stdout"]
        and "indexes/by-project.md" not in governance_result["stdout"],
        "manual-entry-project-index-hint",
        "manual project entries mention by-project index only for project domains",
        {
            "project_exit_code": project_result["exit_code"],
            "governance_exit_code": governance_result["exit_code"],
            "project_has_by_project": "indexes/by-project.md" in project_result["stdout"],
            "governance_has_by_project": "indexes/by-project.md" in governance_result["stdout"],
            "project_stdout_sample": project_result["stdout"][:1200],
            "governance_stdout_sample": governance_result["stdout"][:1200],
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
    today = dt.datetime.utcnow().date().isoformat()
    expect(
        result["exit_code"] == 0
        and f'"created_at":"{today}"' in result["stdout"]
        and f'"updated_at":"{today}"' in result["stdout"]
        and f'"checked_at":"{today}"' in result["stdout"]
        and '"review_after":"<YYYY-MM-DD>"' not in result["stdout"]
        and "checked_at\":\"<YYYY-MM-DD>" not in result["stdout"],
        "manual-entry-default-dates",
        "manual entry skeleton fills default ISO dates",
        {
            "exit_code": result["exit_code"],
            "today": today,
            "has_created_at": f'"created_at":"{today}"' in result["stdout"],
            "has_updated_at": f'"updated_at":"{today}"' in result["stdout"],
            "has_checked_at": f'"checked_at":"{today}"' in result["stdout"],
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
        "owner-summary-all-open",
        "owner-summary-by-owner",
        "owner-next-open-focus",
        "status-next-owner-gate",
        "final-gate-owner-review-blocker",
        "owner-landing-plan-project-index",
        "owner-landing-plan-requires-owner-ready-missing",
        "owner-landing-plan-requires-owner-ready-invalid",
        "owner-landing-plan-requires-owner-ready-duplicate",
        "owner-form-source-identity-mismatch",
        "manual-entry-project-index-hint",
        "manual-entry-project-derived-from-domain",
        "manual-entry-default-dates",
        "manual-entry-owner-override",
        "manual-entry-docs-owner-option",
        "regression-manifest-coverage",
    ]
    missing_ids = [test_id for test_id in required_ids if test_id not in manifest_text]
    expect(
        not read_error
        and not missing_ids
        and "30 个回归场景" in manifest_text,
        "regression-manifest-coverage",
        "regression helper manifest covers current regression ids",
        {
            "manifest": str(manifest_path.relative_to(root)),
            "read_error": read_error,
            "missing_ids": missing_ids,
            "expected_count_text": "30 个回归场景",
        },
    )

for test_fn in [
    test_baseline,
    test_governance_goal_path_allowed,
    test_pcr02_level2_source_coverage,
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
    test_owner_summary_all_open,
    test_owner_summary_by_owner,
    test_owner_next_open_focus,
    test_status_next_owner_gate,
    test_final_gate_owner_review_blocker,
    test_owner_landing_plan_project_index,
    test_owner_landing_plan_requires_owner_ready_package_missing,
    test_owner_landing_plan_requires_owner_ready_package_invalid,
    test_owner_landing_plan_requires_owner_ready_package_duplicate,
    test_owner_form_source_identity_mismatch,
    test_manual_entry_project_index_hint,
    test_manual_entry_project_from_domain,
    test_manual_entry_default_dates,
    test_manual_entry_owner_override,
    test_manual_entry_docs_owner_option,
    test_regression_manifest_coverage,
]:
    run_test(test_fn)

status = "pass" if all(result["status"] == "pass" for result in results) else "fail"
output = {
    "status": status,
    "root": str(root),
    "read_only": True,
    "writes_real_repo": False,
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
