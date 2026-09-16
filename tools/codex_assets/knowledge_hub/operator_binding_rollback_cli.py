"""Explicit internal CLI for governed Operator binding rollback transactions."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Mapping, Sequence

from .common import KnowledgeHubError, repository_root
from .operator_binding_governed_rollback import (
    perform_governed_rollback,
    validate_rollback_authorization,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate or explicitly execute a separately authorized Operator binding rollback."
        )
    )
    parser.add_argument("--root", default="")
    parser.add_argument(
        "--apply-result",
        required=True,
        metavar="JSON_FILE",
        help="exact P2.8 applied-result JSON used to recompute the P2.9 receipt",
    )
    parser.add_argument(
        "--rollback-authorization",
        required=True,
        metavar="JSON_FILE",
        help="external P2.10 rollback authorization JSON; this CLI never generates it",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="perform the governed rollback after all independent confirmations pass",
    )
    parser.add_argument(
        "--confirm-receipt-fingerprint",
        default="",
        metavar="SHA256_FINGERPRINT",
        help="exact P2.9 receipt fingerprint reviewed by the invoking operator",
    )
    parser.add_argument(
        "--confirm-rollback-authorization-fingerprint",
        default="",
        metavar="SHA256_FINGERPRINT",
        help="exact validated rollback-authorization fingerprint reviewed by the operator",
    )
    parser.add_argument(
        "--confirm-registry-current-sha256",
        default="",
        metavar="SHA256",
        help="exact current post-apply registry SHA256 reviewed by the operator",
    )
    parser.add_argument(
        "--acknowledge-reviewer-identity-unverified",
        action="store_true",
        help=(
            "acknowledge that reviewed_by is structurally checked but not externally IdP-verified; "
            "required for --execute"
        ),
    )
    parser.add_argument("--json", action="store_true")
    return parser


def _load_json(root: pathlib.Path, value: str, label: str) -> Mapping[str, object]:
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("cannot load {} JSON {}: {}".format(label, path, exc)) from exc
    if not isinstance(payload, dict):
        raise KnowledgeHubError("{} JSON must be an object".format(label))
    return payload


def _require_execute_confirmations(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if not args.execute:
        return
    missing = []
    if not args.confirm_receipt_fingerprint:
        missing.append("--confirm-receipt-fingerprint")
    if not args.confirm_rollback_authorization_fingerprint:
        missing.append("--confirm-rollback-authorization-fingerprint")
    if not args.confirm_registry_current_sha256:
        missing.append("--confirm-registry-current-sha256")
    if not args.acknowledge_reviewer_identity_unverified:
        missing.append("--acknowledge-reviewer-identity-unverified")
    if missing:
        parser.error("--execute requires {}".format(", ".join(missing)))


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    _require_execute_confirmations(parser, args)
    try:
        root = repository_root(args.root)
        apply_payload = _load_json(root, args.apply_result, "apply result")
        authorization = _load_json(
            root,
            args.rollback_authorization,
            "rollback authorization",
        )
        if args.execute:
            payload = perform_governed_rollback(
                root,
                apply_payload,
                authorization,
                confirm_receipt_fingerprint=args.confirm_receipt_fingerprint,
                confirm_rollback_authorization_fingerprint=(
                    args.confirm_rollback_authorization_fingerprint
                ),
                confirm_registry_current_sha256=args.confirm_registry_current_sha256,
                acknowledge_reviewer_identity_unverified=(
                    args.acknowledge_reviewer_identity_unverified
                ),
            )
        else:
            payload = validate_rollback_authorization(
                root,
                apply_payload,
                authorization,
            )
    except (KnowledgeHubError, OSError, UnicodeError) as exc:
        parser.error(str(exc))

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("status: {}".format(payload["status"]))
        print("read_only: {}".format(str(payload["read_only"]).lower()))
        print("automatic_execution_enabled: false")
        print("reviewer_identity_provider_verified: false")
        print(
            "rollback_authorization_validated: {}".format(
                str(payload["rollback_authorization_validated"]).lower()
            )
        )
        print("rollback_ready: {}".format(str(payload["rollback_ready"]).lower()))
        print("rollback_performed: {}".format(str(payload["rollback_performed"]).lower()))
        if payload.get("rollback_authorization_fingerprint"):
            print(
                "rollback_authorization_fingerprint: {}".format(
                    payload["rollback_authorization_fingerprint"]
                )
            )
        for row in payload.get("rollback_scope", []):
            print(
                "scope {} {} fields={}".format(
                    row.get("project_id", ""),
                    row.get("item_id", ""),
                    ",".join(row.get("changed_fields", [])),
                )
            )
        for path in payload.get("changed_paths", []):
            print("changed_path: {}".format(path))
        for reason in payload.get("reason_codes", []):
            print("reason: {}".format(reason))

    if payload.get("status") == "blocked":
        return 4
    if payload.get("status") == "rejected-by-governance":
        return 5
    if args.execute and payload.get("status") != "rolled-back":
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
