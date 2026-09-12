"""CLI for the Knowledge Hub terminal closure contract."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Dict, Mapping, Sequence

from .common import (
    KnowledgeHubError,
    ensure_private_directory_tree,
    ensure_private_file,
    repository_root,
    resolve_inside,
)
from .terminal_closure import DEFAULT_POLICY, evaluate_terminal_closure


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--policy", default=DEFAULT_POLICY)
    parser.add_argument("--snapshot", default="")
    parser.add_argument("--output", default="")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--summary-json", action="store_true")
    return parser


def _summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    external = payload.get("external_closure", {})
    legacy = payload.get("bounded_legacy", {})
    branch_gc = payload.get("branch_gc", {})
    return {
        "schema_version": 1,
        "projection": "knowledge-hub-terminal-closure-summary-v1",
        "status": payload.get("status", "blocked"),
        "terminal": bool(payload.get("terminal", False)),
        "blockers": list(payload.get("blockers", [])),
        "external_open_count": int(external.get("open_count", 0) or 0)
        if isinstance(external, Mapping)
        else 0,
        "legacy_module_count": int(legacy.get("legacy_module_count", 0) or 0)
        if isinstance(legacy, Mapping)
        else 0,
        "legacy_artifact_reference_count": int(
            legacy.get("legacy_artifact_reference_count", 0) or 0
        )
        if isinstance(legacy, Mapping)
        else 0,
        "branch_gc_status": str(branch_gc.get("status", "open"))
        if isinstance(branch_gc, Mapping)
        else "open",
    }


def _write_output(root: pathlib.Path, relative: str, payload: Mapping[str, Any]) -> None:
    path = resolve_inside(root, relative)
    ensure_private_directory_tree(root, path.parent)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    ensure_private_file(path)


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        payload = evaluate_terminal_closure(
            root,
            policy_path=args.policy,
            snapshot_path=args.snapshot,
        )
        if args.output:
            _write_output(root, args.output, payload)
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    rendered = _summary(payload) if args.summary_json else payload
    print(json.dumps(rendered, ensure_ascii=False, indent=2 if args.json else None))
    return 0 if payload.get("terminal") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
