"""CLI for human review packets and mechanically generated local forms."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Sequence

from .common import KnowledgeHubError, repository_root, resolve_today
from .review_attestation import ATTESTATION_MODES, build_attestation_packet, generate_review_form


def _emit(payload: Dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            print("{}: {}".format(key, json.dumps(value, ensure_ascii=False)))
        else:
            print("{}: {}".format(key, value))


def _item_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default="")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--id", required=True)
    parser.add_argument("--target", required=True, choices=("active", "archived", "superseded", "rejected"))
    parser.add_argument("--json", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Separate lifecycle execution authorization from human content review attestation"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    packet = subparsers.add_parser("packet", help="Build a read-only, hash-bound human decision packet")
    _item_arguments(packet)
    generate = subparsers.add_parser(
        "generate", help="Mechanically generate a local review form after explicit human attestation"
    )
    _item_arguments(generate)
    generate.add_argument("--expected-sha256", required=True)
    generate.add_argument("--attestation-mode", required=True, choices=ATTESTATION_MODES)
    generate.add_argument("--attested-by", required=True)
    generate.add_argument("--attested-at", default="")
    generate.add_argument("--attestation-source-ref", required=True)
    generate.add_argument("--attestation-text", required=True)
    generate.add_argument("--confirm-attestation", action="store_true")
    generate.add_argument("--validation-ref", action="append", default=[])
    generate.add_argument("--output", required=True)
    generate.add_argument("--dry-run", action="store_true")
    generate.add_argument("--apply", action="store_true")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    if getattr(args, "apply", False) and getattr(args, "dry_run", False):
        parser.error("--apply and --dry-run are mutually exclusive")
    root = repository_root(args.root)
    as_of, date_source = resolve_today(args.as_of)
    try:
        if args.command == "packet":
            payload = build_attestation_packet(root, args.id, args.target, as_of)
            dry_run = True
        else:
            payload = generate_review_form(
                root,
                args.id,
                args.target,
                as_of,
                args.expected_sha256,
                args.attestation_mode,
                args.attested_by,
                args.attestation_source_ref,
                args.attestation_text,
                args.output,
                args.apply,
                args.confirm_attestation,
                attested_at=args.attested_at,
                validation_refs=args.validation_ref,
            )
            dry_run = not args.apply
        payload["as_of"] = as_of.isoformat()
        payload["date_source"] = date_source
        payload["dry_run"] = dry_run
        _emit(payload, args.json)
        return 0
    except KnowledgeHubError as exc:
        _emit({"status": "error", "error": str(exc), "command": args.command}, args.json)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
