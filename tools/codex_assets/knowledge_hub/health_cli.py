"""CLI for the low-latency health summary."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .common import repository_root, resolve_today
from .health import health_summary
from .output_contract import status_contract


def health_projection(payload):
    return {
        "schema_version": 2,
        "projection": "knowledge-health-summary-v2",
        "status": payload.get("status", "blocked"),
        "status_contract": payload.get("status_contract", {}),
        "as_of": payload.get("as_of", ""),
        "health_axes": payload.get("health_axes", {}),
        "registry": payload.get("registry", {}),
        "reviewing_triage": payload.get("reviewing_triage", {}),
        "runtime_maintenance": payload.get("runtime_maintenance", {}),
        "final_gate": payload.get("final_gate", {}),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print a concise Knowledge Hub health dashboard.")
    parser.add_argument("--root", default="")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--summary-json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--refresh-gate", action="store_true")
    parser.add_argument("--gate-suite", choices=("auto", "quick", "full"), default="auto")
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
        snapshot_max_age_hours=args.snapshot_max_age_hours,
        gate_suite=args.gate_suite,
    )
    contract = status_contract(payload["status"])
    payload["status_contract"] = contract
    if args.json or args.summary_json:
        projection = health_projection(payload) if args.summary_json else payload
        print(json.dumps(projection, ensure_ascii=False, indent=2))
    else:
        print("# Knowledge Hub Health Summary")
        print()
        print("- status: {}".format(payload["status"]))
        print("- as_of: {}".format(payload["as_of"]))
        print("- items: {} {}".format(payload["registry"]["item_count"], payload["registry"]["by_status"]))
        print("- summary_gap: {}".format(payload["registry"]["summary_gap_total"]))
        print("- reviewing: {}".format(payload["reviewing_triage"]["reviewing_count"]))
        print("- health_axes: {}".format(payload["health_axes"]))
        print(
            "- runtime_maintenance: candidates={} reclaimable_bytes={}".format(
                payload["runtime_maintenance"]["candidate_count"],
                payload["runtime_maintenance"]["candidate_bytes"],
            )
        )
        print(
            "- final_gate: {} ({})".format(
                payload["final_gate"]["status"],
                payload["final_gate"]["snapshot"]["state"],
            )
        )
    return (
        contract["strict_exit_code"]
        if args.strict
        else contract["default_exit_code"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
