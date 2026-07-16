"""CLI for metadata-only raw evidence ledger inspection."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Sequence

from .common import KnowledgeHubError
from .raw_evidence import inspect_raw_evidence_ledger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect a rawmem-compatible ledger without echoing event content.")
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--max-errors", type=int, default=20)
    parser.add_argument("--max-bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--max-events", type=int, default=100000)
    parser.add_argument("--max-line-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        payload = inspect_raw_evidence_ledger(
            pathlib.Path(args.ledger),
            max_errors=args.max_errors,
            max_bytes=args.max_bytes,
            max_events=args.max_events,
            max_line_bytes=args.max_line_bytes,
        )
    except (KnowledgeHubError, OSError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("status: {}".format(payload["status"]))
        print("chain_status: {}".format(payload["chain_status"]))
        print("event_count: {}".format(payload["ledger"]["event_count"]))
        print("hub_route: reference-only")
    return 0 if payload["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
