"""Run registry-driven, report-only source availability checks."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Sequence

from .common import KnowledgeHubError, resolve_today
from .source_runtime import run_source_checks


def main(argv: Sequence[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument(
        "--scope",
        choices=("all", "current"),
        default="all",
        help="all 检查 current 与 retired；current 只检查当前 source。",
    )
    parser.add_argument("--source-id", default="", metavar="SOURCE_ID")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD")
    args = parser.parse_args(list(argv) if argv else None)
    try:
        today, _ = resolve_today(args.as_of)
        payload = run_source_checks(
            pathlib.Path(args.root),
            today,
            scope=args.scope,
            source_id_filter=args.source_id,
            plan=args.plan,
        )
    except KnowledgeHubError as exc:
        if args.json:
            print(json.dumps({"status": "fail", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        else:
            print("fail: {}".format(exc))
        return 1
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("# Knowledge Source Check")
        print()
        print("- status: {}".format(payload["status"]))
        print("- scope: {}".format(payload["scope"]))
        print("- registered sources: {}".format(payload["registry_source_count"]))
        print("- selected sources: {}".format(payload["row_count"]))
        print("- executed: {}".format(payload["executed_count"]))
        print("- failed: {}".format(payload["failed_count"]))
        print("- execution mode: {}".format(payload["execution_mode"]))
        for row in payload["rows"]:
            print(
                "- {}: {} ({}, {}) {}".format(
                    row["status"],
                    row["source_id"],
                    row["registry_bucket"],
                    row["primitive"] or "no-check",
                    row["result"],
                )
            )
    if payload["status"] == "fail":
        return 1
    if args.strict and payload["status"] != ("planned" if args.plan else "pass"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
