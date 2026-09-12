import argparse
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
projection = parser.add_mutually_exclusive_group()
projection.add_argument("--json", action="store_true")
projection.add_argument(
    "--summary-json",
    action="store_true",
    help="Emit bounded counts, slowest cases, and failures only.",
)
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
    # Match public Hub CLIs, which use the host-local calendar date by default.
    # Explicit --as-of / KNOWLEDGE_TODAY still take precedence for reproducibility.
    return dt.date.today(), source

today, today_source = resolve_today()
child_env = os.environ.copy()
child_env["KNOWLEDGE_TELEMETRY"] = "0"
child_env["KNOWLEDGE_PYTHON_RUNTIME"] = os.path.abspath(sys.executable)
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
            # Regression fixtures must rebuild ignored derived state. Copying a live
            # .cache while other workers run root-level read tools creates a mixed
            # snapshot and lets non-authoritative local state leak between cases.
            ignored.update({".git", ".tmp", ".codex", ".cache"})
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
    for _index, line in enumerate(lines):
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
