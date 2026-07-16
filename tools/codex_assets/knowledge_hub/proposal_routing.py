"""Default-disabled, report-only proposal routing inspired by reviewed-memory gates."""

from __future__ import annotations

from collections import Counter
import fcntl
import hashlib
import json
import os
import pathlib
import re
import stat
from typing import Any, Dict, Mapping

from .common import (
    KnowledgeHubError,
    compact_json,
    normalize_relpath,
    read_bytes_bounded,
    read_utf8_bounded,
    resolve_inside,
    utc_timestamp,
)
from .model import ITEM_KINDS


PROPOSAL_ROUTE_SCHEMA = "knowledge-hub.proposal-route.v1"
PROPOSAL_SHADOW_AUDIT_SCHEMA = "knowledge-hub.proposal-shadow-audit.v1"
PROPOSAL_SHADOW_STATS_SCHEMA = "knowledge-hub.proposal-shadow-stats.v1"
PROPOSAL_MAX_BYTES = 128 * 1024
PROPOSAL_MAX_CLIENT_ID_CHARS = 256
PROPOSAL_MAX_QUOTE_CHARS = 4096
PROPOSAL_MAX_EVIDENCE_SOURCE_BYTES = 8 * 1024 * 1024
PROPOSAL_MAX_POLICY_BYTES = 64 * 1024
PROPOSAL_MAX_POLICY_VALUES = 64
PROPOSAL_SHADOW_MAX_BYTES = 64 * 1024 * 1024
PROPOSAL_SHADOW_MAX_LINE_BYTES = 16 * 1024
PROPOSAL_SHADOW_MAX_ROWS = 100000
PROPOSAL_SHADOW_ROUTES = {
    "human-review",
    "human-sampled",
    "auto-stage-reviewing",
}
PROPOSAL_SHADOW_REASON_CODES = {
    "policy_disabled",
    "client_not_trusted_by_host_policy",
    "high_risk_kind_human_only",
    "kind_not_opted_in",
    "runtime_role_not_low_risk_assertion",
    "type_capability_not_opted_in",
    "target_status_not_candidate",
    "promotion_field_forbidden",
    "owner_or_human_review_field_forbidden",
    "evidence_not_exactly_verified",
    "daily_limit_disabled_or_exhausted",
    "write_auto_not_granted_shadow_only",
}
PROPOSAL_SHADOW_SAMPLE_FIELDS = {
    "bucket",
    "human_sample_percent",
    "sampled",
}
PROPOSAL_SHADOW_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)
PROPOSAL_POLICY_REQUIRED_FIELDS = {
    "schema_version",
    "mode",
    "enabled",
    "trusted_clients",
    "eligible_kinds",
    "eligible_runtime_roles",
    "daily_limit",
    "human_sample_percent",
    "sample_seed",
    "evidence_verifier",
    "target_status",
}
PROPOSAL_POLICY_ALLOWED_FIELDS = PROPOSAL_POLICY_REQUIRED_FIELDS | {"notes_zh"}
PROPOSAL_SHADOW_ALLOWED_FIELDS = {
    "schema_version",
    "sequence",
    "recorded_at",
    "proposal_hash",
    "client_fingerprint",
    "actual_route",
    "eligible_route",
    "reason_codes",
    "sample",
    "previous_hash",
    "event_hash",
}
HIGH_RISK_KINDS = {
    "standard",
    "decision",
    "runbook",
    "authorization",
    "owner-decision-worksheet",
    "patent",
    "patent-disclosure",
}


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _proposal_hash(proposal: Mapping[str, Any]) -> str:
    return _hash(compact_json(proposal))


def _is_lower_hex(value: Any, length: int) -> bool:
    text = str(value or "")
    return len(text) == length and all(character in "0123456789abcdef" for character in text)


def _path_without_symlink_components(
    root: pathlib.Path,
    relative: str,
) -> pathlib.Path:
    normalized = normalize_relpath(relative)
    cursor = root
    for part in pathlib.PurePosixPath(normalized).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise KnowledgeHubError("proposal shadow audit path must not contain symlinks")
    return cursor


