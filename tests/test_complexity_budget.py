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


def test_regression_support_split_reduces_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}

    assert report["status"] == "pass"
    assert report["oversized_module_count"] <= 9
    assert "tools/codex_assets/knowledge_hub/regression/support.py" not in oversized_paths
    assert "tools/codex_assets/knowledge_hub/regression/support_runtime.py" not in oversized_paths
    assert "tools/codex_assets/knowledge_hub/regression/support_fixtures.py" not in oversized_paths


def test_regression_model_split_reduces_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}

    assert report["status"] == "pass"
    assert report["oversized_module_count"] <= 8
    assert "tools/codex_assets/knowledge_hub/regression/model.py" not in oversized_paths
    assert "tools/codex_assets/knowledge_hub/regression/model_index.py" not in oversized_paths


def test_regression_lifecycle_split_reduces_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}
    lifecycle_paths = {
        "tools/codex_assets/knowledge_hub/regression/lifecycle.py",
        "tools/codex_assets/knowledge_hub/regression/lifecycle_2.py",
        "tools/codex_assets/knowledge_hub/regression/lifecycle_3.py",
        "tools/codex_assets/knowledge_hub/regression/lifecycle_4.py",
    }

    assert report["status"] == "pass"
    assert report["oversized_module_count"] <= 7
    assert not lifecycle_paths & oversized_paths


def test_regression_governance_split_reduces_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}
    governance_paths = {
        "tools/codex_assets/knowledge_hub/regression/governance.py",
        "tools/codex_assets/knowledge_hub/regression/governance_2.py",
        "tools/codex_assets/knowledge_hub/regression/governance_3.py",
        "tools/codex_assets/knowledge_hub/regression/governance_4.py",
    }

    assert report["status"] == "pass"
    assert report["oversized_module_count"] <= 6
    assert not governance_paths & oversized_paths


def test_product_gate_split_reduces_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}

    assert report["status"] == "pass"
    assert report["oversized_module_count"] <= 5
    assert "tools/codex_assets/knowledge_hub/product_gate.py" not in oversized_paths
    assert "tools/codex_assets/knowledge_hub/product_gate_support.py" not in oversized_paths
    assert "tools/codex_assets/knowledge_hub/product_gate_parallel.py" not in oversized_paths


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


def test_status_split_reduces_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}
    status_paths = {
        "tools/codex_assets/knowledge_hub/status_cli.py",
        "tools/codex_assets/knowledge_hub/status_common.py",
        "tools/codex_assets/knowledge_hub/status_owner_projection.py",
        "tools/codex_assets/knowledge_hub/status_product_audit.py",
        "tools/codex_assets/knowledge_hub/status_result.py",
        "tools/codex_assets/knowledge_hub/status_review.py",
    }

    assert report["status"] == "pass"
    assert report["oversized_module_count"] <= 3
    assert not status_paths & oversized_paths


def test_index_plan_split_reduces_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}
    index_plan_paths = {
        "tools/codex_assets/knowledge_hub/index_plan_cli.py",
        "tools/codex_assets/knowledge_hub/index_plan_support.py",
        "tools/codex_assets/knowledge_hub/index_plan_review_queue.py",
        "tools/codex_assets/knowledge_hub/index_plan_review_forms.py",
        "tools/codex_assets/knowledge_hub/index_plan_manifest.py",
        "tools/codex_assets/knowledge_hub/index_plan_linking.py",
    }

    assert report["status"] == "pass"
    assert report["oversized_module_count"] <= 2
    assert not index_plan_paths & oversized_paths
