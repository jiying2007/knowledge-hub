"""Offline restore drills for a working-tree candidate or committed HEAD."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import tarfile
import tempfile
import time
from typing import Any, Dict, List, Mapping, Sequence

from .common import KnowledgeHubError, parse_json_output, pretty_json, run_rtk, utc_timestamp, working_tree_signature


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
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(pretty_json(dict(payload)) + "\n", encoding="utf-8")
    os.replace(str(temporary), str(path))
    compatibility_path = root / ".cache/knowledge-hub/restore-drill.json"
    compatibility_temporary = compatibility_path.with_suffix(".tmp")
    compatibility_temporary.write_text(pretty_json(dict(payload)) + "\n", encoding="utf-8")
    os.replace(str(compatibility_temporary), str(compatibility_path))
    return str(path.relative_to(root))


def _head_revision(root: pathlib.Path) -> str:
    result = run_rtk(root, ["git", "rev-parse", "HEAD"], timeout=15)
    revision = result["stdout"].strip()
    if not revision:
        raise KnowledgeHubError("HEAD revision is unavailable")
    return revision


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


def run_restore_drill(root: pathlib.Path, as_of: str, source_mode: str = "candidate") -> Dict[str, Any]:
    if source_mode not in {"candidate", "head"}:
        raise KnowledgeHubError("source_mode must be candidate or head")
    started = time.monotonic()
    candidate_signature = working_tree_signature(root)
    source_revision = _head_revision(root)
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
                "python3",
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
            "unit_tests": ["python3", "-m", "pytest", "-q"],
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
            result = run_rtk(
                restored,
                command,
                timeout=180,
                accepted_exit_codes=(0, 1, 2, 4, 5),
                extra_env={"KNOWLEDGE_FINAL_GATE_INNER_REGRESSION": "1"}
                if name == "product_gate_smoke"
                else None,
            )
            parsed_status = ""
            reported_errors: List[Any] = []
            if name not in {"unit_tests", "dependency_imports"}:
                try:
                    parsed = parse_json_output(result)
                    parsed_status = str(
                        parsed.get("status", parsed.get("gate_status", parsed.get("overall_status", "")))
                    )
                    reported_errors = list(parsed.get("errors", []))[:20]
                except KnowledgeHubError:
                    parsed_status = "unparseable"
            checks[name] = {
                "command": result["command"].replace(str(restored), "<restored-root>"),
                "exit_code": result["exit_code"],
                "status": "pass" if result["exit_code"] == 0 else "fail",
                "reported_status": parsed_status,
                "reported_errors": reported_errors,
                "stderr_tail": result["stderr"].strip().splitlines()[-10:],
                "duration_sec": result["duration_sec"],
            }
    failed = [name for name, row in checks.items() if row["status"] != "pass"]
    status = "pass" if not missing and not symlinks and not failed else "fail"
    payload: Dict[str, Any] = {
        "schema_version": 1,
        "status": status,
        "source_mode": source_mode,
        "restore_semantics": (
            "working-tree-delivery-candidate"
            if source_mode == "candidate"
            else "committed-head-git-archive"
        ),
        "source_revision": source_revision,
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
