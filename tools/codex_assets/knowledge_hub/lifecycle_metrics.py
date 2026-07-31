"""Report-only lifecycle operating metrics for governed knowledge."""

from __future__ import annotations

import datetime as dt
import pathlib
from collections import Counter
from typing import Any, Dict, List, Mapping, Sequence

from .common import load_jsonl


AGE_BUCKETS = ("0-7", "8-30", "31-90", ">90")


def _parse_date(value: Any) -> dt.date | None:
    text = str(value or "")
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return dt.date.fromisoformat(text)
        except ValueError:
            return None


def _age_bucket(age_days: int) -> str:
    if age_days <= 7:
        return "0-7"
    if age_days <= 30:
        return "8-30"
    if age_days <= 90:
        return "31-90"
    return ">90"


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * fraction))
    return round(float(ordered[max(0, min(index, len(ordered) - 1))]), 2)


def _recent_result_ids(root: pathlib.Path, cutoff: dt.date) -> set[str]:
    result_ids: set[str] = set()
    for path in (
        root / ".cache/knowledge-hub/search-telemetry.jsonl",
        root / ".cache/knowledge-hub/context-telemetry.jsonl",
    ):
        for row in load_jsonl(path):
            recorded = _parse_date(row.get("recorded_at"))
            if recorded is None or recorded < cutoff:
                continue
            values = row.get("result_ids", [])
            if isinstance(values, list):
                result_ids.update(str(value) for value in values if str(value))
    return result_ids


def _lead_times(events: Sequence[Mapping[str, Any]]) -> List[float]:
    captures: Dict[str, dt.date] = {}
    decisions: List[float] = []
    ordered = sorted(events, key=lambda row: str(row.get("executed_at", "")))
    for row in ordered:
        item_id = str(row.get("item_id", ""))
        executed = _parse_date(row.get("executed_at"))
        if not item_id or executed is None:
            continue
        if row.get("after_status") == "reviewing" and item_id not in captures:
            captures[item_id] = executed
        if (
            row.get("before_status") == "reviewing"
            and row.get("after_status") != "reviewing"
            and item_id in captures
        ):
            decisions.append(float(max(0, (executed - captures[item_id]).days)))
            captures.pop(item_id, None)
    return decisions


def _reviewing_snapshot(
    reviewing: Sequence[Mapping[str, Any]],
    as_of: dt.date,
) -> tuple[Counter[str], List[str]]:
    age_counts: Counter[str] = Counter()
    invalid_created_ids = []
    for row in reviewing:
        created = _parse_date(row.get("created_at"))
        if created is None:
            invalid_created_ids.append(str(row.get("id", "")))
            continue
        age_counts[_age_bucket(max(0, (as_of - created).days))] += 1
    return age_counts, invalid_created_ids


def _flow_snapshot(
    events: Sequence[Mapping[str, Any]],
    *,
    window_start: dt.date,
    as_of: dt.date,
) -> Counter[str]:
    flow_counts: Counter[str] = Counter()
    for row in events:
        executed = _parse_date(row.get("executed_at"))
        if executed is None or not window_start <= executed <= as_of:
            continue
        after = str(row.get("after_status", ""))
        before = str(row.get("before_status", ""))
        if after == "reviewing" and before != "reviewing":
            flow_counts["to_reviewing_count"] += 1
        if after in {"active", "archived", "rejected", "superseded"}:
            flow_counts["to_{}_count".format(after)] += 1
    return flow_counts


def lifecycle_operating_metrics(
    root: pathlib.Path,
    as_of: dt.date,
    *,
    window_days: int = 30,
    cold_days: int = 90,
    sample_limit: int = 20,
) -> Dict[str, Any]:
    """Measure lifecycle debt without performing transitions or deletions."""

    items = load_jsonl(root / "registry/items.jsonl")
    events = load_jsonl(root / "registry/lifecycle-events.jsonl")
    reviewing = [row for row in items if row.get("status") == "reviewing"]
    age_counts, invalid_created_ids = _reviewing_snapshot(reviewing, as_of)
    window_start = as_of - dt.timedelta(days=max(0, window_days - 1))
    flow_counts = _flow_snapshot(events, window_start=window_start, as_of=as_of)
    lead_times = _lead_times(events)
    recent_ids = _recent_result_ids(
        root,
        as_of - dt.timedelta(days=max(0, cold_days - 1)),
    )
    cold_ids = sorted(
        str(row.get("id", ""))
        for row in reviewing
        if row.get("id") and str(row.get("id")) not in recent_ids
    )
    by_owner = Counter(str(row.get("owner", "") or "<missing>") for row in reviewing)
    by_domain = Counter(str(row.get("domain", "") or "<missing>") for row in reviewing)
    return {
        "schema_version": 1,
        "status": "pass" if not invalid_created_ids else "attention",
        "read_only": True,
        "report_only": True,
        "as_of": as_of.isoformat(),
        "reviewing_count": len(reviewing),
        "reviewing_age_buckets": {
            bucket: age_counts.get(bucket, 0) for bucket in AGE_BUCKETS
        },
        "invalid_created_at_count": len(invalid_created_ids),
        "invalid_created_at_sample": invalid_created_ids[:sample_limit],
        "flow": {
            "window_days": window_days,
            "window_start": window_start.isoformat(),
            "to_reviewing_count": flow_counts.get("to_reviewing_count", 0),
            "to_active_count": flow_counts.get("to_active_count", 0),
            "to_archived_count": flow_counts.get("to_archived_count", 0),
            "to_rejected_count": flow_counts.get("to_rejected_count", 0),
            "to_superseded_count": flow_counts.get("to_superseded_count", 0),
        },
        "decision_lead_time_days": {
            "sample_count": len(lead_times),
            "p50": _percentile(lead_times, 0.50),
            "p95": _percentile(lead_times, 0.95),
        },
        "cold_candidates": {
            "window_days": cold_days,
            "count": len(cold_ids),
            "sample": cold_ids[:sample_limit],
            "recommendation": "human-review-or-archive",
            "automatic_delete": False,
        },
        "by_owner": dict(sorted(by_owner.items())),
        "by_domain": dict(sorted(by_domain.items())),
        "must_not": [
            "不自动提升 active",
            "不自动归档或删除",
            "不代签 owner decision",
        ],
    }
