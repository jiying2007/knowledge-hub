"""Knowledge Runtime v3.

Canonical Markdown + registry remain authoritative. Every semantic, graph, memory,
feedback, A2A and self-improvement surface in this module is derived, report-only,
or local-cache evidence unless an existing governed Knowledge Hub promotion path
explicitly authorizes a canonical change.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import re
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Set, Tuple

from .agent_runtime import build_evidence_pack, check_action
from .common import (
    KnowledgeHubError,
    ensure_private_directory,
    ensure_private_file,
    load_json,
    load_jsonl,
    read_repository_utf8_bounded,
    registry_items,
    resolve_today,
    utc_timestamp,
)
from .search import SearchFilters, SearchIndex, search, search_tokens

CONFIG_PATH = "registry/knowledge-runtime-v3.json"
MCP_PROTOCOL_VERSION = "2026-07-28"
A2A_PROTOCOL_VERSION = "1.0.0"
MAX_QUERY_CHARS = 4096
MAX_RESULTS = 100
MAX_BODY_BYTES = 64 * 1024
MAX_GRAPH_HOPS = 2
VECTOR_DIMS = 128
DEFAULT_AGENT = "knowledge-reader"
DEFAULT_PROFILE = "hybrid-engineering-v1"
SERVICEABLE = {"active", "reviewing", "draft"}
FEEDBACK_OUTCOMES = {
    "accepted",
    "partially-useful",
    "wrong",
    "stale",
    "missing",
    "conflicting",
    "permission-denied",
}
MEMORY_LEVELS = {"working", "session", "episodic", "semantic", "procedural", "policy"}


def config(root: pathlib.Path) -> Dict[str, Any]:
    value = load_json(root / CONFIG_PATH, None)
    if not isinstance(value, dict):
        raise KnowledgeHubError("missing or invalid {}".format(CONFIG_PATH))
    return value


def _rows(root: pathlib.Path, key: str) -> List[Dict[str, Any]]:
    value = config(root).get(key, [])
    if not isinstance(value, list):
        raise KnowledgeHubError("runtime config {} must be a list".format(key))
    return [dict(row) for row in value if isinstance(row, Mapping)]


def agent_profile(root: pathlib.Path, agent_id: str = DEFAULT_AGENT) -> Dict[str, Any]:
    for row in _rows(root, "agents"):
        if str(row.get("id", "")) == agent_id:
            return row
    raise KnowledgeHubError("unknown agent profile: {}".format(agent_id))


def capability_catalog(root: pathlib.Path) -> Dict[str, Dict[str, Any]]:
    return {str(row["id"]): row for row in _rows(root, "capabilities") if row.get("id")}


def require_capability(root: pathlib.Path, agent_id: str, capability: str) -> None:
    profile = agent_profile(root, agent_id)
    catalog = capability_catalog(root)
    if capability not in catalog:
        raise KnowledgeHubError("unknown capability: {}".format(capability))
    if capability not in {str(v) for v in profile.get("capabilities", [])}:
        raise KnowledgeHubError(
            "agent {} is not permitted to use {}".format(agent_id, capability)
        )


def retrieval_profile(root: pathlib.Path, profile_id: str = DEFAULT_PROFILE) -> Dict[str, Any]:
    for row in _rows(root, "retrieval_profiles"):
        if str(row.get("id", "")) != profile_id:
            continue
        weights = row.get("weights")
        if not isinstance(weights, Mapping):
            raise KnowledgeHubError("retrieval profile weights must be an object")
        required = {"lexical", "semantic", "authority", "freshness"}
        if set(weights) != required:
            raise KnowledgeHubError("retrieval profile weight contract mismatch")
        total = sum(float(weights[key]) for key in required)
        if total <= 0:
            raise KnowledgeHubError("retrieval profile weights must be positive")
        row["weights"] = {key: float(weights[key]) / total for key in sorted(required)}
        return row
    raise KnowledgeHubError("unknown retrieval profile: {}".format(profile_id))


def _date(value: Any) -> Optional[dt.date]:
    try:
        return dt.date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


def _eligible(item: Mapping[str, Any], today: dt.date, scopes: Sequence[str]) -> bool:
    if str(item.get("status", "")) not in SERVICEABLE:
        return False
    if str(item.get("visibility", "")) == "personal-local":
        return False
    valid_from, valid_to = _date(item.get("valid_from")), _date(item.get("valid_to"))
    if valid_from and today < valid_from:
        return False
    if valid_to and today > valid_to:
        return False
    if not scopes:
        return True
    domain, path = str(item.get("domain", "")), str(item.get("path", ""))
    return any(
        domain == scope
        or domain.startswith(scope.rstrip("/") + "/")
        or path.startswith(scope.rstrip("/") + "/")
        for scope in scopes
        if str(scope).strip()
    )


def _authority(item: Mapping[str, Any]) -> float:
    status = str(item.get("status", ""))
    if status == "active" and not item.get("manual_validation_pending", False):
        return 1.0
    return {"active": 0.75, "reviewing": 0.5, "draft": 0.3}.get(status, 0.0)


def _freshness(item: Mapping[str, Any], today: dt.date) -> float:
    updated = _date(item.get("updated_at"))
    if not updated:
        return 0.5
    age = max(0, (today - updated).days)
    if age <= 30:
        return 1.0
    if age <= 90:
        return 0.85
    if age <= 180:
        return 0.7
    if age <= 365:
        return 0.55
    return 0.4


def _vector(tokens: Iterable[str]) -> Tuple[float, ...]:
    values = [0.0] * VECTOR_DIMS
    for token in tokens:
        digest = hashlib.sha256(str(token).encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % VECTOR_DIMS
        values[index] += 1.0 if digest[4] & 1 else -1.0
    norm = math.sqrt(sum(value * value for value in values))
    return tuple(value / norm for value in values) if norm else tuple(values)


def _semantic_text(root: pathlib.Path, item: Mapping[str, Any]) -> str:
    parts = [
        str(item.get("title", "")),
        str(item.get("summary_zh", "")),
        " ".join(str(v) for v in item.get("tags", [])),
        str(item.get("domain", "")),
    ]
    path = str(item.get("path", ""))
    if path:
        try:
            parts.append(
                read_repository_utf8_bounded(root, path, MAX_BODY_BYTES, "semantic body")
            )
        except KnowledgeHubError:
            pass
    return "\n".join(parts)


def hybrid_search(
    root: pathlib.Path,
    query: str,
    *,
    limit: int = 20,
    profile_id: str = DEFAULT_PROFILE,
    knowledge_scopes: Sequence[str] = (),
    as_of: str = "",
) -> Dict[str, Any]:
    query = str(query or "").strip()
    if not query or len(query) > MAX_QUERY_CHARS:
        raise KnowledgeHubError("query must be non-empty and <= {} chars".format(MAX_QUERY_CHARS))
    if not 1 <= int(limit) <= MAX_RESULTS:
        raise KnowledgeHubError("limit must be between 1 and {}".format(MAX_RESULTS))
    today, source = resolve_today(as_of)
    profile = retrieval_profile(root, profile_id)
    weights = profile["weights"]
    items = [
        row for row in registry_items(root) if _eligible(row, today, knowledge_scopes)
    ][:512]
    by_id = {str(row.get("id", "")): row for row in items if row.get("id")}

    lexical = search(
        root,
        query,
        limit=min(MAX_RESULTS, max(limit * 4, 20)),
        filters=SearchFilters(),
        search_index=SearchIndex(root),
    )
    lexical_scores: Dict[str, float] = {}
    why: Dict[str, List[str]] = {}
    for row in lexical.get("results", []):
        item_id = str(row.get("item_id", row.get("id", "")))
        if item_id not in by_id:
            continue
        lexical_scores[item_id] = max(
            lexical_scores.get(item_id, 0.0), float(row.get("score", 0.0) or 0.0)
        )
        why[item_id] = list(row.get("why_selected", []))[:8]
    lexical_max = max(lexical_scores.values(), default=1.0) or 1.0

    query_vector = _vector(search_tokens(query))
    semantic_scores = {
        item_id: max(
            0.0,
            sum(
                left * right
                for left, right in zip(
                    query_vector, _vector(search_tokens(_semantic_text(root, item)))
                )
            ),
        )
        for item_id, item in by_id.items()
    }
    candidates = set(lexical_scores)
    candidates.update(
        item_id
        for item_id, _ in sorted(
            semantic_scores.items(), key=lambda pair: (-pair[1], pair[0])
        )[: max(40, limit * 4)]
    )
    ranked = []
    for item_id in candidates:
        item = by_id[item_id]
        parts = {
            "lexical": lexical_scores.get(item_id, 0.0) / lexical_max,
            "semantic": semantic_scores.get(item_id, 0.0),
            "authority": _authority(item),
            "freshness": _freshness(item, today),
        }
        score = sum(weights[key] * parts[key] for key in weights)
        ranked.append(
            {
                "id": item_id,
                "title": str(item.get("title", "")),
                "path": str(item.get("path", "")),
                "status": str(item.get("status", "")),
                "kind": str(item.get("kind", "")),
                "domain": str(item.get("domain", "")),
                "score": round(score, 6),
                "score_components": {k: round(v, 6) for k, v in parts.items()},
                "why_selected": why.get(item_id, []),
                "derived": True,
                "authoritative": parts["authority"] == 1.0,
            }
        )
    ranked.sort(
        key=lambda row: (
            -float(row["score"]),
            -float(row["score_components"]["authority"]),
            str(row["id"]),
        )
    )
    return {
        "schema_version": "knowledge-hub.hybrid-search.v1",
        "status": "pass",
        "query": query,
        "profile_id": profile_id,
        "weights": weights,
        "as_of": today.isoformat(),
        "as_of_source": source,
        "results": ranked[:limit],
        "candidate_count": len(ranked),
        "authority_contract": {
            "derived_ranking_is_authority": False,
            "registry_lifecycle_remains_authoritative": True,
        },
    }


def context_graph(
    root: pathlib.Path, seed_ids: Sequence[str], *, hops: int = 1
) -> Dict[str, Any]:
    if not 0 <= hops <= MAX_GRAPH_HOPS:
        raise KnowledgeHubError("graph hops must be between 0 and {}".format(MAX_GRAPH_HOPS))
    by_id = {
        str(row.get("id", "")): row for row in registry_items(root) if row.get("id")
    }
    frontier, visited, edges = set(seed_ids) & set(by_id), set(seed_ids) & set(by_id), []
    for _ in range(hops):
        next_frontier: Set[str] = set()
        for item_id in sorted(frontier):
            contract = by_id[item_id].get("agent_contract", {})
            relations = contract.get("relations", {}) if isinstance(contract, Mapping) else {}
            if not isinstance(relations, Mapping):
                continue
            for relation, targets in relations.items():
                if not isinstance(targets, list):
                    continue
                for target in targets:
                    target_id = str(target)
                    if target_id not in by_id:
                        continue
                    edges.append(
                        {"source_id": item_id, "relation": str(relation), "target_id": target_id}
                    )
                    if target_id not in visited:
                        visited.add(target_id)
                        next_frontier.add(target_id)
        frontier = next_frontier
    return {
        "schema_version": "knowledge-hub.context-graph.v1",
        "derived": True,
        "authoritative": False,
        "seed_ids": list(seed_ids),
        "node_ids": sorted(visited),
        "edges": edges,
    }


def compile_context(
    root: pathlib.Path,
    query: str,
    *,
    agent_id: str = DEFAULT_AGENT,
    task_type: str = "general",
    scope_refs: Sequence[str] = (),
    limit: int = 8,
    as_of: str = "",
) -> Dict[str, Any]:
    require_capability(root, agent_id, "knowledge.context")
    profile = agent_profile(root, agent_id)
    result = hybrid_search(
        root,
        query,
        limit=limit,
        profile_id=str(profile.get("retrieval_profile", DEFAULT_PROFILE)),
        knowledge_scopes=tuple(profile.get("knowledge_scopes", [])),
        as_of=as_of,
    )
    evidence = build_evidence_pack(root, query, limit=max(limit, 8), scope_refs=scope_refs)
    seeds = [str(row.get("id", "")) for row in result["results"][:5]]
    return {
        "schema_version": "knowledge-hub.context-compiler.v1",
        "status": "pass",
        "read_only": True,
        "query": query,
        "task_type": task_type,
        "agent": {
            "id": agent_id,
            "role": profile.get("role", ""),
            "retrieval_profile": profile.get("retrieval_profile", DEFAULT_PROFILE),
        },
        "retrieval": result,
        "evidence_pack": evidence,
        "context_graph": context_graph(root, seeds, hops=1),
        "authority_contract": {
            "evidence_pack_controls_constraints": True,
            "hybrid_ranking_can_promote_lifecycle": False,
            "graph_can_promote_lifecycle": False,
            "memory_can_promote_lifecycle": False,
        },
    }


def memory_candidate(
    agent_id: str, level: str, summary: str, source_refs: Sequence[str] = ()
) -> Dict[str, Any]:
    if level not in MEMORY_LEVELS:
        raise KnowledgeHubError("invalid memory level")
    if not str(summary).strip() or len(summary) > 4096:
        raise KnowledgeHubError("memory summary must be non-empty and bounded")
    durable = level in {"semantic", "procedural", "policy"}
    return {
        "schema_version": "knowledge-hub.memory-candidate.v1",
        "status": "candidate",
        "agent_id": agent_id,
        "level": level,
        "summary": summary,
        "source_refs": [str(v) for v in source_refs][:32],
        "durable": durable,
        "canonical_write_permitted": False,
        "promotion_required": durable,
        "target": "reviewing" if durable else "local-runtime-cache",
    }


def connector_catalog(root: pathlib.Path) -> Dict[str, Any]:
    return {
        "schema_version": "knowledge-hub.connector-catalog.v1",
        "connectors": _rows(root, "connectors"),
        "live_sync_implicitly_authorized": False,
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
    if not str(task).strip() or len(task) > 8192:
        raise KnowledgeHubError("A2A task must be non-empty and bounded")
    agent_profile(root, from_agent)
    target = agent_profile(root, to_agent)
    catalog = capability_catalog(root)
    target_caps = {str(v) for v in target.get("capabilities", [])}
    requested = {str(v) for v in requested_capabilities}
    unsupported = sorted(requested - target_caps)
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
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(str(path), flags, 0o600)
    try:
        os.write(
            descriptor,
            (json.dumps(dict(row), ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"),
        )
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
    if not query or len(query) > MAX_QUERY_CHARS:
        raise KnowledgeHubError("feedback query must be non-empty and bounded")
    row = {
        "schema_version": "knowledge-hub.feedback.v2",
        "recorded_at": utc_timestamp(),
        "agent_id": agent_id,
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "raw_query_stored": False,
        "outcome": outcome,
        "selected_id": selected_id,
        "selected_rank": max(0, int(selected_rank)),
        "candidate_ids": [str(v) for v in candidate_ids][:20],
        "retrieval_profile": profile_id,
    }
    _append_jsonl(_cache(root) / "feedback.jsonl", row)
    return {"status": "recorded", "record": row}


def _feedback(root: pathlib.Path, profile_id: str) -> List[Dict[str, Any]]:
    path = root / ".cache" / "knowledge-hub" / "runtime-v3" / "feedback.jsonl"
    if not path.exists():
        return []
    return [
        row for row in load_jsonl(path, maximum_bytes=16 * 1024 * 1024)
        if row.get("retrieval_profile") == profile_id
    ]


def adaptive_retrieval_proposal(
    root: pathlib.Path, profile_id: str = DEFAULT_PROFILE
) -> Dict[str, Any]:
    weights = dict(retrieval_profile(root, profile_id)["weights"])
    rows = _feedback(root, profile_id)
    counts = {key: 0 for key in FEEDBACK_OUTCOMES}
    for row in rows:
        if row.get("outcome") in counts:
            counts[str(row["outcome"])] += 1
    proposed, reasons, total_count = dict(weights), [], len(rows)
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
    proposed = {key: round(value / norm, 6) for key, value in proposed.items()}
    return {
        "schema_version": "knowledge-hub.adaptive-retrieval-proposal.v1",
        "status": "proposal" if reasons else "no-change",
        "profile_id": profile_id,
        "sample_count": total_count,
        "current_weights": weights,
        "proposed_weights": proposed,
        "reasons": reasons,
        "auto_apply": False,
        "human_review_required": True,
    }


def execution_receipt(
    agent_id: str, action: str, verdict: str, evidence_ids: Sequence[str] = ()
) -> Dict[str, Any]:
    row = {
        "schema_version": "knowledge-hub.execution-receipt.v1",
        "timestamp": utc_timestamp(),
        "agent_id": agent_id,
        "action": str(action)[:4096],
        "verdict": str(verdict)[:64],
        "evidence_ids": [str(v) for v in evidence_ids][:64],
        "canonical_state_changed": False,
    }
    row["receipt_sha256"] = hashlib.sha256(
        json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return row


def trace_projection(
    root: pathlib.Path, agent_id: str, operation: str, query: str = ""
) -> Dict[str, Any]:
    settings = config(root).get("observability", {})
    event = {
        "schema_version": "knowledge-hub.trace.v1",
        "timestamp": utc_timestamp(),
        "agent_id": agent_id,
        "operation": operation,
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest() if query else "",
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
    stale, evidence_gaps = [], []
    titles: MutableMapping[str, List[str]] = {}
    for item in registry_items(root):
        item_id = str(item.get("id", ""))
        if not item_id:
            continue
        review_after = _date(item.get("review_after"))
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
    root: pathlib.Path, *, profile_id: str = DEFAULT_PROFILE, as_of: str = ""
) -> Dict[str, Any]:
    adaptive = adaptive_retrieval_proposal(root, profile_id)
    steward = steward_audit(root, as_of=as_of)
    proposals = list(steward["proposals"])
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


def runtime_health(root: pathlib.Path) -> Dict[str, Any]:
    value = config(root)
    return {
        "schema_version": "knowledge-hub.runtime.v3",
        "status": "pass",
        "protocols": {"mcp": MCP_PROTOCOL_VERSION, "a2a": A2A_PROTOCOL_VERSION},
        "agent_count": len(value.get("agents", [])),
        "retrieval_profile_count": len(value.get("retrieval_profiles", [])),
        "authority": {
            "canonical": "Markdown + registry",
            "derived_planes_are_authoritative": False,
        },
    }


def api_dispatch(
    root: pathlib.Path,
    operation: str,
    payload: Mapping[str, Any],
    *,
    agent_id: str = DEFAULT_AGENT,
    enable_local_write: bool = False,
) -> Dict[str, Any]:
    op = operation.strip().lower()
    if op == "health":
        return runtime_health(root)
    if op == "capabilities":
        return {"agent": agent_profile(root, agent_id), "catalog": list(capability_catalog(root).values())}
    if op == "search":
        require_capability(root, agent_id, "knowledge.search")
        profile = agent_profile(root, agent_id)
        return hybrid_search(
            root,
            str(payload.get("query", "")),
            limit=int(payload.get("limit", 20)),
            profile_id=str(profile.get("retrieval_profile", DEFAULT_PROFILE)),
            knowledge_scopes=tuple(profile.get("knowledge_scopes", [])),
            as_of=str(payload.get("as_of", "")),
        )
    if op == "context":
        return compile_context(
            root,
            str(payload.get("query", "")),
            agent_id=agent_id,
            task_type=str(payload.get("task_type", "general")),
            scope_refs=tuple(payload.get("scope_refs", [])),
            limit=int(payload.get("limit", 8)),
            as_of=str(payload.get("as_of", "")),
        )
    if op == "evidence-pack":
        require_capability(root, agent_id, "knowledge.evidence-pack")
        return build_evidence_pack(
            root,
            str(payload.get("query", "")),
            limit=int(payload.get("limit", 20)),
            scope_refs=tuple(payload.get("scope_refs", [])),
        )
    if op == "action-check":
        require_capability(root, agent_id, "knowledge.action-check")
        return check_action(
            root,
            str(payload.get("task", "")),
            str(payload.get("candidate", "")),
            scope_refs=tuple(payload.get("scope_refs", [])),
        )
    if op == "feedback":
        if not enable_local_write:
            raise KnowledgeHubError("local write API is disabled")
        return record_feedback(
            root,
            agent_id,
            str(payload.get("query", "")),
            str(payload.get("outcome", "")),
            selected_id=str(payload.get("selected_id", "")),
            selected_rank=int(payload.get("selected_rank", 0)),
            candidate_ids=tuple(payload.get("candidate_ids", [])),
            profile_id=str(payload.get("profile_id", DEFAULT_PROFILE)),
        )
    if op == "memory-candidate":
        require_capability(root, agent_id, "memory.candidate")
        return memory_candidate(
            agent_id,
            str(payload.get("level", "")),
            str(payload.get("summary", "")),
            tuple(payload.get("source_refs", [])),
        )
    if op == "steward-audit":
        require_capability(root, agent_id, "knowledge.steward.audit")
        return steward_audit(root, as_of=str(payload.get("as_of", "")))
    if op == "adaptive-retrieval":
        require_capability(root, agent_id, "knowledge.retrieval.propose")
        return adaptive_retrieval_proposal(root, str(payload.get("profile_id", DEFAULT_PROFILE)))
    if op == "improvement-plan":
        require_capability(root, agent_id, "knowledge.improvement.plan")
        return improvement_plan(
            root,
            profile_id=str(payload.get("profile_id", DEFAULT_PROFILE)),
            as_of=str(payload.get("as_of", "")),
        )
    if op == "a2a-card":
        return agent_card(root, str(payload.get("agent_id", agent_id)))
    if op == "a2a-preflight":
        require_capability(root, agent_id, "a2a.preflight")
        return a2a_preflight(
            root,
            agent_id,
            str(payload.get("to_agent", "")),
            str(payload.get("task", "")),
            tuple(payload.get("requested_capabilities", [])),
        )
    raise KnowledgeHubError("unsupported Context API operation: {}".format(operation))


def mcp_tools() -> List[Dict[str, Any]]:
    def schema(properties, required):
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }
    return [
        {
            "name": "knowledge_search",
            "description": "Hybrid governed Knowledge Hub search.",
            "inputSchema": schema(
                {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 100}},
                ["query"],
            ),
        },
        {
            "name": "knowledge_context",
            "description": "Compile agent-scoped context and evidence.",
            "inputSchema": schema(
                {
                    "query": {"type": "string"},
                    "task_type": {"type": "string"},
                    "scope_refs": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                ["query"],
            ),
        },
        {
            "name": "knowledge_evidence_pack",
            "description": "Build authoritative/provisional EvidencePack.",
            "inputSchema": schema({"query": {"type": "string"}}, ["query"]),
        },
        {
            "name": "knowledge_action_check",
            "description": "Deterministic fail-closed action preflight.",
            "inputSchema": schema(
                {"task": {"type": "string"}, "candidate": {"type": "string"}},
                ["task", "candidate"],
            ),
        },
    ]


def handle_mcp_request(
    root: pathlib.Path, request: Mapping[str, Any], *, agent_id: str = DEFAULT_AGENT
) -> Optional[Dict[str, Any]]:
    if request.get("jsonrpc") != "2.0":
        raise KnowledgeHubError("MCP request must use JSON-RPC 2.0")
    method, request_id = str(request.get("method", "")), request.get("id")
    if method.startswith("notifications/"):
        return None
    if method == "ping":
        result: Any = {}
    elif method == "initialize":
        result = {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": "knowledge-hub", "version": "3.0.0"},
            "stateless": True,
        }
    elif method == "tools/list":
        result = {"tools": mcp_tools()}
    elif method == "resources/list":
        result = {
            "resources": [
                {"uri": "knowledge://health", "name": "Knowledge Hub health", "mimeType": "application/json"},
                {"uri": "knowledge://agents", "name": "Knowledge Hub agents", "mimeType": "application/json"},
            ]
        }
    elif method == "resources/read":
        params = request.get("params", {})
        uri = str(params.get("uri", "")) if isinstance(params, Mapping) else ""
        if uri == "knowledge://health":
            value = runtime_health(root)
        elif uri == "knowledge://agents":
            value = {"agents": _rows(root, "agents")}
        else:
            raise KnowledgeHubError("unsupported MCP resource: {}".format(uri))
        result = {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(value, ensure_ascii=False)}]}
    elif method == "tools/call":
        params = request.get("params", {})
        if not isinstance(params, Mapping) or not isinstance(params.get("arguments", {}), Mapping):
            raise KnowledgeHubError("invalid MCP tools/call params")
        name, args = str(params.get("name", "")), params.get("arguments", {})
        operation = {
            "knowledge_search": "search",
            "knowledge_context": "context",
            "knowledge_evidence_pack": "evidence-pack",
            "knowledge_action_check": "action-check",
        }.get(name)
        if not operation:
            raise KnowledgeHubError("unsupported MCP tool: {}".format(name))
        value = api_dispatch(root, operation, args, agent_id=agent_id)
        result = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}], "isError": False}
    else:
        raise KnowledgeHubError("unsupported MCP method: {}".format(method))
    return {"jsonrpc": "2.0", "id": request_id, "result": result}
