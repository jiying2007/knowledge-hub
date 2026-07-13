"""CLI for deterministic project readiness generation."""

from __future__ import annotations

import argparse
import sys

from .common import KnowledgeHubError, pretty_json, repository_root, resolve_today
from .project_readiness import generate_project_readiness
from .schemas import validate_instance


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="knowledge-project-readiness.sh",
        description="Plan or generate reviewing-only readiness assets for all registered projects.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Explicitly select the default read-only check mode.")
    mode.add_argument("--apply", action="store_true", help="Apply one transactional tracked-file update.")
    parser.add_argument("--as-of", default="", help="Deterministic date in YYYY-MM-DD form.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)
    try:
        today, _ = resolve_today(args.as_of)
        root = repository_root()
        payload = generate_project_readiness(root, today, apply=args.apply)
    except KnowledgeHubError as exc:
        payload = {"status": "blocked", "error": str(exc)}
        if args.json:
            print(pretty_json(payload))
        else:
            print("blocked: {}".format(exc), file=sys.stderr)
        return 1
    if args.check:
        payload["status"] = "pass" if payload["transaction"]["changed_count"] == 0 else "stale"
    schema_validation = validate_instance(root, "project-readiness-v1", payload)
    payload["schema_validation"] = schema_validation
    if schema_validation["status"] != "pass":
        payload["status"] = "blocked"
    if args.json:
        print(pretty_json(payload))
    else:
        print(
            "{}: projects={} routes={} slots={} changed={}".format(
                payload["status"],
                payload["project_count"],
                payload["route_count"],
                payload["slot_count"],
                payload["transaction"]["changed_count"],
            )
        )
    return 0 if payload["status"] in {"planned", "applied", "no-change", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
