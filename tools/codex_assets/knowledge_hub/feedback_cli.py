"""Record explicit retrieval feedback without storing raw query text."""

from __future__ import annotations

import argparse
import json
from typing import Iterable

from .common import repository_root
from .context import TASK_TYPES
from .metrics import record_feedback


def main(argv: Iterable[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--query", required=True)
    parser.add_argument("--outcome", choices=("found", "not-found"), required=True)
    parser.add_argument("--selected-id", default="")
    parser.add_argument("--task-type", choices=sorted(TASK_TYPES), default="general")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(list(argv) if argv else None)
    if args.outcome == "found" and not args.selected_id:
        parser.error("--outcome found requires --selected-id")
    payload = record_feedback(
        repository_root(args.root),
        args.query,
        args.outcome,
        selected_id=args.selected_id,
        task_type=args.task_type,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("status: {}".format(payload["status"]))
        print("query_sha256: {}".format(payload["record"]["query_sha256"]))
        print("raw_query_stored: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
