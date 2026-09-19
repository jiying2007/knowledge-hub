import copy

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.maintenance_triage import (
    build_maintenance_triage,
)
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def _review():
    return {
        "status": "report-only",
        "today": "2026-09-19",
        "rows": [
            {
                "row_type": "stale_item",
                "item_id": "ordinary-a",
                "path": "projects/a.md",
                "owner": "ai",
                "status": "reviewing",
                "domain": "project",
                "source_id": "source-a",
                "review_after": "2026-09-01",
                "days_until_review": -18,
                "review_class": "ordinary",
                "stale_severity": "warning",
                "ai_first_action": "auto-triage",
                "selection_reason": "review_after < as_of",
            },
            {
                "row_type": "stale_item",
                "item_id": "governance-a",
                "path": "governance/a.md",
                "owner": "governance-owner",
                "status": "reviewing",
                "domain": "governance",
                "source_id": "source-g",
                "review_after": "2026-09-02",
                "days_until_review": -17,
                "review_class": "governance-critical",
                "stale_severity": "needs-review",
                "ai_first_action": "auto-review-packet",
                "selection_reason": "review_after < as_of",
            },
            {
                "row_type": "stale_item",
                "item_id": "security-a",
                "path": "SECURITY.md",
                "owner": "security-owner",
                "status": "reviewing",
                "domain": "governance",
                "source_id": "source-s",
                "review_after": "2026-09-03",
                "days_until_review": -16,
                "review_class": "security-critical",
                "stale_severity": "blocked",
                "ai_first_action": "human-review-required",
                "selection_reason": "review_after < as_of",
            },
            {
                "row_type": "near_due_item",
                "item_id": "future-a",
                "review_class": "ordinary",
            },
        ],
        "errors": [],
    }


def test_maintenance_triage_materializes_machine_owned_actions():
    triage, packet = build_maintenance_triage(
        _review(),
        {"status": "pass"},
        {"status": "pass"},
    )

    assert triage["read_only"] is True
    assert triage["canonical_write_performed"] is False
    assert triage["ordinary"]["action"] == "machine-triaged-no-semantic-write"
    assert triage["ordinary"]["count"] == 1
    assert triage["governance"]["action"] == "machine-review-packet-generated"
    assert triage["governance"]["count"] == 1
    assert triage["security"]["action"] == "human-review-required"
    assert triage["security"]["count"] == 1

    assert packet["status"] == "ready"
    assert packet["selection_is_authorization"] is False
    assert packet["final_semantic_decision_made"] is False
    assert packet["row_count"] == 1
    assert packet["rows"][0]["item_id"] == "governance-a"


def test_maintenance_triage_is_deterministic_and_bounded():
    review = _review()
    first = build_maintenance_triage(
        review,
        {"status": "pass", "data_growth_attention_count": 0},
        {"status": "pass"},
    )
    second = build_maintenance_triage(
        copy.deepcopy(review),
        {"data_growth_attention_count": 0, "status": "pass"},
        {"status": "pass"},
    )

    assert first == second
    triage, packet = first
    assert "suggested_action_zh" not in triage["ordinary"]["rows"][0]
    assert "body" not in triage["ordinary"]["rows"][0]
    assert triage["input_digests"]["review"].startswith("sha256:")
    assert packet["input_digests"] == triage["input_digests"]


def test_maintenance_triage_rejects_unknown_review_class():
    review = _review()
    review["rows"][0]["review_class"] = "unexpected"

    with pytest.raises(KnowledgeHubError, match="unsupported review class"):
        build_maintenance_triage(review, {"status": "pass"}, {"status": "pass"})


def test_maintenance_and_private_ratchet_cores_are_in_mypy_surface():
    from pathlib import Path

    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert '"tools/codex_assets/knowledge_hub/maintenance_triage.py"' in pyproject
    assert (
        '"tools/codex_assets/knowledge_hub/repository_private_ratchet.py"'
        in pyproject
    )


def test_maintenance_triage_outputs_match_catalog_contracts():
    triage, packet = build_maintenance_triage(
        _review(),
        {"status": "pass"},
        {"status": "pass"},
    )

    root = repository_root()
    assert validate_instance(root, "maintenance-triage-v1", triage)["status"] == "pass"
    assert (
        validate_instance(root, "governance-review-packet-v1", packet)["status"]
        == "pass"
    )