def _shadow_row_semantic_errors(row: Mapping[str, Any]) -> list:
    errors = []
    if set(row) != PROPOSAL_SHADOW_ALLOWED_FIELDS:
        errors.append("invalid_fields")
    if row.get("schema_version") != PROPOSAL_SHADOW_AUDIT_SCHEMA:
        errors.append("invalid_schema")
    sequence = row.get("sequence")
    if type(sequence) is not int or not 1 <= sequence <= PROPOSAL_SHADOW_MAX_ROWS:
        errors.append("invalid_sequence")
    recorded_at = row.get("recorded_at")
    if not isinstance(recorded_at, str) or not PROPOSAL_SHADOW_TIMESTAMP.fullmatch(recorded_at):
        errors.append("invalid_recorded_at")
    if not _is_lower_hex(row.get("proposal_hash"), 64):
        errors.append("invalid_proposal_hash")
    if not _is_lower_hex(row.get("client_fingerprint"), 16):
        errors.append("invalid_client_fingerprint")
    if row.get("actual_route") != "human-review":
        errors.append("invalid_actual_route")
    if row.get("eligible_route") not in PROPOSAL_SHADOW_ROUTES:
        errors.append("invalid_eligible_route")
    reasons = row.get("reason_codes")
    if (
        not isinstance(reasons, list)
        or len(reasons) > 32
        or any(not isinstance(reason, str) for reason in reasons)
        or len(set(reasons)) != len(reasons)
        or any(reason not in PROPOSAL_SHADOW_REASON_CODES for reason in reasons)
    ):
        errors.append("invalid_reason_codes")
    sample = row.get("sample")
    if not isinstance(sample, Mapping) or set(sample) != PROPOSAL_SHADOW_SAMPLE_FIELDS:
        errors.append("invalid_sample")
    else:
        bucket = sample.get("bucket")
        sample_percent = sample.get("human_sample_percent")
        sampled = sample.get("sampled")
        if type(bucket) is not int or not 0 <= bucket <= 99:
            errors.append("invalid_sample_bucket")
        if type(sample_percent) is not int or not 0 <= sample_percent <= 100:
            errors.append("invalid_sample_percent")
        if not isinstance(sampled, bool):
            errors.append("invalid_sampled_flag")
    previous_hash = row.get("previous_hash")
    if previous_hash != "" and not _is_lower_hex(previous_hash, 64):
        errors.append("invalid_previous_hash")
    if not _is_lower_hex(row.get("event_hash"), 64):
        errors.append("invalid_event_hash")
    return errors


def _shadow_audit_projection(payload: Mapping[str, Any]) -> Dict[str, Any]:
    reasons = payload.get("reason_codes")
    sample = payload.get("sample")
    row: Dict[str, Any] = {
        "schema_version": PROPOSAL_SHADOW_AUDIT_SCHEMA,
        "sequence": 1,
        "recorded_at": utc_timestamp(),
        "proposal_hash": payload.get("proposal_hash", ""),
        "client_fingerprint": payload.get("client_fingerprint", ""),
        "actual_route": payload.get("actual_route", ""),
        "eligible_route": payload.get("eligible_route", ""),
        "reason_codes": list(reasons) if isinstance(reasons, list) else [],
        "sample": dict(sample) if isinstance(sample, Mapping) else {},
        "previous_hash": "",
        "event_hash": "0" * 64,
    }
    if _shadow_row_semantic_errors(row):
        raise KnowledgeHubError("proposal shadow assessment metadata is invalid")
    return row


