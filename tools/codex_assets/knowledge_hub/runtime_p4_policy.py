"""Fail-closed policy layer for P4 cross-repo agent handoffs."""

from __future__ import annotations

import pathlib
from typing import Any, Dict, Mapping, Sequence

from .runtime_p4_interop import handoff_envelope
from .runtime_v3_contracts import agent_profile


def _scope_allowed(root: pathlib.Path, agent_id: str, scope_ref: str) -> bool:
    profile = agent_profile(root, agent_id)
    scopes = [
        str(value).strip().strip("/")
        for value in profile.get("knowledge_scopes", [])
        if str(value).strip()
    ]
    if not scope_ref or not scopes:
        return bool(scope_ref) or not scopes
    normalized = scope_ref.strip("/")
    return any(
        normalized == scope or normalized.startswith(scope + "/")
        for scope in scopes
    )


def governed_handoff_envelope(
    root: pathlib.Path,
    consumer: str,
    from_agent: str,
    to_agent: str,
    task: str,
    identity: Mapping[str, Any],
    requested_capabilities: Sequence[str],
    *,
    evidence_ids: Sequence[str] = (),
    execution_receipt_sha256: str = "",
    mcp_version: str = "",
    a2a_version: str = "",
) -> Dict[str, Any]:
    result = handoff_envelope(
        root,
        consumer,
        from_agent,
        to_agent,
        task,
        identity,
        requested_capabilities,
        evidence_ids=evidence_ids,
        execution_receipt_sha256=execution_receipt_sha256,
        mcp_version=mcp_version,
        a2a_version=a2a_version,
    )
    normalized_identity = result.get("identity", {})
    if not isinstance(normalized_identity, Mapping):
        normalized_identity = {}
    scope_ref = str(normalized_identity.get("scope_ref", ""))
    from_allowed = _scope_allowed(root, from_agent, scope_ref)
    to_allowed = _scope_allowed(root, to_agent, scope_ref)

    receipt = result.get("execution_receipt", {})
    if not isinstance(receipt, Mapping):
        receipt = {}
    receipt_verified = bool(receipt.get("verified", False))
    receipt_agent_match = bool(
        not execution_receipt_sha256
        or (receipt_verified and str(receipt.get("agent_id", "")) == from_agent)
    )

    block_reasons = []
    if not from_allowed:
        block_reasons.append("from-agent-scope")
    if not to_allowed:
        block_reasons.append("to-agent-scope")
    if execution_receipt_sha256 and receipt_verified and not receipt_agent_match:
        block_reasons.append("receipt-agent-mismatch")

    result["scope_check"] = {
        "scope_ref": scope_ref,
        "from_agent_allowed": from_allowed,
        "to_agent_allowed": to_allowed,
    }
    result["execution_receipt_agent_match"] = receipt_agent_match
    result["policy_block_reasons"] = block_reasons
    result["policy_enforced"] = True
    if block_reasons:
        result["status"] = "blocked"
        result["human_review_required"] = True
    return result
