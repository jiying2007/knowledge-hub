"""Read-only internal CLI for governed Operator apply receipts and rollback readiness."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Mapping, Sequence

from .common import KnowledgeHubError, repository_root
from .operator_binding_apply_receipt import build_governed_apply_receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify an exact P2.8 apply result, transaction journal, and before backup "
            "without performing rollback."
        )
    )
    parser.add_argument("--root", default="")
    parser.add_argument(
        "--apply-result",
        required=True,
        metavar="JSON_FILE",
        help="saved P2.8 governed-apply JSON result to verify",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def _load_apply_result(root: pathlib.Path, value: str) -> Mapping[str, object]:
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError(
            "cannot load governed apply result JSON {}: {}".format(path, exc)
        ) from exc
    if not isinstance(payload, dict):
        raise KnowledgeHubError("governed apply result JSON must be an object")
    return payload


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        apply_result = _load_apply_result(root, args.apply_result)
        payload = build_governed_apply_receipt(root, apply_result)
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
        print("rollback_ready: {}".format(str(payload["rollback_ready"]).lower()))
        print("rollback_performed: false")
        print("reviewer_identity_provider_verified: false")
        if payload.get("transaction_id"):
            print("transaction_id: {}".format(payload["transaction_id"]))
        if payload.get("receipt_fingerprint"):
            print("receipt_fingerprint: {}".format(payload["receipt_fingerprint"]))
        if payload.get("registry_current_sha256"):
            print("registry_current_sha256: {}".format(payload["registry_current_sha256"]))
        rollback_plan = payload.get("rollback_plan", {})
        if isinstance(rollback_plan, dict) and rollback_plan:
            print("rollback_plan_status: {}".format(rollback_plan.get("status", "")))
            print(
                "rollback_expected_current_sha256: {}".format(
                    rollback_plan.get("expected_current_sha256", "")
                )
            )
            print(
                "rollback_restore_sha256: {}".format(
                    rollback_plan.get("restore_sha256", "")
                )
            )
        for reason in payload.get("reason_codes", []):
            print("reason: {}".format(reason))

    if payload.get("status") == "blocked":
        return 4
    if payload.get("status") == "post-apply-state-drift":
        return 5
    if payload.get("status") != "verified-current-post-apply-state":
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
