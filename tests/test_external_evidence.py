import copy
import json
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub import external_evidence
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
GIT_SHA = "d" * 40


def _base(gap_id, classification):
    return {
        "schema_version": external_evidence.INPUT_SCHEMA,
        "gap_id": gap_id,
        "source_revision": GIT_SHA,
        "observed_at": "2026-09-14T02:00:00Z",
        "evidence_source_refs": ["run://production/123", "artifact://receipt/456"],
        "origin": {
            "classification": classification,
            "environment_id_sha256": SHA_A,
            "synthetic": False,
            "mock": False,
            "fixture": False,
            "static_adapter": False,
            "local_only": False,
        },
    }


def _case(**values):
    result = {"status": "pass", "origin": "real-provider"}
    result.update(values)
    return result


def _provider_evidence():
    payload = _base("connector-provider-pilot", "real-provider")
    payload.update(
        {
            "provider": {
                "name": "feishu",
                "version": "open-api-2026-09",
                "adapter_commit": GIT_SHA,
                "account_id_sha256": SHA_B,
                "transport": "feishu-open-api",
                "network_observed": True,
            },
            "cases": {
                "incremental_checkpoint": _case(
                    before_cursor_sha256=SHA_A,
                    after_cursor_sha256=SHA_B,
                    checkpoint_advanced=True,
                    idempotent_replay=True,
                ),
                "acl_change": _case(
                    before_acl_sha256=SHA_A,
                    after_acl_sha256=SHA_C,
                    propagated=True,
                ),
                "tombstone": _case(
                    object_id_sha256=SHA_B,
                    delete_observed=True,
                ),
                "retry_backoff": _case(
                    attempts=2,
                    backoff_observed=True,
                    provider_response_observed=True,
                ),
                "freshness": _case(
                    sample_count=12,
                    slo_seconds=120,
                    p95_seconds=42.5,
                ),
                "quarantine": _case(
                    case_id_sha256=SHA_C,
                    checkpoint_advanced=False,
                    dead_letter_or_quarantine_observed=True,
                ),
                "stays_at_source": _case(
                    canonical_write_performed=False,
                    auto_promotion=False,
                ),
            },
        }
    )
    return payload


def _retrieval_evidence():
    payload = _base("production-retrieval-eval", "real-production")
    payload["evaluation"] = {
        "case_count": 220,
        "production_derived_case_count": 220,
        "synthetic_case_count": 0,
        "dataset_sha256": SHA_B,
        "evaluator_version": "eval-v2.4",
        "approved_baseline": "prod-2026-08",
        "window_start": "2026-08-01T00:00:00Z",
        "window_end": "2026-09-01T00:00:00Z",
        "metrics": {
            "recall": 0.91,
            "mrr": 0.88,
            "ndcg": 0.9,
            "authority_recall": 0.99,
            "forbidden_hit_rate": 0.0,
            "p50_ms": 23.0,
            "p95_ms": 81.0,
        },
        "comparison": {
            "status": "pass",
            "new_critical_failures": 0,
            "result_sha256": SHA_C,
        },
    }
    return payload


def _production_case(**values):
    result = {"status": "pass", "origin": "real-production"}
    result.update(values)
    return result


def _memory_evidence():
    payload = _base("memory-lifecycle-pilot", "real-production")
    payload["pilot"] = {
        "runtime_version": "knowledge-runtime-v3",
        "window_start": "2026-08-01T00:00:00Z",
        "window_end": "2026-09-01T00:00:00Z",
        "result_sha256": SHA_B,
        "cases": {
            "ttl": _production_case(expiry_verified=True),
            "forget": _production_case(deletion_verified=True),
            "supersede": _production_case(old_state_hidden=True),
            "principal_isolation": _production_case(cross_boundary_leak_count=0),
            "agent_isolation": _production_case(cross_boundary_leak_count=0),
            "scope_isolation": _production_case(cross_boundary_leak_count=0),
            "scope_delete": _production_case(deletion_verified=True),
            "durable_consolidation": _production_case(
                candidate_only=True,
                provenance_bound=True,
                owner_gate_observed=True,
                canonical_write_performed=False,
            ),
        },
    }
    return payload


