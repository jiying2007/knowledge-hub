from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile
import unittest
from typing import Dict, List, Optional, Tuple

from tools.codex_assets.knowledge_hub.operator_binding_authorization import (
    validate_binding_authorization,
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


class OperatorBindingAuthorizationTests(unittest.TestCase):
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
        material = {
            "project_id": row["project_id"],
            "field": row["field"],
            "target": row["target"],
            "current_value": row["current_value"],
            "proposed_reference": row["proposed_reference"],
            "proposed_value": row["proposed_value"],
            "mutation_intent": row["mutation_intent"],
            "candidate_snapshot": row["candidate_snapshot"],
        }
        row["proposal_fingerprint"] = _fingerprint(material)
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
        return temporary, root, row, bundle

    def _authorization(
        self,
        row: Dict[str, object],
        bundle: Dict[str, object],
        decision: str = "approve-binding",
    ) -> Dict[str, object]:
        return {
            "schema_version": 1,
            "review_bundle_fingerprint": bundle["review_bundle_fingerprint"],
            "patch_plan_fingerprint": bundle["patch_plan_fingerprint"],
            "authorizations": [
                {
                    "proposal_fingerprint": row["proposal_fingerprint"],
                    "authorization_id": "AUTH-20260916-001",
                    "owner_ref": {
                        "kind": "owner",
                        "ref": "owner://embedded-team",
                    },
                    "owner_decision": decision,
                    "reviewed_by": "human-owner@example",
                    "reviewed_at": "2026-09-16",
                    "reason": "Reviewed exact proposal and governed patch plan.",
                }
            ],
        }

    def test_approved_external_authorization_is_validated_but_not_applied(self) -> None:
        temporary, root, row, bundle = self._ready()
        self.addCleanup(temporary.cleanup)
        registry = root / "registry/items.jsonl"
        before = registry.read_text(encoding="utf-8")

        payload = validate_binding_authorization(
            root,
            bundle,
            self._authorization(row, bundle),
        )

        self.assertEqual(payload["status"], "ready-for-governed-apply")
        self.assertTrue(payload["authorization_validated"])
        self.assertFalse(payload["authorization_input_generated"])
        self.assertFalse(payload["reviewer_identity_provider_verified"])
        self.assertFalse(payload["apply_enabled"])
        self.assertFalse(payload["canonical_write_performed"])
        self.assertTrue(payload["requires_governed_apply"])
        self.assertEqual(payload["approved_count"], 1)
        self.assertEqual(payload["rejected_count"], 0)
        self.assertEqual(registry.read_text(encoding="utf-8"), before)

    def test_rejection_is_validated_and_never_ready_for_apply(self) -> None:
        temporary, root, row, bundle = self._ready()
        self.addCleanup(temporary.cleanup)

        payload = validate_binding_authorization(
            root,
            bundle,
            self._authorization(row, bundle, decision="reject-binding"),
        )

        self.assertEqual(payload["status"], "rejected-by-governance")
        self.assertTrue(payload["authorization_validated"])
        self.assertFalse(payload["requires_governed_apply"])
        self.assertEqual(payload["approved_count"], 0)
        self.assertEqual(payload["rejected_count"], 1)

    def test_owner_ref_must_match_canonical_contract(self) -> None:
        temporary, root, row, bundle = self._ready()
        self.addCleanup(temporary.cleanup)
        authorization = self._authorization(row, bundle)
        authorization["authorizations"][0]["owner_ref"] = {
            "kind": "owner",
            "ref": "owner://other-team",
        }

        payload = validate_binding_authorization(root, bundle, authorization)

        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(
            any(
                "authorization-owner-ref-mismatch" in reason
                for reason in payload["reason_codes"]
            )
        )

    def test_review_bundle_fingerprint_mismatch_fails_closed(self) -> None:
        temporary, root, row, bundle = self._ready()
        self.addCleanup(temporary.cleanup)
        authorization = self._authorization(row, bundle)
        authorization["review_bundle_fingerprint"] = "sha256:" + "f" * 64

        payload = validate_binding_authorization(root, bundle, authorization)

        self.assertEqual(payload["status"], "upstream-error")
        self.assertIn(
            "authorization-review-bundle-fingerprint-mismatch",
            payload["reason_codes"],
        )

    def test_registry_drift_invalidates_authorization(self) -> None:
        temporary, root, row, bundle = self._ready()
        self.addCleanup(temporary.cleanup)
        path = root / "registry/items.jsonl"
        item = json.loads(path.read_text(encoding="utf-8"))
        item["evidence_contract"]["source_refs"] = [
            {"kind": "git-commit", "ref": "github://drift"}
        ]
        path.write_text(json.dumps(item, ensure_ascii=False) + "\n", encoding="utf-8")

        payload = validate_binding_authorization(
            root,
            bundle,
            self._authorization(row, bundle),
        )

        self.assertEqual(payload["status"], "upstream-error")
        self.assertIn("authorization-registry-precondition-stale", payload["reason_codes"])

    def test_missing_reviewer_and_invalid_date_are_rejected(self) -> None:
        temporary, root, row, bundle = self._ready()
        self.addCleanup(temporary.cleanup)
        authorization = self._authorization(row, bundle)
        authorization["authorizations"][0]["reviewed_by"] = ""
        authorization["authorizations"][0]["reviewed_at"] = "2026-02-30"

        payload = validate_binding_authorization(root, bundle, authorization)

        self.assertEqual(payload["status"], "blocked")
        reasons = " ".join(payload["reason_codes"])
        self.assertIn("authorization-reviewed-by-missing", reasons)
        self.assertIn("authorization-reviewed-at-invalid", reasons)

    def test_reused_authorization_id_across_proposals_is_rejected(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        source = self._proposal_row()
        release = self._proposal_row(
            field="release_ref",
            ref="github-release://jiying2007/agent-dev-kit/55",
            current_value=None,
        )
        proposal = self._proposal([source, release])
        selected = [
            str(source["proposal_fingerprint"]),
            str(release["proposal_fingerprint"]),
        ]
        plan = build_binding_patch_plan(root, proposal, selected)
        bundle = build_binding_review_bundle(root, proposal, plan)
        authorization = {
            "schema_version": 1,
            "review_bundle_fingerprint": bundle["review_bundle_fingerprint"],
            "patch_plan_fingerprint": bundle["patch_plan_fingerprint"],
            "authorizations": [],
        }
        for row in (source, release):
            authorization["authorizations"].append(
                {
                    "proposal_fingerprint": row["proposal_fingerprint"],
                    "authorization_id": "AUTH-REUSED",
                    "owner_ref": {
                        "kind": "owner",
                        "ref": "owner://embedded-team",
                    },
                    "owner_decision": "approve-binding",
                    "reviewed_by": "human-owner@example",
                    "reviewed_at": "2026-09-16",
                    "reason": "Reviewed exact proposal.",
                }
            )

        payload = validate_binding_authorization(root, bundle, authorization)

        self.assertEqual(payload["status"], "blocked")
        self.assertIn("authorization-id-reused:AUTH-REUSED", payload["reason_codes"])


if __name__ == "__main__":
    unittest.main()
