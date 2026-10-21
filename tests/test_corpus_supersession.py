"""Regression for historical supersession provenance, not authority promotion."""
from __future__ import annotations

import copy

from tools.codex_assets.knowledge_hub.corpus_supersession import annotate_supersession


def _row(identity, predecessor="", *, domain="projects/demo", kind="decision",
         status="reviewing", private=False):
    return {
        "id": identity, "kind": kind, "status": "personal" if private else status,
        "domain": "notes" if private else domain,
        "lane": "personal-excluded" if private else "P2-candidate-review",
        "signals": ["personal-excluded"] if private else ["candidate-needs-independent-review"],
        "body": {"status": "read", "supersedes_candidate": predecessor,
                 "supersedes_invalid": False},
    }


def test_explicit_chain_keeps_history_without_owner_or_lifecycle_mutation():
    rows = [_row("old"), _row("v2", "old"), _row("v3", "v2")]
    before = copy.deepcopy(rows)
    audit = annotate_supersession(rows)
    assert audit["declared_link_count"] == 2
    assert audit["candidate_history_count"] == 2
    assert audit["status"] == "report-only"
    assert audit["automatic_delete_enabled"] is False
    assert audit["automatic_status_change_enabled"] is False
    assert audit["owner_approval_performed"] is False
    assert "superseded-candidate-provenance" in rows[0]["signals"]
    assert rows[0]["supersession"]["candidate_successors"] == ["v2"]
    assert rows[1]["supersession"]["candidate_successors"] == ["v3"]
    assert rows[2]["supersession"]["predecessor_id"] == "v2"
    assert [x["status"] for x in rows] == [x["status"] for x in before]


def test_fork_and_cycle_fail_closed_without_deleting_candidates():
    fork = [_row("root"), _row("branch-a", "root"), _row("branch-b", "root")]
    result = annotate_supersession(fork)
    assert result["blocking_signal_counts"]["supersession-fork"] == 3
    assert result["candidate_history_count"] == 0
    cyclic = [_row("a", "b"), _row("b", "a")]
    audit = annotate_supersession(cyclic)
    assert audit["cycle_item_count"] == 2
    assert audit["candidate_history_count"] == 0
    assert all("supersession-cycle" in x["signals"] for x in cyclic)


def test_missing_cross_scope_invalid_and_active_target_fail_closed():
    missing = [_row("child", "missing")]
    assert annotate_supersession(missing)["blocking_signal_counts"] == {
        "supersession-predecessor-missing": 1
    }
    crossing = [_row("parent"), _row("child", "parent", domain="projects/other")]
    assert annotate_supersession(crossing)["blocking_signal_counts"] == {
        "supersession-cross-scope": 1
    }
    invalid = [_row("bad")]
    invalid[0]["body"]["supersedes_invalid"] = True
    assert annotate_supersession(invalid)["blocking_signal_counts"] == {
        "supersession-declaration-invalid": 1
    }
    active = [_row("current", status="active"), _row("candidate", "current")]
    assert annotate_supersession(active)["blocking_signal_counts"] == {
        "supersession-active-requires-owner": 1
    }
    assert active[0]["status"] == "active"


def test_personal_item_is_never_a_visible_supersession_identity():
    rows = [_row("private", private=True), _row("child", "private")]
    result = annotate_supersession(rows)
    assert result["visible_count"] == 1
    assert "supersession-predecessor-missing" in rows[1]["signals"]
    assert "supersession" not in rows[0]
    assert rows[0]["signals"] == ["personal-excluded"]



def test_supersession_execution_roots_are_security_critical():
    import json
    from pathlib import Path
    from tools.codex_assets.knowledge_hub.review_risk import classify_review_risk

    root = Path(__file__).resolve().parents[1]
    policy = json.loads((root / "registry/review-risk-policy.json").read_text(
        encoding="utf-8"
    ))
    for path in (
        "tools/codex_assets/knowledge_hub/corpus_review.py",
        "tools/codex_assets/knowledge_hub/corpus_optimization.py",
        "tools/codex_assets/knowledge_hub/corpus_supersession.py",
    ):
        assert classify_review_risk(policy, path)["review_class"] == "security-critical"
