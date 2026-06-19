#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import json
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
    temp_root = pathlib.Path(tempfile.mkdtemp(prefix=f"kh-regression-{label}-"))
    temp_roots.append(temp_root)
    repo = temp_root / "repo"
    shutil.copytree(root, repo, ignore=shutil.ignore_patterns(".git"))
    return repo

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

def test_status_next_owner_gate():
    result = run_cmd(root, ["rtk", "bash", "tools/knowledge-status.sh", "--json"])
    parsed = {}
    try:
        parsed = json.loads(result["stdout"])
    except Exception:
        pass
    next_open = parsed.get("owner_gates", {}).get("next_open", {})
    expect(
        result["exit_code"] == 0
        and parsed.get("status") == "needs-owner-review"
        and next_open.get("worksheet_id") == "pcr02-owner-decision-worksheet-001"
        and "--worksheet-id pcr02-owner-decision-worksheet-001" in next_open.get("focus_command", ""),
        "status-next-owner-gate",
        "status dashboard exposes next owner gate focus command",
        {
            "exit_code": result["exit_code"],
            "status": parsed.get("status"),
            "worksheet_id": next_open.get("worksheet_id"),
            "focus_command": next_open.get("focus_command", ""),
            "stdout_sample": result["stdout"][:1000],
        },
    )

def test_owner_landing_plan_project_index():
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
            "owner-landing-plan-project-index",
            "owner landing plan requires by-project index",
            {"setup_error": "missing decision form", "stdout_sample": forms_result["stdout"][:1000]},
        )
        return
    form = forms[0]
    for key, value in {
        "owner_decision": form.get("allowed_owner_decisions", ["project-local-rule"])[0],
        "target_decision": "project-local-rule",
        "reviewed_by": "regression-fixture-owner",
        "reviewed_at": "2026-06-19",
        "review_after": "2026-09-19",
        "source_status": "owner-reviewed-fixture",
        "source_sha256": "a" * 64,
        "source_size": 123,
        "current_validity": "fixture-only",
        "scope_statement": "PCR02 project-local only",
        "applicable_project_version": "fixture-version",
        "evidence_refs": ["artifacts/manifests/pcr02-owner-resolution-playbook-20260618.md"],
        "status_reason": "Regression fixture for landing-plan required files.",
    }.items():
        form[key] = value
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
    expect(
        result["exit_code"] == 0
        and parsed.get("landing_plan", {}).get("status") == "planned"
        and "indexes/by-project.md" in required_files
        and "indexes/by-status.md" in required_files,
        "owner-landing-plan-project-index",
        "owner landing plan requires by-project index",
        {
            "exit_code": result["exit_code"],
            "landing_status": parsed.get("landing_plan", {}).get("status"),
            "required_manual_files": required_files,
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
        "status-wrong-bucket",
        "status-noncanonical-only",
        "owner-partial-resolved",
        "owner-single-form",
        "status-next-owner-gate",
        "owner-landing-plan-project-index",
        "manual-entry-project-index-hint",
        "manual-entry-project-derived-from-domain",
        "manual-entry-default-dates",
        "manual-entry-owner-override",
        "regression-manifest-coverage",
    ]
    missing_ids = [test_id for test_id in required_ids if test_id not in manifest_text]
    expect(
        not read_error
        and not missing_ids
        and "12 个回归场景" in manifest_text,
        "regression-manifest-coverage",
        "regression helper manifest covers current regression ids",
        {
            "manifest": str(manifest_path.relative_to(root)),
            "read_error": read_error,
            "missing_ids": missing_ids,
            "expected_count_text": "12 个回归场景",
        },
    )

test_baseline()
test_status_wrong_bucket()
test_status_noncanonical_only()
test_owner_partial_resolved()
test_owner_single_form()
test_status_next_owner_gate()
test_owner_landing_plan_project_index()
test_manual_entry_project_index_hint()
test_manual_entry_project_from_domain()
test_manual_entry_default_dates()
test_manual_entry_owner_override()
test_regression_manifest_coverage()

if not args.keep_temp:
    for temp_root in temp_roots:
        shutil.rmtree(temp_root, ignore_errors=True)

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
