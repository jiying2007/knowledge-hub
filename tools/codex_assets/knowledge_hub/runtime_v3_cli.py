"""CLI and loopback-only HTTP surface for Knowledge Runtime v3."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Mapping, Sequence
from urllib.parse import urlparse

from .common import KnowledgeHubError, repository_root
from .runtime_v3 import DEFAULT_AGENT, api_dispatch

MAX_REQUEST_BYTES = 256 * 1024
LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


def _payload(raw: str) -> Dict[str, Any]:
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise KnowledgeHubError("request must be valid JSON") from exc
    if not isinstance(value, dict):
        raise KnowledgeHubError("request JSON must be an object")
    return value


def _handler(root, agent_id: str, local_write: bool):
    class Handler(BaseHTTPRequestHandler):
        server_version = "KnowledgeHubContextAPI/1.0"

        def _send(self, status: int, value: Mapping[str, Any]) -> None:
            body = (json.dumps(dict(value), ensure_ascii=False) + "\n").encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _op(self) -> str:
            path = urlparse(self.path).path
            return path[len("/v1/") :].strip("/") if path.startswith("/v1/") else ""

        def do_GET(self):  # noqa: N802
            op = self._op()
            if op not in {"health", "capabilities"}:
                self._send(404, {"status": "not-found"})
                return
            try:
                self._send(200, api_dispatch(root, op, {}, agent_id=agent_id))
            except KnowledgeHubError as exc:
                self._send(400, {"status": "error", "error": str(exc)})

        def do_POST(self):  # noqa: N802
            op = self._op()
            if not op:
                self._send(404, {"status": "not-found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > MAX_REQUEST_BYTES:
                    raise KnowledgeHubError("request body too large")
                request = _payload(self.rfile.read(length).decode("utf-8"))
                result = api_dispatch(
                    root,
                    op,
                    request,
                    agent_id=agent_id,
                    enable_local_write=local_write,
                )
                self._send(200, result)
            except (KnowledgeHubError, UnicodeDecodeError, ValueError) as exc:
                self._send(400, {"status": "error", "error": str(exc)})

        def log_message(self, format, *args):  # noqa: A003
            return

    return Handler


def main(argv: Sequence[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--agent-id", default=DEFAULT_AGENT)
    sub = parser.add_subparsers(dest="command", required=True)
    request = sub.add_parser("request")
    request.add_argument("operation")
    request.add_argument("--json", dest="request_json", default="")
    request.add_argument("--enable-local-write", action="store_true")
    serve = sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--enable-local-write", action="store_true")
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        if args.command == "request":
            raw = args.request_json if args.request_json else sys.stdin.read()
            result = api_dispatch(
                root,
                args.operation,
                _payload(raw),
                agent_id=args.agent_id,
                enable_local_write=args.enable_local_write,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.host not in LOOPBACK_HOSTS:
            raise KnowledgeHubError(
                "Context API is loopback-only; remote serving is not implemented"
            )
        if not 1 <= args.port <= 65535:
            raise KnowledgeHubError("port must be between 1 and 65535")
        server = ThreadingHTTPServer(
            (args.host, args.port),
            _handler(root, args.agent_id, args.enable_local_write),
        )
        print(
            json.dumps(
                {
                    "status": "serving",
                    "api": "knowledge-hub.context-api.v1",
                    "host": args.host,
                    "port": args.port,
                    "agent_id": args.agent_id,
                    "local_write_enabled": args.enable_local_write,
                    "network_scope": "loopback-only",
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        server.serve_forever()
        return 0
    except KnowledgeHubError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
