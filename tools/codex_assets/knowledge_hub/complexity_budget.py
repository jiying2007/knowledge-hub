"""Report legacy complexity and fail only on new budget regressions."""

from __future__ import annotations

import ast
import json
import os
import pathlib
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union

from .common import KnowledgeHubError, run_rtk


def _load_policy(root: pathlib.Path) -> Mapping[str, Any]:
    path = root / "registry/engineering-budgets.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema_version": 0, "error": str(exc)}
    return payload if isinstance(payload, Mapping) else {}


def _tracked_files(root: pathlib.Path) -> set[str]:
    if not (root / ".git").exists():
        return set()
    try:
        result = run_rtk(root, ["git", "ls-files"], timeout=20)
    except (KnowledgeHubError, OSError):
        return set()
    return {
        line.strip()
        for line in result["stdout"].splitlines()
        if line.strip()
    }


class _FunctionCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: List[str] = []
        self.rows: List[Dict[str, Any]] = []

    def _visit_function(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
    ) -> None:
        end = int(getattr(node, "end_lineno", node.lineno))
        qualname = ".".join(self.stack + [node.name])
        self.rows.append(
            {
                "name": node.name,
                "qualname": qualname,
                "line": node.lineno,
                "lines": end - node.lineno + 1,
            }
        )
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(
        self,
        node: ast.AsyncFunctionDef,
    ) -> None:
        self._visit_function(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()


def _function_lengths_from_text(text: str) -> List[Dict[str, Any]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    collector = _FunctionCollector()
    collector.visit(tree)
    return collector.rows


def _function_lengths(path: pathlib.Path) -> List[Dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    return _function_lengths_from_text(text)


def _baseline_ref() -> str:
    return os.environ.get("KNOWLEDGE_COMPLEXITY_BASE_REF", "").strip()


def _git_ref_exists(root: pathlib.Path, ref: str) -> bool:
    if not ref or not (root / ".git").exists():
        return False
    try:
        result = run_rtk(
            root,
            ["git", "rev-parse", "--verify", "{}^{{commit}}".format(ref)],
            timeout=20,
            accepted_exit_codes=(0, 128),
        )
    except (KnowledgeHubError, OSError):
        return False
    return result["exit_code"] == 0


def _git_show_text(
    root: pathlib.Path,
    ref: str,
    relative: str,
) -> Optional[str]:
    try:
        result = run_rtk(
            root,
            ["git", "show", "{}:{}".format(ref, relative)],
            timeout=20,
            accepted_exit_codes=(0, 128),
        )
    except (KnowledgeHubError, OSError):
        return None
    return result["stdout"] if result["exit_code"] == 0 else None


def _baseline_functions(text: str) -> Dict[str, int]:
    return {
        str(row["qualname"]): int(row["lines"])
        for row in _function_lengths_from_text(text)
    }


def _strict_new_module_regressions(
    relative: str,
    line_count: int,
    functions: List[Dict[str, Any]],
    *,
    module_limit: int,
    function_limit: int,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if line_count > module_limit:
        rows.append(
            {
                "type": "new-module-size",
                "path": relative,
                "actual": line_count,
                "limit": module_limit,
            }
        )
    for row in functions:
        if int(row["lines"]) > function_limit:
            rows.append(
                {
                    "type": "new-function-size",
                    "path": relative,
                    "function": row["name"],
                    "qualname": row["qualname"],
                    "line": row["line"],
                    "actual": row["lines"],
                    "limit": function_limit,
                }
            )
    return rows


def _baseline_function_regressions(
    relative: str,
    functions: List[Dict[str, Any]],
    baseline: Mapping[str, int],
    *,
    function_limit: int,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in functions:
        actual = int(row["lines"])
        if actual <= function_limit:
            continue
        qualname = str(row["qualname"])
        before = baseline.get(qualname)
        if before is None or int(before) <= function_limit:
            kind = "function-size-regression"
            limit = function_limit
        elif actual > int(before):
            kind = "legacy-function-growth"
            limit = int(before)
        else:
            continue
        rows.append(
            {
                "type": kind,
                "path": relative,
                "function": row["name"],
                "qualname": qualname,
                "line": row["line"],
                "actual": actual,
                "limit": limit,
            }
        )
    return rows


def _evaluate_against_git_baseline(
    root: pathlib.Path,
    *,
    baseline_ref: str,
    relative: str,
    line_count: int,
    functions: List[Dict[str, Any]],
    module_limit: int,
    function_limit: int,
    cap: Any,
) -> Tuple[bool, List[Dict[str, Any]], List[Dict[str, Any]]]:
    baseline_text = _git_show_text(root, baseline_ref, relative)
    if baseline_text is None:
        return (
            False,
            _strict_new_module_regressions(
                relative,
                line_count,
                functions,
                module_limit=module_limit,
                function_limit=function_limit,
            ),
            [],
        )
    regressions: List[Dict[str, Any]] = []
    attention: List[Dict[str, Any]] = []
    baseline_lines = len(baseline_text.splitlines())
    limit = int(cap) if cap is not None else max(module_limit, baseline_lines)
    if line_count > limit:
        regressions.append(
            {
                "type": "legacy-module-growth",
                "path": relative,
                "actual": line_count,
                "limit": limit,
            }
        )
    elif line_count > module_limit:
        attention.append(
            {
                "type": "legacy-module-size",
                "path": relative,
                "actual": line_count,
                "limit": module_limit,
            }
        )
    regressions.extend(
        _baseline_function_regressions(
            relative,
            functions,
            _baseline_functions(baseline_text),
            function_limit=function_limit,
        )
    )
    return True, regressions, attention


def _evaluate_without_git_baseline(
    *,
    relative: str,
    line_count: int,
    functions: List[Dict[str, Any]],
    module_limit: int,
    function_limit: int,
    cap: Any,
    is_tracked: bool,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    regressions: List[Dict[str, Any]] = []
    attention: List[Dict[str, Any]] = []
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
        attention.append(
            {
                "type": "legacy-module-size",
                "path": relative,
                "actual": line_count,
                "limit": module_limit,
            }
        )
    elif not is_tracked:
        regressions.extend(
            _strict_new_module_regressions(
                relative,
                line_count,
                functions,
                module_limit=module_limit,
                function_limit=function_limit,
            )
        )
    return regressions, attention


def _evaluate_python(
    root: pathlib.Path,
    *,
    module_limit: int,
    function_limit: int,
    legacy_caps: Mapping[str, Any],
    baseline_ref: str,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    git_index_available = (root / ".git").exists()
    tracked_files = _tracked_files(root)
    tracked_python = {
        path
        for path in tracked_files
        if path.startswith("tools/codex_assets/knowledge_hub/")
        and path.endswith(".py")
    }
    baseline_without_git_index = not tracked_files and (
        git_index_available or bool(legacy_caps)
    )
    regressions: List[Dict[str, Any]] = []
    legacy_attention: List[Dict[str, Any]] = []
    module_rows: List[Dict[str, Any]] = []
    package = root / "tools/codex_assets/knowledge_hub"
    paths = sorted(package.rglob("*.py")) if package.exists() else []
    for path in paths:
        relative = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8")
        line_count = len(text.splitlines())
        functions = _function_lengths_from_text(text)
        cap = legacy_caps.get(relative)
        if baseline_ref:
            is_baseline, new_regressions, attention = (
                _evaluate_against_git_baseline(
                    root,
                    baseline_ref=baseline_ref,
                    relative=relative,
                    line_count=line_count,
                    functions=functions,
                    module_limit=module_limit,
                    function_limit=function_limit,
                    cap=cap,
                )
            )
        else:
            is_baseline = (
                relative in tracked_python or baseline_without_git_index
            )
            new_regressions, attention = _evaluate_without_git_baseline(
                relative=relative,
                line_count=line_count,
                functions=functions,
                module_limit=module_limit,
                function_limit=function_limit,
                cap=cap,
                is_tracked=is_baseline,
            )
        regressions.extend(new_regressions)
        legacy_attention.extend(attention)
        module_rows.append(
            {
                "path": relative,
                "lines": line_count,
                "tracked_baseline": is_baseline,
                "legacy_cap": cap,
                "oversized_function_count": sum(
                    1
                    for row in functions
                    if int(row["lines"]) > function_limit
                ),
            }
        )
    return module_rows, regressions, legacy_attention


def _evaluate_data_growth(
    root: pathlib.Path,
    policy: Mapping[str, Any],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    growth = (
        policy.get("data_growth", {})
        if isinstance(policy, Mapping)
        else {}
    )
    if not isinstance(growth, Mapping):
        return [], [{"type": "data-growth-policy-invalid"}]
    tracked = growth.get("tracked_paths", {})
    if not tracked:
        return [], []
    if not isinstance(tracked, Mapping):
        return [], [{"type": "data-growth-policy-invalid"}]
    rows: List[Dict[str, Any]] = []
    regressions: List[Dict[str, Any]] = []
    for relative, raw_limits in sorted(tracked.items()):
        if not isinstance(raw_limits, Mapping):
            regressions.append(
                {
                    "type": "data-growth-policy-invalid",
                    "path": str(relative),
                }
            )
            continue
        segment_at = int(raw_limits.get("segment_at_bytes", 0) or 0)
        hard_max = int(raw_limits.get("hard_max_bytes", 0) or 0)
        if segment_at < 1 or hard_max < segment_at:
            regressions.append(
                {
                    "type": "data-growth-policy-invalid",
                    "path": str(relative),
                }
            )
            continue
        path = root / str(relative)
        size = (
            path.stat().st_size
            if path.exists() and path.is_file()
            else 0
        )
        if size > hard_max:
            state = "hard-cap-exceeded"
        elif size >= segment_at:
            state = "segment-candidate"
        else:
            state = "within-budget"
        row = {
            "path": str(relative),
            "bytes": size,
            "segment_at_bytes": segment_at,
            "hard_max_bytes": hard_max,
            "state": state,
        }
        rows.append(row)
        if size > hard_max:
            regressions.append(
                {
                    "type": "data-growth-hard-cap",
                    "path": str(relative),
                    "actual": size,
                    "limit": hard_max,
                }
            )
    return rows, regressions


def _python_budget_settings(
    policy: Mapping[str, Any],
) -> Tuple[int, int, Mapping[str, Any]]:
    python_policy = (
        policy.get("python", {}) if isinstance(policy, Mapping) else {}
    )
    module_limit = int(
        python_policy.get("new_module_max_lines", 800) or 800
    )
    function_limit = int(
        python_policy.get("new_function_max_lines", 80) or 80
    )
    legacy_caps = python_policy.get("legacy_module_line_caps", {})
    if not isinstance(legacy_caps, Mapping):
        legacy_caps = {}
    return module_limit, function_limit, legacy_caps


def _wrapper_budget(
    root: pathlib.Path,
    policy: Mapping[str, Any],
) -> Tuple[int, int, List[Dict[str, Any]]]:
    command_policy = (
        policy.get("commands", {}) if isinstance(policy, Mapping) else {}
    )
    wrapper_count = len(list((root / "tools").glob("knowledge-*.sh")))
    wrapper_baseline = int(
        command_policy.get("wrapper_baseline", wrapper_count) or 0
    )
    regressions: List[Dict[str, Any]] = []
    if wrapper_count > wrapper_baseline:
        regressions.append(
            {
                "type": "wrapper-growth",
                "actual": wrapper_count,
                "limit": wrapper_baseline,
            }
        )
    return wrapper_count, wrapper_baseline, regressions


def _oversized_modules(
    module_rows: List[Dict[str, Any]],
    module_limit: int,
) -> List[Dict[str, Any]]:
    return [
        {
            "path": str(row.get("path", "")),
            "lines": int(row.get("lines", 0) or 0),
            "limit": module_limit,
            "legacy_cap": row.get("legacy_cap"),
        }
        for row in module_rows
        if int(row.get("lines", 0) or 0) > module_limit
    ]


def evaluate_complexity_budget(root: pathlib.Path) -> Dict[str, Any]:
    policy = _load_policy(root)
    module_limit, function_limit, legacy_caps = _python_budget_settings(
        policy
    )
    requested_baseline = _baseline_ref()
    baseline_ref = requested_baseline
    baseline_error = bool(
        baseline_ref and not _git_ref_exists(root, baseline_ref)
    )
    if baseline_error:
        baseline_ref = ""

    module_rows, regressions, legacy_attention = _evaluate_python(
        root,
        module_limit=module_limit,
        function_limit=function_limit,
        legacy_caps=legacy_caps,
        baseline_ref=baseline_ref,
    )
    if baseline_error:
        regressions.append(
            {
                "type": "complexity-baseline-unavailable",
                "ref": requested_baseline,
            }
        )
    data_growth, growth_regressions = _evaluate_data_growth(root, policy)
    regressions.extend(growth_regressions)
    wrapper_count, wrapper_baseline, wrapper_regressions = _wrapper_budget(
        root,
        policy,
    )
    regressions.extend(wrapper_regressions)
    oversized = _oversized_modules(module_rows, module_limit)

    errors = []
    if policy.get("schema_version") != 1:
        errors.append("engineering budget schema_version must be 1")
    return {
        "schema_version": 1,
        "status": "fail" if errors or regressions else "pass",
        "read_only": True,
        "report_only_legacy": True,
        "policy": "registry/engineering-budgets.json",
        "baseline_ref": requested_baseline,
        "baseline_ref_resolved": bool(baseline_ref),
        "new_module_max_lines": module_limit,
        "new_function_max_lines": function_limit,
        "wrapper_count": wrapper_count,
        "wrapper_baseline": wrapper_baseline,
        "regression_count": len(regressions),
        "regressions": regressions,
        "oversized_module_count": len(oversized),
        "oversized_modules": oversized,
        "legacy_attention_count": len(legacy_attention),
        "legacy_attention": legacy_attention,
        "module_count": len(module_rows),
        "modules": module_rows,
        "data_growth": data_growth,
        "data_growth_attention_count": sum(
            1
            for row in data_growth
            if row.get("state") == "segment-candidate"
        ),
        "errors": errors,
    }

