from __future__ import annotations

import unittest

from tools.codex_assets.knowledge_hub.operator_candidate_qualification import (
    MAX_REVIEW_CANDIDATES,
    qualify_provider_projection,
)


class OperatorCandidateQualificationTests(unittest.TestCase):
    def _execution(self, field: str, candidate: dict) -> dict:
        return {
            "schema_version": 1,
            "projection": "knowledge-operator-github-provider-v1",
            "status": "pass",
            "read_only": True,
            "network_performed": True,
            "canonical_write_performed": False,
            "automatic_binding_enabled": False,
            "error_count": 0,
            "results": [
                {
                    "project_id": "agent-dev-kit",
                    "field": field,
                    "provider": "github",
                    "operation": "test-operation",
                    "target": "jiying2007/agent-dev-kit",
                    "candidates": [candidate],
                }
            ],
        }

    def _candidate(self, kind: str, ref: str, details: dict) -> dict:
        return {
            "provider": "github",
            "kind": kind,
            "ref": ref,
            "provenance": "github-read-only-api",
            "provider_verified": True,
            "candidate_only": True,
            "eligible_for_binding": False,
            "details": details,
        }

    def test_exact_source_revision_is_reviewable_but_never_binding_eligible(self) -> None:
        candidate = self._candidate(
            "github-source-revision",
            "github://jiying2007/agent-dev-kit@abc123",
            {
                "repository": "jiying2007/agent-dev-kit",
                "commit_sha": "abc123",
                "exact_identity": True,
            },
        )
        payload = qualify_provider_projection(self._execution("source_refs", candidate))

        self.assertEqual(payload["status"], "needs-governed-review")
        self.assertEqual(payload["reviewable_count"], 1)
        self.assertFalse(payload["eligible_for_binding"])
        self.assertFalse(payload["automatic_binding_enabled"])
        self.assertFalse(payload["automatic_execution_enabled"])
        row = payload["rows"][0]
        self.assertTrue(row["review_eligible"])
        self.assertTrue(row["requires_governed_review"])
        self.assertFalse(row["eligible_for_binding"])
        self.assertEqual(row["reason_codes"], ["review-floor-met"])

    def test_successful_workflow_run_requires_exact_head_sha(self) -> None:
        candidate = self._candidate(
            "github-workflow-run",
            "github-actions://jiying2007/agent-dev-kit/runs/123",
            {"run_id": "123", "head_sha": "", "conclusion": "success"},
        )
        payload = qualify_provider_projection(
            self._execution("validation_refs", candidate)
        )

        row = payload["rows"][0]
        self.assertFalse(row["review_eligible"])
        self.assertIn("validation-head-sha-missing", row["reason_codes"])
        self.assertEqual(payload["rejected_count"], 1)

    def test_artifact_without_digest_is_rejected(self) -> None:
        candidate = self._candidate(
            "github-actions-artifact",
            "github-actions-artifact://jiying2007/agent-dev-kit/44",
            {
                "artifact_id": "44",
                "digest": "",
                "expired": False,
            },
        )
        payload = qualify_provider_projection(self._execution("artifact_refs", candidate))

        row = payload["rows"][0]
        self.assertFalse(row["review_eligible"])
        self.assertIn("artifact-digest-missing", row["reason_codes"])

    def test_immutable_release_is_reviewable(self) -> None:
        candidate = self._candidate(
            "github-release",
            "github-release://jiying2007/agent-dev-kit/55",
            {
                "release_id": "55",
                "tag_name": "v5.1.0",
                "immutable": True,
                "draft": False,
                "prerelease": False,
                "meets_immutable_release_policy": True,
            },
        )
        payload = qualify_provider_projection(self._execution("release_ref", candidate))

        self.assertEqual(payload["reviewable_count"], 1)
        self.assertTrue(payload["rows"][0]["review_eligible"])

    def test_mutable_tag_cannot_qualify_as_release_evidence(self) -> None:
        candidate = self._candidate(
            "github-tag",
            "github-tag://jiying2007/agent-dev-kit/v5.1.0",
            {"tag_name": "v5.1.0", "meets_immutable_release_policy": False},
        )
        payload = qualify_provider_projection(self._execution("release_ref", candidate))

        row = payload["rows"][0]
        self.assertFalse(row["review_eligible"])
        self.assertIn("candidate-kind-does-not-match-field", row["reason_codes"])

    def test_upstream_contract_violation_rejects_otherwise_valid_candidate(self) -> None:
        candidate = self._candidate(
            "github-source-revision",
            "github://jiying2007/agent-dev-kit@abc123",
            {
                "repository": "jiying2007/agent-dev-kit",
                "commit_sha": "abc123",
                "exact_identity": True,
            },
        )
        execution = self._execution("source_refs", candidate)
        execution["automatic_binding_enabled"] = True
        payload = qualify_provider_projection(execution)

        self.assertEqual(payload["status"], "upstream-error")
        self.assertEqual(
            payload["upstream_contract_reason_codes"],
            ["upstream-automatic-binding-state-invalid"],
        )
        self.assertFalse(payload["rows"][0]["review_eligible"])

    def test_candidate_that_claims_binding_eligibility_is_rejected(self) -> None:
        candidate = self._candidate(
            "github-source-revision",
            "github://jiying2007/agent-dev-kit@abc123",
            {
                "repository": "jiying2007/agent-dev-kit",
                "commit_sha": "abc123",
                "exact_identity": True,
            },
        )
        candidate["eligible_for_binding"] = True
        payload = qualify_provider_projection(self._execution("source_refs", candidate))

        row = payload["rows"][0]
        self.assertFalse(row["review_eligible"])
        self.assertIn("binding-state-not-false", row["reason_codes"])
        self.assertFalse(row["eligible_for_binding"])

    def test_projection_is_bounded_and_marks_truncation(self) -> None:
        candidate = self._candidate(
            "github-source-revision",
            "github://jiying2007/agent-dev-kit@abc123",
            {
                "repository": "jiying2007/agent-dev-kit",
                "commit_sha": "abc123",
                "exact_identity": True,
            },
        )
        execution = self._execution("source_refs", candidate)
        execution["results"][0]["candidates"] = [
            dict(candidate) for _ in range(MAX_REVIEW_CANDIDATES + 1)
        ]
        payload = qualify_provider_projection(execution)

        self.assertEqual(payload["candidate_count"], MAX_REVIEW_CANDIDATES)
        self.assertTrue(payload["truncated"])

    def test_source_provider_errors_keep_projection_fail_closed(self) -> None:
        execution = self._execution(
            "source_refs",
            self._candidate(
                "github-source-revision",
                "github://jiying2007/agent-dev-kit@abc123",
                {
                    "repository": "jiying2007/agent-dev-kit",
                    "commit_sha": "abc123",
                    "exact_identity": True,
                },
            ),
        )
        execution["error_count"] = 1
        payload = qualify_provider_projection(execution)

        self.assertEqual(payload["status"], "upstream-error")
        self.assertEqual(payload["source_error_count"], 1)
        self.assertEqual(payload["reviewable_count"], 1)
        self.assertFalse(payload["eligible_for_binding"])


if __name__ == "__main__":
    unittest.main()
