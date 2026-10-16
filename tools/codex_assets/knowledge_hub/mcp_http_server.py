"""Local-only Streamable HTTP transport for the MCP 2026-07-28 native profile.

This module intentionally exposes no remote-listen mode. Knowledge Hub can be placed
behind a separately governed authenticated gateway later; the repository-native
transport is loopback-only so conformance testing cannot silently create a new remote
security boundary.
"""

from __future__ import annotations

import argparse
import hmac
import json
import pathlib
import re
import socket
import stat
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Mapping, Optional, Sequence
from urllib.parse import urlparse

from .common import KnowledgeHubError, repository_root
from .protocol_conformance import (
    MCP_PROTOCOL_META_KEY,
    MCP_PROTOCOL_VERSION,
    MCPProtocolError,
    handle_mcp_stateless_request,
)
from .runtime_v3_contracts import DEFAULT_AGENT
from .team_mcp import handle_team_mcp

MAX_REQUEST_BYTES = 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 5.0
MCP_PATH = "/mcp"
LOOPBACK_HOSTS = {"localhost", "127.0.0.1"}


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
    origin_header = str(headers.get("Origin", "")).strip()
    origin = _origin_host(origin_header)
    if host not in LOOPBACK_HOSTS:
        raise MCPProtocolError(
            "localhost MCP transport rejected non-loopback Host",
            code=-32001,
            http_status=403,
            data={"reason": "dns-rebinding-host-rejected"},
        )
    if origin_header and (not origin or origin not in {"localhost", "127.0.0.1"}):
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


class _BoundedTeamServer(ThreadingHTTPServer):
    """Bound *connections*, including idle pre-HTTP connections, not only POST calls."""

    daemon_threads = True

    def __init__(self, address, handler, *, max_connections: int) -> None:
        self._connection_slots = threading.BoundedSemaphore(max_connections)
        super().__init__(address, handler)

    def process_request(self, request, client_address) -> None:
        if not self._connection_slots.acquire(blocking=False):
            try:
                request.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            request.close()
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._connection_slots.release()
            raise

    def process_request_thread(self, request, client_address) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._connection_slots.release()


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
        limiter = getattr(self.server, "knowledge_limiter", None)
        if limiter is not None and not limiter.acquire(blocking=False):
            self._send_json(503, _error_payload(None, -32003, "MCP concurrency limit"))
            return
        try:
            self._post()
        finally:
            if limiter is not None:
                limiter.release()

    def _post(self) -> None:
        if self.path != MCP_PATH:
            self._send_json(404, _error_payload(None, -32601, "MCP endpoint not found"))
            return
        request_id: Any = None
        try:
            self.connection.settimeout(REQUEST_TIMEOUT_SECONDS)
            validate_local_origin(self.headers)
            token = getattr(self.server, "knowledge_team_token", None)
            if token is not None:
                supplied = str(self.headers.get("Authorization", ""))
                if not hmac.compare_digest(supplied, "Bearer " + token):
                    self._send_json(401, _error_payload(None, -32001, "Authentication required"))
                    return
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
            validate_http_request(request, self.headers)
            root = self.server.knowledge_root  # type: ignore[attr-defined]
            agent_id = self.server.knowledge_agent_id  # type: ignore[attr-defined]
            serving_sha = getattr(self.server, "knowledge_serving_sha", "")
            response = (handle_team_mcp(root, request, serving_sha) if token is not None
                        else handle_mcp_stateless_request(root, request, agent_id=agent_id))
            self._send_json(200, response)
        except socket.timeout:
            self._send_json(408, _error_payload(request_id, -32021, "MCP request timed out"))
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
    parser.add_argument("--team", action="store_true", help="Strict read-only team MCP profile")
    parser.add_argument("--team-token-file", default="", help="Owner-only file, never a CLI secret")
    parser.add_argument("--serving-sha", default="", help="Exact immutable Git revision being served")
    parser.add_argument("--max-inflight", type=int, default=8)
    return parser


def serve(
    root: pathlib.Path,
    *,
    host: str = "127.0.0.1",
    port: int = 3000,
    agent_id: str = DEFAULT_AGENT,
    team: bool = False,
    token_file: str = "",
    serving_sha: str = "",
    max_inflight: int = 8,
) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise KnowledgeHubError("native MCP transport may bind loopback only")
    if not 1 <= int(port) <= 65535:
        raise KnowledgeHubError("MCP port must be between 1 and 65535")
    if not 1 <= max_inflight <= 32:
        raise KnowledgeHubError("max-inflight must be between 1 and 32")
    token = None
    if team:
        if not re.fullmatch(r"[a-f0-9]{40}", serving_sha):
            raise KnowledgeHubError("team profile requires exact serving SHA")
        marker = pathlib.Path(root) / ".serving-sha"
        if marker.is_symlink() or not marker.is_file() or marker.read_text(encoding="utf-8").strip() != serving_sha:
            raise KnowledgeHubError("team release marker does not match serving SHA")
        if not token_file:
            raise KnowledgeHubError("team profile requires a token file")
        key_path = pathlib.Path(token_file)
        details = key_path.lstat()
        if not stat.S_ISREG(details.st_mode) or details.st_mode & 0o077:
            raise KnowledgeHubError("team token file must be private regular file (0600)")
        token = key_path.read_text(encoding="utf-8").strip()
        if not 32 <= len(token) <= 512 or any(char.isspace() for char in token):
            raise KnowledgeHubError("team token must be 32-512 nonwhitespace characters")
    elif token_file or serving_sha:
        raise KnowledgeHubError("team token or serving SHA requires --team")
    server = (_BoundedTeamServer((host, int(port)), _Handler, max_connections=max_inflight * 2)
              if team else ThreadingHTTPServer((host, int(port)), _Handler))
    server.daemon_threads = True
    server.knowledge_limiter = threading.BoundedSemaphore(max_inflight) if team else None  # type: ignore[attr-defined]
    server.knowledge_team_token = token  # type: ignore[attr-defined]
    server.knowledge_serving_sha = serving_sha  # type: ignore[attr-defined]
    server.knowledge_root = root  # type: ignore[attr-defined]
    server.knowledge_agent_id = agent_id  # type: ignore[attr-defined]
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()


def main(argv: Sequence[str] = ()) -> int:
    args = _parser().parse_args(list(argv) if argv else None)
    root = repository_root(args.root)
    serve(root, host=args.host, port=args.port, agent_id=args.agent_id,
          team=args.team, token_file=args.team_token_file,
          serving_sha=args.serving_sha, max_inflight=args.max_inflight)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