def _adoption_evidence():
    payload = _base("real-adoption-evidence", "real-production")
    payload["adoption"] = {
        "runtime_version": "knowledge-hub-2026.09",
        "window_start": "2026-08-01T00:00:00Z",
        "window_end": "2026-09-01T00:00:00Z",
        "observation_days": 31,
        "valid_real_calls": 44,
        "synthetic_calls": 0,
        "explicit_feedback_count": 12,
        "call_ledger_sha256": SHA_B,
        "feedback_sha256": SHA_C,
        "slo": {
            "status": "pass",
            "p50_ms": 41.0,
            "p95_ms": 125.0,
            "error_rate": 0.01,
            "retrieval_lane_health": "pass",
        },
        "traceability": {
            "status": "pass",
            "work_item_run_handoff_receipt_linked": True,
        },
        "privacy": {
            "raw_query_stored": False,
            "raw_task_stored": False,
            "raw_prompt_stored": False,
            "raw_content_stored": False,
            "network_export_mode": "disabled",
        },
    }
    return payload


@pytest.mark.parametrize(
    ("payload", "gap_id"),
    [
        (_provider_evidence(), "connector-provider-pilot"),
        (_retrieval_evidence(), "production-retrieval-eval"),
        (_memory_evidence(), "memory-lifecycle-pilot"),
        (_adoption_evidence(), "real-adoption-evidence"),
    ],
)
def test_real_external_evidence_produces_bounded_closure_receipt(payload, gap_id):
    receipt = external_evidence.validate_external_evidence(payload, expected_gap=gap_id)
    assert receipt["status"] == "pass"
    assert receipt["closure_ready"] is True
    assert receipt["gap_id"] == gap_id
    assert receipt["source_revision"] == GIT_SHA
    assert receipt["synthetic_evidence_accepted"] is False
    assert receipt["mock_evidence_accepted"] is False
    assert receipt["local_only_evidence_accepted"] is False
    assert receipt["canonical_write_performed"] is False
    assert len(receipt["evidence_payload_sha256"]) == 64
    assert receipt["generated_at"] == payload["observed_at"]


@pytest.mark.parametrize("flag", external_evidence.PROHIBITED_ORIGIN_FLAGS)
def test_external_evidence_rejects_prohibited_origin_flags(flag):
    payload = _provider_evidence()
    payload["origin"][flag] = True
    with pytest.raises(KnowledgeHubError, match="explicitly false"):
        external_evidence.validate_external_evidence(payload)


def test_provider_pilot_rejects_static_transport_and_stale_freshness():
    payload = _provider_evidence()
    payload["provider"]["transport"] = "static"
    with pytest.raises(KnowledgeHubError, match="real provider API transport"):
        external_evidence.validate_external_evidence(payload)

    payload = _provider_evidence()
    payload["cases"]["freshness"]["p95_seconds"] = 121
    with pytest.raises(KnowledgeHubError, match="exceeds declared SLO"):
        external_evidence.validate_external_evidence(payload)


def test_provider_pilot_rejects_acl_without_real_change_and_quarantine_checkpoint_advance():
    payload = _provider_evidence()
    payload["cases"]["acl_change"]["after_acl_sha256"] = SHA_A
    with pytest.raises(KnowledgeHubError, match="real ACL change"):
        external_evidence.validate_external_evidence(payload)

    payload = _provider_evidence()
    payload["cases"]["quarantine"]["checkpoint_advanced"] = True
    with pytest.raises(KnowledgeHubError, match="must be false"):
        external_evidence.validate_external_evidence(payload)


def test_retrieval_evidence_rejects_synthetic_padding_and_insufficient_production_cases():
    payload = _retrieval_evidence()
    payload["evaluation"]["case_count"] = 199
    payload["evaluation"]["production_derived_case_count"] = 199
    with pytest.raises(KnowledgeHubError, match="below minimum"):
        external_evidence.validate_external_evidence(payload)

    payload = _retrieval_evidence()
    payload["evaluation"]["synthetic_case_count"] = 1
    with pytest.raises(KnowledgeHubError, match="entirely production-derived"):
        external_evidence.validate_external_evidence(payload)


def test_retrieval_evidence_rejects_forbidden_hits_or_new_critical_failures():
    payload = _retrieval_evidence()
    payload["evaluation"]["metrics"]["forbidden_hit_rate"] = 0.01
    with pytest.raises(KnowledgeHubError, match="zero forbidden-hit rate"):
        external_evidence.validate_external_evidence(payload)

    payload = _retrieval_evidence()
    payload["evaluation"]["comparison"]["new_critical_failures"] = 1
    with pytest.raises(KnowledgeHubError, match="new critical failures"):
        external_evidence.validate_external_evidence(payload)


