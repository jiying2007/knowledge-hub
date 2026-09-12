import json

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.protocol_conformance import (
    handle_mcp_stateless_request,
)
from tools.codex_assets.knowledge_hub.runtime_v3_contracts import MCP_PROTOCOL_VERSION
from tools.codex_assets.knowledge_hub.temporal_graph import temporal_context_graph


def _request(method, params=None, request_id=1):
    value = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "_meta": {"protocolVersion": MCP_PROTOCOL_VERSION},
    }
    if params is not None:
        value["params"] = params
    return value


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
        assert response["result"]["contents"][0]["uri"] == uri
        json.loads(response["result"]["contents"][0]["text"])


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


def test_temporal_graph_anonymous_view_hides_acl_and_personal_nodes(tmp_path):
    _write_items(tmp_path)
    graph = temporal_context_graph(tmp_path, as_of="2026-09-12")
    ids = {row["id"] for row in graph["nodes"]}

    assert graph["authorization_applied_before_graph"] is True
    assert graph["principal_id"] == "anonymous-local"
    assert ids == {"public-a"}
    assert graph["edges"] == []


def test_temporal_graph_principal_acl_and_scope_apply_before_edges(tmp_path):
    _write_items(tmp_path)
    alice = {"principal_id": "user:alice", "groups": []}
    full = temporal_context_graph(
        tmp_path,
        as_of="2026-09-12",
        principal=alice,
    )
    scoped = temporal_context_graph(
        tmp_path,
        as_of="2026-09-12",
        principal=alice,
        knowledge_scopes=["projects/a"],
    )

    assert {row["id"] for row in full["nodes"]} == {
        "public-a",
        "acl-secret",
        "personal-alice",
    }
    assert full["edges"] == [
        {
            "source_id": "public-a",
            "relation": "conflicts_with",
            "target_id": "acl-secret",
            "valid_from": "",
            "valid_to": "",
            "source_item_id": "public-a",
        }
    ]
    assert {row["id"] for row in scoped["nodes"]} == {"public-a"}
    assert scoped["edges"] == []
