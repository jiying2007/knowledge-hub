"""Parallel evidence collection for the product maturity gate."""

from __future__ import annotations

import concurrent.futures
import pathlib
import sys
from typing import Any, Dict, Mapping

from .common import run_rtk
from .engineering import evaluate_engineering_contract
from .export import plan_team_export
from .link_audit import audit_links
from .metrics import local_metrics
from .obsidian_view import build_obsidian_views
from .product_gate_support import _project_readiness, _restore_state
from .schemas import validate_schema_catalog
from .store import incomplete_transactions


def _check_result(root: pathlib.Path, as_of: str) -> Dict[str, Any]:
    return run_rtk(
        root,
        ["bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics", "--as-of", as_of],
        timeout=45,
        accepted_exit_codes=(0, 1),
    )


def _status_result(root: pathlib.Path, as_of: str) -> Dict[str, Any]:
    return run_rtk(
        root,
        ["bash", "tools/knowledge-status.sh", "--strict", "--json", "--as-of", as_of],
        timeout=60,
        accepted_exit_codes=(0, 1, 2),
    )


def _source_check_result(root: pathlib.Path, as_of: str) -> Dict[str, Any]:
    return run_rtk(
        root,
        ["bash", "tools/knowledge-source-check.sh", "--scope", "all", "--json", "--as-of", as_of],
        timeout=60,
        accepted_exit_codes=(0, 1),
    )


def _unit_result(
    root: pathlib.Path,
    reuse_unit_tests: bool,
    preflight_engineering_quality: Mapping[str, Any],
    unit_test_timeout_seconds: int,
) -> Dict[str, Any]:
    if reuse_unit_tests:
        return {
            "command": "snapshot:{}#coverage".format(preflight_engineering_quality.get("path", "")),
            "exit_code": 0,
            "stdout": "full engineering coverage/pytest evidence reused",
            "stderr": "",
            "duration_sec": 0,
        }
    return run_rtk(
        root,
        [sys.executable, "-m", "pytest", "-q"],
        timeout=unit_test_timeout_seconds,
        accepted_exit_codes=(0, 1, 4, 5),
    )


def collect_parallel_results(
    root: pathlib.Path,
    as_of: str,
    signature: str,
    git_delivery: Mapping[str, Any],
    reuse_unit_tests: bool,
    preflight_engineering_quality: Mapping[str, Any],
    *,
    unit_test_timeout_seconds: int,
) -> Dict[str, Any]:
    head_revision = str(git_delivery["head_revision"])
    tasks = {
        "check_result": lambda: _check_result(root, as_of),
        "status_result": lambda: _status_result(root, as_of),
        "source_check_result": lambda: _source_check_result(root, as_of),
        "unit_result": lambda: _unit_result(
            root, reuse_unit_tests, preflight_engineering_quality, unit_test_timeout_seconds
        ),
        "diff_result": lambda: run_rtk(root, ["git", "diff", "--check"], timeout=20, accepted_exit_codes=(0, 1)),
        "links": lambda: audit_links(root),
        "obsidian_view": lambda: build_obsidian_views(root),
        "schema_catalog": lambda: validate_schema_catalog(root),
        "engineering_contract": lambda: evaluate_engineering_contract(root),
        "metrics": lambda: local_metrics(root),
        "readiness": lambda: _project_readiness(root),
        "export_plan": lambda: plan_team_export(root),
        "restore_candidate": lambda: _restore_state(root, as_of, "candidate", signature, head_revision),
        "restore_head": lambda: _restore_state(root, as_of, "head", signature, head_revision),
        "incomplete": lambda: incomplete_transactions(root),
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {name: executor.submit(task) for name, task in tasks.items()}
        return {name: future.result() for name, future in futures.items()}
