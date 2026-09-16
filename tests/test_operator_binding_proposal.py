from __future__ import annotations

import json
import pathlib
import tempfile
import unittest

from tools.codex_assets.knowledge_hub.operator_binding_proposal import (
    build_binding_proposal,
)


class OperatorBindingProposalTests(unittest.TestCase):
    def _contract(self, profile: str = "software-tool") -> dict:
        return {
            "schema_version": 1,
            "profile": profile,
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

    def _root(self, contract: dict | None = None) -> tuple[tempfile.TemporaryDirectory, pathlib.Path]:
        temporary = tempfile.TemporaryDirectory()
        root = pathlib.Path(temporary.name)
        (root / "registry").mkdir()
        (root / "registry/project-routes.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "routes": [
                        {
                            "project_id": "agent-dev-kit",
                            "validation_path": "projects/agent-dev-kit/validation",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        item = {
            "id": "agent-dev-kit-readiness-validation-20260916",
            "project_id": "agent-dev-kit",
            "readiness_slot": "validation",
            "path": "projects/agent-dev-kit/validation/project-readiness.md",
            "evidence_contract": contract or self._contract(),
        }
        (root / "registry/items.jsonl").write_text(
            json.dumps(item) + "\n", encoding="utf-8"
        )
        return temporary, root

    def _candidate(self, kind: str, ref: str) -> dict:
        return {
            "provider": "github",
            "kind": kind,
            "ref": ref,
            "provenance": "github-read-only-api",
            "provider_verified": True,
            "candidate_only": True,
            "eligible_for_binding": False,
            "details": {},
        }

    def _row(self, field: str, kind: str, ref: str) -> dict:
        candidate = self._candidate(kind, ref)
        return {
            "project_id": "agent-dev-kit",
            "field": field,
            "provider": "github",
            "operation": "test-operation",
            "target": "jiying2007/agent-dev-kit",
            "kind": kind,
            "ref": ref,
            "qualification_status": "reviewable",
            "review_eligible": True,
            "requires_governed_review": True,
            "candidate_only": True,
            "eligible_for_binding": False,
            "reason_codes": ["review-floor-met"],
            "candidate": candidate,
        }

    def _qualification(self, rows: list[dict]) -> dict:
        reviewable = sum(
            1 for row in rows if row.get("qualification_status") == "reviewable"
        )
        rejected = sum(
            1 for row in rows if row.get("qualification_status") == "rejected"
        )
        return {
            "schema_version": 1,
            "projection": "knowledge-operator-candidate-qualification-v1",
            "status": "needs-governed-review" if reviewable else "no-reviewable-candidate",
            "read_only": True,
            "network_performed": False,
            "source_projection_network_performed": True,
            "canonical_write_performed": False,
            "automatic_binding_enabled": False,
            "automatic_execution_enabled": False,
            "candidate_only": True,
            "eligible_for_binding": False,
            "requires_governed_review": True,
            "candidate_count": len(rows),
            "reviewable_count": reviewable,
            "rejected_count": rejected,
            "truncated": False,
            "source_error_count": 0,
            "upstream_contract_reason_codes": [],
            "rows": rows,
        }

    def test_list_reference_builds_append_only_governed_proposal(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        qualification = self._qualification(
            [
                self._row(
                    "source_refs",
                    "github-source-revision",
                    "github://jiying2007/agent-dev-kit@" + "a" * 40,
                )
            ]
        )

        payload = build_binding_proposal(root, qualification)

        self.assertEqual(payload["status"], "needs-governed-review")
        self.assertEqual(payload["proposal_count"], 1)
        self.assertFalse(payload["canonical_write_performed"])
        self.assertFalse(payload["automatic_binding_enabled"])
        self.assertFalse(payload["automatic_execution_enabled"])
        self.assertFalse(payload["eligible_for_binding"])
        row = payload["rows"][0]
        self.assertEqual(row["proposal_status"], "ready-for-governed-review")
        self.assertEqual(row["mutation_intent"], "append-reference")
        self.assertTrue(row["proposal_ready_for_review"])
        self.assertFalse(row["eligible_for_binding"])
        self.assertEqual(
            row["target"]["item_path"],
            "projects/agent-dev-kit/validation/project-readiness.md",
        )
        self.assertEqual(row["target"]["contract_field"], "source_refs")
        self.assertEqual(len(row["proposed_value"]), 1)
        self.assertTrue(row["proposal_fingerprint"].startswith("sha256:"))

    def test_proposal_is_deterministic(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        qualification = self._qualification(
            [
                self._row(
                    "validation_refs",
                    "github-workflow-run",
                    "github-actions://jiying2007/agent-dev-kit/runs/123",
                )
            ]
        )

        first = build_binding_proposal(root, qualification)
        second = build_binding_proposal(root, qualification)

        self.assertEqual(
            first["rows"][0]["proposal_fingerprint"],
            second["rows"][0]["proposal_fingerprint"],
        )
        self.assertEqual(first["rows"][0]["proposed_value"], second["rows"][0]["proposed_value"])

    def test_release_is_set_only_when_empty(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        qualification = self._qualification(
            [
                self._row(
                    "release_ref",
                    "github-release",
                    "github-release://jiying2007/agent-dev-kit/55",
                )
            ]
        )

        payload = build_binding_proposal(root, qualification)

        row = payload["rows"][0]
        self.assertEqual(row["proposal_status"], "ready-for-governed-review")
        self.assertEqual(row["mutation_intent"], "set-if-empty")
        self.assertEqual(
            row["proposed_value"],
            {
                "kind": "github-release",
                "ref": "github-release://jiying2007/agent-dev-kit/55",
            },
        )

    def test_existing_reference_is_no_change(self) -> None:
        contract = self._contract()
        contract["source_refs"] = [
            {
                "kind": "github-source-revision",
                "ref": "github://jiying2007/agent-dev-kit@" + "b" * 40,
            }
        ]
        temporary, root = self._root(contract)
        self.addCleanup(temporary.cleanup)
        qualification = self._qualification(
            [
                self._row(
                    "source_refs",
                    "github-source-revision",
                    "github://jiying2007/agent-dev-kit@" + "b" * 40,
                )
            ]
        )

        payload = build_binding_proposal(root, qualification)

        self.assertEqual(payload["status"], "no-change")
        self.assertEqual(payload["already_present_count"], 1)
        self.assertEqual(payload["rows"][0]["mutation_intent"], "none")

    def test_conflicting_single_release_never_plans_overwrite(self) -> None:
        contract = self._contract()
        contract["release_ref"] = {
            "kind": "github-release",
            "ref": "github-release://jiying2007/agent-dev-kit/44",
        }
        temporary, root = self._root(contract)
        self.addCleanup(temporary.cleanup)
        qualification = self._qualification(
            [
                self._row(
                    "release_ref",
                    "github-release",
                    "github-release://jiying2007/agent-dev-kit/55",
                )
            ]
        )

        payload = build_binding_proposal(root, qualification)

        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["blocked_conflict_count"], 1)
        row = payload["rows"][0]
        self.assertEqual(row["proposal_status"], "blocked-conflict")
        self.assertEqual(row["mutation_intent"], "none")
        self.assertIn("canonical-single-value-conflict", row["reason_codes"])

    def test_authorized_not_applicable_is_not_silently_reversed(self) -> None:
        contract = self._contract()
        contract["artifact_refs"] = []
        contract["not_applicable"] = {
            "artifact_refs": {
                "owner_ref": "owner://team",
                "authorization_id": "auth-1",
                "reason": "no distributable artifact",
            }
        }
        temporary, root = self._root(contract)
        self.addCleanup(temporary.cleanup)
        qualification = self._qualification(
            [
                self._row(
                    "artifact_refs",
                    "github-actions-artifact",
                    "github-actions-artifact://jiying2007/agent-dev-kit/77",
                )
            ]
        )

        payload = build_binding_proposal(root, qualification)

        row = payload["rows"][0]
        self.assertEqual(row["proposal_status"], "blocked-conflict")
        self.assertIn("approved-not-applicable-conflict", row["reason_codes"])

    def test_field_not_required_by_profile_is_unmappable(self) -> None:
        contract = self._contract("control-plane")
        temporary, root = self._root(contract)
        self.addCleanup(temporary.cleanup)
        qualification = self._qualification(
            [
                self._row(
                    "artifact_refs",
                    "github-actions-artifact",
                    "github-actions-artifact://jiying2007/agent-dev-kit/77",
                )
            ]
        )

        payload = build_binding_proposal(root, qualification)

        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["unmappable_count"], 1)
        self.assertIn(
            "field-not-required-by-evidence-profile",
            payload["rows"][0]["reason_codes"],
        )

    def test_route_or_item_drift_fails_closed(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        (root / "registry/project-routes.json").write_text(
            json.dumps({"schema_version": 2, "routes": []}), encoding="utf-8"
        )
        qualification = self._qualification(
            [
                self._row(
                    "source_refs",
                    "github-source-revision",
                    "github://jiying2007/agent-dev-kit@" + "c" * 40,
                )
            ]
        )

        payload = build_binding_proposal(root, qualification)

        self.assertEqual(payload["status"], "blocked")
        self.assertIn("canonical-route-not-unique", payload["rows"][0]["reason_codes"])
        self.assertFalse(payload["rows"][0]["proposal_ready_for_review"])

    def test_qualification_trust_boundary_is_fail_closed(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        qualification = self._qualification(
            [
                self._row(
                    "source_refs",
                    "github-source-revision",
                    "github://jiying2007/agent-dev-kit@" + "d" * 40,
                )
            ]
        )
        qualification["automatic_binding_enabled"] = True

        payload = build_binding_proposal(root, qualification)

        self.assertEqual(payload["status"], "upstream-error")
        self.assertEqual(payload["rows"], [])
        self.assertIn(
            "qualification-automatic-binding-enabled-invalid",
            payload["upstream_contract_reason_codes"],
        )

    def test_truncated_qualification_never_produces_proposals(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        qualification = self._qualification(
            [
                self._row(
                    "source_refs",
                    "github-source-revision",
                    "github://jiying2007/agent-dev-kit@" + "e" * 40,
                )
            ]
        )
        qualification["truncated"] = True

        payload = build_binding_proposal(root, qualification)

        self.assertEqual(payload["status"], "upstream-error")
        self.assertIn("qualification-truncated", payload["upstream_contract_reason_codes"])

    def test_rejected_qualification_rows_do_not_become_proposals(self) -> None:
        temporary, root = self._root()
        self.addCleanup(temporary.cleanup)
        row = self._row(
            "source_refs",
            "github-source-revision",
            "github://jiying2007/agent-dev-kit@" + "f" * 40,
        )
        row["qualification_status"] = "rejected"
        row["review_eligible"] = False
        row["reason_codes"] = ["provider-not-verified"]
        qualification = self._qualification([row])

        payload = build_binding_proposal(root, qualification)

        self.assertEqual(payload["status"], "no-change")
        self.assertEqual(payload["candidate_count"], 0)
        self.assertEqual(payload["rows"], [])


if __name__ == "__main__":
    unittest.main()
