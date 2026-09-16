"""Explicit governed apply transaction for authorized Operator evidence bindings."""

from __future__ import annotations

import pathlib
import re
from typing import Any, Dict, Mapping, Sequence

from .common import KnowledgeHubError, encode_jsonl, file_sha256
from .operator_binding_authorization import validate_binding_authorization
from .operator_binding_patch_plan import (
    _materialize,
    _selected_rows,
    build_binding_patch_plan,
)
from .operator_binding_review_bundle import build_binding_review_bundle
from .store import RepositoryTransaction

APPLY_PROJECTION = "knowledge-operator-binding-governed-apply-v1"
AUTHORIZATION_FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
RAW_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _blocked(reasons: Sequence[str]) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": APPLY_PROJECTION,
        "status": "blocked",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "apply_enabled": False,
        "apply_requested": True,
        "apply_performed": False,
        "authorization_input_generated": False,
        "authorization_validated": False,
        "reviewer_identity_provider_verified": False,
        "explicit_operator_confirmation_verified": False,
        "status_mutation_performed": False,
        "owner_mutation_performed": False,
        "readiness_mutation_performed": False,
        "changed_paths": [],
        "transaction": {},
        "reason_codes": list(
            dict.fromkeys(str(reason) for reason in reasons if str(reason))
        ),
    }


def _selection_reasons(
    selected: Sequence[str], bundle: Mapping[str, Any]
) -> Sequence[str]:
    canonical = sorted({str(value).strip() for value in selected if str(value).strip()})
    expected = bundle.get("selected_proposal_fingerprints", [])
    if canonical != expected:
        return ["apply-selection-review-bundle-mismatch"]
    return []


def _prepare_transaction(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
    selected: Sequence[str],
    before_sha256: str,
    after_sha256: str,
    authorization_fingerprint: str,
) -> RepositoryTransaction:
    chosen, reasons = _selected_rows(proposal, selected)
    if reasons:
        raise KnowledgeHubError(
            "governed apply selection revalidation failed: {}".format(
                ", ".join(reasons)
            )
        )
    items, _rows, reasons = _materialize(root, chosen)
    if reasons:
        raise KnowledgeHubError(
            "governed apply materialization failed: {}".format(", ".join(reasons))
        )
    transaction = RepositoryTransaction(
        root,
        transaction_id="kh-operator-binding-apply-{}".format(
            authorization_fingerprint.split(":", 1)[1][:16]
        ),
    )
    transaction.add_text(
        "registry/items.jsonl",
        encode_jsonl(items),
        expected_sha256=before_sha256,
    )
    plan = transaction.plan()
    writes = plan.get("writes", [])
    if not (
        plan.get("changed_count") == 1
        and isinstance(writes, list)
        and len(writes) == 1
        and isinstance(writes[0], Mapping)
        and writes[0].get("path") == "registry/items.jsonl"
        and writes[0].get("before_sha256") == before_sha256
        and writes[0].get("after_sha256") == after_sha256
        and writes[0].get("expected_sha256") == before_sha256
    ):
        raise KnowledgeHubError("governed apply transaction does not match exact patch plan")
    return transaction


