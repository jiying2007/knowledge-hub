"""CLI for the offline Knowledge Hub restore drill."""

from __future__ import annotations

import argparse
import sys

from .common import KnowledgeHubError, pretty_json, repository_root, resolve_today
from .output_contract import status_contract
from .restore import run_restore_drill
from .schemas import validate_instance


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="knowledge-restore-drill.sh",
        description="Restore a delivery candidate or committed HEAD in /tmp and run offline smoke gates.",
    )
    parser.add_argument("--as-of", default="")
    parser.add_argument("--source-mode", choices=("candidate", "head"), default="candidate")
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument("--json", action="store_true")
    output_mode.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        today, _ = resolve_today(args.as_of)
        root = repository_root()
        payload = run_restore_drill(root, today.isoformat(), source_mode=args.source_mode)
        schema_validation = validate_instance(root, "restore-drill-v4", payload)
        payload["schema_validation"] = schema_validation
        if schema_validation["status"] != "pass":
            payload["status"] = "needs-fix"
        payload["status_contract"] = status_contract(payload["status"])
    except KnowledgeHubError as exc:
        payload = {"status": "blocked", "error": str(exc)}
        if args.json or args.summary_json:
            print(pretty_json(payload))
        else:
            print("blocked: {}".format(exc), file=sys.stderr)
        return 1
    if args.json or args.summary_json:
        projection = payload
        if args.summary_json:
            environment = payload.get("execution_environment", {})
            projection = {
                "schema_version": 2,
                "projection": "knowledge-restore-summary-v2",
                "status": payload.get("status", ""),
                "status_contract": payload.get("status_contract", {}),
                "source_mode": payload.get("source_mode", ""),
                "source_revision": payload.get("source_revision", ""),
                "candidate_signature": payload.get("candidate_signature", ""),
                "copied_file_count": payload.get("copied_file_count", 0),
                "failed_checks": payload.get("failed_checks", []),
                "network_used": payload.get("network_used", False),
                "execution_environment": {
                    key: environment.get(key)
                    for key in (
                        "provider",
                        "repository",
                        "revision",
                        "event",
                        "ref",
                        "run_id",
                        "workflow_ref",
                        "remote_checkout_verified",
                        "remote_published_ref_verified",
                        "offsite_environment_verified",
                        "evidence_sha256",
                    )
                },
                "schema_validation": payload.get("schema_validation", {}),
                "duration_ms": payload.get("duration_ms", 0),
            }
        print(pretty_json(projection))
    else:
        print("{}: copied={} failed_checks={}".format(payload["status"], payload["copied_file_count"], len(payload["failed_checks"])))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
