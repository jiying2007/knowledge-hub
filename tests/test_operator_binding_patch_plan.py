from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile
import unittest
from typing import Dict, List, Optional, Tuple

from tools.codex_assets.knowledge_hub.operator_binding_patch_plan import (
    build_binding_patch_plan,
)


def _fingerprint(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:{}".format(hashlib.sha256(raw).hexdigest())


class OperatorBindingPatchPlanTests(unittest.TestCase):
    def _contract(self, status: str = "pending") -> Dict[str, object]:
        return {
            "schema_version": 1,
            "profile": "software-tool",
            "status": status,
            "owner_ref": {"kind": "owner", "ref": "owner://team"},
            "source_refs": [],
            "validation_refs": [],
            "artifact_refs": [],
            "device_refs": [],
            "release_ref": None,
            "rollback_ref": {"kind": "runbook", "ref": "doc://rollback"},
            "not_applicable": {},
            "member_project_ids": [],
        }

    def _root(
        self, contract: Optional[Dict[str, object]] = None
    ) -> Tuple[tempfile.TemporaryDirectory, pathlib.Path]:
        temporary = tempfile.TemporaryDirectory()
        root = pathlib.Path(temporary.name)
        (root / "registry").mkdir()
        item = {
            "id": "agent-dev-kit-readiness-validation-20260916",
            "project_id": "agent-dev-kit",
            "readiness_slot": "validation",
            "path": "projects/agent-dev-kit/validation/project-readiness.md",
            "evidence_contract": contract or self._contract(),
        }
        (root / "registry/items.jsonl").write_text(
            json.dumps(item, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return temporary, root

    def _row(
        self,
        field: str = "source_refs",
        ref: str = "",
        current_value: object = None,
    ) -> Dict[str, object]:
        if not ref:
            ref = "github://jiying2007/agent-dev-kit@" + "a" * 40
        kind = "github-source-revision"
        intent = "append-reference"
        if field == "validation_refs":
            kind = "github-workflow-run"
            intent = "append-reference"
        elif field == "artifact_refs":
            kind = "github-actions-artifact"
            intent = "append-reference"
        elif field == "release_ref":
            kind = "github-release"
            intent = "set-if-empty"
        if current_value is None and field != "release_ref":
            current_value = []
        proposed_reference = {"kind": kind, "ref": ref}
        if field == "release_ref":
            proposed_value = dict(proposed_reference)
        else:
            proposed_value = list(current_value) + [dict(proposed_reference)]
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
            "status": "needs-governed-review" if rows else "no-change",
            "read_only": True,
            "network_performed": False,
            "source_projection_network_performed": True,
            "canonical_write_performed": False,
            "automatic_binding_enabled": False,
            "automatic_execution_enabled": False,
            "proposal_only": True,
            "eligible_for_binding": False,
            "requires_governed_review": True,
            "candidate_count": len(rows),
            "proposal_count": len(rows),
            "already_present_count": 0,
            "blocked_conflict_count": 0,
            "unmappable_count": 0,
            "rows": rows,
            "upstream_contract_reason_codes": [],
        }

    def test_selected_source_proposal_builds_read_only_transaction_plan(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        row = self._row()
        proposal = self._proposal([row])
        registry = root / "registry/items.jsonl"
        before_text = registry.read_text(encoding="utf-8")

        payload = build_binding_patch_plan(
            root,
            proposal,
            [str(row["proposal_fingerprint"])],
        )

        self.assertEqual(payload["status"], "needs-governed-pr")
        self.assertTrue(payload["read_only"])
        self.assertFalse(payload["canonical_write_performed"])
        self.assertFalse(payload["apply_enabled"])
        self.assertFalse(payload["selection_is_authorization"])
        self.assertTrue(payload["requires_governed_pr"])
        self.assertEqual(payload["selected_proposal_count"], 1)
        self.assertEqual(payload["planned_item_count"], 1)
        self.assertEqual(payload["planned_write_count"], 1)
        self.assertEqual(payload["transaction_plan"]["changed_count"], 1)
        self.assertEqual(
            payload["transaction_plan"]["writes"][0]["expected_sha256"],
            payload["registry_before_sha256"],
        )
        self.assertNotEqual(
            payload["registry_before_sha256"],
            payload["registry_after_sha256"],
        )
        self.assertEqual(registry.read_text(encoding="utf-8"), before_text)

    def test_selection_is_required(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        row = self._row()

        payload = build_binding_patch_plan(root, self._proposal([row]), [])

        self.assertEqual(payload["status"], "blocked")
        self.assertIn("proposal-selection-required", payload["reason_codes"])
        self.assertEqual(payload["planned_write_count"], 0)

    def test_unknown_fingerprint_fails_closed(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        row = self._row()
        unknown = "sha256:" + "f" * 64

        payload = build_binding_patch_plan(
            root,
            self._proposal([row]),
            [unknown],
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(
            any(
                reason.startswith("selected-proposal-not-found:")
                for reason in payload["reason_codes"]
            )
        )

    def test_stale_canonical_field_fails_closed(self) -> None:
        contract = self._contract()
        contract["source_refs"] = [
            {"kind": "git-commit", "ref": "github://existing"}
        ]
        temporary, root = self._root(contract)
        self.addCleanup(temporary.cleanup)
        row = self._row(current_value=[])

        payload = build_binding_patch_plan(
            root,
            self._proposal([row]),
            [str(row["proposal_fingerprint"])],
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(
            any(
                "canonical-field-stale" in reason
                for reason in payload["reason_codes"]
            )
        )

    def test_non_pending_contract_cannot_be_planned(self) -> None:
        temporary, root = self._root(self._contract(status="ready"))
        self.addCleanup(temporary.cleanup)
        row = self._row()

        payload = build_binding_patch_plan(
            root,
            self._proposal([row]),
            [str(row["proposal_fingerprint"])],
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(
            any(
                "canonical-evidence-contract-not-pending" in reason
                for reason in payload["reason_codes"]
            )
        )
        self.assertFalse(payload["readiness_mutation_planned"])

    def test_tampered_candidate_snapshot_invalidates_proposal_fingerprint(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        row = self._row()
        fingerprint = str(row["proposal_fingerprint"])
        snapshot = dict(row["candidate_snapshot"])
        snapshot["ref"] = "github://tampered"
        row["candidate_snapshot"] = snapshot

        payload = build_binding_patch_plan(
            root,
            self._proposal([row]),
            [fingerprint],
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(
            any(
                "proposal-fingerprint-mismatch" in reason
                for reason in payload["reason_codes"]
            )
        )

    def test_same_target_field_multi_selection_is_rejected(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        first = self._row(
            ref="github://jiying2007/agent-dev-kit@" + "a" * 40
        )
        second = self._row(
            ref="github://jiying2007/agent-dev-kit@" + "b" * 40
        )

        payload = build_binding_patch_plan(
            root,
            self._proposal([first, second]),
            [
                str(first["proposal_fingerprint"]),
                str(second["proposal_fingerprint"]),
            ],
        )

        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(
            any(
                reason.startswith("multiple-proposals-same-target-field:")
                for reason in payload["reason_codes"]
            )
        )

    def test_different_fields_can_share_one_governed_patch_plan(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        source = self._row()
        release = self._row(
            field="release_ref",
            ref="github-release://jiying2007/agent-dev-kit/55",
            current_value=None,
        )

        payload = build_binding_patch_plan(
            root,
            self._proposal([source, release]),
            [
                str(source["proposal_fingerprint"]),
                str(release["proposal_fingerprint"]),
            ],
        )

        self.assertEqual(payload["status"], "needs-governed-pr")
        self.assertEqual(payload["selected_proposal_count"], 2)
        self.assertEqual(payload["planned_item_count"], 1)
        self.assertEqual(
            payload["rows"][0]["changed_fields"],
            ["release_ref", "source_refs"],
        )

    def test_upstream_proposal_contract_drift_is_error(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        row = self._row()
        proposal = self._proposal([row])
        proposal["automatic_binding_enabled"] = True

        payload = build_binding_patch_plan(
            root,
            proposal,
            [str(row["proposal_fingerprint"])],
        )

        self.assertEqual(payload["status"], "upstream-error")
        self.assertIn(
            "proposal-automatic-binding-enabled-invalid",
            payload["reason_codes"],
        )


if __name__ == "__main__":
    unittest.main()
