"""Support helpers for the stable Operator provider CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
from typing import Any, Dict, Mapping, Tuple

from .common import (
    KnowledgeHubError,
    ensure_private_directory_tree,
    ensure_private_file,
    repository_root,
    resolve_inside,
)
from .operator_auto_review import build_unique_review_bundle
from .operator_auto_route import build_unique_execution_routes
from .operator_binding_authorization import validate_binding_authorization
from .operator_binding_patch_plan import build_binding_patch_plan
from .operator_binding_proposal import build_binding_proposal
from .operator_binding_review_bundle import build_binding_review_bundle
from .operator_candidate_qualification import qualify_provider_projection
from .operator_github_provider import execute_projection_queries
from .operator_machine_ratchet import build_machine_ratchet_candidate
from .operator_state import build_operator_state


def _add_binding_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--plan-binding",
        action="append",
        default=[],
        metavar="PROPOSAL_FINGERPRINT",
        help=(
            "plan an exact registry patch for one explicitly selected proposal "
            "fingerprint; repeat only for different target fields"
        ),
    )
    parser.add_argument(
        "--review-binding",
        action="append",
        default=[],
        metavar="PROPOSAL_FINGERPRINT",
        help=(
            "build a deterministic review-only bundle for selected proposal "
            "fingerprints; selection is not authorization and no canonical write "
            "is performed"
        ),
    )
    parser.add_argument(
        "--validate-binding-authorization",
        default="",
        metavar="JSON_FILE",
        help=(
            "validate externally supplied owner authorization against the exact "
            "review bundle; requires --review-binding and never applies canonical "
            "evidence"
        ),
    )


def _add_machine_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--auto-review-unique",
        action="store_true",
        help=(
            "automatically select only unambiguous P2.4 proposal targets and build "
            "the existing review bundle; selection is not authorization and no apply "
            "occurs"
        ),
    )
    parser.add_argument(
        "--auto-route-unique",
        action="store_true",
        help=(
            "partition unambiguous P2.4 proposal targets into append-only "
            "machine-ratchet and governed human-authorization routes; no canonical "
            "apply occurs"
        ),
    )
    parser.add_argument(
        "--machine-candidate-output",
        default="",
        metavar="PATH",
        help="write the non-canonical machine-ratchet candidate registry to PATH",
    )
    parser.add_argument(
        "--machine-manifest-output",
        default="",
        metavar="PATH",
        help="write the machine-ratchet proof manifest to PATH",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute generated GitHub Operator discovery queries without binding "
            "evidence."
        )
    )
    parser.add_argument("--root", default="")
    parser.add_argument("--project", default="")
    parser.add_argument(
        "--field",
        choices=(
            "",
            "source_refs",
            "validation_refs",
            "artifact_refs",
            "release_ref",
        ),
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
    _add_binding_arguments(parser)
    _add_machine_arguments(parser)
    parser.add_argument("--json", action="store_true")
    return parser


def validate_args(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> bool:
    if args.plan_binding and args.review_binding:
        parser.error("--plan-binding and --review-binding are mutually exclusive")
    if args.auto_review_unique and (args.plan_binding or args.review_binding):
        parser.error(
            "--auto-review-unique cannot be combined with explicit binding selection"
        )
    if args.auto_route_unique and (
        args.plan_binding or args.review_binding or args.auto_review_unique
    ):
        parser.error(
            "--auto-route-unique cannot be combined with explicit binding selection "
            "or --auto-review-unique"
        )
    if args.validate_binding_authorization and not args.review_binding:
        parser.error(
            "--validate-binding-authorization requires --review-binding"
        )
    machine_outputs = bool(
        args.machine_candidate_output or args.machine_manifest_output
    )
    if machine_outputs and not (
        args.machine_candidate_output and args.machine_manifest_output
    ):
        parser.error(
            "--machine-candidate-output and --machine-manifest-output must be used "
            "together"
        )
    if machine_outputs and not args.auto_route_unique:
        parser.error("machine candidate outputs require --auto-route-unique")
    return machine_outputs


def _write_noncanonical(
    root: pathlib.Path,
    relative: str,
    content: str,
) -> None:
    path = resolve_inside(root, relative)
    canonical = resolve_inside(root, "registry/items.jsonl")
    if path == canonical:
        raise KnowledgeHubError(
            "machine candidate output must not overwrite canonical registry"
        )
    ensure_private_directory_tree(root, path.parent)
    path.write_text(content, encoding="utf-8")
    ensure_private_file(path)


def _token() -> str:
    return os.environ.get("GITHUB_TOKEN", "") or os.environ.get("GH_TOKEN", "")


def _load_authorization(
    root: pathlib.Path,
    value: str,
) -> Mapping[str, object]:
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError(
            "cannot load binding authorization JSON {}: {}".format(path, exc)
        ) from exc
    if not isinstance(payload, dict):
        raise KnowledgeHubError("binding authorization JSON must be an object")
    return payload


def _projection_chain(
    root: pathlib.Path,
    args: argparse.Namespace,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    state = build_operator_state(root)
    discovery = state.get("discovery", {})
    if not isinstance(discovery, dict):
        raise KnowledgeHubError("operator discovery projection is unavailable")
    provider = execute_projection_queries(
        discovery,
        token=_token(),
        project_id=args.project,
        field=args.field,
    )
    selected = args.review_binding or args.plan_binding
    needs_qualification = bool(
        args.qualify
        or args.propose
        or selected
        or args.auto_review_unique
        or args.auto_route_unique
    )
    qualification = (
        qualify_provider_projection(provider) if needs_qualification else {}
    )
    needs_proposal = bool(
        args.propose
        or selected
        or args.auto_review_unique
        or args.auto_route_unique
    )
    proposal = build_binding_proposal(root, qualification) if needs_proposal else {}
    plan = (
        build_binding_patch_plan(root, proposal, selected)
        if selected
        else {}
    )
    review = (
        build_binding_review_bundle(root, proposal, plan)
        if args.review_binding
        else {}
    )
    return provider, qualification, proposal, plan, review


def _machine_candidate(
    root: pathlib.Path,
    args: argparse.Namespace,
    proposal: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> None:
    candidate, manifest = build_machine_ratchet_candidate(
        root,
        proposal,
        payload,
    )
    if manifest.get("status") != "ready-for-machine-ratchet":
        raise KnowledgeHubError(
            "machine ratchet candidate is not ready: {}".format(
                ",".join(
                    str(value)
                    for value in manifest.get("reason_codes", [])
                )
            )
        )
    _write_noncanonical(root, args.machine_candidate_output, candidate)
    _write_noncanonical(
        root,
        args.machine_manifest_output,
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )


def execute_command(
    args: argparse.Namespace,
    *,
    machine_outputs: bool,
) -> Tuple[Mapping[str, Any], Mapping[str, Any]]:
    root = repository_root(args.root)
    provider, qualification, proposal, plan, review = _projection_chain(root, args)
    if args.auto_route_unique:
        payload = build_unique_execution_routes(root, proposal)
        if machine_outputs and int(payload.get("machine_ratchet_count", 0) or 0):
            _machine_candidate(root, args, proposal, payload)
    elif args.auto_review_unique:
        payload = build_unique_review_bundle(root, proposal)
    elif args.validate_binding_authorization:
        authorization = _load_authorization(
            root,
            args.validate_binding_authorization,
        )
        payload = validate_binding_authorization(
            root,
            review,
            authorization,
        )
    elif args.review_binding:
        payload = review
    elif args.plan_binding:
        payload = plan
    elif args.propose:
        payload = proposal
    elif args.qualify:
        payload = qualification
    else:
        payload = provider
    return provider, payload


def _print_reasons(payload: Mapping[str, Any]) -> None:
    for reason in payload.get("reason_codes", []):
        print("reason: {}".format(reason))


def _render_auto_route(payload: Mapping[str, Any]) -> None:
    print("status: {}".format(payload["status"]))
    print("read_only: true")
    print("selection_is_authorization: false")
    print("canonical_write_performed: false")
    print("automatic_binding_enabled: false")
    print("automatic_execution_enabled: false")
    for key in (
        "machine_ratchet_count",
        "human_authorization_count",
        "ambiguous_target_count",
    ):
        print("{}: {}".format(key, payload[key]))
    _print_reasons(payload)


def _render_auto_review(payload: Mapping[str, Any]) -> None:
    print("status: {}".format(payload["status"]))
    print("read_only: true")
    print("selection_is_authorization: false")
    print("canonical_write_performed: false")
    print("automatic_binding_enabled: false")
    print("automatic_execution_enabled: false")
    print(
        "selected_proposal_count: {}".format(
            payload["selected_proposal_count"]
        )
    )
    print("ambiguous_target_count: {}".format(payload["ambiguous_target_count"]))
    _print_reasons(payload)


def _render_authorization(payload: Mapping[str, Any]) -> None:
    print("status: {}".format(payload["status"]))
    print("read_only: true")
    print("authorization_input_generated: false")
    print(
        "authorization_validated: {}".format(
            str(payload["authorization_validated"]).lower()
        )
    )
    print("reviewer_identity_provider_verified: false")
    print("apply_enabled: false")
    print("canonical_write_performed: false")
    print("automatic_binding_enabled: false")
    print("automatic_execution_enabled: false")
    for key in ("authorization_count", "approved_count", "rejected_count"):
        print("{}: {}".format(key, payload[key]))
    _print_reasons(payload)


def _render_review(payload: Mapping[str, Any]) -> None:
    print("status: {}".format(payload["status"]))
    print("read_only: true")
    print("review_bundle_only: true")
    print("apply_enabled: false")
    print("selection_is_authorization: false")
    print("authorization_state: {}".format(payload["authorization_state"]))
    print("requires_governed_authorization: true")
    print("automatic_binding_enabled: false")
    print("automatic_execution_enabled: false")
    print(
        "selected_proposal_count: {}".format(payload["selected_proposal_count"])
    )
    print("review_row_count: {}".format(payload["review_row_count"]))
    if payload.get("patch_plan_fingerprint"):
        print(
            "patch_plan_fingerprint: {}".format(
                payload["patch_plan_fingerprint"]
            )
        )
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
    _print_reasons(payload)


def _render_plan(payload: Mapping[str, Any]) -> None:
    print("status: {}".format(payload["status"]))
    print("read_only: true")
    print("patch_plan_only: true")
    print("apply_enabled: false")
    print("selection_is_authorization: false")
    print("automatic_binding_enabled: false")
    print("automatic_execution_enabled: false")
    for key in (
        "selected_proposal_count",
        "planned_item_count",
        "planned_write_count",
    ):
        print("{}: {}".format(key, payload[key]))
    if payload.get("registry_before_sha256"):
        print("registry_before_sha256: {}".format(payload["registry_before_sha256"]))
        print("registry_after_sha256: {}".format(payload["registry_after_sha256"]))
    for row in payload["rows"]:
        print(
            "{} {} fields={} proposals={}".format(
                row.get("project_id", ""),
                row.get("item_id", ""),
                ",".join(row.get("changed_fields", [])),
                len(row.get("selected_proposal_fingerprints", [])),
            )
        )
    _print_reasons(payload)


def _render_proposal(payload: Mapping[str, Any]) -> None:
    print("status: {}".format(payload["status"]))
    print("read_only: true")
    print("proposal_only: true")
    print("automatic_binding_enabled: false")
    print("automatic_execution_enabled: false")
    for key in (
        "candidate_count",
        "proposal_count",
        "already_present_count",
        "blocked_conflict_count",
        "unmappable_count",
    ):
        print("{}: {}".format(key, payload[key]))
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


def _render_qualification(payload: Mapping[str, Any]) -> None:
    print("status: {}".format(payload["status"]))
    print("read_only: true")
    print("automatic_binding_enabled: false")
    for key in ("candidate_count", "reviewable_count", "rejected_count"):
        print("{}: {}".format(key, payload[key]))
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


def _render_provider(payload: Mapping[str, Any]) -> None:
    print("status: {}".format(payload["status"]))
    print("read_only: true")
    print("automatic_binding_enabled: false")
    for key in (
        "selected_query_count",
        "executed_query_count",
        "unsupported_query_count",
        "error_count",
    ):
        print("{}: {}".format(key, payload[key]))
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


def render_text(args: argparse.Namespace, payload: Mapping[str, Any]) -> None:
    if args.auto_route_unique:
        _render_auto_route(payload)
    elif args.auto_review_unique:
        _render_auto_review(payload)
    elif args.validate_binding_authorization:
        _render_authorization(payload)
    elif args.review_binding:
        _render_review(payload)
    elif args.plan_binding:
        _render_plan(payload)
    elif args.propose:
        _render_proposal(payload)
    elif args.qualify:
        _render_qualification(payload)
    else:
        _render_provider(payload)


def exit_code(
    args: argparse.Namespace,
    provider: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> int:
    if provider["error_count"] or payload.get("status") == "upstream-error":
        return 3
    selected = args.review_binding or args.plan_binding
    if (
        selected or args.auto_review_unique or args.auto_route_unique
    ) and payload.get("status") in {"blocked", "ambiguous"}:
        return 4
    if (
        args.validate_binding_authorization
        and payload.get("status") == "rejected-by-governance"
    ):
        return 5
    return 0
