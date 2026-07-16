"""CLI for the derived Agent EvidencePack."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .agent_runtime import build_evidence_pack, render_evidence_pack
from .common import KnowledgeHubError, repository_root
from .search import SearchFilters


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a layered, read-only Agent EvidencePack.")
    parser.add_argument("query")
    parser.add_argument("--root", default="")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--scope-ref", action="append", default=[])
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--owner", action="append", default=[])
    parser.add_argument("--status", action="append", default=[])
    parser.add_argument("--kind", action="append", default=[])
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        payload = build_evidence_pack(
            repository_root(args.root),
            args.query,
            limit=args.limit,
            filters=SearchFilters(
                args.source, args.owner, args.status, args.kind, args.domain, args.source_id
            ),
            scope_refs=args.scope_ref,
        )
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_evidence_pack(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
