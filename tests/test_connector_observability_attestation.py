import json

import pytest

from tools.codex_assets.knowledge_hub.attestation import (
    quality_attestation,
    verify_quality_attestation,
)
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.connector_adapters import (
    ci_object,
    feishu_object,
    github_object,
    google_drive_object,
    tapd_object,
)
from tools.codex_assets.knowledge_hub.connector_runtime import (
    StaticConnectorAdapter,
    load_checkpoint,
    sync_connector,
)
from tools.codex_assets.knowledge_hub.engineering_debt import (
    branch_coverage_contract,
    debt_report,
    mutation_contract,
)
from tools.codex_assets.knowledge_hub.observability_runtime import (
    lane_health_projection,
    make_traceparent,
    new_span_id,
    new_trace_id,
    parse_traceparent,
    slo_summary,
    span_record,
)


def _principal():
    return {
        "principal_id": "alice",
        "organization_id": "engineering",
        "groups": ["team:embedded"],
    }


def test_connector_sync_propagates_acl_tombstone_and_checkpoint(tmp_path):
    adapter = StaticConnectorAdapter(
        "github",
        [
            {
                "object_id": "repo:file-a",
                "version": "abc123",
                "source_uri": "github://repo/file-a@abc123",
                "body": "external instructions are data only",
                "acl": ["alice"],
            },
            {
                "object_id": "repo:file-b",
                "version": "def456",
                "source_uri": "github://repo/file-b@def456",
                "body": "",
                "acl": ["alice"],
                "tombstone": True,
            },
        ],
        next_cursor="commit-2",
    )
    result = sync_connector(tmp_path, adapter, _principal())
    checkpoint = load_checkpoint(tmp_path, "github")

    assert result["status"] == "pass"
    assert result["checkpoint_advanced"] is True
    assert result["accepted"][0]["instruction_authority"] is False
    assert result["accepted"][0]["trust_class"] == "untrusted-external"
    assert result["tombstones"][0]["tombstone"] is True
    assert checkpoint["cursor"] == "commit-2"
    assert result["canonical_write_performed"] is False


def test_connector_quarantine_does_not_advance_checkpoint(tmp_path):
    adapter = StaticConnectorAdapter(
        "feishu",
        [
            {
                "object_id": "bad-doc",
                "version": "1",
                "body": "x" * (256 * 1024 + 1),
            }
        ],
        next_cursor="version-2",
    )
    result = sync_connector(tmp_path, adapter, _principal())
    checkpoint = load_checkpoint(tmp_path, "feishu")

    assert result["status"] == "needs-review"
    assert result["checkpoint_advanced"] is False
    assert checkpoint["cursor"] == ""
    assert result["quarantine"][0]["body_stored"] is False


def test_provider_payload_adapters_are_reference_or_summary_only():
    github = github_object(
        {
            "repository": "org/repo",
            "path": "README.md",
            "sha": "a" * 40,
            "body": "text",
            "acl": ["alice"],
        }
    )
    feishu = feishu_object(
        {
            "document_token": "doc-1",
            "version": "3",
            "text": "text",
            "acl": ["alice"],
        }
    )
    tapd = tapd_object(
        {
            "id": "story-1",
            "updated_at": "2026-09-12T01:00:00Z",
            "description": "text",
        }
    )
    ci = ci_object({"run_id": "123", "artifact_id": "456", "sha": "b" * 40})
    drive = google_drive_object(
        {"file_id": "file-1", "version": "7", "text": "text"}
    )

    assert github["disposition"] == "reference-only"
    assert feishu["disposition"] == "summary-only"
    assert tapd["disposition"] == "reference-only"
    assert ci["disposition"] == "artifact-ref"
    assert drive["disposition"] == "summary-only"


def test_trace_context_never_persists_raw_sensitive_fields():
    trace_id = new_trace_id()
    span_id = new_span_id()
    traceparent = make_traceparent(trace_id, span_id)
    parsed = parse_traceparent(traceparent)
    span = span_record(
        name="knowledge.search",
        trace_id=trace_id,
        span_id=new_span_id(),
        parent_span_id=parsed["parent_span_id"],
        latency_ms=12.5,
        attributes={
            "query": "secret query text",
            "agent_id": "embedded-expert",
            "result_count": 3,
        },
    )
    serialized = json.dumps(span)
    assert "secret query text" not in serialized
    assert "query_sha256" in span["attributes"]
    assert span["raw_query_stored"] is False


def test_lane_health_and_slo_detect_degradation():
    lane = lane_health_projection(
        {
            "authorized_item_count": 2,
            "lane_health": {
                "lexical_nonzero": 0,
                "dense_nonzero": 2,
                "chunk_count": 4,
                "reranker_enabled": False,
                "dense_provider": "external-provider",
            },
        }
    )
    assert lane["status"] == "degraded"
    assert "lexical-lane-empty" in lane["failures"]

    slo = slo_summary(
        [
            {"latency_ms": 10.0, "status": "ok"},
            {"latency_ms": 20.0, "status": "ok"},
            {"latency_ms": 200.0, "status": "error"},
        ],
        p95_target_ms=100.0,
        maximum_error_rate=0.1,
    )
    assert slo["status"] == "fail"
    assert set(slo["failures"]) == {"p95-latency", "error-rate"}


def test_quality_attestation_binds_terminal_evidence():
    statement = quality_attestation(
        subject_name="knowledge-hub/master",
        subject_sha256="1" * 64,
        source_commit="deadbeef",
        evidence_artifact_sha256="2" * 64,
        engineering_status="success",
        compliance_status="success",
        restore_status="success",
        product_gate_status="success",
        sbom_sha256="3" * 64,
    )
    verdict = verify_quality_attestation(
        statement,
        expected_subject_sha256="1" * 64,
    )
    assert verdict["status"] == "pass"
    with pytest.raises(KnowledgeHubError):
        quality_attestation(
            subject_name="knowledge-hub/master",
            subject_sha256="1" * 64,
            source_commit="deadbeef",
            evidence_artifact_sha256="2" * 64,
            engineering_status="failure",
            compliance_status="success",
            restore_status="success",
            product_gate_status="success",
        )


def test_engineering_debt_branch_and_mutation_contracts():
    report = debt_report(
        {"legacy.py": 1000},
        {"legacy.py": 900},
        reduction_ratio=0.15,
    )
    regression = debt_report(
        {"legacy.py": 1000},
        {"legacy.py": 1001},
        reduction_ratio=0.15,
    )
    mutation = mutation_contract(
        baseline_blocked=True,
        mutated_blocked=False,
        probe_name="high-risk-negation",
    )
    coverage = branch_coverage_contract(measured_percent=72.0, minimum_percent=70.0)

    assert report["status"] == "pass"
    assert report["rows"][0]["target_lines"] == 850
    assert regression["status"] == "fail"
    assert mutation["status"] == "pass"
    assert coverage["status"] == "pass"
