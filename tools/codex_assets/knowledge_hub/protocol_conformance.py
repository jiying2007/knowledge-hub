"""P5 protocol conformance surfaces for MCP 2026-07-28 and A2A 1.0.

The Knowledge Hub remains a context/evidence provider. The A2A surface advertises
provider capabilities but never implements task execution or ownership.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping

from .common import KnowledgeHubError
from .runtime_v3 import api_dispatch, mcp_tools, runtime_health
from .runtime_v3_contracts import (
    A2A_PROTOCOL_VERSION,
    DEFAULT_AGENT,
    MCP_PROTOCOL_VERSION,
    agent_profile,
    rows,
)

MCP_NATIVE_PROFILE = "stateless-2026-07-28"
A2A_PROVIDER_PROFILE = "provider-card-1.0"


def mcp_native_capabilities() -> Dict[str, Any]:
    return {
        "protocol_version": MCP_PROTOCOL_VERSION,
        "profile": MCP_NATIVE_PROFILE,
        "stateless": True,
        "handshake_required": False,
        "sessions_required": False,
        "tools": True,
        "resources": True,
        "tasks_extension": False,
        "network_auth_required_if_remote": True,
        "legacy_initialize_supported_by_compat_adapter": True,
    }


def _request_version(request: Mapping[str, Any]) -> str:
    meta = request.get("_meta", {})
    return str(meta.get("protocolVersion", "")).strip() if isinstance(meta, Mapping) else ""


def _resource_list() -> Dict[str, Any]:
    return {
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
        ],
        "_meta": {"cacheControl": {"maxAgeSeconds": 30}},
    }


def _resource_read(root, request: Mapping[str, Any]) -> Dict[str, Any]:
    params = request.get("params", {})
    if not isinstance(params, Mapping):
        raise KnowledgeHubError("invalid MCP resources/read params")
    uri = str(params.get("uri", ""))
    if uri == "knowledge://health":
        value: Any = runtime_health(root)
    elif uri == "knowledge://agents":
        value = {"agents": rows(root, "agents")}
    else:
        raise KnowledgeHubError("native MCP resource not available: {}".format(uri))
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(value, ensure_ascii=False),
            }
        ]
    }


def _tool_call(root, request: Mapping[str, Any], agent_id: str) -> Dict[str, Any]:
    params = request.get("params", {})
    if not isinstance(params, Mapping):
        raise KnowledgeHubError("invalid MCP tools/call params")
    arguments = params.get("arguments", {})
    if not isinstance(arguments, Mapping):
        raise KnowledgeHubError("MCP tool arguments must be an object")
    operation = {
        "knowledge_search": "search",
        "knowledge_context": "context",
        "knowledge_evidence_pack": "evidence-pack",
        "knowledge_action_check": "action-check",
    }.get(str(params.get("name", "")))
    if not operation:
        raise KnowledgeHubError("unsupported MCP tool")
    value = api_dispatch(root, operation, arguments, agent_id=agent_id)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(value, ensure_ascii=False),
            }
        ],
        "isError": False,
    }


def _dispatch_native(root, request: Mapping[str, Any], agent_id: str) -> Any:
    method = str(request.get("method", ""))
    if method == "initialize":
        raise KnowledgeHubError("MCP 2026-07-28 native profile has no initialize handshake")
    if method == "ping":
        return {}
    if method == "tools/list":
        return {
            "tools": mcp_tools(),
            "_meta": {"cacheControl": {"maxAgeSeconds": 60}},
        }
    if method == "resources/list":
        return _resource_list()
    if method == "resources/read":
        return _resource_read(root, request)
    if method == "tools/call":
        return _tool_call(root, request, agent_id)
    raise KnowledgeHubError("unsupported MCP native method: {}".format(method))


def handle_mcp_stateless_request(
    root,
    request: Mapping[str, Any],
    *,
    agent_id: str = DEFAULT_AGENT,
) -> Dict[str, Any]:
    if not isinstance(request, Mapping):
        raise KnowledgeHubError("MCP request must be an object")
    if request.get("jsonrpc") != "2.0":
        raise KnowledgeHubError("MCP request must use JSON-RPC 2.0")
    if _request_version(request) != MCP_PROTOCOL_VERSION:
        raise KnowledgeHubError(
            "MCP stateless request must self-describe protocol version {}".format(
                MCP_PROTOCOL_VERSION
            )
        )
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": _dispatch_native(root, request, agent_id),
        "_meta": {"protocolVersion": MCP_PROTOCOL_VERSION, "stateless": True},
    }


def a2a_provider_card(
    root,
    agent_id: str,
    *,
    base_url: str = "local://knowledge-hub",
) -> Dict[str, Any]:
    profile = agent_profile(root, agent_id)
    if not base_url or len(base_url) > 2048:
        raise KnowledgeHubError("A2A base_url must be non-empty and bounded")
    return {
        "name": profile.get("name", agent_id),
        "description": profile.get("description", ""),
        "version": A2A_PROTOCOL_VERSION,
        "supportedInterfaces": [
            {
                "url": base_url,
                "protocolBinding": "JSONRPC",
                "protocolVersion": A2A_PROTOCOL_VERSION,
            }
        ],
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
        },
        "skills": [
            {
                "id": str(skill),
                "name": str(skill),
                "description": "Knowledge Hub provider-side skill",
                "tags": ["knowledge", "context", "evidence"],
            }
            for skill in profile.get("skills", [])
        ],
        "provider": {"organization": "knowledge-hub", "url": base_url},
        "extensions": {
            "knowledgeHub": {
                "taskExecution": False,
                "canonicalWritePermitted": False,
                "agentId": agent_id,
                "profile": A2A_PROVIDER_PROFILE,
            }
        },
    }


def protocol_conformance_report(root, *, agent_id: str = DEFAULT_AGENT) -> Dict[str, Any]:
    profile = agent_profile(root, agent_id)
    return {
        "schema_version": "knowledge-hub.protocol-conformance.v1",
        "status": "pass",
        "mcp": {
            "declared": MCP_PROTOCOL_VERSION,
            "native_profile": MCP_NATIVE_PROFILE,
            "native_stateless": True,
            "legacy_compatibility_adapter": True,
            "legacy_initialize_is_native": False,
            "official_conformance_evidence": "external-required",
        },
        "a2a": {
            "declared": A2A_PROTOCOL_VERSION,
            "provider_card_profile": A2A_PROVIDER_PROFILE,
            "task_server_implemented_here": False,
            "execution_plane_expected_elsewhere": True,
            "official_tck_if_task_server": "external-required",
        },
        "agent_id": agent_id,
        "agent_capability_count": len(profile.get("capabilities", [])),
    }
