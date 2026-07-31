"""Plan or apply bounded cleanup of ignored Knowledge Hub runtime artifacts."""

from __future__ import annotations

import argparse
import json
from typing import Iterable

from .common import KnowledgeHubError, repository_root, resolve_today
from .runtime_maintenance import (
    DEFAULT_TRANSACTION_MIN_KEEP,
    DEFAULT_TRANSACTION_RETENTION_DAYS,
    apply_runtime_maintenance,
    plan_runtime_maintenance,
    runtime_maintenance_summary,
)


def main(argv: Iterable[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument(
        "--scope",
        choices=(
            "all",
            "obsolete-search-index",
            "terminal-transactions",
            "runtime-permissions",
        ),
        default="all",
    )
    parser.add_argument(
        "--transaction-retention-days",
        type=int,
        default=DEFAULT_TRANSACTION_RETENTION_DAYS,
    )
    parser.add_argument(
        "--transaction-min-keep",
        type=int,
        default=DEFAULT_TRANSACTION_MIN_KEEP,
    )
    parser.add_argument("--as-of", default="")
    parser.add_argument("--apply", action="store_true")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(list(argv) if argv else None)
    try:
        today, _ = resolve_today(args.as_of)
        root = repository_root(args.root)
        parameters = {
            "scope": args.scope,
            "transaction_retention_days": args.transaction_retention_days,
            "transaction_min_keep": args.transaction_min_keep,
        }
        payload = (
            apply_runtime_maintenance(root, today, **parameters)
            if args.apply
            else plan_runtime_maintenance(root, today, **parameters)
        )
    except KnowledgeHubError as exc:
        if args.json or args.summary_json:
            print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print("blocked: {}".format(exc))
        return 1
    if args.summary_json:
        print(json.dumps(runtime_maintenance_summary(payload), ensure_ascii=False, indent=2))
    elif args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("# Knowledge Hub Runtime Maintenance")
        print()
        print("- status: {}".format(payload["status"]))
        print("- scope: {}".format(payload["scope"]))
        print("- candidate_count: {}".format(payload.get("candidate_count", payload.get("planned_count", 0))))
        print("- deleted_count: {}".format(payload.get("deleted_count", 0)))
        print("- hardened_count: {}".format(payload.get("hardened_count", 0)))
        print("- telemetry_pruned: false")
        print("- incomplete_transactions_pruned: false")
    return 0 if payload["status"] in {"ready", "applied"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
