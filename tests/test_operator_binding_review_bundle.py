from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile
import unittest
from typing import Dict, List, Optional, Tuple
from unittest import mock

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


class OperatorBindingReviewBundleTests(unittest.TestCase):
    def _contract(self) -> Dict[str, object]:
        return {
            "schema_version": 1,
            "profile": "software-tool",
            "status": "pending",
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

    def _row(
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
        row = self._row()
        proposal = self._proposal([row])
        selected = [str(row["proposal_fingerprint"])]
        plan = build_binding_patch_plan(root, proposal, selected)
        self.assertEqual(plan["status"], "needs-governed-pr")
        return temporary, root, row, proposal, plan

    def test_review_bundle_is_deterministic_and_read_only(self) -> None:
        temporary, root, row, proposal, plan = self._ready()
        self.addCleanup(temporary.cleanup)
        registry = root / "registry/items.jsonl"
        before = registry.read_text(encoding="utf-8")

        payload = build_binding_review_bundle(root, proposal, plan)

        self.assertEqual(payload["status"], "needs-governed-authorization")
        self.assertTrue(payload["read_only"])
        self.assertFalse(payload["canonical_write_performed"])
        self.assertFalse(payload["apply_enabled"])
        self.assertFalse(payload["selection_is_authorization"])
        self.assertEqual(payload["authorization_state"], "not-provided")
        self.assertTrue(payload["requires_governed_authorization"])
        self.assertEqual(payload["review_row_count"], 1)
        self.assertEqual(payload["rows"][0]["field"], "source_refs")
        self.assertEqual(
            payload["rows"][0]["proposal_fingerprint"],
            row["proposal_fingerprint"],
        )
        self.assertEqual(payload["registry_before_sha256"], plan["registry_before_sha256"])
        self.assertEqual(payload["registry_after_sha256"], plan["registry_after_sha256"])
        self.assertTrue(payload["patch_plan_fingerprint"].startswith("sha256:"))
        self.assertTrue(payload["review_bundle_fingerprint"].startswith("sha256:"))
        self.assertTrue(payload["pr_review"]["authorization_required"])
        self.assertFalse(payload["pr_review"]["merge_automatically"])
        self.assertEqual(registry.read_text(encoding="utf-8"), before)

    def test_tampered_patch_plan_fails_recompute(self) -> None:
        temporary, root, _row, proposal, plan = self._ready()
        self.addCleanup(temporary.cleanup)
        plan = dict(plan)
        plan["registry_after_sha256"] = "f" * 64

        payload = build_binding_review_bundle(root, proposal, plan)

        self.assertEqual(payload["status"], "upstream-error")
        self.assertIn("patch-plan-recompute-mismatch", payload["reason_codes"])

    def test_stale_registry_invalidates_review_bundle(self) -> None:
        temporary, root, _row, proposal, plan = self._ready()
        self.addCleanup(temporary.cleanup)
        path = root / "registry/items.jsonl"
        item = json.loads(path.read_text(encoding="utf-8"))
        item["evidence_contract"]["source_refs"] = [
            {"kind": "git-commit", "ref": "github://drift"}
        ]
        path.write_text(json.dumps(item, ensure_ascii=False) + "\n", encoding="utf-8")

        payload = build_binding_review_bundle(root, proposal, plan)

        self.assertEqual(payload["status"], "upstream-error")
        self.assertIn("patch-plan-recompute-not-ready", payload["reason_codes"])

    def test_missing_selected_proposal_invalidates_bundle(self) -> None:
        temporary, root, _row, _proposal, plan = self._ready()
        self.addCleanup(temporary.cleanup)
        proposal = self._proposal([])

        payload = build_binding_review_bundle(root, proposal, plan)

        self.assertEqual(payload["status"], "upstream-error")
        self.assertIn("patch-plan-recompute-not-ready", payload["reason_codes"])

    def test_review_bundle_byte_budget_fails_closed(self) -> None:
        temporary, root, _row, proposal, plan = self._ready()
        self.addCleanup(temporary.cleanup)

        with mock.patch(
            "tools.codex_assets.knowledge_hub.operator_binding_review_bundle.MAX_REVIEW_BYTES",
            1,
        ):
            payload = build_binding_review_bundle(root, proposal, plan)

        self.assertEqual(payload["status"], "blocked")
        self.assertIn("review-bundle-byte-budget-exceeded", payload["reason_codes"])
        self.assertFalse(payload["apply_enabled"])


if __name__ == "__main__":
    unittest.main()
