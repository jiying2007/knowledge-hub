"""Report-only and local-evidence services for Knowledge Runtime v3."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence

from .common import (
    KnowledgeHubError,
    ensure_private_directory,
    ensure_private_file,
    load_jsonl,
    registry_items,
    resolve_today,
    utc_timestamp,
)
from .runtime_v3_contracts import (
    A2A_PROTOCOL_VERSION,
    DEFAULT_PROFILE,
    FEEDBACK_OUTCOMES,
    MEMORY_LEVELS,
    agent_profile,
    capability_catalog,
    config,
    require_capability,
    retrieval_profile,
    rows,
)

MAX_TEXT_CHARS = 8192
MAX_LIST_VALUES = 64
MAX_VALUE_CHARS = 2048


def _bounded_strings(
    values: Sequence[Any], *, maximum: int = MAX_LIST_VALUES, label: str = "values"
) -> List[str]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise KnowledgeHubError("{} must be a sequence".format(label))
    if len(values) > maximum:
        raise KnowledgeHubError("{} exceeds {} values".format(label, maximum))
    result = []
    for value in values:
        text = str(value).strip()
        if not text or len(text) > MAX_VALUE_CHARS:
            raise KnowledgeHubError("{} contains an invalid value".format(label))
        result.append(text)
    return result


def memory_candidate(
    agent_id: str, level: str, summary: str, source_refs: Sequence[str] = ()
) -> Dict[str, Any]:
    if level not in MEMORY_LEVELS:
        raise KnowledgeHubError("invalid memory level")
    summary = str(summary).strip()
    if not summary or len(summary) > 4096:
        raise KnowledgeHubError("memory summary must be non-empty and bounded")
    refs = _bounded_strings(source_refs, maximum=32, label="source_refs")
    durable = level in {"semantic", "procedural", "policy"}
    return {
        "schema_version": "knowledge-hub.memory-candidate.v1",
        "status": "candidate",
        "agent_id": agent_id,
        "level": level,
        "summary": summary,
        "source_refs": refs,
        "durable": durable,
        "canonical_write_permitted": False,
        "promotion_required": durable,
        "target": "reviewing" if durable else "local-runtime-cache",
    }


def connector_catalog(root: pathlib.Path) -> Dict[str, Any]:
    return {
        "schema_version": "knowledge-hub.connector-catalog.v1",
        "connectors": rows(root, "connectors"),
        "live_sync_implicitly_authorized": False,
    }


def connector_envelope(
    root: pathlib.Path,
    connector_id: str,
    object_id: str,
    *,
    version: str = "",
    source_uri: str = "",
    visibility: str = "team-internal",
    content_type: str = "text/unknown",
    acl: Sequence[str] = (),
    content_sha256: str = "",
) -> Dict[str, Any]:
    connectors = {
        str(row.get("id", "")): row for row in rows(root, "connectors")
    }
    if connector_id not in connectors:
        raise KnowledgeHubError("unknown connector: {}".format(connector_id))
    object_id = str(object_id).strip()
    if not object_id or len(object_id) > 1024:
        raise KnowledgeHubError("connector object_id must be non-empty and bounded")
    if source_uri and len(source_uri) > 4096:
        raise KnowledgeHubError("connector source_uri is too long")
    if content_sha256 and not re.fullmatch(r"[0-9a-f]{64}", content_sha256):
        raise KnowledgeHubError("connector content_sha256 must be lowercase SHA256")
    acl_values = _bounded_strings(acl, maximum=64, label="connector acl")
    connector = connectors[connector_id]
    return {
        "schema_version": "knowledge-hub.connector-envelope.v1",
        "connector_id": connector_id,
        "object_id": object_id,
        "version": str(version)[:512],
        "source_uri": str(source_uri),
        "visibility": str(visibility)[:128],
        "content_type": str(content_type)[:256],
        "acl": acl_values,
        "content_sha256": content_sha256,
        "hub_disposition": connector.get("default_disposition", "reference-only"),
        "acl_passthrough": bool(connector.get("acl_passthrough", True)),
        "sync_performed": False,
        "canonical_write_performed": False,
    }


def agent_card(root: pathlib.Path, agent_id: str) -> Dict[str, Any]:
    profile = agent_profile(root, agent_id)
    return {
        "schema_version": "knowledge-hub.a2a-agent-card.v1",
        "protocol_version": A2A_PROTOCOL_VERSION,
        "id": agent_id,
        "name": profile.get("name", agent_id),
        "description": profile.get("description", ""),
        "skills": list(profile.get("skills", [])),
        "capabilities": list(profile.get("capabilities", [])),
        "task_execution": "report-only",
        "canonical_write_permitted": False,
    }


def a2a_preflight(
    root: pathlib.Path,
    from_agent: str,
    to_agent: str,
    task: str,
    requested_capabilities: Sequence[str],
) -> Dict[str, Any]:
    task = str(task).strip()
    if not task or len(task) > MAX_TEXT_CHARS:
        raise KnowledgeHubError("A2A task must be non-empty and bounded")
    agent_profile(root, from_agent)
    target = agent_profile(root, to_agent)
    catalog = capability_catalog(root)
    requested = set(
        _bounded_strings(
            requested_capabilities,
            maximum=32,
            label="requested_capabilities",
        )
    )
    target_caps = {str(value) for value in target.get("capabilities", [])}
    unknown = sorted(requested - set(catalog))
    unsupported = sorted((requested - target_caps) | set(unknown))
    high_risk = sorted(
        capability
        for capability in requested
        if capability in catalog
        and (
            catalog[capability].get("requires_human_approval", False)
            or catalog[capability].get("mode") == "write"
        )
    )
    return {
        "schema_version": "knowledge-hub.a2a-preflight.v1",
        "status": "pass" if not unsupported and not high_risk else "needs-review",
        "from_agent": from_agent,
        "to_agent": to_agent,
        "unknown_capabilities": unknown,
        "unsupported_capabilities": unsupported,
        "high_risk_capabilities": high_risk,
        "delegation_executes_task": False,
        "human_review_required": bool(unsupported or high_risk),
    }


def _cache(root: pathlib.Path) -> pathlib.Path:
    path = root / ".cache" / "knowledge-hub" / "runtime-v3"
    ensure_private_directory(path)
    return path


def _append_jsonl(path: pathlib.Path, row: Mapping[str, Any]) -> None:
    ensure_private_directory(path.parent)
    if path.exists():
        ensure_private_file(path)
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_APPEND
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(str(path), flags, 0o600)
    try:
        encoded = (
            json.dumps(dict(row), ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    ensure_private_file(path)


def record_feedback(
    root: pathlib.Path,
    agent_id: str,
    query: str,
    outcome: str,
    *,
    selected_id: str = "",
    selected_rank: int = 0,
    candidate_ids: Sequence[str] = (),
    profile_id: str = DEFAULT_PROFILE,
) -> Dict[str, Any]:
    require_capability(root, agent_id, "knowledge.feedback.write")
    if outcome not in FEEDBACK_OUTCOMES:
        raise KnowledgeHubError("invalid feedback outcome")
    query = str(query).strip()
    if not query or len(query) > 4096:
        raise KnowledgeHubError("feedback query must be non-empty and bounded")
    candidates = _bounded_strings(
        candidate_ids, maximum=20, label="candidate_ids"
    )
    row = {
        "schema_version": "knowledge-hub.feedback.v2",
        "recorded_at": utc_timestamp(),
        "agent_id": agent_id,
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "raw_query_stored": False,
        "outcome": outcome,
        "selected_id": str(selected_id)[:512],
        "selected_rank": max(0, int(selected_rank)),
        "candidate_ids": candidates,
        "retrieval_profile": profile_id,
    }
    _append_jsonl(_cache(root) / "feedback.jsonl", row)
    return {"status": "recorded", "record": row}


def _feedback(root: pathlib.Path, profile_id: str) -> List[Dict[str, Any]]:
    path = root / ".cache" / "knowledge-hub" / "runtime-v3" / "feedback.jsonl"
    if not path.exists():
        return []
    return [
        row
        for row in load_jsonl(path, maximum_bytes=16 * 1024 * 1024)
        if row.get("retrieval_profile") == profile_id
    ]


def adaptive_retrieval_proposal(
    root: pathlib.Path, profile_id: str = DEFAULT_PROFILE
) -> Dict[str, Any]:
    weights = dict(retrieval_profile(root, profile_id)["weights"])
    feedback = _feedback(root, profile_id)
    counts = {key: 0 for key in FEEDBACK_OUTCOMES}
    for row in feedback:
        outcome = str(row.get("outcome", ""))
        if outcome in counts:
            counts[outcome] += 1
    proposed = dict(weights)
    reasons: List[str] = []
    total_count = len(feedback)
    if total_count >= 10:
        if counts["missing"] / total_count >= 0.2:
            proposed["semantic"] += 0.05
            proposed["lexical"] = max(0.05, proposed["lexical"] - 0.05)
            reasons.append("missing>=20%")
        if counts["stale"] / total_count >= 0.1:
            proposed["freshness"] += 0.05
            proposed["lexical"] = max(0.05, proposed["lexical"] - 0.05)
            reasons.append("stale>=10%")
        if (counts["wrong"] + counts["conflicting"]) / total_count >= 0.1:
            proposed["authority"] += 0.05
            proposed["semantic"] = max(0.05, proposed["semantic"] - 0.05)
            reasons.append("wrong-or-conflicting>=10%")
    norm = sum(proposed.values()) or 1.0
    normalized = {key: round(value / norm, 6) for key, value in proposed.items()}
    return {
        "schema_version": "knowledge-hub.adaptive-retrieval-proposal.v1",
        "status": "proposal" if reasons else "no-change",
        "profile_id": profile_id,
        "sample_count": total_count,
        "current_weights": weights,
        "proposed_weights": normalized,
        "reasons": reasons,
        "auto_apply": False,
        "human_review_required": True,
    }


def _receipt_sha256(row: Mapping[str, Any]) -> str:
    payload = dict(row)
    payload.pop("receipt_sha256", None)
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _validate_receipt_chain(rows: Sequence[Mapping[str, Any]]) -> str:
    previous = ""
    for index, row in enumerate(rows, start=1):
        observed = str(row.get("receipt_sha256", ""))
        linked = str(row.get("previous_receipt_sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", observed):
            raise KnowledgeHubError(
                "execution receipt ledger row {} has invalid digest".format(index)
            )
        if linked != previous:
            raise KnowledgeHubError(
                "execution receipt ledger row {} has invalid previous link".format(index)
            )
        if observed != _receipt_sha256(row):
            raise KnowledgeHubError(
                "execution receipt ledger row {} failed integrity check".format(index)
            )
        previous = observed
    return previous


def execution_receipt(
    agent_id: str,
    action: str,
    verdict: str,
    evidence_ids: Sequence[str] = (),
    *,
    previous_receipt_sha256: str = "",
) -> Dict[str, Any]:
    evidence = _bounded_strings(
        evidence_ids, maximum=64, label="evidence_ids"
    )
    row = {
        "schema_version": "knowledge-hub.execution-receipt.v1",
        "timestamp": utc_timestamp(),
        "agent_id": agent_id,
        "action": str(action)[:4096],
        "verdict": str(verdict)[:64],
        "evidence_ids": evidence,
        "previous_receipt_sha256": previous_receipt_sha256,
        "canonical_state_changed": False,
    }
    row["receipt_sha256"] = _receipt_sha256(row)
    return row


def record_execution_receipt(
    root: pathlib.Path,
    agent_id: str,
    action: str,
    verdict: str,
    evidence_ids: Sequence[str] = (),
) -> Dict[str, Any]:
    require_capability(root, agent_id, "execution.receipt.write")
    path = _cache(root) / "execution-receipts.jsonl"
    previous = ""
    if path.exists():
        existing = load_jsonl(path, maximum_bytes=16 * 1024 * 1024)
        previous = _validate_receipt_chain(existing)
    row = execution_receipt(
        agent_id,
        action,
        verdict,
        evidence_ids,
        previous_receipt_sha256=previous,
    )
    _append_jsonl(path, row)
    return {"status": "recorded", "record": row}


def trace_projection(
    root: pathlib.Path, agent_id: str, operation: str, query: str = ""
) -> Dict[str, Any]:
    settings = config(root).get("observability", {})
    event = {
        "schema_version": "knowledge-hub.trace.v1",
        "timestamp": utc_timestamp(),
        "agent_id": agent_id,
        "operation": str(operation)[:256],
        "query_sha256": (
            hashlib.sha256(query.encode("utf-8")).hexdigest() if query else ""
        ),
        "raw_query_stored": False,
    }
    return {
        "schema_version": "knowledge-hub.observation.v1",
        "event": event,
        "opentelemetry_enabled": bool(settings.get("opentelemetry_enabled", False)),
        "langfuse_enabled": bool(settings.get("langfuse_enabled", False)),
        "network_export_performed": False,
    }


def steward_audit(root: pathlib.Path, *, as_of: str = "") -> Dict[str, Any]:
    today, _ = resolve_today(as_of)
    stale = []
    evidence_gaps = []
    titles: MutableMapping[str, List[str]] = {}
    for item in registry_items(root):
        item_id = str(item.get("id", ""))
        if not item_id:
            continue
        review_after = None
        try:
            if item.get("review_after"):
                import datetime as dt

                review_after = dt.date.fromisoformat(str(item["review_after"]))
        except ValueError:
            review_after = None
        if item.get("status") == "active" and review_after and review_after < today:
            stale.append({"id": item_id, "review_after": review_after.isoformat()})
        if item.get("status") in {"active", "reviewing"} and not item.get("evidence_refs"):
            evidence_gaps.append({"id": item_id, "reason": "missing-evidence-refs"})
        key = re.sub(r"\s+", "", str(item.get("title", "")).casefold())
        if key:
            titles.setdefault(key, []).append(item_id)
    duplicates = [
        {"normalized_title": key[:120], "ids": sorted(ids)}
        for key, ids in sorted(titles.items())
        if len(ids) > 1
    ]
    proposals = [
        {"kind": "review-stale-item", "item_id": row["id"]}
        for row in stale[:20]
    ] + [
        {"kind": "request-evidence", "item_id": row["id"]}
        for row in evidence_gaps[:20]
    ]
    return {
        "schema_version": "knowledge-hub.steward-audit.v1",
        "status": "needs-review" if proposals else "pass",
        "stale_active": stale,
        "evidence_gaps": evidence_gaps,
        "duplicate_titles": duplicates,
        "proposals": proposals,
        "report_only": True,
        "canonical_write_performed": False,
    }


def improvement_plan(
    root: pathlib.Path,
    *,
    profile_id: str = DEFAULT_PROFILE,
    as_of: str = "",
) -> Dict[str, Any]:
    adaptive = adaptive_retrieval_proposal(root, profile_id)
    steward = steward_audit(root, as_of=as_of)
    proposals: List[Dict[str, Any]] = [
        dict(row) for row in steward["proposals"] if isinstance(row, Mapping)
    ]
    if adaptive["status"] == "proposal":
        proposals.insert(
            0,
            {
                "kind": "retrieval-profile-change",
                "payload": adaptive,
                "requires_fresh_eval": True,
            },
        )
    return {
        "schema_version": "knowledge-hub.improvement-plan.v1",
        "status": "proposal" if proposals else "no-change",
        "proposals": proposals,
        "guards": {
            "auto_apply": False,
            "auto_promote_active": False,
            "owner_decision_bypass": False,
            "requires_human_review": True,
        },
    }
