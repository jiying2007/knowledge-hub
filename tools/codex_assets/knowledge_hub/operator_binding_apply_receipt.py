"""Read-only receipt and rollback readiness for governed Operator binding applies."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import file_sha256, resolve_inside

APPLY_PROJECTION = "knowledge-operator-binding-governed-apply-v1"
RECEIPT_PROJECTION = "knowledge-operator-binding-apply-receipt-v1"
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
RAW_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REGISTRY_PATH = "registry/items.jsonl"


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
        "projection": RECEIPT_PROJECTION,
        "status": "blocked",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "receipt_generated": False,
        "receipt_fingerprint": "",
        "transaction_id": transaction_id,
        "reviewer_identity_provider_verified": False,
        "rollback_plan": {},
        "rollback_ready": False,
        "rollback_performed": False,
        "reason_codes": list(
            dict.fromkeys(str(reason) for reason in reasons if str(reason))
        ),
    }


def _apply_payload_reasons(payload: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    expected = {
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
        "reviewer_identity_provider_verified": False,
        "explicit_operator_confirmation_verified": True,
        "reviewer_identity_boundary_acknowledged": True,
        "status_mutation_performed": False,
        "owner_mutation_performed": False,
        "readiness_mutation_performed": False,
        "failure_rollback_enabled": True,
    }
    for key, expected_value in expected.items():
        if payload.get(key) != expected_value:
            reasons.append("apply-receipt-{}-invalid".format(key.replace("_", "-")))
    if payload.get("changed_paths") != [REGISTRY_PATH]:
        reasons.append("apply-receipt-changed-paths-invalid")
    if payload.get("registry_path") != REGISTRY_PATH:
        reasons.append("apply-receipt-registry-path-invalid")
    for key in (
        "authorization_fingerprint",
        "review_bundle_fingerprint",
        "patch_plan_fingerprint",
    ):
        if not FINGERPRINT_RE.fullmatch(str(payload.get(key, ""))):
            reasons.append("apply-receipt-{}-invalid".format(key.replace("_", "-")))
    for key in (
        "registry_before_sha256",
        "registry_after_sha256",
        "registry_post_apply_sha256",
    ):
        if not RAW_SHA256_RE.fullmatch(str(payload.get(key, ""))):
            reasons.append("apply-receipt-{}-invalid".format(key.replace("_", "-")))
    before = str(payload.get("registry_before_sha256", ""))
    after = str(payload.get("registry_after_sha256", ""))
    post = str(payload.get("registry_post_apply_sha256", ""))
    if before and after and before == after:
        reasons.append("apply-receipt-registry-sha-no-change")
    if after and post and after != post:
        reasons.append("apply-receipt-post-apply-sha-mismatch")
    selected = payload.get("selected_proposal_fingerprints", [])
    if not isinstance(selected, list) or not selected:
        reasons.append("apply-receipt-selection-invalid")
    elif selected != sorted(set(str(value) for value in selected)):
        reasons.append("apply-receipt-selection-not-canonical")
    if int(payload.get("selected_proposal_count", -1) or 0) != len(selected):
        reasons.append("apply-receipt-selection-count-mismatch")
    if int(payload.get("authorization_count", -1) or 0) <= 0:
        reasons.append("apply-receipt-authorization-count-invalid")
    if payload.get("approved_count") != payload.get("authorization_count"):
        reasons.append("apply-receipt-authorization-not-unanimous")
    if int(payload.get("rejected_count", -1) or 0) != 0:
        reasons.append("apply-receipt-rejection-present")
    if payload.get("reason_codes") != ["explicit-governed-apply-completed"]:
        reasons.append("apply-receipt-reason-codes-invalid")
    return list(dict.fromkeys(reasons))


def _transaction_reasons(payload: Mapping[str, Any]) -> Tuple[str, str, List[str]]:
    reasons: List[str] = []
    transaction = payload.get("transaction", {})
    if not isinstance(transaction, Mapping):
        return "", "", ["apply-receipt-transaction-invalid"]
    transaction_id = str(transaction.get("transaction_id", ""))
    authorization = str(payload.get("authorization_fingerprint", ""))
    expected_id = ""
    if FINGERPRINT_RE.fullmatch(authorization):
        expected_id = "kh-operator-binding-apply-{}".format(
            authorization.split(":", 1)[1][:16]
        )
    if not transaction_id or transaction_id != expected_id:
        reasons.append("apply-receipt-transaction-id-mismatch")
    if transaction.get("status") != "applied":
        reasons.append("apply-receipt-transaction-status-invalid")
    if transaction.get("changed_paths") != [REGISTRY_PATH]:
        reasons.append("apply-receipt-transaction-changed-paths-invalid")
    if transaction.get("unchanged_paths") not in ([], None):
        reasons.append("apply-receipt-transaction-unchanged-paths-invalid")
    if transaction.get("rolled_back") is not False:
        reasons.append("apply-receipt-transaction-rollback-state-invalid")
    expected_journal = ".tmp/transactions/{}/journal.json".format(transaction_id)
    journal = str(transaction.get("journal", ""))
    if journal != expected_journal:
        reasons.append("apply-receipt-journal-path-mismatch")
    return transaction_id, journal, reasons


def _load_journal(root: pathlib.Path, relative: str) -> Tuple[pathlib.Path, Dict[str, Any], List[str]]:
    reasons: List[str] = []
    try:
        path = resolve_inside(root, relative)
    except Exception:
        return root / "__invalid_journal__", {}, ["apply-receipt-journal-path-invalid"]
    if not path.is_file():
        return path, {}, ["apply-receipt-journal-missing"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return path, {}, ["apply-receipt-journal-unreadable"]
    if not isinstance(payload, dict):
        reasons.append("apply-receipt-journal-shape-invalid")
        return path, {}, reasons
    return path, payload, reasons


def _journal_reasons(
    journal: Mapping[str, Any],
    transaction_id: str,
    before_sha256: str,
    after_sha256: str,
) -> List[str]:
    reasons: List[str] = []
    if journal.get("schema_version") != 1:
        reasons.append("apply-receipt-journal-schema-invalid")
    if str(journal.get("transaction_id", "")) != transaction_id:
        reasons.append("apply-receipt-journal-transaction-id-mismatch")
    if journal.get("status") != "applied":
        reasons.append("apply-receipt-journal-status-invalid")
    if journal.get("applied_paths") != [REGISTRY_PATH]:
        reasons.append("apply-receipt-journal-applied-paths-invalid")
    if journal.get("rollback_paths") != []:
        reasons.append("apply-receipt-journal-rollback-paths-invalid")
    if not str(journal.get("completed_at", "")).strip():
        reasons.append("apply-receipt-journal-completed-at-missing")
    writes = journal.get("writes", [])
    if not (
        isinstance(writes, list)
        and len(writes) == 1
        and isinstance(writes[0], Mapping)
    ):
        reasons.append("apply-receipt-journal-write-shape-invalid")
        return reasons
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
                "apply-receipt-journal-write-{}-mismatch".format(
                    key.replace("_", "-")
                )
            )
    return reasons


def _receipt_material(
    payload: Mapping[str, Any],
    transaction_id: str,
    journal_sha256: str,
    backup_sha256: str,
) -> Dict[str, Any]:
    return {
        "transaction_id": transaction_id,
        "authorization_fingerprint": str(payload.get("authorization_fingerprint", "")),
        "review_bundle_fingerprint": str(payload.get("review_bundle_fingerprint", "")),
        "patch_plan_fingerprint": str(payload.get("patch_plan_fingerprint", "")),
        "selected_proposal_fingerprints": payload.get(
            "selected_proposal_fingerprints", []
        ),
        "registry_before_sha256": str(payload.get("registry_before_sha256", "")),
        "registry_after_sha256": str(payload.get("registry_after_sha256", "")),
        "journal_sha256": journal_sha256,
        "backup_sha256": backup_sha256,
    }


def _rollback_plan(
    transaction_id: str,
    before_sha256: str,
    after_sha256: str,
    backup_relative: str,
    ready: bool,
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "ready-for-separate-governed-rollback" if ready else "not-ready-current-drift",
        "read_only": True,
        "rollback_performed": False,
        "rollback_ready": ready,
        "automatic_execution_enabled": False,
        "requires_separate_governed_rollback": True,
        "requires_explicit_current_sha_confirmation": True,
        "transaction_id": transaction_id,
        "target_path": REGISTRY_PATH,
        "expected_current_sha256": after_sha256,
        "restore_sha256": before_sha256,
        "backup_path": backup_relative,
        "must_not": [
            "do not rollback if registry/items.jsonl changed after the governed apply",
            "do not infer owner revocation from filesystem rollback readiness",
            "do not overwrite unrelated registry changes",
        ],
    }


def build_governed_apply_receipt(
    root: pathlib.Path,
    apply_payload: Mapping[str, Any],
) -> Dict[str, Any]:
    """Verify one P2.8 apply result and build a read-only rollback readiness receipt."""

    reasons = _apply_payload_reasons(apply_payload)
    transaction_id, journal_relative, transaction_reasons = _transaction_reasons(
        apply_payload
    )
    reasons.extend(transaction_reasons)
    if reasons:
        return _blocked(reasons, transaction_id)
    before_sha256 = str(apply_payload.get("registry_before_sha256", ""))
    after_sha256 = str(apply_payload.get("registry_after_sha256", ""))
    journal_path, journal, journal_load_reasons = _load_journal(
        root, journal_relative
    )
    reasons.extend(journal_load_reasons)
    reasons.extend(
        _journal_reasons(journal, transaction_id, before_sha256, after_sha256)
    )
    backup_relative = ".tmp/transactions/{}/before/{}".format(
        transaction_id, REGISTRY_PATH
    )
    try:
        backup_path = resolve_inside(root, backup_relative)
    except Exception:
        backup_path = root / "__invalid_backup__"
        reasons.append("apply-receipt-backup-path-invalid")
    if not backup_path.is_file():
        reasons.append("apply-receipt-before-backup-missing")
        backup_sha256 = ""
    else:
        backup_sha256 = file_sha256(backup_path)
        if backup_sha256 != before_sha256:
            reasons.append("apply-receipt-before-backup-sha-mismatch")
    if reasons:
        return _blocked(reasons, transaction_id)
    journal_sha256 = file_sha256(journal_path)
    registry_path = root / REGISTRY_PATH
    current_sha256 = file_sha256(registry_path) if registry_path.is_file() else ""
    current_matches_after = current_sha256 == after_sha256
    receipt_fingerprint = _fingerprint(
        _receipt_material(
            apply_payload,
            transaction_id,
            journal_sha256,
            backup_sha256,
        )
    )
    rollback_plan = _rollback_plan(
        transaction_id,
        before_sha256,
        after_sha256,
        backup_relative,
        current_matches_after,
    )
    return {
        "schema_version": 1,
        "projection": RECEIPT_PROJECTION,
        "status": "verified-current-post-apply-state" if current_matches_after else "post-apply-state-drift",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "receipt_generated": True,
        "receipt_fingerprint": receipt_fingerprint,
        "transaction_id": transaction_id,
        "authorization_fingerprint": str(apply_payload.get("authorization_fingerprint", "")),
        "review_bundle_fingerprint": str(apply_payload.get("review_bundle_fingerprint", "")),
        "patch_plan_fingerprint": str(apply_payload.get("patch_plan_fingerprint", "")),
        "selected_proposal_fingerprints": list(
            apply_payload.get("selected_proposal_fingerprints", [])
        ),
        "registry_path": REGISTRY_PATH,
        "registry_before_sha256": before_sha256,
        "registry_after_sha256": after_sha256,
        "registry_current_sha256": current_sha256,
        "current_state_matches_applied_result": current_matches_after,
        "journal_path": journal_relative,
        "journal_sha256": journal_sha256,
        "backup_path": backup_relative,
        "backup_sha256": backup_sha256,
        "reviewer_identity_provider_verified": False,
        "rollback_plan": rollback_plan,
        "rollback_ready": current_matches_after,
        "rollback_performed": False,
        "reason_codes": [
            "separate-governed-rollback-required"
            if current_matches_after
            else "rollback-blocked-current-registry-drift"
        ],
    }
