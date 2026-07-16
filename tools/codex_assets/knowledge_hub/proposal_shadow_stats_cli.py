"""CLI for privacy-preserving proposal shadow audit statistics."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .common import KnowledgeHubError, repository_root
from .proposal_routing import shadow_audit_stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize the local report-only proposal shadow audit."
    )
    parser.add_argument("--root", default="")
    parser.add_argument(
        "--audit",
        default=".cache/knowledge-hub/proposal-route-shadow.jsonl",
    )
    parser.add_argument("--policy", default="registry/agent-review-policy.json")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        payload = shadow_audit_stats(
            repository_root(args.root),
            audit_path=args.audit,
            policy_path=args.policy,
        )
    except (KnowledgeHubError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("status: {}".format(payload["status"]))
        print("sample_count: {}".format(payload["sample_count"]))
        print(
            "actual_non_human_route_count: {}".format(
                payload["safety"]["actual_non_human_route_count"]
            )
        )
    return 1 if payload["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
