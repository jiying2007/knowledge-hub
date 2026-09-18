"""Build or verify the exact-revision Quality evidence binding."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Sequence

from .common import KnowledgeHubError, repository_root, resolve_inside
from .quality_evidence_binding import (
    DEFAULT_OUTPUT,
    build_quality_evidence_binding,
    load_binding,
    verify_quality_evidence_binding,
    write_binding,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify"))
    parser.add_argument("--root", default="")
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--binding", default=DEFAULT_OUTPUT)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        if args.action == "build":
            payload = build_quality_evidence_binding(
                root,
                source_revision=args.source_revision,
            )
            payload["binding_path"] = write_binding(root, args.binding, payload)
        else:
            binding_path = resolve_inside(root, args.binding)
            payload = verify_quality_evidence_binding(
                root,
                load_binding(binding_path),
                source_revision=args.source_revision,
            )
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.json else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
