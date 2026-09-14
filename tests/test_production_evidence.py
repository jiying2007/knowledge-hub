import hashlib
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.external_evidence import validate_external_evidence
from tools.codex_assets.knowledge_hub.production_evidence import (
    HEALTH_SCHEMA,
    PROVENANCE_SCHEMA,
    TRACE_SCHEMA,
    build_real_adoption_evidence,
)


SOURCE_SHA = "a" * 40
DIGEST = "b" * 64


def _metrics(ready=True):
    return {
        "usage": {"observation_days": 14, "invocation_count": 64},
        "retrieval": {"feedback_count": 12, "found_rate": 0.9167},
        "performance": {
            "warm_interactive": {
                "search_p95_ms": 120.0,
                "context_p95_ms": 180.0,
            }
        },
        "adoption": {"evaluable": True, "ready": ready},
    }


def _provenance():
    return {
        "schema_version": PROVENANCE_SCHEMA,
        "classification": "real-production",
        "environment_id_sha256": "c" * 64,
        "runtime_version": "knowledge-hub-runtime/5",
        "window_start": "2026-09-01T00:00:00Z",
        "window_end": "2026-09-14T15:00:00Z",
        "evidence_source_refs": [
            "production-run://runtime/42",
            "handoff-receipt://runtime/42/adoption",
        ],
        "network_export_mode": "explicitly-configured",
        "synthetic": False,
        "mock": False,
        "fixture": False,
        "static_adapter": False,
        "local_only": False,
    }


def _health():
    return {
        "schema_version": HEALTH_SCHEMA,
        "status": "pass",
        "p50_ms": 75.0,
        "error_rate": 0.01,
        "retrieval_lane_health": "pass",
    }


def _trace():
    return {
        "schema_version": TRACE_SCHEMA,
        "status": "pass",
        "work_item_run_handoff_receipt_linked": True,
        "work_item_id_sha256": "d" * 64,
        "run_id_sha256": "e" * 64,
        "handoff_id_sha256": "f" * 64,
        "receipt_id_sha256": "1" * 64,
    }


def _build(**overrides):
    values = {
        "metrics": _metrics(),
        "provenance": _provenance(),
        "health": _health(),
        "traceability": _trace(),
        "source_revision": SOURCE_SHA,
        "call_ledger_sha256": DIGEST,
        "feedback_sha256": "2" * 64,
    }
    values.update(overrides)
    return build_real_adoption_evidence(**values)


def test_real_adoption_builder_projects_existing_metrics_into_external_contract():
    payload = _build()
    assert payload["gap_id"] == "real-adoption-evidence"
    assert payload["origin"]["classification"] == "real-production"
    assert payload["adoption"]["valid_real_calls"] == 64
    assert payload["adoption"]["explicit_feedback_count"] == 12
    assert payload["adoption"]["slo"]["p95_ms"] == 180.0
    assert payload["adoption"]["synthetic_calls"] == 0
    assert payload["adoption"]["privacy"]["raw_query_stored"] is False
    receipt = validate_external_evidence(payload, expected_gap="real-adoption-evidence")
    assert receipt["status"] == "pass"
    assert receipt["closure_ready"] is True
    assert receipt["canonical_write_performed"] is False


def test_real_adoption_builder_rejects_local_or_synthetic_provenance():
    provenance = _provenance()
    provenance["local_only"] = True
    with pytest.raises(KnowledgeHubError, match="local_only must be explicitly false"):
        _build(provenance=provenance)
    provenance = _provenance()
    provenance["synthetic"] = True
    with pytest.raises(KnowledgeHubError, match="synthetic must be explicitly false"):
        _build(provenance=provenance)


def test_real_adoption_builder_rejects_not_ready_existing_metrics():
    with pytest.raises(KnowledgeHubError, match="local metrics adoption is not ready"):
        _build(metrics=_metrics(ready=False))


def test_real_adoption_builder_rejects_broken_cross_work_trace():
    trace = _trace()
    trace["work_item_run_handoff_receipt_linked"] = False
    with pytest.raises(KnowledgeHubError, match="must link work-item, run, handoff and receipt"):
        _build(traceability=trace)


def test_real_adoption_builder_rejects_health_that_understates_latency():
    health = _health()
    health["p50_ms"] = 200.0
    with pytest.raises(KnowledgeHubError, match="p50 cannot exceed telemetry-derived p95"):
        _build(health=health)


def test_production_evidence_cli_is_repository_bounded_and_cannot_write_registry():
    root = Path(__file__).resolve().parents[1]
    cli = (
        root / "tools/codex_assets/knowledge_hub/production_evidence_cli.py"
    ).read_text(encoding="utf-8")
    producer = (
        root / "tools/codex_assets/knowledge_hub/production_evidence.py"
    ).read_text(encoding="utf-8")
    registry = (root / "registry/knowledge-platform-p5-p10.json").read_bytes()
    before = hashlib.sha256(registry).hexdigest()
    assert "resolve_inside" in cli
    assert "production evidence CLI must never write the canonical registry" in cli
    assert "local_metrics(root)" in producer
    assert "validate_external_evidence(payload, expected_gap=\"real-adoption-evidence\")" in producer
    assert "raw_query_stored\": False" in producer
    after = hashlib.sha256(
        (root / "registry/knowledge-platform-p5-p10.json").read_bytes()
    ).hexdigest()
    assert after == before
