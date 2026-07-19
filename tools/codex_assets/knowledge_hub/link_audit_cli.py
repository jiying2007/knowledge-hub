"""CLI for Knowledge Hub Markdown link audits."""

from __future__ import annotations

import argparse

from .common import pretty_json, repository_root
from .link_audit import audit_links, link_audit_summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="knowledge-link-audit.sh", description="Audit standard Markdown links and Obsidian Bases.")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Print full JSON output.")
    output.add_argument("--summary-json", action="store_true", help="Print bounded JSON summary.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when blocking links or Bases fail.")
    args = parser.parse_args(argv)
    payload = audit_links(repository_root())
    if args.summary_json:
        print(pretty_json(link_audit_summary(payload)))
    elif args.json:
        print(pretty_json(payload))
    else:
        print(
            "{}: files={} links={} blocking={} historical_warnings={} bases={}".format(
                payload["status"],
                payload["markdown_file_count"],
                payload["standard_link_count"],
                payload["blocking_broken_count"],
                payload["historical_warning_count"],
                len(payload["obsidian_bases"]),
            )
        )
    return 1 if args.strict and payload["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