def test_memory_evidence_rejects_cross_boundary_leak_or_canonical_write():
    payload = _memory_evidence()
    payload["pilot"]["cases"]["scope_isolation"]["cross_boundary_leak_count"] = 1
    with pytest.raises(KnowledgeHubError, match="zero cross-boundary leaks"):
        external_evidence.validate_external_evidence(payload)

    payload = _memory_evidence()
    payload["pilot"]["cases"]["durable_consolidation"]["canonical_write_performed"] = True
    with pytest.raises(KnowledgeHubError, match="must be false"):
        external_evidence.validate_external_evidence(payload)


def test_adoption_evidence_enforces_real_duration_or_calls_and_feedback():
    payload = _adoption_evidence()
    payload["adoption"]["observation_days"] = 29
    payload["adoption"]["valid_real_calls"] = 49
    with pytest.raises(KnowledgeHubError, match="30 days or 50 valid real calls"):
        external_evidence.validate_external_evidence(payload)

    payload = _adoption_evidence()
    payload["adoption"]["explicit_feedback_count"] = 9
    with pytest.raises(KnowledgeHubError, match="at least 10 explicit feedback"):
        external_evidence.validate_external_evidence(payload)


def test_file_loader_rejects_symlink_and_expected_gap_drift(tmp_path: Path):
    payload_path = tmp_path / "evidence.json"
    payload_path.write_text(json.dumps(_provider_evidence()), encoding="utf-8")
    with pytest.raises(KnowledgeHubError, match="does not match expected gap"):
        external_evidence.load_and_validate_external_evidence(
            payload_path,
            expected_gap="real-adoption-evidence",
        )

    target = tmp_path / "target.json"
    target.write_text(json.dumps(_provider_evidence()), encoding="utf-8")
    symlink = tmp_path / "symlink.json"
    symlink.symlink_to(target)
    with pytest.raises(KnowledgeHubError, match="unavailable"):
        external_evidence.load_and_validate_external_evidence(symlink)


def test_payload_digest_and_receipt_are_stable_for_equivalent_json():
    first = _provider_evidence()
    second = copy.deepcopy(first)
    second["provider"] = dict(reversed(list(second["provider"].items())))
    first_receipt = external_evidence.validate_external_evidence(first)
    second_receipt = external_evidence.validate_external_evidence(second)
    assert first_receipt["evidence_payload_sha256"] == second_receipt["evidence_payload_sha256"]
    assert first_receipt == second_receipt


def test_external_evidence_receipt_replay_is_byte_deterministic():
    payload = _provider_evidence()
    first = external_evidence.validate_external_evidence(payload)
    second = external_evidence.validate_external_evidence(copy.deepcopy(payload))

    assert first == second
    assert (
        json.dumps(first, ensure_ascii=False, sort_keys=True)
        == json.dumps(second, ensure_ascii=False, sort_keys=True)
    )


def test_external_evidence_requires_utc_observed_at():
    payload = _provider_evidence()
    payload["observed_at"] = "2026-09-14T10:00:00+08:00"

    with pytest.raises(KnowledgeHubError, match="must be UTC"):
        external_evidence.validate_external_evidence(payload)


@pytest.mark.parametrize(
    ("factory", "section"),
    [
        (_retrieval_evidence, "evaluation"),
        (_memory_evidence, "pilot"),
        (_adoption_evidence, "adoption"),
    ],
)
def test_external_evidence_rejects_reversed_production_window(factory, section):
    payload = factory()
    payload[section]["window_start"] = "2026-09-15T00:00:00Z"
    payload[section]["window_end"] = "2026-09-14T00:00:00Z"

    with pytest.raises(KnowledgeHubError, match="window_end must not precede"):
        external_evidence.validate_external_evidence(payload)


def test_connector_evidence_binds_adapter_commit_to_source_revision():
    payload = _provider_evidence()
    payload["provider"]["adapter_commit"] = "9" * 40

    with pytest.raises(
        KnowledgeHubError,
        match="connector adapter commit must equal evidence source revision",
    ):
        external_evidence.validate_external_evidence(payload)
