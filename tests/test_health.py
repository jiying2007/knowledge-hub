from tools.codex_assets.knowledge_hub.health import _is_body_markdown, _review_queue


def test_fast_body_coverage_matches_orphan_body_boundary():
    assert _is_body_markdown("projects/xcrz-sigmastar-demo/current/runbooks/debug.md") is True
    assert _is_body_markdown("projects/pcr02-ssc305/README.md") is False
    assert _is_body_markdown("templates/inbox-note.md") is False
    assert _is_body_markdown("docs/goals/knowledge-hub-final-state.md") is False


def test_fast_review_queue_excludes_archived_and_active_items():
    rows = [
        {"status": "reviewing", "generated_by_ai": True, "human_review_decision": ""},
        {"status": "archived", "generated_by_ai": True, "human_review_decision": ""},
        {"status": "active", "generated_by_ai": True, "human_review_decision": ""},
        {
            "status": "reviewing",
            "kind": "external-source-note",
            "generated_by_ai": False,
            "human_review_decision": "",
        },
    ]

    payload = _review_queue(rows)

    assert payload["pending_total"] == 2
    assert payload["ai_generated_pending"] == 1
    assert payload["external_source_pending"] == 1
    assert payload["active_or_promotion_blocker_count"] == 1
