"""Explicit governed rollback for one verified Operator binding apply transaction."""

from __future__ import annotations

import datetime as _datetime
import hashlib
import json
import pathlib
import re
from collections import Counter
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError, file_sha256, resolve_inside
from .operator_binding_apply_receipt import build_governed_apply_receipt
from .store import RepositoryTransaction

ROLLBACK_PROJECTION = "knowledge-operator-binding-governed-rollback-v1"
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
RAW_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REGISTRY_PATH = "registry/items.jsonl"
ALLOWED_EVIDENCE_FIELDS = {
    "source_refs",
    "validation_refs",
    "artifact_refs",
    "release_ref",
}


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:{}".format(hashlib.sha256(raw).hexdigest())


def _valid_reference(value: Any) -> bool:
    return bool(
        isinstance(value, Mapping)
        and str(value.get("kind", "")).strip()
        and str(value.get("ref", "")).strip()
    )


def _valid_date(value: Any) -> bool:
    try:
        _datetime.date.fromisoformat(str(value))
    except ValueError:
        return False
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)))


def _blocked(reasons: Sequence[str]) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": ROLLBACK_PROJECTION,
        "status": "blocked",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "rollback_authorization_input_generated": False,
        "rollback_authorization_validated": False,
        "rollback_authorization_fingerprint": "",
        "reviewer_identity_provider_verified": False,
        "explicit_operator_confirmation_verified": False,
        "reviewer_identity_boundary_acknowledged": False,
        "rollback_ready": False,
        "rollback_performed": False,
        "status_mutation_performed": False,
        "owner_mutation_performed": False,
        "readiness_mutation_performed": False,
        "rollback_scope": [],
        "changed_paths": [],
        "transaction": {},
        "reason_codes": list(
            dict.fromkeys(str(reason) for reason in reasons if str(reason))
        ),
    }


