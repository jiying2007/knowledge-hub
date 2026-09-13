import json

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.protocol_conformance import (
    MCP_CLIENT_CAPABILITIES_META_KEY,
    MCP_CLIENT_INFO_META_KEY,
    MCP_PROTOCOL_META_KEY,
    handle_mcp_stateless_request,
)
from tools.codex_assets.knowledge_hub.runtime_v3_contracts import MCP_PROTOCOL_VERSION
from tools.codex_assets.knowledge_hub.temporal_graph import temporal_context_graph


def _request(method, params=None, request_id=1):
    value = dict(params or {})
    value["_meta"] = {
        MCP_PROTOCOL_META_KEY: MCP_PROTOCOL_VERSION,
        MCP_CLIENT_CAPABILITIES_META_KEY: {},
        MCP_CLIENT_INFO_META_KEY: {
            "name": "knowledge-hub-security-test",
            "version": "1.0.0",
        },
    }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": value,
    }


def test_mcp_native_every_listed_resource_is_readable():
    root = repository_root()
    listed = handle_mcp_stateless_request(root, _request("resources/list"))
    uris = [row["uri"] for row in listed["result"]["resources"]]

    assert "knowledge://health" in uris
    assert "knowledge://agents" in uris
    for index, uri in enumerate(uris, 10):
        response = handle_mcp_stateless_request(
            root,
            _request("resources/read", {"uri": uri}, request_id=index),
        )
        result = response["result"]
        assert result["resultType"] == "complete"
        assert result["ttlMs"] == 0
        assert result["cacheScope"] == "private"
        assert result["contents"][0]["uri"] == uri
        json.loads(result["contents"][0]["text"])


def _write_items(root):
    registry = root / "registry"
    registry.mkdir(parents=True)
    rows = [
        {
            "id": "public-a",
            "title": "Public A",
            "status": "active",
            "visibility": "team-internal",
            "owner": "team-owner",
            "domain": "projects/a",
            "path": "projects/a/current.md",
            "source": {},
            "tags": ["a"],
            "created_at": "2026-01-01",
            "updated_at": "2026-09-01",
            "agent_contract": {
                "relations": {"conflicts_with": ["acl-secret"]}
            },
        },
        {
            "id": "acl-secret",
            "title": "ACL secret",
            "status": "active",
            "visibility": "team-internal",
            "owner": "team-owner",
            "domain": "projects/secret",
            "path": "projects/secret/current.md",
            "source": {"acl": ["user:alice"]},
            "tags": ["secret"],
            "created_at": "2026-01-01",
            "updated_at": "2026-09-01",
        },
        {
            "id": "personal-alice",
            "title": "Alice private note",
            "status": "personal",
            "visibility": "personal-local",
            "owner": "user:alice",
            "domain": "notes/personal",
            "path": "notes/personal/alice.md",
            "source": {},
            "tags": ["private"],
            "created_at": "2026-01-01",
            "updated_at": "2026-09-01",
        },
    ]
    (registry / "items.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_temporal_graph_never_leaks_acl_denied_nodes(tmp_path):
    _write_items(tmp_path)
    result = temporal_context_graph(
        tmp_path,
        "public-a",
        principal={"principal_id": "bob", "organization_id": "engineering"},
        agent_scopes=[],
    )
    ids = {node["id"] for node in result["nodes"]}
    assert "public-a" in ids
    assert "acl-secret" not in ids
    assert "personal-alice" not in ids
