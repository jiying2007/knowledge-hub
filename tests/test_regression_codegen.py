import ast

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.regression_codegen import (
    DEFAULT_SOURCE_PATHS,
    MODEL_MODULES,
    rebalance_model_sources,
)


def _test_names(source):
    tree = ast.parse(source)
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]


def test_regression_codegen_round_trip_preserves_current_model_shards():
    root = repository_root()
    paths = [
        root / "tools/codex_assets/knowledge_hub/regression" / (name + ".py")
        for name in MODEL_MODULES
    ]
    current = [path.read_text(encoding="utf-8") for path in paths]

    rendered = rebalance_model_sources(current)

    assert tuple(rendered) == MODEL_MODULES
    assert [rendered[name] for name in MODEL_MODULES] == current
    assert all(len(rendered[name].splitlines()) <= 800 for name in MODEL_MODULES)


def test_regression_codegen_preserves_test_identity_and_order():
    first = '''"""Generated regression cases: model."""\n\nfrom .support import *  # noqa: F401,F403\n\ndef test_a():\n    value = 1\n    assert value\n\ndef test_b():\n    value = 2\n    assert value\n'''
    second = '''"""Generated regression cases: model index."""\n\nfrom .support import *  # noqa: F401,F403\n\ndef test_c():\n    value = 3\n    assert value\n\ndef test_d():\n    value = 4\n    assert value\n'''

    rendered = rebalance_model_sources([first, second])
    before = _test_names(first) + _test_names(second)
    after = []
    for name in MODEL_MODULES:
        ast.parse(rendered[name])
        after.extend(_test_names(rendered[name]))

    assert after == before
    assert len(after) == len(set(after))


def test_regression_codegen_targets_only_generated_model_shards():
    assert MODEL_MODULES == ("model", "model_index")
    assert DEFAULT_SOURCE_PATHS == (
        "tools/codex_assets/knowledge_hub/regression/model.py",
        "tools/codex_assets/knowledge_hub/regression/model_index.py",
    )
    assert all("knowledge-regression.sh" not in path for path in DEFAULT_SOURCE_PATHS)
