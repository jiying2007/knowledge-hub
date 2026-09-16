"""Opt-in CLI for bounded read-only Operator provider discovery."""

from __future__ import annotations

import argparse
import json
import os
from typing import Sequence

from .common import KnowledgeHubError, repository_root
from .operator_binding_patch_plan import build_binding_patch_plan
from .operator_binding_proposal import build_binding_proposal
from .operator_binding_review_bundle import build_binding_review_bundle
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
    parser.add_argument(
        "--propose",
        action="store_true",
        help="build proposal-only canonical evidence changes for governed review",
    )
    parser.add_argument(
        "--plan-binding",
        action="append",
        default=[],
        metavar="PROPOSAL_FINGERPRINT",
        help=(
            "plan an exact registry patch for one explicitly selected proposal fingerprint; "
            "repeat only for different target fields"
        ),
    )
    parser.add_argument(
        "--review-binding",
        action="append",
        default=[],
        metavar="PROPOSAL_FINGERPRINT",
        help=(
            "build a deterministic review-only bundle for selected proposal fingerprints; "
            "selection is not authorization and no canonical write is performed"
        ),
    )
    parser.add_argument("--json", action="store_true")
    return parser


def _token() -> str:
    return os.environ.get("GITHUB_TOKEN", "") or os.environ.get("GH_TOKEN", "")


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    if args.plan_binding and args.review_binding:
        parser.error("--plan-binding and --review-binding are mutually exclusive")
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
        selected_binding = args.review_binding or args.plan_binding
        needs_qualification = bool(
            args.qualify or args.propose or selected_binding
        )
        qualification_payload = (
            qualify_provider_projection(provider_payload)
            if needs_qualification
            else {}
        )
        needs_proposal = bool(args.propose or selected_binding)
        proposal_payload = (
            build_binding_proposal(root, qualification_payload)
            if needs_proposal
            else {}
        )
        patch_plan_payload = (
            build_binding_patch_plan(root, proposal_payload, selected_binding)
            if selected_binding
            else {}
        )
        if args.review_binding:
            payload = build_binding_review_bundle(
                root,
                proposal_payload,
                patch_plan_payload,
            )
        elif args.plan_binding:
            payload = patch_plan_payload
        elif args.propose:
            payload = proposal_payload
        elif args.qualify:
            payload = qualification_payload
        else:
            payload = provider_payload
    except (KnowledgeHubError, OSError, UnicodeError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.review_binding:
        print("status: {}".format(payload["status"]))
        print("read_only: true")
        print("review_bundle_only: true")
        print("apply_enabled: false")
        print("selection_is_authorization: false")
        print("authorization_state: {}".format(payload["authorization_state"]))
        print("requires_governed_authorization: true")
        print("automatic_binding_enabled: false")
        print("automatic_execution_enabled: false")
        print("selected_proposal_count: {}".format(payload["selected_proposal_count"]))
        print("review_row_count: {}".format(payload["review_row_count"]))
        if payload.get("patch_plan_fingerprint"):
            print("patch_plan_fingerprint: {}".format(payload["patch_plan_fingerprint"]))
            print(
                "review_bundle_fingerprint: {}".format(
                    payload["review_bundle_fingerprint"]
                )
            )
        for row in payload["rows"]:
            print(
                "{} {} {} {} {}".format(
                    row.get("project_id", ""),
                    row.get("item_id", ""),
                    row.get("field", ""),
                    row.get("mutation_intent", ""),
                    row.get("proposal_fingerprint", ""),
                )
            )
        for reason in payload.get("reason_codes", []):
            print("reason: {}".format(reason))
    elif args.plan_binding:
        print("status: {}".format(payload["status"]))
        print("read_only: true")
        print("patch_plan_only: true")
        print("apply_enabled: false")
        print("selection_is_authorization: false")
        print("automatic_binding_enabled: false")
        print("automatic_execution_enabled: false")
        print(
            "selected_proposal_count: {}".format(
                payload["selected_proposal_count"]
            )
        )
        print("planned_item_count: {}".format(payload["planned_item_count"]))
        print("planned_write_count: {}".format(payload["planned_write_count"]))
        if payload.get("registry_before_sha256"):
            print(
                "registry_before_sha256: {}".format(
                    payload["registry_before_sha256"]
                )
            )
            print(
                "registry_after_sha256: {}".format(
                    payload["registry_after_sha256"]
                )
            )
        for row in payload["rows"]:
            print(
                "{} {} fields={} proposals={}".format(
                    row.get("project_id", ""),
                    row.get("item_id", ""),
                    ",".join(row.get("changed_fields", [])),
                    len(row.get("selected_proposal_fingerprints", [])),
                )
            )
        for reason in payload.get("reason_codes", []):
            print("reason: {}".format(reason))
    elif args.propose:
        print("status: {}".format(payload["status"]))
        print("read_only: true")
        print("proposal_only: true")
        print("automatic_binding_enabled: false")
        print("automatic_execution_enabled: false")
        print("candidate_count: {}".format(payload["candidate_count"]))
        print("proposal_count: {}".format(payload["proposal_count"]))
        print("already_present_count: {}".format(payload["already_present_count"]))
        print("blocked_conflict_count: {}".format(payload["blocked_conflict_count"]))
        print("unmappable_count: {}".format(payload["unmappable_count"]))
        for row in payload["rows"]:
            print(
                "{} {} {} {} {}".format(
                    row.get("project_id", ""),
                    row.get("field", ""),
                    row.get("proposal_status", ""),
                    row.get("mutation_intent", ""),
                    row.get("ref", ""),
                )
            )
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
    if provider_payload["error_count"] or payload.get("status") == "upstream-error":
        return 3
    if selected_binding and payload.get("status") == "blocked":
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
