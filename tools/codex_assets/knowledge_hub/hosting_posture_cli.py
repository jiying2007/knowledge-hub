"""Capture hosted repository posture bound to the current branch inventory."""

from __future__ import annotations

import argparse
import json
import os
from typing import Sequence

from .common import KnowledgeHubError, repository_root
from .hosting_posture import evaluate_hosting_posture, write_hosting_posture
from .schemas import validate_instance


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--branch-inventory", default=".cache/knowledge-hub/remote-branch-inventory.json")
    parser.add_argument("--output", default=".cache/knowledge-hub/hosting-posture.json")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        payload = evaluate_hosting_posture(
            root,
            repository=args.repository,
            source_revision=args.source_revision,
            branch_inventory=args.branch_inventory,
            token=os.environ.get("GITHUB_TOKEN", ""),
        )
        validation = validate_instance(root, "hosting-posture-v1", payload)
        if validation.get("status") != "pass":
            raise KnowledgeHubError(
                "hosting posture contract validation failed: {}".format(
                    validation.get("errors", [])
                )
            )
        payload["snapshot"] = write_hosting_posture(root, args.output, payload)
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
