import json

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.complexity_budget import evaluate_complexity_budget


def test_complexity_budget_counts_all_oversized_modules_explicitly(tmp_path):
    package = tmp_path / "tools/codex_assets/knowledge_hub"
    package.mkdir(parents=True)
    (package / "capped.py").write_text("\n".join(["x = 1"] * 10) + "\n", encoding="utf-8")
    (package / "uncapped.py").write_text("\n".join(["x = 1"] * 6) + "\n", encoding="utf-8")
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "engineering-budgets.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "python": {
                    "new_module_max_lines": 5,
                    "new_function_max_lines": 80,
                    "legacy_module_line_caps": {
                        "tools/codex_assets/knowledge_hub/capped.py": 20
                    },
                },
                "commands": {"wrapper_baseline": 0},
            }
        ),
        encoding="utf-8",
    )

    report = evaluate_complexity_budget(tmp_path)

    assert report["status"] == "pass"
    assert report["oversized_module_count"] == 2
    assert [row["path"] for row in report["oversized_modules"]] == [
        "tools/codex_assets/knowledge_hub/capped.py",
        "tools/codex_assets/knowledge_hub/uncapped.py",
    ]
    # Legacy caps prevent growth regressions; they do not remove an oversized
    # tracked module from the report-only legacy attention set.
    assert report["legacy_attention_count"] == 2
    assert [row["path"] for row in report["legacy_attention"]] == [
        "tools/codex_assets/knowledge_hub/capped.py",
        "tools/codex_assets/knowledge_hub/uncapped.py",
    ]


def test_context_split_reduces_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}

    assert report["status"] == "pass"
    assert report["oversized_module_count"] <= 10
    assert "tools/codex_assets/knowledge_hub/context.py" not in oversized_paths
    assert "tools/codex_assets/knowledge_hub/context_support.py" not in oversized_paths
    assert "tools/codex_assets/knowledge_hub/context_assembly.py" not in oversized_paths
