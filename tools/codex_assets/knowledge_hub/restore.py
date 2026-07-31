"""Offline restore drills for a working-tree candidate or committed HEAD."""

from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import sys
import tarfile
import tempfile
import time
import uuid
from typing import Any, Dict, List, Mapping

from .common import (
    KnowledgeHubError,
    ensure_private_directory_tree,
    ensure_private_file,
    parse_json_output,
    pretty_json,
    run_rtk,
    utc_timestamp,
    working_tree_signature,
)
from .recovery_evidence import (
    evidence_matches_current_execution,
    execution_environment_evidence,
    expected_repository_from_registry,
)


def _candidate_paths(root: pathlib.Path) -> List[str]:
    result = run_rtk(
        root,
        ["git", "-c", "core.quotePath=false", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        timeout=30,
    )
    deleted_result = run_rtk(
        root,
        ["git", "-c", "core.quotePath=false", "ls-files", "-z", "--deleted"],
        timeout=30,
    )
    deleted = set(value for value in deleted_result["stdout"].split("\0") if value)
    return sorted(set(value for value in result["stdout"].split("\0") if value) - deleted)


def _hash(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _snapshot_path(root: pathlib.Path, source_mode: str) -> pathlib.Path:
    return root / ".cache/knowledge-hub/restore-drill-{}.json".format(source_mode)


def _write_snapshot(root: pathlib.Path, payload: Mapping[str, Any]) -> str:
    source_mode = str(payload["source_mode"])
    path = _snapshot_path(root, source_mode)
    ensure_private_directory_tree(root, path.parent)
    temporary = path.with_name("{}.tmp-{}".format(path.name, uuid.uuid4().hex))
    temporary.write_text(pretty_json(dict(payload)) + "\n", encoding="utf-8")
    ensure_private_file(temporary)
    os.replace(str(temporary), str(path))
    ensure_private_file(path)
    return str(path.relative_to(root))


def _head_revision(root: pathlib.Path) -> str:
    result = run_rtk(root, ["git", "rev-parse", "HEAD"], timeout=15)
    revision = result["stdout"].strip()
    if not revision:
        raise KnowledgeHubError("HEAD revision is unavailable")
    return revision


def _restore_runtime() -> str:
    runtime = pathlib.Path(os.path.abspath(sys.executable))
    if not runtime.is_file():
        raise KnowledgeHubError("restore runtime interpreter is unavailable")
    return str(runtime)


def _execution_environment(
    source_mode: str,
    source_revision: str,
    expected_repository: str,
) -> Dict[str, Any]:
    return execution_environment_evidence(
        source_mode,
        source_revision,
        expected_repository=expected_repository,
    )


def _copy_candidate(root: pathlib.Path, restored: pathlib.Path) -> Dict[str, Any]:
    paths = _candidate_paths(root)
    missing: List[str] = []
    symlinks: List[str] = []
    copied: List[Dict[str, Any]] = []
    for relative in paths:
        source = root / relative
        if not source.exists():
            missing.append(relative)
            continue
        if source.is_symlink():
            symlinks.append(relative)
            continue
        if not source.is_file():
            continue
        target = restored / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(target))
        before = _hash(source)
        after = _hash(target)
        if before != after:
            raise KnowledgeHubError("restore copy hash mismatch: {}".format(relative))
        copied.append({"path": relative, "sha256": before, "size": source.stat().st_size})
    return {"paths": paths, "missing": missing, "symlinks": symlinks, "copied": copied}


def _copy_head_archive(root: pathlib.Path, restored: pathlib.Path, directory: pathlib.Path) -> Dict[str, Any]:
    archive = directory / "knowledge-hub-head.tar"
    run_rtk(
        root,
        ["git", "archive", "--format=tar", "--output", str(archive), "HEAD"],
        timeout=60,
    )
    paths: List[str] = []
    symlinks: List[str] = []
    copied: List[Dict[str, Any]] = []
    with tarfile.open(str(archive), mode="r") as handle:
        for member in handle.getmembers():
            relative = pathlib.PurePosixPath(member.name)
            if relative.is_absolute() or ".." in relative.parts:
                raise KnowledgeHubError("unsafe path in HEAD archive: {}".format(member.name))
            if member.issym() or member.islnk():
                symlinks.append(member.name)
                continue
            target = restored.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                continue
            source = handle.extractfile(member)
            if source is None:
                raise KnowledgeHubError("cannot read HEAD archive member: {}".format(member.name))
            target.parent.mkdir(parents=True, exist_ok=True)
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            target.chmod(member.mode & 0o777)
            paths.append(member.name)
            copied.append({"path": member.name, "sha256": _hash(target), "size": target.stat().st_size})
    return {"paths": sorted(paths), "missing": [], "symlinks": symlinks, "copied": copied}


def _run_restore_check(
    restored: pathlib.Path,
    command: List[str],
    command_env: Dict[str, str],
    *,
    parse_status: bool = True,
    max_attempts: int = 1,
) -> Dict[str, Any]:
    attempts: List[Dict[str, Any]] = []
    for attempt_number in range(1, max_attempts + 1):
        try:
            result = run_rtk(
                restored,
                command,
                timeout=180,
                accepted_exit_codes=(0, 1, 2, 4, 5),
                extra_env=command_env,
            )
            parsed_status = ""
            reported_errors: List[Any] = []
            if parse_status:
                try:
                    parsed = parse_json_output(result)
                    parsed_status = str(parsed.get("status", ""))
                    reported_errors = list(parsed.get("errors", []))[:20]
                except KnowledgeHubError:
                    parsed_status = "unparseable"
            row: Dict[str, Any] = {
                "attempt": attempt_number,
                "command": result["command"].replace(
                    str(restored), "<restored-root>"
                ),
                "exit_code": result["exit_code"],
                "status": "pass" if result["exit_code"] == 0 else "fail",
                "reported_status": parsed_status,
                "reported_errors": reported_errors,
                "stdout_tail": result["stdout"].strip().splitlines()[-20:],
                "stderr_tail": result["stderr"].strip().splitlines()[-10:],
                "duration_sec": result["duration_sec"],
            }
        except (KnowledgeHubError, OSError) as exc:
            row = {
                "attempt": attempt_number,
                "status": "fail",
                "error": str(exc),
            }
        attempts.append(row)
        if row["status"] == "pass":
            break

    check = dict(attempts[-1])
    check["attempt_count"] = len(attempts)
    check["recovered_after_retry"] = (
        len(attempts) > 1 and check["status"] == "pass"
    )
    if max_attempts > 1:
        check["attempts"] = attempts
    return check


def run_restore_drill(root: pathlib.Path, as_of: str, source_mode: str = "candidate") -> Dict[str, Any]:
    if source_mode not in {"candidate", "head"}:
        raise KnowledgeHubError("source_mode must be candidate or head")
    started = time.monotonic()
    candidate_signature = working_tree_signature(root)
    source_revision = _head_revision(root)
    expected_repository = expected_repository_from_registry(root)
    execution_environment = _execution_environment(
        source_mode,
        source_revision,
        expected_repository,
    )
    current_execution_bound = evidence_matches_current_execution(
        execution_environment,
        source_revision,
        expected_repository=expected_repository,
    )
    runtime_python = _restore_runtime()
    runtime_env = {"KNOWLEDGE_PYTHON_RUNTIME": runtime_python}
    checks: Dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="knowledge-hub-restore-") as directory:
        temporary_root = pathlib.Path(directory)
        restored = temporary_root / "knowledge-hub"
        restored.mkdir()
        copy_result = (
            _copy_candidate(root, restored)
            if source_mode == "candidate"
            else _copy_head_archive(root, restored, temporary_root)
        )
        paths = copy_result["paths"]
        missing = copy_result["missing"]
        symlinks = copy_result["symlinks"]
        copied = copy_result["copied"]
        run_rtk(restored, ["git", "init", "-q"], timeout=15)
        run_rtk(restored, ["git", "add", "--all"], timeout=30)
        run_rtk(
            restored,
            [
                "git",
                "-c",
                "user.name=Knowledge Hub Restore Drill",
                "-c",
                "user.email=restore-drill@localhost",
                "commit",
                "-q",
                "-m",
                "restore drill scratch snapshot",
            ],
            timeout=60,
        )
        commands = {
            "dependency_imports": [
                "bash",
                "tools/ci/python-runtime.sh",
                "-c",
                "import jsonschema, pytest, yaml",
            ],
            "knowledge_check": [
                "bash",
                "tools/knowledge-check.sh",
                "--dry-run",
                "--json",
                "--diagnostics",
                "--as-of",
                as_of,
            ],
            "unit_tests": [
                "bash",
                "tools/ci/python-runtime.sh",
                "-m",
                "pytest",
                "-q",
            ],
            "link_audit": ["bash", "tools/knowledge-link-audit.sh", "--json", "--strict"],
            "obsidian_view": ["bash", "tools/knowledge-obsidian-view-build.sh", "--check", "--json"],
            "retrieval_benchmark": ["bash", "tools/knowledge-retrieval-benchmark.sh", "--json"],
            "project_readiness": [
                "bash",
                "tools/knowledge-project-readiness.sh",
                "--check",
                "--json",
                "--as-of",
                as_of,
            ],
            "team_export_plan": ["bash", "tools/knowledge-export.sh", "--plan", "--json"],
            "search_smoke": ["bash", "tools/knowledge-search.sh", "ASAN", "--json", "--limit", "3", "--no-telemetry"],
            "context_smoke": [
                "bash",
                "tools/knowledge-context.sh",
                "--cwd",
                str(restored),
                "--query",
                "knowledge-hub 自举",
                "--task-type",
                "general",
                "--json",
                "--no-telemetry",
            ],
            "product_gate_smoke": [
                "bash",
                "tools/knowledge-final-gate.sh",
                "--json",
                "--final-profile",
                "product",
                "--as-of",
                as_of,
            ],
        }
        for name, command in commands.items():
            command_env = dict(runtime_env)
            if name == "product_gate_smoke":
                command_env["KNOWLEDGE_FINAL_GATE_INNER_REGRESSION"] = "1"
            checks[name] = _run_restore_check(
                restored,
                command,
                command_env,
                parse_status=name not in {"unit_tests", "dependency_imports"},
                max_attempts=2 if name == "retrieval_benchmark" else 1,
            )
    failed = [name for name, row in checks.items() if row["status"] != "pass"]
    status = (
        "pass" if not missing and not symlinks and not failed else "needs-fix"
    )
    payload: Dict[str, Any] = {
        "schema_version": 4,
        "status": status,
        "source_mode": source_mode,
        "restore_semantics": (
            "working-tree-delivery-candidate"
            if source_mode == "candidate"
            else "committed-head-git-archive"
        ),
        "source_revision": source_revision,
        "execution_environment": execution_environment,
        "evidence_matches_current_execution": current_execution_bound,
        "remote_checkout_verified": execution_environment[
            "remote_checkout_verified"
        ],
        "remote_published_ref_verified": execution_environment[
            "remote_published_ref_verified"
        ],
        "offsite_environment_verified": execution_environment[
            "offsite_environment_verified"
        ],
        "temporary_git_semantics": "scratch-metadata-for-offline-checks-not-a-clone",
        "network_used": False,
        "source_project_write": False,
        "tracked_files_written": False,
        "generated_at": utc_timestamp(),
        "as_of": as_of,
        "candidate_path_count": len(paths),
        "candidate_signature": candidate_signature,
        "dependency_baseline": {
            "runtime": "requirements-runtime.txt",
            "development": "requirements-dev.txt",
            "runtime_injected": True,
            "runtime_selector": "tools/ci/python-runtime.sh",
            "installation_performed": False,
        },
        "cache_included": any(path.startswith(".cache/") for path in paths),
        "local_workspace_mapping_included": "local/workspaces.json" in paths,
        "copied_file_count": len(copied),
        "missing_count": len(missing),
        "missing": missing,
        "symlink_count": len(symlinks),
        "symlinks": symlinks,
        "hash_mismatch_count": 0,
        "checks": checks,
        "failed_checks": failed,
        "temporary_restore_removed": True,
        "duration_ms": round((time.monotonic() - started) * 1000, 2),
    }
    payload["snapshot"] = _write_snapshot(root, payload)
    return payload
