"""Read-only lifecycle receipt for one completed governed binding rollback."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import file_sha256, resolve_inside
from .operator_binding_apply_receipt import build_governed_apply_receipt
from .operator_binding_governed_rollback import _load_jsonl_bytes, _scope_row

ROLLBACK_RECEIPT_PROJECTION = "knowledge-operator-binding-rollback-receipt-v1"
ROLLBACK_PROJECTION = "knowledge-operator-binding-governed-rollback-v1"
REGISTRY_PATH = "registry/items.jsonl"
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
RAW_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:{}".format(hashlib.sha256(raw).hexdigest())


def _blocked(reasons: Sequence[str], transaction_id: str = "") -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": ROLLBACK_RECEIPT_PROJECTION,
        "status": "blocked",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "receipt_generated": False,
        "rollback_receipt_fingerprint": "",
        "rollback_transaction_id": transaction_id,
        "reviewer_identity_provider_verified": False,
        "current_state_matches_rollback_result": False,
        "reapply_ready": False,
        "requires_new_governed_apply": True,
        "original_apply_authorization_reusable": False,
        "rollback_authorization_reusable": False,
        "reapply_performed": False,
        "reason_codes": list(
            dict.fromkeys(str(reason) for reason in reasons if str(reason))
        ),
    }


def _rollback_payload_reasons(payload: Mapping[str, Any]) -> List[str]:
    expected = {
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
        "reviewer_identity_provider_verified": False,
        "explicit_operator_confirmation_verified": True,
        "reviewer_identity_boundary_acknowledged": True,
        "rollback_ready": False,
        "rollback_performed": True,
        "registry_path": REGISTRY_PATH,
        "status_mutation_performed": False,
        "owner_mutation_performed": False,
        "readiness_mutation_performed": False,
        "evidence_reference_rollback_performed": True,
        "failure_rollback_enabled": True,
        "changed_paths": [REGISTRY_PATH],
    }
    reasons: List[str] = []
    for key, value in expected.items():
        if payload.get(key) != value:
            reasons.append(
                "rollback-receipt-{}-invalid".format(key.replace("_", "-"))
            )
    for key in (
        "rollback_authorization_fingerprint",
        "receipt_fingerprint",
        "apply_authorization_fingerprint",
    ):
        if not FINGERPRINT_RE.fullmatch(str(payload.get(key, ""))):
            reasons.append(
                "rollback-receipt-{}-invalid".format(key.replace("_", "-"))
            )
    for key in (
        "registry_pre_rollback_sha256",
        "registry_restore_sha256",
        "registry_post_rollback_sha256",
    ):
        if not RAW_SHA256_RE.fullmatch(str(payload.get(key, ""))):
            reasons.append(
                "rollback-receipt-{}-invalid".format(key.replace("_", "-"))
            )
    if payload.get("registry_post_rollback_sha256") != payload.get(
        "registry_restore_sha256"
    ):
        reasons.append("rollback-receipt-post-restore-sha-mismatch")
    if int(payload.get("authorization_count", -1) or 0) <= 0:
        reasons.append("rollback-receipt-authorization-count-invalid")
    if payload.get("approved_count") != payload.get("authorization_count"):
        reasons.append("rollback-receipt-approval-count-mismatch")
    if int(payload.get("rejected_count", -1) or 0) != 0:
        reasons.append("rollback-receipt-rejection-present")
    if not isinstance(payload.get("rollback_scope"), list) or not payload.get(
        "rollback_scope"
    ):
        reasons.append("rollback-receipt-scope-invalid")
    return reasons


def _transaction_identity(payload: Mapping[str, Any]) -> Tuple[str, str, List[str]]:
    reasons: List[str] = []
    transaction = payload.get("transaction", {})
    if not isinstance(transaction, Mapping):
        return "", "", ["rollback-receipt-transaction-invalid"]
    rollback_fingerprint = str(
        payload.get("rollback_authorization_fingerprint", "")
    )
    expected_id = (
        "kh-operator-binding-rollback-"
        + rollback_fingerprint.split(":", 1)[1][:16]
        if FINGERPRINT_RE.fullmatch(rollback_fingerprint)
        else ""
    )
    transaction_id = str(transaction.get("transaction_id", ""))
    if transaction_id != expected_id:
        reasons.append("rollback-receipt-transaction-id-mismatch")
    if transaction.get("status") != "applied":
        reasons.append("rollback-receipt-transaction-status-invalid")
    if transaction.get("changed_paths") != [REGISTRY_PATH]:
        reasons.append("rollback-receipt-transaction-changed-paths-invalid")
    if transaction.get("unchanged_paths") not in ([], None):
        reasons.append("rollback-receipt-transaction-unchanged-paths-invalid")
    if transaction.get("rolled_back") is not False:
        reasons.append("rollback-receipt-transaction-rolled-back-invalid")
    journal_relative = str(transaction.get("journal", ""))
    expected_journal = ".tmp/transactions/{}/journal.json".format(transaction_id)
    if journal_relative != expected_journal:
        reasons.append("rollback-receipt-journal-path-mismatch")
    return transaction_id, journal_relative, reasons


def _load_journal(
    root: pathlib.Path, journal_relative: str
) -> Tuple[pathlib.Path, Mapping[str, Any], List[str]]:
    try:
        path = resolve_inside(root, journal_relative)
    except Exception:
        return root / "__invalid_journal__", {}, [
            "rollback-receipt-journal-path-invalid"
        ]
    if not path.is_file():
        return path, {}, ["rollback-receipt-journal-missing"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return path, {}, ["rollback-receipt-journal-json-invalid"]
    if not isinstance(value, Mapping):
        return path, {}, ["rollback-receipt-journal-shape-invalid"]
    return path, value, []


def _journal_reasons(
    journal: Mapping[str, Any],
    transaction_id: str,
    before_sha256: str,
    after_sha256: str,
) -> List[str]:
    reasons: List[str] = []
    if journal.get("schema_version") != 1:
        reasons.append("rollback-receipt-journal-schema-invalid")
    if str(journal.get("transaction_id", "")) != transaction_id:
        reasons.append("rollback-receipt-journal-transaction-id-mismatch")
    if journal.get("status") != "applied":
        reasons.append("rollback-receipt-journal-status-invalid")
    if journal.get("applied_paths") != [REGISTRY_PATH]:
        reasons.append("rollback-receipt-journal-applied-paths-invalid")
    if journal.get("rollback_paths") not in ([], None):
        reasons.append("rollback-receipt-journal-rollback-paths-invalid")
    writes = journal.get("writes", [])
    if not (
        isinstance(writes, list)
        and len(writes) == 1
        and isinstance(writes[0], Mapping)
    ):
        return reasons + ["rollback-receipt-journal-writes-invalid"]
    write = writes[0]
    checks = {
        "path": REGISTRY_PATH,
        "before_sha256": before_sha256,
        "after_sha256": after_sha256,
        "expected_sha256": before_sha256,
        "changed": True,
    }
    for key, expected in checks.items():
        if write.get(key) != expected:
            reasons.append(
                "rollback-receipt-journal-write-{}-mismatch".format(
                    key.replace("_", "-")
                )
            )
    return reasons


def _load_backup(
    root: pathlib.Path,
    transaction_id: str,
    expected_sha256: str,
) -> Tuple[str, str, bytes, List[str]]:
    relative = ".tmp/transactions/{}/before/{}".format(
        transaction_id, REGISTRY_PATH
    )
    try:
        path = resolve_inside(root, relative)
    except Exception:
        return relative, "", b"", ["rollback-receipt-backup-path-invalid"]
    if not path.is_file():
        return relative, "", b"", ["rollback-receipt-backup-missing"]
    raw = path.read_bytes()
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    reasons = (
        []
        if actual_sha256 == expected_sha256
        else ["rollback-receipt-backup-sha-mismatch"]
    )
    return relative, actual_sha256, raw, reasons


def _rederive_scope(
    root: pathlib.Path,
    apply_receipt: Mapping[str, Any],
    rollback_backup_raw: bytes,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    try:
        apply_backup = resolve_inside(
            root, str(apply_receipt.get("backup_path", ""))
        )
    except Exception:
        return [], ["rollback-receipt-apply-backup-path-invalid"]
    if not apply_backup.is_file():
        return [], ["rollback-receipt-apply-backup-missing"]
    before_rows, before_reasons = _load_jsonl_bytes(apply_backup.read_bytes())
    after_rows, after_reasons = _load_jsonl_bytes(rollback_backup_raw)
    reasons = list(before_reasons) + list(after_reasons)
    before_ids = [str(row.get("id", "")) for row in before_rows]
    after_ids = [str(row.get("id", "")) for row in after_rows]
    if before_ids != after_ids or len(set(after_ids)) != len(after_ids):
        reasons.append("rollback-receipt-scope-item-identity-drift")
    if reasons:
        return [], list(dict.fromkeys(reasons))
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
        reasons.append("rollback-receipt-scope-empty")
    return sorted(scope, key=lambda row: row["item_id"]), list(
        dict.fromkeys(reasons)
    )


def _receipt_material(
    apply_receipt: Mapping[str, Any],
    rollback_payload: Mapping[str, Any],
    transaction_id: str,
    journal_sha256: str,
    backup_sha256: str,
    scope: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    return {
        "apply_receipt_fingerprint": str(
            apply_receipt.get("receipt_fingerprint", "")
        ),
        "apply_transaction_id": str(apply_receipt.get("transaction_id", "")),
        "apply_authorization_fingerprint": str(
            apply_receipt.get("authorization_fingerprint", "")
        ),
        "rollback_authorization_fingerprint": str(
            rollback_payload.get("rollback_authorization_fingerprint", "")
        ),
        "rollback_transaction_id": transaction_id,
        "registry_pre_rollback_sha256": str(
            rollback_payload.get("registry_pre_rollback_sha256", "")
        ),
        "registry_restore_sha256": str(
            rollback_payload.get("registry_restore_sha256", "")
        ),
        "rollback_scope": [dict(row) for row in scope],
        "apply_journal_sha256": str(apply_receipt.get("journal_sha256", "")),
        "apply_backup_sha256": str(apply_receipt.get("backup_sha256", "")),
        "rollback_journal_sha256": journal_sha256,
        "rollback_backup_sha256": backup_sha256,
    }


def _apply_chain(
    root: pathlib.Path,
    apply_payload: Mapping[str, Any],
    rollback_payload: Mapping[str, Any],
) -> Tuple[Mapping[str, Any], str, str, List[str]]:
    reasons: List[str] = []
    apply_receipt = build_governed_apply_receipt(root, apply_payload)
    if not apply_receipt.get("receipt_generated"):
        reasons.extend(
            "apply-receipt:{}".format(value)
            for value in apply_receipt.get("reason_codes", [])
        )
    elif apply_receipt.get("status") != "post-apply-state-drift":
        reasons.append("rollback-receipt-apply-receipt-state-invalid")
    checks = {
        "receipt_fingerprint": "receipt_fingerprint",
        "apply_transaction_id": "transaction_id",
        "apply_authorization_fingerprint": "authorization_fingerprint",
    }
    for rollback_key, receipt_key in checks.items():
        if str(rollback_payload.get(rollback_key, "")) != str(
            apply_receipt.get(receipt_key, "")
        ):
            reasons.append(
                "rollback-receipt-{}-mismatch".format(
                    rollback_key.replace("_", "-")
                )
            )
    before_sha256 = str(rollback_payload.get("registry_pre_rollback_sha256", ""))
    after_sha256 = str(rollback_payload.get("registry_restore_sha256", ""))
    if before_sha256 != str(apply_receipt.get("registry_after_sha256", "")):
        reasons.append("rollback-receipt-pre-rollback-sha-chain-mismatch")
    if after_sha256 != str(apply_receipt.get("registry_before_sha256", "")):
        reasons.append("rollback-receipt-restore-sha-chain-mismatch")
    return apply_receipt, before_sha256, after_sha256, reasons


def _rollback_evidence(
    root: pathlib.Path,
    rollback_payload: Mapping[str, Any],
    apply_receipt: Mapping[str, Any],
    transaction_id: str,
    journal_relative: str,
    before_sha256: str,
    after_sha256: str,
) -> Tuple[pathlib.Path, str, str, List[Dict[str, Any]], List[str]]:
    reasons: List[str] = []
    journal_path, journal, load_reasons = _load_journal(root, journal_relative)
    reasons.extend(load_reasons)
    reasons.extend(
        _journal_reasons(journal, transaction_id, before_sha256, after_sha256)
    )
    backup_relative, backup_sha256, backup_raw, backup_reasons = _load_backup(
        root, transaction_id, before_sha256
    )
    reasons.extend(backup_reasons)
    scope, scope_reasons = _rederive_scope(root, apply_receipt, backup_raw)
    reasons.extend(scope_reasons)
    if scope != rollback_payload.get("rollback_scope"):
        reasons.append("rollback-receipt-scope-mismatch")
    return journal_path, backup_relative, backup_sha256, scope, reasons


def _success_payload(
    apply_receipt: Mapping[str, Any],
    rollback_payload: Mapping[str, Any],
    transaction_id: str,
    journal_relative: str,
    journal_sha256: str,
    backup_relative: str,
    backup_sha256: str,
    scope: Sequence[Mapping[str, Any]],
    before_sha256: str,
    after_sha256: str,
    current_sha256: str,
    fingerprint: str,
) -> Dict[str, Any]:
    current_matches_restore = current_sha256 == after_sha256
    return {
        "schema_version": 1,
        "projection": ROLLBACK_RECEIPT_PROJECTION,
        "status": (
            "verified-current-post-rollback-state"
            if current_matches_restore
            else "post-rollback-state-drift"
        ),
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "receipt_generated": True,
        "rollback_receipt_fingerprint": fingerprint,
        "apply_receipt_fingerprint": str(
            apply_receipt.get("receipt_fingerprint", "")
        ),
        "apply_transaction_id": str(apply_receipt.get("transaction_id", "")),
        "apply_authorization_fingerprint": str(
            apply_receipt.get("authorization_fingerprint", "")
        ),
        "rollback_authorization_fingerprint": str(
            rollback_payload.get("rollback_authorization_fingerprint", "")
        ),
        "rollback_transaction_id": transaction_id,
        "reviewer_identity_provider_verified": False,
        "registry_path": REGISTRY_PATH,
        "registry_pre_rollback_sha256": before_sha256,
        "registry_restore_sha256": after_sha256,
        "registry_current_sha256": current_sha256,
        "current_state_matches_rollback_result": current_matches_restore,
        "rollback_scope": [dict(row) for row in scope],
        "apply_journal_path": str(apply_receipt.get("journal_path", "")),
        "apply_journal_sha256": str(apply_receipt.get("journal_sha256", "")),
        "apply_backup_path": str(apply_receipt.get("backup_path", "")),
        "apply_backup_sha256": str(apply_receipt.get("backup_sha256", "")),
        "rollback_journal_path": journal_relative,
        "rollback_journal_sha256": journal_sha256,
        "rollback_backup_path": backup_relative,
        "rollback_backup_sha256": backup_sha256,
        "lifecycle_status": "rolled-back-and-verified",
        "reapply_ready": False,
        "requires_new_governed_apply": True,
        "original_apply_authorization_reusable": False,
        "rollback_authorization_reusable": False,
        "reapply_performed": False,
        "reason_codes": [
            "new-governed-apply-required-for-reapply"
            if current_matches_restore
            else "post-rollback-state-drift-detected"
        ],
    }


def build_governed_rollback_receipt(
    root: pathlib.Path,
    apply_payload: Mapping[str, Any],
    rollback_payload: Mapping[str, Any],
) -> Dict[str, Any]:
    """Verify a completed rollback and emit a read-only lifecycle receipt."""

    reasons = _rollback_payload_reasons(rollback_payload)
    transaction_id, journal_relative, transaction_reasons = _transaction_identity(
        rollback_payload
    )
    reasons.extend(transaction_reasons)
    apply_receipt, before_sha256, after_sha256, apply_reasons = _apply_chain(
        root, apply_payload, rollback_payload
    )
    reasons.extend(apply_reasons)
    journal_path, backup_relative, backup_sha256, scope, evidence_reasons = (
        _rollback_evidence(
            root,
            rollback_payload,
            apply_receipt,
            transaction_id,
            journal_relative,
            before_sha256,
            after_sha256,
        )
    )
    reasons.extend(evidence_reasons)
    if reasons:
        return _blocked(reasons, transaction_id)
    journal_sha256 = file_sha256(journal_path)
    registry_path = root / REGISTRY_PATH
    current_sha256 = file_sha256(registry_path) if registry_path.is_file() else ""
    fingerprint = _fingerprint(
        _receipt_material(
            apply_receipt,
            rollback_payload,
            transaction_id,
            journal_sha256,
            backup_sha256,
            scope,
        )
    )
    return _success_payload(
        apply_receipt,
        rollback_payload,
        transaction_id,
        journal_relative,
        journal_sha256,
        backup_relative,
        backup_sha256,
        scope,
        before_sha256,
        after_sha256,
        current_sha256,
        fingerprint,
    )
