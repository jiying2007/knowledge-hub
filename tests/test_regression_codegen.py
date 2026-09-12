import ast

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.regression_codegen import (
    DEFAULT_SOURCE_PATHS,
    GOVERNANCE_MODULES,
    GOVERNANCE_SOURCE_PATHS,
    LIFECYCLE_MODULES,
    LIFECYCLE_SOURCE_PATHS,
    MODEL_MODULES,
    MODEL_SOURCE_PATHS,
    rebalance_governance_sources,
    rebalance_lifecycle_sources,
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


def _current_sources(module_names):
    root = repository_root()
    paths = [
        root / "tools/codex_assets/knowledge_hub/regression" / (name + ".py")
        for name in module_names
    ]
    return [path.read_text(encoding="utf-8") for path in paths]


def test_regression_codegen_round_trip_preserves_current_model_shards():
    current = _current_sources(MODEL_MODULES)

    rendered = rebalance_model_sources(current)

    assert tuple(rendered) == MODEL_MODULES
    assert [rendered[name] for name in MODEL_MODULES] == current
    assert all(len(rendered[name].splitlines()) <= 800 for name in MODEL_MODULES)


def test_regression_codegen_round_trip_preserves_current_lifecycle_shards():
    current = _current_sources(LIFECYCLE_MODULES)

    rendered = rebalance_lifecycle_sources(current)

    assert tuple(rendered) == LIFECYCLE_MODULES
    assert [rendered[name] for name in LIFECYCLE_MODULES] == current
    assert all(
        len(rendered[name].splitlines()) <= 800 for name in LIFECYCLE_MODULES
    )


def test_regression_codegen_round_trip_preserves_current_governance_shards():
    current = _current_sources(GOVERNANCE_MODULES)

    rendered = rebalance_governance_sources(current)

    assert tuple(rendered) == GOVERNANCE_MODULES
    assert [rendered[name] for name in GOVERNANCE_MODULES] == current
    assert all(
        len(rendered[name].splitlines()) <= 800 for name in GOVERNANCE_MODULES
    )


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


def _four_shard_sources(prefix, module_names):
    sources = []
    for module_index, module_name in enumerate(module_names):
        functions = []
        for offset in range(2):
            test_index = module_index * 2 + offset
            functions.append(
                "def test_{}_{}():\n    value = {}\n    assert value >= 0\n".format(
                    prefix, test_index, test_index
                )
            )
        sources.append(
            '"""Generated regression cases: {}."""\n\n'.format(
                module_name.replace("_", " ")
            )
            + "from .support import *  # noqa: F401,F403\n\n"
            + "\n".join(functions)
        )
    return sources


def _assert_identity_and_order(sources, module_names, rendered):
    before = []
    after = []
    for source in sources:
        before.extend(_test_names(source))
    for name in module_names:
        ast.parse(rendered[name])
        after.extend(_test_names(rendered[name]))

    assert after == before
    assert len(after) == len(set(after))


def test_regression_codegen_lifecycle_preserves_test_identity_and_order():
    sources = _four_shard_sources("lifecycle", LIFECYCLE_MODULES)

    rendered = rebalance_lifecycle_sources(sources)

    _assert_identity_and_order(sources, LIFECYCLE_MODULES, rendered)


def test_regression_codegen_governance_preserves_test_identity_and_order():
    sources = _four_shard_sources("governance", GOVERNANCE_MODULES)

    rendered = rebalance_governance_sources(sources)

    _assert_identity_and_order(sources, GOVERNANCE_MODULES, rendered)


def test_regression_codegen_targets_only_generated_case_shards():
    assert MODEL_MODULES == ("model", "model_index")
    assert LIFECYCLE_MODULES == (
        "lifecycle",
        "lifecycle_2",
        "lifecycle_3",
        "lifecycle_4",
    )
    assert GOVERNANCE_MODULES == (
        "governance",
        "governance_2",
        "governance_3",
        "governance_4",
    )
    assert MODEL_SOURCE_PATHS == (
        "tools/codex_assets/knowledge_hub/regression/model.py",
        "tools/codex_assets/knowledge_hub/regression/model_index.py",
    )
    assert LIFECYCLE_SOURCE_PATHS == (
        "tools/codex_assets/knowledge_hub/regression/lifecycle.py",
        "tools/codex_assets/knowledge_hub/regression/lifecycle_2.py",
        "tools/codex_assets/knowledge_hub/regression/lifecycle_3.py",
        "tools/codex_assets/knowledge_hub/regression/lifecycle_4.py",
    )
    assert GOVERNANCE_SOURCE_PATHS == (
        "tools/codex_assets/knowledge_hub/regression/governance.py",
        "tools/codex_assets/knowledge_hub/regression/governance_2.py",
        "tools/codex_assets/knowledge_hub/regression/governance_3.py",
        "tools/codex_assets/knowledge_hub/regression/governance_4.py",
    )
    assert DEFAULT_SOURCE_PATHS == (
        MODEL_SOURCE_PATHS + LIFECYCLE_SOURCE_PATHS + GOVERNANCE_SOURCE_PATHS
    )
    assert all("knowledge-regression.sh" not in path for path in DEFAULT_SOURCE_PATHS)