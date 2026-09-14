"""CLI for building and validating hosted signed quality attestation materials."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Sequence

from .common import KnowledgeHubError, repository_root
from .signed_attestation import (
    DEFAULT_OUTPUT,
    build_signed_quality_materials,
    verify_hosted_attestation,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    sub = parser.add_subparsers(dest="operation", required=True)
    build = sub.add_parser("build")
    build.add_argument("--source-revision", required=True)
    build.add_argument("--output", default=DEFAULT_OUTPUT)
    verify = sub.add_parser("verify-hosted")
    verify.add_argument("--source-revision", required=True)
    verify.add_argument("--source-ref", required=True)
    verify.add_argument("--signer-workflow", required=True)
    verify.add_argument("--verification", required=True)
    verify.add_argument("--bundle", required=True)
    verify.add_argument("--attestation-id", required=True)
    verify.add_argument("--attestation-url", required=True)
    verify.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        if args.operation == "build":
            payload = build_signed_quality_materials(
                root,
                source_revision=args.source_revision,
                output_relative=args.output,
            )
        else:
            payload = verify_hosted_attestation(
                root,
                verification_path=pathlib.Path(args.verification),
                source_revision=args.source_revision,
                source_ref=args.source_ref,
                signer_workflow=args.signer_workflow,
                bundle_path=pathlib.Path(args.bundle),
                attestation_id=args.attestation_id,
                attestation_url=args.attestation_url,
                output_relative=args.output,
            )
    except (KnowledgeHubError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0 if payload.get("status", "pass") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
