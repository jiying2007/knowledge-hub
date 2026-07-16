"""CLI for an isolated checksum-bound artifact restore drill."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
from typing import Sequence

from .artifact_restore import run_artifact_restore_drill
from .common import KnowledgeHubError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify, corrupt and restore a temporary artifact deployment."
    )
    parser.add_argument("--release-root", required=True)
    parser.add_argument("--source-label", required=True)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    release_root = pathlib.Path(args.release_root)
    if not release_root.is_absolute():
        caller_cwd = pathlib.Path(
            os.environ.get("KNOWLEDGE_CALLER_CWD", os.getcwd())
        )
        release_root = caller_cwd / release_root
    try:
        payload = run_artifact_restore_drill(
            release_root, args.source_label
        )
    except (KnowledgeHubError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("status: {}".format(payload["status"]))
        print("file_count: {}".format(payload["file_count"]))
        print("restore_integrity: {}".format(payload["phases"]["restore_integrity"]))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
