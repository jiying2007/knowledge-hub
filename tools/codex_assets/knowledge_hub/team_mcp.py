"""Small-team, read-only MCP projection over the canonical Knowledge Hub.

Not an alternative registry or retrieval engine. A single eligibility rule is
applied before retrieval scoring, and again before exact-id reads. This profile
never exposes history, local drafts, write tools, or unrestricted resources.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import re
from typing import Any, Dict, Mapping

from .common import KnowledgeHubError, read_utf8_bounded, registry_items, resolve_inside
from .protocol_conformance import (
    MCPProtocolError, MCP_PROTOCOL_VERSION, _complete_result,
    _validate_request_meta,
)
from .retrieval_v4 import retrieve_v4

SHA_RE = re.compile(r"^[a-f0-9]{40}$")
DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")
DENIED_ROOTS = {
    ".github", "artifacts", "indexes", "issues", "registry", "schemas",
    "sources", "templates", "tools", "inbox", "notes",
}
DENIED_SEGMENTS = {"archive", "personal"}
MAX_DOCUMENT_BYTES = 512 * 1024
MAX_PAGE_BYTES = 16 * 1024
MAX_QUERY_LENGTH = 4096


def team_publishable(item: Mapping[str, Any], today: dt.date) -> bool:
    """This is an *additional* hard visibility gate, not a status promotion."""
    if item.get("visibility") != "team-internal":
        return False
    if item.get("status") not in {"active", "reviewing"}:
        return False
    if item.get("searchable") is False:
        return False
    # Per-user ACL content cannot silently become available to everybody.
    if item.get("acl") or (isinstance(item.get("source"), dict) and item["source"].get("acl")):
        return False
    path = item.get("path")
    if not isinstance(path, str) or not path.endswith(".md"):
        return False
    parts = pathlib.PurePosixPath(path).parts
    if not parts or path.startswith("/") or ".." in parts or "\\" in path:
        return False
    if parts[0] in DENIED_ROOTS or DENIED_SEGMENTS.intersection(parts):
        return False
    if any(part.startswith(".") for part in parts):
        return False
    try:
        start = dt.date.fromisoformat(item["valid_from"]) if item.get("valid_from") else None
        end = dt.date.fromisoformat(item["valid_to"]) if item.get("valid_to") else None
    except (ValueError, TypeError):
        return False
    if start and end and start > end:
        return False
    return not ((start and today < start) or (end and today > end))


def _args(value: Any, allowed: set, required: set) -> Dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) - allowed or not required <= set(value):
        raise KnowledgeHubError("invalid team MCP arguments")
    return dict(value)


def _limit(value: Any, maximum: int, default: int) -> int:
    if value is None:
        return default
    if type(value) is not int or not 1 <= value <= maximum:
        raise KnowledgeHubError("invalid result limit")
    return value


def _query(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_QUERY_LENGTH:
        raise KnowledgeHubError("query must be a nonempty bounded string")
    return value.strip()


def _kind(item: Mapping[str, Any]) -> str:
    reviewed = (
        item.get("status") == "active"
        and not bool(item.get("manual_validation_pending", False))
        and item.get("content_review_status") == "accepted"
        and item.get("evidence_validation_status") == "verified"
    )
    return "verified" if reviewed else "provisional"


def _review_overdue(item: Mapping[str, Any], today: dt.date) -> bool:
    """Freshness is independent from historical evidence authority."""
    value = item.get("review_after", "")
    if not isinstance(value, str):
        return True
    try:
        deadline = dt.date.fromisoformat(value)
        return deadline.isoformat() != value or deadline < today
    except ValueError:
        return True


def team_search(root: pathlib.Path, query: str, serving_sha: str, limit: int = 5) -> Dict[str, Any]:
    query = _query(query)
    limit = _limit(limit, 10, 5)
    today = dt.date.today()
    result = retrieve_v4(
        root, query, {"principal_id": "team-shared-reader"},
        limit=limit, candidate_filter=lambda item: team_publishable(item, today),
    )
    eligible = {str(item["id"]): item for item in registry_items(root)
                if item.get("id") and team_publishable(item, today)}
    matches = []
    for row in result["results"]:
        item = eligible.get(str(row["id"]))
        if item is None:
            raise KnowledgeHubError("retrieval violated team eligibility")
        matches.append({
            "id": str(row["id"]),
            "title": str(item.get("title", ""))[:512],
            "status": str(item["status"]),
            "authority": _kind(item),
            "review_required": _kind(item) != "verified" or _review_overdue(item, today),
            "review_after": str(item.get("review_after", "")),
            "review_overdue": _review_overdue(item, today),
            "manual_validation_pending": bool(item.get("manual_validation_pending", False)),
            "evidence_validation_status": str(item.get("evidence_validation_status", ""))[:64],
            "summary_zh": str(item.get("summary_zh", ""))[:1024],
            "source_path": str(item["path"]),
            "score": row["score"],
            "rank_components": dict(row.get("score_components", {})),
        })
    return {
        "schema_version": "knowledge-hub.team-search.v1",
        "serving_sha": serving_sha,
        "results": matches,
        "status": result["status"],
        "coverage_complete": result["retrieval_coverage"]["complete"],
    }


def team_get(
    root: pathlib.Path, item_id: str, serving_sha: str, *,
    offset: int = 0, max_bytes: int = MAX_PAGE_BYTES, expected_sha256: str = "",
) -> Dict[str, Any]:
    if not isinstance(item_id, str) or not ID_RE.fullmatch(item_id):
        raise KnowledgeHubError("knowledge item not found")
    if type(offset) is not int or offset < 0 or offset > MAX_DOCUMENT_BYTES:
        raise KnowledgeHubError("invalid offset")
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_PAGE_BYTES:
        raise KnowledgeHubError("invalid page limit")
    if expected_sha256 and (not isinstance(expected_sha256, str) or not DIGEST_RE.fullmatch(expected_sha256)):
        raise KnowledgeHubError("invalid expected digest")
    today = dt.date.today()
    entries = [item for item in registry_items(root) if item.get("id") == item_id]
    if len(entries) != 1 or not team_publishable(entries[0], today):
        raise KnowledgeHubError("knowledge item not found")
    item = entries[0]
    try:
        source = resolve_inside(root, item["path"])
        raw = read_utf8_bounded(source, MAX_DOCUMENT_BYTES, "team document").encode("utf-8")
    except (OSError, UnicodeError, KnowledgeHubError) as exc:
        raise KnowledgeHubError("knowledge item unavailable") from exc
    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 and expected_sha256 != digest:
        raise KnowledgeHubError("document version conflict")
    if offset > len(raw) or (offset and (raw[offset] & 0xc0) == 0x80 if offset < len(raw) else False):
        raise KnowledgeHubError("invalid offset")
    end = min(len(raw), offset + max_bytes)
    while end > offset and end < len(raw) and (raw[end] & 0xc0) == 0x80:
        end -= 1
    if end <= offset and offset < len(raw):
        raise KnowledgeHubError("invalid page limit")
    return {
        "schema_version": "knowledge-hub.team-get.v1",
        "item_id": item_id,
        "status": item["status"],
        "authority": _kind(item),
        "review_required": _kind(item) != "verified" or _review_overdue(item, today),
        "review_after": str(item.get("review_after", "")),
        "review_overdue": _review_overdue(item, today),
        "manual_validation_pending": bool(item.get("manual_validation_pending", False)),
        "evidence_validation_status": str(item.get("evidence_validation_status", ""))[:64],
        "content": raw[offset:end].decode("utf-8"),
        "content_sha256": digest,
        "source_path": item["path"],
        "serving_sha": serving_sha,
        "next_offset": end if end < len(raw) else None,
        "instruction_authority": False,
    }


def team_context(root: pathlib.Path, query: str, serving_sha: str, limit: int = 3, task_type: str = "general") -> Dict[str, Any]:
    if not isinstance(task_type, str) or len(task_type) > 128:
        raise KnowledgeHubError("invalid task_type")
    found = team_search(root, query, serving_sha, limit=_limit(limit, 3, 3))
    current, provisional = [], []
    for row in found["results"]:
        body = team_get(root, row["id"], serving_sha, max_bytes=4096)
        item = dict(row, excerpt=body["content"], content_sha256=body["content_sha256"])
        (current if row["authority"] == "verified" and not row["review_overdue"]
         else provisional).append(item)
    return {
        "schema_version": "knowledge-hub.team-context.v1",
        "serving_sha": serving_sha,
        "task_type": task_type,
        "current": current,
        "provisional": provisional,
        "coverage_complete": found["coverage_complete"],
        "instruction_authority": False,
    }


def team_tools() -> list:
    def schema(fields: Dict[str, Any], required: list) -> dict:
        return {"type": "object", "properties": fields, "required": required, "additionalProperties": False}
    query = {"type": "string", "minLength": 1, "maxLength": MAX_QUERY_LENGTH}
    limited = {"type": "integer", "minimum": 1, "maximum": 10}
    read_only = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
    return [
        {"name": "knowledge_search", "description": "Search shared, current, reviewed-or-provisional knowledge.",
         "annotations": dict(read_only),
         "inputSchema": schema({"query": query, "limit": limited}, ["query"])},
        {"name": "knowledge_get", "description": "Read a registered, shared item by ID with bounded UTF-8 pagination.",
         "annotations": dict(read_only),
         "inputSchema": schema({"item_id": {"type": "string"}, "offset": {"type": "integer", "minimum": 0},
                                "max_bytes": {"type": "integer", "minimum": 1, "maximum": MAX_PAGE_BYTES},
                                "expected_sha256": {"type": "string"}}, ["item_id"])},
        {"name": "knowledge_context", "description": "Bounded team context with explicit provisional facts.",
         "annotations": dict(read_only),
         "inputSchema": schema({"query": query, "limit": {"type": "integer", "minimum": 1, "maximum": 3},
                                "task_type": {"type": "string", "maxLength": 128}}, ["query"])},
    ]


def handle_team_mcp(root: pathlib.Path, request: Mapping[str, Any], serving_sha: str) -> dict:
    if not SHA_RE.fullmatch(serving_sha):
        raise MCPProtocolError("missing trusted serving revision", code=-32603, http_status=503)
    if not isinstance(request, Mapping) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
        raise MCPProtocolError("invalid JSON-RPC request", code=-32600, http_status=400)
    _validate_request_meta(request)
    method = request["method"]
    if method == "server/discover":
        result = _complete_result({"supportedVersions": [MCP_PROTOCOL_VERSION],
                                   "capabilities": {"tools": {}, "resources": {}},
                                   "instructions": "Read-only shared knowledge. Reviewing is not authoritative."}, cacheable=True)
    elif method == "tools/list":
        result = _complete_result({"tools": team_tools()}, cacheable=True)
    elif method == "resources/list":
        result = _complete_result({"resources": [{"uri": "knowledge://health", "name": "Team MCP health",
                                                  "mimeType": "application/json"}]}, cacheable=True)
    elif method == "resources/read":
        args = _args(request.get("params", {}), {"uri", "_meta"}, {"uri"})
        if args["uri"] != "knowledge://health":
            raise MCPProtocolError("resource not found", code=-32602, http_status=404)
        result = _complete_result({"contents": [{"uri": "knowledge://health", "mimeType": "application/json",
                  "text": json.dumps({"status": "running", "serving_sha": serving_sha})}]}, cacheable=False)
    elif method == "tools/call":
        params = _args(request.get("params", {}), {"name", "arguments", "_meta"}, {"name"})
        args = params.get("arguments", {})
        if params["name"] == "knowledge_search":
            p = _args(args, {"query", "limit"}, {"query"})
            value = team_search(root, p["query"], serving_sha, limit=p.get("limit", 5))
        elif params["name"] == "knowledge_get":
            p = _args(args, {"item_id", "offset", "max_bytes", "expected_sha256"}, {"item_id"})
            value = team_get(root, p["item_id"], serving_sha, offset=p.get("offset", 0),
                             max_bytes=p.get("max_bytes", MAX_PAGE_BYTES), expected_sha256=p.get("expected_sha256", ""))
        elif params["name"] == "knowledge_context":
            p = _args(args, {"query", "limit", "task_type"}, {"query"})
            value = team_context(root, p["query"], serving_sha, limit=p.get("limit", 3),
                                 task_type=p.get("task_type", "general"))
        else:
            raise MCPProtocolError("tool not found", code=-32602, http_status=404)
        result = _complete_result({"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}],
                                   "isError": False})
    else:
        raise MCPProtocolError("method not supported", code=-32601, http_status=404)
    return {"jsonrpc": "2.0", "id": request.get("id"), "result": result}
