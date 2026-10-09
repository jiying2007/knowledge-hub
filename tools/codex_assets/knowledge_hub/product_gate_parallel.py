"""Parallel evidence collection for the product maturity gate."""

from __future__ import annotations

import concurrent.futures
import pathlib
import sys
import os
import subprocess
import time
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
from .unit_evidence import verified_parent_unit


def _partial_timeout_output(value):
    raw = value if isinstance(value, bytes) else str(value or '').encode('utf-8')
    return raw[-4096:].decode('utf-8', errors='replace'), len(raw) > 4096


def _run_timed_command(root, command, *, timeout, accepted_exit_codes=(0,), extra_env=None):
    """Only command timeouts become failed evidence; programming errors escape."""
    started = time.monotonic()
    try:
        return run_rtk(root, command, timeout=timeout, accepted_exit_codes=accepted_exit_codes, extra_env=extra_env)
    except subprocess.TimeoutExpired as error:
        stdout, clipped_out = _partial_timeout_output(error.output)
        stderr, clipped_err = _partial_timeout_output(error.stderr)
        return {'command':'rtk ' + ' '.join(command), 'exit_code':124, 'stdout':stdout, 'stderr':stderr,
                'duration_sec':round(time.monotonic()-started, 3), 'evidence_status':'failed-timeout',
                'timed_out':True, 'timeout_sec':timeout, 'output_incomplete':True,
                'output_truncated':bool(getattr(error, 'output_truncated', False) or clipped_out or clipped_err),
                'error_type':type(error).__name__, 'automatic_retry_performed':False}


def command_timeout_projection(result):
    if result.get('timed_out') is not True:
        return {}
    return {'status':'fail', 'command_timeout':{
        key:result[key] for key in ('timed_out', 'timeout_sec', 'output_incomplete', 'output_truncated',
                                   'error_type', 'automatic_retry_performed')
    }, 'stdout_tail':result['stdout'].splitlines()[-20:], 'stderr_tail':result['stderr'].splitlines()[-20:]}


def attach_command_timeout_diagnostics(checks, results):
    pairs = (('knowledge_check', 'check_result'), ('knowledge_status_strict', 'status_result'),
             ('source_check_runtime', 'source_check_result'), ('shared_unit_tests', 'unit_result'),
             ('git_diff_check', 'diff_result'))
    for check, result_key in pairs:
        checks[check].update(command_timeout_projection(results[result_key]))


def _check_result(root: pathlib.Path, as_of: str) -> Dict[str, Any]:
    return _run_timed_command(
        root,
        ["bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics", "--as-of", as_of],
        timeout=45,
        accepted_exit_codes=(0, 1),
    )


def _status_result(root: pathlib.Path, as_of: str) -> Dict[str, Any]:
    return _run_timed_command(
        root,
        ["bash", "tools/knowledge-status.sh", "--strict", "--json", "--as-of", as_of],
        timeout=60,
        accepted_exit_codes=(0, 1, 2),
    )


def _source_check_result(root: pathlib.Path, as_of: str) -> Dict[str, Any]:
    return _run_timed_command(
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
        statuses = preflight_engineering_quality.get("check_statuses", {})
        if not (preflight_engineering_quality.get("fresh") and preflight_engineering_quality.get("signature_matches")
                and isinstance(statuses, Mapping) and statuses.get("coverage") == "pass"
                and statuses.get("coverage_report") == "pass"):
            return {"command":"snapshot", "exit_code":77, "stdout":"parent evidence is stale", "stderr":"", "duration_sec":0, "evidence_status":"not-run"}
        return {
            "command": "snapshot:{}#coverage".format(preflight_engineering_quality.get("path", "")),
            "exit_code": 0,
            "stdout": "full engineering coverage/pytest evidence reused",
            "stderr": "",
            "duration_sec": 0,
            "evidence_status": "passed-reused",
            "parent_evidence": {key:preflight_engineering_quality.get(key) for key in ("path", "generated_at", "signature_matches", "check_statuses")},
        }
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
        parent = verified_parent_unit(root)
        if parent:
            return {'command':'parent-unit-evidence', 'exit_code':0, 'stdout':'completed parent pytest evidence reused',
                    'stderr':'', 'duration_sec':0, 'evidence_status':'passed-reused', 'parent_evidence':parent}
        return {"command":"pytest", "exit_code":77, "stdout":"pytest delegated without successful parent evidence",
                "stderr":"", "duration_sec":0, "evidence_status":"delegated-unverified"}
    return _run_timed_command(
        root,
        [sys.executable, "-m", "pytest", "-q"],
        timeout=unit_test_timeout_seconds,
        accepted_exit_codes=(0, 1, 4, 5, 77),
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
        "diff_result": lambda: _run_timed_command(root, ["git", "diff", "--check"], timeout=20, accepted_exit_codes=(0, 1)),
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
