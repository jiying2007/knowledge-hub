import ast
import copy
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Set, Tuple


ROOT = Path(".")
SOURCE_PATH = Path("tools/codex_assets/knowledge_hub/search.py")
CORE_PATH = Path("tools/codex_assets/knowledge_hub/search_core.py")
INDEX_PATH = Path("tools/codex_assets/knowledge_hub/search_index.py")
QUERY_SUPPORT_PATH = Path("tools/codex_assets/knowledge_hub/search_query_support.py")
QUERY_PATH = Path("tools/codex_assets/knowledge_hub/search_query.py")
WORKFLOW_PATH = Path(".github/workflows/search-burndown-bootstrap.yml")
SCRIPT_PATH = Path(".github/search_burndown_bootstrap.py")

source = SOURCE_PATH.read_text(encoding="utf-8")
lines = source.splitlines(keepends=True)
tree = ast.parse(source)


def is_docstring(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def node_start(node: ast.AST) -> int:
    start = int(getattr(node, "lineno", 1))
    decorators = getattr(node, "decorator_list", [])
    if decorators:
        start = min(start, *(int(item.lineno) for item in decorators))
    return start


def slice_node(node: ast.AST) -> str:
    start = node_start(node)
    end = int(getattr(node, "end_lineno", start))
    return "".join(lines[start - 1 : end]).rstrip()


def bound_import_names(node: ast.AST) -> Dict[str, ast.alias]:
    result: Dict[str, ast.alias] = {}
    if isinstance(node, ast.Import):
        for alias in node.names:
            result[alias.asname or alias.name.split(".", 1)[0]] = alias
    elif isinstance(node, ast.ImportFrom):
        for alias in node.names:
            if alias.name == "*":
                continue
            result[alias.asname or alias.name] = alias
    return result


def assigned_names(node: ast.AST) -> Set[str]:
    result: Set[str] = set()
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        result.add(node.name)
    elif isinstance(node, ast.Assign):
        for target in node.targets:
            for item in ast.walk(target):
                if isinstance(item, ast.Name):
                    result.add(item.id)
    elif isinstance(node, ast.AnnAssign):
        for item in ast.walk(node.target):
            if isinstance(item, ast.Name):
                result.add(item.id)
    return result


def loaded_names(nodes: Sequence[ast.AST]) -> Set[str]:
    result: Set[str] = set()
    for node in nodes:
        for item in ast.walk(node):
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load):
                result.add(item.id)
    return result


body = tree.body
search_index_pos = next(
    index
    for index, node in enumerate(body)
    if isinstance(node, ast.ClassDef) and node.name == "SearchIndex"
)
search_pos = next(
    index
    for index, node in enumerate(body)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "search"
)
if search_pos <= search_index_pos:
    raise SystemExit("unexpected search.py top-level ordering")

import_nodes = [
    node
    for node in body
    if isinstance(node, (ast.Import, ast.ImportFrom))
    and not (isinstance(node, ast.ImportFrom) and node.module == "__future__")
]
non_import = [
    node
    for node in body
    if not isinstance(node, (ast.Import, ast.ImportFrom)) and not is_docstring(node)
]
search_index_node = body[search_index_pos]
search_node = body[search_pos]

core_nodes = [
    node
    for node in non_import
    if int(getattr(node, "end_lineno", 0)) < node_start(search_index_node)
]
index_nodes = [search_index_node]
query_support_nodes = [
    node
    for node in non_import
    if node_start(node) > int(search_index_node.end_lineno)
    and int(getattr(node, "end_lineno", 0)) < node_start(search_node)
]
query_nodes = [
    node
    for node in non_import
    if node_start(node) >= node_start(search_node)
]

partitions: Mapping[str, Sequence[ast.AST]] = {
    "core": core_nodes,
    "index": index_nodes,
    "query_support": query_support_nodes,
    "query": query_nodes,
}
module_path = {
    "core": ".search_core",
    "index": ".search_index",
    "query_support": ".search_query_support",
    "query": ".search_query",
}
module_doc = {
    "core": "Core corpus, token, and cache primitives for Knowledge Hub search.",
    "index": "SQLite index lifecycle for Knowledge Hub search.",
    "query_support": "Ranking and result-shaping helpers for Knowledge Hub search.",
    "query": "Public query execution and telemetry for Knowledge Hub search.",
}

owned: Dict[str, Set[str]] = {
    name: set().union(*(assigned_names(node) for node in nodes))
    for name, nodes in partitions.items()
}
owner_by_name: Dict[str, str] = {}
for partition, names in owned.items():
    for name in names:
        if name in owner_by_name:
            raise SystemExit(f"duplicate top-level owner for {name}")
        owner_by_name[name] = partition


