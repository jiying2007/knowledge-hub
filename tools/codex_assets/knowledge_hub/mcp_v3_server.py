"""Stateless read-only MCP 2026-07-28 stdio adapter for Knowledge Hub."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Mapping, Sequence

from .common import KnowledgeHubError, repository_root
from .runtime_v3 import DEFAULT_AGENT, handle_mcp_request

MAX_LINE_BYTES = 1024 * 1024


def _error(request_id: Any, code: int, message: str):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message[:2048]}}


def _process(root, raw: str, agent_id: str):
    if len(raw.encode("utf-8")) > MAX_LINE_BYTES:
        return _error(None, -32600, "request exceeds byte budget")
    try:
        request = json.loads(raw)
    except json.JSONDecodeError:
        return _error(None, -32700, "parse error")
    if not isinstance(request, Mapping):
        return _error(None, -32600, "request must be an object")
    try:
        return handle_mcp_request(root, request, agent_id=agent_id)
    except KnowledgeHubError as exc:
        return _error(request.get("id"), -32602, str(exc))


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
        return 2
    if args.one_shot:
        response = _process(root, args.one_shot, args.agent_id)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False))
        return 0
    for raw in sys.stdin:
        if raw.strip():
            response = _process(root, raw, args.agent_id)
            if response is not None:
                print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
