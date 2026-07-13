"""CLI for PCR02 owner/device/release validation readiness hardening."""

from __future__ import annotations

import argparse
import sys

from .common import KnowledgeHubError, pretty_json, repository_root, resolve_today
from .pcr02_validation import harden_pcr02_validation
from .schemas import validate_instance


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="knowledge-pcr02-owner-readiness.sh",
        description="Plan, apply or check evidence-readiness contracts for three PCR02 decision candidates.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Require the generated contract to be current.")
    mode.add_argument("--apply", action="store_true", help="Apply one transactional Hub-only update.")
    parser.add_argument("--as-of", default="", help="Deterministic date in YYYY-MM-DD form.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)
    try:
        today, _ = resolve_today(args.as_of)
        root = repository_root()
        payload = harden_pcr02_validation(root, today, apply=args.apply)
    except KnowledgeHubError as exc:
        payload = {"status": "blocked", "error": str(exc)}
        if args.json:
            print(pretty_json(payload))
        else:
            print("blocked: {}".format(exc), file=sys.stderr)
        return 1
    if args.check:
        payload["status"] = "pass" if payload["transaction"]["changed_count"] == 0 else "stale"
    schema_validation = validate_instance(root, "pcr02-evidence-readiness-v1", payload)
    payload["schema_validation"] = schema_validation
    if schema_validation["status"] != "pass":
        payload["status"] = "blocked"
    if args.json:
        print(pretty_json(payload))
    else:
        print(
            "{}: candidates={} changed={}".format(
                payload["status"], payload["candidate_count"], payload["transaction"]["changed_count"]
            )
        )
    return 0 if payload["status"] in {"planned", "applied", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
