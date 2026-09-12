"""P9 local-first W3C trace propagation and bounded SLO telemetry."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import secrets
import statistics
from typing import Any, Dict, Mapping, Optional, Sequence

from .common import KnowledgeHubError, ensure_private_directory, utc_timestamp

TRACE_ROOT = pathlib.Path(".cache/knowledge-hub/observability")
TRACEPARENT_RE = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")
MAX_SPAN_ATTRS = 64
MAX_ATTRIBUTE_CHARS = 1024
SENSITIVE_ATTRIBUTE_NAMES = {"query", "raw_query", "body", "content", "prompt", "task"}


def new_trace_id() -> str:
    return secrets.token_hex(16)


def new_span_id() -> str:
    return secrets.token_hex(8)


def parse_traceparent(value: str) -> Dict[str, str]:
    match = TRACEPARENT_RE.fullmatch(str(value).strip())
    if not match:
        raise KnowledgeHubError("invalid W3C traceparent")
    trace_id, parent_span_id, flags = match.groups()
    if trace_id == "0" * 32 or parent_span_id == "0" * 16:
        raise KnowledgeHubError("traceparent ids must be non-zero")
    return {
        "trace_id": trace_id,
        "parent_span_id": parent_span_id,
        "trace_flags": flags,
    }


def make_traceparent(
    trace_id: str,
    span_id: str,
    *,
    sampled: bool = False,
) -> str:
    if not re.fullmatch(r"[0-9a-f]{32}", trace_id) or trace_id == "0" * 32:
        raise KnowledgeHubError("invalid trace id")
    if not re.fullmatch(r"[0-9a-f]{16}", span_id) or span_id == "0" * 16:
        raise KnowledgeHubError("invalid span id")
    return "00-{}-{}-{}".format(trace_id, span_id, "01" if sampled else "00")


def _safe_attributes(value: Mapping[str, Any]) -> Dict[str, Any]:
    if len(value) > MAX_SPAN_ATTRS:
        raise KnowledgeHubError("span attribute count exceeds budget")
    result: Dict[str, Any] = {}
    for key, raw in value.items():
        name = str(key)
        if name in SENSITIVE_ATTRIBUTE_NAMES:
            if raw:
                result[name + "_sha256"] = hashlib.sha256(
                    str(raw).encode("utf-8")
                ).hexdigest()
            continue
        if isinstance(raw, (bool, int, float)):
            result[name] = raw
            continue
        text = str(raw)
        result[name] = text[:MAX_ATTRIBUTE_CHARS]
    return result


def span_record(
    *,
    name: str,
    trace_id: str,
    span_id: str,
    parent_span_id: str = "",
    status: str = "ok",
    latency_ms: float = 0.0,
    attributes: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    if not name or len(name) > 256:
        raise KnowledgeHubError("span name must be non-empty and bounded")
    if status not in {"ok", "error", "degraded"}:
        raise KnowledgeHubError("invalid span status")
    make_traceparent(trace_id, span_id)
    if parent_span_id and not re.fullmatch(r"[0-9a-f]{16}", parent_span_id):
        raise KnowledgeHubError("invalid parent span id")
    return {
        "schema_version": "knowledge-hub.trace-span.v1",
        "name": name,
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "status": status,
        "latency_ms": round(max(0.0, float(latency_ms)), 3),
        "attributes": _safe_attributes(attributes or {}),
        "recorded_at": utc_timestamp(),
        "raw_query_stored": False,
    }


def append_span(root: pathlib.Path, span: Mapping[str, Any]) -> Dict[str, Any]:
    path = root / TRACE_ROOT / "spans.jsonl"
    ensure_private_directory(path.parent)
    if path.exists() and path.is_symlink():
        raise KnowledgeHubError("trace ledger must not be a symlink")
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(str(path), flags, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(span), ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return {"status": "recorded", "path": str(TRACE_ROOT / "spans.jsonl")}


def propagation_context(
    *,
    traceparent: str = "",
    work_item_id: str = "",
    run_id: str = "",
    handoff_id: str = "",
    receipt_sha256: str = "",
) -> Dict[str, str]:
    parsed = parse_traceparent(traceparent) if traceparent else {
        "trace_id": new_trace_id(),
        "parent_span_id": "",
        "trace_flags": "00",
    }
    span_id = new_span_id()
    return {
        "trace_id": parsed["trace_id"],
        "span_id": span_id,
        "parent_span_id": parsed.get("parent_span_id", ""),
        "traceparent": make_traceparent(parsed["trace_id"], span_id),
        "work_item_id": str(work_item_id)[:256],
        "run_id": str(run_id)[:256],
        "handoff_id": str(handoff_id)[:256],
        "receipt_sha256": str(receipt_sha256)[:64],
    }


def lane_health_projection(retrieval_payload: Mapping[str, Any]) -> Dict[str, Any]:
    lane = retrieval_payload.get("lane_health", {})
    if not isinstance(lane, Mapping):
        raise KnowledgeHubError("retrieval payload missing lane health")
    lexical = int(lane.get("lexical_nonzero", 0) or 0)
    dense = int(lane.get("dense_nonzero", 0) or 0)
    failures = []
    if int(retrieval_payload.get("authorized_item_count", 0) or 0) > 0 and lexical == 0:
        failures.append("lexical-lane-empty")
    if int(retrieval_payload.get("authorized_item_count", 0) or 0) > 0 and dense == 0:
        failures.append("dense-lane-empty")
    return {
        "schema_version": "knowledge-hub.retrieval-lane-health.v1",
        "status": "pass" if not failures else "degraded",
        "failures": failures,
        "lexical_nonzero": lexical,
        "dense_nonzero": dense,
        "chunk_count": int(lane.get("chunk_count", 0) or 0),
        "reranker_enabled": bool(lane.get("reranker_enabled", False)),
        "dense_provider": str(lane.get("dense_provider", "")),
    }


def slo_summary(
    spans: Sequence[Mapping[str, Any]],
    *,
    p95_target_ms: float,
    maximum_error_rate: float,
) -> Dict[str, Any]:
    if isinstance(spans, (str, bytes)) or not isinstance(spans, Sequence):
        raise KnowledgeHubError("spans must be a sequence")
    latencies = [float(row.get("latency_ms", 0.0)) for row in spans]
    ordered = sorted(latencies)
    p95 = ordered[int(round((len(ordered) - 1) * 0.95))] if ordered else 0.0
    errors = sum(str(row.get("status", "")) == "error" for row in spans)
    error_rate = errors / len(spans) if spans else 0.0
    failures = []
    if p95 > p95_target_ms:
        failures.append("p95-latency")
    if error_rate > maximum_error_rate:
        failures.append("error-rate")
    return {
        "schema_version": "knowledge-hub.slo-summary.v1",
        "status": "pass" if not failures else "fail",
        "span_count": len(spans),
        "p50_ms": round(statistics.median(latencies) if latencies else 0.0, 3),
        "p95_ms": round(p95, 3),
        "error_rate": round(error_rate, 6),
        "targets": {
            "p95_ms": p95_target_ms,
            "maximum_error_rate": maximum_error_rate,
        },
        "failures": failures,
    }
