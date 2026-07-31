"""Privacy-preserving local usage, performance and feedback metrics."""

from __future__ import annotations

import datetime as dt
import hashlib
import pathlib
from typing import Any, Dict, List, Mapping, Sequence

from .common import (
    load_jsonl,
    utc_timestamp,
)
from .artifact_governance import evaluate_artifact_governance
from .lifecycle_metrics import lifecycle_operating_metrics
from .output_contract import status_contract
from .retrieval_telemetry import (
    IMPLEMENTATION_GENERATION,
    INTERACTION_CONTRACT,
    INTERACTIVE_TELEMETRY_SCHEMA_VERSION,
    PERFORMANCE_CONTRACT,
    append_optional_telemetry,
    append_telemetry_row,
    make_interaction_id,
)


__all__ = [
    "IMPLEMENTATION_GENERATION",
    "INTERACTION_CONTRACT",
    "INTERACTIVE_TELEMETRY_SCHEMA_VERSION",
    "PERFORMANCE_CONTRACT",
    "append_optional_telemetry",
    "make_interaction_id",
]


FEEDBACK_SCHEMA_VERSION = 2
LOCAL_METRICS_SCHEMA_VERSION = 5
MINIMUM_PERFORMANCE_SAMPLE_COUNT = 10
SEARCH_WARM_TARGET_MS = 500.0
CONTEXT_WARM_TARGET_MS = 1000.0
INDEX_PREPARATION_TARGET_MS = 5000.0


def _is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _current_interaction_rows(
    rows: Sequence[Mapping[str, Any]],
    retrieval_kind: str,
) -> List[Mapping[str, Any]]:
    return [
        row
        for row in rows
        if row.get("schema_version") == INTERACTIVE_TELEMETRY_SCHEMA_VERSION
        and row.get("sample_kind") == "interactive"
        and row.get("interaction_contract") == INTERACTION_CONTRACT
        and row.get("retrieval_kind") == retrieval_kind
        and _is_sha256(row.get("interaction_id"))
        and _is_sha256(row.get("query_sha256"))
        and row.get("raw_query_stored") is False
    ]


def _current_performance_rows(
    rows: Sequence[Mapping[str, Any]],
) -> List[Mapping[str, Any]]:
    return [
        row
        for row in rows
        if row.get("performance_contract") == PERFORMANCE_CONTRACT
        and row.get("implementation_generation") == IMPLEMENTATION_GENERATION
    ]


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = int(round((len(ordered) - 1) * fraction))
    return round(float(ordered[max(0, min(position, len(ordered) - 1))]), 2)


