"""CLI for the engineering and supply-chain quality contract."""

from __future__ import annotations

import argparse
import pathlib

from .common import KnowledgeHubError, pretty_json, repository_root
from .engineering import evaluate_engineering_contract, run_engineering_quality


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="knowledge-engineering-check.sh",
        description="Validate runtime support, dependency, CI and supply-chain contracts.",
    )
    parser.add_argument("--root", default="")
    parser.add_argument("--mode", choices=("contract", "full"), default="contract")
    parser.add_argument("--sbom-output", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = repository_root(args.root or None)
    try:
        if args.mode == "full":
            output = pathlib.Path(args.sbom_output).expanduser() if args.sbom_output else None
            payload = run_engineering_quality(root, sbom_output=output)
        else:
            payload = evaluate_engineering_contract(root)
    except KnowledgeHubError as exc:
        parser.error(str(exc))
    if args.json:
        print(pretty_json(payload))
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
