from __future__ import annotations

import pathlib
from unittest import mock

from tools.codex_assets.knowledge_hub.operator_auto_review import build_unique_review_bundle


def _row(item_id="item-1", field="source_refs", fingerprint="sha256:" + "a" * 64):
    return {
        "project_id": "project-1",
        "field": field,
        "proposal_status": "ready-for-governed-review",
        "proposal_ready_for_review": True,
        "proposal_fingerprint": fingerprint,
        "target": {"item_id": item_id},
    }


def _proposal(rows):
    return {
        "projection": "knowledge-operator-binding-proposal-v1",
        "status": "needs-governed-review",
        "read_only": True,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "proposal_only": True,
        "blocked_conflict_count": 0,
        "unmappable_count": 0,
        "rows": rows,
    }


def test_unique_proposals_advance_to_review_bundle_without_authorization(tmp_path):
    plan = {"status": "needs-governed-pr"}
    bundle = {"status": "needs-governed-authorization"}
    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_review.build_binding_patch_plan",
        return_value=plan,
    ) as build_plan, mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_review.build_binding_review_bundle",
        return_value=bundle,
    ):
        result = build_unique_review_bundle(pathlib.Path(tmp_path), _proposal([_row()]))

    assert result["status"] == "needs-governed-authorization"
    assert result["selection_is_authorization"] is False
    assert result["canonical_write_performed"] is False
    assert result["selected_proposal_count"] == 1
    build_plan.assert_called_once()
    build_bundle_args = build_plan.call_args.args
    assert build_bundle_args[2] == ["sha256:" + "a" * 64]


def test_ambiguous_same_target_never_auto_selects(tmp_path):
    result = build_unique_review_bundle(
        pathlib.Path(tmp_path),
        _proposal(
            [
                _row(fingerprint="sha256:" + "a" * 64),
                _row(fingerprint="sha256:" + "b" * 64),
            ]
        ),
    )

    assert result["status"] == "ambiguous"
    assert result["selected_proposal_count"] == 0
    assert result["ambiguous_target_count"] == 1
    assert result["reason_codes"] == ["ambiguous-proposal-target"]


def test_conflicted_proposal_fails_closed(tmp_path):
    proposal = _proposal([_row()])
    proposal["blocked_conflict_count"] = 1

    result = build_unique_review_bundle(pathlib.Path(tmp_path), proposal)

    assert result["status"] == "blocked"
    assert "proposal-conflicts-present" in result["reason_codes"]
