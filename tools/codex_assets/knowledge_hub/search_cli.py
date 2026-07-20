"""CLI for cached Knowledge Hub search."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .common import KnowledgeHubError, repository_root
from .search import SearchFilters, record_search_telemetry, search


SEARCH_FULL_OUTPUT_BUDGET_BYTES = 256 * 1024
SEARCH_SUMMARY_OUTPUT_BUDGET_BYTES = 64 * 1024


def search_summary(payload):
    return {
        "schema_version": 1,
        "projection": "knowledge-search-summary-v1",
        "status": payload.get("status", ""),
        "query": payload.get("query", ""),
        "count": payload.get("count", 0),
        "total_matches": payload.get("total_matches", 0),
        "latency_ms": payload.get("latency_ms", 0),
        "index": {
            key: payload.get("index", {}).get(key)
            for key in (
                "state",
                "mode",
                "fresh",
                "rebuilt",
                "updated",
                "document_files",
                "candidate_count",
                "authority_candidate_count",
            )
        },
        "pagination": payload.get("pagination", {}),
        "zero_hit": payload.get("zero_hit", {}),
        "schema_validation": payload.get("schema_validation", {}),
        "results": [
            {
                key: row.get(key)
                for key in (
                    "id",
                    "title",
                    "path",
                    "status",
                    "kind",
                    "domain",
                    "score",
                    "why_selected",
                    "preview_redacted",
                )
            }
            for row in payload.get("results", [])
        ],
        "telemetry": payload.get("telemetry", {}),
    }


def _serialized_json(payload, budget):
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    size = len(serialized.encode("utf-8"))
    if size > budget:
        raise KnowledgeHubError(
            "search JSON output exceeds {} bytes; reduce --limit or use --summary-json".format(
                budget
            )
        )
    return serialized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search Knowledge Hub with a local governed index.")
    parser.add_argument("query")
    parser.add_argument("--root", default="")
    projection = parser.add_mutually_exclusive_group()
    projection.add_argument("--json", action="store_true")
    projection.add_argument("--summary-json", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--owner", action="append", default=[])
    parser.add_argument("--status", action="append", default=[])
    parser.add_argument("--kind", action="append", default=[])
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--rebuild-index", action="store_true")
    parser.add_argument("--cursor", default="")
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
            cursor=args.cursor,
        )
        payload["telemetry"] = record_search_telemetry(root, payload, enabled=not args.no_telemetry)
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    if args.json or args.summary_json:
        projection_payload = search_summary(payload) if args.summary_json else payload
        budget = (
            SEARCH_SUMMARY_OUTPUT_BUDGET_BYTES
            if args.summary_json
            else SEARCH_FULL_OUTPUT_BUDGET_BYTES
        )
        try:
            print(_serialized_json(projection_payload, budget))
        except KnowledgeHubError as exc:
            parser.error(str(exc))
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
