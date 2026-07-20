"""Read-only transaction journal and recovery-material audit."""

from __future__ import annotations

import argparse
import json
from typing import Iterable

from .common import repository_root
from .store import audit_transactions


RECOVERY_FULL_JSON_MAX_BYTES = 256 * 1024
RECOVERY_SUMMARY_JSON_MAX_BYTES = 64 * 1024


def serialized_recovery_payload(payload, maximum_bytes: int) -> str:
    output = json.dumps(payload, ensure_ascii=False, indent=2)
    output_bytes = len(output.encode("utf-8"))
    if output_bytes > maximum_bytes:
        raise ValueError(
            "recovery output budget exceeded: {} > {}; reduce --limit or use --summary-json".format(
                output_bytes, maximum_bytes
            )
        )
    return output


def project_recovery_payload(payload, limit: int, offset: int, include_rows: bool = True):
    rows = list(payload.get("rows", []))
    shown = rows[offset:] if limit == 0 else rows[offset : offset + limit]
    next_offset = offset + len(shown)
    result = dict(payload)
    result["pagination"] = {
        "total_count": len(rows),
        "offset": offset,
        "limit": limit,
        "shown_count": len(shown),
        "has_next": next_offset < len(rows),
        "next_offset": next_offset if next_offset < len(rows) else None,
    }
    if include_rows:
        result["rows"] = shown
    else:
        result.pop("rows", None)
        result["projection"] = "knowledge-recovery-audit-summary-v1"
    return result


def main(argv: Iterable[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--transaction-id", default="")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--summary-json", action="store_true")
    parser.add_argument("--limit", type=int, default=50, help="Maximum journal rows to show (default: 50); 0 disables pagination.")
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args(list(argv) if argv else None)
    if args.json and args.summary_json:
        parser.error("--json and --summary-json are mutually exclusive")
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    if args.offset < 0:
        parser.error("--offset must be >= 0")
    full_payload = audit_transactions(repository_root(args.root), args.transaction_id)
    payload = project_recovery_payload(
        full_payload,
        limit=args.limit,
        offset=args.offset,
        include_rows=not args.summary_json,
    )
    if args.json or args.summary_json:
        maximum_bytes = (
            RECOVERY_SUMMARY_JSON_MAX_BYTES
            if args.summary_json
            else RECOVERY_FULL_JSON_MAX_BYTES
        )
        try:
            output = serialized_recovery_payload(payload, maximum_bytes)
        except ValueError as exc:
            print(
                json.dumps(
                    {
                        "status": "fail",
                        "error": "output-budget-exceeded",
                        "detail": str(exc),
                        "budget_bytes": maximum_bytes,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 2
        print(output)
    else:
        print("# Knowledge Hub Transaction Recovery Audit")
        print()
        print("- status: {}".format(payload["status"]))
        print("- transaction_count: {}".format(payload["transaction_count"]))
        print("- attention_count: {}".format(payload["attention_count"]))
        for row in payload["rows"]:
            print("- {}: {} ({})".format(row["transaction_id"], row["status"], row["recovery_action"]))
    return 0 if full_payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