def _policy_string_list(policy: Mapping[str, Any], field: str) -> list:
    value = policy.get(field, [])
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise KnowledgeHubError("Agent review policy {} must be a string list".format(field))
    if len(value) > PROPOSAL_MAX_POLICY_VALUES:
        raise KnowledgeHubError(
            "Agent review policy {} exceeds {} values".format(
                field, PROPOSAL_MAX_POLICY_VALUES
            )
        )
    if any(len(item) > 256 for item in value):
        raise KnowledgeHubError(
            "Agent review policy {} value exceeds 256 characters".format(field)
        )
    if len(set(value)) != len(value):
        raise KnowledgeHubError(
            "Agent review policy {} must not contain duplicates".format(field)
        )
    return value


def _load_policy(root: pathlib.Path, policy_path: str) -> Mapping[str, Any]:
    path = resolve_inside(root, policy_path)
    text = read_utf8_bounded(
        path,
        PROPOSAL_MAX_POLICY_BYTES,
        "Agent review policy",
    )
    try:
        policy = json.loads(text)
    except json.JSONDecodeError as exc:
        raise KnowledgeHubError("invalid or unsafe Agent review policy") from exc
    if not isinstance(policy, Mapping):
        raise KnowledgeHubError("invalid or unsafe Agent review policy")
    return policy


def _validate_policy(policy: Mapping[str, Any]) -> Dict[str, Any]:
    missing_fields = PROPOSAL_POLICY_REQUIRED_FIELDS - set(policy)
    unknown_fields = set(policy) - PROPOSAL_POLICY_ALLOWED_FIELDS
    if missing_fields or unknown_fields:
        raise KnowledgeHubError("invalid or unsafe Agent review policy fields")
    if policy.get("schema_version") != 1 or policy.get("mode") != "shadow":
        raise KnowledgeHubError("invalid or unsafe Agent review policy")
    if not isinstance(policy.get("enabled"), bool):
        raise KnowledgeHubError("Agent review policy enabled must be boolean")
    trusted_clients = _policy_string_list(policy, "trusted_clients")
    eligible_kinds = _policy_string_list(policy, "eligible_kinds")
    eligible_roles = _policy_string_list(policy, "eligible_runtime_roles")
    unknown_kinds = sorted(set(eligible_kinds) - ITEM_KINDS)
    if unknown_kinds:
        raise KnowledgeHubError(
            "Agent review policy has invalid eligible_kinds: {}".format(
                ", ".join(unknown_kinds)
            )
        )
    if any(role != "assertion" for role in eligible_roles):
        raise KnowledgeHubError(
            "Agent review policy eligible_runtime_roles must contain only assertion"
        )
    daily_limit = policy.get("daily_limit")
    sample_percent = policy.get("human_sample_percent")
    if type(daily_limit) is not int or type(sample_percent) is not int:
        raise KnowledgeHubError("Agent review policy limits must be integers")
    if daily_limit < 0 or daily_limit > 10000:
        raise KnowledgeHubError("Agent review policy daily_limit must be between 0 and 10000")
    if sample_percent < 0 or sample_percent > 100:
        raise KnowledgeHubError(
            "Agent review policy human_sample_percent must be between 0 and 100"
        )
    if policy.get("evidence_verifier") != "hub-file-exact-quote":
        raise KnowledgeHubError("Agent review policy evidence_verifier is not supported")
    if policy.get("target_status") != "reviewing":
        raise KnowledgeHubError("Agent review policy target_status must be reviewing")
    sample_seed = policy.get("sample_seed", "")
    if not isinstance(sample_seed, str) or not sample_seed or len(sample_seed) > 200:
        raise KnowledgeHubError("Agent review policy sample_seed must be 1..200 characters")
    notes = policy.get("notes_zh")
    if notes is not None and (not isinstance(notes, str) or len(notes) > 4096):
        raise KnowledgeHubError("Agent review policy notes_zh must be at most 4096 characters")
    return {
        "trusted_clients": trusted_clients,
        "eligible_kinds": eligible_kinds,
        "eligible_runtime_roles": eligible_roles,
        "daily_limit": daily_limit,
        "human_sample_percent": sample_percent,
    }


