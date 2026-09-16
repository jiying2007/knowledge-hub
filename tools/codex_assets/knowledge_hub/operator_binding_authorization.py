"""Validate explicit external owner authorization for governed binding review bundles."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import re
from collections import Counter
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import file_sha256, registry_items

REVIEW_BUNDLE_PROJECTION = "knowledge-operator-binding-review-bundle-v1"
AUTHORIZATION_PROJECTION = "knowledge-operator-binding-authorization-v1"
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ALLOWED_DECISIONS = {"approve-binding", "reject-binding"}
MAX_AUTHORIZATION_ROWS = 50


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:{}".format(hashlib.sha256(raw).hexdigest())


def _bundle_fingerprint_material(bundle: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "patch_plan_fingerprint": str(bundle.get("patch_plan_fingerprint", "")),
        "registry_before_sha256": str(bundle.get("registry_before_sha256", "")),
        "registry_after_sha256": str(bundle.get("registry_after_sha256", "")),
        "selected_proposal_fingerprints": bundle.get(
            "selected_proposal_fingerprints", []
        ),
        "rows": bundle.get("rows", []),
    }


def _bundle_contract_reasons(bundle: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    expected = {
        "projection": REVIEW_BUNDLE_PROJECTION,
        "status": "needs-governed-authorization",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "apply_enabled": False,
        "selection_is_authorization": False,
        "authorization_state": "not-provided",
        "requires_governed_authorization": True,
        "requires_governed_pr": True,
        "review_bundle_only": True,
        "status_mutation_planned": False,
        "owner_mutation_planned": False,
        "readiness_mutation_planned": False,
    }
    for key, expected_value in expected.items():
        if bundle.get(key) != expected_value:
            reasons.append("review-bundle-{}-invalid".format(key.replace("_", "-")))
    selected = bundle.get("selected_proposal_fingerprints", [])
    rows = bundle.get("rows", [])
    if not isinstance(selected, list) or not selected:
        reasons.append("review-bundle-selection-invalid")
    elif selected != sorted(set(str(value) for value in selected)):
        reasons.append("review-bundle-selection-not-canonical")
    if not isinstance(rows, list) or not rows:
        reasons.append("review-bundle-rows-invalid")
        rows = []
    if int(bundle.get("selected_proposal_count", -1) or 0) != len(selected):
        reasons.append("review-bundle-selection-count-mismatch")
    if int(bundle.get("review_row_count", -1) or 0) != len(rows):
        reasons.append("review-bundle-row-count-mismatch")
    fingerprint = str(bundle.get("review_bundle_fingerprint", ""))
    if not FINGERPRINT_RE.fullmatch(fingerprint):
        reasons.append("review-bundle-fingerprint-invalid")
    elif _fingerprint(_bundle_fingerprint_material(bundle)) != fingerprint:
        reasons.append("review-bundle-fingerprint-mismatch")
    if bundle.get("reason_codes") != ["governed-authorization-required"]:
        reasons.append("review-bundle-reason-codes-invalid")
    return list(dict.fromkeys(reasons))


def _valid_date(value: Any) -> bool:
    try:
        parts = str(value).split("-")
        if len(parts) != 3 or any(not part.isdigit() for part in parts):
            return False
        year, month, day = (int(part) for part in parts)
        dt.date(year, month, day)
        return True
    except (TypeError, ValueError):
        return False


def _valid_reference(value: Any) -> bool:
    return bool(
        isinstance(value, Mapping)
        and str(value.get("kind", "")).strip()
        and str(value.get("ref", "")).strip()
    )


def _reference_equal(left: Any, right: Any) -> bool:
    return bool(
        _valid_reference(left)
        and _valid_reference(right)
        and str(left.get("kind", "")) == str(right.get("kind", ""))
        and str(left.get("ref", "")) == str(right.get("ref", ""))
    )


def _authorization_input_reasons(
    authorization: Mapping[str, Any], bundle: Mapping[str, Any]
) -> List[str]:
    reasons: List[str] = []
    if authorization.get("schema_version") != 1:
        reasons.append("authorization-schema-version-invalid")
    if str(authorization.get("review_bundle_fingerprint", "")) != str(
        bundle.get("review_bundle_fingerprint", "")
    ):
        reasons.append("authorization-review-bundle-fingerprint-mismatch")
    if str(authorization.get("patch_plan_fingerprint", "")) != str(
        bundle.get("patch_plan_fingerprint", "")
    ):
        reasons.append("authorization-patch-plan-fingerprint-mismatch")
    rows = authorization.get("authorizations", [])
    if not isinstance(rows, list) or not rows:
        reasons.append("authorization-rows-missing")
    elif len(rows) > MAX_AUTHORIZATION_ROWS:
        reasons.append("authorization-row-budget-exceeded")
    return reasons


def _canonical_owner_inventory(
    root: pathlib.Path, bundle_rows: Sequence[Mapping[str, Any]]
) -> Tuple[Dict[Tuple[str, str, str], Mapping[str, Any]], List[str]]:
    reasons: List[str] = []
    wanted = {
        (
            str(row.get("project_id", "")),
            str(row.get("item_id", "")),
            str(row.get("item_path", "")),
        )
        for row in bundle_rows
    }
    matches: Dict[Tuple[str, str, str], List[Mapping[str, Any]]] = {
        key: [] for key in wanted
    }
    for item in registry_items(root):
        key = (
            str(item.get("project_id", "")),
            str(item.get("id", "")),
            str(item.get("path", "")),
        )
        if key in matches and str(item.get("readiness_slot", "")) == "validation":
            matches[key].append(item)
    result: Dict[Tuple[str, str, str], Mapping[str, Any]] = {}
    for key, rows in matches.items():
        if len(rows) != 1:
            reasons.append("canonical-authorization-target-not-unique:{}".format("|".join(key)))
            continue
        contract = rows[0].get("evidence_contract", {})
        if not isinstance(contract, Mapping):
            reasons.append("canonical-evidence-contract-invalid:{}".format("|".join(key)))
            continue
        owner_ref = contract.get("owner_ref")
        if not _valid_reference(owner_ref):
            reasons.append("canonical-owner-ref-invalid:{}".format("|".join(key)))
            continue
        result[key] = contract
    return result, reasons


def _authorization_row_reasons(
    row: Mapping[str, Any],
    bundle_row: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> List[str]:
    reasons: List[str] = []
    fingerprint = str(bundle_row.get("proposal_fingerprint", ""))
    if str(row.get("proposal_fingerprint", "")) != fingerprint:
        reasons.append("authorization-proposal-fingerprint-mismatch")
    authorization_id = str(row.get("authorization_id", "")).strip()
    if not authorization_id:
        reasons.append("authorization-id-missing")
    decision = str(row.get("owner_decision", ""))
    if decision not in ALLOWED_DECISIONS:
        reasons.append("authorization-owner-decision-invalid")
    if not _reference_equal(row.get("owner_ref"), contract.get("owner_ref")):
        reasons.append("authorization-owner-ref-mismatch")
    if not str(row.get("reviewed_by", "")).strip():
        reasons.append("authorization-reviewed-by-missing")
    if not _valid_date(row.get("reviewed_at")):
        reasons.append("authorization-reviewed-at-invalid")
    if not str(row.get("reason", "")).strip():
        reasons.append("authorization-reason-missing")
    return reasons


def _match_authorizations(
    bundle: Mapping[str, Any],
    authorization: Mapping[str, Any],
    contracts: Mapping[Tuple[str, str, str], Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    reasons: List[str] = []
    auth_rows = [row for row in authorization.get("authorizations", []) if isinstance(row, Mapping)]
    if len(auth_rows) != len(authorization.get("authorizations", [])):
        reasons.append("authorization-row-type-invalid")
    by_proposal: Dict[str, List[Mapping[str, Any]]] = {}
    for row in auth_rows:
        by_proposal.setdefault(str(row.get("proposal_fingerprint", "")), []).append(row)
    output: List[Dict[str, Any]] = []
    authorization_ids: List[str] = []
    for bundle_row in bundle.get("rows", []):
        if not isinstance(bundle_row, Mapping):
            continue
        fingerprint = str(bundle_row.get("proposal_fingerprint", ""))
        matches = by_proposal.get(fingerprint, [])
        if len(matches) != 1:
            reasons.append("authorization-proposal-coverage-invalid:{}".format(fingerprint))
            continue
        key = (
            str(bundle_row.get("project_id", "")),
            str(bundle_row.get("item_id", "")),
            str(bundle_row.get("item_path", "")),
        )
        contract = contracts.get(key, {})
        row_reasons = _authorization_row_reasons(matches[0], bundle_row, contract)
        reasons.extend("{}:{}".format(fingerprint, reason) for reason in row_reasons)
        authorization_ids.append(str(matches[0].get("authorization_id", "")))
        output.append(dict(matches[0]))
    selected = {str(value) for value in bundle.get("selected_proposal_fingerprints", [])}
    extras = sorted(set(by_proposal) - selected)
    reasons.extend("authorization-extra-proposal:{}".format(value) for value in extras)
    duplicates = [value for value, count in Counter(authorization_ids).items() if value and count > 1]
    reasons.extend("authorization-id-reused:{}".format(value) for value in sorted(duplicates))
    return output, list(dict.fromkeys(reasons))


def _blocked(reasons: Sequence[str], status: str = "blocked") -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": AUTHORIZATION_PROJECTION,
        "status": status,
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "apply_enabled": False,
        "authorization_input_generated": False,
        "authorization_validated": False,
        "reviewer_identity_provider_verified": False,
        "requires_governed_apply": False,
        "status_mutation_planned": False,
        "owner_mutation_planned": False,
        "readiness_mutation_planned": False,
        "authorization_count": 0,
        "approved_count": 0,
        "rejected_count": 0,
        "rows": [],
        "reason_codes": list(dict.fromkeys(str(value) for value in reasons if str(value))),
    }


def validate_binding_authorization(
    root: pathlib.Path,
    bundle: Mapping[str, Any],
    authorization: Mapping[str, Any],
) -> Dict[str, Any]:
    """Validate externally supplied owner decisions without applying canonical evidence."""

    reasons = _bundle_contract_reasons(bundle)
    reasons.extend(_authorization_input_reasons(authorization, bundle))
    registry_path = root / "registry/items.jsonl"
    if file_sha256(registry_path) != str(bundle.get("registry_before_sha256", "")):
        reasons.append("authorization-registry-precondition-stale")
    bundle_rows = [row for row in bundle.get("rows", []) if isinstance(row, Mapping)]
    contracts, inventory_reasons = _canonical_owner_inventory(root, bundle_rows)
    reasons.extend(inventory_reasons)
    if reasons:
        return _blocked(reasons, status="upstream-error")
    rows, row_reasons = _match_authorizations(bundle, authorization, contracts)
    if row_reasons:
        return _blocked(row_reasons)
    decisions = Counter(str(row.get("owner_decision", "")) for row in rows)
    rejected = decisions.get("reject-binding", 0)
    approved = decisions.get("approve-binding", 0)
    status = "rejected-by-governance" if rejected else "ready-for-governed-apply"
    return {
        "schema_version": 1,
        "projection": AUTHORIZATION_PROJECTION,
        "status": status,
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "apply_enabled": False,
        "authorization_input_generated": False,
        "authorization_validated": True,
        "reviewer_identity_provider_verified": False,
        "requires_governed_apply": not bool(rejected),
        "status_mutation_planned": False,
        "owner_mutation_planned": False,
        "readiness_mutation_planned": False,
        "review_bundle_fingerprint": str(bundle.get("review_bundle_fingerprint", "")),
        "patch_plan_fingerprint": str(bundle.get("patch_plan_fingerprint", "")),
        "registry_before_sha256": str(bundle.get("registry_before_sha256", "")),
        "registry_after_sha256": str(bundle.get("registry_after_sha256", "")),
        "authorization_count": len(rows),
        "approved_count": approved,
        "rejected_count": rejected,
        "rows": rows,
        "reason_codes": [
            "governed-apply-required" if not rejected else "governance-rejected"
        ],
    }
