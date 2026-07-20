"""CLI for the single product final gate."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .common import repository_root, resolve_today
from .product_gate import product_gate_summary, run_product_gate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Knowledge Hub product final gate.")
    parser.add_argument("--root", default="")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--summary-json", action="store_true")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--final-profile", choices=("product",), default="product")
    parser.add_argument("--regression-suite", choices=("quick", "full"), default="quick")
    parser.add_argument(
        "--reuse-engineering-evidence",
        action="store_true",
        help=(
            "Reuse signature-bound fresh full engineering pytest/regression evidence when available; "
            "quick gates automatically reuse eligible pytest evidence."
        ),
    )
    parser.add_argument("--require-terminal", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    args = build_parser().parse_args(list(argv) if argv else None)
    root = repository_root(args.root)
    today, _ = resolve_today(args.as_of)
    payload = run_product_gate(
        root,
        today.isoformat(),
        regression_suite=args.regression_suite,
        reuse_engineering_evidence=args.reuse_engineering_evidence,
    )
    if args.summary_json:
        print(json.dumps(product_gate_summary(payload), ensure_ascii=False, indent=2))
    elif args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("# Knowledge Hub Product Final Gate")
        print()
        print("- platform_status: {}".format(payload["platform_status"]["status"]))
        print("- local_delivery_complete: {}".format(payload["local_delivery_complete"]))
        print("- remote_published: {}".format(payload["remote_published"]))
        print("- offsite_restore_verified: {}".format(payload["offsite_restore_verified"]))
        print("- adoption_ready: {}".format(payload["adoption_ready"]))
        print("- terminal: {}".format(payload["terminal"]))
        print("- overall_status: {}".format(payload["overall_status"]))
        print("- final_profile: {}".format(payload["final_profile"]))
        print("- duration_ms: {}".format(payload["duration_ms"]))
    if payload["platform_status"]["status"] != "pass":
        return 1
    if args.require_terminal and not payload["terminal"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