def _verify_exact_quote(root: pathlib.Path, proposal: Mapping[str, Any]) -> Dict[str, Any]:
    evidence = proposal.get("evidence")
    if not isinstance(evidence, Mapping):
        return {"status": "unverified", "reason": "missing_evidence"}
    source_path = evidence.get("source_path")
    quote = evidence.get("quote")
    if not isinstance(source_path, str) or not source_path:
        return {"status": "unverified", "reason": "missing_source_path"}
    if not isinstance(quote, str) or not quote:
        return {"status": "unverified", "reason": "missing_quote"}
    if len(quote) > PROPOSAL_MAX_QUOTE_CHARS:
        return {"status": "unverified", "reason": "quote_exceeds_limit"}
    try:
        normalized = normalize_relpath(source_path)
        path = resolve_inside(root, normalized)
    except KnowledgeHubError:
        return {"status": "unverified", "reason": "source_outside_hub"}
    if path.is_symlink() or not path.is_file():
        return {"status": "unverified", "reason": "source_missing_or_symlink"}
    try:
        text = read_utf8_bounded(
            path,
            PROPOSAL_MAX_EVIDENCE_SOURCE_BYTES,
            "proposal evidence source",
        )
    except KnowledgeHubError as exc:
        message = str(exc)
        if "exceeds" in message:
            return {"status": "unverified", "reason": "source_exceeds_limit"}
        if "valid UTF-8" in message:
            return {"status": "unverified", "reason": "source_not_utf8_readable"}
        return {"status": "unverified", "reason": "source_not_readable"}
    except OSError:
        return {"status": "unverified", "reason": "source_not_readable"}
    if quote not in text:
        return {"status": "unverified", "reason": "quote_not_exact"}
    return {
        "status": "verified",
        "verifier": "hub-file-exact-quote",
        "source_digest": _hash(text),
        "quote_digest": _hash(quote),
    }


