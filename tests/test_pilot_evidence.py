import hashlib
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub.external_evidence import validate_external_evidence
from tools.codex_assets.knowledge_hub.schemas import validate_instance
from tools.codex_assets.knowledge_hub.pilot_evidence import (
    ADOPTION_SCHEMA,
    CONNECTOR_SCHEMA,
    MEMORY_SCHEMA,
    RETRIEVAL_SCHEMA,
    build_connector_provider_evidence,
    build_memory_lifecycle_evidence,
    build_pilot_evidence,
    build_production_retrieval_evidence,
    build_real_adoption_evidence,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
GIT_SHA = "e" * 40


def _origin(classification):
    return {
        "classification": classification,
        "environment_id_sha256": SHA_A,
        "synthetic": False,
        "mock": False,
        "fixture": False,
        "static_adapter": False,
        "local_only": False,
    }


def _base(schema, gap, classification):
    return {
        "schema_version": schema,
        "gap_id": gap,
        "source_revision": GIT_SHA,
        "observed_at": "2026-09-15T00:00:00Z",
        "evidence_source_refs": [
            "provider-run://real/42",
            "receipt://real/42",
        ],
        "origin": _origin(classification),
    }


def _provider_case(**values):
    row = {
        "status": "pass",
        "provider_request_sha256": SHA_B,
        "provider_response_sha256": SHA_C,
        "observed_at": "2026-09-15T00:00:00Z",
    }
    row.update(values)
    return row


def _connector():
    payload = _base(CONNECTOR_SCHEMA, "connector-provider-pilot", "real-provider")
    payload.update(
        {
            "observation_ledger_sha256": SHA_D,
            "provider": {
                "name": "google-drive",
                "version": "drive-v3",
                "adapter_commit": GIT_SHA,
                "account_id_sha256": SHA_B,
                "transport": "google-drive-v3-api",
                "network_observed": True,
            },
            "cases": {
                "incremental_checkpoint": _provider_case(
                    before_cursor_sha256=SHA_A,
                    after_cursor_sha256=SHA_B,
                    checkpoint_advanced=True,
                    idempotent_replay=True,
                ),
                "acl_change": _provider_case(
                    before_acl_sha256=SHA_A,
                    after_acl_sha256=SHA_C,
                    propagated=True,
                ),
                "tombstone": _provider_case(
                    object_id_sha256=SHA_D,
                    delete_acknowledged=True,
                    post_delete_status_code=404,
                ),
                "retry_backoff": _provider_case(
                    attempts=2,
                    first_status_code=429,
                    recovery_status_code=200,
                    backoff_seconds=2.0,
                    backoff_observed=True,
                    provider_response_observed=True,
                ),
                "freshness": _provider_case(
                    sample_count=4,
                    slo_seconds=60.0,
                    p95_seconds=9.5,
                ),
                "quarantine": _provider_case(
                    before_checkpoint_sha256=SHA_A,
                    after_checkpoint_sha256=SHA_A,
                    case_id_sha256=SHA_C,
                    runtime_receipt_sha256=SHA_D,
                    dead_letter_or_quarantine_observed=True,
                ),
                "stays_at_source": _provider_case(
                    registry_before_sha256=SHA_B,
                    registry_after_sha256=SHA_B,
                    canonical_write_performed=False,
                    auto_promotion=False,
                ),
            },
        }
    )
    return payload


def _retrieval():
    payload = _base(RETRIEVAL_SCHEMA, "production-retrieval-eval", "real-production")
    payload["evaluation"] = {
        "raw_query_stored_in_evidence": False,
        "case_count": 240,
        "production_derived_case_count": 240,
        "synthetic_case_count": 0,
        "dataset_sha256": SHA_B,
        "dataset_receipt_sha256": SHA_C,
        "evaluation_run_receipt_sha256": SHA_D,
        "evaluator_version": "eval-v2.4",
        "approved_baseline": "prod-2026-08",
        "window_start": "2026-08-15T00:00:00Z",
        "window_end": "2026-09-15T00:00:00Z",
        "metrics": {
            "recall": 0.94,
            "mrr": 0.90,
            "ndcg": 0.92,
            "authority_recall": 0.99,
            "forbidden_hit_rate": 0.0,
            "p50_ms": 25.0,
            "p95_ms": 90.0,
        },
        "comparison": {
            "status": "pass",
            "new_critical_failures": 0,
            "result_sha256": SHA_A,
        },
    }
    return payload


def _memory_case(**values):
    row = {
        "status": "pass",
        "receipt_sha256": SHA_B,
        "event_count": 2,
    }
    row.update(values)
    return row


def _memory():
    payload = _base(MEMORY_SCHEMA, "memory-lifecycle-pilot", "real-production")
    payload["pilot"] = {
        "runtime_version": "memory-runtime-v3",
        "window_start": "2026-09-01T00:00:00Z",
        "window_end": "2026-09-15T00:00:00Z",
        "result_sha256": SHA_D,
        "cases": {
            "ttl": _memory_case(expiry_verified=True),
            "forget": _memory_case(deletion_verified=True),
            "supersede": _memory_case(old_state_hidden=True),
            "principal_isolation": _memory_case(cross_boundary_leak_count=0),
            "agent_isolation": _memory_case(cross_boundary_leak_count=0),
            "scope_isolation": _memory_case(cross_boundary_leak_count=0),
            "scope_delete": _memory_case(deletion_verified=True),
            "durable_consolidation": _memory_case(
                candidate_only=True,
                provenance_bound=True,
                owner_gate_observed=True,
                canonical_write_performed=False,
            ),
        },
    }
    return payload



def _adoption():
    payload = _base(
        ADOPTION_SCHEMA,
        "real-adoption-evidence",
        "real-production",
    )
    payload["adoption"] = {
        "runtime_version": "knowledge-runtime-v4",
        "window_start": "2026-08-15T00:00:00Z",
        "window_end": "2026-09-15T00:00:00Z",
        "observation_days": 31,
        "valid_real_calls": 72,
        "synthetic_calls": 0,
        "explicit_feedback_count": 14,
        "call_ledger_sha256": SHA_B,
        "call_ledger_receipt_sha256": SHA_C,
        "feedback_sha256": SHA_D,
        "feedback_receipt_sha256": SHA_A,
        "slo": {
            "status": "pass",
            "receipt_sha256": SHA_B,
            "p50_ms": 35.0,
            "p95_ms": 120.0,
            "error_rate": 0.01,
            "retrieval_lane_health": "pass",
        },
        "traceability": {
            "status": "pass",
            "receipt_sha256": SHA_C,
            "work_item_run_handoff_receipt_linked": True,
        },
        "privacy": {
            "receipt_sha256": SHA_D,
            "raw_query_stored": False,
            "raw_task_stored": False,
            "raw_prompt_stored": False,
            "raw_content_stored": False,
            "network_export_mode": "disabled",
        },
    }
    return payload


def test_connector_observation_projects_to_strict_external_evidence():
    payload = build_connector_provider_evidence(_connector())
    assert payload["gap_id"] == "connector-provider-pilot"
    assert payload["provider"]["name"] == "google-drive"
    assert payload["cases"]["tombstone"]["delete_observed"] is True
    assert payload["cases"]["quarantine"]["checkpoint_advanced"] is False
    receipt = validate_external_evidence(payload, expected_gap="connector-provider-pilot")
    assert receipt["closure_ready"] is True
    assert receipt["canonical_write_performed"] is False


def test_connector_rejects_fake_acl_retry_delete_and_quarantine():
    observation = _connector()
    observation["cases"]["acl_change"]["after_acl_sha256"] = SHA_A
    with pytest.raises(KnowledgeHubError, match="real permission change"):
        build_connector_provider_evidence(observation)

    observation = _connector()
    observation["cases"]["retry_backoff"]["recovery_status_code"] = 429
    with pytest.raises(KnowledgeHubError, match="successful recovery"):
        build_connector_provider_evidence(observation)

    observation = _connector()
    observation["cases"]["tombstone"]["post_delete_status_code"] = 200
    with pytest.raises(KnowledgeHubError, match="404/410"):
        build_connector_provider_evidence(observation)

    observation = _connector()
    observation["cases"]["quarantine"]["after_checkpoint_sha256"] = SHA_C
    with pytest.raises(KnowledgeHubError, match="must not advance checkpoint"):
        build_connector_provider_evidence(observation)


def test_connector_rejects_canonical_write_and_prohibited_origin():
    observation = _connector()
    observation["cases"]["stays_at_source"]["registry_after_sha256"] = SHA_C
    with pytest.raises(KnowledgeHubError, match="registry stayed unchanged"):
        build_connector_provider_evidence(observation)

    observation = _connector()
    observation["origin"]["local_only"] = True
    with pytest.raises(KnowledgeHubError, match="local_only must be explicitly false"):
        build_connector_provider_evidence(observation)


def test_retrieval_observation_projects_without_raw_queries():
    payload = build_production_retrieval_evidence(_retrieval())
    assert payload["gap_id"] == "production-retrieval-eval"
    assert payload["evaluation"]["case_count"] == 240
    assert "query" not in payload["evaluation"]
    receipt = validate_external_evidence(payload, expected_gap="production-retrieval-eval")
    assert receipt["closure_ready"] is True


def test_retrieval_rejects_synthetic_padding_underfilled_or_unbounded_manifest():
    observation = _retrieval()
    observation["evaluation"]["synthetic_case_count"] = 1
    with pytest.raises(KnowledgeHubError, match="entirely production-derived"):
        build_production_retrieval_evidence(observation)

    observation = _retrieval()
    observation["evaluation"]["case_count"] = 199
    observation["evaluation"]["production_derived_case_count"] = 199
    with pytest.raises(KnowledgeHubError, match="below minimum"):
        build_production_retrieval_evidence(observation)

    observation = _retrieval()
    observation["evaluation"]["raw_query_stored_in_evidence"] = True
    with pytest.raises(KnowledgeHubError, match="must not store raw production queries"):
        build_production_retrieval_evidence(observation)


def test_retrieval_rejects_forbidden_hits_and_critical_regression():
    observation = _retrieval()
    observation["evaluation"]["metrics"]["forbidden_hit_rate"] = 0.01
    with pytest.raises(KnowledgeHubError, match="zero forbidden-hit rate"):
        build_production_retrieval_evidence(observation)

    observation = _retrieval()
    observation["evaluation"]["comparison"]["new_critical_failures"] = 1
    with pytest.raises(KnowledgeHubError, match="new critical failures"):
        build_production_retrieval_evidence(observation)


def test_memory_observation_projects_to_strict_external_evidence():
    payload = build_memory_lifecycle_evidence(_memory())
    assert payload["gap_id"] == "memory-lifecycle-pilot"
    assert payload["pilot"]["cases"]["principal_isolation"]["cross_boundary_leak_count"] == 0
    assert payload["pilot"]["cases"]["durable_consolidation"]["canonical_write_performed"] is False
    receipt = validate_external_evidence(payload, expected_gap="memory-lifecycle-pilot")
    assert receipt["closure_ready"] is True


def test_memory_rejects_cross_boundary_leak_and_automatic_canonical_write():
    observation = _memory()
    observation["pilot"]["cases"]["agent_isolation"]["cross_boundary_leak_count"] = 1
    with pytest.raises(KnowledgeHubError, match="zero cross-boundary leaks"):
        build_memory_lifecycle_evidence(observation)

    observation = _memory()
    observation["pilot"]["cases"]["durable_consolidation"]["canonical_write_performed"] = True
    with pytest.raises(KnowledgeHubError, match="must be false"):
        build_memory_lifecycle_evidence(observation)


def test_dispatch_builder_requires_exact_gap():
    with pytest.raises(KnowledgeHubError, match="does not match expected gap"):
        build_pilot_evidence(_connector(), expected_gap="memory-lifecycle-pilot")


def test_pilot_cli_is_repository_bounded_and_never_writes_canonical():
    root = Path(__file__).resolve().parents[1]
    cli = (root / "tools/codex_assets/knowledge_hub/pilot_evidence_cli.py").read_text(
        encoding="utf-8"
    )
    producer = (root / "tools/codex_assets/knowledge_hub/pilot_evidence.py").read_text(
        encoding="utf-8"
    )
    registry_path = root / "registry/knowledge-platform-p5-p10.json"
    before = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    assert "resolve_inside" in cli
    assert "pilot evidence CLI must never write the canonical registry" in cli
    assert "validate_external_evidence" in producer
    assert "raw_query_stored_in_evidence" in producer
    assert "runtime_receipt_sha256" in producer
    after = hashlib.sha256(registry_path.read_bytes()).hexdigest()
    assert after == before


def test_adoption_observation_projects_to_strict_external_evidence():
    payload = build_real_adoption_evidence(_adoption())
    assert payload["gap_id"] == "real-adoption-evidence"
    assert payload["adoption"]["valid_real_calls"] == 72
    assert payload["adoption"]["explicit_feedback_count"] == 14
    assert payload["adoption"]["synthetic_calls"] == 0
    receipt = validate_external_evidence(
        payload,
        expected_gap="real-adoption-evidence",
    )
    assert receipt["closure_ready"] is True


def test_adoption_rejects_underqualified_synthetic_or_privacy_unsafe_observation():
    observation = _adoption()
    observation["adoption"]["observation_days"] = 10
    observation["adoption"]["valid_real_calls"] = 20
    with pytest.raises(KnowledgeHubError, match="30 days or 50 valid real calls"):
        build_real_adoption_evidence(observation)

    observation = _adoption()
    observation["adoption"]["synthetic_calls"] = 1
    with pytest.raises(KnowledgeHubError, match="must not include synthetic calls"):
        build_real_adoption_evidence(observation)

    observation = _adoption()
    observation["adoption"]["privacy"]["raw_prompt_stored"] = True
    with pytest.raises(KnowledgeHubError, match="must be false"):
        build_real_adoption_evidence(observation)


def test_adoption_dispatch_builder_requires_exact_gap():
    with pytest.raises(KnowledgeHubError, match="does not match expected gap"):
        build_pilot_evidence(
            _adoption(),
            expected_gap="memory-lifecycle-pilot",
        )


def test_real_observation_fixtures_match_catalog_contracts():
    root = repository_root()
    cases = (
        ("connector-provider-observation-v1", _connector()),
        ("production-retrieval-observation-v1", _retrieval()),
        ("production-memory-observation-v1", _memory()),
        ("production-adoption-observation-v1", _adoption()),
    )
    for contract_id, payload in cases:
        result = validate_instance(root, contract_id, payload)
        assert result["status"] == "pass", (contract_id, result["errors"])


def test_real_observation_schema_rejects_prohibited_origin_before_projection():
    root = repository_root()
    payload = _adoption()
    payload["origin"]["synthetic"] = True

    result = validate_instance(
        root,
        "production-adoption-observation-v1",
        payload,
    )

    assert result["status"] == "fail"
    assert result["error_count"] > 0


def test_pilot_cli_uses_catalog_schema_before_business_projection():
    root = Path(__file__).resolve().parents[1]
    text = (
        root / "tools/codex_assets/knowledge_hub/pilot_evidence_cli.py"
    ).read_text(encoding="utf-8")
    assert "OBSERVATION_CONTRACTS" in text
    assert "validate_instance(root, contract_id, observation)" in text
    assert "pilot observation schema validation failed" in text


def test_pilot_cli_observation_contract_mapping_matches_machine_policy():
    import json

    from tools.codex_assets.knowledge_hub.pilot_evidence_cli import (
        OBSERVATION_CONTRACTS,
    )

    policy = json.loads(
        (
            repository_root()
            / "registry/ai-operations-policy.json"
        ).read_text(encoding="utf-8")
    )
    external = policy["external_evidence"]
    assert OBSERVATION_CONTRACTS == external["observation_contracts"]
    assert (
        external["validator_receipt_timestamp_source"]
        == "observation-observed-at"
    )


def test_real_observation_schema_rejects_invalid_datetime():
    payload = _retrieval()
    payload["observed_at"] = "not-a-date-time"

    result = validate_instance(
        repository_root(),
        "production-retrieval-observation-v1",
        payload,
    )

    assert result["status"] == "fail"
    assert result["error_count"] > 0
