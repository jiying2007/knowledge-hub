"""CLI for project-aware context assembly."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Sequence

from .common import repository_root
from .context import (
    BUDGET_LIMITS,
    TASK_TYPES,
    assemble_context,
    attach_context_receipt,
    context_receipt_request,
    load_context_receipt,
    record_context_telemetry,
    summarize_context,
    write_context_receipt,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve Knowledge Hub context by Git remote, route aliases and registries.")
    parser.add_argument("--root", default="")
    parser.add_argument("--cwd", default=str(pathlib.Path.cwd()))
    parser.add_argument("--query", required=True)
    parser.add_argument(
        "--project",
        default="",
        help="显式限定 project_id；无匹配或不唯一时 fail closed",
    )
    parser.add_argument("--task-type", choices=sorted(TASK_TYPES), default="general")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="输出完整可解释 JSON")
    output.add_argument("--summary-json", action="store_true", help="输出低 Token Agent 上下文摘要")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--context-budget", choices=sorted(BUDGET_LIMITS), default="small")
    parser.add_argument(
        "--receipt-key",
        default="",
        help="显式复用绑定 query hash、workspace HEAD、registry 与原文 hash 的 summary cache",
    )
    telemetry = parser.add_mutually_exclusive_group()
    telemetry.add_argument("--telemetry", action="store_true", help="显式写入脱敏本地 telemetry")
    telemetry.add_argument("--no-telemetry", dest="telemetry", action="store_false", help=argparse.SUPPRESS)
    parser.set_defaults(telemetry=False)
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    if args.limit < 1:
        parser.error("--limit must be >= 1")
    if args.receipt_key and not args.summary_json:
        parser.error("--receipt-key requires --summary-json")
    if args.receipt_key and args.telemetry:
        parser.error("--receipt-key cannot combine with --telemetry")
    root = repository_root(args.root)
    receipt_request = None
    receipt_miss_reason = ""
    if args.receipt_key:
        try:
            receipt_request = context_receipt_request(
                root,
                args.cwd,
                args.query,
                args.task_type,
                args.limit,
                args.context_budget,
                args.project,
            )
            cached, receipt_miss_reason = load_context_receipt(
                root, args.receipt_key, receipt_request
            )
        except ValueError as exc:
            parser.error(str(exc))
        if cached is not None:
            summary = attach_context_receipt(cached, args.receipt_key, True, "hit")
            print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
            return 0
    try:
        payload = assemble_context(
            root,
            args.cwd,
            args.query,
            args.task_type,
            args.limit,
            args.context_budget,
            project_hint=args.project,
        )
    except ValueError as exc:
        parser.error(str(exc))
    payload["telemetry"] = record_context_telemetry(root, payload, enabled=args.telemetry)
    if args.summary_json:
        summary = summarize_context(payload)
        if args.receipt_key and receipt_request is not None:
            write_context_receipt(root, args.receipt_key, receipt_request, summary)
            summary = attach_context_receipt(
                summary, args.receipt_key, False, receipt_miss_reason or "miss"
            )
        print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    elif args.json:
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
