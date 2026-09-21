from __future__ import annotations

import json
import pathlib
from unittest import mock

from tools.codex_assets.knowledge_hub.operator_auto_route import (
    build_unique_execution_routes,
)
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance





def _write_policy(root):
    registry = pathlib.Path(root) / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    (registry / "ai-operations-policy.json").write_text(
        json.dumps(
            {
                "evidence_binding": {
                    "machine_ratchet_fields": [
                        "artifact_refs",
                        "source_refs",
                        "validation_refs",
                    ],
                    "human_authorization_fields": ["release_ref"],
                    "machine_ratchet_mutation_intent": "append-reference",
                    "machine_ratchet_may_change_owner": False,
                    "machine_ratchet_may_change_status": False,
                    "machine_ratchet_may_change_readiness": False,
                    "machine_ratchet_may_auto_promote_evidence_ready": False,
                    "machine_validation_requires_source_revision_match": True,
                    "machine_artifact_kinds": ["github-release-asset"],
                    "machine_artifact_requires_validation_run_match": False,
                    "machine_artifact_requires_source_revision_match": True,
                    "machine_artifact_requires_immutable_release": True,
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (registry / "items.jsonl").write_text(
        json.dumps(
            {
                "id": "item-1",
                "project_id": "project-1",
                "evidence_contract": {
                    "status": "pending",
                    "source_refs": [
                        {
                            "kind": "github-source-revision",
                            "ref": "github://example/repo@" + "1" * 40,
                        }
                    ],
                    "validation_refs": [
                        {
                            "kind": "github-workflow-run",
                            "ref": "github-actions://example/repo/runs/123",
                        }
                    ],
                    "artifact_refs": [],
                    "release_ref": None,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _row(
    *,
    item_id="item-1",
    field="source_refs",
    fingerprint="sha256:" + "a" * 64,
    provider_verified=True,
):
    kind_by_field = {
        "source_refs": "github-source-revision",
        "validation_refs": "github-workflow-run",
        "artifact_refs": "github-release-asset",
        "release_ref": "github-release",
    }
    kind = kind_by_field[field]
    ref = {
        "source_refs": "github://example/repo@" + "1" * 40,
        "validation_refs": "github-actions://example/repo/runs/123",
        "artifact_refs": "github-release-asset://example/repo/456",
        "release_ref": "github-release://example/repo/789",
    }[field]
    return {
        "project_id": "project-1",
        "field": field,
        "provider": "github",
        "proposal_status": "ready-for-governed-review",
        "proposal_ready_for_review": True,
        "proposal_fingerprint": fingerprint,
        "mutation_intent": (
            "set-if-empty" if field == "release_ref" else "append-reference"
        ),
        "target": {
            "registry_path": "registry/items.jsonl",
            "item_id": item_id,
            "project_id": "project-1",
        },
        "current_value": None if field == "release_ref" else [],
        "proposed_reference": {"kind": kind, "ref": ref},
        "candidate_snapshot": {
            "provider": "github",
            "provider_verified": provider_verified,
            "candidate_only": True,
            "eligible_for_binding": False,
            "provenance": "github-read-only-api",
            "kind": kind,
            "ref": ref,
            "details": {
                "repository": "example/repo",
                "exact_identity": field == "source_refs",
                "commit_sha": "1" * 40 if field == "source_refs" else "",
                "run_id": "123" if field == "validation_refs" else "",
                "head_sha": "1" * 40 if field == "validation_refs" else "",
                "release_immutable": field == "artifact_refs",
                "release_draft": False,
                "release_prerelease": False,
                "release_tag_commit_sha": (
                    "1" * 40 if field == "artifact_refs" else ""
                ),
            },
        },
        "status_mutation_planned": False,
        "owner_mutation_planned": False,
        "readiness_mutation_planned": False,
    }


def _proposal(rows):
    return {
        "projection": "knowledge-operator-binding-proposal-v1",
        "read_only": True,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "proposal_only": True,
        "blocked_conflict_count": 0,
        "unmappable_count": 0,
        "rows": rows,
    }


def _plan(selected):
    return {
        "status": "needs-governed-pr",
        "planned_write_count": 1,
        "status_mutation_planned": False,
        "owner_mutation_planned": False,
        "readiness_mutation_planned": False,
        "selected_proposal_fingerprints": list(selected),
    }


def _plan_side_effect(_root, _proposal, selected):
    return _plan(selected)


def test_append_only_verified_evidence_routes_to_machine_ratchet(tmp_path):
    for index, field in enumerate(
        ("source_refs", "validation_refs", "artifact_refs"), 1
    ):
        _write_policy(tmp_path)
        row = _row(
            field=field,
            item_id="item-1",
            fingerprint="sha256:" + str(index) * 64,
        )
        with mock.patch(
            "tools.codex_assets.knowledge_hub.operator_auto_route."
            "build_binding_patch_plan",
            side_effect=_plan_side_effect,
        ), mock.patch(
            "tools.codex_assets.knowledge_hub.operator_auto_route."
            "build_binding_review_bundle"
        ) as review:
            result = build_unique_execution_routes(
                pathlib.Path(tmp_path), _proposal([row])
            )

        assert result["status"] == "ready-for-machine-ratchet"
        assert result["machine_ratchet_count"] == 1
        assert result["human_authorization_count"] == 0
        assert (
            result["machine_route"]["authorization_class"]
            == "autonomous-low-risk-ratchet"
        )
        assert result["machine_route"]["automatic_execution_enabled"] is False
        review.assert_not_called()


def test_release_ref_remains_human_authorization(tmp_path):
    _write_policy(tmp_path)
    row = _row(field="release_ref")
    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_patch_plan",
        side_effect=_plan_side_effect,
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_review_bundle",
        return_value={"status": "needs-governed-authorization"},
    ):
        result = build_unique_execution_routes(
            pathlib.Path(tmp_path), _proposal([row])
        )

    assert result["status"] == "needs-governed-authorization"
    assert result["machine_ratchet_count"] == 0
    assert result["human_authorization_count"] == 1
    assert result["human_route"]["authorization_class"] == "human-authorization"


def test_mixed_unique_evidence_is_partitioned_without_cross_authorization(tmp_path):
    _write_policy(tmp_path)
    machine = _row(
        field="source_refs",
        item_id="item-machine",
        fingerprint="sha256:" + "a" * 64,
    )
    human = _row(
        field="release_ref",
        item_id="item-human",
        fingerprint="sha256:" + "b" * 64,
    )
    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_patch_plan",
        side_effect=_plan_side_effect,
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_review_bundle",
        return_value={"status": "needs-governed-authorization"},
    ):
        result = build_unique_execution_routes(
            pathlib.Path(tmp_path), _proposal([machine, human])
        )

    assert result["status"] == "mixed-routing"
    assert result["machine_ratchet_count"] == 1
    assert result["human_authorization_count"] == 1
    assert result["machine_route"]["selected_proposal_fingerprints"] == [
        "sha256:" + "a" * 64
    ]
    assert result["human_route"]["selected_proposal_fingerprints"] == [
        "sha256:" + "b" * 64
    ]


def test_unverified_append_only_candidate_falls_back_to_human(tmp_path):
    _write_policy(tmp_path)
    row = _row(field="artifact_refs", provider_verified=False)
    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_patch_plan",
        side_effect=_plan_side_effect,
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_review_bundle",
        return_value={"status": "needs-governed-authorization"},
    ):
        result = build_unique_execution_routes(
            pathlib.Path(tmp_path), _proposal([row])
        )

    assert result["status"] == "needs-governed-authorization"
    assert result["machine_ratchet_count"] == 0
    assert result["human_authorization_count"] == 1


def test_ambiguous_target_blocks_both_routes(tmp_path):
    _write_policy(tmp_path)
    first = _row(fingerprint="sha256:" + "a" * 64)
    second = _row(fingerprint="sha256:" + "b" * 64)
    result = build_unique_execution_routes(
        pathlib.Path(tmp_path), _proposal([first, second])
    )

    assert result["status"] == "ambiguous"
    assert result["selected_proposal_count"] == 0
    assert result["ambiguous_target_count"] == 1
    assert result["machine_ratchet_count"] == 0
    assert result["human_authorization_count"] == 0


def test_machine_route_fails_closed_on_patch_plan_mutation_drift(tmp_path):
    _write_policy(tmp_path)
    row = _row()
    unsafe = _plan([row["proposal_fingerprint"]])
    unsafe["readiness_mutation_planned"] = True
    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_patch_plan",
        return_value=unsafe,
    ):
        result = build_unique_execution_routes(
            pathlib.Path(tmp_path), _proposal([row])
        )

    assert result["status"] == "blocked"
    assert result["machine_route"]["status"] == "blocked"
    assert "machine-readiness-mutation-planned-invalid" in result[
        "machine_route"
    ]["reason_codes"]


def test_machine_route_fails_closed_when_policy_expands_or_weakens(tmp_path):
    _write_policy(tmp_path)
    policy_path = tmp_path / "registry/ai-operations-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["evidence_binding"]["machine_ratchet_fields"].append("release_ref")
    policy_path.write_text(json.dumps(policy) + "\n", encoding="utf-8")

    result = build_unique_execution_routes(
        pathlib.Path(tmp_path), _proposal([_row()])
    )

    assert result["status"] == "blocked"
    assert result["machine_ratchet_count"] == 0
    assert result["human_authorization_count"] == 0
    assert result["reason_codes"][0].startswith("machine-policy-invalid:")


def test_machine_route_output_matches_catalog_contract(tmp_path):
    _write_policy(tmp_path)
    row = _row()
    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_patch_plan",
        side_effect=_plan_side_effect,
    ):
        result = build_unique_execution_routes(
            pathlib.Path(tmp_path), _proposal([row])
        )

    assert (
        validate_instance(
            repository_root(),
            "operator-auto-route-v1",
            result,
        )["status"]
        == "pass"
    )


def test_auto_router_is_in_mypy_surface():
    pyproject = pathlib.Path("pyproject.toml").read_text(encoding="utf-8")
    assert '"tools/codex_assets/knowledge_hub/operator_auto_route.py"' in pyproject


def test_validation_from_different_source_revision_falls_back_to_human(tmp_path):
    _write_policy(tmp_path)
    row = _row(field="validation_refs")
    row["candidate_snapshot"]["details"]["head_sha"] = "9" * 40
    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_patch_plan",
        side_effect=_plan_side_effect,
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_review_bundle",
        return_value={"status": "needs-governed-authorization"},
    ):
        result = build_unique_execution_routes(
            pathlib.Path(tmp_path), _proposal([row])
        )

    assert result["status"] == "needs-governed-authorization"
    assert result["machine_ratchet_count"] == 0
    assert result["human_authorization_count"] == 1


def test_actions_artifact_stays_human_even_when_provider_verified(tmp_path):
    _write_policy(tmp_path)
    row = _row(field="artifact_refs")
    row["proposed_reference"] = {
        "kind": "github-actions-artifact",
        "ref": "github-actions-artifact://example/repo/456",
    }
    row["candidate_snapshot"]["kind"] = "github-actions-artifact"
    row["candidate_snapshot"]["ref"] = row["proposed_reference"]["ref"]
    row["candidate_snapshot"]["details"] = {
        "artifact_id": "456",
        "digest": "sha256:" + "d" * 64,
        "workflow_run_id": "123",
        "workflow_run_head_sha": "1" * 40,
        "expired": False,
    }
    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_patch_plan",
        side_effect=_plan_side_effect,
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_review_bundle",
        return_value={"status": "needs-governed-authorization"},
    ):
        result = build_unique_execution_routes(
            pathlib.Path(tmp_path), _proposal([row])
        )

    assert result["status"] == "needs-governed-authorization"
    assert result["machine_ratchet_count"] == 0
    assert result["human_authorization_count"] == 1


def test_immutable_release_asset_from_different_source_stays_human(tmp_path):
    _write_policy(tmp_path)
    row = _row(field="artifact_refs")
    row["candidate_snapshot"]["details"]["release_tag_commit_sha"] = "9" * 40
    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_patch_plan",
        side_effect=_plan_side_effect,
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_auto_route."
        "build_binding_review_bundle",
        return_value={"status": "needs-governed-authorization"},
    ):
        result = build_unique_execution_routes(
            pathlib.Path(tmp_path), _proposal([row])
        )

    assert result["status"] == "needs-governed-authorization"
    assert result["machine_ratchet_count"] == 0
    assert result["human_authorization_count"] == 1
