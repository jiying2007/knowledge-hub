import json

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.mcp_v3_server import _process
from tools.codex_assets.knowledge_hub.protocol_conformance import (
    MCP_CLIENT_CAPABILITIES_META_KEY,
    MCP_CLIENT_INFO_META_KEY,
    MCP_PROTOCOL_META_KEY,
    MCP_SERVER_INFO_META_KEY,
)
from tools.codex_assets.knowledge_hub.runtime_v3_contracts import MCP_PROTOCOL_VERSION


def _native_request(method: str):
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": {
                "_meta": {
                    MCP_PROTOCOL_META_KEY: MCP_PROTOCOL_VERSION,
                    MCP_CLIENT_CAPABILITIES_META_KEY: {},
                    MCP_CLIENT_INFO_META_KEY: {
                        "name": "knowledge-hub-stdio-test",
                        "version": "1.0.0",
                    },
                }
            },
        }
    )


def test_mcp_stdio_defaults_to_native_stateless_profile():
    response = _process(
        repository_root(),
        _native_request("tools/list"),
        "knowledge-reader",
    )
    result = response["result"]
    assert result["resultType"] == "complete"
    assert result["_meta"][MCP_SERVER_INFO_META_KEY]["name"] == "knowledge-hub"
    assert result["tools"]


def test_mcp_stdio_default_rejects_legacy_initialize():
    response = _process(
        repository_root(),
        _native_request("initialize"),
        "knowledge-reader",
    )
    assert response["error"]["code"] == -32601
    assert "unsupported MCP native method: initialize" in response["error"]["message"]


def test_mcp_stdio_legacy_initialize_requires_explicit_opt_in():
    response = _process(
        repository_root(),
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
        "knowledge-reader",
        legacy_compat=True,
    )
    assert response["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION


def test_mcp_notifications_remain_no_response_in_both_profiles():
    raw = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {
                "_meta": {
                    MCP_PROTOCOL_META_KEY: MCP_PROTOCOL_VERSION,
                    MCP_CLIENT_CAPABILITIES_META_KEY: {},
                }
            },
        }
    )
    assert _process(repository_root(), raw, "knowledge-reader") is None
    assert _process(repository_root(), raw, "knowledge-reader", legacy_compat=True) is None


def test_duplicate_context_api_runtime_alias_is_retired():
    root = repository_root()
    assert (root / "tools/runtime/knowledge-runtime.sh").is_file()
    assert not (root / "tools/runtime/knowledge-context-api.sh").exists()
