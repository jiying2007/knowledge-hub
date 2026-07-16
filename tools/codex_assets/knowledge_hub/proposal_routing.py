"""Default-disabled, report-only proposal routing inspired by reviewed-memory gates."""

from __future__ import annotations

import fcntl
import hashlib
import json
import pathlib
from typing import Any, Dict, Mapping

from .common import (
    KnowledgeHubError,
    compact_json,
    load_json,
    normalize_relpath,
    resolve_inside,
    utc_timestamp,
)


PROPOSAL_ROUTE_SCHEMA = "knowledge-hub.proposal-route.v1"
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
    try:
        normalized = normalize_relpath(source_path)
        path = resolve_inside(root, normalized)
    except KnowledgeHubError:
        return {"status": "unverified", "reason": "source_outside_hub"}
    if path.is_symlink() or not path.is_file():
        return {"status": "unverified", "reason": "source_missing_or_symlink"}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {"status": "unverified", "reason": "source_not_utf8_readable"}
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
    policy = load_json(resolve_inside(root, policy_path), {}) or {}
    if policy.get("schema_version") != 1 or policy.get("mode") != "shadow":
        raise KnowledgeHubError("invalid or unsafe Agent review policy")
    proposal_hash = _proposal_hash(proposal)
    client_fingerprint = _hash(client_id)[:16]
    reasons = []
    contract = proposal.get("agent_contract")
    contract = contract if isinstance(contract, Mapping) else {}
    role = str(contract.get("role", ""))
    kind = str(proposal.get("kind", ""))
    status = str(proposal.get("status", "reviewing"))
    capabilities = set(contract.get("capabilities", []))
    evidence = _verify_exact_quote(root, proposal)

    if not policy.get("enabled"):
        reasons.append("policy_disabled")
    if client_id not in set(policy.get("trusted_clients", [])):
        reasons.append("client_not_trusted_by_host_policy")
    if kind in HIGH_RISK_KINDS:
        reasons.append("high_risk_kind_human_only")
    if kind not in set(policy.get("eligible_kinds", [])):
        reasons.append("kind_not_opted_in")
    if role not in set(policy.get("eligible_runtime_roles", [])) or role != "assertion":
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
    daily_limit = int(policy.get("daily_limit", 0))
    if daily_limit <= 0 or staged_today >= daily_limit:
        reasons.append("daily_limit_disabled_or_exhausted")

    eligible = not reasons
    sample_bucket = int(
        _hash("{}:{}".format(policy.get("sample_seed", ""), proposal_hash))[:8], 16
    ) % 100
    sample_percent = int(policy.get("human_sample_percent", 100))
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

    path = root / ".cache/knowledge-hub/proposal-route-shadow.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "schema_version": PROPOSAL_ROUTE_SCHEMA,
        "recorded_at": utc_timestamp(),
        "proposal_hash": payload.get("proposal_hash", ""),
        "client_fingerprint": payload.get("client_fingerprint", ""),
        "actual_route": payload.get("actual_route", ""),
        "eligible_route": payload.get("eligible_route", ""),
        "reason_codes": list(payload.get("reason_codes", [])),
        "sample": dict(payload.get("sample", {})),
    }
    with path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.write(compact_json(row) + "\n")
        handle.flush()
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return path
