"""CLI for controlled local team exports."""

from __future__ import annotations

import argparse
import pathlib
import sys

from .common import KnowledgeHubError, pretty_json, repository_root, resolve_today
from .export import apply_team_export, plan_team_export
from .schemas import validate_instance


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="knowledge-export.sh", description="Plan or create an active-only local team export.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Explicitly select the default read-only plan mode.")
    mode.add_argument("--apply", action="store_true", help="Create a local export under ignored cache or /tmp.")
    parser.add_argument("--output", default="", help="Optional output directory under the allowed local roots.")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = repository_root()
    try:
        if args.apply:
            today, _ = resolve_today(args.as_of)
            output = pathlib.Path(args.output) if args.output else None
            payload = apply_team_export(root, today, output)
        else:
            payload = plan_team_export(root)
    except KnowledgeHubError as exc:
        payload = {"status": "blocked", "error": str(exc)}
        if args.json:
            print(pretty_json(payload))
        else:
            print("blocked: {}".format(exc), file=sys.stderr)
        return 1
    schema_validation = validate_instance(root, "team-export-v1", payload)
    payload["schema_validation"] = schema_validation
    if schema_validation["status"] != "pass":
        payload["status"] = "blocked"
    if args.json:
        print(pretty_json(payload))
    else:
        print("{}: files={}".format(payload["status"], payload.get("selected_count", payload.get("file_count", 0))))
    return 0 if payload["status"] in {"ready", "exported"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
