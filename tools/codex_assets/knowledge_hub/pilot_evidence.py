"""Build strict external evidence from real provider or production observations.

These builders are projection-only. They never collect provider data, relabel local
fixtures as production, or write canonical state. They require independently captured,
hash-bound receipts and emit only payloads accepted by ``external_evidence``.
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any, Dict, Mapping, Sequence

from .common import KnowledgeHubError
from .external_evidence import INPUT_SCHEMA, validate_external_evidence

CONNECTOR_SCHEMA = "knowledge-hub.connector-provider-observation.v1"
RETRIEVAL_SCHEMA = "knowledge-hub.production-retrieval-observation.v1"
MEMORY_SCHEMA = "knowledge-hub.production-memory-observation.v1"
ADOPTION_SCHEMA = "knowledge-hub.production-adoption-observation.v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PROHIBITED_ORIGIN_FLAGS = (
    "synthetic",
    "mock",
    "fixture",
    "static_adapter",
    "local_only",
)
KNOWN_PROVIDERS = {"github", "feishu", "tapd", "ci", "google-drive"}
SUPPORTED_GAPS = {
    "connector-provider-pilot",
    "production-retrieval-eval",
    "memory-lifecycle-pilot",
    "real-adoption-evidence",
}


def _object(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return dict(value)


def _text(value: Any, label: str, *, maximum: int = 4096) -> str:
    result = str(value or "").strip()
    if not result or len(result) > maximum:
        raise KnowledgeHubError("{} must be non-empty and bounded".format(label))
    return result


def _sha256(value: Any, label: str) -> str:
    result = str(value or "").strip().lower()
    if not SHA256_RE.fullmatch(result):
        raise KnowledgeHubError("{} must be lowercase SHA256".format(label))
    return result


def _git_sha(value: Any, label: str) -> str:
    result = str(value or "").strip().lower()
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


def _refs(value: Any) -> Sequence[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KnowledgeHubError("evidence_source_refs must be a sequence")
    rows = [_text(item, "evidence source ref", maximum=2048) for item in value]
    if not rows or len(rows) > 32:
        raise KnowledgeHubError("evidence_source_refs must be non-empty and bounded")
    return rows


def _origin(value: Any, classification: str) -> Dict[str, Any]:
    row = _object(value, "observation origin")
    if _text(row.get("classification"), "origin classification", maximum=64) != classification:
        raise KnowledgeHubError("observation origin classification must be {}".format(classification))
    for key in PROHIBITED_ORIGIN_FLAGS:
        if row.get(key) is not False:
            raise KnowledgeHubError("observation origin {} must be explicitly false".format(key))
    row["environment_id_sha256"] = _sha256(
        row.get("environment_id_sha256"), "observation environment id"
    )
    return row


def _base(observation: Mapping[str, Any], gap_id: str, classification: str) -> Dict[str, Any]:
    origin = _origin(observation.get("origin"), classification)
    return {
        "schema_version": INPUT_SCHEMA,
        "gap_id": gap_id,
        "source_revision": _git_sha(observation.get("source_revision"), "source revision"),
        "observed_at": _text(observation.get("observed_at"), "observed_at", maximum=128),
        "evidence_source_refs": list(_refs(observation.get("evidence_source_refs"))),
        "origin": {
            "classification": classification,
            "environment_id_sha256": origin["environment_id_sha256"],
            "synthetic": False,
            "mock": False,
            "fixture": False,
            "static_adapter": False,
            "local_only": False,
        },
    }


def _provider_case(cases: Mapping[str, Any], name: str) -> Dict[str, Any]:
    row = _object(cases.get(name), "{} observation".format(name))
    if row.get("status") != "pass":
        raise KnowledgeHubError("{} observation must pass".format(name))
    _sha256(row.get("provider_request_sha256"), "{} provider request".format(name))
    _sha256(row.get("provider_response_sha256"), "{} provider response".format(name))
    _text(row.get("observed_at"), "{} observed_at".format(name), maximum=128)
    return row


def _connector_incremental(cases: Mapping[str, Any]) -> Dict[str, Any]:
    row = _provider_case(cases, "incremental_checkpoint")
    before_cursor = _sha256(row.get("before_cursor_sha256"), "before cursor")
    after_cursor = _sha256(row.get("after_cursor_sha256"), "after cursor")
    if before_cursor == after_cursor:
        raise KnowledgeHubError("incremental observation must demonstrate cursor advancement")
    _true(row.get("checkpoint_advanced"), "checkpoint advancement")
    _true(row.get("idempotent_replay"), "idempotent replay")
    return {
        "status": "pass",
        "origin": "real-provider",
        "before_cursor_sha256": before_cursor,
        "after_cursor_sha256": after_cursor,
        "checkpoint_advanced": True,
        "idempotent_replay": True,
    }


def _connector_acl(cases: Mapping[str, Any]) -> Dict[str, Any]:
    row = _provider_case(cases, "acl_change")
    before_acl = _sha256(row.get("before_acl_sha256"), "before ACL")
    after_acl = _sha256(row.get("after_acl_sha256"), "after ACL")
    if before_acl == after_acl:
        raise KnowledgeHubError("ACL observation must demonstrate a real permission change")
    _true(row.get("propagated"), "ACL propagation")
    return {
        "status": "pass",
        "origin": "real-provider",
        "before_acl_sha256": before_acl,
        "after_acl_sha256": after_acl,
        "propagated": True,
    }


def _connector_tombstone(cases: Mapping[str, Any]) -> Dict[str, Any]:
    row = _provider_case(cases, "tombstone")
    object_id_sha = _sha256(row.get("object_id_sha256"), "tombstone object id")
    _true(row.get("delete_acknowledged"), "provider delete acknowledgement")
    post_delete_status = _integer(row.get("post_delete_status_code"), "post-delete status")
    if post_delete_status not in {404, 410}:
        raise KnowledgeHubError("tombstone observation must include provider 404/410 after deletion")
    return {
        "status": "pass",
        "origin": "real-provider",
        "object_id_sha256": object_id_sha,
        "delete_observed": True,
    }


def _connector_retry(cases: Mapping[str, Any]) -> Dict[str, Any]:
    row = _provider_case(cases, "retry_backoff")
    attempts = _integer(row.get("attempts"), "retry attempts", minimum=2)
    first_status = _integer(row.get("first_status_code"), "first retry status")
    if first_status != 429 and first_status < 500:
        raise KnowledgeHubError("retry observation must start from provider 429 or 5xx")
    recovery_status = _integer(row.get("recovery_status_code"), "recovery status")
    if not 200 <= recovery_status < 300:
        raise KnowledgeHubError("retry observation must demonstrate a successful recovery response")
    _number(row.get("backoff_seconds"), "retry backoff seconds", minimum=0.001)
    _true(row.get("backoff_observed"), "retry backoff observation")
    _true(row.get("provider_response_observed"), "retry provider response observation")
    return {
        "status": "pass",
        "origin": "real-provider",
        "attempts": attempts,
        "backoff_observed": True,
        "provider_response_observed": True,
    }


def _connector_freshness(cases: Mapping[str, Any]) -> Dict[str, Any]:
    row = _provider_case(cases, "freshness")
    sample_count = _integer(row.get("sample_count"), "freshness sample count", minimum=1)
    slo_seconds = _number(row.get("slo_seconds"), "freshness SLO", minimum=0.001)
    p95_seconds = _number(row.get("p95_seconds"), "freshness p95")
    if p95_seconds > slo_seconds:
        raise KnowledgeHubError("freshness observation exceeds declared SLO")
    return {
        "status": "pass",
        "origin": "real-provider",
        "sample_count": sample_count,
        "slo_seconds": slo_seconds,
        "p95_seconds": p95_seconds,
    }


def _connector_quarantine(cases: Mapping[str, Any]) -> Dict[str, Any]:
    row = _provider_case(cases, "quarantine")
    before_checkpoint = _sha256(row.get("before_checkpoint_sha256"), "quarantine before checkpoint")
    after_checkpoint = _sha256(row.get("after_checkpoint_sha256"), "quarantine after checkpoint")
    if before_checkpoint != after_checkpoint:
        raise KnowledgeHubError("quarantine observation must not advance checkpoint")
    case_id_sha = _sha256(row.get("case_id_sha256"), "quarantine case id")
    _sha256(row.get("runtime_receipt_sha256"), "quarantine runtime receipt")
    _true(row.get("dead_letter_or_quarantine_observed"), "quarantine observation")
    return {
        "status": "pass",
        "origin": "real-provider",
        "case_id_sha256": case_id_sha,
        "checkpoint_advanced": False,
        "dead_letter_or_quarantine_observed": True,
    }


def _connector_stays(cases: Mapping[str, Any]) -> Dict[str, Any]:
    row = _provider_case(cases, "stays_at_source")
    registry_before = _sha256(row.get("registry_before_sha256"), "registry before")
    registry_after = _sha256(row.get("registry_after_sha256"), "registry after")
    if registry_before != registry_after:
        raise KnowledgeHubError("connector pilot must prove canonical registry stayed unchanged")
    _false(row.get("canonical_write_performed"), "connector canonical write")
    _false(row.get("auto_promotion"), "connector auto promotion")
    return {
        "status": "pass",
        "origin": "real-provider",
        "canonical_write_performed": False,
        "auto_promotion": False,
    }


def _connector_cases(value: Any) -> Dict[str, Any]:
    cases = _object(value, "connector provider cases")
    return {
        "incremental_checkpoint": _connector_incremental(cases),
        "acl_change": _connector_acl(cases),
        "tombstone": _connector_tombstone(cases),
        "retry_backoff": _connector_retry(cases),
        "freshness": _connector_freshness(cases),
        "quarantine": _connector_quarantine(cases),
        "stays_at_source": _connector_stays(cases),
    }


def _connector_provider(value: Any) -> Dict[str, Any]:
    provider = _object(value, "provider observation")
    provider_name = _text(provider.get("name"), "provider name", maximum=64)
    if provider_name not in KNOWN_PROVIDERS:
        raise KnowledgeHubError("connector observation provider is unsupported")
    transport = _text(provider.get("transport"), "provider transport", maximum=128)
    if transport in {"static", "mock", "fixture", "local"}:
        raise KnowledgeHubError("connector observation transport must be a real provider API")
    _true(provider.get("network_observed"), "provider network observation")
    return {
        "name": provider_name,
        "version": _text(provider.get("version"), "provider version", maximum=256),
        "adapter_commit": _git_sha(provider.get("adapter_commit"), "adapter commit"),
        "account_id_sha256": _sha256(provider.get("account_id_sha256"), "provider account id"),
        "transport": transport,
        "network_observed": True,
    }


def build_connector_provider_evidence(observation: Mapping[str, Any]) -> Dict[str, Any]:
    if observation.get("schema_version") != CONNECTOR_SCHEMA:
        raise KnowledgeHubError("connector observation schema_version is unsupported")
    payload = _base(observation, "connector-provider-pilot", "real-provider")
    payload["observation_ledger_sha256"] = _sha256(
        observation.get("observation_ledger_sha256"), "connector observation ledger"
    )
    payload["provider"] = _connector_provider(observation.get("provider"))
    payload["cases"] = _connector_cases(observation.get("cases"))
    validate_external_evidence(payload, expected_gap="connector-provider-pilot")
    return payload


def _retrieval_metrics(value: Any) -> Dict[str, Any]:
    metrics = _object(value, "retrieval metrics")
    return {
        "recall": _number(metrics.get("recall"), "recall"),
        "mrr": _number(metrics.get("mrr"), "mrr"),
        "ndcg": _number(metrics.get("ndcg"), "ndcg"),
        "authority_recall": _number(metrics.get("authority_recall"), "authority recall"),
        "forbidden_hit_rate": _number(metrics.get("forbidden_hit_rate"), "forbidden hit rate"),
        "p50_ms": _number(metrics.get("p50_ms"), "retrieval p50"),
        "p95_ms": _number(metrics.get("p95_ms"), "retrieval p95"),
    }


def _retrieval_comparison(value: Any) -> Dict[str, Any]:
    comparison = _object(value, "retrieval comparison")
    return {
        "status": _text(comparison.get("status"), "retrieval comparison status", maximum=32),
        "new_critical_failures": _integer(
            comparison.get("new_critical_failures"), "new critical retrieval failures"
        ),
        "result_sha256": _sha256(comparison.get("result_sha256"), "retrieval result"),
    }


def _retrieval_evaluation(value: Any) -> Dict[str, Any]:
    evaluation = _object(value, "production retrieval observation")
    if evaluation.get("raw_query_stored_in_evidence") is not False:
        raise KnowledgeHubError("retrieval evidence manifest must not store raw production queries")
    case_count = _integer(evaluation.get("case_count"), "retrieval case count", minimum=200)
    production_count = _integer(
        evaluation.get("production_derived_case_count"), "production-derived case count", minimum=200
    )
    synthetic_count = _integer(evaluation.get("synthetic_case_count"), "synthetic case count")
    if production_count != case_count or synthetic_count != 0:
        raise KnowledgeHubError("retrieval observation must be entirely production-derived")
    _sha256(evaluation.get("dataset_receipt_sha256"), "retrieval dataset receipt")
    _sha256(evaluation.get("evaluation_run_receipt_sha256"), "retrieval run receipt")
    return {
        "case_count": case_count,
        "production_derived_case_count": production_count,
        "synthetic_case_count": synthetic_count,
        "dataset_sha256": _sha256(evaluation.get("dataset_sha256"), "retrieval dataset"),
        "evaluator_version": _text(evaluation.get("evaluator_version"), "evaluator version", maximum=256),
        "approved_baseline": _text(evaluation.get("approved_baseline"), "approved baseline", maximum=256),
        "window_start": _text(evaluation.get("window_start"), "retrieval window_start", maximum=128),
        "window_end": _text(evaluation.get("window_end"), "retrieval window_end", maximum=128),
        "metrics": _retrieval_metrics(evaluation.get("metrics")),
        "comparison": _retrieval_comparison(evaluation.get("comparison")),
    }


def build_production_retrieval_evidence(observation: Mapping[str, Any]) -> Dict[str, Any]:
    if observation.get("schema_version") != RETRIEVAL_SCHEMA:
        raise KnowledgeHubError("retrieval observation schema_version is unsupported")
    payload = _base(observation, "production-retrieval-eval", "real-production")
    payload["evaluation"] = _retrieval_evaluation(observation.get("evaluation"))
    validate_external_evidence(payload, expected_gap="production-retrieval-eval")
    return payload


def _memory_case(cases: Mapping[str, Any], name: str) -> Dict[str, Any]:
    row = _object(cases.get(name), "{} memory observation".format(name))
    if row.get("status") != "pass":
        raise KnowledgeHubError("{} memory observation must pass".format(name))
    _sha256(row.get("receipt_sha256"), "{} memory receipt".format(name))
    _integer(row.get("event_count"), "{} memory event count".format(name), minimum=1)
    return row


def _memory_inputs(cases: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        name: _memory_case(cases, name)
        for name in (
            "ttl",
            "forget",
            "supersede",
            "principal_isolation",
            "agent_isolation",
            "scope_isolation",
            "scope_delete",
            "durable_consolidation",
        )
    }


def _validate_memory_inputs(rows: Mapping[str, Mapping[str, Any]]) -> None:
    _true(rows["ttl"].get("expiry_verified"), "TTL expiry verification")
    _true(rows["forget"].get("deletion_verified"), "forget deletion verification")
    _true(rows["supersede"].get("old_state_hidden"), "supersede old-state hiding")
    for name in ("principal_isolation", "agent_isolation", "scope_isolation"):
        if _integer(rows[name].get("cross_boundary_leak_count"), "{} leak count".format(name)) != 0:
            raise KnowledgeHubError("{} must have zero cross-boundary leaks".format(name))
    _true(rows["scope_delete"].get("deletion_verified"), "scope deletion verification")
    durable = rows["durable_consolidation"]
    _true(durable.get("candidate_only"), "durable consolidation candidate-only")
    _true(durable.get("provenance_bound"), "durable consolidation provenance")
    _true(durable.get("owner_gate_observed"), "durable consolidation owner gate")
    _false(durable.get("canonical_write_performed"), "durable consolidation canonical write")


def _memory_output_cases() -> Dict[str, Any]:
    return {
        "ttl": {"status": "pass", "origin": "real-production", "expiry_verified": True},
        "forget": {"status": "pass", "origin": "real-production", "deletion_verified": True},
        "supersede": {"status": "pass", "origin": "real-production", "old_state_hidden": True},
        "principal_isolation": {
            "status": "pass", "origin": "real-production", "cross_boundary_leak_count": 0
        },
        "agent_isolation": {
            "status": "pass", "origin": "real-production", "cross_boundary_leak_count": 0
        },
        "scope_isolation": {
            "status": "pass", "origin": "real-production", "cross_boundary_leak_count": 0
        },
        "scope_delete": {
            "status": "pass", "origin": "real-production", "deletion_verified": True
        },
        "durable_consolidation": {
            "status": "pass",
            "origin": "real-production",
            "candidate_only": True,
            "provenance_bound": True,
            "owner_gate_observed": True,
            "canonical_write_performed": False,
        },
    }


def _memory_pilot(value: Any) -> Dict[str, Any]:
    pilot = _object(value, "memory lifecycle observation")
    cases = _object(pilot.get("cases"), "memory lifecycle cases")
    rows = _memory_inputs(cases)
    _validate_memory_inputs(rows)
    return {
        "runtime_version": _text(pilot.get("runtime_version"), "memory runtime version", maximum=256),
        "window_start": _text(pilot.get("window_start"), "memory window_start", maximum=128),
        "window_end": _text(pilot.get("window_end"), "memory window_end", maximum=128),
        "result_sha256": _sha256(pilot.get("result_sha256"), "memory pilot result"),
        "cases": _memory_output_cases(),
    }


def build_memory_lifecycle_evidence(observation: Mapping[str, Any]) -> Dict[str, Any]:
    if observation.get("schema_version") != MEMORY_SCHEMA:
        raise KnowledgeHubError("memory observation schema_version is unsupported")
    payload = _base(observation, "memory-lifecycle-pilot", "real-production")
    payload["pilot"] = _memory_pilot(observation.get("pilot"))
    validate_external_evidence(payload, expected_gap="memory-lifecycle-pilot")
    return payload



def _adoption_slo(value: Any) -> Dict[str, Any]:
    slo = _object(value, "adoption SLO observation")
    _sha256(slo.get("receipt_sha256"), "adoption SLO receipt")
    if _text(slo.get("status"), "adoption SLO status", maximum=32) != "pass":
        raise KnowledgeHubError("adoption SLO observation must pass")
    p50_ms = _number(slo.get("p50_ms"), "adoption p50")
    p95_ms = _number(slo.get("p95_ms"), "adoption p95")
    if p95_ms < p50_ms:
        raise KnowledgeHubError("adoption p95 must not be below p50")
    error_rate = _number(slo.get("error_rate"), "adoption error rate")
    if error_rate > 1.0:
        raise KnowledgeHubError("adoption error rate must be in [0,1]")
    if _text(
        slo.get("retrieval_lane_health"),
        "adoption retrieval lane health",
        maximum=32,
    ) != "pass":
        raise KnowledgeHubError("adoption retrieval lane health must pass")
    return {
        "status": "pass",
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "error_rate": error_rate,
        "retrieval_lane_health": "pass",
    }


def _adoption_traceability(value: Any) -> Dict[str, Any]:
    row = _object(value, "adoption traceability observation")
    _sha256(row.get("receipt_sha256"), "adoption traceability receipt")
    if _text(row.get("status"), "adoption traceability status", maximum=32) != "pass":
        raise KnowledgeHubError("adoption traceability observation must pass")
    _true(
        row.get("work_item_run_handoff_receipt_linked"),
        "cross-work trace linkage",
    )
    return {
        "status": "pass",
        "work_item_run_handoff_receipt_linked": True,
    }


def _adoption_privacy(value: Any) -> Dict[str, Any]:
    row = _object(value, "adoption privacy observation")
    _sha256(row.get("receipt_sha256"), "adoption privacy receipt")
    result: Dict[str, Any] = {}
    for key in (
        "raw_query_stored",
        "raw_task_stored",
        "raw_prompt_stored",
        "raw_content_stored",
    ):
        _false(row.get(key), "adoption privacy {}".format(key))
        result[key] = False
    mode = _text(
        row.get("network_export_mode"),
        "adoption network export mode",
        maximum=64,
    )
    if mode not in {"disabled", "explicitly-configured"}:
        raise KnowledgeHubError(
            "adoption network export must be disabled or explicitly configured"
        )
    result["network_export_mode"] = mode
    return result


def _adoption_observation(value: Any) -> Dict[str, Any]:
    adoption = _object(value, "adoption observation")
    _sha256(adoption.get("call_ledger_receipt_sha256"), "adoption call ledger receipt")
    _sha256(adoption.get("feedback_receipt_sha256"), "adoption feedback receipt")
    observation_days = _integer(
        adoption.get("observation_days"), "adoption observation days"
    )
    valid_calls = _integer(
        adoption.get("valid_real_calls"), "adoption valid real calls"
    )
    synthetic_calls = _integer(
        adoption.get("synthetic_calls"), "adoption synthetic calls"
    )
    feedback_count = _integer(
        adoption.get("explicit_feedback_count"),
        "adoption explicit feedback count",
    )
    if observation_days < 30 and valid_calls < 50:
        raise KnowledgeHubError(
            "adoption observation requires 30 days or 50 valid real calls"
        )
    if synthetic_calls != 0:
        raise KnowledgeHubError(
            "adoption observation must not include synthetic calls"
        )
    if feedback_count < 10:
        raise KnowledgeHubError(
            "adoption observation requires at least 10 explicit feedback items"
        )
    return {
        "runtime_version": _text(
            adoption.get("runtime_version"),
            "adoption runtime version",
            maximum=256,
        ),
        "window_start": _text(
            adoption.get("window_start"),
            "adoption window_start",
            maximum=128,
        ),
        "window_end": _text(
            adoption.get("window_end"),
            "adoption window_end",
            maximum=128,
        ),
        "observation_days": observation_days,
        "valid_real_calls": valid_calls,
        "synthetic_calls": synthetic_calls,
        "explicit_feedback_count": feedback_count,
        "call_ledger_sha256": _sha256(
            adoption.get("call_ledger_sha256"), "adoption call ledger"
        ),
        "feedback_sha256": _sha256(
            adoption.get("feedback_sha256"), "adoption feedback"
        ),
        "slo": _adoption_slo(adoption.get("slo")),
        "traceability": _adoption_traceability(
            adoption.get("traceability")
        ),
        "privacy": _adoption_privacy(adoption.get("privacy")),
    }


def build_real_adoption_evidence(
    observation: Mapping[str, Any],
) -> Dict[str, Any]:
    if observation.get("schema_version") != ADOPTION_SCHEMA:
        raise KnowledgeHubError(
            "adoption observation schema_version is unsupported"
        )
    payload = _base(
        observation,
        "real-adoption-evidence",
        "real-production",
    )
    payload["adoption"] = _adoption_observation(
        observation.get("adoption")
    )
    validate_external_evidence(
        payload,
        expected_gap="real-adoption-evidence",
    )
    return payload


def build_pilot_evidence(observation: Mapping[str, Any], *, expected_gap: str = "") -> Dict[str, Any]:
    gap_id = _text(observation.get("gap_id"), "gap id", maximum=128)
    if expected_gap and gap_id != expected_gap:
        raise KnowledgeHubError("pilot observation gap does not match expected gap")
    if gap_id == "connector-provider-pilot":
        return build_connector_provider_evidence(observation)
    if gap_id == "production-retrieval-eval":
        return build_production_retrieval_evidence(observation)
    if gap_id == "memory-lifecycle-pilot":
        return build_memory_lifecycle_evidence(observation)
    if gap_id == "real-adoption-evidence":
        return build_real_adoption_evidence(observation)
    raise KnowledgeHubError("pilot observation gap is unsupported")


def load_pilot_observation(path: pathlib.Path, *, maximum_bytes: int = 4 * 1024 * 1024) -> Dict[str, Any]:
    path = pathlib.Path(path)
    if not path.is_file() or path.is_symlink():
        raise KnowledgeHubError("pilot observation input is unavailable")
    if path.stat().st_size > maximum_bytes:
        raise KnowledgeHubError("pilot observation input exceeds byte budget")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("pilot observation input is invalid JSON") from exc
    return _object(value, "pilot observation")
