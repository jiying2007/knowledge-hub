"""CLI for validating real external closure evidence without mutating canonical state."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .common import (
    KnowledgeHubError,
    ensure_private_directory_tree,
    ensure_private_file,
    repository_root,
    resolve_inside,
)
from .external_evidence import SUPPORTED_GAPS, load_and_validate_external_evidence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--input", required=True)
    parser.add_argument("--expected-gap", choices=sorted(SUPPORTED_GAPS), required=True)
    parser.add_argument("--output", default="")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        input_path = resolve_inside(root, args.input)
        receipt = load_and_validate_external_evidence(
            input_path,
            expected_gap=args.expected_gap,
        )
        if args.output:
            output = resolve_inside(root, args.output)
            ensure_private_directory_tree(root, output.parent)
            output.write_text(
                json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            ensure_private_file(output)
    except (KnowledgeHubError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(receipt, ensure_ascii=False, separators=(",", ":")))
    return 0 if receipt.get("closure_ready") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
