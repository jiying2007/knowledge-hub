"""Read-only transaction journal and recovery-material audit."""

from __future__ import annotations

import argparse
import json
from typing import Iterable

from .common import repository_root
from .store import audit_transactions


def main(argv: Iterable[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--transaction-id", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(list(argv) if argv else None)
    payload = audit_transactions(repository_root(args.root), args.transaction_id)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("# Knowledge Hub Transaction Recovery Audit")
        print()
        print("- status: {}".format(payload["status"]))
        print("- transaction_count: {}".format(payload["transaction_count"]))
        print("- attention_count: {}".format(payload["attention_count"]))
        for row in payload["rows"]:
            print("- {}: {} ({})".format(row["transaction_id"], row["status"], row["recovery_action"]))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
