import copy

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.maintenance_notification import (
    critical_notification_decision,
)


def _inputs():
    return (
        {"security": {"rows": [
            {"item_id": "sec-b", "review_after": "2026-09-02", "selection_reason": "stale"},
            {"item_id": "sec-a", "review_after": "2026-09-01", "selection_reason": "stale"},
        ]}},
        {"status": "pass", "regressions": [
            {"type": "data-growth-hard-cap", "path": "registry/items.jsonl", "reason": "size"},
            {"type": "warning", "path": "ignored", "reason": "ignored"},
        ]},
        {"errors": []},
    )


def test_notification_identity_is_order_independent():
    triage, growth, review = _inputs()
    first = critical_notification_decision(triage, growth, review)
    triage["security"]["rows"].reverse()
    growth["regressions"].reverse()
    second = critical_notification_decision(triage, growth, review)
    assert first == second
    assert first["human_required"] is True
    assert first["notification_fingerprint"].startswith("sha256:")


@pytest.mark.parametrize("field", ["ordinary", "governance", "health_status", "run_url"])
def test_noncritical_changes_do_not_churn_notification_identity(field):
    triage, growth, review = _inputs()
    before = critical_notification_decision(triage, growth, review)
    triage[field] = {"volatile": "value"}
    after = critical_notification_decision(triage, growth, review)
    assert after == before


def test_security_change_rotates_fingerprint():
    triage, growth, review = _inputs()
    before = critical_notification_decision(triage, growth, review)
    triage["security"]["rows"][0]["review_after"] = "2026-09-03"
    assert critical_notification_decision(triage, growth, review)["notification_fingerprint"] != before["notification_fingerprint"]


def test_hard_cap_change_rotates_fingerprint():
    triage, growth, review = _inputs()
    before = critical_notification_decision(triage, growth, review)
    growth["regressions"][0]["reason"] = "count"
    assert critical_notification_decision(triage, growth, review)["notification_fingerprint"] != before["notification_fingerprint"]


def test_review_policy_error_routes_to_human():
    triage = {"security": {"rows": []}}
    growth = {"status": "pass", "regressions": []}
    result = critical_notification_decision(triage, growth, {"errors": ["invalid review policy"]})
    assert result["human_required"] is True
    assert result["policy_error_count"] == 1


def test_growth_failure_routes_to_human_even_without_regression_row():
    result = critical_notification_decision(
        {"security": {"rows": []}}, {"status": "fail", "regressions": []}, {"errors": []}
    )
    assert result["human_required"] is True
    assert result["policy_error_count"] == 1


def test_clean_state_has_stable_nonhuman_fingerprint():
    result = critical_notification_decision(
        {"security": {"rows": []}}, {"status": "pass", "regressions": []}, {"errors": []}
    )
    assert result["human_required"] is False
    assert len(result["notification_fingerprint"]) == 71


@pytest.mark.parametrize(
    "triage,growth,review",
    [
        ({}, {"status": "pass", "regressions": []}, {"errors": []}),
        ({"security": {"rows": "bad"}}, {"status": "pass", "regressions": []}, {"errors": []}),
        ({"security": {"rows": []}}, {"status": "pass"}, {"errors": []}),
        ({"security": {"rows": []}}, {"status": "pass", "regressions": []}, {}),
        ({"security": {"rows": [{"item_id": 1, "review_after": "", "selection_reason": ""}]}}, {"status": "pass", "regressions": []}, {"errors": []}),
    ],
)
def test_malformed_inputs_fail_closed(triage, growth, review):
    with pytest.raises(KnowledgeHubError):
        critical_notification_decision(triage, growth, review)


def test_duplicate_security_rows_are_rejected():
    triage, growth, review = _inputs()
    triage["security"]["rows"].append(copy.deepcopy(triage["security"]["rows"][0]))
    with pytest.raises(KnowledgeHubError, match="duplicates"):
        critical_notification_decision(triage, growth, review)
