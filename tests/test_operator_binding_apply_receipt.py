from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile
import unittest
from typing import Dict, Tuple

from tools.codex_assets.knowledge_hub.common import file_sha256
from tools.codex_assets.knowledge_hub.operator_binding_apply_receipt import (
    build_governed_apply_receipt,
)
from tools.codex_assets.knowledge_hub.store import RepositoryTransaction


class OperatorBindingApplyReceiptTests(unittest.TestCase):
    def _sha256_text(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _applied_fixture(
        self,
    ) -> Tuple[tempfile.TemporaryDirectory, pathlib.Path, Dict[str, object]]:
        temporary = tempfile.TemporaryDirectory()
        root = pathlib.Path(temporary.name)
        (root / "registry").mkdir()
        before_text = json.dumps(
            {"id": "receipt-test", "evidence_contract": {"status": "pending", "source_refs": []}},
            sort_keys=True,
        ) + "\n"
        after_text = json.dumps(
            {
                "id": "receipt-test",
                "evidence_contract": {
                    "status": "pending",
                    "source_refs": [{"kind": "github-source-revision", "ref": "github://example/repo@" + "1" * 40}],
                },
            },
            sort_keys=True,
        ) + "\n"
        registry = root / "registry/items.jsonl"
        registry.write_text(before_text, encoding="utf-8")
        before_sha256 = file_sha256(registry)
        after_sha256 = self._sha256_text(after_text)
        authorization_fingerprint = "sha256:" + "a" * 64
        transaction_id = "kh-operator-binding-apply-" + "a" * 16
        transaction = RepositoryTransaction(root, transaction_id=transaction_id)
        transaction.add_text(
            "registry/items.jsonl",
            after_text,
            expected_sha256=before_sha256,
        )
        result = transaction.apply()
        self.assertEqual(result.status, "applied")
        self.assertEqual(file_sha256(registry), after_sha256)
        payload: Dict[str, object] = {
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
            "authorization_fingerprint": authorization_fingerprint,
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
            "registry_path": "registry/items.jsonl",
            "registry_before_sha256": before_sha256,
            "registry_after_sha256": after_sha256,
            "registry_post_apply_sha256": after_sha256,
            "status_mutation_performed": False,
            "owner_mutation_performed": False,
            "readiness_mutation_performed": False,
            "failure_rollback_enabled": True,
            "changed_paths": ["registry/items.jsonl"],
            "transaction": result.to_dict(),
            "reason_codes": ["explicit-governed-apply-completed"],
        }
        return temporary, root, payload

    def test_receipt_verifies_real_transaction_journal_and_backup(self) -> None:
        temporary, root, payload = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        registry = root / "registry/items.jsonl"
        current = registry.read_text(encoding="utf-8")

        receipt = build_governed_apply_receipt(root, payload)
        second = build_governed_apply_receipt(root, payload)

        self.assertEqual(receipt["status"], "verified-current-post-apply-state")
        self.assertTrue(receipt["receipt_generated"])
        self.assertTrue(receipt["rollback_ready"])
        self.assertFalse(receipt["rollback_performed"])
        self.assertFalse(receipt["canonical_write_performed"])
        self.assertFalse(receipt["automatic_execution_enabled"])
        self.assertFalse(receipt["reviewer_identity_provider_verified"])
        self.assertEqual(
            receipt["rollback_plan"]["status"],
            "ready-for-separate-governed-rollback",
        )
        self.assertEqual(
            receipt["rollback_plan"]["expected_current_sha256"],
            payload["registry_after_sha256"],
        )
        self.assertEqual(
            receipt["rollback_plan"]["restore_sha256"],
            payload["registry_before_sha256"],
        )
        self.assertEqual(receipt["receipt_fingerprint"], second["receipt_fingerprint"])
        self.assertEqual(registry.read_text(encoding="utf-8"), current)

    def test_registry_drift_keeps_receipt_but_blocks_rollback_readiness(self) -> None:
        temporary, root, payload = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        registry = root / "registry/items.jsonl"
        registry.write_text('{"later":"legitimate-change"}\n', encoding="utf-8")
        drifted = registry.read_text(encoding="utf-8")

        receipt = build_governed_apply_receipt(root, payload)

        self.assertEqual(receipt["status"], "post-apply-state-drift")
        self.assertTrue(receipt["receipt_generated"])
        self.assertFalse(receipt["rollback_ready"])
        self.assertEqual(receipt["rollback_plan"]["status"], "not-ready-current-drift")
        self.assertEqual(
            receipt["reason_codes"], ["rollback-blocked-current-registry-drift"]
        )
        self.assertEqual(registry.read_text(encoding="utf-8"), drifted)

    def test_missing_before_backup_blocks_receipt(self) -> None:
        temporary, root, payload = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        backup = root / str(
            payload["transaction"]["journal"]
        ).replace("journal.json", "before/registry/items.jsonl")
        backup.unlink()

        receipt = build_governed_apply_receipt(root, payload)

        self.assertEqual(receipt["status"], "blocked")
        self.assertFalse(receipt["receipt_generated"])
        self.assertIn("apply-receipt-before-backup-missing", receipt["reason_codes"])

    def test_tampered_before_backup_blocks_receipt(self) -> None:
        temporary, root, payload = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        backup = root / str(
            payload["transaction"]["journal"]
        ).replace("journal.json", "before/registry/items.jsonl")
        backup.write_text("tampered\n", encoding="utf-8")

        receipt = build_governed_apply_receipt(root, payload)

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn(
            "apply-receipt-before-backup-sha-mismatch", receipt["reason_codes"]
        )

    def test_tampered_journal_write_scope_blocks_receipt(self) -> None:
        temporary, root, payload = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        journal = root / str(payload["transaction"]["journal"])
        data = json.loads(journal.read_text(encoding="utf-8"))
        data["writes"][0]["path"] = "registry/other.jsonl"
        journal.write_text(json.dumps(data) + "\n", encoding="utf-8")

        receipt = build_governed_apply_receipt(root, payload)

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn(
            "apply-receipt-journal-write-path-mismatch", receipt["reason_codes"]
        )

    def test_apply_identity_boundary_cannot_be_upgraded_in_receipt(self) -> None:
        temporary, root, payload = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        payload["reviewer_identity_provider_verified"] = True

        receipt = build_governed_apply_receipt(root, payload)

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn(
            "apply-receipt-reviewer-identity-provider-verified-invalid",
            receipt["reason_codes"],
        )

    def test_transaction_identity_must_match_authorization_fingerprint(self) -> None:
        temporary, root, payload = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        payload["transaction"]["transaction_id"] = "kh-operator-binding-apply-ffffffffffffffff"

        receipt = build_governed_apply_receipt(root, payload)

        self.assertEqual(receipt["status"], "blocked")
        self.assertIn("apply-receipt-transaction-id-mismatch", receipt["reason_codes"])


if __name__ == "__main__":
    unittest.main()
