"""Read-only, metadata-only inspection for rawmem-compatible evidence ledgers."""

from __future__ import annotations

import hashlib
import json
import pathlib
from collections import Counter
from typing import Any, Dict, List, Mapping

from .common import KnowledgeHubError, compact_json, display_path
from .security import scan_secret_text


RAW_EVIDENCE_SCHEMA = "knowledge-hub.raw-evidence-inspection.v1"
RAWMEM_EVENT_SCHEMA = "rawmem.event.v1"
RAW_EVIDENCE_DEFAULT_MAX_BYTES = 64 * 1024 * 1024
RAW_EVIDENCE_MAX_MAX_BYTES = 1024 * 1024 * 1024
RAW_EVIDENCE_DEFAULT_MAX_EVENTS = 100000
RAW_EVIDENCE_MAX_MAX_EVENTS = 1000000
RAW_EVIDENCE_DEFAULT_MAX_LINE_BYTES = 1024 * 1024
RAW_EVIDENCE_MAX_MAX_LINE_BYTES = 16 * 1024 * 1024


def _canonical_event_hash(event: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in event.items() if key != "content_hash"}
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_hash(value: Any) -> str:
    text = str(value or "")
    if len(text) == 64 and all(character in "0123456789abcdef" for character in text):
        return text
    return ""


def _bounded_counts(counter: Counter, limit: int = 20) -> Dict[str, Any]:
    rows = sorted(counter.items(), key=lambda row: (-row[1], str(row[0])))
    return {
        "values": [{"value": str(value), "count": count} for value, count in rows[:limit]],
        "total_values": len(rows),
        "truncated": len(rows) > limit,
    }


