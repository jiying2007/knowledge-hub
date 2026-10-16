"""End-to-end smoke against an authenticated team HTTP MCP endpoint."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import urllib.request

from .common import KnowledgeHubError, registry_items
from .team_mcp import team_publishable
from .runtime_v3_contracts import MCP_PROTOCOL_VERSION


def call(url, token, method, params=None):
    body = dict(params or {})
    body["_meta"] = {
        "io.modelcontextprotocol/protocolVersion": MCP_PROTOCOL_VERSION,
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "knowledge-hub-smoke", "version": "1"},
    }
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": body}
    name = str(body.get("name") if method == "tools/call" else
               body.get("uri") if method == "resources/read" else "")
    headers = {"Authorization": "Bearer " + token,
               "Content-Type": "application/json", "Accept": "application/json, text/event-stream",
               "MCP-Protocol-Version": MCP_PROTOCOL_VERSION, "Mcp-Method": method}
    if name:
        headers["Mcp-Name"] = name
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                     headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.loads(response.read(131072).decode("utf-8"))
    if result.get("error") or result.get("id") != 1:
        raise KnowledgeHubError("invalid team MCP smoke response")
    return result["result"]


def _tool(url, token, name, args):
    result = call(url, token, "tools/call", {"name": name, "arguments": args})
    if result.get("isError") or not result.get("content"):
        raise KnowledgeHubError("team MCP smoke tool failed")
    return json.loads(result["content"][0]["text"])


def smoke(url: str, token: str, sha: str, root: pathlib.Path) -> dict:
    names = {tool["name"] for tool in call(url, token, "tools/list")["tools"]}
    if names != {"knowledge_search", "knowledge_get", "knowledge_context"}:
        raise KnowledgeHubError("team tools differ from the frozen profile")
    rows = [row for row in registry_items(root) if team_publishable(row, dt.date.today())]
    if not rows:
        raise KnowledgeHubError("team MCP has no serviceable knowledge")
    probe = next((row for row in rows if row.get("status") == "active" and row.get("title")), rows[0])
    item_id = probe["id"]
    got = _tool(url, token, "knowledge_get", {"item_id": item_id, "max_bytes": 4096})
    if got["item_id"] != item_id or got["serving_sha"] != sha or not got["content"]:
        raise KnowledgeHubError("team get readback does not match release")
    search = _tool(url, token, "knowledge_search", {"query": probe.get("title") or item_id, "limit": 5})
    if search["serving_sha"] != sha or not search["results"]:
        raise KnowledgeHubError("team search did not find a known-answer case")
    context = _tool(url, token, "knowledge_context", {"query": probe.get("title") or item_id, "limit": 2})
    if context["serving_sha"] != sha or not (context["current"] or context["provisional"]):
        raise KnowledgeHubError("team context failed known-answer case")
    return {"status": "pass", "serving_sha": sha, "tools": sorted(names),
            "probe_id": item_id, "search_results": len(search["results"])}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--serving-sha", required=True)
    parser.add_argument("--token-file", required=True)
    args = parser.parse_args(argv)
    token = pathlib.Path(args.token_file).read_text(encoding="utf-8").strip()
    result = smoke(args.url, token, args.serving_sha, pathlib.Path(args.root))
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
