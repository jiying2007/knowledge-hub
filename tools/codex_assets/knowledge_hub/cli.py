"""CLI dispatcher used by stable shell wrappers."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Dict, Sequence

from .common import KnowledgeHubError, repository_root, resolve_today
from .lifecycle import capture, transition


def _emit(payload: Dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            print("{}: {}".format(key, json.dumps(value, ensure_ascii=False)))
        else:
            print("{}: {}".format(key, value))


def _common_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default="")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")


def _capture_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("capture", help="Capture a file as a governed item")
    _common_parser(parser)
    parser.add_argument("--source", required=True)
    parser.add_argument("--kind", required=True)
    parser.add_argument("--target", default="inbox")
    parser.add_argument("--id", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--domain", default="")
    parser.add_argument("--owner", default="leiwenjun")
    parser.add_argument("--scope", default="")
    parser.add_argument("--visibility", default="team-internal")
    parser.add_argument("--status", default="reviewing")
    parser.add_argument("--review-after", default="")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--summary-zh", default="")
    parser.add_argument("--generated-by-ai", action="store_true")
    parser.add_argument("--ai-role", default="drafted")
    parser.add_argument("--ai-model-or-tool", default="Codex")
    parser.add_argument("--source-type", default="")
    parser.add_argument("--source-from", default="")


def _transition_parser(subparsers: Any, command: str) -> None:
    parser = subparsers.add_parser(command)
    _common_parser(parser)
    parser.add_argument("--id", required=True)
    if command == "promote":
        parser.add_argument("--target", default="active", choices=("active",))
    else:
        parser.add_argument("--target", default="archived", choices=("archived", "superseded", "rejected"))
    parser.add_argument("--authorization-id", default="")
    parser.add_argument("--forms", "--review-form", dest="review_form", default="")
    parser.add_argument("--expected-sha256", "--expected-item-sha256", dest="expected_item_sha256", default="")
    parser.add_argument("--reason", default="")
    parser.add_argument("--superseded-by", default="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Knowledge Hub shared tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _capture_parser(subparsers)
    _transition_parser(subparsers, "promote")
    _transition_parser(subparsers, "retire")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    if args.apply and args.dry_run:
        parser.error("--apply and --dry-run are mutually exclusive")
    root = repository_root(args.root)
    today, date_source = resolve_today(args.as_of)
    try:
        if args.command == "capture":
            payload = capture(
                root,
                pathlib.Path(args.source),
                args.kind,
                args.target,
                today,
                args.apply,
                item_id=args.id,
                title=args.title,
                domain=args.domain,
                owner=args.owner,
                scope=args.scope,
                visibility=args.visibility,
                status=args.status,
                review_after=args.review_after,
                tags=args.tag,
                summary_zh=args.summary_zh,
                generated_by_ai=args.generated_by_ai,
                ai_role=args.ai_role,
                ai_model_or_tool=args.ai_model_or_tool,
                source_type=args.source_type,
                source_from=args.source_from,
            )
        else:
            payload = transition(
                root,
                args.id,
                args.target,
                today,
                args.apply,
                authorization_id=args.authorization_id,
                review_form=pathlib.Path(args.review_form) if args.review_form else None,
                expected_item_sha256=args.expected_item_sha256,
                reason=args.reason,
                superseded_by=args.superseded_by,
            )
        payload["as_of"] = today.isoformat()
        payload["date_source"] = date_source
        payload["dry_run"] = not args.apply
        _emit(payload, args.json)
        return 0 if payload.get("status") != "blocked" else 3
    except KnowledgeHubError as exc:
        payload = {"status": "error", "error": str(exc), "command": args.command}
        _emit(payload, args.json)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