# Keep only the original imports actually loaded by each partition.
def render_original_imports(nodes: Sequence[ast.AST]) -> List[str]:
    loaded = loaded_names(nodes)
    rendered: List[str] = []
    for node in import_nodes:
        bindings = bound_import_names(node)
        selected = [name for name in bindings if name in loaded]
        if not selected:
            continue
        clone = copy.deepcopy(node)
        clone.names = [bindings[name] for name in selected]
        rendered.append(ast.unparse(clone))
    return rendered


def dependency_imports(partition: str, nodes: Sequence[ast.AST]) -> List[str]:
    loaded = loaded_names(nodes)
    groups: Dict[str, List[str]] = {}
    for name in sorted(loaded):
        owner = owner_by_name.get(name)
        if owner is None or owner == partition:
            continue
        groups.setdefault(owner, []).append(name)
    # The original file is ordered core -> index -> query support -> query.
    # Any dependency in the opposite direction would create a circular split.
    order = {"core": 0, "index": 1, "query_support": 2, "query": 3}
    for owner in groups:
        if order[owner] > order[partition]:
            raise SystemExit(
                f"unsafe reverse dependency: {partition} loads {owner}: {groups[owner]}"
            )
    rendered: List[str] = []
    for owner in sorted(groups, key=lambda value: order[value]):
        names = groups[owner]
        if len(names) == 1:
            rendered.append(f"from {module_path[owner]} import {names[0]}")
        else:
            block = "\n".join(f"    {name}," for name in names)
            rendered.append(f"from {module_path[owner]} import (\n{block}\n)")
    return rendered


def render_module(partition: str, nodes: Sequence[ast.AST]) -> str:
    imports = render_original_imports(nodes) + dependency_imports(partition, nodes)
    header = [
        f'"""{module_doc[partition]}"""',
        "",
        "from __future__ import annotations",
        "",
    ]
    if imports:
        header.extend(imports)
        header.append("")
    body_text = "\n\n\n".join(slice_node(node) for node in nodes)
    return "\n".join(header) + "\n" + body_text.rstrip() + "\n"


rendered = {
    "core": render_module("core", core_nodes),
    "index": render_module("index", index_nodes),
    "query_support": render_module("query_support", query_support_nodes),
    "query": render_module("query", query_nodes),
}
for partition, text in rendered.items():
    ast.parse(text)
    line_count = len(text.splitlines())
    if line_count > 800:
        raise SystemExit(f"{partition} partition remains oversized: {line_count}")

CORE_PATH.write_text(rendered["core"], encoding="utf-8")
INDEX_PATH.write_text(rendered["index"], encoding="utf-8")
QUERY_SUPPORT_PATH.write_text(rendered["query_support"], encoding="utf-8")
QUERY_PATH.write_text(rendered["query"], encoding="utf-8")

alias_by_partition = {
    "core": "_core",
    "index": "_index",
    "query_support": "_query_support",
    "query": "_query",
}
facade_lines = [
    '"""Stable compatibility facade for cached, explainable Knowledge Hub search."""',
    "",
    "from __future__ import annotations",
    "",
    "import sys as _sys",
    "import types as _types",
    "",
    "from . import search_core as _core",
    "from . import search_index as _index",
    "from . import search_query as _query",
    "from . import search_query_support as _query_support",
    "",
    "_IMPLEMENTATIONS = (_core, _index, _query_support, _query)",
    "",
    "# Preserve the broad historical module surface, including imported helpers used",
    "# by tests and callers for dependency injection. Explicit aliases below keep",
    "# statically imported public/private definitions visible to mypy as well.",
    "for _module in _IMPLEMENTATIONS:",
    "    for _name, _value in vars(_module).items():",
    "        if not _name.startswith(\"__\"):",
    "            globals().setdefault(_name, _value)",
    "",
]
for name in sorted(owner_by_name):
    facade_lines.append(
        f"{name} = {alias_by_partition[owner_by_name[name]]}.{name}"
    )
facade_lines.extend(
    [
        "",
        "class _SearchFacadeModule(_types.ModuleType):",
        '    """Propagate facade monkeypatches to implementation-module globals."""',
        "",
        "    def __setattr__(self, name: str, value: object) -> None:",
        "        _types.ModuleType.__setattr__(self, name, value)",
        "        if name.startswith(\"__\"):",
        "            return",
        "        for module in _IMPLEMENTATIONS:",
        "            if hasattr(module, name):",
        "                setattr(module, name, value)",
        "",
        "",
        "setattr(_sys.modules[__name__], \"__class__\", _SearchFacadeModule)",
        "",
    ]
)
facade = "\n".join(facade_lines)
ast.parse(facade)
if len(facade.splitlines()) > 800:
    raise SystemExit("search facade remains oversized")
