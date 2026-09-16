from __future__ import annotations

import hashlib
import pathlib

from tools.codex_assets.knowledge_hub import operator_binding_governed_apply as governed_apply
from tools.codex_assets.knowledge_hub.common import encode_jsonl, file_sha256
from tools.codex_assets.knowledge_hub.operator_binding_apply_receipt import (
    build_governed_apply_receipt,
)


def test_real_governed_apply_output_is_directly_receiptable(
    monkeypatch, tmp_path: pathlib.Path
) -> None:
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    registry = registry_dir / "items.jsonl"
    before_items = [{"id": "before", "value": 0}]
    after_items = [{"id": "after", "value": 1}]
    registry.write_text(encode_jsonl(before_items), encoding="utf-8")
    before_sha256 = file_sha256(registry)
    after_text = encode_jsonl(after_items)
    after_sha256 = hashlib.sha256(after_text.encode("utf-8")).hexdigest()

    authorization_fingerprint = "sha256:" + "a" * 64
    review_bundle_fingerprint = "sha256:" + "b" * 64
    patch_plan_fingerprint = "sha256:" + "c" * 64
    selected = ["sha256:" + "d" * 64]

    monkeypatch.setattr(
        governed_apply,
        "build_binding_patch_plan",
        lambda root, proposal, selection: {"status": "needs-governed-pr"},
    )
    monkeypatch.setattr(
        governed_apply,
        "build_binding_review_bundle",
        lambda root, proposal, patch_plan: {
            "status": "needs-governed-authorization",
            "selected_proposal_fingerprints": selected,
            "registry_after_sha256": after_sha256,
        },
    )
    monkeypatch.setattr(
        governed_apply,
        "validate_binding_authorization",
        lambda root, bundle, authorization_input: {
            "status": "ready-for-governed-apply",
            "reviewer_identity_provider_verified": False,
            "authorization_fingerprint": authorization_fingerprint,
            "review_bundle_fingerprint": review_bundle_fingerprint,
            "patch_plan_fingerprint": patch_plan_fingerprint,
            "registry_before_sha256": before_sha256,
            "registry_after_sha256": after_sha256,
            "authorization_count": 1,
            "approved_count": 1,
            "rejected_count": 0,
        },
    )
    monkeypatch.setattr(
        governed_apply,
        "_selected_rows",
        lambda proposal, selection: ([{"proposal_fingerprint": selected[0]}], []),
    )
    monkeypatch.setattr(
        governed_apply,
        "_materialize",
        lambda root, chosen: (after_items, [], []),
    )

    payload = governed_apply.apply_governed_binding(
        tmp_path,
        {"projection": "test-proposal"},
        selected,
        {"schema_version": 1},
        confirm_authorization_fingerprint=authorization_fingerprint,
        confirm_registry_before_sha256=before_sha256,
        acknowledge_reviewer_identity_unverified=True,
    )

    expected_transaction_id = "kh-operator-binding-apply-" + "a" * 16
    assert payload["status"] == "applied"
    assert payload["reviewer_identity_unverified_acknowledged"] is True
    assert payload["transaction"]["transaction_id"] == expected_transaction_id
    assert payload["registry_post_apply_sha256"] == after_sha256

    receipt = build_governed_apply_receipt(tmp_path, payload)

    assert receipt["status"] == "verified-current-post-apply-state"
    assert receipt["receipt_generated"] is True
    assert receipt["rollback_ready"] is True
    assert receipt["transaction_id"] == expected_transaction_id
    assert receipt["authorization_fingerprint"] == authorization_fingerprint
    assert receipt["registry_current_sha256"] == after_sha256
    assert receipt["automatic_execution_enabled"] is False
