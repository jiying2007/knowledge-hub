import ast
from pathlib import Path


source_path = Path("tools/codex_assets/knowledge_hub/product_gate.py")
source = source_path.read_text(encoding="utf-8")
lines = source.splitlines(keepends=True)
tree = ast.parse(source)
functions = {
    node.name: node
    for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
helper_names = [
    "_source_runtime_ready",
    "_unit_test_evidence_reuse_mode",
    "product_snapshot_path",
    "_write_snapshot",
    "_git_delivery_state",
    "_engineering_quality_state",
    "_candidate_integrity",
    "_restore_state",
    "_project_readiness",
]
missing = [name for name in helper_names + ["run_product_gate"] if name not in functions]
if missing:
    raise SystemExit(f"missing expected product gate functions: {missing}")


def slice_node(node):
    return "".join(lines[node.lineno - 1 : node.end_lineno])


support_header = '''"""Support helpers for the product maturity gate."""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import time
import uuid
from typing import Any, Dict, Mapping, Set

from .common import (
    KnowledgeHubError,
    ensure_private_directory_tree,
    ensure_private_file,
    load_json,
    pretty_json,
    project_rows,
    registry_items,
    repository_rows,
    route_rows,
    run_rtk,
    working_tree_signature,
)
from .context import TASK_TYPES, _query_route
from .engineering import engineering_snapshot_path
from .evidence import evaluate_evidence_contract
from .project_readiness import (
    SLOT_NAMES,
    _project_paths,
    _repo_rows_for_project,
    _workspace_state,
)
from .recovery_evidence import (
    evidence_matches_current_execution,
    expected_repository_from_registry,
)
from .schemas import validate_instance

'''
support_body = "\n\n".join(
    slice_node(functions[name]).rstrip() for name in helper_names
) + "\n"
support_path = Path("tools/codex_assets/knowledge_hub/product_gate_support.py")
support_path.write_text(support_header + support_body, encoding="utf-8")

run_text = slice_node(functions["run_product_gate"])
task_start = run_text.index("    tasks = {\n")
result_marker = '    check_result = results["check_result"]\n'
task_end = run_text.index(result_marker)
replacement = '''    results = collect_parallel_results(
        root,
        as_of,
        signature,
        git_delivery,
        reuse_unit_tests,
        preflight_engineering_quality,
        unit_test_timeout_seconds=UNIT_TEST_TIMEOUT_SECONDS,
    )
'''
run_text = run_text[:task_start] + replacement + run_text[task_end:]

facade_header = '''"""Product-level maturity gate beyond lifecycle governance."""

from __future__ import annotations

import os
import pathlib
import re
import sys
import time
from collections import Counter
from typing import Any, Dict

from .common import (
    parse_json_output,
    registry_items,
    run_rtk,
    utc_timestamp,
    working_tree_signature,
)
from .maturity import evaluate_maturity_axes
from .product_gate_parallel import collect_parallel_results
from .product_gate_support import (
    _candidate_integrity as _candidate_integrity,
    _engineering_quality_state as _engineering_quality_state,
    _git_delivery_state as _git_delivery_state,
    _project_readiness as _project_readiness,
    _restore_state as _restore_state,
    _source_runtime_ready as _source_runtime_ready,
    _unit_test_evidence_reuse_mode as _unit_test_evidence_reuse_mode,
    _write_snapshot as _write_snapshot,
    product_snapshot_path as product_snapshot_path,
)
from .product_policy import (
    evaluate_specialized_owner_requirements,
    load_product_policy,
)
from .product_summary import product_gate_summary as product_gate_summary
from .retrieval import (
    retrieval_benchmark_summary,
    run_retrieval_benchmark_serialized,
)
from .schemas import validate_instance

UNIT_TEST_TIMEOUT_SECONDS = 180

'''
source_path.write_text(facade_header + run_text.rstrip() + "\n", encoding="utf-8")

parallel = '''"""Parallel evidence collection for the product maturity gate."""

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
'''
parallel_path = Path("tools/codex_assets/knowledge_hub/product_gate_parallel.py")
parallel_path.write_text(parallel, encoding="utf-8")

pyproject = Path("pyproject.toml")
text = pyproject.read_text(encoding="utf-8")
waiver = '''# product_gate is a legacy oversized module whose timeout constant currently
# separates two import groups. Keep the waiver local until that module is split;
# E402 remains enforced everywhere else.
"tools/codex_assets/knowledge_hub/product_gate.py" = ["E402"]
'''
if waiver not in text:
    raise SystemExit("expected product_gate E402 waiver not found")
text = text.replace(waiver, "")
mypy_anchor = '    "tools/codex_assets/knowledge_hub/product_gate.py",\n'
if mypy_anchor not in text:
    raise SystemExit("product_gate mypy anchor missing")
text = text.replace(
    mypy_anchor,
    mypy_anchor
    + '    "tools/codex_assets/knowledge_hub/product_gate_support.py",\n'
    + '    "tools/codex_assets/knowledge_hub/product_gate_parallel.py",\n',
    1,
)
pyproject.write_text(text, encoding="utf-8")

complexity_test = Path("tests/test_complexity_budget.py")
test_text = complexity_test.read_text(encoding="utf-8")
addition = '''


def test_product_gate_split_reduces_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}

    assert report["status"] == "pass"
    assert report["oversized_module_count"] <= 5
    assert "tools/codex_assets/knowledge_hub/product_gate.py" not in oversized_paths
    assert "tools/codex_assets/knowledge_hub/product_gate_support.py" not in oversized_paths
    assert "tools/codex_assets/knowledge_hub/product_gate_parallel.py" not in oversized_paths
'''
if "test_product_gate_split_reduces_repository_oversized_module_debt" not in test_text:
    complexity_test.write_text(test_text.rstrip() + addition + "\n", encoding="utf-8")

facade_test = Path("tests/test_product_gate.py")
facade_text = facade_test.read_text(encoding="utf-8")
facade_addition = '''


def test_product_gate_split_keeps_helper_facade_and_module_budget():
    from tools.codex_assets.knowledge_hub import product_gate, product_gate_support

    assert product_gate._project_readiness is product_gate_support._project_readiness
    assert product_gate._restore_state is product_gate_support._restore_state
    root = repository_root()
    for relative in (
        "tools/codex_assets/knowledge_hub/product_gate.py",
        "tools/codex_assets/knowledge_hub/product_gate_support.py",
        "tools/codex_assets/knowledge_hub/product_gate_parallel.py",
    ):
        assert len((root / relative).read_text(encoding="utf-8").splitlines()) <= 800
'''
if "test_product_gate_split_keeps_helper_facade_and_module_budget" not in facade_text:
    facade_test.write_text(facade_text.rstrip() + facade_addition + "\n", encoding="utf-8")

for path in (source_path, support_path, parallel_path):
    text = path.read_text(encoding="utf-8")
    parsed = ast.parse(text)
    line_count = len(text.splitlines())
    if line_count > 800:
        raise SystemExit(f"{path} remains oversized: {line_count}")
    if path == parallel_path:
        for node in ast.walk(parsed):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = int(getattr(node, "end_lineno", node.lineno))
                if end - node.lineno + 1 > 80:
                    raise SystemExit(f"new function oversized: {path}:{node.name}")
    print(f"{path}: {line_count} lines")

Path(".github/workflows/product-gate-burndown-bootstrap.yml").unlink()
Path(".github/product_gate_burndown_bootstrap.py").unlink()
