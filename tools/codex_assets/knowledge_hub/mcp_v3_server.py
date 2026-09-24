"""Native stateless MCP 2026-07-28 stdio adapter for Knowledge Hub.

Only the native stateless profile is accepted; initialize/session compatibility is retired.
Oversized input terminates stdio after one bounded error; it is never drained or
reinterpreted as multiple requests. A client may reconnect with valid input.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Mapping, Sequence

from .common import KnowledgeHubError, repository_root
from .protocol_conformance import MCPProtocolError, handle_mcp_stateless_request
from .runtime_v3 import DEFAULT_AGENT

MAX_LINE_BYTES = 1024 * 1024


def _error(request_id: Any, code: int, message: str, data=None):
    error = {"code": int(code), "message": str(message)[:2048]}
    if data:
        error["data"] = dict(data)
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _process(root, raw: str, agent_id: str):
    try:
        size = len(raw.encode("utf-8"))
    except UnicodeError:
        return _error(None, -32700, "request must be UTF-8")
    if size > MAX_LINE_BYTES:
        return _error(None, -32600, "request exceeds byte budget")
    try:
        request = json.loads(raw)
    except (json.JSONDecodeError, RecursionError):
        return _error(None, -32700, "parse error")
    if not isinstance(request, Mapping):
        return _error(None, -32600, "request must be an object")
    if str(request.get("method", "")).startswith("notifications/"):
        return None
    try:
        return handle_mcp_stateless_request(root, request, agent_id=agent_id)
    except MCPProtocolError as exc:
        return _error(request.get("id"), exc.code, str(exc), exc.data)
    except KnowledgeHubError as exc:
        return _error(request.get("id"), -32602, str(exc))


def _serve(root, input_stream, output_stream, agent_id: str) -> int:
    while True:
        # Bound the read itself. Never use iterator/readline() without a size.
        raw = input_stream.readline(MAX_LINE_BYTES + 1)
        if not raw:
            return 0
        if isinstance(raw, str):
            try:
                raw = raw.encode("utf-8")
            except UnicodeError:
                response = _error(None, -32700, "request must be UTF-8")
                print(json.dumps(response), file=output_stream, flush=True)
                continue
        if len(raw) > MAX_LINE_BYTES:
            response = _error(None, -32600, "request exceeds byte budget")
            print(json.dumps(response), file=output_stream, flush=True)
            return 2
        try:
            text = raw.decode("utf-8")
        except UnicodeError:
            response = _error(None, -32700, "request must be UTF-8")
        else:
            if not text.strip():
                continue
            response = _process(root, text, agent_id)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), file=output_stream, flush=True)


def main(argv: Sequence[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--agent-id", default=DEFAULT_AGENT)
    parser.add_argument("--one-shot", default="")
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    if args.one_shot:
        response = _process(root, args.one_shot, args.agent_id)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False))
        return 0
    return _serve(root, getattr(sys.stdin, "buffer", sys.stdin), sys.stdout, args.agent_id)


if __name__ == "__main__":
    raise SystemExit(main())
