"""CLI for the engineering and supply-chain quality contract."""

from __future__ import annotations

import argparse
import pathlib

from .common import KnowledgeHubError, pretty_json, repository_root
from .engineering import evaluate_engineering_contract, run_engineering_quality


def _blocked_preflight(checked):
    return dict(checked, phase='preflight', checks={}, errors=['engineering preflight failed'])


def _summary_projection(payload, args):
    contract = payload.get("contract", payload)
    return {
        "schema_version": 1,
        "projection": "knowledge-engineering-summary-v1",
        "status": payload.get("status", ""),
        "mode": args.mode,
        "generated_at": payload.get("generated_at", ""),
        "python_support": contract.get("python_support", {}),
        "command_surface": {
            key: contract.get("command_surface", {}).get(key)
            for key in (
                "status",
                "wrapper_count",
                "wrapper_growth",
                "daily_count",
            )
        },
        "complexity_budget": {
            key: contract.get("complexity_budget", {}).get(key)
            for key in (
                "status",
                "regression_count",
                "legacy_attention_count",
            )
        },
        "artifact_governance": {
            key: contract.get("artifact_governance", {}).get(key)
            for key in (
                "status",
                "violation_count",
                "binary_manifest_count",
            )
        },
        "check_statuses": {
            name: row.get("status", "")
            for name, row in payload.get("checks", {}).items()
        },
        "retry_evidence": {
            name: {
                "attempt_count": row.get("attempt_count", 1),
                "recovered_after_retry": row.get("recovered_after_retry", False),
            }
            for name, row in payload.get("checks", {}).items()
            if row.get("attempt_count", 1) > 1
        },
        "error_count": len(payload.get("errors", [])),
        "errors": list(payload.get("errors", []))[:20],
        "preflight": args.preflight or payload.get('phase') == 'preflight',
        "environment": payload.get('environment', {}),
        "expensive_checks_started": payload.get('expensive_checks_started'),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="knowledge-engineering-check.sh",
        description="Validate runtime support, dependency, CI and supply-chain contracts.",
    )
    parser.add_argument("--root", default="")
    parser.add_argument("--mode", choices=("contract", "full"), default="contract")
    parser.add_argument("--sbom-output", default="")
    parser.add_argument('--in-place', action='store_true', help='Run against this exact tree; normal full mode captures an isolated dirty snapshot')
    parser.add_argument('--replay', default='', help='Replay a retained failure snapshot relative to this root; requires original host input hashes')
    parser.add_argument('--preflight', action='store_true', help='Check input, interpreter, loopback and DNS capabilities without expensive checks')
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument("--json", action="store_true")
    output_mode.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    root = repository_root(args.root or None)
    try:
        if args.preflight:
            if args.replay or args.in_place or args.sbom_output:
                raise KnowledgeHubError('preflight cannot be combined with replay, in-place or SBOM overrides')
            from .engineering_preflight import preflight
            payload = preflight(root, verify_capabilities=True)
        elif args.replay:
            if args.mode != 'full' or args.in_place or args.sbom_output:
                raise KnowledgeHubError('replay requires full mode without in-place or SBOM overrides')
            from .snapshot_retention import replay_failure
            from .engineering_preflight import preflight
            checked = preflight(root, verify_capabilities=True)
            payload = replay_failure(root, args.replay) if checked['status'] == 'pass' else _blocked_preflight(checked)
        elif args.mode == "full":
            output = pathlib.Path(args.sbom_output).expanduser() if args.sbom_output else None
            if args.in_place:
                from .engineering_preflight import preflight
                checked = preflight(root, verify_capabilities=True)
                payload = (run_engineering_quality(root, sbom_output=output) if checked['status'] == 'pass'
                           else _blocked_preflight(checked))
            else:
                from .engineering_snapshot import run_snapshot_engineering
                payload = run_snapshot_engineering(root, sbom_output=output)
        else:
            payload = evaluate_engineering_contract(root)
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    if args.json or args.summary_json:
        projection = payload
        if args.summary_json:
            projection = _summary_projection(payload, args)
        print(pretty_json(projection))
    else:
        print(
            "{}: mode={} errors={}".format(
                payload["status"],
                args.mode,
                len(payload.get("errors", [])),
            )
        )
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