SOURCE_PATH.write_text(facade, encoding="utf-8")

# Directly type-check all split modules.
pyproject = Path("pyproject.toml")
pyproject_text = pyproject.read_text(encoding="utf-8")
anchor = '    "tools/codex_assets/knowledge_hub/search.py",\n'
if anchor not in pyproject_text:
    raise SystemExit("search.py mypy anchor missing")
extra_mypy = (
    '    "tools/codex_assets/knowledge_hub/search_core.py",\n'
    '    "tools/codex_assets/knowledge_hub/search_index.py",\n'
    '    "tools/codex_assets/knowledge_hub/search_query_support.py",\n'
    '    "tools/codex_assets/knowledge_hub/search_query.py",\n'
)
if "search_core.py" not in pyproject_text:
    pyproject_text = pyproject_text.replace(
        anchor,
        anchor + "".join(extra_mypy),
        1,
    )
pyproject.write_text(pyproject_text, encoding="utf-8")

complexity_test = Path("tests/test_complexity_budget.py")
complexity_text = complexity_test.read_text(encoding="utf-8")
complexity_addition = '''


def test_search_split_reduces_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}
    search_paths = {
        "tools/codex_assets/knowledge_hub/search.py",
        "tools/codex_assets/knowledge_hub/search_core.py",
        "tools/codex_assets/knowledge_hub/search_index.py",
        "tools/codex_assets/knowledge_hub/search_query_support.py",
        "tools/codex_assets/knowledge_hub/search_query.py",
    }

    assert report["status"] == "pass"
    assert report["oversized_module_count"] <= 4
    assert not search_paths & oversized_paths
'''
if "test_search_split_reduces_repository_oversized_module_debt" not in complexity_text:
    complexity_test.write_text(
        complexity_text.rstrip() + complexity_addition.rstrip() + "\n",
        encoding="utf-8",
    )

split_test = '''from tools.codex_assets.knowledge_hub import search as search_module
from tools.codex_assets.knowledge_hub import search_core
from tools.codex_assets.knowledge_hub import search_index
from tools.codex_assets.knowledge_hub import search_query
from tools.codex_assets.knowledge_hub import search_query_support
from tools.codex_assets.knowledge_hub.common import repository_root


def test_search_split_keeps_facade_identity_and_module_budget():
    assert search_module.SearchFilters is search_core.SearchFilters
    assert search_module.SearchIndex is search_index.SearchIndex
    assert search_module.search is search_query.search
    assert search_module._score is search_query_support._score

    root = repository_root()
    for relative in (
        "tools/codex_assets/knowledge_hub/search.py",
        "tools/codex_assets/knowledge_hub/search_core.py",
        "tools/codex_assets/knowledge_hub/search_index.py",
        "tools/codex_assets/knowledge_hub/search_query_support.py",
        "tools/codex_assets/knowledge_hub/search_query.py",
    ):
        assert len((root / relative).read_text(encoding="utf-8").splitlines()) <= 800


def test_search_facade_monkeypatches_reach_split_implementation(monkeypatch):
    def replacement_tokens(value, maximum=20000):
        return ["patched", str(maximum), value[:1]]

    def replacement_reader(*args, **kwargs):
        return b"patched"

    monkeypatch.setattr(search_module, "_index_tokens", replacement_tokens)
    monkeypatch.setattr(search_module, "SEARCH_MAX_FILE_BYTES", 12345)
    monkeypatch.setattr(
        search_module,
        "read_repository_bytes_bounded",
        replacement_reader,
    )

    assert search_core._index_tokens is replacement_tokens
    assert search_core.SEARCH_MAX_FILE_BYTES == 12345
    assert search_core.read_repository_bytes_bounded is replacement_reader
    assert search_index._index_tokens is replacement_tokens
    assert search_index.SEARCH_MAX_FILE_BYTES == 12345
    assert search_index.read_repository_bytes_bounded is replacement_reader
    assert search_query.SEARCH_MAX_FILE_BYTES == 12345
    assert search_query.read_repository_bytes_bounded is replacement_reader
'''
Path("tests/test_search_split_surface.py").write_text(split_test, encoding="utf-8")

# Parse every generated source and enforce the module budget before the commit.
for path in (SOURCE_PATH, CORE_PATH, INDEX_PATH, QUERY_SUPPORT_PATH, QUERY_PATH):
    text = path.read_text(encoding="utf-8")
    ast.parse(text)
    count = len(text.splitlines())
    if count > 800:
        raise SystemExit(f"{path} remains oversized: {count}")
    print(f"{path}: {count} lines")

WORKFLOW_PATH.unlink()
SCRIPT_PATH.unlink()
