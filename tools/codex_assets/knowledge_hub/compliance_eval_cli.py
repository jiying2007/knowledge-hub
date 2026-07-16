"""CLI for deterministic Agent compliance cases."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Sequence

from .common import KnowledgeHubError, repository_root
from .compliance_eval import evaluate_compliance_cases


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate JSONL action cases against explicit active Agent contracts.")
    parser.add_argument("--root", default="")
    parser.add_argument("--cases", required=True)
    parser.add_argument("--minimum-cases", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        payload = evaluate_compliance_cases(
            repository_root(args.root),
            pathlib.Path(args.cases),
            minimum_cases=args.minimum_cases,
        )
    except (KnowledgeHubError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("status: {}".format(payload["status"]))
        print("passed: {}/{}".format(payload["passed"], payload["total"]))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