def apply_governed_binding(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
    selected_fingerprints: Sequence[str],
    authorization_input: Mapping[str, Any],
    *,
    confirm_authorization_fingerprint: str,
    confirm_registry_before_sha256: str,
) -> Dict[str, Any]:
    """Revalidate the whole chain and explicitly apply one authorized registry transaction."""

    selected = sorted(
        {
            str(value).strip()
            for value in selected_fingerprints
            if str(value).strip()
        }
    )
    patch_plan = build_binding_patch_plan(root, proposal, selected)
    if patch_plan.get("status") != "needs-governed-pr":
        return _blocked(
            ["apply-patch-plan-not-ready"]
            + [str(value) for value in patch_plan.get("reason_codes", [])]
        )
    bundle = build_binding_review_bundle(root, proposal, patch_plan)
    if bundle.get("status") != "needs-governed-authorization":
        return _blocked(
            ["apply-review-bundle-not-ready"]
            + [str(value) for value in bundle.get("reason_codes", [])]
        )
    selection_reasons = list(_selection_reasons(selected, bundle))
    if selection_reasons:
        return _blocked(selection_reasons)
    authorization = validate_binding_authorization(
        root,
        bundle,
        authorization_input,
    )
    if authorization.get("status") != "ready-for-governed-apply":
        return _blocked(
            ["apply-authorization-not-ready:{}".format(authorization.get("status", ""))]
            + [str(value) for value in authorization.get("reason_codes", [])]
        )
    authorization_fingerprint = str(
        authorization.get("authorization_fingerprint", "")
    )
    if not AUTHORIZATION_FINGERPRINT_RE.fullmatch(
        confirm_authorization_fingerprint
    ):
        return _blocked(["apply-confirm-authorization-fingerprint-invalid"])
    if confirm_authorization_fingerprint != authorization_fingerprint:
        return _blocked(["apply-confirm-authorization-fingerprint-mismatch"])
    before_sha256 = str(authorization.get("registry_before_sha256", ""))
    after_sha256 = str(authorization.get("registry_after_sha256", ""))
    if not RAW_SHA256_RE.fullmatch(confirm_registry_before_sha256):
        return _blocked(["apply-confirm-registry-before-sha256-invalid"])
    if confirm_registry_before_sha256 != before_sha256:
        return _blocked(["apply-confirm-registry-before-sha256-mismatch"])
    registry_path = root / "registry/items.jsonl"
    if file_sha256(registry_path) != before_sha256:
        return _blocked(["apply-registry-precondition-stale"])
    if str(bundle.get("registry_after_sha256", "")) != after_sha256:
        return _blocked(["apply-registry-after-sha256-chain-mismatch"])
    if authorization.get("approved_count") != authorization.get("authorization_count"):
        return _blocked(["apply-authorization-not-unanimously-approved"])
    if authorization.get("rejected_count") != 0:
        return _blocked(["apply-authorization-rejection-present"])

    transaction = _prepare_transaction(
        root,
        proposal,
        selected,
        before_sha256,
        after_sha256,
        authorization_fingerprint,
    )
    result = transaction.apply()
    post_sha256 = file_sha256(registry_path)
    if result.status != "applied" or post_sha256 != after_sha256:
        raise KnowledgeHubError(
            "governed apply postcondition failed: expected {} actual {} status {}".format(
                after_sha256,
                post_sha256,
                result.status,
            )
        )
    return {
        "schema_version": 1,
        "projection": APPLY_PROJECTION,
        "status": "applied",
        "read_only": False,
        "network_performed": False,
        "canonical_write_performed": True,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "apply_enabled": True,
        "apply_requested": True,
        "apply_performed": True,
        "authorization_input_generated": False,
        "authorization_validated": True,
        "authorization_fingerprint": authorization_fingerprint,
        "reviewer_identity_provider_verified": False,
        "explicit_operator_confirmation_verified": True,
        "review_bundle_fingerprint": str(
            authorization.get("review_bundle_fingerprint", "")
        ),
        "patch_plan_fingerprint": str(
            authorization.get("patch_plan_fingerprint", "")
        ),
        "selected_proposal_fingerprints": selected,
        "selected_proposal_count": len(selected),
        "authorization_count": int(authorization.get("authorization_count", 0)),
        "approved_count": int(authorization.get("approved_count", 0)),
        "rejected_count": 0,
        "registry_path": "registry/items.jsonl",
        "registry_before_sha256": before_sha256,
        "registry_after_sha256": after_sha256,
        "registry_post_apply_sha256": post_sha256,
        "status_mutation_performed": False,
        "owner_mutation_performed": False,
        "readiness_mutation_performed": False,
        "failure_rollback_enabled": True,
        "changed_paths": list(result.changed_paths),
        "transaction": result.to_dict(),
        "reason_codes": ["explicit-governed-apply-completed"],
    }