def assess_proposal(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
    *,
    client_id: str = "untrusted",
    staged_today: int = 0,
    write_auto_granted: bool = False,
    policy_path: str = "registry/agent-review-policy.json",
) -> Dict[str, Any]:
    if not isinstance(proposal, Mapping):
        raise KnowledgeHubError("proposal must be a JSON object")
    policy = _load_policy(root, policy_path)
    policy_values = _validate_policy(policy)
    proposal_bytes = len(compact_json(proposal).encode("utf-8"))
    if proposal_bytes > PROPOSAL_MAX_BYTES:
        raise KnowledgeHubError(
            "proposal exceeds {} bytes".format(PROPOSAL_MAX_BYTES)
        )
    if not isinstance(client_id, str) or not client_id:
        raise KnowledgeHubError("client_id must be a non-empty host identity")
    if len(client_id) > PROPOSAL_MAX_CLIENT_ID_CHARS:
        raise KnowledgeHubError(
            "client_id exceeds {} characters".format(
                PROPOSAL_MAX_CLIENT_ID_CHARS
            )
        )
    if type(staged_today) is not int or staged_today < 0:
        raise KnowledgeHubError("staged_today must be a non-negative integer")
    if not isinstance(write_auto_granted, bool):
        raise KnowledgeHubError("write_auto_granted must be boolean")
    proposal_hash = _proposal_hash(proposal)
    client_fingerprint = _hash(client_id)[:16]
    reasons = []
    contract = proposal.get("agent_contract")
    contract = contract if isinstance(contract, Mapping) else {}
    role = str(contract.get("role", ""))
    kind = str(proposal.get("kind", ""))
    status = str(proposal.get("status", "reviewing"))
    raw_capabilities = contract.get("capabilities", [])
    capabilities = (
        set(raw_capabilities)
        if isinstance(raw_capabilities, list)
        and all(isinstance(value, str) for value in raw_capabilities)
        else set()
    )
    evidence = _verify_exact_quote(root, proposal)

    if not policy.get("enabled"):
        reasons.append("policy_disabled")
    if client_id not in set(policy_values["trusted_clients"]):
        reasons.append("client_not_trusted_by_host_policy")
    if kind in HIGH_RISK_KINDS:
        reasons.append("high_risk_kind_human_only")
    if kind not in set(policy_values["eligible_kinds"]):
        reasons.append("kind_not_opted_in")
    if role not in set(policy_values["eligible_runtime_roles"]) or role != "assertion":
        reasons.append("runtime_role_not_low_risk_assertion")
    if "shadow_auto_stage_eligible" not in capabilities:
        reasons.append("type_capability_not_opted_in")
    if status not in {"draft", "reviewing"}:
        reasons.append("target_status_not_candidate")
    if proposal.get("promotion") not in (None, "", "none"):
        reasons.append("promotion_field_forbidden")
    if any(proposal.get(field) not in (None, "", []) for field in ("owner_decision", "reviewed_by", "human_reviewed_by")):
        reasons.append("owner_or_human_review_field_forbidden")
    if evidence.get("status") != "verified":
        reasons.append("evidence_not_exactly_verified")
    daily_limit = policy_values["daily_limit"]
    if daily_limit <= 0 or staged_today >= daily_limit:
        reasons.append("daily_limit_disabled_or_exhausted")

    eligible = not reasons
    sample_bucket = int(
        _hash("{}:{}".format(policy.get("sample_seed", ""), proposal_hash))[:8], 16
    ) % 100
    sample_percent = policy_values["human_sample_percent"]
    sampled = eligible and sample_bucket < sample_percent
    eligible_route = (
        "human-sampled" if sampled else "auto-stage-reviewing" if eligible else "human-review"
    )
    if eligible and not write_auto_granted:
        reasons.append("write_auto_not_granted_shadow_only")
    return {
        "schema_version": PROPOSAL_ROUTE_SCHEMA,
        "read_only": True,
        "report_only": True,
        "policy_mode": "shadow",
        "policy_enabled": bool(policy.get("enabled")),
        "actual_route": "human-review",
        "eligible_route": eligible_route,
        "proposal_hash": proposal_hash,
        "client_fingerprint": client_fingerprint,
        "reason_codes": reasons,
        "evidence_verification": evidence,
        "sample": {
            "bucket": sample_bucket,
            "human_sample_percent": sample_percent,
            "sampled": sampled,
        },
        "would_apply_with_write_auto": bool(
            eligible_route == "auto-stage-reviewing" and write_auto_granted
        ),
        "authority_contract": {
            "can_write_registry": False,
            "can_promote_active": False,
            "host_identity_from_proposal": False,
            "constraints_guidance_questions_symbols_human_only": True,
        },
    }