def _numeric_latency(value: Any) -> float:
    try:
        return max(0.0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _index_preparation_latency(row: Mapping[str, Any]) -> float:
    timings = row.get("search_stage_timing") or row.get("stage_timing") or {}
    if not isinstance(timings, Mapping):
        timings = {}
    measured = _numeric_latency(timings.get("index_ensure_ms"))
    if measured:
        return measured
    # Fail closed for an otherwise current preparation sample: do not hide its
    # end-to-end cost merely because an optional stage timer is absent.
    return _numeric_latency(row.get("latency_ms"))


def _performance_samples(
    rows: Sequence[Mapping[str, Any]],
) -> Dict[str, List[float]]:
    samples: Dict[str, List[float]] = {
        "warm": [],
        "preparation": [],
        "end_to_end": [],
        "unclassified": [],
    }
    for row in rows:
        latency = _numeric_latency(row.get("latency_ms"))
        samples["end_to_end"].append(latency)
        index_state = str(row.get("index_state", "")).strip()
        if index_state == "warm":
            samples["warm"].append(latency)
        elif index_state in {"rebuilt", "updated"}:
            samples["preparation"].append(_index_preparation_latency(row))
        else:
            samples["unclassified"].append(latency)
    return samples


def _date(value: Any) -> dt.date:
    text = str(value or "")
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return dt.date.min


def record_feedback(
    root: pathlib.Path,
    query: str,
    outcome: str,
    selected_id: str = "",
    task_type: str = "general",
    interaction_id: str = "",
) -> Dict[str, Any]:
    if outcome not in {"found", "not-found"}:
        raise ValueError("outcome must be found or not-found")
    if outcome == "not-found" and selected_id:
        raise ValueError("--outcome not-found does not accept selected_id")
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    interactions = [
        row
        for path, retrieval_kind in (
            (root / ".cache/knowledge-hub/search-telemetry.jsonl", "search"),
            (root / ".cache/knowledge-hub/context-telemetry.jsonl", "context"),
        )
        for row in _current_interaction_rows(load_jsonl(path), retrieval_kind)
        if row.get("query_sha256") == query_hash
        and (not interaction_id or row.get("interaction_id") == interaction_id)
    ]
    if not interactions:
        raise ValueError("feedback requires a matching current-contract retrieval interaction")
    interaction = max(interactions, key=lambda row: str(row.get("recorded_at", "")))
    resolved_interaction_id = str(interaction.get("interaction_id", ""))
    if not resolved_interaction_id:
        raise ValueError("matching retrieval interaction is missing interaction_id")
    if outcome == "found":
        result_ids = {str(value) for value in interaction.get("result_ids", []) if str(value)}
        if selected_id not in result_ids:
            raise ValueError("selected_id was not present in the matching retrieval interaction")
    existing_feedback = load_jsonl(root / ".cache/knowledge-hub/retrieval-feedback.jsonl")
    if any(
        row.get("schema_version") == FEEDBACK_SCHEMA_VERSION
        and row.get("interaction_contract") == INTERACTION_CONTRACT
        and row.get("interaction_id") == resolved_interaction_id
        for row in existing_feedback
    ):
        raise ValueError("feedback already exists for this retrieval interaction")
    row = {
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "sample_kind": "explicit-feedback",
        "interaction_contract": INTERACTION_CONTRACT,
        "interaction_id": resolved_interaction_id,
        "retrieval_kind": interaction.get("retrieval_kind", ""),
        "recorded_at": utc_timestamp(),
        "query_sha256": query_hash,
        "query_term_count": len(query.split()),
        "outcome": outcome,
        "selected_id": selected_id if outcome == "found" else "",
        "task_type": task_type,
        "raw_query_stored": False,
    }
    append_telemetry_row(root / ".cache/knowledge-hub/retrieval-feedback.jsonl", row)
    return {"status": "recorded", "raw_query_stored": False, "record": row}


def _retrieval_improvement_queue(
    search_rows: Sequence[Mapping[str, Any]],
    feedback_rows: Sequence[Mapping[str, Any]],
    *,
    sample_limit: int = 20,
) -> Dict[str, Any]:
    signals: Dict[str, Dict[str, Any]] = {}
    for row in search_rows:
        if int(row.get("result_count", 0) or 0) != 0:
            continue
        query_sha256 = str(row.get("query_sha256", ""))
        if not _is_sha256(query_sha256):
            continue
        signal = signals.setdefault(
            query_sha256,
            {
                "query_sha256": query_sha256,
                "zero_hit_count": 0,
                "not_found_count": 0,
                "interaction_ids": set(),
                "task_types": set(),
                "last_seen_at": "",
            },
        )
        signal["zero_hit_count"] += 1
        signal["interaction_ids"].add(str(row.get("interaction_id", "")))
        signal["last_seen_at"] = max(
            signal["last_seen_at"], str(row.get("recorded_at", ""))
        )
    for row in feedback_rows:
        if row.get("outcome") != "not-found":
            continue
        query_sha256 = str(row.get("query_sha256", ""))
        if not _is_sha256(query_sha256):
            continue
        signal = signals.setdefault(
            query_sha256,
            {
                "query_sha256": query_sha256,
                "zero_hit_count": 0,
                "not_found_count": 0,
                "interaction_ids": set(),
                "task_types": set(),
                "last_seen_at": "",
            },
        )
        signal["not_found_count"] += 1
        signal["interaction_ids"].add(str(row.get("interaction_id", "")))
        signal["task_types"].add(str(row.get("task_type", "general")))
        signal["last_seen_at"] = max(
            signal["last_seen_at"], str(row.get("recorded_at", ""))
        )
    rows = []
    for signal in signals.values():
        rows.append(
            {
                "query_sha256": signal["query_sha256"],
                "signal_count": signal["zero_hit_count"]
                + signal["not_found_count"],
                "zero_hit_count": signal["zero_hit_count"],
                "not_found_count": signal["not_found_count"],
                "interaction_count": len(
                    {value for value in signal["interaction_ids"] if value}
                ),
                "task_types": sorted(
                    value for value in signal["task_types"] if value
                ),
                "last_seen_at": signal["last_seen_at"],
                "recommended_action": "review-routing-or-knowledge-gap",
            }
        )
    rows.sort(
        key=lambda row: (
            -int(row["signal_count"]),
            str(row["query_sha256"]),
        )
    )
    return {
        "status": "action-needed" if rows else "clear",
        "report_only": True,
        "raw_query_stored": False,
        "query_hash_only": True,
        "candidate_count": len(rows),
        "sample": rows[:sample_limit],
        "automatic_content_write": False,
        "automatic_route_change": False,
    }


def local_metrics(
    root: pathlib.Path,
    as_of: dt.date | None = None,
) -> Dict[str, Any]:
    all_search_rows = load_jsonl(root / ".cache/knowledge-hub/search-telemetry.jsonl")
    all_context_rows = load_jsonl(root / ".cache/knowledge-hub/context-telemetry.jsonl")
    candidate_search_rows = _current_interaction_rows(all_search_rows, "search")
    candidate_context_rows = _current_interaction_rows(all_context_rows, "context")
    interaction_counts: Dict[str, int] = {}
    for row in candidate_search_rows + candidate_context_rows:
        interaction_id = str(row.get("interaction_id", ""))
        interaction_counts[interaction_id] = interaction_counts.get(interaction_id, 0) + 1
    duplicate_interaction_ids = {
        interaction_id
        for interaction_id, count in interaction_counts.items()
        if count > 1
    }
    search_rows = [
        row
        for row in candidate_search_rows
        if row.get("interaction_id") not in duplicate_interaction_ids
    ]
    context_rows = [
        row
        for row in candidate_context_rows
        if row.get("interaction_id") not in duplicate_interaction_ids
    ]
    all_rows = search_rows + context_rows
    interactions_by_id = {
        str(row.get("interaction_id")): row
        for row in all_rows
    }
    all_feedback_rows = load_jsonl(root / ".cache/knowledge-hub/retrieval-feedback.jsonl")
    feedback_rows: List[Mapping[str, Any]] = []
    feedback_interaction_ids = set()
    for row in all_feedback_rows:
        interaction_id = str(row.get("interaction_id", ""))
        interaction = interactions_by_id.get(interaction_id)
        outcome = str(row.get("outcome", ""))
        selected_id = str(row.get("selected_id", ""))
        if (
            row.get("schema_version") != FEEDBACK_SCHEMA_VERSION
            or row.get("sample_kind") != "explicit-feedback"
            or row.get("interaction_contract") != INTERACTION_CONTRACT
            or interaction is None
            or interaction_id in feedback_interaction_ids
            or row.get("query_sha256") != interaction.get("query_sha256")
            or row.get("retrieval_kind") != interaction.get("retrieval_kind")
            or row.get("raw_query_stored") is not False
            or outcome not in {"found", "not-found"}
        ):
            continue
        if outcome == "found" and selected_id not in {
            str(value) for value in interaction.get("result_ids", []) if str(value)
        }:
            continue
        if outcome == "not-found" and selected_id:
            continue
        feedback_rows.append(row)
        feedback_interaction_ids.add(interaction_id)
    dates = sorted(value for value in (_date(row.get("recorded_at")) for row in all_rows) if value != dt.date.min)
    observation_days = (dates[-1] - dates[0]).days + 1 if dates else 0
    invocation_count = len(all_rows)
    usage_evaluable = observation_days >= 30 or invocation_count >= 50
    found_count = sum(1 for row in feedback_rows if row.get("outcome") == "found")
    not_found_count = sum(1 for row in feedback_rows if row.get("outcome") == "not-found")
    feedback_count = found_count + not_found_count
    found_rate = round(found_count / float(feedback_count), 4) if feedback_count else 0.0
    performance_search_rows = _current_performance_rows(search_rows)
    performance_context_rows = _current_performance_rows(context_rows)
    current_contract_search_rows = [
        row
        for row in search_rows
        if row.get("performance_contract") == PERFORMANCE_CONTRACT
    ]
    current_contract_context_rows = [
        row
        for row in context_rows
        if row.get("performance_contract") == PERFORMANCE_CONTRACT
    ]
    search_samples = _performance_samples(performance_search_rows)
    context_samples = _performance_samples(performance_context_rows)
    search_latencies = search_samples["warm"]
    context_latencies = context_samples["warm"]
    zero_hits = sum(1 for row in search_rows if int(row.get("result_count", 0) or 0) == 0)
    search_p95 = _percentile(search_latencies, 0.95)
    context_p95 = _percentile(context_latencies, 0.95)
    performance_evaluable = (
        len(search_latencies) >= MINIMUM_PERFORMANCE_SAMPLE_COUNT
        and len(context_latencies) >= MINIMUM_PERFORMANCE_SAMPLE_COUNT
    )
    preparation_search_p95 = _percentile(search_samples["preparation"], 0.95)
    preparation_context_p95 = _percentile(context_samples["preparation"], 0.95)
    preparation_observed = bool(
        search_samples["preparation"] or context_samples["preparation"]
    )
    preparation_failed = (
        preparation_search_p95 > INDEX_PREPARATION_TARGET_MS
        or preparation_context_p95 > INDEX_PREPARATION_TARGET_MS
    )
    performance_ready = (
        performance_evaluable
        and search_p95 <= SEARCH_WARM_TARGET_MS
        and context_p95 <= CONTEXT_WARM_TARGET_MS
        and not preparation_failed
    )
    evaluable = usage_evaluable and performance_evaluable
    adoption_ready = evaluable and feedback_count >= 10 and found_rate >= 0.8 and performance_ready
    lifecycle = lifecycle_operating_metrics(root, as_of or dt.date.today())
    artifact_capacity = evaluate_artifact_governance(root)
    improvement = _retrieval_improvement_queue(search_rows, feedback_rows)
    payload = {
        "schema_version": LOCAL_METRICS_SCHEMA_VERSION,
        "status": "pass",
        "status_contract": status_contract("pass"),
        "measurement_contract": {
            "interaction_contract": INTERACTION_CONTRACT,
            "performance_contract": PERFORMANCE_CONTRACT,
            "implementation_generation": IMPLEMENTATION_GENERATION,
            "interactive_telemetry_schema_version": INTERACTIVE_TELEMETRY_SCHEMA_VERSION,
            "feedback_schema_version": FEEDBACK_SCHEMA_VERSION,
        },
        "privacy": {"raw_query_stored": False, "query_hash_only": True},
        "usage": {
            "invocation_count": invocation_count,
            "search_count": len(search_rows),
            "context_count": len(context_rows),
            "excluded_historical_or_noninteractive_count": (
                len(all_search_rows) + len(all_context_rows) - invocation_count
            ),
            "observation_days": observation_days,
            "first_observed_at": dates[0].isoformat() if dates else "",
            "last_observed_at": dates[-1].isoformat() if dates else "",
        },
        "retrieval": {
            "zero_hit_count": zero_hits,
            "zero_hit_rate": round(zero_hits / float(len(search_rows)), 4) if search_rows else 0.0,
            "feedback_count": feedback_count,
            "found_count": found_count,
            "not_found_count": not_found_count,
            "found_rate": found_rate,
            "excluded_unbound_or_historical_feedback_count": len(all_feedback_rows) - len(feedback_rows),
        },
        "retrieval_improvement": improvement,
        "knowledge_lifecycle": lifecycle,
        "artifact_capacity": artifact_capacity,
        "performance": {
            "search_p95_ms": search_p95,
            "context_p95_ms": context_p95,
            "search_target_ms": SEARCH_WARM_TARGET_MS,
            "context_target_ms": CONTEXT_WARM_TARGET_MS,
            "search_sample_count": len(search_latencies),
            "context_sample_count": len(context_latencies),
            "warm_interactive": {
                "search_p95_ms": search_p95,
                "context_p95_ms": context_p95,
                "search_target_ms": SEARCH_WARM_TARGET_MS,
                "context_target_ms": CONTEXT_WARM_TARGET_MS,
                "search_sample_count": len(search_latencies),
                "context_sample_count": len(context_latencies),
                "minimum_sample_count_each": MINIMUM_PERFORMANCE_SAMPLE_COUNT,
                "evaluable": performance_evaluable,
            },
            "index_preparation": {
                "search_p95_ms": preparation_search_p95,
                "context_p95_ms": preparation_context_p95,
                "maximum_target_ms": INDEX_PREPARATION_TARGET_MS,
                "search_sample_count": len(search_samples["preparation"]),
                "context_sample_count": len(context_samples["preparation"]),
                "observed": preparation_observed,
                "status": (
                    "fail"
                    if preparation_failed
                    else ("pass" if preparation_observed else "not-observed")
                ),
            },
            "end_to_end_observed": {
                "search_p95_ms": _percentile(search_samples["end_to_end"], 0.95),
                "context_p95_ms": _percentile(context_samples["end_to_end"], 0.95),
                "search_sample_count": len(search_samples["end_to_end"]),
                "context_sample_count": len(context_samples["end_to_end"]),
                "thresholded": False,
            },
            "excluded_non_warm_sample_count": (
                len(search_samples["preparation"])
                + len(context_samples["preparation"])
                + len(search_samples["unclassified"])
                + len(context_samples["unclassified"])
            ),
            "excluded_stale_contract_sample_count": (
                len(search_rows)
                + len(context_rows)
                - len(current_contract_search_rows)
                - len(current_contract_context_rows)
            ),
            "excluded_stale_generation_sample_count": (
                len(current_contract_search_rows)
                + len(current_contract_context_rows)
                - len(performance_search_rows)
                - len(performance_context_rows)
            ),
            "minimum_sample_count_each": MINIMUM_PERFORMANCE_SAMPLE_COUNT,
            "evaluable": performance_evaluable,
            "status": (
                "pass"
                if performance_ready
                else ("fail" if performance_evaluable or preparation_failed else "pending")
            ),
        },
        "adoption": {
            "evaluable": evaluable,
            "ready": adoption_ready,
            "criteria": {
                "observation_days_or_invocations": "observation_days >= 30 or invocation_count >= 50",
                "sample_kind": (
                    "current performance-contract and implementation-generation warm "
                    "interactions; index preparation is measured separately and "
                    "end-to-end latency remains report-only"
                ),
                "minimum_performance_samples_each": MINIMUM_PERFORMANCE_SAMPLE_COUNT,
                "minimum_feedback_count": 10,
                "minimum_found_rate": 0.8,
                "performance_required": True,
            },
            "reason": (
                "adoption evidence meets the observation, feedback and performance thresholds"
                if adoption_ready
                else "long-term adoption is not yet evidenced"
            ),
        },
    }
    return payload


def local_metrics_summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    usage = payload.get("usage", {}) or {}
    retrieval = payload.get("retrieval", {}) or {}
    performance = payload.get("performance", {}) or {}
    lifecycle = payload.get("knowledge_lifecycle", {}) or {}
    improvement = payload.get("retrieval_improvement", {}) or {}
    artifact = payload.get("artifact_capacity", {}) or {}
    return {
        "schema_version": 2,
        "projection": "knowledge-local-metrics-summary-v2",
        "status": payload.get("status", ""),
        "status_contract": payload.get("status_contract", {}),
        "privacy": payload.get("privacy", {}),
        "usage": {
            key: usage.get(key)
            for key in (
                "invocation_count",
                "search_count",
                "context_count",
                "observation_days",
            )
        },
        "retrieval": {
            key: retrieval.get(key)
            for key in (
                "zero_hit_count",
                "zero_hit_rate",
                "feedback_count",
                "found_rate",
            )
        },
        "performance": {
            "status": performance.get("status", ""),
            "warm_interactive": performance.get("warm_interactive", {}),
            "index_preparation": performance.get("index_preparation", {}),
        },
        "lifecycle": {
            "reviewing_count": lifecycle.get("reviewing_count", 0),
            "reviewing_age_buckets": lifecycle.get(
                "reviewing_age_buckets", {}
            ),
            "flow": lifecycle.get("flow", {}),
            "decision_lead_time_days": lifecycle.get(
                "decision_lead_time_days", {}
            ),
            "cold_candidate_count": (
                lifecycle.get("cold_candidates", {}) or {}
            ).get("count", 0),
        },
        "retrieval_improvement": {
            "status": improvement.get("status", ""),
            "candidate_count": improvement.get("candidate_count", 0),
            "sample": list(improvement.get("sample", []))[:10],
            "automatic_content_write": False,
        },
        "artifact_capacity": {
            "status": artifact.get("status", ""),
            "tracked": artifact.get("tracked", {}),
            "growth": artifact.get("growth", {}),
            "violation_count": artifact.get("violation_count", 0),
            "automatic_delete": False,
        },
        "adoption": payload.get("adoption", {}),
    }
