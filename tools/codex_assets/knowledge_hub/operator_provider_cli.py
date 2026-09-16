"""Opt-in CLI for bounded read-only Operator provider discovery."""

from __future__ import annotations

import argparse
import json
import os
from typing import Sequence

from .common import KnowledgeHubError, repository_root
from .operator_candidate_qualification import qualify_provider_projection
from .operator_github_provider import execute_projection_queries
from .operator_state import build_operator_state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute generated GitHub Operator discovery queries without binding evidence."
    )
    parser.add_argument("--root", default="")
    parser.add_argument("--project", default="")
    parser.add_argument(
        "--field",
        choices=("", "source_refs", "validation_refs", "artifact_refs", "release_ref"),
        default="",
    )
    parser.add_argument(
        "--qualify",
        action="store_true",
        help="classify provider candidates for governed review without binding evidence",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def _token() -> str:
    return os.environ.get("GITHUB_TOKEN", "") or os.environ.get("GH_TOKEN", "")


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
        payload = (
            qualify_provider_projection(provider_payload)
            if args.qualify
            else provider_payload
        )
    except (KnowledgeHubError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.qualify:
        print("status: {}".format(payload["status"]))
        print("read_only: true")
        print("automatic_binding_enabled: false")
        print("candidate_count: {}".format(payload["candidate_count"]))
        print("reviewable_count: {}".format(payload["reviewable_count"]))
        print("rejected_count: {}".format(payload["rejected_count"]))
        print("truncated: {}".format(str(payload["truncated"]).lower()))
        for row in payload["rows"]:
            print(
                "{} {} {} {} {}".format(
                    row.get("project_id", ""),
                    row.get("field", ""),
                    row.get("qualification_status", ""),
                    row.get("kind", ""),
                    row.get("ref", ""),
                )
            )
    else:
        print("status: {}".format(payload["status"]))
        print("read_only: true")
        print("automatic_binding_enabled: false")
        print("selected_query_count: {}".format(payload["selected_query_count"]))
        print("executed_query_count: {}".format(payload["executed_query_count"]))
        print("unsupported_query_count: {}".format(payload["unsupported_query_count"]))
        print("error_count: {}".format(payload["error_count"]))
        for result in payload["results"]:
            print(
                "{} {} {} candidates={}".format(
                    result.get("project_id", ""),
                    result.get("field", ""),
                    result.get("target", ""),
                    result.get("candidate_count", 0),
                )
            )
        for error in payload["errors"]:
            print(
                "error {} {} {}: {}".format(
                    error.get("project_id", ""),
                    error.get("field", ""),
                    error.get("target", ""),
                    error.get("error", ""),
                )
            )
    return 3 if provider_payload["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
