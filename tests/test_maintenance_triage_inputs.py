"""Incomplete input must not become a successful maintenance receipt."""

import copy

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub import maintenance_triage as triage_module
from tools.codex_assets.knowledge_hub.maintenance_triage import build_maintenance_triage


def _row(**changes):
    row = {"row_type": "stale_item", "item_id": "doc", "path": "governance/doc.md",
           "owner": "owner", "status": "reviewing", "domain": "governance",
           "source_id": "source", "review_after": "2026-09-24", "days_until_review": -1,
           "review_class": "governance-critical", "stale_severity": "needs-review",
           "ai_first_action": "auto-review-packet", "selection_reason": "review_after < as_of"}
    row.update(changes)
    return row


def _review(**changes):
    review = {"status": "report-only", "today": "2026-09-25", "rows": [_row()], "errors": []}
    review.update(changes)
    return review


def _build(review):
    return build_maintenance_triage(review, {"status": "pass"}, {"status": "pass"})


@pytest.mark.parametrize("status", ["fail", "blocked", "pending", "unknown", None, True])
def test_incomplete_or_failed_report_is_not_a_pass_receipt(status):
    with pytest.raises(KnowledgeHubError, match="incomplete or failed"):
        _build(_review(status=status))


@pytest.mark.parametrize("errors", [["read failed"], "", None, False])
def test_error_payload_is_not_silently_ignored(errors):
    with pytest.raises(KnowledgeHubError, match="contains errors"):
        _build(_review(errors=errors))


@pytest.mark.parametrize("today", ["2026-02-30", "20260925", "", 20260925])
def test_evaluation_date_is_valid_and_canonical(today):
    with pytest.raises(KnowledgeHubError, match="YYYY-MM-DD"):
        _build(_review(today=today))


@pytest.mark.parametrize("changes", [
    {"days_until_review": True}, {"days_until_review": "-1"}, {"days_until_review": -2},
    {"review_after": "2026-09-26"}, {"review_after": "invalid"},
    {"item_id": ""}, {"path": ""}, {"owner": []}, {"review_class": []},
    {"row_type": "stale_typo"},
])
def test_malformed_or_inconsistent_stale_rows_fail_closed(changes):
    with pytest.raises(KnowledgeHubError):
        _build(_review(rows=[_row(**changes)]))


def test_exact_duplicate_pending_items_collapse_without_mutating_input():
    review = _review(rows=[_row(), _row()])
    before = copy.deepcopy(review)
    triage, packet = _build(review)
    assert triage["governance"]["count"] == packet["row_count"] == 1
    assert len(packet["rows"]) == 1
    assert review == before
    assert packet["selection_is_authorization"] is False
    assert packet["final_semantic_decision_made"] is False


@pytest.mark.parametrize("change", [{"owner": "other"}, {"path": "different.md"},
    {"review_class": "security-critical"}])
def test_conflicting_duplicates_are_not_arbitrarily_resolved(change):
    with pytest.raises(KnowledgeHubError, match="conflicting"):
        _build(_review(rows=[_row(), _row(**change)]))


def test_distinct_items_sharing_one_path_remain_distinct():
    triage, _ = _build(_review(rows=[_row(), _row(item_id="another")]))
    assert triage["governance"]["count"] == 2


def test_empty_successful_review_is_a_valid_no_change_not_an_eval_pass():
    triage, packet = _build(_review(rows=[]))
    assert triage["governance"]["count"] == 0
    assert packet["status"] == "no-change"
    assert packet["final_semantic_decision_made"] is False


def test_growth_and_health_findings_are_preserved_for_existing_alert_routing():
    triage, _ = build_maintenance_triage(_review(), {"status": "fail"}, {"status": "needs-fix"})
    assert triage["data_growth_status"] == "fail"
    assert triage["health_status"] == "needs-fix"


def test_row_and_field_budgets_are_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(triage_module, "MAX_REVIEW_ROWS", 1)
    with pytest.raises(KnowledgeHubError, match="bounded list"):
        _build(_review(rows=[_row(), _row()]))
    monkeypatch.setattr(triage_module, "MAX_FIELD_CHARS", 3)
    with pytest.raises(KnowledgeHubError, match="bounded string"):
        _build(_review())


@pytest.mark.parametrize("payload", [float("nan"), float("inf"), object()])
def test_non_json_or_nonfinite_input_cannot_get_a_digest(payload):
    with pytest.raises(KnowledgeHubError, match="finite JSON"):
        _build(_review(unknown=payload))


def test_report_byte_budget_is_enforced(monkeypatch):
    monkeypatch.setattr(triage_module, "MAX_REPORT_BYTES", 10)
    with pytest.raises(KnowledgeHubError, match="byte budget"):
        _build(_review())


def test_raw_body_is_not_promoted_into_the_bounded_review_packet():
    review = _review(rows=[_row(body="untrusted full body", suggested_action_zh="rewrite policy")])
    triage, packet = _build(review)
    assert "body" not in packet["rows"][0]
    assert "suggested_action_zh" not in packet["rows"][0]
    assert triage["canonical_write_performed"] is False
