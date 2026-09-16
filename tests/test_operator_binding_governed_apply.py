from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile
import unittest
from typing import Dict, List, Optional, Tuple

from tools.codex_assets.knowledge_hub.common import file_sha256
from tools.codex_assets.knowledge_hub.operator_binding_authorization import (
    validate_binding_authorization,
)
from tools.codex_assets.knowledge_hub.operator_binding_governed_apply import (
    apply_governed_binding,
)
from tools.codex_assets.knowledge_hub.operator_binding_patch_plan import (
    build_binding_patch_plan,
)
from tools.codex_assets.knowledge_hub.operator_binding_review_bundle import (
    build_binding_review_bundle,
)


def _fingerprint(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:{}".format(hashlib.sha256(raw).hexdigest())


class OperatorBindingGovernedApplyTests(unittest.TestCase):
    def _contract(self) -> Dict[str, object]:
        return {
            "schema_version": 1,
            "profile": "software-tool",
            "status": "pending",
            "owner_ref": {"kind": "owner", "ref": "owner://embedded-team"},
            "source_refs": [],
            "validation_refs": [],
            "artifact_refs": [],
            "device_refs": [],
            "release_ref": None,
            "rollback_ref": {"kind": "runbook", "ref": "doc://rollback"},
            "not_applicable": {},
            "member_project_ids": [],
        }

    def _root(self) -> Tuple[tempfile.TemporaryDirectory, pathlib.Path]:
        temporary = tempfile.TemporaryDirectory()
        root = pathlib.Path(temporary.name)
        (root / "registry").mkdir()
        item = {
            "id": "agent-dev-kit-readiness-validation-20260916",
            "project_id": "agent-dev-kit",
            "readiness_slot": "validation",
            "path": "projects/agent-dev-kit/validation/project-readiness.md",
            "evidence_contract": self._contract(),
        }
        (root / "registry/items.jsonl").write_text(
            json.dumps(item, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return temporary, root

    def _proposal_row(
        self,
        field: str = "source_refs",
        ref: str = "",
        current_value: Optional[object] = None,
    ) -> Dict[str, object]:
        if not ref:
            ref = "github://jiying2007/agent-dev-kit@" + "a" * 40
        kind = "github-source-revision"
        intent = "append-reference"
        if field == "release_ref":
            kind = "github-release"
            intent = "set-if-empty"
        if current_value is None and field != "release_ref":
            current_value = []
        proposed_reference = {"kind": kind, "ref": ref}
        proposed_value = (
            dict(proposed_reference)
            if field == "release_ref"
            else list(current_value or []) + [dict(proposed_reference)]
        )
        snapshot = {
            "provider": "github",
            "kind": kind,
            "ref": ref,
            "provider_verified": True,
            "candidate_only": True,
            "eligible_for_binding": False,
            "details": {"exact_identity": True},
        }
        row: Dict[str, object] = {
            "project_id": "agent-dev-kit",
            "field": field,
            "provider": "github",
            "operation": "test-operation",
            "source_target": "jiying2007/agent-dev-kit",
            "kind": kind,
            "ref": ref,
            "proposal_status": "ready-for-governed-review",
            "proposal_ready_for_review": True,
            "requires_governed_review": True,
            "proposal_only": True,
            "candidate_only": True,
            "eligible_for_binding": False,
            "canonical_write_performed": False,
            "target": {
                "registry_path": "registry/items.jsonl",
                "item_id": "agent-dev-kit-readiness-validation-20260916",
                "project_id": "agent-dev-kit",
                "readiness_slot": "validation",
                "item_path": "projects/agent-dev-kit/validation/project-readiness.md",
                "contract_field": field,
                "evidence_profile": "software-tool",
            },
            "current_value": current_value,
            "proposed_reference": proposed_reference,
            "proposed_value": proposed_value,
            "mutation_intent": intent,
            "candidate_snapshot": snapshot,
            "candidate_snapshot_fingerprint": _fingerprint(snapshot),
            "status_mutation_planned": False,
            "owner_mutation_planned": False,
            "readiness_mutation_planned": False,
            "reason_codes": ["governed-review-required"],
        }
        row["proposal_fingerprint"] = _fingerprint(
            {
                "project_id": row["project_id"],
                "field": row["field"],
                "target": row["target"],
                "current_value": row["current_value"],
                "proposed_reference": row["proposed_reference"],
                "proposed_value": row["proposed_value"],
                "mutation_intent": row["mutation_intent"],
                "candidate_snapshot": row["candidate_snapshot"],
            }
        )
        return row

    def _proposal(self, rows: List[Dict[str, object]]) -> Dict[str, object]:
        return {
            "schema_version": 1,
            "projection": "knowledge-operator-binding-proposal-v1",
            "status": "needs-governed-review",
            "read_only": True,
            "network_performed": False,
            "source_projection_network_performed": True,
            "canonical_write_performed": False,
            "automatic_binding_enabled": False,
            "automatic_execution_enabled": False,
            "proposal_only": True,
            "candidate_only": True,
            "eligible_for_binding": False,
            "requires_governed_review": True,
            "status_mutation_planned": False,
            "owner_mutation_planned": False,
            "readiness_mutation_planned": False,
            "candidate_count": len(rows),
            "proposal_count": len(rows),
            "already_present_count": 0,
            "blocked_conflict_count": 0,
            "unmappable_count": 0,
            "rows": rows,
            "upstream_contract_reason_codes": [],
        }

    def _ready(self):
        temporary, root = self._root()
        row = self._proposal_row()
        proposal = self._proposal([row])
        selected = [str(row["proposal_fingerprint"])]
        plan = build_binding_patch_plan(root, proposal, selected)
        self.assertEqual(plan["status"], "needs-governed-pr")
        bundle = build_binding_review_bundle(root, proposal, plan)
        self.assertEqual(bundle["status"], "needs-governed-authorization")
        authorization = {
            "schema_version": 1,
            "review_bundle_fingerprint": bundle["review_bundle_fingerprint"],
            "patch_plan_fingerprint": bundle["patch_plan_fingerprint"],
            "authorizations": [
                {
                    "proposal_fingerprint": row["proposal_fingerprint"],
                    "authorization_id": "AUTH-20260916-APPLY-001",
                    "owner_ref": {
                        "kind": "owner",
                        "ref": "owner://embedded-team",
                    },
                    "owner_decision": "approve-binding",
                    "reviewed_by": "human-owner@example",
                    "reviewed_at": "2026-09-16",
                    "reason": "Reviewed exact governed binding transaction.",
                }
            ],
        }
        validated = validate_binding_authorization(root, bundle, authorization)
        self.assertEqual(validated["status"], "ready-for-governed-apply")
        return temporary, root, row, proposal, selected, bundle, authorization, validated

    def test_explicit_confirmed_apply_writes_only_registry_evidence(self) -> None:
        (
            temporary,
            root,
            row,
            proposal,
            selected,
            _bundle,
            authorization,
            validated,
        ) = self._ready()
        self.addCleanup(temporary.cleanup)
        before_sha = file_sha256(root / "registry/items.jsonl")

        payload = apply_governed_binding(
            root,
            proposal,
            selected,
            authorization,
            confirm_authorization_fingerprint=str(
                validated["authorization_fingerprint"]
            ),
            confirm_registry_before_sha256=before_sha,
        )

        self.assertEqual(payload["status"], "applied")
        self.assertTrue(payload["canonical_write_performed"])
        self.assertTrue(payload["apply_performed"])
        self.assertTrue(payload["explicit_operator_confirmation_verified"])
        self.assertFalse(payload["automatic_binding_enabled"])
        self.assertFalse(payload["automatic_execution_enabled"])
        self.assertFalse(payload["reviewer_identity_provider_verified"])
        self.assertFalse(payload["status_mutation_performed"])
        self.assertFalse(payload["owner_mutation_performed"])
        self.assertFalse(payload["readiness_mutation_performed"])
        self.assertEqual(payload["changed_paths"], ["registry/items.jsonl"])
        self.assertEqual(
            payload["registry_post_apply_sha256"],
            payload["registry_after_sha256"],
        )
        item = json.loads((root / "registry/items.jsonl").read_text().strip())
        contract = item["evidence_contract"]
        self.assertEqual(contract["status"], "pending")
        self.assertEqual(
            contract["owner_ref"],
            {"kind": "owner", "ref": "owner://embedded-team"},
        )
        self.assertEqual(contract["source_refs"], [row["proposed_reference"]])
        journal = root / payload["transaction"]["journal"]
        self.assertTrue(journal.is_file())

    def test_authorization_fingerprint_confirmation_is_mandatory(self) -> None:
        temporary, root, _row, proposal, selected, _bundle, authorization, validated = self._ready()
        self.addCleanup(temporary.cleanup)
        registry = root / "registry/items.jsonl"
        before = registry.read_text(encoding="utf-8")

        payload = apply_governed_binding(
            root,
            proposal,
            selected,
            authorization,
            confirm_authorization_fingerprint="sha256:" + "0" * 64,
            confirm_registry_before_sha256=file_sha256(registry),
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertFalse(payload["canonical_write_performed"])
        self.assertIn(
            "apply-confirm-authorization-fingerprint-mismatch",
            payload["reason_codes"],
        )
        self.assertNotEqual(validated["authorization_fingerprint"], "sha256:" + "0" * 64)
        self.assertEqual(registry.read_text(encoding="utf-8"), before)

    def test_registry_before_confirmation_is_mandatory(self) -> None:
        temporary, root, _row, proposal, selected, _bundle, authorization, validated = self._ready()
        self.addCleanup(temporary.cleanup)
        registry = root / "registry/items.jsonl"
        before = registry.read_text(encoding="utf-8")

        payload = apply_governed_binding(
            root,
            proposal,
            selected,
            authorization,
            confirm_authorization_fingerprint=str(validated["authorization_fingerprint"]),
            confirm_registry_before_sha256="0" * 64,
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertIn(
            "apply-confirm-registry-before-sha256-mismatch",
            payload["reason_codes"],
        )
        self.assertEqual(registry.read_text(encoding="utf-8"), before)

    def test_governance_rejection_never_applies(self) -> None:
        temporary, root, _row, proposal, selected, bundle, authorization, _validated = self._ready()
        self.addCleanup(temporary.cleanup)
        registry = root / "registry/items.jsonl"
        before = registry.read_text(encoding="utf-8")
        authorization["authorizations"][0]["owner_decision"] = "reject-binding"
        rejected = validate_binding_authorization(root, bundle, authorization)
        self.assertEqual(rejected["status"], "rejected-by-governance")

        payload = apply_governed_binding(
            root,
            proposal,
            selected,
            authorization,
            confirm_authorization_fingerprint=str(rejected["authorization_fingerprint"]),
            confirm_registry_before_sha256=file_sha256(registry),
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(
            any(
                reason.startswith("apply-authorization-not-ready:rejected-by-governance")
                for reason in payload["reason_codes"]
            )
        )
        self.assertEqual(registry.read_text(encoding="utf-8"), before)

    def test_workspace_drift_invalidates_chain_before_apply(self) -> None:
        temporary, root, _row, proposal, selected, _bundle, authorization, validated = self._ready()
        self.addCleanup(temporary.cleanup)
        registry = root / "registry/items.jsonl"
        payload = json.loads(registry.read_text().strip())
        payload["evidence_contract"]["validation_refs"] = [
            {"kind": "manual", "ref": "evidence://drift"}
        ]
        registry.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        drifted = registry.read_text(encoding="utf-8")

        result = apply_governed_binding(
            root,
            proposal,
            selected,
            authorization,
            confirm_authorization_fingerprint=str(validated["authorization_fingerprint"]),
            confirm_registry_before_sha256=str(validated["registry_before_sha256"]),
        )

        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["canonical_write_performed"])
        self.assertEqual(registry.read_text(encoding="utf-8"), drifted)


if __name__ == "__main__":
    unittest.main()