def inspect_raw_evidence_ledger(
    ledger_path: pathlib.Path,
    *,
    max_errors: int = 20,
    max_bytes: int = RAW_EVIDENCE_DEFAULT_MAX_BYTES,
    max_events: int = RAW_EVIDENCE_DEFAULT_MAX_EVENTS,
    max_line_bytes: int = RAW_EVIDENCE_DEFAULT_MAX_LINE_BYTES,
) -> Dict[str, Any]:
    path = ledger_path.expanduser().resolve()
    if max_errors < 1 or max_errors > 100:
        raise KnowledgeHubError("--max-errors must be between 1 and 100")
    if not 1 <= max_bytes <= RAW_EVIDENCE_MAX_MAX_BYTES:
        raise KnowledgeHubError(
            "--max-bytes must be between 1 and {}".format(
                RAW_EVIDENCE_MAX_MAX_BYTES
            )
        )
    if not 1 <= max_events <= RAW_EVIDENCE_MAX_MAX_EVENTS:
        raise KnowledgeHubError(
            "--max-events must be between 1 and {}".format(
                RAW_EVIDENCE_MAX_MAX_EVENTS
            )
        )
    if not 1 <= max_line_bytes <= RAW_EVIDENCE_MAX_MAX_LINE_BYTES:
        raise KnowledgeHubError(
            "--max-line-bytes must be between 1 and {}".format(
                RAW_EVIDENCE_MAX_MAX_LINE_BYTES
            )
        )
    if not path.is_file():
        raise KnowledgeHubError("raw evidence ledger does not exist: {}".format(display_path(path)))
    before = path.stat()
    if before.st_size > max_bytes:
        raise KnowledgeHubError(
            "raw evidence ledger exceeds {} bytes".format(max_bytes)
        )
    snapshot_digest = hashlib.sha256()
    previous_hash = None
    first_hash = ""
    last_hash = ""
    event_ids = set()
    event_count = 0
    nonempty_line_count = 0
    errors: List[Dict[str, Any]] = []
    error_count_total = 0
    sources: Counter = Counter()
    event_types: Counter = Counter()
    scopes: Counter = Counter()
    secret_rules: Counter = Counter()
    raw_text_present = 0
    summary_present = 0
    payload_present = 0
    cwd_present = 0
    artifact_reference_count = 0
    review_not_required_count = 0
    redaction_count = 0
    capture_policy_event_count = 0

    def add_error(code: str, line: int, message: str) -> None:
        nonlocal error_count_total
        error_count_total += 1
        if len(errors) < max_errors:
            errors.append({"code": code, "line": line, "message": message})

    bytes_read = 0
    with path.open("rb") as handle:
        line_no = 0
        while True:
            remaining_bytes = max_bytes - bytes_read
            read_limit = min(max_line_bytes + 1, remaining_bytes + 1)
            raw = handle.readline(read_limit)
            if not raw:
                break
            line_no += 1
            bytes_read += len(raw)
            snapshot_digest.update(raw)
            if bytes_read > max_bytes:
                add_error(
                    "byte_limit_exceeded",
                    line_no,
                    "ledger grew beyond the configured byte budget",
                )
                break
            if len(raw) > max_line_bytes:
                add_error(
                    "line_too_large",
                    line_no,
                    "line exceeds configured byte budget",
                )
                break
            if not raw.strip():
                continue
            nonempty_line_count += 1
            if nonempty_line_count > max_events:
                add_error(
                    "event_limit_exceeded",
                    line_no,
                    "event count exceeds configured budget",
                )
                break
            for finding in scan_secret_text(raw.decode("utf-8", errors="ignore")):
                secret_rules[str(finding.get("rule", "unknown"))] += 1
            try:
                event = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                add_error("invalid_json", line_no, "line is not a UTF-8 JSON object")
                continue
            if not isinstance(event, dict):
                add_error("invalid_event_object", line_no, "event must be a JSON object")
                continue
            event_count += 1
            if event.get("schema") != RAWMEM_EVENT_SCHEMA:
                add_error("invalid_event_schema", line_no, "event schema must be rawmem.event.v1")
            event_id = str(event.get("event_id", ""))
            if not event_id:
                add_error("missing_event_id", line_no, "event_id is required")
            elif event_id in event_ids:
                add_error("duplicate_event_id", line_no, "event_id must be unique")
            else:
                event_ids.add(event_id)
            stored_hash = _safe_hash(event.get("content_hash"))
            if not stored_hash:
                add_error("invalid_content_hash", line_no, "content_hash must be lowercase SHA-256")
            else:
                calculated = _canonical_event_hash(event)
                if calculated != stored_hash:
                    add_error("content_hash_mismatch", line_no, "canonical event hash does not match content_hash")
            actual_previous = event.get("previous_hash")
            if actual_previous != previous_hash:
                add_error("previous_hash_mismatch", line_no, "previous_hash does not match preceding content_hash")
            if event_count == 1:
                first_hash = stored_hash
            last_hash = stored_hash
            previous_hash = stored_hash or event.get("content_hash")

            sources[str(event.get("source", "unknown"))] += 1
            event_types[str(event.get("event_type", "unknown"))] += 1
            privacy = event.get("privacy") if isinstance(event.get("privacy"), dict) else {}
            scopes[str(privacy.get("scope", "unspecified"))] += 1
            if privacy.get("review_required") is False:
                review_not_required_count += 1
            raw_text_present += int(bool(event.get("raw_text")))
            summary_present += int(bool(event.get("summary")))
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            payload_present += int(bool(payload))
            cwd_present += int(bool(event.get("cwd")))
            artifacts = event.get("artifacts") if isinstance(event.get("artifacts"), list) else []
            artifact_reference_count += len(artifacts)
            redaction = payload.get("redaction") if isinstance(payload.get("redaction"), dict) else {}
            count = redaction.get("count", 0)
            if isinstance(count, int) and count > 0:
                redaction_count += count
            capture_policy_event_count += int(isinstance(payload.get("capture_policy"), dict))

    after = path.stat()
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        add_error("ledger_changed_during_verification", 0, "ledger size or mtime changed during verification")
    snapshot_sha256 = snapshot_digest.hexdigest()
    valid = not errors and event_count == nonempty_line_count
    nonlocal_scopes = [scope for scope in scopes if scope != "local_only"]
    privacy_status = "needs-review" if secret_rules or nonlocal_scopes else "observed"
    reference_id = "raw-evidence-{}".format(snapshot_sha256[:16])
    return {
        "schema_version": RAW_EVIDENCE_SCHEMA,
        "read_only": True,
        "projection": "metadata-only",
        "source_format": RAWMEM_EVENT_SCHEMA,
        "limits": {
            "max_bytes": max_bytes,
            "max_events": max_events,
            "max_line_bytes": max_line_bytes,
        },
        "status": "pass" if valid else "fail",
        "chain_status": "verified" if valid else "failed",
        "ledger": {
            "path": display_path(path),
            "size_bytes": after.st_size,
            "snapshot_sha256": snapshot_sha256,
            "event_count": event_count,
            "first_content_hash": first_hash,
            "last_content_hash": last_hash,
        },
        "vocabulary": {
            "sources": _bounded_counts(sources),
            "event_types": _bounded_counts(event_types),
            "privacy_scopes": _bounded_counts(scopes),
        },
        "privacy": {
            "status": privacy_status,
            "raw_text_present_count": raw_text_present,
            "summary_present_count": summary_present,
            "payload_present_count": payload_present,
            "cwd_present_count": cwd_present,
            "artifact_reference_count": artifact_reference_count,
            "review_not_required_count": review_not_required_count,
            "declared_redaction_count": redaction_count,
            "capture_policy_event_count": capture_policy_event_count,
            "suspected_secret_finding_count": sum(secret_rules.values()),
            "suspected_secret_rules": _bounded_counts(secret_rules),
            "content_echoed": False,
        },
        "errors": errors,
        "error_count": error_count_total,
        "errors_truncated": error_count_total > len(errors),
        "hub_route": {
            "route": "reference-only",
            "eligible_for_text_ingest": False,
            "eligible_for_active_promotion": False,
            "review_required": True,
            "candidate": {
                "id": reference_id,
                "kind": "artifact-ref",
                "status": "reviewing",
                "source": {
                    "type": "raw-evidence-ledger",
                    "uri": display_path(path),
                    "sha256": snapshot_sha256,
                    "size_bytes": after.st_size,
                },
            },
        },
        "authority_contract": {
            "chain_integrity_is_content_truth": False,
            "ledger_is_long_term_knowledge": False,
            "raw_body_may_enter_hub_text": False,
            "verification_has_side_effects": False,
            "input_budgets_enforced": True,
        },
    }
