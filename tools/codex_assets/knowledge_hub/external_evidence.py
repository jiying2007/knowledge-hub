"""Fail-closed validation for real external closure evidence.

This module deliberately validates evidence *before* a canonical external gap may be
ratcheted closed.  It never changes the registry and never treats local fixtures,
static adapters, mocks, or synthetic samples as production/provider evidence.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any, Dict, List, Mapping, Sequence

from .common import KnowledgeHubError, utc_timestamp

INPUT_SCHEMA = "knowledge-hub.external-evidence-input.v1"
RECEIPT_SCHEMA = "knowledge-hub.external-evidence-receipt.v1"
MAX_INPUT_BYTES = 4 * 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SUPPORTED_GAPS = {
    "connector-provider-pilot",
    "production-retrieval-eval",
    "memory-lifecycle-pilot",
    "real-adoption-evidence",
}
KNOWN_PROVIDERS = {"github", "feishu", "tapd", "ci", "google-drive"}
PROHIBITED_ORIGIN_FLAGS = (
    "synthetic",
    "mock",
    "fixture",
    "static_adapter",
    "local_only",
)


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _object(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return dict(value)


def _text(value: Any, label: str, *, maximum: int = 4096) -> str:
    result = str(value).strip()
    if not result or len(result) > maximum:
        raise KnowledgeHubError("{} must be non-empty and bounded".format(label))
    return result


def _sha256(value: Any, label: str) -> str:
    result = str(value).strip().lower()
    if not SHA256_RE.fullmatch(result):
        raise KnowledgeHubError("{} must be lowercase SHA256".format(label))
    return result


def _git_sha(value: Any, label: str) -> str:
    result = str(value).strip().lower()
    if not GIT_SHA_RE.fullmatch(result):
        raise KnowledgeHubError("{} must be a lowercase 40-character git SHA".format(label))
    return result


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool):
        raise KnowledgeHubError("{} must be an integer".format(label))
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise KnowledgeHubError("{} must be an integer".format(label)) from exc
    if result < minimum:
        raise KnowledgeHubError("{} is below minimum".format(label))
    return result


def _number(value: Any, label: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool):
        raise KnowledgeHubError("{} must be numeric".format(label))
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise KnowledgeHubError("{} must be numeric".format(label)) from exc
    if result < minimum:
        raise KnowledgeHubError("{} is below minimum".format(label))
    return result


def _true(value: Any, label: str) -> None:
    if value is not True:
        raise KnowledgeHubError("{} must be true".format(label))


def _false(value: Any, label: str) -> None:
    if value is not False:
        raise KnowledgeHubError("{} must be false".format(label))


def _pass(row: Mapping[str, Any], label: str) -> None:
    if str(row.get("status", "")).strip() != "pass":
        raise KnowledgeHubError("{} must pass".format(label))


def _refs(value: Any) -> List[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KnowledgeHubError("evidence_source_refs must be a sequence")
    rows = [_text(item, "evidence source ref", maximum=2048) for item in value]
    if not rows or len(rows) > 32:
        raise KnowledgeHubError("evidence_source_refs must be non-empty and bounded")
    return rows


def _real_origin(payload: Mapping[str, Any], *, expected_classification: str) -> Dict[str, Any]:
    origin = _object(payload.get("origin"), "origin")
    classification = _text(origin.get("classification", ""), "origin classification", maximum=64)
    if classification != expected_classification:
        raise KnowledgeHubError(
            "origin classification must be {}".format(expected_classification)
        )
    for key in PROHIBITED_ORIGIN_FLAGS:
        if origin.get(key) is not False:
            raise KnowledgeHubError("origin {} must be explicitly false".format(key))
    _sha256(origin.get("environment_id_sha256", ""), "environment id")
    return origin


def _case(cases: Mapping[str, Any], name: str, *, origin: str) -> Dict[str, Any]:
    row = _object(cases.get(name), "{} case".format(name))
    _pass(row, "{} case".format(name))
    if _text(row.get("origin", ""), "{} case origin".format(name), maximum=64) != origin:
        raise KnowledgeHubError("{} case must come from {}".format(name, origin))
    return row


def _validate_connector(payload: Mapping[str, Any]) -> Dict[str, Any]:
    _real_origin(payload, expected_classification="real-provider")
    provider = _object(payload.get("provider"), "provider")
    name = _text(provider.get("name", ""), "provider name", maximum=64)
    if name not in KNOWN_PROVIDERS:
        raise KnowledgeHubError("provider is not supported by the current adapter contract")
    version = _text(provider.get("version", ""), "provider version", maximum=256)
    adapter_commit = _git_sha(provider.get("adapter_commit", ""), "adapter commit")
    account_id = _sha256(provider.get("account_id_sha256", ""), "provider account id")
    transport = _text(provider.get("transport", ""), "provider transport", maximum=128)
    if transport in {"static", "mock", "fixture", "local"}:
        raise KnowledgeHubError("provider transport must be a real provider API transport")
    _true(provider.get("network_observed"), "provider network_observed")

    cases = _object(payload.get("cases"), "connector pilot cases")
    incremental = _case(cases, "incremental_checkpoint", origin="real-provider")
    before_cursor = _sha256(incremental.get("before_cursor_sha256", ""), "before cursor")
    after_cursor = _sha256(incremental.get("after_cursor_sha256", ""), "after cursor")
    if before_cursor == after_cursor:
        raise KnowledgeHubError("incremental checkpoint must demonstrate cursor advancement")
    _true(incremental.get("checkpoint_advanced"), "checkpoint advancement")
    _true(incremental.get("idempotent_replay"), "idempotent replay")

    acl = _case(cases, "acl_change", origin="real-provider")
    before_acl = _sha256(acl.get("before_acl_sha256", ""), "before ACL")
    after_acl = _sha256(acl.get("after_acl_sha256", ""), "after ACL")
    if before_acl == after_acl:
        raise KnowledgeHubError("ACL pilot must demonstrate a real ACL change")
    _true(acl.get("propagated"), "ACL propagation")

    tombstone = _case(cases, "tombstone", origin="real-provider")
    _sha256(tombstone.get("object_id_sha256", ""), "tombstone object id")
    _true(tombstone.get("delete_observed"), "tombstone delete observation")

    retry = _case(cases, "retry_backoff", origin="real-provider")
    attempts = _integer(retry.get("attempts"), "retry attempts", minimum=2)
    _true(retry.get("backoff_observed"), "retry backoff observation")
    _true(retry.get("provider_response_observed"), "retry provider response observation")

    freshness = _case(cases, "freshness", origin="real-provider")
    samples = _integer(freshness.get("sample_count"), "freshness sample count", minimum=1)
    slo_seconds = _number(freshness.get("slo_seconds"), "freshness SLO", minimum=0.001)
    p95_seconds = _number(freshness.get("p95_seconds"), "freshness p95", minimum=0.0)
    if p95_seconds > slo_seconds:
        raise KnowledgeHubError("freshness p95 exceeds declared SLO")

    quarantine = _case(cases, "quarantine", origin="real-provider")
    _sha256(quarantine.get("case_id_sha256", ""), "quarantine case id")
    _false(quarantine.get("checkpoint_advanced"), "quarantine checkpoint advancement")
    _true(quarantine.get("dead_letter_or_quarantine_observed"), "quarantine observation")

    stays = _case(cases, "stays_at_source", origin="real-provider")
    _false(stays.get("canonical_write_performed"), "connector canonical write")
    _false(stays.get("auto_promotion"), "connector auto promotion")

    return {
        "provider": name,
        "provider_version": version,
        "adapter_commit": adapter_commit,
        "account_id_sha256": account_id,
        "transport": transport,
        "retry_attempts": attempts,
        "freshness_sample_count": samples,
        "freshness_slo_seconds": slo_seconds,
        "freshness_p95_seconds": p95_seconds,
        "case_count": 7,
    }


def _validate_retrieval(payload: Mapping[str, Any]) -> Dict[str, Any]:
    _real_origin(payload, expected_classification="real-production")
    evaluation = _object(payload.get("evaluation"), "retrieval evaluation")
    case_count = _integer(evaluation.get("case_count"), "retrieval case count", minimum=200)
    production_count = _integer(
        evaluation.get("production_derived_case_count"),
        "production-derived case count",
        minimum=200,
    )
    synthetic_count = _integer(evaluation.get("synthetic_case_count"), "synthetic case count")
    if production_count != case_count or synthetic_count != 0:
        raise KnowledgeHubError("retrieval evaluation must be entirely production-derived")
    dataset_sha = _sha256(evaluation.get("dataset_sha256", ""), "retrieval dataset")
    evaluator_version = _text(
        evaluation.get("evaluator_version", ""), "evaluator version", maximum=256
    )
    baseline = _text(evaluation.get("approved_baseline", ""), "approved baseline", maximum=256)
    _text(evaluation.get("window_start", ""), "retrieval window_start", maximum=128)
    _text(evaluation.get("window_end", ""), "retrieval window_end", maximum=128)

    metrics = _object(evaluation.get("metrics"), "retrieval metrics")
    for key in ("recall", "mrr", "ndcg", "authority_recall"):
        value = _number(metrics.get(key), key)
        if value > 1.0:
            raise KnowledgeHubError("{} must be in [0,1]".format(key))
    forbidden = _number(metrics.get("forbidden_hit_rate"), "forbidden hit rate")
    if forbidden != 0.0:
        raise KnowledgeHubError("production retrieval evidence must have zero forbidden-hit rate")
    p50_ms = _number(metrics.get("p50_ms"), "retrieval p50", minimum=0.0)
    p95_ms = _number(metrics.get("p95_ms"), "retrieval p95", minimum=0.0)
    if p95_ms < p50_ms:
        raise KnowledgeHubError("retrieval p95 must not be below p50")

    comparison = _object(evaluation.get("comparison"), "retrieval comparison")
    _pass(comparison, "retrieval comparison")
    new_critical = _integer(
        comparison.get("new_critical_failures"), "new critical retrieval failures"
    )
    if new_critical != 0:
        raise KnowledgeHubError("retrieval evaluation has new critical failures")
    _sha256(comparison.get("result_sha256", ""), "retrieval result")
    return {
        "case_count": case_count,
        "production_derived_case_count": production_count,
        "dataset_sha256": dataset_sha,
        "evaluator_version": evaluator_version,
        "approved_baseline": baseline,
        "forbidden_hit_rate": forbidden,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "new_critical_failures": new_critical,
    }


def _validate_memory(payload: Mapping[str, Any]) -> Dict[str, Any]:
    _real_origin(payload, expected_classification="real-production")
    pilot = _object(payload.get("pilot"), "memory pilot")
    _text(pilot.get("runtime_version", ""), "memory runtime version", maximum=256)
    _text(pilot.get("window_start", ""), "memory window_start", maximum=128)
    _text(pilot.get("window_end", ""), "memory window_end", maximum=128)
    cases = _object(pilot.get("cases"), "memory pilot cases")

    ttl = _case(cases, "ttl", origin="real-production")
    _true(ttl.get("expiry_verified"), "TTL expiry verification")
    forget = _case(cases, "forget", origin="real-production")
    _true(forget.get("deletion_verified"), "forget deletion verification")
    supersede = _case(cases, "supersede", origin="real-production")
    _true(supersede.get("old_state_hidden"), "supersede old-state hiding")

    for name in ("principal_isolation", "agent_isolation", "scope_isolation"):
        row = _case(cases, name, origin="real-production")
        if _integer(row.get("cross_boundary_leak_count"), "{} leak count".format(name)) != 0:
            raise KnowledgeHubError("{} must have zero cross-boundary leaks".format(name))

    scope_delete = _case(cases, "scope_delete", origin="real-production")
    _true(scope_delete.get("deletion_verified"), "scope deletion verification")
    durable = _case(cases, "durable_consolidation", origin="real-production")
    _true(durable.get("candidate_only"), "durable consolidation candidate-only")
    _true(durable.get("provenance_bound"), "durable consolidation provenance")
    _true(durable.get("owner_gate_observed"), "durable consolidation owner gate")
    _false(durable.get("canonical_write_performed"), "durable consolidation canonical write")

    result_sha = _sha256(pilot.get("result_sha256", ""), "memory pilot result")
    return {
        "runtime_version": str(pilot.get("runtime_version")),
        "case_count": 8,
        "result_sha256": result_sha,
        "canonical_write_performed": False,
    }


def _validate_adoption(payload: Mapping[str, Any]) -> Dict[str, Any]:
    _real_origin(payload, expected_classification="real-production")
    adoption = _object(payload.get("adoption"), "adoption evidence")
    runtime_version = _text(
        adoption.get("runtime_version", ""), "adoption runtime version", maximum=256
    )
    _text(adoption.get("window_start", ""), "adoption window_start", maximum=128)
    _text(adoption.get("window_end", ""), "adoption window_end", maximum=128)
    observation_days = _integer(adoption.get("observation_days"), "observation days")
    valid_calls = _integer(adoption.get("valid_real_calls"), "valid real calls")
    synthetic_calls = _integer(adoption.get("synthetic_calls"), "synthetic calls")
    feedback_count = _integer(adoption.get("explicit_feedback_count"), "explicit feedback count")
    if observation_days < 30 and valid_calls < 50:
        raise KnowledgeHubError("adoption evidence requires 30 days or 50 valid real calls")
    if synthetic_calls != 0:
        raise KnowledgeHubError("synthetic calls cannot qualify adoption evidence")
    if feedback_count < 10:
        raise KnowledgeHubError("adoption evidence requires at least 10 explicit feedback items")
    call_ledger = _sha256(adoption.get("call_ledger_sha256", ""), "adoption call ledger")
    feedback_digest = _sha256(adoption.get("feedback_sha256", ""), "adoption feedback")

    slo = _object(adoption.get("slo"), "adoption SLO")
    _pass(slo, "adoption SLO")
    p50_ms = _number(slo.get("p50_ms"), "adoption p50", minimum=0.0)
    p95_ms = _number(slo.get("p95_ms"), "adoption p95", minimum=0.0)
    if p95_ms < p50_ms:
        raise KnowledgeHubError("adoption p95 must not be below p50")
    error_rate = _number(slo.get("error_rate"), "adoption error rate", minimum=0.0)
    if error_rate > 1.0:
        raise KnowledgeHubError("adoption error rate must be in [0,1]")
    if str(slo.get("retrieval_lane_health", "")) != "pass":
        raise KnowledgeHubError("retrieval lane health must pass")

    traces = _object(adoption.get("traceability"), "adoption traceability")
    _pass(traces, "adoption traceability")
    _true(traces.get("work_item_run_handoff_receipt_linked"), "cross-work trace linkage")

    privacy = _object(adoption.get("privacy"), "adoption privacy")
    for key in ("raw_query_stored", "raw_task_stored", "raw_prompt_stored", "raw_content_stored"):
        _false(privacy.get(key), "adoption privacy {}".format(key))
    export_mode = _text(privacy.get("network_export_mode", ""), "network export mode", maximum=64)
    if export_mode not in {"disabled", "explicitly-configured"}:
        raise KnowledgeHubError("network telemetry export must be disabled or explicitly configured")

    return {
        "runtime_version": runtime_version,
        "observation_days": observation_days,
        "valid_real_calls": valid_calls,
        "explicit_feedback_count": feedback_count,
        "call_ledger_sha256": call_ledger,
        "feedback_sha256": feedback_digest,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "error_rate": error_rate,
        "network_export_mode": export_mode,
    }


_VALIDATORS = {
    "connector-provider-pilot": _validate_connector,
    "production-retrieval-eval": _validate_retrieval,
    "memory-lifecycle-pilot": _validate_memory,
    "real-adoption-evidence": _validate_adoption,
}


def validate_external_evidence(
    payload: Mapping[str, Any],
    *,
    expected_gap: str = "",
) -> Dict[str, Any]:
    value = _object(payload, "external evidence")
    if value.get("schema_version") != INPUT_SCHEMA:
        raise KnowledgeHubError("external evidence schema_version is unsupported")
    gap_id = _text(value.get("gap_id", ""), "gap id", maximum=128)
    if gap_id not in SUPPORTED_GAPS:
        raise KnowledgeHubError("external evidence gap is unsupported")
    if expected_gap and gap_id != expected_gap:
        raise KnowledgeHubError("external evidence gap does not match expected gap")
    source_revision = _git_sha(value.get("source_revision", ""), "source revision")
    observed_at = _text(value.get("observed_at", ""), "observed_at", maximum=128)
    refs = _refs(value.get("evidence_source_refs"))
    summary = _VALIDATORS[gap_id](value)
    payload_sha = _sha256_bytes(_canonical_bytes(value))
    return {
        "schema_version": RECEIPT_SCHEMA,
        "status": "pass",
        "closure_ready": True,
        "gap_id": gap_id,
        "source_revision": source_revision,
        "observed_at": observed_at,
        "evidence_payload_sha256": payload_sha,
        "evidence_source_refs": refs,
        "summary": summary,
        "synthetic_evidence_accepted": False,
        "mock_evidence_accepted": False,
        "local_only_evidence_accepted": False,
        "canonical_write_performed": False,
        "generated_at": utc_timestamp(),
    }


def load_and_validate_external_evidence(
    path: pathlib.Path,
    *,
    expected_gap: str = "",
) -> Dict[str, Any]:
    path = pathlib.Path(path)
    if not path.is_file() or path.is_symlink():
        raise KnowledgeHubError("external evidence input is unavailable")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise KnowledgeHubError("external evidence input exceeds byte budget")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("external evidence input is invalid JSON") from exc
    if not isinstance(payload, Mapping):
        raise KnowledgeHubError("external evidence input must be an object")
    return validate_external_evidence(payload, expected_gap=expected_gap)
