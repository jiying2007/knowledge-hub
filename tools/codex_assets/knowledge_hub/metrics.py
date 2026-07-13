"""Privacy-preserving local usage, performance and feedback metrics."""

from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import os
import pathlib
from typing import Any, Dict, List, Mapping, Sequence

from .common import compact_json, load_jsonl, utc_timestamp


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


def record_feedback(
    root: pathlib.Path,
    query: str,
    outcome: str,
    selected_id: str = "",
    task_type: str = "general",
) -> Dict[str, Any]:
    if outcome not in {"found", "not-found"}:
        raise ValueError("outcome must be found or not-found")
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    row = {
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
    search_rows = [
        row
        for row in all_search_rows
        if row.get("schema_version") == 2 and row.get("sample_kind") == "interactive"
    ]
    context_rows = [
        row
        for row in all_context_rows
        if row.get("schema_version") == 2 and row.get("sample_kind") == "interactive"
    ]
    feedback_rows = load_jsonl(root / ".cache/knowledge-hub/retrieval-feedback.jsonl")
    all_rows = search_rows + context_rows
    dates = sorted(value for value in (_date(row.get("recorded_at")) for row in all_rows) if value != dt.date.min)
    observation_days = (dates[-1] - dates[0]).days + 1 if dates else 0
    invocation_count = len(all_rows)
    evaluable = observation_days >= 30 or invocation_count >= 50
    found_count = sum(1 for row in feedback_rows if row.get("outcome") == "found")
    not_found_count = sum(1 for row in feedback_rows if row.get("outcome") == "not-found")
    feedback_count = found_count + not_found_count
    found_rate = round(found_count / float(feedback_count), 4) if feedback_count else 0.0
    search_latencies = [float(row.get("latency_ms", 0) or 0) for row in search_rows]
    context_latencies = [float(row.get("latency_ms", 0) or 0) for row in context_rows]
    zero_hits = sum(1 for row in search_rows if int(row.get("result_count", 0) or 0) == 0)
    search_p95 = _percentile(search_latencies, 0.95)
    context_p95 = _percentile(context_latencies, 0.95)
    performance_ready = (not search_latencies or search_p95 <= 500.0) and (not context_latencies or context_p95 <= 1000.0)
    adoption_ready = evaluable and feedback_count >= 10 and found_rate >= 0.8 and performance_ready
    return {
        "schema_version": 1,
        "status": "pass",
        "privacy": {"raw_query_stored": False, "query_hash_only": True},
        "usage": {
            "invocation_count": invocation_count,
            "search_count": len(search_rows),
            "context_count": len(context_rows),
            "excluded_legacy_or_noninteractive_count": (
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
        },
        "performance": {
            "search_p95_ms": search_p95,
            "context_p95_ms": context_p95,
            "search_target_ms": 500,
            "context_target_ms": 1000,
            "status": "pass" if performance_ready else "fail",
        },
        "adoption": {
            "evaluable": evaluable,
            "ready": adoption_ready,
            "criteria": {
                "observation_days_or_invocations": "observation_days >= 30 or invocation_count >= 50",
                "sample_kind": "interactive schema v2 only",
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
