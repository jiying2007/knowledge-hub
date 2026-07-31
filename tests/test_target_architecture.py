import datetime as dt
import json

import pytest

from tools.codex_assets.knowledge_hub.artifact_governance import (
    evaluate_artifact_governance,
    validate_immutable_artifact_ref,
)
from tools.codex_assets.knowledge_hub.command_surface import (
    DAILY_COMMANDS,
    PLANES,
    evaluate_command_surface,
)
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.complexity_budget import (
    evaluate_complexity_budget,
)
from tools.codex_assets.knowledge_hub.lifecycle_metrics import (
    lifecycle_operating_metrics,
)
from tools.codex_assets.knowledge_hub.maturity import evaluate_maturity_axes
from tools.codex_assets.knowledge_hub.output_contract import status_contract
from tools.codex_assets.knowledge_hub.recovery_evidence import (
    execution_environment_evidence,
    evidence_matches_current_execution,
)


def _jsonl(rows):
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)


def test_command_surface_catalog_matches_all_wrappers():
    payload = evaluate_command_surface(repository_root())

    assert payload["status"] == "pass"
    assert payload["daily_commands"] == sorted(DAILY_COMMANDS)
    assert payload["daily_count"] == 5
    assert payload["uncataloged_wrappers"] == []
    assert payload["missing_wrappers"] == []
    assert payload["summary_contract_errors"] == []
    assert payload["wrapper_growth"] == 0
    assert set(payload["by_plane"]) == set(PLANES)
    assert all(row["summary_json"] for row in payload["daily"])


