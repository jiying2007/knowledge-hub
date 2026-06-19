#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
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

test_baseline()
test_status_wrong_bucket()
test_status_noncanonical_only()
test_owner_partial_resolved()

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
