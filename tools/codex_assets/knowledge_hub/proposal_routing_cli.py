"""CLI for report-only Agent proposal shadow routing."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Sequence

from .common import KnowledgeHubError, read_utf8_bounded, repository_root
from .proposal_routing import (
    PROPOSAL_MAX_BYTES,
    assess_proposal,
    record_shadow_assessment,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assess a proposal through the default-disabled shadow review policy.")
    parser.add_argument("--root", default="")
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--policy", default="registry/agent-review-policy.json")
    parser.add_argument("--client-id", default="untrusted")
    parser.add_argument("--staged-today", type=int, default=0)
    parser.add_argument("--write-auto-granted", action="store_true")
    parser.add_argument("--record-shadow", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        proposal_path = pathlib.Path(args.proposal)
        proposal = json.loads(
            read_utf8_bounded(
                proposal_path,
                PROPOSAL_MAX_BYTES,
                "proposal file",
            )
        )
        payload = assess_proposal(
            root,
            proposal,
            client_id=args.client_id,
            staged_today=args.staged_today,
            write_auto_granted=args.write_auto_granted,
            policy_path=args.policy,
        )
        if args.record_shadow:
            payload["shadow_audit"] = {
                "recorded": True,
                "path": str(record_shadow_assessment(root, payload).relative_to(root)),
                "content_stored": False,
            }
    except (KnowledgeHubError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("actual_route: {}".format(payload["actual_route"]))
        print("eligible_route: {}".format(payload["eligible_route"]))
        print("reason_codes: {}".format(",".join(payload["reason_codes"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