def _load_jsonl_bytes(raw: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    rows: List[Dict[str, Any]] = []
    reasons: List[str] = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return [], ["rollback-registry-utf8-invalid"]
    for index, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            reasons.append("rollback-registry-json-invalid:{}".format(index))
            continue
        if not isinstance(value, dict):
            reasons.append("rollback-registry-row-shape-invalid:{}".format(index))
            continue
        rows.append(value)
    if not rows:
        reasons.append("rollback-registry-empty")
    return rows, reasons


def _contract_changed_fields(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> List[str]:
    return sorted(
        key
        for key in set(before) | set(after)
        if before.get(key) != after.get(key)
    )


def _scope_row(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> Tuple[Dict[str, Any], List[str]]:
    reasons: List[str] = []
    before_outer = {key: value for key, value in before.items() if key != "evidence_contract"}
    after_outer = {key: value for key, value in after.items() if key != "evidence_contract"}
    if before_outer != after_outer:
        reasons.append("rollback-item-non-evidence-drift")
    before_contract = before.get("evidence_contract", {})
    after_contract = after.get("evidence_contract", {})
    if not isinstance(before_contract, Mapping) or not isinstance(after_contract, Mapping):
        return {}, reasons + ["rollback-evidence-contract-invalid"]
    changed_fields = _contract_changed_fields(before_contract, after_contract)
    if not changed_fields:
        return {}, reasons + ["rollback-item-change-missing"]
    unsupported = sorted(set(changed_fields) - ALLOWED_EVIDENCE_FIELDS)
    if unsupported:
        reasons.append("rollback-evidence-field-unsupported:{}".format(",".join(unsupported)))
    for key in ("status", "profile", "owner_ref"):
        if before_contract.get(key) != after_contract.get(key):
            reasons.append("rollback-evidence-{}-drift".format(key.replace("_", "-")))
    owner_ref = after_contract.get("owner_ref", {})
    if not _valid_reference(owner_ref):
        reasons.append("rollback-owner-ref-invalid")
    item_id = str(after.get("id", ""))
    project_id = str(after.get("project_id", ""))
    item_path = str(after.get("path", ""))
    if not item_id:
        reasons.append("rollback-item-id-missing")
    if not project_id:
        reasons.append("rollback-project-id-missing")
    if not item_path:
        reasons.append("rollback-item-path-missing")
    return {
        "item_id": item_id,
        "project_id": project_id,
        "item_path": item_path,
        "owner_ref": dict(owner_ref) if isinstance(owner_ref, Mapping) else {},
        "changed_fields": changed_fields,
    }, reasons


def _derive_scope(
    root: pathlib.Path, receipt: Mapping[str, Any]
) -> Tuple[List[Dict[str, Any]], bytes, List[str]]:
    reasons: List[str] = []
    backup_relative = str(receipt.get("backup_path", ""))
    try:
        backup_path = resolve_inside(root, backup_relative)
    except Exception:
        return [], b"", ["rollback-backup-path-invalid"]
    registry_path = root / REGISTRY_PATH
    if not backup_path.is_file() or not registry_path.is_file():
        return [], b"", ["rollback-registry-or-backup-missing"]
    before_raw = backup_path.read_bytes()
    after_raw = registry_path.read_bytes()
    before_rows, before_reasons = _load_jsonl_bytes(before_raw)
    after_rows, after_reasons = _load_jsonl_bytes(after_raw)
    reasons.extend(before_reasons)
    reasons.extend(after_reasons)
    before_ids = [str(row.get("id", "")) for row in before_rows]
    after_ids = [str(row.get("id", "")) for row in after_rows]
    if before_ids != after_ids or len(set(after_ids)) != len(after_ids):
        reasons.append("rollback-registry-item-identity-drift")
    if reasons:
        return [], before_raw, list(dict.fromkeys(reasons))
    scope: List[Dict[str, Any]] = []
    for before, after in zip(before_rows, after_rows):
        if before == after:
            continue
        row, row_reasons = _scope_row(before, after)
        reasons.extend(
            "{}:{}".format(str(after.get("id", "")), reason)
            for reason in row_reasons
        )
        if row:
            scope.append(row)
    if not scope:
        reasons.append("rollback-scope-empty")
    return sorted(scope, key=lambda row: row["item_id"]), before_raw, list(dict.fromkeys(reasons))


def _authorization_input_reasons(
    authorization: Mapping[str, Any], receipt: Mapping[str, Any]
) -> List[str]:
    reasons: List[str] = []
    checks = {
        "schema_version": 1,
        "receipt_fingerprint": str(receipt.get("receipt_fingerprint", "")),
        "transaction_id": str(receipt.get("transaction_id", "")),
        "apply_authorization_fingerprint": str(receipt.get("authorization_fingerprint", "")),
        "registry_after_sha256": str(receipt.get("registry_after_sha256", "")),
        "registry_restore_sha256": str(receipt.get("registry_before_sha256", "")),
    }
    for key, expected in checks.items():
        if authorization.get(key) != expected:
            reasons.append("rollback-authorization-{}-mismatch".format(key.replace("_", "-")))
    rows = authorization.get("authorizations", [])
    if not isinstance(rows, list):
        reasons.append("rollback-authorization-rows-invalid")
    return reasons


def _authorization_row_reasons(
    row: Mapping[str, Any], scope: Mapping[str, Any]
) -> List[str]:
    reasons: List[str] = []
    checks = {
        "item_id": scope.get("item_id"),
        "project_id": scope.get("project_id"),
        "item_path": scope.get("item_path"),
        "owner_ref": scope.get("owner_ref"),
    }
    for key, expected in checks.items():
        if row.get(key) != expected:
            reasons.append("rollback-authorization-{}-mismatch".format(key.replace("_", "-")))
    if str(row.get("owner_decision", "")) not in {"approve-rollback", "reject-rollback"}:
        reasons.append("rollback-authorization-decision-invalid")
    if not str(row.get("authorization_id", "")).strip():
        reasons.append("rollback-authorization-id-missing")
    if not str(row.get("reviewed_by", "")).strip():
        reasons.append("rollback-authorization-reviewed-by-missing")
    if not _valid_date(row.get("reviewed_at")):
        reasons.append("rollback-authorization-reviewed-at-invalid")
    if not str(row.get("reason", "")).strip():
        reasons.append("rollback-authorization-reason-missing")
    return reasons


def _match_authorizations(
    scope: Sequence[Mapping[str, Any]], authorization: Mapping[str, Any]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    raw_rows = authorization.get("authorizations", [])
    if not isinstance(raw_rows, list):
        return [], ["rollback-authorization-rows-invalid"]
    rows = [row for row in raw_rows if isinstance(row, Mapping)]
    reasons: List[str] = []
    if len(rows) != len(raw_rows):
        reasons.append("rollback-authorization-row-type-invalid")
    by_item: Dict[str, List[Mapping[str, Any]]] = {}
    for row in rows:
        by_item.setdefault(str(row.get("item_id", "")), []).append(row)
    output: List[Dict[str, Any]] = []
    authorization_ids: List[str] = []
    scope_ids = {str(value.get("item_id", "")) for value in scope}
    for scope_row in scope:
        item_id = str(scope_row.get("item_id", ""))
        matches = by_item.get(item_id, [])
        if len(matches) != 1:
            reasons.append("rollback-authorization-item-coverage-invalid:{}".format(item_id))
            continue
        reasons.extend(
            "{}:{}".format(item_id, reason)
            for reason in _authorization_row_reasons(matches[0], scope_row)
        )
        output.append(dict(matches[0]))
        authorization_ids.append(str(matches[0].get("authorization_id", "")))
    for item_id in sorted(set(by_item) - scope_ids):
        reasons.append("rollback-authorization-extra-item:{}".format(item_id))
    duplicates = [
        value
        for value, count in Counter(authorization_ids).items()
        if value and count > 1
    ]
    reasons.extend(
        "rollback-authorization-id-reused:{}".format(value)
        for value in sorted(duplicates)
    )
    return output, list(dict.fromkeys(reasons))


def _authorization_material(
    receipt: Mapping[str, Any],
    scope: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    return {
        "receipt_fingerprint": str(receipt.get("receipt_fingerprint", "")),
        "transaction_id": str(receipt.get("transaction_id", "")),
        "apply_authorization_fingerprint": str(receipt.get("authorization_fingerprint", "")),
        "registry_after_sha256": str(receipt.get("registry_after_sha256", "")),
        "registry_restore_sha256": str(receipt.get("registry_before_sha256", "")),
        "rollback_scope": [dict(row) for row in scope],
        "authorizations": [dict(row) for row in rows],
    }


def validate_rollback_authorization(
    root: pathlib.Path,
    apply_payload: Mapping[str, Any],
    authorization: Mapping[str, Any],
) -> Dict[str, Any]:
    """Validate an external rollback decision without mutating canonical evidence."""

    receipt = build_governed_apply_receipt(root, apply_payload)
    if receipt.get("status") != "verified-current-post-apply-state":
        return _blocked(
            ["rollback-receipt-not-ready:{}".format(receipt.get("status", ""))]
            + [str(value) for value in receipt.get("reason_codes", [])]
        )
    scope, _before_raw, reasons = _derive_scope(root, receipt)
    reasons.extend(_authorization_input_reasons(authorization, receipt))
    if reasons:
        return _blocked(reasons)
    rows, row_reasons = _match_authorizations(scope, authorization)
    if row_reasons:
        return _blocked(row_reasons)
    decisions = Counter(str(row.get("owner_decision", "")) for row in rows)
    rejected = decisions.get("reject-rollback", 0)
    approved = decisions.get("approve-rollback", 0)
    fingerprint = _fingerprint(_authorization_material(receipt, scope, rows))
    return {
        "schema_version": 1,
        "projection": ROLLBACK_PROJECTION,
        "status": "rejected-by-governance" if rejected else "ready-for-governed-rollback",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "rollback_authorization_input_generated": False,
        "rollback_authorization_validated": True,
        "rollback_authorization_fingerprint": fingerprint,
        "reviewer_identity_provider_verified": False,
        "explicit_operator_confirmation_verified": False,
        "reviewer_identity_boundary_acknowledged": False,
        "receipt_fingerprint": str(receipt.get("receipt_fingerprint", "")),
        "apply_transaction_id": str(receipt.get("transaction_id", "")),
        "apply_authorization_fingerprint": str(receipt.get("authorization_fingerprint", "")),
        "registry_after_sha256": str(receipt.get("registry_after_sha256", "")),
        "registry_restore_sha256": str(receipt.get("registry_before_sha256", "")),
        "rollback_ready": not bool(rejected),
        "rollback_performed": False,
        "authorization_count": len(rows),
        "approved_count": approved,
        "rejected_count": rejected,
        "rollback_scope": [dict(row) for row in scope],
        "rows": rows,
        "reason_codes": ["governed-rollback-required" if not rejected else "governance-rejected"],
    }


def _prepare_transaction(
    root: pathlib.Path,
    before_raw: bytes,
    current_sha256: str,
    restore_sha256: str,
    authorization_fingerprint: str,
) -> RepositoryTransaction:
    transaction = RepositoryTransaction(
        root,
        transaction_id="kh-operator-binding-rollback-{}".format(
            authorization_fingerprint.split(":", 1)[1][:16]
        ),
    )
    transaction.add_bytes(
        REGISTRY_PATH,
        before_raw,
        expected_sha256=current_sha256,
    )
    plan = transaction.plan()
    writes = plan.get("writes", [])
    if not (
        plan.get("changed_count") == 1
        and isinstance(writes, list)
        and len(writes) == 1
        and isinstance(writes[0], Mapping)
        and writes[0].get("path") == REGISTRY_PATH
        and writes[0].get("before_sha256") == current_sha256
        and writes[0].get("after_sha256") == restore_sha256
        and writes[0].get("expected_sha256") == current_sha256
    ):
        raise KnowledgeHubError("governed rollback transaction does not match exact receipt plan")
    return transaction


def perform_governed_rollback(
    root: pathlib.Path,
    apply_payload: Mapping[str, Any],
    authorization_input: Mapping[str, Any],
    *,
    confirm_receipt_fingerprint: str,
    confirm_rollback_authorization_fingerprint: str,
    confirm_registry_current_sha256: str,
    acknowledge_reviewer_identity_unverified: bool = False,
) -> Dict[str, Any]:
    """Revalidate and explicitly restore one authorized binding apply transaction."""

    validated = validate_rollback_authorization(root, apply_payload, authorization_input)
    if validated.get("status") != "ready-for-governed-rollback":
        return _blocked(
            ["rollback-authorization-not-ready:{}".format(validated.get("status", ""))]
            + [str(value) for value in validated.get("reason_codes", [])]
        )
    receipt = build_governed_apply_receipt(root, apply_payload)
    if confirm_receipt_fingerprint != str(receipt.get("receipt_fingerprint", "")):
        return _blocked(["rollback-confirm-receipt-fingerprint-mismatch"])
    if not FINGERPRINT_RE.fullmatch(confirm_receipt_fingerprint):
        return _blocked(["rollback-confirm-receipt-fingerprint-invalid"])
    rollback_fingerprint = str(validated.get("rollback_authorization_fingerprint", ""))
    if confirm_rollback_authorization_fingerprint != rollback_fingerprint:
        return _blocked(["rollback-confirm-authorization-fingerprint-mismatch"])
    if not FINGERPRINT_RE.fullmatch(confirm_rollback_authorization_fingerprint):
        return _blocked(["rollback-confirm-authorization-fingerprint-invalid"])
    current_sha256 = str(receipt.get("registry_after_sha256", ""))
    restore_sha256 = str(receipt.get("registry_before_sha256", ""))
    if not RAW_SHA256_RE.fullmatch(confirm_registry_current_sha256):
        return _blocked(["rollback-confirm-current-sha256-invalid"])
    if confirm_registry_current_sha256 != current_sha256:
        return _blocked(["rollback-confirm-current-sha256-mismatch"])
    if not acknowledge_reviewer_identity_unverified:
        return _blocked(["rollback-reviewer-identity-boundary-acknowledgement-required"])
    if validated.get("approved_count") != validated.get("authorization_count"):
        return _blocked(["rollback-authorization-not-unanimously-approved"])
    if int(validated.get("rejected_count", -1) or 0) != 0:
        return _blocked(["rollback-authorization-rejection-present"])
    registry_path = root / REGISTRY_PATH
    if file_sha256(registry_path) != current_sha256:
        return _blocked(["rollback-registry-precondition-stale"])
    _scope, before_raw, reasons = _derive_scope(root, receipt)
    if reasons:
        return _blocked(reasons)

    transaction = _prepare_transaction(
        root,
        before_raw,
        current_sha256,
        restore_sha256,
        rollback_fingerprint,
    )
    result = transaction.apply()
    post_sha256 = file_sha256(registry_path)
    if result.status != "applied" or post_sha256 != restore_sha256:
        raise KnowledgeHubError(
            "governed rollback postcondition failed: expected {} actual {} status {}".format(
                restore_sha256,
                post_sha256,
                result.status,
            )
        )
    return {
        "schema_version": 1,
        "projection": ROLLBACK_PROJECTION,
        "status": "rolled-back",
        "read_only": False,
        "network_performed": False,
        "canonical_write_performed": True,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "rollback_authorization_input_generated": False,
        "rollback_authorization_validated": True,
        "rollback_authorization_fingerprint": rollback_fingerprint,
        "reviewer_identity_provider_verified": False,
        "explicit_operator_confirmation_verified": True,
        "reviewer_identity_boundary_acknowledged": True,
        "receipt_fingerprint": str(receipt.get("receipt_fingerprint", "")),
        "apply_transaction_id": str(receipt.get("transaction_id", "")),
        "apply_authorization_fingerprint": str(receipt.get("authorization_fingerprint", "")),
        "rollback_ready": False,
        "rollback_performed": True,
        "authorization_count": int(validated.get("authorization_count", 0)),
        "approved_count": int(validated.get("approved_count", 0)),
        "rejected_count": 0,
        "rollback_scope": list(validated.get("rollback_scope", [])),
        "registry_path": REGISTRY_PATH,
        "registry_pre_rollback_sha256": current_sha256,
        "registry_restore_sha256": restore_sha256,
        "registry_post_rollback_sha256": post_sha256,
        "status_mutation_performed": False,
        "owner_mutation_performed": False,
        "readiness_mutation_performed": False,
        "evidence_reference_rollback_performed": True,
        "failure_rollback_enabled": True,
        "changed_paths": list(result.changed_paths),
        "transaction": result.to_dict(),
        "reason_codes": ["explicit-governed-rollback-completed"],
    }
