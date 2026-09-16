"""Read-only internal CLI for governed Operator rollback lifecycle receipts."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Mapping, Sequence

from .common import KnowledgeHubError, repository_root
from .operator_binding_rollback_receipt import build_governed_rollback_receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify one completed P2.10 rollback against its original P2.8 apply "
            "without performing rollback or reapply."
        )
    )
    parser.add_argument("--root", default="")
    parser.add_argument(
        "--apply-result",
        required=True,
        metavar="JSON_FILE",
        help="saved P2.8 governed-apply JSON result",
    )
    parser.add_argument(
        "--rollback-result",
        required=True,
        metavar="JSON_FILE",
        help="saved P2.10 governed-rollback JSON result",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def _load_json_object(
    root: pathlib.Path,
    value: str,
    label: str,
) -> Mapping[str, object]:
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError(
            "cannot load {} JSON {}: {}".format(label, path, exc)
        ) from exc
    if not isinstance(payload, dict):
        raise KnowledgeHubError("{} JSON must be an object".format(label))
    return payload


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        apply_result = _load_json_object(root, args.apply_result, "governed apply result")
        rollback_result = _load_json_object(
            root,
            args.rollback_result,
            "governed rollback result",
        )
        payload = build_governed_rollback_receipt(
            root,
            apply_result,
            rollback_result,
        )
    except (KnowledgeHubError, OSError, UnicodeError) as exc:
        parser.error(str(exc))

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("status: {}".format(payload["status"]))
        print("read_only: true")
        print("canonical_write_performed: false")
        print("automatic_binding_enabled: false")
        print("automatic_execution_enabled: false")
        print("receipt_generated: {}".format(str(payload["receipt_generated"]).lower()))
        print(
            "current_state_matches_rollback_result: {}".format(
                str(payload["current_state_matches_rollback_result"]).lower()
            )
        )
        print("reapply_ready: false")
        print("requires_new_governed_apply: true")
        print("original_apply_authorization_reusable: false")
        print("rollback_authorization_reusable: false")
        print("reapply_performed: false")
        print("reviewer_identity_provider_verified: false")
        if payload.get("rollback_transaction_id"):
            print(
                "rollback_transaction_id: {}".format(
                    payload["rollback_transaction_id"]
                )
            )
        if payload.get("rollback_receipt_fingerprint"):
            print(
                "rollback_receipt_fingerprint: {}".format(
                    payload["rollback_receipt_fingerprint"]
                )
            )
        if payload.get("registry_current_sha256"):
            print(
                "registry_current_sha256: {}".format(
                    payload["registry_current_sha256"]
                )
            )
        for reason in payload.get("reason_codes", []):
            print("reason: {}".format(reason))

    if payload.get("status") == "blocked":
        return 4
    if payload.get("status") == "post-rollback-state-drift":
        return 5
    if payload.get("status") != "verified-current-post-rollback-state":
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
