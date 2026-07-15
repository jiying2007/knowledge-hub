"""CLI for cached Knowledge Hub search."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .common import KnowledgeHubError, repository_root
from .search import SearchFilters, record_search_telemetry, search


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search Knowledge Hub with a local governed index.")
    parser.add_argument("query")
    parser.add_argument("--root", default="")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--owner", action="append", default=[])
    parser.add_argument("--status", action="append", default=[])
    parser.add_argument("--kind", action="append", default=[])
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--rebuild-index", action="store_true")
    parser.add_argument("--no-telemetry", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        payload = search(
            root,
            args.query,
            args.limit,
            SearchFilters(args.source, args.owner, args.status, args.kind, args.domain, args.source_id),
            rebuild_index=args.rebuild_index,
        )
        payload["telemetry"] = record_search_telemetry(root, payload, enabled=not args.no_telemetry)
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("query: {}".format(args.query))
        print("count: {}".format(payload["count"]))
        for item in payload["results"]:
            metadata = ""
            if item.get("item_id"):
                metadata = " [item={} owner={} status={} kind={} domain={} source_id={}]".format(
                    item.get("item_id", ""),
                    item.get("owner", ""),
                    item.get("status", ""),
                    item.get("kind", ""),
                    item.get("domain", ""),
                    item.get("source_id", ""),
                )
            print("{}:{}:{}{}: {}".format(item["source"], item["path"], item["line"], metadata, item["preview"]))
    return 0 if payload["results"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
