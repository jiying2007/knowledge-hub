"""CLI for the offline Knowledge Hub restore drill."""

from __future__ import annotations

import argparse
import sys

from .common import KnowledgeHubError, pretty_json, repository_root, resolve_today
from .restore import run_restore_drill
from .schemas import validate_instance


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="knowledge-restore-drill.sh",
        description="Restore a delivery candidate or committed HEAD in /tmp and run offline smoke gates.",
    )
    parser.add_argument("--as-of", default="")
    parser.add_argument("--source-mode", choices=("candidate", "head"), default="candidate")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        today, _ = resolve_today(args.as_of)
        root = repository_root()
        payload = run_restore_drill(root, today.isoformat(), source_mode=args.source_mode)
        schema_validation = validate_instance(root, "restore-drill-v2", payload)
        payload["schema_validation"] = schema_validation
        if schema_validation["status"] != "pass":
            payload["status"] = "fail"
    except KnowledgeHubError as exc:
        payload = {"status": "blocked", "error": str(exc)}
        if args.json:
            print(pretty_json(payload))
        else:
            print("blocked: {}".format(exc), file=sys.stderr)
        return 1
    if args.json:
        print(pretty_json(payload))
    else:
        print("{}: copied={} failed_checks={}".format(payload["status"], payload["copied_file_count"], len(payload["failed_checks"])))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
