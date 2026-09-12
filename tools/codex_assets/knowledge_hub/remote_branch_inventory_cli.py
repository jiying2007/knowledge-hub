"""Capture remote branch inventory evidence for terminal branch GC."""

from __future__ import annotations

import argparse
import json
import os
from typing import Sequence

from .common import KnowledgeHubError, repository_root
from .remote_branch_inventory import evaluate_remote_branch_inventory, write_inventory


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument(
        "--output",
        default=".cache/knowledge-hub/remote-branch-inventory.json",
    )
    parser.add_argument(
        "--lifecycle",
        default="registry/branch-lifecycle.json",
    )
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        payload = evaluate_remote_branch_inventory(
            root,
            repository=args.repository,
            source_revision=args.source_revision,
            token=os.environ.get("GITHUB_TOKEN", ""),
            lifecycle=args.lifecycle,
        )
        payload["snapshot"] = write_inventory(root, args.output, payload)
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    # Capturing an open/blocked inventory is still a successful evidence operation.
    # The terminal-closure evaluator owns the fail-closed verdict.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
