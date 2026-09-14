"""Build privacy-preserving evidence from real production adoption telemetry.

The producer reuses the existing local metrics contract.  It cannot classify local,
fixture, mock, or synthetic data as production on its own: production provenance,
runtime health, and cross-work traceability must be supplied independently.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any, Dict, List, Mapping, Sequence

from .common import KnowledgeHubError
from .external_evidence import INPUT_SCHEMA, validate_external_evidence
from .metrics import local_metrics

PROVENANCE_SCHEMA = "knowledge-hub.production-provenance.v1"
HEALTH_SCHEMA = "knowledge-hub.production-runtime-health.v1"
TRACE_SCHEMA = "knowledge-hub.production-traceability.v1"
PROHIBITED_ORIGIN_FLAGS = (
    "synthetic",
    "mock",
    "fixture",
    "static_adapter",
    "local_only",
)
TELEMETRY_PATHS = (
    ".cache/knowledge-hub/search-telemetry.jsonl",
    ".cache/knowledge-hub/context-telemetry.jsonl",
)
FEEDBACK_PATH = ".cache/knowledge-hub/retrieval-feedback.jsonl"


def _object(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return dict(value)


def _text(value: Any, label: str, *, maximum: int = 2048) -> str:
    result = str(value or "").strip()
    if not result or len(result) > maximum:
        raise KnowledgeHubError("{} must be non-empty and bounded".format(label))
    return result


def _sha256(value: Any, label: str) -> str:
    result = str(value or "").strip().lower()
    if len(result) != 64 or any(character not in "0123456789abcdef" for character in result):
        raise KnowledgeHubError("{} must be lowercase SHA256".format(label))
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


def _load_json(path: pathlib.Path, label: str) -> Dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise KnowledgeHubError("{} is unavailable".format(label))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("{} is invalid JSON".format(label)) from exc
    return _object(value, label)


def _hash_files(root: pathlib.Path, relative_paths: Sequence[str], label: str) -> str:
    digest = hashlib.sha256()
    for relative in relative_paths:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise KnowledgeHubError("{} source is unavailable: {}".format(label, relative))
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _validate_provenance(value: Mapping[str, Any]) -> Dict[str, Any]:
    row = _object(value, "production provenance")
    if row.get("schema_version") != PROVENANCE_SCHEMA:
        raise KnowledgeHubError("production provenance schema_version is unsupported")
    if row.get("classification") != "real-production":
        raise KnowledgeHubError("production provenance classification must be real-production")
    for key in PROHIBITED_ORIGIN_FLAGS:
        if row.get(key) is not False:
            raise KnowledgeHubError("production provenance {} must be explicitly false".format(key))
    _sha256(row.get("environment_id_sha256"), "production environment id")
    _text(row.get("runtime_version"), "production runtime version", maximum=256)
    _text(row.get("window_start"), "production window_start", maximum=128)
    _text(row.get("window_end"), "production window_end", maximum=128)
    refs = row.get("evidence_source_refs")
    if isinstance(refs, (str, bytes)) or not isinstance(refs, Sequence) or not refs or len(refs) > 32:
        raise KnowledgeHubError("production evidence_source_refs must be non-empty and bounded")
    row["evidence_source_refs"] = [
        _text(item, "production evidence source ref") for item in refs
    ]
    export_mode = _text(row.get("network_export_mode"), "network export mode", maximum=64)
    if export_mode not in {"disabled", "explicitly-configured"}:
        raise KnowledgeHubError("network export mode must be disabled or explicitly-configured")
    return row


def _validate_health(value: Mapping[str, Any]) -> Dict[str, Any]:
    row = _object(value, "production runtime health")
    if row.get("schema_version") != HEALTH_SCHEMA or row.get("status") != "pass":
        raise KnowledgeHubError("production runtime health must use the supported passing contract")
    p50_ms = _number(row.get("p50_ms"), "production p50", minimum=0.0)
    error_rate = _number(row.get("error_rate"), "production error rate", minimum=0.0)
    if error_rate > 1.0:
        raise KnowledgeHubError("production error rate must be in [0,1]")
    if row.get("retrieval_lane_health") != "pass":
        raise KnowledgeHubError("production retrieval lane health must pass")
    row["p50_ms"] = p50_ms
    row["error_rate"] = error_rate
    return row


def _validate_trace(value: Mapping[str, Any]) -> Dict[str, Any]:
    row = _object(value, "production traceability")
    if row.get("schema_version") != TRACE_SCHEMA or row.get("status") != "pass":
        raise KnowledgeHubError("production traceability must use the supported passing contract")
    if row.get("work_item_run_handoff_receipt_linked") is not True:
        raise KnowledgeHubError("production traceability must link work-item, run, handoff and receipt")
    for key in ("work_item_id_sha256", "run_id_sha256", "handoff_id_sha256", "receipt_id_sha256"):
        _sha256(row.get(key), "production traceability {}".format(key))
    return row


def build_real_adoption_evidence(
    *,
    metrics: Mapping[str, Any],
    provenance: Mapping[str, Any],
    health: Mapping[str, Any],
    traceability: Mapping[str, Any],
    source_revision: str,
    call_ledger_sha256: str,
    feedback_sha256: str,
) -> Dict[str, Any]:
    provenance_row = _validate_provenance(provenance)
    health_row = _validate_health(health)
    trace_row = _validate_trace(traceability)
    adoption = _object(metrics.get("adoption"), "local metrics adoption")
    if adoption.get("ready") is not True:
        raise KnowledgeHubError("local metrics adoption is not ready")
    usage = _object(metrics.get("usage"), "local metrics usage")
    retrieval = _object(metrics.get("retrieval"), "local metrics retrieval")
    performance = _object(metrics.get("performance"), "local metrics performance")
    warm = _object(performance.get("warm_interactive"), "warm interactive performance")
    observation_days = _integer(usage.get("observation_days"), "observation days")
    valid_calls = _integer(usage.get("invocation_count"), "valid real calls")
    feedback_count = _integer(retrieval.get("feedback_count"), "explicit feedback count")
    search_p95 = _number(warm.get("search_p95_ms"), "search p95")
    context_p95 = _number(warm.get("context_p95_ms"), "context p95")
    p95_ms = max(search_p95, context_p95)
    if health_row["p50_ms"] > p95_ms:
        raise KnowledgeHubError("production p50 cannot exceed telemetry-derived p95")
    payload = {
        "schema_version": INPUT_SCHEMA,
        "gap_id": "real-adoption-evidence",
        "source_revision": _text(source_revision, "source revision", maximum=40).lower(),
        "observed_at": provenance_row["window_end"],
        "evidence_source_refs": list(provenance_row["evidence_source_refs"]),
        "origin": {
            "classification": "real-production",
            "environment_id_sha256": provenance_row["environment_id_sha256"],
            "synthetic": False,
            "mock": False,
            "fixture": False,
            "static_adapter": False,
            "local_only": False,
        },
        "adoption": {
            "runtime_version": provenance_row["runtime_version"],
            "window_start": provenance_row["window_start"],
            "window_end": provenance_row["window_end"],
            "observation_days": observation_days,
            "valid_real_calls": valid_calls,
            "synthetic_calls": 0,
            "explicit_feedback_count": feedback_count,
            "call_ledger_sha256": _sha256(call_ledger_sha256, "call ledger"),
            "feedback_sha256": _sha256(feedback_sha256, "feedback ledger"),
            "slo": {
                "status": "pass",
                "p50_ms": health_row["p50_ms"],
                "p95_ms": p95_ms,
                "error_rate": health_row["error_rate"],
                "retrieval_lane_health": "pass",
            },
            "traceability": {
                "status": "pass",
                "work_item_run_handoff_receipt_linked": trace_row[
                    "work_item_run_handoff_receipt_linked"
                ],
            },
            "privacy": {
                "raw_query_stored": False,
                "raw_task_stored": False,
                "raw_prompt_stored": False,
                "raw_content_stored": False,
                "network_export_mode": provenance_row["network_export_mode"],
            },
        },
    }
    validate_external_evidence(payload, expected_gap="real-adoption-evidence")
    return payload


def export_real_adoption_evidence(
    *,
    root: pathlib.Path,
    provenance_path: pathlib.Path,
    health_path: pathlib.Path,
    traceability_path: pathlib.Path,
    source_revision: str,
) -> Dict[str, Any]:
    root = pathlib.Path(root)
    metrics = local_metrics(root)
    call_ledger_sha = _hash_files(root, TELEMETRY_PATHS, "call ledger")
    feedback_sha = _hash_files(root, (FEEDBACK_PATH,), "feedback ledger")
    return build_real_adoption_evidence(
        metrics=metrics,
        provenance=_load_json(provenance_path, "production provenance"),
        health=_load_json(health_path, "production runtime health"),
        traceability=_load_json(traceability_path, "production traceability"),
        source_revision=source_revision,
        call_ledger_sha256=call_ledger_sha,
        feedback_sha256=feedback_sha,
    )