def record_shadow_assessment(root: pathlib.Path, payload: Mapping[str, Any]) -> pathlib.Path:
    """Append only non-content routing metadata to ignored local cache."""

    row = _shadow_audit_projection(payload)
    relative = ".cache/knowledge-hub/proposal-route-shadow.jsonl"
    path = _path_without_symlink_components(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(str(path), flags, 0o600)
    with os.fdopen(descriptor, "r+b") as handle:
        descriptor_stat = os.fstat(handle.fileno())
        if not stat.S_ISREG(descriptor_stat.st_mode) or descriptor_stat.st_nlink != 1:
            raise KnowledgeHubError("proposal shadow audit must be one regular file")
        os.fchmod(handle.fileno(), 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        if size > PROPOSAL_SHADOW_MAX_BYTES:
            raise KnowledgeHubError(
                "proposal shadow audit exceeds {} bytes".format(
                    PROPOSAL_SHADOW_MAX_BYTES
                )
            )
        previous_hash = ""
        sequence = 1
        if size:
            handle.seek(-1, os.SEEK_END)
            if handle.read(1) != b"\n":
                raise KnowledgeHubError("proposal shadow audit has a truncated tail row")
            handle.seek(max(0, size - (PROPOSAL_SHADOW_MAX_LINE_BYTES + 1)))
            tail = handle.read()
            lines = [line for line in tail.splitlines() if line.strip()]
            if not lines or len(lines[-1]) > PROPOSAL_SHADOW_MAX_LINE_BYTES:
                raise KnowledgeHubError("proposal shadow audit has an invalid tail row")
            try:
                previous = json.loads(lines[-1].decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise KnowledgeHubError("proposal shadow audit tail is invalid") from exc
            if not isinstance(previous, Mapping) or _shadow_row_semantic_errors(previous):
                raise KnowledgeHubError("proposal shadow audit tail metadata is invalid")
            previous_core = dict(previous)
            previous_event_hash = str(previous_core.pop("event_hash", ""))
            if previous_event_hash != _hash(compact_json(previous_core)):
                raise KnowledgeHubError("proposal shadow audit tail hash is invalid")
            previous_hash = str(previous.get("event_hash", ""))
            sequence = int(previous.get("sequence", 0)) + 1
            if sequence > PROPOSAL_SHADOW_MAX_ROWS:
                raise KnowledgeHubError(
                    "proposal shadow audit exceeds {} rows".format(
                        PROPOSAL_SHADOW_MAX_ROWS
                    )
                )
        row["sequence"] = sequence
        row["previous_hash"] = previous_hash
        row.pop("event_hash", None)
        row["event_hash"] = _hash(compact_json(row))
        encoded = (compact_json(row) + "\n").encode("utf-8")
        if len(encoded) > PROPOSAL_SHADOW_MAX_LINE_BYTES:
            raise KnowledgeHubError("proposal shadow audit row exceeds the line budget")
        if size + len(encoded) > PROPOSAL_SHADOW_MAX_BYTES:
            raise KnowledgeHubError(
                "proposal shadow audit exceeds {} bytes".format(
                    PROPOSAL_SHADOW_MAX_BYTES
                )
            )
        handle.seek(0, os.SEEK_END)
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return path


def shadow_audit_stats(
    root: pathlib.Path,
    audit_path: str = ".cache/knowledge-hub/proposal-route-shadow.jsonl",
    policy_path: str = "registry/agent-review-policy.json",
) -> Dict[str, Any]:
    """Summarize shadow routing safety without exposing proposal or client content."""

    policy = _load_policy(root, policy_path)
    _validate_policy(policy)
    path = _path_without_symlink_components(root, audit_path)
    if not path.exists():
        return {
            "schema_version": PROPOSAL_SHADOW_STATS_SCHEMA,
            "read_only": True,
            "status": "pending",
            "policy_enabled": bool(policy.get("enabled")),
            "sample_count": 0,
            "route_counts": {"actual": {}, "eligible": {}},
            "reason_counts": {},
            "sampled_count": 0,
            "client_fingerprint_count": 0,
            "first_recorded_at": "",
            "last_recorded_at": "",
            "safety": {
                "actual_non_human_route_count": 0,
                "high_risk_non_human_eligible_count": 0,
                "content_leak_row_count": 0,
            },
            "integrity": {
                "hash_chain_valid": True,
                "invalid_row_count": 0,
                "duplicate_proposal_hash_count": 0,
            },
            "content_echoed": False,
        }
    raw_audit = read_bytes_bounded(
        path,
        PROPOSAL_SHADOW_MAX_BYTES,
        "proposal shadow audit",
    )
    actual_counts: Counter = Counter()
    eligible_counts: Counter = Counter()
    reason_counts: Counter = Counter()
    fingerprints = set()
    proposal_hashes = set()
    duplicate_hashes = 0
    sampled_count = 0
    actual_non_human = 0
    high_risk_non_human = 0
    content_leak_rows = 0
    invalid_rows = 0
    previous_hash = ""
    recorded_at_values = []
    row_count = 0
    truncated_tail = bool(raw_audit and not raw_audit.endswith(b"\n"))
    for line_no, line in enumerate(raw_audit.splitlines(), 1):
        if not line.strip():
            continue
        row_count += 1
        if row_count > PROPOSAL_SHADOW_MAX_ROWS:
            raise KnowledgeHubError(
                "proposal shadow audit exceeds {} rows".format(
                    PROPOSAL_SHADOW_MAX_ROWS
                )
            )
        if len(line) > PROPOSAL_SHADOW_MAX_LINE_BYTES:
            raise KnowledgeHubError(
                "proposal shadow audit line {} exceeds the line budget".format(
                    line_no
                )
            )
        try:
            row = json.loads(line.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            invalid_rows += 1
            actual_counts["invalid"] += 1
            eligible_counts["invalid"] += 1
            reason_counts["invalid"] += 1
            continue
        if not isinstance(row, dict):
            invalid_rows += 1
            actual_counts["invalid"] += 1
            eligible_counts["invalid"] += 1
            reason_counts["invalid"] += 1
            continue
        unexpected = set(row) - PROPOSAL_SHADOW_ALLOWED_FIELDS
        content_leak_rows += int(bool(unexpected))
        event_hash = str(row.get("event_hash", ""))
        core = dict(row)
        core.pop("event_hash", None)
        expected_hash = _hash(compact_json(core))
        semantic_errors = _shadow_row_semantic_errors(row)
        row_invalid = bool(
            semantic_errors
            or row.get("sequence") != row_count
            or str(row.get("previous_hash", "")) != previous_hash
            or event_hash != expected_hash
        )
        if row_invalid:
            invalid_rows += 1
        previous_hash = event_hash if _is_lower_hex(event_hash, 64) else ""
        actual = str(row.get("actual_route", ""))
        eligible = str(row.get("eligible_route", ""))
        reasons = row.get("reason_codes", [])
        reasons = reasons if isinstance(reasons, list) else []
        actual_non_human += int(actual != "human-review")
        high_risk_non_human += int(
            "high_risk_kind_human_only" in reasons and eligible != "human-review"
        )
        if row_invalid:
            actual_counts["invalid"] += 1
            eligible_counts["invalid"] += 1
            reason_counts["invalid"] += 1
            continue
        actual_counts[actual] += 1
        eligible_counts[eligible] += 1
        reason_counts.update(reasons)
        sample = row.get("sample") if isinstance(row.get("sample"), Mapping) else {}
        sampled_count += int(bool(sample.get("sampled", False)))
        fingerprint = str(row.get("client_fingerprint", ""))
        if fingerprint:
            fingerprints.add(fingerprint)
        proposal_hash = str(row.get("proposal_hash", ""))
        if proposal_hash in proposal_hashes:
            duplicate_hashes += 1
        elif proposal_hash:
            proposal_hashes.add(proposal_hash)
        recorded_at = str(row.get("recorded_at", ""))
        if recorded_at:
            recorded_at_values.append(recorded_at)
    invalid_rows += int(truncated_tail)
    unsafe = actual_non_human or high_risk_non_human or content_leak_rows
    status = "pending" if row_count == 0 else "fail" if unsafe or invalid_rows else "pass"
    return {
        "schema_version": PROPOSAL_SHADOW_STATS_SCHEMA,
        "read_only": True,
        "status": status,
        "policy_enabled": bool(policy.get("enabled")),
        "sample_count": row_count,
        "route_counts": {
            "actual": dict(sorted(actual_counts.items())),
            "eligible": dict(sorted(eligible_counts.items())),
        },
        "reason_counts": dict(sorted(reason_counts.items())),
        "sampled_count": sampled_count,
        "client_fingerprint_count": len(fingerprints),
        "first_recorded_at": min(recorded_at_values) if recorded_at_values else "",
        "last_recorded_at": max(recorded_at_values) if recorded_at_values else "",
        "safety": {
            "actual_non_human_route_count": actual_non_human,
            "high_risk_non_human_eligible_count": high_risk_non_human,
            "content_leak_row_count": content_leak_rows,
        },
        "integrity": {
            "hash_chain_valid": invalid_rows == 0,
            "invalid_row_count": invalid_rows,
            "duplicate_proposal_hash_count": duplicate_hashes,
        },
        "content_echoed": False,
    }
