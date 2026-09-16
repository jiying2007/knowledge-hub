"""Explicit internal CLI for governed Operator evidence binding apply transactions."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
from typing import Mapping, Sequence

from .common import KnowledgeHubError, repository_root
from .operator_binding_governed_apply import apply_governed_binding
from .operator_binding_proposal import build_binding_proposal
from .operator_candidate_qualification import qualify_provider_projection
from .operator_github_provider import execute_projection_queries
from .operator_state import build_operator_state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explicitly apply an externally authorized Operator evidence binding transaction."
    )
    parser.add_argument("--root", default="")
    parser.add_argument("--project", default="")
    parser.add_argument(
        "--field",
        choices=("", "source_refs", "validation_refs", "artifact_refs", "release_ref"),
        default="",
    )
    parser.add_argument(
        "--proposal-fingerprint",
        action="append",
        required=True,
        metavar="SHA256_FINGERPRINT",
        help="exact proposal fingerprint to apply; repeat for distinct target fields",
    )
    parser.add_argument(
        "--authorization",
        required=True,
        metavar="JSON_FILE",
        help="external P2.7 owner authorization JSON file; this CLI never generates it",
    )
    parser.add_argument(
        "--confirm-authorization-fingerprint",
        required=True,
        metavar="SHA256_FINGERPRINT",
        help="exact P2.7 authorization fingerprint reviewed by the invoking operator",
    )
    parser.add_argument(
        "--confirm-registry-before-sha256",
        required=True,
        metavar="SHA256",
        help="exact current registry/items.jsonl SHA256 reviewed by the invoking operator",
    )
    parser.add_argument(
        "--acknowledge-reviewer-identity-unverified",
        action="store_true",
        help="acknowledge that P2.7 reviewer identity was not verified by an external identity provider",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def _token() -> str:
    return os.environ.get("GITHUB_TOKEN", "") or os.environ.get("GH_TOKEN", "")


def _load_authorization(root: pathlib.Path, value: str) -> Mapping[str, object]:
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError(
            "cannot load binding authorization JSON {}: {}".format(path, exc)
        ) from exc
    if not isinstance(payload, dict):
        raise KnowledgeHubError("binding authorization JSON must be an object")
    return payload


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        state = build_operator_state(root)
        discovery = state.get("discovery", {})
        if not isinstance(discovery, dict):
            raise KnowledgeHubError("operator discovery projection is unavailable")
        provider_payload = execute_projection_queries(
            discovery,
            token=_token(),
            project_id=args.project,
            field=args.field,
        )
        if provider_payload.get("error_count"):
            raise KnowledgeHubError("provider discovery contains errors; governed apply blocked")
        qualification = qualify_provider_projection(provider_payload)
        proposal = build_binding_proposal(root, qualification)
        authorization = _load_authorization(root, args.authorization)
        payload = apply_governed_binding(
            root,
            proposal,
            args.proposal_fingerprint,
            authorization,
            confirm_authorization_fingerprint=args.confirm_authorization_fingerprint,
            confirm_registry_before_sha256=args.confirm_registry_before_sha256,
            acknowledge_reviewer_identity_unverified=args.acknowledge_reviewer_identity_unverified,
        )
    except (KnowledgeHubError, OSError, UnicodeError) as exc:
        parser.error(str(exc))

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("status: {}".format(payload["status"]))
        print("apply_requested: true")
        print("apply_performed: {}".format(str(payload["apply_performed"]).lower()))
        print("canonical_write_performed: {}".format(str(payload["canonical_write_performed"]).lower()))
        print("automatic_binding_enabled: false")
        print("automatic_execution_enabled: false")
        print("reviewer_identity_provider_verified: false")
        print(
            "reviewer_identity_unverified_acknowledged: {}".format(
                str(payload.get("reviewer_identity_unverified_acknowledged", False)).lower()
            )
        )
        print(
            "explicit_operator_confirmation_verified: {}".format(
                str(payload["explicit_operator_confirmation_verified"]).lower()
            )
        )
        if payload.get("authorization_fingerprint"):
            print("authorization_fingerprint: {}".format(payload["authorization_fingerprint"]))
        if payload.get("registry_before_sha256"):
            print("registry_before_sha256: {}".format(payload["registry_before_sha256"]))
            print("registry_after_sha256: {}".format(payload["registry_after_sha256"]))
        for path in payload.get("changed_paths", []):
            print("changed_path: {}".format(path))
        for reason in payload.get("reason_codes", []):
            print("reason: {}".format(reason))

    if payload.get("status") == "blocked":
        return 4
    if payload.get("status") != "applied":
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
