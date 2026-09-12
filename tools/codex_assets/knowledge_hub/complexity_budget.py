"""Report legacy complexity and fail only on new budget regressions."""

from __future__ import annotations

import ast
import json
import pathlib
from typing import Any, Dict, List, Mapping

from .common import KnowledgeHubError, run_rtk


def _load_policy(root: pathlib.Path) -> Mapping[str, Any]:
    path = root / "registry/engineering-budgets.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema_version": 0, "error": str(exc)}
    return payload if isinstance(payload, Mapping) else {}


def _tracked_python(root: pathlib.Path) -> set[str]:
    if not (root / ".git").exists():
        return set()
    try:
        result = run_rtk(
            root,
            ["git", "ls-files", "tools/codex_assets/knowledge_hub/*.py"],
            timeout=20,
        )
    except (KnowledgeHubError, OSError):
        return set()
    return {line.strip() for line in result["stdout"].splitlines() if line.strip()}


def _function_lengths(path: pathlib.Path) -> List[Dict[str, Any]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []
    rows = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = int(getattr(node, "end_lineno", node.lineno))
            rows.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "lines": end - node.lineno + 1,
                }
            )
    return rows


def _evaluate_python(
    root: pathlib.Path,
    *,
    module_limit: int,
    function_limit: int,
    legacy_caps: Mapping[str, Any],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    tracked = _tracked_python(root)
    baseline_without_git_index = not tracked and bool(legacy_caps)
    regressions: List[Dict[str, Any]] = []
    legacy_attention: List[Dict[str, Any]] = []
    module_rows: List[Dict[str, Any]] = []
    package = root / "tools/codex_assets/knowledge_hub"
    for path in sorted(package.rglob("*.py")) if package.exists() else []:
        relative = str(path.relative_to(root))
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        functions = _function_lengths(path)
        is_tracked = relative in tracked or baseline_without_git_index
        cap = legacy_caps.get(relative)
        module_rows.append(
            {
                "path": relative,
                "lines": line_count,
                "tracked_baseline": is_tracked,
                "legacy_cap": cap,
                "oversized_function_count": sum(
                    1 for row in functions if row["lines"] > function_limit
                ),
            }
        )
        if cap is not None and line_count > int(cap):
            regressions.append(
                {
                    "type": "legacy-module-growth",
                    "path": relative,
                    "actual": line_count,
                    "limit": int(cap),
                }
            )
        elif is_tracked and line_count > module_limit:
            legacy_attention.append(
                {
                    "type": "legacy-module-size",
                    "path": relative,
                    "actual": line_count,
                    "limit": module_limit,
                }
            )
        elif not is_tracked:
            if line_count > module_limit:
                regressions.append(
                    {
                        "type": "new-module-size",
                        "path": relative,
                        "actual": line_count,
                        "limit": module_limit,
                    }
                )
            for row in functions:
                if row["lines"] > function_limit:
                    regressions.append(
                        {
                            "type": "new-function-size",
                            "path": relative,
                            "function": row["name"],
                            "line": row["line"],
                            "actual": row["lines"],
                            "limit": function_limit,
                        }
                    )
    return module_rows, regressions, legacy_attention


def evaluate_complexity_budget(root: pathlib.Path) -> Dict[str, Any]:
    policy = _load_policy(root)
    python_policy = policy.get("python", {}) if isinstance(policy, Mapping) else {}
    command_policy = policy.get("commands", {}) if isinstance(policy, Mapping) else {}
    module_limit = int(python_policy.get("new_module_max_lines", 800) or 800)
    function_limit = int(python_policy.get("new_function_max_lines", 80) or 80)
    legacy_caps = python_policy.get("legacy_module_line_caps", {})
    if not isinstance(legacy_caps, Mapping):
        legacy_caps = {}
    module_rows, regressions, legacy_attention = _evaluate_python(
        root,
        module_limit=module_limit,
        function_limit=function_limit,
        legacy_caps=legacy_caps,
    )
    oversized_modules = [
        {
            "path": str(row.get("path", "")),
            "lines": int(row.get("lines", 0) or 0),
            "limit": module_limit,
            "legacy_cap": row.get("legacy_cap"),
        }
        for row in module_rows
        if int(row.get("lines", 0) or 0) > module_limit
    ]
    wrapper_count = len(list((root / "tools").glob("knowledge-*.sh")))
    wrapper_baseline = int(command_policy.get("wrapper_baseline", wrapper_count) or 0)
    if wrapper_count > wrapper_baseline:
        regressions.append(
            {
                "type": "wrapper-growth",
                "actual": wrapper_count,
                "limit": wrapper_baseline,
            }
        )
    errors = []
    if policy.get("schema_version") != 1:
        errors.append("engineering budget schema_version must be 1")
    return {
        "schema_version": 1,
        "status": "fail" if errors or regressions else "pass",
        "read_only": True,
        "report_only_legacy": True,
        "policy": "registry/engineering-budgets.json",
        "new_module_max_lines": module_limit,
        "new_function_max_lines": function_limit,
        "wrapper_count": wrapper_count,
        "wrapper_baseline": wrapper_baseline,
        "regression_count": len(regressions),
        "regressions": regressions,
        "oversized_module_count": len(oversized_modules),
        "oversized_modules": oversized_modules,
        "legacy_attention_count": len(legacy_attention),
        "legacy_attention": legacy_attention,
        "module_count": len(module_rows),
        "modules": module_rows,
        "errors": errors,
    }
