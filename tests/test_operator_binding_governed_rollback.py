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
from tools.codex_assets.knowledge_hub.store import RepositoryTransaction


class OperatorBindingGovernedRollbackTests(unittest.TestCase):
    def _sha256_text(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _owner(self, suffix: str) -> Dict[str, str]:
        return {"kind": "owner", "ref": "owner://{}".format(suffix)}

    def _item(
        self,
        item_id: str,
        project_id: str,
        owner: Dict[str, str],
        refs: List[Dict[str, str]],
    ) -> Dict[str, object]:
        return {
            "id": item_id,
            "project_id": project_id,
            "readiness_slot": "validation",
            "path": "projects/{}/validation/project-readiness.md".format(project_id),
            "evidence_contract": {
                "schema_version": 1,
                "profile": "software-tool",
                "status": "pending",
                "owner_ref": owner,
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

    def _jsonl(self, rows: List[Dict[str, object]]) -> str:
        return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)

    def _applied_fixture(
        self,
    ) -> Tuple[
        tempfile.TemporaryDirectory,
        pathlib.Path,
        Dict[str, object],
        str,
    ]:
        temporary = tempfile.TemporaryDirectory()
        root = pathlib.Path(temporary.name)
        (root / "registry").mkdir()
        before_rows = [
            self._item("item-alpha", "alpha", self._owner("team-alpha"), []),
            self._item("item-beta", "beta", self._owner("team-beta"), []),
        ]
        after_rows = [
            self._item(
                "item-alpha",
                "alpha",
                self._owner("team-alpha"),
                [{"kind": "github-source-revision", "ref": "github://example/alpha@" + "1" * 40}],
            ),
            self._item(
                "item-beta",
                "beta",
                self._owner("team-beta"),
                [{"kind": "github-source-revision", "ref": "github://example/beta@" + "2" * 40}],
            ),
        ]
        before_text = self._jsonl(before_rows)
        after_text = self._jsonl(after_rows)
        registry = root / "registry/items.jsonl"
        registry.write_text(before_text, encoding="utf-8")
        before_sha256 = file_sha256(registry)
        after_sha256 = self._sha256_text(after_text)
        apply_authorization_fingerprint = "sha256:" + "a" * 64
        transaction_id = "kh-operator-binding-apply-" + "a" * 16
        transaction = RepositoryTransaction(root, transaction_id=transaction_id)
        transaction.add_text(REGISTRY_PATH, after_text, expected_sha256=before_sha256)
        result = transaction.apply()
        self.assertEqual(result.status, "applied")
        self.assertEqual(file_sha256(registry), after_sha256)
        selected = sorted(["sha256:" + "d" * 64, "sha256:" + "e" * 64])
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
            "authorization_fingerprint": apply_authorization_fingerprint,
            "reviewer_identity_provider_verified": False,
            "explicit_operator_confirmation_verified": True,
            "reviewer_identity_boundary_acknowledged": True,
            "review_bundle_fingerprint": "sha256:" + "b" * 64,
            "patch_plan_fingerprint": "sha256:" + "c" * 64,
            "selected_proposal_fingerprints": selected,
            "selected_proposal_count": len(selected),
            "authorization_count": 2,
            "approved_count": 2,
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
            "transaction": result.to_dict(),
            "reason_codes": ["explicit-governed-apply-completed"],
        }
        return temporary, root, payload, before_text

    def _authorization(
        self,
        root: pathlib.Path,
        payload: Dict[str, object],
        *,
        decision: str = "approve-rollback",
    ) -> Dict[str, object]:
        receipt = build_governed_apply_receipt(root, payload)
        self.assertTrue(receipt["rollback_ready"])
        return {
            "schema_version": 1,
            "receipt_fingerprint": receipt["receipt_fingerprint"],
            "transaction_id": receipt["transaction_id"],
            "apply_authorization_fingerprint": receipt["authorization_fingerprint"],
            "registry_after_sha256": receipt["registry_after_sha256"],
            "registry_restore_sha256": receipt["registry_before_sha256"],
            "authorizations": [
                {
                    "item_id": "item-alpha",
                    "project_id": "alpha",
                    "item_path": "projects/alpha/validation/project-readiness.md",
                    "owner_ref": self._owner("team-alpha"),
                    "authorization_id": "ROLLBACK-ALPHA-001",
                    "owner_decision": decision,
                    "reviewed_by": "alpha-owner@example",
                    "reviewed_at": "2026-09-16",
                    "reason": "Reviewed the exact apply receipt and rollback scope.",
                },
                {
                    "item_id": "item-beta",
                    "project_id": "beta",
                    "item_path": "projects/beta/validation/project-readiness.md",
                    "owner_ref": self._owner("team-beta"),
                    "authorization_id": "ROLLBACK-BETA-001",
                    "owner_decision": decision,
                    "reviewed_by": "beta-owner@example",
                    "reviewed_at": "2026-09-16",
                    "reason": "Reviewed the exact apply receipt and rollback scope.",
                },
            ],
        }

    def _validated(
        self,
        root: pathlib.Path,
        payload: Dict[str, object],
        authorization: Dict[str, object],
    ) -> Dict[str, object]:
        validated = validate_rollback_authorization(root, payload, authorization)
        self.assertEqual(validated["status"], "ready-for-governed-rollback")
        return validated

    def test_validate_requires_all_changed_items_and_is_read_only(self) -> None:
        temporary, root, payload, _before_text = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        registry = root / REGISTRY_PATH
        current = registry.read_text(encoding="utf-8")
        authorization = self._authorization(root, payload)

        validated = self._validated(root, payload, authorization)

        self.assertTrue(validated["rollback_authorization_validated"])
        self.assertTrue(validated["rollback_ready"])
        self.assertFalse(validated["canonical_write_performed"])
        self.assertFalse(validated["rollback_performed"])
        self.assertFalse(validated["reviewer_identity_provider_verified"])
        self.assertEqual(validated["authorization_count"], 2)
        self.assertEqual(
            [row["item_id"] for row in validated["rollback_scope"]],
            ["item-alpha", "item-beta"],
        )
        self.assertEqual(registry.read_text(encoding="utf-8"), current)

    def test_explicit_governed_rollback_restores_exact_before_registry(self) -> None:
        temporary, root, payload, before_text = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        authorization = self._authorization(root, payload)
        validated = self._validated(root, payload, authorization)
        receipt = build_governed_apply_receipt(root, payload)
        original_apply_journal = root / str(payload["transaction"]["journal"])

        result = perform_governed_rollback(
            root,
            payload,
            authorization,
            confirm_receipt_fingerprint=str(receipt["receipt_fingerprint"]),
            confirm_rollback_authorization_fingerprint=str(
                validated["rollback_authorization_fingerprint"]
            ),
            confirm_registry_current_sha256=str(receipt["registry_after_sha256"]),
            acknowledge_reviewer_identity_unverified=True,
        )

        self.assertEqual(result["status"], "rolled-back")
        self.assertTrue(result["rollback_performed"])
        self.assertTrue(result["canonical_write_performed"])
        self.assertFalse(result["automatic_execution_enabled"])
        self.assertFalse(result["reviewer_identity_provider_verified"])
        self.assertTrue(result["reviewer_identity_boundary_acknowledged"])
        self.assertFalse(result["status_mutation_performed"])
        self.assertFalse(result["owner_mutation_performed"])
        self.assertFalse(result["readiness_mutation_performed"])
        self.assertEqual(result["changed_paths"], [REGISTRY_PATH])
        self.assertEqual((root / REGISTRY_PATH).read_text(encoding="utf-8"), before_text)
        rollback_journal = root / result["transaction"]["journal"]
        self.assertTrue(rollback_journal.is_file())
        self.assertNotEqual(rollback_journal, original_apply_journal)
        self.assertEqual(
            json.loads(original_apply_journal.read_text(encoding="utf-8"))["status"],
            "applied",
        )

    def test_rejection_never_rolls_back(self) -> None:
        temporary, root, payload, _before_text = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        registry = root / REGISTRY_PATH
        current = registry.read_text(encoding="utf-8")
        authorization = self._authorization(root, payload, decision="reject-rollback")
        rejected = validate_rollback_authorization(root, payload, authorization)

        result = perform_governed_rollback(
            root,
            payload,
            authorization,
            confirm_receipt_fingerprint="sha256:" + "0" * 64,
            confirm_rollback_authorization_fingerprint=str(
                rejected.get("rollback_authorization_fingerprint", "")
            ),
            confirm_registry_current_sha256=file_sha256(registry),
            acknowledge_reviewer_identity_unverified=True,
        )

        self.assertEqual(rejected["status"], "rejected-by-governance")
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["canonical_write_performed"])
        self.assertEqual(registry.read_text(encoding="utf-8"), current)

    def test_owner_ref_mismatch_blocks_rollback_authorization(self) -> None:
        temporary, root, payload, _before_text = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        authorization = self._authorization(root, payload)
        authorization["authorizations"][0]["owner_ref"] = self._owner("wrong-owner")

        validated = validate_rollback_authorization(root, payload, authorization)

        self.assertEqual(validated["status"], "blocked")
        self.assertTrue(
            any("rollback-authorization-owner-ref-mismatch" in reason for reason in validated["reason_codes"])
        )

    def test_missing_changed_item_authorization_blocks(self) -> None:
        temporary, root, payload, _before_text = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        authorization = self._authorization(root, payload)
        authorization["authorizations"] = authorization["authorizations"][:1]

        validated = validate_rollback_authorization(root, payload, authorization)

        self.assertEqual(validated["status"], "blocked")
        self.assertIn(
            "rollback-authorization-item-coverage-invalid:item-beta",
            validated["reason_codes"],
        )

    def test_current_registry_drift_blocks_before_any_rollback_write(self) -> None:
        temporary, root, payload, _before_text = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        authorization = self._authorization(root, payload)
        registry = root / REGISTRY_PATH
        registry.write_text('{"later":"legitimate-change"}\n', encoding="utf-8")
        drifted = registry.read_text(encoding="utf-8")

        validated = validate_rollback_authorization(root, payload, authorization)

        self.assertEqual(validated["status"], "blocked")
        self.assertIn(
            "rollback-receipt-not-ready:post-apply-state-drift",
            validated["reason_codes"],
        )
        self.assertEqual(registry.read_text(encoding="utf-8"), drifted)

    def test_explicit_confirmations_and_identity_ack_are_mandatory(self) -> None:
        temporary, root, payload, _before_text = self._applied_fixture()
        self.addCleanup(temporary.cleanup)
        registry = root / REGISTRY_PATH
        current = registry.read_text(encoding="utf-8")
        authorization = self._authorization(root, payload)
        validated = self._validated(root, payload, authorization)
        receipt = build_governed_apply_receipt(root, payload)

        result = perform_governed_rollback(
            root,
            payload,
            authorization,
            confirm_receipt_fingerprint=str(receipt["receipt_fingerprint"]),
            confirm_rollback_authorization_fingerprint=str(
                validated["rollback_authorization_fingerprint"]
            ),
            confirm_registry_current_sha256=str(receipt["registry_after_sha256"]),
            acknowledge_reviewer_identity_unverified=False,
        )

        self.assertEqual(result["status"], "blocked")
        self.assertIn(
            "rollback-reviewer-identity-boundary-acknowledgement-required",
            result["reason_codes"],
        )
        self.assertEqual(registry.read_text(encoding="utf-8"), current)


REGISTRY_PATH = "registry/items.jsonl"


if __name__ == "__main__":
    unittest.main()
