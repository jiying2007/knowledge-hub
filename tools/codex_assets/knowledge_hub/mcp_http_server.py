"""Local-only Streamable HTTP transport for the MCP 2026-07-28 native profile.

This module intentionally exposes no remote-listen mode. Knowledge Hub can be placed
behind a separately governed authenticated gateway later; the repository-native
transport is loopback-only so conformance testing cannot silently create a new remote
security boundary.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlparse

from .common import KnowledgeHubError, repository_root
from .protocol_conformance import (
    MCP_PROTOCOL_META_KEY,
    MCP_PROTOCOL_VERSION,
    MCPProtocolError,
    handle_mcp_stateless_request,
)
from .runtime_v3_contracts import DEFAULT_AGENT

MAX_REQUEST_BYTES = 1024 * 1024
MCP_PATH = "/mcp"
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]"}


def _host_name(value: str) -> str:
    value = str(value or "").strip().lower()
    if not value:
        return ""
    if value.startswith("["):
        end = value.find("]")
        return value[: end + 1] if end >= 0 else value
    return value.split(":", 1)[0]


def _origin_host(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        parsed = urlparse(text)
    except ValueError:
        return "invalid"
    return str(parsed.hostname or "").lower()


def _body_protocol_version(request: Mapping[str, Any]) -> str:
    params = request.get("params")
    if not isinstance(params, Mapping):
        return ""
    meta = params.get("_meta")
    if not isinstance(meta, Mapping):
        return ""
    return str(meta.get(MCP_PROTOCOL_META_KEY, "")).strip()


def _expected_name(request: Mapping[str, Any]) -> str:
    method = str(request.get("method", ""))
    params = request.get("params")
    if not isinstance(params, Mapping):
        return ""
    if method == "tools/call":
        return str(params.get("name", ""))
    if method == "resources/read":
        return str(params.get("uri", ""))
    if method == "prompts/get":
        return str(params.get("name", ""))
    return ""


def validate_http_request(
    request: Mapping[str, Any],
    headers: Mapping[str, str],
) -> None:
    """Enforce 2026 routing/version headers before dispatching the JSON-RPC body."""

    protocol_header = str(headers.get("MCP-Protocol-Version", "")).strip()
    if not protocol_header:
        raise MCPProtocolError(
            "HeaderMismatch: MCP-Protocol-Version is required",
            code=-32020,
            http_status=400,
            data={"header": "MCP-Protocol-Version", "expected": MCP_PROTOCOL_VERSION},
        )
    body_version = _body_protocol_version(request)
    if body_version and protocol_header != body_version:
        raise MCPProtocolError(
            "HeaderMismatch: MCP-Protocol-Version does not match request _meta",
            code=-32020,
            http_status=400,
            data={
                "header": "MCP-Protocol-Version",
                "headerValue": protocol_header,
                "bodyValue": body_version,
            },
        )

    method = str(request.get("method", ""))
    method_header = str(headers.get("Mcp-Method", "")).strip()
    if not method_header or method_header != method:
        raise MCPProtocolError(
            "HeaderMismatch: Mcp-Method does not match JSON-RPC method",
            code=-32020,
            http_status=400,
            data={
                "header": "Mcp-Method",
                "headerValue": method_header,
                "bodyValue": method,
            },
        )

    expected_name = _expected_name(request)
    name_header = str(headers.get("Mcp-Name", "")).strip()
    if expected_name and name_header != expected_name:
        raise MCPProtocolError(
            "HeaderMismatch: Mcp-Name does not match request params",
            code=-32020,
            http_status=400,
            data={
                "header": "Mcp-Name",
                "headerValue": name_header,
                "bodyValue": expected_name,
            },
        )
    if not expected_name and name_header:
        raise MCPProtocolError(
            "HeaderMismatch: Mcp-Name is not valid for this method",
            code=-32020,
            http_status=400,
            data={"header": "Mcp-Name", "headerValue": name_header},
        )


def validate_local_origin(headers: Mapping[str, str]) -> None:
    host = _host_name(str(headers.get("Host", "")))
    origin = _origin_host(str(headers.get("Origin", "")))
    if host not in LOOPBACK_HOSTS:
        raise MCPProtocolError(
            "localhost MCP transport rejected non-loopback Host",
            code=-32001,
            http_status=403,
            data={"reason": "dns-rebinding-host-rejected"},
        )
    if origin and origin not in {"localhost", "127.0.0.1", "::1"}:
        raise MCPProtocolError(
            "localhost MCP transport rejected non-loopback Origin",
            code=-32001,
            http_status=403,
            data={"reason": "dns-rebinding-origin-rejected"},
        )


def _error_payload(
    request_id: Any,
    code: int,
    message: str,
    data: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    error: Dict[str, Any] = {"code": int(code), "message": str(message)}
    if data:
        error["data"] = dict(data)
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


class _Handler(BaseHTTPRequestHandler):
    server_version = "KnowledgeHubMCP/2026-07-28"
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def _send_json(self, status: int, payload: Mapping[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_method_not_allowed(self) -> None:
        self._send_json(
            405,
            _error_payload(None, -32601, "Method not allowed; MCP uses POST /mcp"),
        )

    def do_GET(self) -> None:  # noqa: N802
        self._send_method_not_allowed()

    def do_DELETE(self) -> None:  # noqa: N802
        self._send_method_not_allowed()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != MCP_PATH:
            self._send_json(404, _error_payload(None, -32601, "MCP endpoint not found"))
            return
        request_id: Any = None
        try:
            length_text = str(self.headers.get("Content-Length", "0")).strip()
            try:
                length = int(length_text)
            except ValueError:
                length = -1
            if length < 0 or length > MAX_REQUEST_BYTES:
                raise MCPProtocolError(
                    "MCP request body exceeds transport budget",
                    code=-32600,
                    http_status=413,
                )
            raw = self.rfile.read(length)
            try:
                request = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise MCPProtocolError(
                    "invalid JSON request body",
                    code=-32700,
                    http_status=400,
                ) from exc
            if not isinstance(request, Mapping):
                raise MCPProtocolError(
                    "MCP request must be a JSON object",
                    code=-32600,
                    http_status=400,
                )
            request_id = request.get("id")
            validate_local_origin(self.headers)
            validate_http_request(request, self.headers)
            root = getattr(self.server, "knowledge_root")
            agent_id = getattr(self.server, "knowledge_agent_id")
            response = handle_mcp_stateless_request(root, request, agent_id=agent_id)
            self._send_json(200, response)
        except MCPProtocolError as exc:
            self._send_json(
                exc.http_status,
                _error_payload(request_id, exc.code, str(exc), exc.data),
            )
        except KnowledgeHubError as exc:
            self._send_json(400, _error_payload(request_id, -32602, str(exc)))
        except Exception:
            self._send_json(500, _error_payload(request_id, -32603, "Internal error"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--agent-id", default=DEFAULT_AGENT)
    return parser


def serve(
    root: pathlib.Path,
    *,
    host: str = "127.0.0.1",
    port: int = 3000,
    agent_id: str = DEFAULT_AGENT,
) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise KnowledgeHubError("native MCP transport may bind loopback only")
    if not 1 <= int(port) <= 65535:
        raise KnowledgeHubError("MCP port must be between 1 and 65535")
    server = ThreadingHTTPServer((host, int(port)), _Handler)
    server.knowledge_root = root  # type: ignore[attr-defined]
    server.knowledge_agent_id = agent_id  # type: ignore[attr-defined]
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()


def main(argv: Sequence[str] = ()) -> int:
    args = _parser().parse_args(list(argv) if argv else None)
    root = repository_root(args.root)
    serve(root, host=args.host, port=args.port, agent_id=args.agent_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
