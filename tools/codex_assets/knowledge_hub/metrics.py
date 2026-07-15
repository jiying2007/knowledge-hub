"""Privacy-preserving local usage, performance and feedback metrics."""

from __future__ import annotations

import datetime as dt
import errno
import fcntl
import hashlib
import os
import pathlib
import secrets
from typing import Any, Dict, List, Mapping, Sequence

from .common import compact_json, load_jsonl, utc_timestamp


INTERACTIVE_TELEMETRY_SCHEMA_VERSION = 3
INTERACTION_CONTRACT = "knowledge-retrieval-interaction-v1"
FEEDBACK_SCHEMA_VERSION = 2
MINIMUM_PERFORMANCE_SAMPLE_COUNT = 10


def make_interaction_id(
    kind: str,
    query_sha256: str,
    recorded_at: str,
    nonce: str = "",
) -> str:
    payload = "{}\0{}\0{}\0{}\0{}".format(
        INTERACTION_CONTRACT,
        kind,
        query_sha256,
        recorded_at,
        nonce or secrets.token_hex(16),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = int(round((len(ordered) - 1) * fraction))
    return round(float(ordered[max(0, min(position, len(ordered) - 1))]), 2)


def _date(value: Any) -> dt.date:
    text = str(value or "")
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return dt.date.min


def _append_locked(path: pathlib.Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.write(compact_json(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def append_optional_telemetry(
    path: pathlib.Path,
    row: Mapping[str, Any],
    enabled: bool = True,
) -> Dict[str, Any]:
    """Append local telemetry without making observation a command dependency."""
    if not enabled:
        return {
            "status": "disabled",
            "recorded": False,
            "non_blocking": True,
            "reason": "cli-disabled",
            "error_code": "",
        }
    if os.environ.get("KNOWLEDGE_TELEMETRY", "1").lower() in {"0", "false", "off", "no"}:
        return {
            "status": "disabled",
            "recorded": False,
            "non_blocking": True,
            "reason": "environment-disabled",
            "error_code": "",
        }
    try:
        _append_locked(path, row)
    except OSError as exc:
        error_code = errno.errorcode.get(exc.errno or 0, "OSERROR")
        permission_errors = {errno.EACCES, errno.EPERM, errno.EROFS}
        return {
            "status": "degraded",
            "recorded": False,
            "non_blocking": True,
            "reason": (
                "read-only-or-permission-denied"
                if exc.errno in permission_errors
                else "local-storage-unavailable"
            ),
            "error_code": error_code,
        }
    return {
        "status": "recorded",
        "recorded": True,
        "non_blocking": True,
        "reason": "",
        "error_code": "",
    }


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
    _append_locked(root / ".cache/knowledge-hub/retrieval-feedback.jsonl", row)
    return {"status": "recorded", "raw_query_stored": False, "record": row}


def local_metrics(root: pathlib.Path) -> Dict[str, Any]:
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
    search_latencies = [float(row.get("latency_ms", 0) or 0) for row in search_rows]
    context_latencies = [float(row.get("latency_ms", 0) or 0) for row in context_rows]
    zero_hits = sum(1 for row in search_rows if int(row.get("result_count", 0) or 0) == 0)
    search_p95 = _percentile(search_latencies, 0.95)
    context_p95 = _percentile(context_latencies, 0.95)
    performance_evaluable = (
        len(search_latencies) >= MINIMUM_PERFORMANCE_SAMPLE_COUNT
        and len(context_latencies) >= MINIMUM_PERFORMANCE_SAMPLE_COUNT
    )
    performance_ready = (
        performance_evaluable
        and search_p95 <= 500.0
        and context_p95 <= 1000.0
    )
    evaluable = usage_evaluable and performance_evaluable
    adoption_ready = evaluable and feedback_count >= 10 and found_rate >= 0.8 and performance_ready
    return {
        "schema_version": 2,
        "status": "pass",
        "measurement_contract": {
            "interaction_contract": INTERACTION_CONTRACT,
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
        "performance": {
            "search_p95_ms": search_p95,
            "context_p95_ms": context_p95,
            "search_target_ms": 500,
            "context_target_ms": 1000,
            "search_sample_count": len(search_latencies),
            "context_sample_count": len(context_latencies),
            "minimum_sample_count_each": MINIMUM_PERFORMANCE_SAMPLE_COUNT,
            "evaluable": performance_evaluable,
            "status": "pass" if performance_ready else ("fail" if performance_evaluable else "pending"),
        },
        "adoption": {
            "evaluable": evaluable,
            "ready": adoption_ready,
            "criteria": {
                "observation_days_or_invocations": "observation_days >= 30 or invocation_count >= 50",
                "sample_kind": "current-contract interactive telemetry only",
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
