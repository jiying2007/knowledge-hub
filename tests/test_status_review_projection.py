from tools.codex_assets.knowledge_hub.status_projection import status_summary


def test_status_summary_keeps_ai_and_human_completion_separate():
    payload = {
        "status": "needs-review",
        "review_queues": {
            "status": "needs-human-review",
            "summary": {
                "total_pending_count": 7,
                "ai_generated_pending_count": 7,
                "ai_delegated_closed_count": 20,
                "human_reviewed_count": 364,
            },
        },
        "strict_blockers": [{"id": "review-queue-pending-product", "count": 7}],
    }
    result = status_summary(payload)
    assert result["review_queues"]["ai_delegated_closed_count"] == 20
    assert result["review_queues"]["human_reviewed_count"] == 364
    assert result["review_queues"]["total_pending_count"] == 7
    assert result["status"] == "needs-review"
    assert result["strict_blockers"][0]["count"] == 7


def test_status_summary_defaults_completion_counts_for_old_payloads():
    result = status_summary({})
    assert result["review_queues"]["ai_delegated_closed_count"] == 0
    assert result["review_queues"]["human_reviewed_count"] == 0
