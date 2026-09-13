import json
import subprocess

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.complexity_budget import evaluate_complexity_budget


def _write_budget_policy(root, *, module_limit=800, function_limit=80, legacy_caps=None):
    registry = root / "registry"
    registry.mkdir(exist_ok=True)
    (registry / "engineering-budgets.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "python": {
                    "new_module_max_lines": module_limit,
                    "new_function_max_lines": function_limit,
                    "legacy_module_line_caps": legacy_caps or {},
                },
                "commands": {"wrapper_baseline": 0},
            }
        ),
        encoding="utf-8",
    )


def _long_function(name="legacy_function", body_lines=90):
    return "def {}():\n{}\n".format(
        name,
        "\n".join("    value = {}".format(index) for index in range(body_lines)),
    )


def test_complexity_budget_counts_all_oversized_modules_explicitly(tmp_path):
    package = tmp_path / "tools/codex_assets/knowledge_hub"
    package.mkdir(parents=True)
    (package / "capped.py").write_text("\n".join(["x = 1"] * 10) + "\n", encoding="utf-8")
    (package / "uncapped.py").write_text("\n".join(["x = 1"] * 6) + "\n", encoding="utf-8")
    _write_budget_policy(
        tmp_path,
        module_limit=5,
        legacy_caps={"tools/codex_assets/knowledge_hub/capped.py": 20},
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


def test_complexity_budget_empty_git_index_is_zero_debt_baseline_snapshot(tmp_path):
    package = tmp_path / "tools/codex_assets/knowledge_hub"
    package.mkdir(parents=True)
    (package / "existing.py").write_text(_long_function(), encoding="utf-8")
    _write_budget_policy(tmp_path)
    subprocess.run(
        ["git", "init", "-q"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    report = evaluate_complexity_budget(tmp_path)

    assert report["status"] == "pass"
    assert report["regressions"] == []
    row = next(row for row in report["modules"] if row["path"].endswith("existing.py"))
    assert row["tracked_baseline"] is True
    assert row["oversized_function_count"] == 1


def test_complexity_budget_nonempty_git_index_keeps_untracked_new_code_strict(tmp_path):
    package = tmp_path / "tools/codex_assets/knowledge_hub"
    package.mkdir(parents=True)
    (package / "baseline.py").write_text(_long_function("baseline_function"), encoding="utf-8")
    (package / "new_module.py").write_text(_long_function("new_function"), encoding="utf-8")
    _write_budget_policy(tmp_path)
    subprocess.run(
        ["git", "init", "-q"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    subprocess.run(
        ["git", "add", "tools/codex_assets/knowledge_hub/baseline.py"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    report = evaluate_complexity_budget(tmp_path)

    assert report["status"] == "fail"
    assert any(
        row["type"] == "new-function-size"
        and row["path"] == "tools/codex_assets/knowledge_hub/new_module.py"
        and row["function"] == "new_function"
        for row in report["regressions"]
    )
    baseline = next(row for row in report["modules"] if row["path"].endswith("baseline.py"))
    new_module = next(row for row in report["modules"] if row["path"].endswith("new_module.py"))
    assert baseline["tracked_baseline"] is True
    assert new_module["tracked_baseline"] is False


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


def test_owner_gates_split_reduces_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}
    owner_gates_paths = {
        "tools/codex_assets/knowledge_hub/owner_gates_cli.py",
        "tools/codex_assets/knowledge_hub/owner_gates_support.py",
        "tools/codex_assets/knowledge_hub/owner_gates_evidence.py",
        "tools/codex_assets/knowledge_hub/owner_gates_forms.py",
        "tools/codex_assets/knowledge_hub/owner_gates_dispatch.py",
    }

    assert report["status"] == "pass"
    assert report["oversized_module_count"] <= 1
    assert not owner_gates_paths & oversized_paths


def test_check_split_eliminates_repository_oversized_module_debt():
    report = evaluate_complexity_budget(repository_root())
    oversized_paths = {row["path"] for row in report["oversized_modules"]}
    check_paths = {
        "tools/codex_assets/knowledge_hub/check_cli.py",
        "tools/codex_assets/knowledge_hub/check_validation_pre.py",
        "tools/codex_assets/knowledge_hub/check_validation_registry.py",
        "tools/codex_assets/knowledge_hub/check_validation_governance.py",
        "tools/codex_assets/knowledge_hub/check_validation_post.py",
    }

    assert report["status"] == "pass"
    assert report["oversized_module_count"] == 0
    assert report["regressions"] == []
    assert not check_paths & oversized_paths
