"""Knowledge Runtime v3 context fabric.

Canonical Markdown + registry remain authoritative. Semantic ranking, graph,
memory, feedback, A2A and self-improvement are derived, report-only, or private
runtime evidence unless an existing governed promotion path explicitly changes
canonical state.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import pathlib
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from .agent_runtime import build_evidence_pack, check_action
from .common import KnowledgeHubError, registry_items, resolve_today
from .runtime_v3_contracts import (
    A2A_PROTOCOL_VERSION,
    CONFIG_PATH,
    DEFAULT_AGENT,
    DEFAULT_PROFILE,
    MCP_PROTOCOL_VERSION,
    agent_profile,
    capability_catalog,
    config,
    require_capability,
    retrieval_profile,
    rows as _rows,
)
from .runtime_v3_governance import (
    a2a_preflight,
    adaptive_retrieval_proposal,
    agent_card,
    connector_catalog,
    connector_envelope,
    execution_receipt,
    improvement_plan,
    memory_candidate,
    record_execution_receipt,
    record_feedback,
    steward_audit,
    trace_projection,
)
from .search import SearchFilters, SearchIndex, search, search_tokens

MAX_QUERY_CHARS = 4096
MAX_RESULTS = 100
MAX_GRAPH_HOPS = 2
MAX_SEMANTIC_ITEMS = 5000
VECTOR_DIMS = 128
SERVICEABLE = {"active", "reviewing", "draft"}


def _sequence(
    value: Any,
    label: str,
    *,
    maximum: int = 64,
    maximum_length: int = 2048,
) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KnowledgeHubError("{} must be a sequence".format(label))
    if len(value) > maximum:
        raise KnowledgeHubError("{} exceeds {} values".format(label, maximum))
    result = []
    for row in value:
        text = str(row).strip()
        if not text or len(text) > maximum_length:
            raise KnowledgeHubError("{} contains an invalid value".format(label))
        result.append(text)
    return tuple(result)


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
    valid_from = _date(item.get("valid_from"))
    valid_to = _date(item.get("valid_to"))
    if valid_from and today < valid_from:
        return False
    if valid_to and today > valid_to:
        return False
    if not scopes:
        return True
    domain = str(item.get("domain", ""))
    path = str(item.get("path", ""))
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


def _semantic_text(item: Mapping[str, Any]) -> str:
    """Return bounded governed metadata for the zero-dependency semantic lane.

    Full body recall remains the FTS/BM25 lane. Avoiding a full body read for
    every item keeps semantic discovery predictable and makes this feature-hash
    lane a rebuildable augmentation rather than a second corpus.
    """

    return "\n".join(
        (
            str(item.get("title", "")),
            str(item.get("summary_zh", "")),
            " ".join(str(value) for value in item.get("tags", [])),
            str(item.get("domain", "")),
            str(item.get("path", "")),
        )
    )


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
        raise KnowledgeHubError(
            "query must be non-empty and <= {} chars".format(MAX_QUERY_CHARS)
        )
    if not 1 <= int(limit) <= MAX_RESULTS:
        raise KnowledgeHubError("limit must be between 1 and {}".format(MAX_RESULTS))
    scopes = _sequence(knowledge_scopes, "knowledge_scopes", maximum=64)
    today, source = resolve_today(as_of)
    profile = retrieval_profile(root, profile_id)
    weights = profile["weights"]
    items = [
        row for row in registry_items(root) if _eligible(row, today, scopes)
    ]
    if len(items) > MAX_SEMANTIC_ITEMS:
        raise KnowledgeHubError(
            "semantic candidate corpus exceeds explicit {} item budget".format(
                MAX_SEMANTIC_ITEMS
            )
        )
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
            lexical_scores.get(item_id, 0.0),
            float(row.get("score", 0.0) or 0.0),
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
                    query_vector,
                    _vector(search_tokens(_semantic_text(item))),
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
                "score_components": {
                    key: round(value, 6) for key, value in parts.items()
                },
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
        "semantic_corpus_count": len(items),
        "semantic_lane": "governed-metadata-feature-hash-v1",
        "authority_contract": {
            "derived_ranking_is_authority": False,
            "registry_lifecycle_remains_authoritative": True,
        },
    }


def context_graph(
    root: pathlib.Path, seed_ids: Sequence[str], *, hops: int = 1
) -> Dict[str, Any]:
    if not 0 <= hops <= MAX_GRAPH_HOPS:
        raise KnowledgeHubError(
            "graph hops must be between 0 and {}".format(MAX_GRAPH_HOPS)
        )
    seeds = _sequence(seed_ids, "seed_ids", maximum=100)
    by_id = {
        str(row.get("id", "")): row
        for row in registry_items(root)
        if row.get("id")
    }
    frontier = set(seeds) & set(by_id)
    visited = set(frontier)
    edges = []
    for _ in range(hops):
        next_frontier: Set[str] = set()
        for item_id in sorted(frontier):
            contract = by_id[item_id].get("agent_contract", {})
            relations = (
                contract.get("relations", {})
                if isinstance(contract, Mapping)
                else {}
            )
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
                        {
                            "source_id": item_id,
                            "relation": str(relation),
                            "target_id": target_id,
                        }
                    )
                    if target_id not in visited:
                        visited.add(target_id)
                        next_frontier.add(target_id)
        frontier = next_frontier
    return {
        "schema_version": "knowledge-hub.context-graph.v1",
        "derived": True,
        "authoritative": False,
        "seed_ids": list(seeds),
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
    scopes = _sequence(scope_refs, "scope_refs", maximum=32)
    result = hybrid_search(
        root,
        query,
        limit=limit,
        profile_id=str(profile.get("retrieval_profile", DEFAULT_PROFILE)),
        knowledge_scopes=_sequence(
            profile.get("knowledge_scopes", []),
            "agent knowledge_scopes",
            maximum=64,
        ),
        as_of=as_of,
    )
    evidence = build_evidence_pack(
        root,
        query,
        limit=max(limit, 8),
        scope_refs=scopes,
    )
    seeds = [str(row.get("id", "")) for row in result["results"][:5]]
    return {
        "schema_version": "knowledge-hub.context-compiler.v1",
        "status": "pass",
        "read_only": True,
        "query": query,
        "task_type": str(task_type)[:128],
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


def runtime_health(root: pathlib.Path) -> Dict[str, Any]:
    value = config(root)
    return {
        "schema_version": "knowledge-hub.runtime.v3",
        "status": "pass",
        "protocols": {
            "mcp": MCP_PROTOCOL_VERSION,
            "a2a": A2A_PROTOCOL_VERSION,
        },
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
    if not isinstance(payload, Mapping):
        raise KnowledgeHubError("Context API payload must be an object")
    op = operation.strip().lower()
    if op == "health":
        return runtime_health(root)
    if op == "capabilities":
        return {
            "agent": agent_profile(root, agent_id),
            "catalog": list(capability_catalog(root).values()),
        }
    if op == "search":
        require_capability(root, agent_id, "knowledge.search")
        profile = agent_profile(root, agent_id)
        return hybrid_search(
            root,
            str(payload.get("query", "")),
            limit=int(payload.get("limit", 20)),
            profile_id=str(profile.get("retrieval_profile", DEFAULT_PROFILE)),
            knowledge_scopes=_sequence(
                profile.get("knowledge_scopes", []),
                "agent knowledge_scopes",
            ),
            as_of=str(payload.get("as_of", "")),
        )
    if op == "context":
        return compile_context(
            root,
            str(payload.get("query", "")),
            agent_id=agent_id,
            task_type=str(payload.get("task_type", "general")),
            scope_refs=_sequence(payload.get("scope_refs", []), "scope_refs", maximum=32),
            limit=int(payload.get("limit", 8)),
            as_of=str(payload.get("as_of", "")),
        )
    if op == "evidence-pack":
        require_capability(root, agent_id, "knowledge.evidence-pack")
        return build_evidence_pack(
            root,
            str(payload.get("query", "")),
            limit=int(payload.get("limit", 20)),
            scope_refs=_sequence(payload.get("scope_refs", []), "scope_refs", maximum=32),
        )
    if op == "action-check":
        require_capability(root, agent_id, "knowledge.action-check")
        return check_action(
            root,
            str(payload.get("task", "")),
            str(payload.get("candidate", "")),
            scope_refs=_sequence(payload.get("scope_refs", []), "scope_refs", maximum=32),
        )
    if op in {"feedback", "execution-receipt"} and not enable_local_write:
        raise KnowledgeHubError("local write API is disabled")
    if op == "feedback":
        return record_feedback(
            root,
            agent_id,
            str(payload.get("query", "")),
            str(payload.get("outcome", "")),
            selected_id=str(payload.get("selected_id", "")),
            selected_rank=int(payload.get("selected_rank", 0)),
            candidate_ids=_sequence(
                payload.get("candidate_ids", []),
                "candidate_ids",
                maximum=20,
            ),
            profile_id=str(payload.get("profile_id", DEFAULT_PROFILE)),
        )
    if op == "execution-receipt":
        return record_execution_receipt(
            root,
            agent_id,
            str(payload.get("action", "")),
            str(payload.get("verdict", "")),
            _sequence(payload.get("evidence_ids", []), "evidence_ids", maximum=64),
        )
    if op == "memory-candidate":
        require_capability(root, agent_id, "memory.candidate")
        return memory_candidate(
            agent_id,
            str(payload.get("level", "")),
            str(payload.get("summary", "")),
            _sequence(payload.get("source_refs", []), "source_refs", maximum=32),
        )
    if op == "connector-envelope":
        return connector_envelope(
            root,
            str(payload.get("connector_id", "")),
            str(payload.get("object_id", "")),
            version=str(payload.get("version", "")),
            source_uri=str(payload.get("source_uri", "")),
            visibility=str(payload.get("visibility", "team-internal")),
            content_type=str(payload.get("content_type", "text/unknown")),
            acl=_sequence(payload.get("acl", []), "acl", maximum=64),
            content_sha256=str(payload.get("content_sha256", "")),
        )
    if op == "connectors":
        return connector_catalog(root)
    if op == "steward-audit":
        require_capability(root, agent_id, "knowledge.steward.audit")
        return steward_audit(root, as_of=str(payload.get("as_of", "")))
    if op == "adaptive-retrieval":
        require_capability(root, agent_id, "knowledge.retrieval.propose")
        return adaptive_retrieval_proposal(
            root, str(payload.get("profile_id", DEFAULT_PROFILE))
        )
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
            _sequence(
                payload.get("requested_capabilities", []),
                "requested_capabilities",
                maximum=32,
            ),
        )
    raise KnowledgeHubError(
        "unsupported Context API operation: {}".format(operation)
    )


def _mcp_schema(properties: Mapping[str, Any], required: Sequence[str]) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": dict(properties),
        "required": list(required),
        "additionalProperties": False,
    }


def mcp_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": "knowledge_search",
            "description": "Hybrid governed Knowledge Hub search.",
            "inputSchema": _mcp_schema(
                {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                ["query"],
            ),
        },
        {
            "name": "knowledge_context",
            "description": "Compile agent-scoped context and evidence.",
            "inputSchema": _mcp_schema(
                {
                    "query": {"type": "string"},
                    "task_type": {"type": "string"},
                    "scope_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                ["query"],
            ),
        },
        {
            "name": "knowledge_evidence_pack",
            "description": "Build authoritative/provisional EvidencePack.",
            "inputSchema": _mcp_schema(
                {"query": {"type": "string"}}, ["query"]
            ),
        },
        {
            "name": "knowledge_action_check",
            "description": "Deterministic fail-closed action preflight.",
            "inputSchema": _mcp_schema(
                {
                    "task": {"type": "string"},
                    "candidate": {"type": "string"},
                },
                ["task", "candidate"],
            ),
        },
    ]


def handle_mcp_request(
    root: pathlib.Path,
    request: Mapping[str, Any],
    *,
    agent_id: str = DEFAULT_AGENT,
) -> Optional[Dict[str, Any]]:
    if request.get("jsonrpc") != "2.0":
        raise KnowledgeHubError("MCP request must use JSON-RPC 2.0")
    method = str(request.get("method", ""))
    request_id = request.get("id")
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
                {
                    "uri": "knowledge://health",
                    "name": "Knowledge Hub health",
                    "mimeType": "application/json",
                },
                {
                    "uri": "knowledge://agents",
                    "name": "Knowledge Hub agents",
                    "mimeType": "application/json",
                },
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
        result = {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(value, ensure_ascii=False),
                }
            ]
        }
    elif method == "tools/call":
        params = request.get("params", {})
        if not isinstance(params, Mapping) or not isinstance(
            params.get("arguments", {}), Mapping
        ):
            raise KnowledgeHubError("invalid MCP tools/call params")
        name = str(params.get("name", ""))
        args = params.get("arguments", {})
        operation = {
            "knowledge_search": "search",
            "knowledge_context": "context",
            "knowledge_evidence_pack": "evidence-pack",
            "knowledge_action_check": "action-check",
        }.get(name)
        if not operation:
            raise KnowledgeHubError("unsupported MCP tool: {}".format(name))
        value = api_dispatch(root, operation, args, agent_id=agent_id)
        result = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(value, ensure_ascii=False),
                }
            ],
            "isError": False,
        }
    else:
        raise KnowledgeHubError("unsupported MCP method: {}".format(method))
    return {"jsonrpc": "2.0", "id": request_id, "result": result}
