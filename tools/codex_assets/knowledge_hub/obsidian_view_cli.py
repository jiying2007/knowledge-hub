"""CLI for deterministic Obsidian Properties, MOCs and Bases."""

from __future__ import annotations

import argparse

from .common import pretty_json, repository_root
from .obsidian_view import build_obsidian_views
from .schemas import validate_instance


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="knowledge-obsidian-view-build.sh",
        description="Plan, apply or check plugin-free Obsidian views over canonical Hub Markdown.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Check whether generated Properties and views are current.")
    mode.add_argument("--apply", action="store_true", help="Apply one transactional Hub-only view refresh.")
    parser.add_argument(
        "--reconcile-content-mirrors",
        action="store_true",
        help="Resolve existing title/summary/tags drift using Markdown authority; tags use an ordered union.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args(argv)
    root = repository_root()
    payload = build_obsidian_views(
        root, apply=args.apply, reconcile_content_mirrors=args.reconcile_content_mirrors
    )
    if args.check and payload["status"] == "planned" and payload["transaction"]["changed_count"]:
        payload["status"] = "stale"
    elif args.check and payload["status"] == "planned":
        payload["status"] = "pass"
    schema_validation = validate_instance(root, "obsidian-view-build-v1", payload)
    payload["schema_validation"] = schema_validation
    if schema_validation["status"] != "pass":
        payload["status"] = "blocked"
    if args.json:
        print(pretty_json(payload))
    else:
        print(
            "{}: managed={} drift={} changed={}".format(
                payload["status"],
                payload["managed_document_count"],
                payload["content_mirror_drift_count"],
                payload["transaction"]["changed_count"],
            )
        )
    return 0 if payload["status"] in {"planned", "applied", "no-change", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
