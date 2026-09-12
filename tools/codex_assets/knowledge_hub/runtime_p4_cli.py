"""One-shot CLI for P4 digital-worker interoperability."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import List, Optional

from .common import KnowledgeHubError
from .runtime_p4_interop import (
    DEFAULT_CONSUMER,
    consumer_handshake,
    integration_readiness,
)
from .runtime_p4_policy import governed_handoff_envelope


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    subparsers = parser.add_subparsers(dest="operation", required=True)

    readiness = subparsers.add_parser("readiness")
    readiness.add_argument("--consumer", default=DEFAULT_CONSUMER)

    handshake = subparsers.add_parser("handshake")
    handshake.add_argument("--consumer", default=DEFAULT_CONSUMER)
    handshake.add_argument("--agent", required=True)
    handshake.add_argument("--work-item-id", required=True)
    handshake.add_argument("--run-id", required=True)
    handshake.add_argument("--scope-ref", required=True)
    handshake.add_argument("--capability", action="append", default=[])
    handshake.add_argument("--mcp-version", default="")
    handshake.add_argument("--a2a-version", default="")

    handoff = subparsers.add_parser("handoff")
    handoff.add_argument("--consumer", default=DEFAULT_CONSUMER)
    handoff.add_argument("--from-agent", required=True)
    handoff.add_argument("--to-agent", required=True)
    handoff.add_argument("--work-item-id", required=True)
    handoff.add_argument("--run-id", required=True)
    handoff.add_argument("--scope-ref", required=True)
    handoff.add_argument("--task", required=True)
    handoff.add_argument("--capability", action="append", default=[])
    handoff.add_argument("--evidence-id", action="append", default=[])
    handoff.add_argument("--execution-receipt-sha256", default="")
    handoff.add_argument("--mcp-version", default="")
    handoff.add_argument("--a2a-version", default="")
    return parser


def _identity(args: argparse.Namespace):
    return {
        "work_item_id": args.work_item_id,
        "run_id": args.run_id,
        "scope_ref": args.scope_ref,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    root = pathlib.Path(args.root).resolve()
    try:
        if args.operation == "readiness":
            result = integration_readiness(root, args.consumer)
        elif args.operation == "handshake":
            result = consumer_handshake(
                root,
                args.consumer,
                args.agent,
                _identity(args),
                args.capability,
                mcp_version=args.mcp_version,
                a2a_version=args.a2a_version,
            )
        else:
            result = governed_handoff_envelope(
                root,
                args.consumer,
                args.from_agent,
                args.to_agent,
                args.task,
                _identity(args),
                args.capability,
                evidence_ids=args.evidence_id,
                execution_receipt_sha256=args.execution_receipt_sha256,
                mcp_version=args.mcp_version,
                a2a_version=args.a2a_version,
            )
    except KnowledgeHubError as exc:
        print(
            json.dumps(
                {"status": "blocked", "error": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
