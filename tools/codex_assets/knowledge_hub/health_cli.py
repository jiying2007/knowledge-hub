"""CLI for the low-latency health summary."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .common import repository_root, resolve_today
from .health import health_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print a concise Knowledge Hub health dashboard.")
    parser.add_argument("--root", default="")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--refresh-gate", action="store_true")
    parser.add_argument("--skip-final-gate", action="store_true", help="Deprecated compatibility alias: ignore gate snapshot.")
    parser.add_argument("--snapshot-max-age-hours", type=int, default=24)
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    if args.snapshot_max_age_hours < 1:
        parser.error("--snapshot-max-age-hours must be >= 1")
    root = repository_root(args.root)
    today, _ = resolve_today(args.as_of)
    payload = health_summary(
        root,
        today,
        refresh_gate=args.refresh_gate,
        skip_final_gate=args.skip_final_gate,
        snapshot_max_age_hours=args.snapshot_max_age_hours,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("# Knowledge Hub Health Summary")
        print()
        print("- health: {}".format(payload["health_status"]))
        print("- as_of: {}".format(payload["as_of"]))
        print("- items: {} {}".format(payload["registry"]["item_count"], payload["registry"]["by_status"]))
        print("- summary_gap: {}".format(payload["registry"]["summary_gap_total"]))
        print("- reviewing: {}".format(payload["reviewing_triage"]["reviewing_count"]))
        print("- final_gate: {} ({})".format(payload["final_gate"]["final_status"], payload["final_gate"]["snapshot"]["state"]))
    return 0 if payload["health_status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
