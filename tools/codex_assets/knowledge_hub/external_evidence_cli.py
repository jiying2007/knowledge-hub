"""CLI for validating real external closure evidence without mutating canonical state."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Sequence

from .common import KnowledgeHubError, repository_root
from .external_evidence import SUPPORTED_GAPS, load_and_validate_external_evidence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--input", required=True)
    parser.add_argument("--expected-gap", choices=sorted(SUPPORTED_GAPS), default="")
    parser.add_argument("--output", default="")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        input_path = pathlib.Path(args.input)
        if not input_path.is_absolute():
            input_path = root / input_path
        receipt = load_and_validate_external_evidence(
            input_path,
            expected_gap=args.expected_gap,
        )
        if args.output:
            output = pathlib.Path(args.output)
            if not output.is_absolute():
                output = root / output
            resolved_root = root.resolve()
            resolved_output = output.resolve()
            try:
                resolved_output.relative_to(resolved_root)
            except ValueError as exc:
                raise KnowledgeHubError("external evidence output must stay inside repository") from exc
            resolved_output.parent.mkdir(parents=True, exist_ok=True)
            resolved_output.write_text(
                json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
    except (KnowledgeHubError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(receipt, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
