from __future__ import annotations

import json
import pathlib
from typing import Dict, Mapping

from tools.codex_assets.knowledge_hub import operator_actions, operator_state, operator_ui
from tools.codex_assets.knowledge_hub import operator_binding_lifecycle as lifecycle


def _write(root: pathlib.Path, name: str, payload: Mapping[str, object]) -> str:
    path = root / name
    path.write_text(json.dumps(dict(payload), sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def _readonly_payload(projection: str, status: str) -> Dict[str, object]:
    return {
        "schema_version": 1,
        "projection": projection,
        "status": status,
        "read_only": True,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "reason_codes": [],
    }


def _patch_plan_payload() -> Dict[str, object]:
    payload = _readonly_payload(
        lifecycle.PATCH_PLAN_PROJECTION,
        "needs-governed-pr",
    )
    payload.update(
        {
            "selected_proposal_fingerprints": ["sha256:" + "a" * 64],
            "registry_before_sha256": "1" * 64,
            "registry_after_sha256": "2" * 64,
        }
    )
    return payload


def test_no_explicit_input_is_not_observed_not_failed(tmp_path: pathlib.Path) -> None:
    projection = lifecycle.build_binding_lifecycle_projection(tmp_path)

    assert projection["status"] == "not-observed"
    assert projection["trust_state"] == "not-observed"
    assert projection["observed_stage_count"] == 0
    assert projection["next_execution_class"] == ""
    assert projection["automatic_execution_enabled"] is False
    assert projection["reason_codes"] == ["no-explicit-lifecycle-observation-input"]


def test_patch_plan_routes_to_existing_machine_after_prerequisite_class(
    tmp_path: pathlib.Path,
) -> None:
    path = _write(tmp_path, "patch-plan.json", _patch_plan_payload())

    projection = lifecycle.build_binding_lifecycle_projection(
        tmp_path,
        {"patch_plan": path},
    )
    actions = operator_actions.lifecycle_actions(projection)

    assert projection["status"] == "needs-governed-pr"
    assert projection["current_stage"] == "patch_plan"
    assert projection["next_execution_class"] == "machine-after-prerequisite"
    assert projection["automatic_execution_enabled"] is False
    assert len(actions) == 1
    assert actions[0]["scope"] == "lifecycle"
    assert actions[0]["execution_class"] == "machine-after-prerequisite"
    assert actions[0]["automatic_execution_enabled"] is False


def test_cross_stage_identity_mismatch_fails_closed(tmp_path: pathlib.Path) -> None:
    review = _readonly_payload(
        lifecycle.REVIEW_PROJECTION,
        "needs-governed-authorization",
    )
    review.update(
        {
            "review_bundle_fingerprint": "sha256:" + "b" * 64,
            "patch_plan_fingerprint": "sha256:" + "c" * 64,
            "registry_before_sha256": "1" * 64,
            "registry_after_sha256": "2" * 64,
        }
    )
    authorization = _readonly_payload(
        lifecycle.AUTHORIZATION_PROJECTION,
        "ready-for-governed-apply",
    )
    authorization.update(
        {
            "review_bundle_fingerprint": "sha256:" + "f" * 64,
            "patch_plan_fingerprint": "sha256:" + "c" * 64,
            "registry_before_sha256": "1" * 64,
            "registry_after_sha256": "2" * 64,
            "authorization_fingerprint": "sha256:" + "d" * 64,
        }
    )
    review_path = _write(tmp_path, "review.json", review)
    authorization_path = _write(tmp_path, "authorization.json", authorization)

    projection = lifecycle.build_binding_lifecycle_projection(
        tmp_path,
        {
            "review_bundle": review_path,
            "authorization": authorization_path,
        },
    )

    assert projection["status"] == "observation-error"
    assert projection["trust_state"] == "fail-closed-observation"
    assert projection["next_execution_class"] == "governance-review"
    assert "review-authorization-review-bundle-fingerprint-chain-mismatch" in projection[
        "reason_codes"
    ]


def test_real_apply_result_is_revalidated_by_existing_receipt_verifier(
    monkeypatch,
    tmp_path: pathlib.Path,
) -> None:
    apply_payload = {
        "schema_version": 1,
        "projection": lifecycle.APPLY_PROJECTION,
        "status": "applied",
        "read_only": False,
        "canonical_write_performed": True,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "authorization_fingerprint": "sha256:" + "a" * 64,
        "reason_codes": ["explicit-governed-apply-completed"],
    }
    apply_path = _write(tmp_path, "apply.json", apply_payload)
    calls = []

    def fake_receipt(root: pathlib.Path, payload: Mapping[str, object]):
        calls.append((root, payload))
        return {
            "schema_version": 1,
            "projection": "knowledge-operator-binding-apply-receipt-v1",
            "status": "verified-current-post-apply-state",
            "reason_codes": ["separate-governed-rollback-required"],
        }

    monkeypatch.setattr(lifecycle, "build_governed_apply_receipt", fake_receipt)

    projection = lifecycle.build_binding_lifecycle_projection(
        tmp_path,
        {"apply": apply_path},
    )

    assert projection["status"] == "verified-current-post-apply-state"
    assert projection["current_stage"] == "apply"
    assert projection["next_execution_class"] == ""
    assert projection["reason_codes"] == ["separate-governed-rollback-required"]
    assert [row["stage"] for row in projection["stages"]] == [
        "apply",
        "apply_receipt",
    ]
    assert projection["stages"][-1]["trust_state"] == "revalidated-by-apply-receipt"
    assert len(calls) == 1
    assert calls[0][0] == tmp_path
    assert calls[0][1]["status"] == "applied"


def test_completed_rollback_revalidates_full_lifecycle_without_reapply_action(
    monkeypatch,
    tmp_path: pathlib.Path,
) -> None:
    apply_payload = {
        "schema_version": 1,
        "projection": lifecycle.APPLY_PROJECTION,
        "status": "applied",
        "read_only": False,
        "canonical_write_performed": True,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "authorization_fingerprint": "sha256:" + "a" * 64,
        "transaction": {"transaction_id": "kh-operator-binding-apply-" + "a" * 16},
        "reason_codes": ["explicit-governed-apply-completed"],
    }
    rollback_payload = {
        "schema_version": 1,
        "projection": lifecycle.ROLLBACK_PROJECTION,
        "status": "rolled-back",
        "read_only": False,
        "canonical_write_performed": True,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "apply_authorization_fingerprint": "sha256:" + "a" * 64,
        "apply_transaction_id": "kh-operator-binding-apply-" + "a" * 16,
        "reason_codes": ["explicit-governed-rollback-completed"],
    }
    apply_path = _write(tmp_path, "apply.json", apply_payload)
    rollback_path = _write(tmp_path, "rollback.json", rollback_payload)

    monkeypatch.setattr(
        lifecycle,
        "build_governed_apply_receipt",
        lambda root, payload: {
            "schema_version": 1,
            "projection": "knowledge-operator-binding-apply-receipt-v1",
            "status": "post-apply-state-drift",
            "reason_codes": ["rollback-blocked-current-registry-drift"],
        },
    )
    monkeypatch.setattr(
        lifecycle,
        "build_governed_rollback_receipt",
        lambda root, apply, rollback: {
            "schema_version": 1,
            "projection": "knowledge-operator-binding-rollback-receipt-v1",
            "status": "verified-current-post-rollback-state",
            "reason_codes": ["governed-rollback-lifecycle-verified"],
        },
    )

    projection = lifecycle.build_binding_lifecycle_projection(
        tmp_path,
        {"apply": apply_path, "rollback": rollback_path},
    )
    actions = operator_actions.lifecycle_actions(projection)

    assert projection["status"] == "verified-current-post-rollback-state"
    assert projection["current_stage"] == "rollback"
    assert projection["next_execution_class"] == ""
    assert projection["reason_codes"] == ["governed-rollback-lifecycle-verified"]
    assert [row["stage"] for row in projection["stages"]] == [
        "apply",
        "apply_receipt",
        "rollback",
        "rollback_receipt",
    ]
    assert actions == []


def test_unknown_input_key_is_not_silently_ignored(tmp_path: pathlib.Path) -> None:
    projection = lifecycle.build_binding_lifecycle_projection(
        tmp_path,
        {"invented_stage": "anything.json"},
    )

    assert projection["status"] == "observation-error"
    assert projection["reason_codes"] == ["unknown-lifecycle-input:invented_stage"]
    assert projection["automatic_execution_enabled"] is False


def test_operator_state_merges_lifecycle_responsibility_into_existing_queue(
    monkeypatch,
    tmp_path: pathlib.Path,
) -> None:
    path = _write(tmp_path, "patch-plan.json", _patch_plan_payload())
    monkeypatch.setattr(
        operator_state,
        "_project_readiness",
        lambda root: {
            "project_count": 0,
            "structural_ready_count": 0,
            "source_mapping_ready_count": 0,
            "owner_boundary_ready_count": 0,
            "evidence_field_complete_count": 0,
            "evidence_ready_count": 0,
            "rows": [],
        },
    )
    monkeypatch.setattr(
        operator_state,
        "_status_summary",
        lambda root: {"status": "needs-review", "next_actions_zh": []},
    )
    monkeypatch.setattr(
        operator_state,
        "_external_state",
        lambda root: {"status": "pass", "open_count": 0, "open_gaps": []},
    )
    monkeypatch.setattr(
        operator_state,
        "_terminal_state",
        lambda root: {"status": "needs-review", "terminal": False},
    )
    monkeypatch.setattr(
        operator_state,
        "build_discovery_projection",
        lambda root, queue: {"status": "pass", "rows": []},
    )

    state = operator_state.build_operator_state(
        tmp_path,
        lifecycle_inputs={"patch_plan": path},
    )

    assert state["binding_lifecycle"]["current_stage"] == "patch_plan"
    lifecycle_actions = [
        row for row in state["action_queue"]["actions"] if row["scope"] == "lifecycle"
    ]
    assert len(lifecycle_actions) == 1
    assert lifecycle_actions[0]["execution_class"] == "machine-after-prerequisite"
    assert state["action_queue"]["automatic_execution_enabled"] is False


def test_ui_accepts_explicit_lifecycle_files_and_renders_trust_state() -> None:
    args = operator_ui.build_parser().parse_args(
        [
            ".",
            "--binding-proposal",
            "proposal.json",
            "--binding-patch-plan",
            "plan.json",
            "--binding-review-bundle",
            "review.json",
            "--binding-authorization-result",
            "authorization.json",
            "--binding-apply-result",
            "apply.json",
            "--binding-rollback-result",
            "rollback.json",
        ]
    )
    assert operator_ui._lifecycle_inputs(args) == {
        "proposal": "proposal.json",
        "patch_plan": "plan.json",
        "review_bundle": "review.json",
        "authorization": "authorization.json",
        "apply": "apply.json",
        "rollback": "rollback.json",
    }

    page = operator_ui.render_dashboard(
        {
            "status": "needs-review",
            "readiness": {},
            "action_queue": {"actions": []},
            "discovery": {},
            "binding_lifecycle": {
                "current_stage": "review_bundle",
                "status": "needs-governed-authorization",
                "stages": [
                    {
                        "stage": "review_bundle",
                        "status": "needs-governed-authorization",
                        "trust_state": "observed-output-not-revalidated",
                        "reason_codes": ["<script>alert(1)</script>"],
                    }
                ],
            },
            "external_closure": {},
            "terminal_closure": {"terminal": False, "status": "needs-review"},
            "next_actions_zh": [],
        }
    )
    assert "Governed Binding Lifecycle" in page
    assert "review_bundle" in page
    assert "observed-output-not-revalidated" in page
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
