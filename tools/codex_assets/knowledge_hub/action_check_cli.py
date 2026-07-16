"""CLI for deterministic, fail-closed Agent action preflight."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Sequence

from .agent_runtime import ACTION_TEXT_MAX_CHARS, check_action
from .common import KnowledgeHubError, read_utf8_bounded, repository_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check a candidate action against explicit active Agent contracts.")
    parser.add_argument("--root", default="")
    parser.add_argument("--task", required=True)
    candidate = parser.add_mutually_exclusive_group(required=True)
    candidate.add_argument("--candidate")
    candidate.add_argument("--candidate-file")
    parser.add_argument("--scope-ref", action="append", default=[])
    parser.add_argument("--exception", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        candidate = args.candidate
        if args.candidate_file:
            candidate = read_utf8_bounded(
                pathlib.Path(args.candidate_file),
                ACTION_TEXT_MAX_CHARS * 4,
                "candidate file",
            )
        payload = check_action(
            repository_root(args.root),
            args.task,
            candidate or "",
            scope_refs=args.scope_ref,
            asserted_exceptions=args.exception,
        )
    except (KnowledgeHubError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("VERDICT: {}".format(payload["verdict"]))
        print("reason: {}".format(payload["reason"]))
        for row in payload["violations"]:
            print("violation: {}".format(row["id"]))
    return {"ALLOW": 0, "NEEDS_REVIEW": 2, "BLOCK": 3}[payload["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