def test_command_surface_rejects_false_summary_declaration_for_implemented_flag(
    tmp_path,
):
    (tmp_path / "registry").mkdir()
    (tmp_path / "tools/codex_assets/knowledge_hub").mkdir(parents=True)
    (tmp_path / "tools/knowledge-example.sh").write_text(
        "#!/usr/bin/env bash\n"
        "rtk bash tools/ci/python-runtime.sh "
        "-m tools.codex_assets.knowledge_hub.example_cli \"$@\"\n",
        encoding="utf-8",
    )
    (tmp_path / "tools/codex_assets/knowledge_hub/example_cli.py").write_text(
        'parser.add_argument("--summary-json", action="store_true")\n',
        encoding="utf-8",
    )
    (tmp_path / "registry/command-surface.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "model": "knowledge-hub-five-plane-command-surface-v1",
                "wrapper_baseline": 1,
                "daily_command_limit": 5,
                "planes": sorted(PLANES),
                "tiers": [
                    "daily",
                    "maintenance",
                    "governance",
                    "engineering",
                    "internal",
                ],
                "commands": [
                    {
                        "name": "knowledge-example",
                        "wrapper": "tools/knowledge-example.sh",
                        "plane": "query",
                        "tier": "internal",
                        "summary_json": False,
                        "read_only": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    payload = evaluate_command_surface(tmp_path)

    assert payload["status"] == "fail"
    assert payload["summary_contract_errors"] == ["knowledge-example"]
    assert "summary-json declaration differs from implementation" in payload["errors"]


def test_status_contract_v2_rejects_legacy_aliases():
    review = status_contract("needs-review")
    assert review["contract_version"] == 2
    assert review["status"] == "needs-review"
    assert review["default_exit_code"] == 0
    assert review["strict_exit_code"] == 1
    assert "canonical_status" not in review
    assert "legacy_status" not in review
    assert status_contract("needs-fix")["default_exit_code"] == 1
    for removed in ("ok", "fail", "needs-owner-review", "partial", "unknown-state"):
        with pytest.raises(ValueError, match="canonical status"):
            status_contract(removed)


def test_lifecycle_metrics_report_age_flow_lead_time_and_cold_candidates(tmp_path):
    (tmp_path / "registry").mkdir()
    (tmp_path / ".cache/knowledge-hub").mkdir(parents=True)
    (tmp_path / "registry/items.jsonl").write_text(
        _jsonl(
            [
                {
                    "id": "recent",
                    "status": "reviewing",
                    "created_at": "2026-07-28",
                },
                {
                    "id": "old",
                    "status": "reviewing",
                    "created_at": "2026-03-01",
                },
                {
                    "id": "accepted",
                    "status": "active",
                    "created_at": "2026-07-01",
                },
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "registry/lifecycle-events.jsonl").write_text(
        _jsonl(
            [
                {
                    "item_id": "accepted",
                    "event_type": "capture",
                    "before_status": "missing",
                    "after_status": "reviewing",
                    "executed_at": "2026-07-01T00:00:00Z",
                },
                {
                    "item_id": "accepted",
                    "event_type": "promote",
                    "before_status": "reviewing",
                    "after_status": "active",
                    "executed_at": "2026-07-05T00:00:00Z",
                },
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / ".cache/knowledge-hub/search-telemetry.jsonl").write_text(
        _jsonl(
            [
                {
                    "schema_version": 3,
                    "sample_kind": "interactive",
                    "interaction_contract": "knowledge-retrieval-interaction-v1",
                    "retrieval_kind": "search",
                    "interaction_id": "a" * 64,
                    "query_sha256": "b" * 64,
                    "recorded_at": "2026-07-29T00:00:00Z",
                    "result_ids": ["recent"],
                    "raw_query_stored": False,
                }
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / ".cache/knowledge-hub/context-telemetry.jsonl").write_text(
        "",
        encoding="utf-8",
    )

    payload = lifecycle_operating_metrics(
        tmp_path,
        dt.date(2026, 7, 30),
        cold_days=90,
    )

    assert payload["status"] == "pass"
    assert payload["reviewing_age_buckets"] == {
        "0-7": 1,
        "8-30": 0,
        "31-90": 0,
        ">90": 1,
    }
    assert payload["flow"]["to_active_count"] == 1
    assert payload["decision_lead_time_days"]["p50"] == 4.0
    assert payload["cold_candidates"]["sample"] == ["old"]
    assert payload["cold_candidates"]["automatic_delete"] is False


def test_complexity_budget_is_report_only_for_legacy_and_blocks_new_regression(
    tmp_path,
):
    (tmp_path / "registry").mkdir()
    (tmp_path / "tools/codex_assets/knowledge_hub").mkdir(parents=True)
    (tmp_path / "tools").mkdir(exist_ok=True)
    (tmp_path / "registry/engineering-budgets.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "python": {
                    "new_module_max_lines": 4,
                    "new_function_max_lines": 3,
                    "legacy_module_line_caps": {},
                },
                "commands": {
                    "wrapper_baseline": 0,
                    "daily_max": 5,
                    "readme_daily_max": 7,
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "tools/codex_assets/knowledge_hub/oversized.py").write_text(
        "def oversized():\n"
        "    value = 1\n"
        "    value += 1\n"
        "    value += 1\n"
        "    return value\n",
        encoding="utf-8",
    )

    payload = evaluate_complexity_budget(tmp_path)

    assert payload["status"] == "fail"
    assert payload["regression_count"] >= 1
    assert payload["legacy_attention_count"] == 0
    assert payload["report_only_legacy"] is True


def test_immutable_artifact_ref_requires_hash_size_owner_and_restore_contract():
    valid = {
        "schema_version": "knowledge-hub.immutable-artifact-ref.v1",
        "id": "artifact-a",
        "uri": "source://source-a/path.bin",
        "size": 12,
        "sha256": "a" * 64,
        "owner": "owner-a",
        "immutability": {
            "content_addressed": True,
            "identity": "sha256:" + "a" * 64,
        },
        "restore": {
            "mode": "source-registry-hash-verified",
            "source_id": "source-a",
            "source_path": "path.bin",
            "network_required": False,
        },
    }

    assert validate_immutable_artifact_ref(valid) == []
    invalid = dict(valid)
    invalid.pop("restore")
    assert "missing restore" in validate_immutable_artifact_ref(invalid)
    credential_uri = dict(valid, uri="https://user:secret@example.invalid/a")
    credential_uri["restore"] = {
        "mode": "external-uri-hash-verified",
        "network_required": True,
    }
    assert "unsafe uri" in validate_immutable_artifact_ref(credential_uri)


def test_artifact_budget_evaluator_passes_current_repository():
    payload = evaluate_artifact_governance(repository_root())

    assert payload["status"] == "pass"
    assert payload["automatic_delete"] is False
    assert payload["tracked"]["total_bytes"] <= payload["budget"]["tracked_max_bytes"]
    assert payload["immutable_refs"]["invalid_count"] == 0


def test_maturity_axes_keep_platform_independent_from_project_evidence():
    payload = evaluate_maturity_axes(
        platform_status="pass",
        content_status="needs-review",
        project_count=30,
        project_evidence_ready_count=0,
        owner_gate_open_count=4,
        review_queue_pending_count=12,
        adoption_ready=False,
        local_delivery_complete=True,
        remote_published=False,
        offsite_restore_verified=False,
    )

    assert payload["platform"]["status"] == "pass"
    assert payload["project_evidence"]["status"] == "needs-review"
    assert payload["delivery"]["status"] == "needs-review"
    assert payload["status"] == "needs-review"
    assert "overall_status" not in payload
    assert payload["terminal"] is False


def _github_environment(revision):
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": "jiying2007/knowledge-hub",
        "GITHUB_SHA": revision,
        "GITHUB_EVENT_NAME": "schedule",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_RUN_ID": "123456",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_WORKFLOW_REF": (
            "jiying2007/knowledge-hub/.github/workflows/recovery-drill.yml"
            "@refs/heads/main"
        ),
        "GITHUB_WORKFLOW_SHA": revision,
        "RUNNER_ENVIRONMENT": "github-hosted",
    }


def test_offsite_evidence_requires_trusted_run_identity_and_current_binding():
    revision = "a" * 40
    complete = _github_environment(revision)
    evidence = execution_environment_evidence(
        "head",
        revision,
        expected_repository="jiying2007/knowledge-hub",
        environment=complete,
    )

    assert evidence["remote_checkout_verified"] is True
    assert evidence["remote_published_ref_verified"] is True
    assert evidence["offsite_environment_verified"] is True
    assert len(evidence["evidence_sha256"]) == 64
    assert evidence_matches_current_execution(
        evidence,
        revision,
        expected_repository="jiying2007/knowledge-hub",
        environment=complete,
    )

    missing_run_id = dict(complete)
    missing_run_id["GITHUB_RUN_ID"] = ""
    degraded = execution_environment_evidence(
        "head",
        revision,
        expected_repository="jiying2007/knowledge-hub",
        environment=missing_run_id,
    )
    assert degraded["offsite_environment_verified"] is False

    different_run = dict(complete)
    different_run["GITHUB_RUN_ID"] = "987654"
    assert not evidence_matches_current_execution(
        evidence,
        revision,
        expected_repository="jiying2007/knowledge-hub",
        environment=different_run,
    )
