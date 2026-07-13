"""CLI for project-aware context assembly."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Sequence

from .common import repository_root
from .context import BUDGET_LIMITS, TASK_TYPES, assemble_context, record_context_telemetry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve Knowledge Hub context by Git remote, route aliases and registries.")
    parser.add_argument("--root", default="")
    parser.add_argument("--cwd", default=str(pathlib.Path.cwd()))
    parser.add_argument("--query", required=True)
    parser.add_argument("--task-type", choices=sorted(TASK_TYPES), default="general")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--context-budget", choices=sorted(BUDGET_LIMITS), default="normal")
    parser.add_argument("--no-telemetry", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    if args.limit < 1:
        parser.error("--limit must be >= 1")
    root = repository_root(args.root)
    payload = assemble_context(root, args.cwd, args.query, args.task_type, args.limit, args.context_budget)
    record_context_telemetry(root, payload, enabled=not args.no_telemetry)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        route = payload.get("route") or {}
        repo = payload.get("repo_route") or {}
        print("query: {}".format(args.query))
        print("task_type: {}".format(args.task_type))
        print("repo: {} ({})".format(repo.get("repo_id"), repo.get("remote_key")) if repo else "repo: unresolved")
        if route:
            print("project: {} ({})".format(route.get("project_id"), route.get("name")))
            print("hub_entry: {}".format(route.get("hub_entry")))
            print("archive_path: {}".format(route.get("archive_path")))
        else:
            print("project: unresolved")
        print("ranked_items:")
        for item in payload["ranked_items"]:
            print("- {} [{}] {}".format(item["id"], item["kind"], item["path"]))
        print("candidate_required: {}".format(payload["candidate_recommendation"]["required"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
