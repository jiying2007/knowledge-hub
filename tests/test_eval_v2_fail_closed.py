"""Regression cases for #109/F01; fixtures are not production qualification."""

import copy
import json

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.eval_v2 import (
    compare_baseline,
    load_dataset,
    metric_summary,
    migrate_v1_cases,
    validate_case,
)


def result(case_id="a", **changes):
    value = {"id": case_id, "passed": True, "criticality": "critical", "latency_ms": 10.0}
    value.update(changes)
    return value


def case(**changes):
    value = {
        "id": "a", "query": "断电 recovery", "query_class": "known-answer",
        "language": "mixed", "criticality": "critical", "expected_ids": ["doc"],
        "forbidden_ids": [], "principal": {"principal_id": "alice"}, "scope": "team-general",
    }
    value.update(changes)
    return value


@pytest.mark.parametrize("rows", [[], [result(), result()]])
def test_empty_or_duplicate_results_are_rejected(rows):
    with pytest.raises(KnowledgeHubError):
        metric_summary(rows)


@pytest.mark.parametrize("verdict", ["false", "true", 0, 1, None, [], {}])
def test_verdict_requires_a_real_boolean(verdict):
    with pytest.raises(KnowledgeHubError, match="boolean"):
        metric_summary([result(passed=verdict)])


@pytest.mark.parametrize("latency", [None, "10", True, -1, float("nan"), float("inf")])
def test_latency_requires_a_finite_nonnegative_number(latency):
    with pytest.raises(KnowledgeHubError):
        metric_summary([result(latency_ms=latency)])


@pytest.mark.parametrize("field", ["id", "passed", "latency_ms"])
def test_missing_execution_fields_cannot_be_defaulted_to_success(field):
    row = result()
    del row[field]
    with pytest.raises(KnowledgeHubError):
        metric_summary([row])


@pytest.mark.parametrize("state", ["skipped", "pending", "failed", None])
def test_explicit_incomplete_execution_is_rejected(state):
    with pytest.raises(KnowledgeHubError, match="not completed"):
        metric_summary([result(execution_status=state)])


def test_expected_coverage_and_case_identity_are_enforced():
    with pytest.raises(KnowledgeHubError, match="coverage"):
        metric_summary([result()], expected_case_ids=["a", "b"])
    baseline = metric_summary([result("a")])
    candidate = metric_summary([result("b")])
    comparison = compare_baseline(baseline, candidate)
    assert comparison["status"] == "fail"
    assert "case-coverage-mismatch" in comparison["failures"]


def test_same_case_set_in_different_order_is_comparable():
    baseline = metric_summary([result("a"), result("b")])
    candidate = metric_summary([result("b"), result("a")])
    assert compare_baseline(baseline, candidate)["status"] == "pass"


@pytest.mark.parametrize("bad", [{}, {"case_count": 0, "pass_rate": 1.0, "p95_ms": 0.0}])
def test_empty_or_legacy_unbound_summaries_never_compare_as_pass(bad):
    good = metric_summary([result()])
    assert compare_baseline(good, bad)["status"] == "fail"
    assert compare_baseline(bad, good)["status"] == "fail"


@pytest.mark.parametrize("changes", [
    {"case_count": True}, {"case_count": 2}, {"case_ids": ["a", "a"]},
    {"case_set_sha256": "0" * 64}, {"pass_rate": "1.0"}, {"pass_rate": 1.1},
    {"pass_rate": float("nan")}, {"p95_ms": float("inf")}, {"p95_ms": -1},
    {"critical_failure_ids": ["not-evaluated"]},
])
def test_forged_summary_fields_fail_closed(changes):
    baseline = metric_summary([result()])
    candidate = copy.deepcopy(baseline)
    candidate.update(changes)
    assert compare_baseline(baseline, candidate)["status"] == "fail"


def test_real_failure_regression_and_new_critical_ids_are_distinct():
    baseline = metric_summary([result("a", passed=False), result("b")])
    candidate = metric_summary([result("a", passed=False), result("b", passed=False, latency_ms=30)])
    comparison = compare_baseline(baseline, candidate)
    assert comparison["status"] == "fail"
    assert set(comparison["failures"]) == {
        "pass-rate-regression", "p95-regression", "critical-case-failure",
    }
    assert comparison["newly_failing_critical_ids"] == ["b"]


def test_optional_dataset_and_evaluator_bindings_cannot_silently_drift():
    baseline = metric_summary([result()])
    candidate = copy.deepcopy(baseline)
    baseline["dataset_sha256"] = "a" * 64
    assert compare_baseline(baseline, candidate)["status"] == "fail"
    candidate["dataset_sha256"] = "a" * 64
    baseline["source_revision"] = "old-source"
    candidate["source_revision"] = "new-source"
    assert compare_baseline(baseline, candidate)["status"] == "pass"
    candidate["evaluator_revision"] = "different-evaluator"
    assert compare_baseline(baseline, candidate)["status"] == "fail"


@pytest.mark.parametrize("drop,ratio", [(float("nan"), 1.2), (0, float("inf")), (-0.1, 1.2), (0, True)])
def test_invalid_thresholds_do_not_disable_regression_checks(drop, ratio):
    summary = metric_summary([result()])
    with pytest.raises(KnowledgeHubError):
        compare_baseline(summary, summary, maximum_pass_rate_drop=drop, maximum_p95_regression_ratio=ratio)


def test_loader_rejects_empty_duplicate_and_oversized_jsonl(tmp_path):
    path = tmp_path / "cases.jsonl"
    for text in ("\n", (json.dumps(case()) + "\n") * 2, " " * (1024 * 1024 + 1)):
        path.write_text(text, encoding="utf-8")
        with pytest.raises(KnowledgeHubError):
            load_dataset(path)
    path.write_text(json.dumps(case()) + "\n", encoding="utf-8")
    dataset = load_dataset(path)
    assert dataset["case_count"] == 1
    assert len(dataset["dataset_sha256"]) == 64


@pytest.mark.parametrize("changes", [
    {"id": 1}, {"query": None}, {"expected_ids": [1]}, {"forbidden_ids": ["x", "x"]},
    {"criticality": []}, {"scope": {}}, {"principal": []}, {"expected_zero_hit": "false"},
])
def test_dataset_field_types_are_not_coerced(changes):
    assert validate_case(case(**changes))


def test_migration_does_not_convert_string_false_to_true():
    with pytest.raises(KnowledgeHubError, match="boolean"):
        migrate_v1_cases({"cases": [{"id": "a", "expected_zero_hit": "false"}]})
