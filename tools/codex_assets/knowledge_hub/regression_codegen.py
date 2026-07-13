"""Split the historical regression payload into maintainable Python modules.

This generator is intentionally deterministic.  It is retained so the initial
hard cut from the shell heredoc can be audited and reproduced without copying
truncated terminal output into source files.
"""

from __future__ import annotations

import argparse
import ast
import os
import pathlib
import subprocess
from typing import Dict, Iterable, List, Sequence, Tuple


CASE_MODULES = (
    "model",
    "lifecycle",
    "retrieval",
    "project_routing",
    "obsidian",
    "governance",
    "terminal_gates",
)

PRODUCT_GATE_REPLACEMENTS = {
    "test_final_gate_owner_review_blocker",
    "test_final_gate_skip_regression_blocker",
    # Historical shell name is pruned when regenerating the hard-cut package.
    "test_final_gate_mature_review_queue_owner_review_blocker",
    "test_final_gate_product_review_queue_owner_review_blocker",
    "test_final_gate_empty_child_json_blocker",
    "test_final_gate_default_regression_path",
    "test_final_gate_source_final_state_field_gap",
    "test_final_gate_strict_status_nonowner_blocker",
    "test_final_gate_source_check_runtime_failed_blocker",
}


def _source_from_git(root: pathlib.Path, revision: str, path: str) -> str:
    result = subprocess.run(
        ["rtk", "git", "show", "{}:{}".format(revision, path)],
        cwd=str(root),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError("unable to read {}:{}: {}".format(revision, path, result.stderr.strip()))
    return result.stdout


def _extract_python(shell_text: str) -> str:
    marker = "<<'PY'\n"
    if marker not in shell_text or "\nPY" not in shell_text:
        raise RuntimeError("source script does not contain the expected quoted Python heredoc")
    return shell_text.split(marker, 1)[1].rsplit("\nPY", 1)[0] + "\n"


def _slice(lines: Sequence[str], node: ast.AST) -> str:
    return "".join(lines[node.lineno - 1 : node.end_lineno])


def _category(name: str) -> str:
    if "knowledge_search" in name or "knowledge_context" in name:
        return "retrieval"
    if name.startswith(("test_pcr02_", "test_boundary_")):
        return "project_routing"
    if "obsidian" in name:
        return "obsidian"
    if name.startswith(
        (
            "test_manual_entry_",
            "test_review_queue_",
            "test_summary_backfill_",
            "test_orphan_",
            "test_reviewing_",
            "test_source_manual_entry_",
        )
    ):
        return "lifecycle"
    if name.startswith(("test_final_gate_", "test_health_summary_", "test_regression_", "test_status_")):
        return "terminal_gates"
    if name.startswith(
        (
            "test_governance_",
            "test_manifest_",
            "test_index_",
            "test_registry_",
            "test_template_",
            "test_templates_",
            "test_source_coverage_",
            "test_source_check_",
            "test_offline_",
            "test_ai_generated_",
            "test_by_topic_",
        )
    ):
        return "model"
    return "governance"


def _atomic_write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(str(temporary), str(path))


def prune_replaced_product_gate_tests(root: pathlib.Path) -> str:
    path = root / "tools/codex_assets/knowledge_hub/regression/terminal_gates.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    ranges = [
        (node.lineno - 1, node.end_lineno)
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in PRODUCT_GATE_REPLACEMENTS
    ]
    for start, end in sorted(ranges, reverse=True):
        del lines[start:end]
    content = "".join(lines)
    while "\n\n\n\ndef " in content:
        content = content.replace("\n\n\n\ndef ", "\n\n\ndef ")
    _atomic_write(path, content)
    return str(path.relative_to(root))


def split_payload(source: str) -> Tuple[str, Dict[str, str], str]:
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    tests = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]
    if not tests:
        raise RuntimeError("no top-level regression test functions found")
    first_test_line = min(node.lineno for node in tests)
    last_test_line = max(node.end_lineno for node in tests)
    helpers = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("test_")
        and node.lineno >= first_test_line
        and node.end_lineno <= last_test_line
    ]
    support = "".join(lines[: first_test_line - 1]).rstrip() + "\n\n"
    if helpers:
        support += "\n\n".join(_slice(lines, node).rstrip() for node in helpers) + "\n"
    grouped: Dict[str, List[str]] = {name: [] for name in CASE_MODULES}
    for node in tests:
        grouped[_category(node.name)].append(_slice(lines, node).rstrip())
    cases = {}
    for module_name in CASE_MODULES:
        header = (
            '"""Generated regression cases: {}."""\n\n'
            "# Generated by regression_codegen.py; edit assertions here, then keep the generator deterministic.\n"
            "from .support import *  # noqa: F401,F403\n\n"
        ).format(module_name.replace("_", " "))
        body = "\n\n".join(grouped[module_name])
        cases[module_name] = header + body + ("\n" if body else "")
    tail_nodes = [node for node in tree.body if node.lineno > last_test_line]
    if not tail_nodes:
        raise RuntimeError("regression runner tail is missing")
    tail = "".join(lines[tail_nodes[0].lineno - 1 :])
    imports = "".join("from .{} import *  # noqa: F401,F403\n".format(name) for name in CASE_MODULES)
    runner = '"""Regression suite selection and execution."""\n\n' + imports + "\n" + tail
    return support, cases, runner


def generate(root: pathlib.Path, revision: str, source_path: str) -> List[str]:
    shell_text = _source_from_git(root, revision, source_path)
    support, cases, runner = split_payload(_extract_python(shell_text))
    output_root = root / "tools/codex_assets/knowledge_hub/regression"
    outputs = {
        output_root / "__init__.py": '"""Modular Knowledge Hub regression suite."""\n',
        output_root / "support.py": support,
        output_root / "runner.py": runner,
    }
    for name, content in cases.items():
        outputs[output_root / (name + ".py")] = content
    for path, content in outputs.items():
        _atomic_write(path, content)
    return [str(path.relative_to(root)) for path in sorted(outputs)]


def main(argv: Iterable[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--source-path", default="tools/knowledge-regression.sh")
    parser.add_argument(
        "--prune-product-legacy",
        action="store_true",
        help="Remove product-gate tests replaced by regression/product_gates.py from the current split module.",
    )
    args = parser.parse_args(list(argv) if argv else None)
    root = pathlib.Path(args.root or pathlib.Path(__file__).resolve().parents[3]).resolve()
    if args.prune_product_legacy:
        print(prune_replaced_product_gate_tests(root))
        return 0
    for path in generate(root, args.revision, args.source_path):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
