"""CLI for the bounded Knowledge Hub navigation map."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .common import KnowledgeHubError, compact_json, repository_root
from .map_view import build_knowledge_map, render_knowledge_map


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a bounded, read-only Knowledge Hub navigation map.")
    parser.add_argument("--root", default="")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--max-bytes", type=int, default=8192)
    parser.add_argument("--cursor", default="")
    parser.add_argument("--status", action="append", default=[])
    parser.add_argument("--kind", action="append", default=[])
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--owner", action="append", default=[])
    parser.add_argument("--all-statuses", action="store_true")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--summary-json", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        payload = build_knowledge_map(
            repository_root(args.root),
            limit=args.limit,
            max_bytes=args.max_bytes,
            cursor=args.cursor,
            statuses=args.status,
            kinds=args.kind,
            domains=args.domain,
            owners=args.owner,
            all_statuses=args.all_statuses,
        )
    except KnowledgeHubError as exc:
        if args.json or args.summary_json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
            return 2
        parser.error(str(exc))
    if args.summary_json:
        print(compact_json(payload))
    elif args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_knowledge_map(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
