"""CLI for read-only local workspace discovery."""

from __future__ import annotations

import argparse
import pathlib
import sys

from .common import KnowledgeHubError, pretty_json, repository_root
from .workspace_discovery import discover_workspaces


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="knowledge-workspace-discover.sh",
        description="Match local Git repositories to registered remote keys without writing source projects.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Print the default read-only discovery plan.")
    mode.add_argument("--apply", action="store_true", help="Write only ignored local/workspaces.json transactionally.")
    parser.add_argument("--root", default="", help="Knowledge Hub root.")
    parser.add_argument("--scan-root", action="append", default=[], help="Local directory to scan; repeatable.")
    parser.add_argument("--max-depth", type=int, default=12)
    parser.add_argument("--first-party-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    scan_roots = [pathlib.Path(value) for value in args.scan_root]
    if not scan_roots:
        scan_roots = [pathlib.Path.home()]
        vsdata = pathlib.Path("/vsdata") / pathlib.Path.home().name
        if vsdata.is_dir():
            scan_roots.append(vsdata)
    try:
        payload = discover_workspaces(
            repository_root(args.root),
            scan_roots,
            maximum_depth=args.max_depth,
            include_external=not args.first_party_only,
            apply=args.apply,
        )
    except KnowledgeHubError as exc:
        if args.json:
            print(pretty_json({"status": "blocked", "error": str(exc)}))
        else:
            print("blocked: {}".format(exc), file=sys.stderr)
        return 1
    if args.json:
        print(pretty_json(payload))
    else:
        print(
            "{}: matched={}/{} unmatched={} duplicates={} changed={}".format(
                payload["status"],
                payload["matched_remote_count"],
                payload["registered_remote_count"],
                payload["unmatched_remote_count"],
                payload["duplicate_remote_count"],
                payload["transaction"]["changed_count"],
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
