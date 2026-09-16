from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile
import unittest
from typing import Dict, List, Tuple

from tools.codex_assets.knowledge_hub.common import file_sha256
from tools.codex_assets.knowledge_hub.operator_binding_apply_receipt import (
    build_governed_apply_receipt,
)
from tools.codex_assets.knowledge_hub.operator_binding_governed_rollback import (
    perform_governed_rollback,
    validate_rollback_authorization,
)
from tools.codex_assets.knowledge_hub.operator_binding_rollback_receipt import (
    build_governed_rollback_receipt,
)
from tools.codex_assets.knowledge_hub.store import RepositoryTransaction

REGISTRY_PATH = "registry/items.jsonl"


class OperatorBindingRollbackReceiptTests(unittest.TestCase):
    def _sha256_text(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _owner(self) -> Dict[str, str]:
        return {"kind": "owner", "ref": "owner://team-alpha"}

    def _item(self, refs: List[Dict[str, str]]) -> Dict[str, object]:
        return {
            "id": "item-alpha",
            "project_id": "alpha",
            "readiness_slot": "validation",
            "path": "projects/alpha/validation/project-readiness.md",
            "evidence_contract": {
                "schema_version": 1,
                "profile": "software-tool",
                "status": "pending",
                "owner_ref": self._owner(),
                "source_refs": refs,
                "validation_refs": [],
                "artifact_refs": [],
                "device_refs": [],
                "release_ref": None,
                "rollback_ref": {"kind": "runbook", "ref": "doc://rollback"},
                "not_applicable": {},
                "member_project_ids": [],
            },
        }

    def _lifecycle_fixture(
        self,
    ) -> Tuple[
        tempfile.TemporaryDirectory,
        pathlib.Path,
        Dict[str, object],
        Dict[str, object],
        str,
    ]:
        temporary = tempfile.TemporaryDirectory()
        root = pathlib.Path(temporary.name)
        (root / "registry").mkdir()
        before_text = json.dumps(self._item([]), sort_keys=True) + "\n"
        reference = {
            "kind": "github-source-revision",
            "ref": "github://example/alpha@" + "1" * 40,
        }
        after_text = json.dumps(self._item([reference]), sort_keys=True) + "\n"
        registry = root / REGISTRY_PATH
        registry.write_text(before_text, encoding="utf-8")
        before_sha256 = file_sha256(registry)
        after_sha256 = self._sha256_text(after_text)

        apply_authorization_fingerprint = "sha256:" + "a" * 64
        apply_transaction_id = "kh-operator-binding-apply-" + "a" * 16
        apply_tx = RepositoryTransaction(root, transaction_id=apply_transaction_id)
        apply_tx.add_text(REGISTRY_PATH, after_text, expected_sha256=before_sha256)
        apply_result = apply_tx.apply()
        self.assertEqual(apply_result.status, "applied")
        self.assertEqual(file_sha256(registry), after_sha256)

        apply_payload: Dict[str, object] = {
            "schema_version": 1,
            "projection": "knowledge-operator-binding-governed-apply-v1",
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
            "authorization_fingerprint": apply_authorization_fingerprint,
            "reviewer_identity_provider_verified": False,
            "explicit_operator_confirmation_verified": True,
            "reviewer_identity_boundary_acknowledged": True,
            "review_bundle_fingerprint": "sha256:" + "b" * 64,
            "patch_plan_fingerprint": "sha256:" + "c" * 64,
            "selected_proposal_fingerprints": ["sha256:" + "d" * 64],
            "selected_proposal_count": 1,
            "authorization_count": 1,
            "approved_count": 1,
            "rejected_count": 0,
            "registry_path": REGISTRY_PATH,
            "registry_before_sha256": before_sha256,
            "registry_after_sha256": after_sha256,
            "registry_post_apply_sha256": after_sha256,
            "status_mutation_performed": False,
            "owner_mutation_performed": False,
            "readiness_mutation_performed": False,
            "failure_rollback_enabled": True,
            "changed_paths": [REGISTRY_PATH],
            "transaction": apply_result.to_dict(),
            "reason_codes": ["explicit-governed-apply-completed"],
        }

        apply_receipt = build_governed_apply_receipt(root, apply_payload)
        self.assertEqual(apply_receipt["status"], "verified-current-post-apply-state")
        authorization: Dict[str, object] = {
            "schema_version": 1,
            "receipt_fingerprint": apply_receipt["receipt_fingerprint"],
            "transaction_id": apply_receipt["transaction_id"],
            "apply_authorization_fingerprint": apply_receipt["authorization_fingerprint"],
            "registry_after_sha256": apply_receipt["registry_after_sha256"],
            "registry_restore_sha256": apply_receipt["registry_before_sha256"],
            "authorizations": [
                {
                    "item_id": "item-alpha",
                    "project_id": "alpha",
                    "item_path": "projects/alpha/validation/project-readiness.md",
                    "owner_ref": self._owner(),
                    "authorization_id": "ROLLBACK-ALPHA-001",
                    "owner_decision": "approve-rollback",
                    "reviewed_by": "alpha-owner@example",
                    "reviewed_at": "2026-09-16",
                    "reason": "Reviewed the exact rollback scope.",
                }
            ],
        }
        validated = validate_rollback_authorization(root, apply_payload, authorization)
        self.assertEqual(validated["status"], "ready-for-governed-rollback")
        rollback_payload = perform_governed_rollback(
            root,
            apply_payload,
            authorization,
            confirm_receipt_fingerprint=str(apply_receipt["receipt_fingerprint"]),
            confirm_rollback_authorization_fingerprint=str(
                validated["rollback_authorization_fingerprint"]
            ),
            confirm_registry_current_sha256=str(apply_receipt["registry_after_sha256"]),
            acknowledge_reviewer_identity_unverified=True,
        )
        self.assertEqual(rollback_payload["status"], "rolled-back")
        self.assertEqual(registry.read_text(encoding="utf-8"), before_text)
        return temporary, root, apply_payload, rollback_payload, before_text

    def test_receipt_verifies_complete_apply_to_rollback_lifecycle(self) -> None:
        temporary, root, apply_payload, rollback_payload, before_text = self._lifecycle_fixture()
        self.addCleanup(temporary.cleanup)
        registry = root / REGISTRY_PATH

        receipt = build_governed_rollback_receipt(root, apply_payload, rollback_payload)
        second = build_governed_rollback_receipt(root, apply_payload, rollback_payload)

        self.assertEqual(receipt["status"], "verified-current-post-rollback-state")
        self.assertTrue(receipt["receipt_generated"])
        self.assertTrue(receipt["current_state_matches_rollback_result"])
        self.assertFalse(receipt["canonical_write_performed"])
        self.assertFalse(receipt["automatic_execution_enabled"])
        self.assertFalse(receipt["reviewer_identity_provider_verified"])
        self.assertFalse(receipt["reapply_ready"])
        self.assertTrue(receipt["requires_new_governed_apply"])
        self.assertFalse(receipt["original_apply_authorization_reusable"])
        self.assertFalse(receipt["rollback_authorization_reusable"])
        self.assertFalse(receipt["reapply_performed"])
        self.assertTrue(str(receipt["rollback_receipt_fingerprint"]).startswith("sha256:"))
        self.assertEqual(
            receipt["rollback_receipt_fingerprint"],
            second["rollback_receipt_fingerprint"],
        )
        self.assertEqual(registry.read_text(encoding="utf-8"), before_text)

    def test_post_rollback_drift_preserves_receipt_identity_but_marks_drift(self) -> None:
        temporary, root, apply_payload, rollback_payload, _before_text = self._lifecycle_fixture()
        self.addCleanup(temporary.cleanup)
        first = build_governed_rollback_receipt(root, apply_payload, rollback_payload)
        registry = root / REGISTRY_PATH
        registry.write_text('{"later":"legitimate-change"}\n', encoding="utf-8")

        drifted = build_governed_rollback_receipt(root, apply_payload, rollback_payload)

        self.assertEqual(drifted["status"], "post-rollback-state-drift")
        self.assertTrue(drifted["receipt_generated"])
        self.assertFalse(drifted["current_state_matches_rollback_result"])
        self.assertEqual(
            first["rollback_receipt_fingerprint"],
            drifted["rollback_receipt_fingerprint"],
        )
        self.assertEqual(drifted["reason_codes"], ["post-rollback-state-drift-detected"])
        self.assertFalse(drifted["reapply_ready"])

    def test_tampered_rollback_journal_blocks_receipt(self) -> None:
        temporary, root, apply_payload, rollback_payload, _before_text = self._lifecycle_fixture()
        self.addCleanup(temporary.cleanup)
        journal = root / str(rollback_payload["transaction"]["journal"])
        data = json.loads(journal.read_text(encoding="utf-8"))
        data["writes"][0]["path"] = "registry/other.jsonl"
        journal.write_text(json.dumps(data) + "\n", encoding="utf-8")

        receipt = build_governed_rollback_receipt(root, apply_payload, rollback_payload)

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn(
            "rollback-receipt-journal-write-path-mismatch",
            receipt["reason_codes"],
        )

    def test_missing_rollback_backup_blocks_receipt(self) -> None:
        temporary, root, apply_payload, rollback_payload, _before_text = self._lifecycle_fixture()
        self.addCleanup(temporary.cleanup)
        rollback_journal = str(rollback_payload["transaction"]["journal"])
        backup = root / rollback_journal.replace(
            "journal.json", "before/registry/items.jsonl"
        )
        backup.unlink()

        receipt = build_governed_rollback_receipt(root, apply_payload, rollback_payload)

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn("rollback-receipt-backup-missing", receipt["reason_codes"])

    def test_tampered_scope_in_result_blocks_receipt(self) -> None:
        temporary, root, apply_payload, rollback_payload, _before_text = self._lifecycle_fixture()
        self.addCleanup(temporary.cleanup)
        rollback_payload["rollback_scope"][0]["changed_fields"] = ["artifact_refs"]

        receipt = build_governed_rollback_receipt(root, apply_payload, rollback_payload)

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn("rollback-receipt-scope-mismatch", receipt["reason_codes"])

    def test_tampered_apply_journal_breaks_lifecycle_chain(self) -> None:
        temporary, root, apply_payload, rollback_payload, _before_text = self._lifecycle_fixture()
        self.addCleanup(temporary.cleanup)
        journal = root / str(apply_payload["transaction"]["journal"])
        data = json.loads(journal.read_text(encoding="utf-8"))
        data["status"] = "tampered"
        journal.write_text(json.dumps(data) + "\n", encoding="utf-8")

        receipt = build_governed_rollback_receipt(root, apply_payload, rollback_payload)

        self.assertEqual(receipt["status"], "blocked")
        self.assertTrue(
            any(str(reason).startswith("apply-receipt:") for reason in receipt["reason_codes"])
        )


if __name__ == "__main__":
    unittest.main()
