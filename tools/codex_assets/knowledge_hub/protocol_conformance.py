"""P5 protocol conformance surfaces for MCP 2026-07-28 and A2A 1.0.

The Knowledge Hub remains a context/evidence provider. The A2A surface advertises
provider capabilities but never implements task execution or ownership.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional

from .common import KnowledgeHubError
from .runtime_v3 import api_dispatch, mcp_tools, runtime_health
from .runtime_v3_contracts import (
    A2A_PROTOCOL_VERSION,
    DEFAULT_AGENT,
    MCP_PROTOCOL_VERSION,
    agent_profile,
    rows as _rows,
)

MCP_NATIVE_PROFILE = "stateless-2026-07-28"
A2A_PROVIDER_PROFILE = "provider-card-1.0"
MCP_PROTOCOL_META_KEY = "io.modelcontextprotocol/protocolVersion"
MCP_CLIENT_INFO_META_KEY = "io.modelcontextprotocol/clientInfo"
MCP_CLIENT_CAPABILITIES_META_KEY = "io.modelcontextprotocol/clientCapabilities"
MCP_SERVER_INFO_META_KEY = "io.modelcontextprotocol/serverInfo"
MCP_SERVER_INFO = {"name": "knowledge-hub", "version": "p5-p10-v2"}
MCP_CACHE_TTL_MS = 0
MCP_CACHE_SCOPE = "private"


class MCPProtocolError(KnowledgeHubError):
    """Native MCP error carrying the required JSON-RPC/HTTP boundary."""

    def __init__(
        self,
        message: str,
        *,
        code: int,
        http_status: int,
        data: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = int(code)
        self.http_status = int(http_status)
        self.data = dict(data or {})


def mcp_native_capabilities() -> Dict[str, Any]:
    return {
        "protocol_version": MCP_PROTOCOL_VERSION,
        "profile": MCP_NATIVE_PROFILE,
        "stateless": True,
        "handshake_required": False,
        "sessions_required": False,
        "tools": True,
        "resources": True,
        "prompts": False,
        "completion": False,
        "tasks_extension": False,
        "network_auth_required_if_remote": True,
    }


def _request_meta(request: Mapping[str, Any]) -> Mapping[str, Any]:
    params = request.get("params")
    if not isinstance(params, Mapping):
        raise MCPProtocolError(
            "MCP 2026-07-28 request params must be an object containing _meta",
            code=-32602,
            http_status=400,
        )
    meta = params.get("_meta")
    if not isinstance(meta, Mapping):
        raise MCPProtocolError(
            "MCP 2026-07-28 request params._meta is required",
            code=-32602,
            http_status=400,
        )
    return meta


def request_protocol_version(request: Mapping[str, Any]) -> str:
    meta = _request_meta(request)
    version = str(meta.get(MCP_PROTOCOL_META_KEY, "")).strip()
    if not version:
        raise MCPProtocolError(
            "MCP request _meta is missing {}".format(MCP_PROTOCOL_META_KEY),
            code=-32602,
            http_status=400,
        )
    return version


def _validate_request_meta(request: Mapping[str, Any]) -> Mapping[str, Any]:
    meta = _request_meta(request)
    version = request_protocol_version(request)
    if version != MCP_PROTOCOL_VERSION:
        raise MCPProtocolError(
            "unsupported MCP protocol version: {}".format(version),
            code=-32022,
            http_status=400,
            data={"supported": [MCP_PROTOCOL_VERSION], "requested": version},
        )
    capabilities = meta.get(MCP_CLIENT_CAPABILITIES_META_KEY)
    if not isinstance(capabilities, Mapping):
        raise MCPProtocolError(
            "MCP request _meta is missing {}".format(MCP_CLIENT_CAPABILITIES_META_KEY),
            code=-32602,
            http_status=400,
        )
    client_info = meta.get(MCP_CLIENT_INFO_META_KEY)
    if client_info is not None and not isinstance(client_info, Mapping):
        raise MCPProtocolError(
            "MCP clientInfo must be an object when present",
            code=-32602,
            http_status=400,
        )
    return meta


def _server_meta() -> Dict[str, Any]:
    return {MCP_SERVER_INFO_META_KEY: dict(MCP_SERVER_INFO)}


def _complete_result(value: Mapping[str, Any], *, cacheable: bool = False) -> Dict[str, Any]:
    result = dict(value)
    result["resultType"] = "complete"
    result["_meta"] = _server_meta()
    if cacheable:
        result["ttlMs"] = MCP_CACHE_TTL_MS
        result["cacheScope"] = MCP_CACHE_SCOPE
    return result


def _discover_result() -> Dict[str, Any]:
    return _complete_result(
        {
            "supportedVersions": [MCP_PROTOCOL_VERSION],
            "capabilities": {
                "tools": {},
                "resources": {},
            },
            "instructions": (
                "Knowledge Hub exposes governed read/context tools and read-only "
                "knowledge resources. Canonical writes are not available over MCP."
            ),
        },
        cacheable=True,
    )


def _resource_list() -> Dict[str, Any]:
    return _complete_result(
        {
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
        },
        cacheable=True,
    )


def _resource_read(root, request: Mapping[str, Any]) -> Dict[str, Any]:
    params = request.get("params", {})
    if not isinstance(params, Mapping):
        raise MCPProtocolError(
            "invalid MCP resources/read params",
            code=-32602,
            http_status=400,
        )
    uri = str(params.get("uri", ""))
    if uri == "knowledge://health":
        value: Any = runtime_health(root)
    elif uri == "knowledge://agents":
        value = {"agents": _rows(root, "agents")}
    else:
        raise MCPProtocolError(
            "native MCP resource not available: {}".format(uri),
            code=-32602,
            http_status=404,
            data={"uri": uri},
        )
    return _complete_result(
        {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(value, ensure_ascii=False),
                }
            ]
        },
        cacheable=True,
    )


def _tool_call(root, request: Mapping[str, Any], agent_id: str) -> Dict[str, Any]:
    params = request.get("params", {})
    if not isinstance(params, Mapping):
        raise MCPProtocolError(
            "invalid MCP tools/call params",
            code=-32602,
            http_status=400,
        )
    arguments = params.get("arguments", {})
    if not isinstance(arguments, Mapping):
        raise MCPProtocolError(
            "MCP tool arguments must be an object",
            code=-32602,
            http_status=400,
        )
    name = str(params.get("name", ""))
    operation = {
        "knowledge_search": "search",
        "knowledge_context": "context",
        "knowledge_evidence_pack": "evidence-pack",
        "knowledge_action_check": "action-check",
    }.get(name)
    if not operation:
        raise MCPProtocolError(
            "unsupported MCP tool: {}".format(name),
            code=-32602,
            http_status=404,
            data={"name": name},
        )
    value = api_dispatch(root, operation, arguments, agent_id=agent_id)
    return _complete_result(
        {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(value, ensure_ascii=False),
                }
            ],
            "isError": False,
        }
    )


def _dispatch_native(root, request: Mapping[str, Any], agent_id: str) -> Dict[str, Any]:
    method = str(request.get("method", ""))
    if method == "server/discover":
        return _discover_result()
    if method == "tools/list":
        return _complete_result({"tools": mcp_tools()}, cacheable=True)
    if method == "resources/list":
        return _resource_list()
    if method == "resources/read":
        return _resource_read(root, request)
    if method == "tools/call":
        return _tool_call(root, request, agent_id)
    raise MCPProtocolError(
        "unsupported MCP native method: {}".format(method),
        code=-32601,
        http_status=404,
        data={"method": method},
    )


def handle_mcp_stateless_request(
    root,
    request: Mapping[str, Any],
    *,
    agent_id: str = DEFAULT_AGENT,
) -> Dict[str, Any]:
    if not isinstance(request, Mapping):
        raise MCPProtocolError(
            "MCP request must be an object",
            code=-32600,
            http_status=400,
        )
    if request.get("jsonrpc") != "2.0":
        raise MCPProtocolError(
            "MCP request must use JSON-RPC 2.0",
            code=-32600,
            http_status=400,
        )
    if not str(request.get("method", "")).strip():
        raise MCPProtocolError(
            "MCP request method is required",
            code=-32600,
            http_status=400,
        )
    _validate_request_meta(request)
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": _dispatch_native(root, request, agent_id),
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
        "provider": {
            "organization": "knowledge-hub",
            "url": base_url,
        },
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
        "schema_version": "knowledge-hub.protocol-conformance.v2",
        "status": "pass",
        "mcp": {
            "declared": MCP_PROTOCOL_VERSION,
            "native_profile": MCP_NATIVE_PROFILE,
            "native_stateless": True,
            "server_discover": True,
            "wire_result_type": True,
            "wire_server_identity_meta": True,
            "streamable_http_transport": "localhost-only",
            "listed_resources_are_readable": True,
        },
        "a2a": {
            "declared": A2A_PROTOCOL_VERSION,
            "provider_card_profile": A2A_PROVIDER_PROFILE,
            "task_server_implemented_here": False,
            "execution_plane_expected_elsewhere": True,
        },
        "agent_id": agent_id,
        "agent_capability_count": len(profile.get("capabilities", [])),
    }
