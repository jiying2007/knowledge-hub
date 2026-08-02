"""CLI dispatcher used by stable shell wrappers."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Dict, Sequence

from .common import KnowledgeHubError, repository_root, resolve_today
from .lifecycle import capture, transition
from .tool_asset_import_cli import import_candidate
from .tool_asset_scan import scan_tool_assets
from .tool_asset_session import close_tool_asset_session, start_tool_asset_session


SUMMARY_JSON_MAX_BYTES = 2048


def _capture_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    transaction = payload.get("transaction") if isinstance(payload.get("transaction"), dict) else {}
    writes = transaction.get("writes") if isinstance(transaction.get("writes"), list) else []
    changed_paths = transaction.get("changed_paths")
    if not isinstance(changed_paths, list):
        changed_paths = [str(row.get("path", "")) for row in writes if row.get("changed")]
    unchanged_paths = transaction.get("unchanged_paths")
    if not isinstance(unchanged_paths, list):
        unchanged_paths = []
    summary = {
        "schema_version": 1,
        "projection": "knowledge-capture-summary-v1",
        "status": payload.get("status", ""),
        "error": payload.get("error", ""),
        "command": payload.get("command", ""),
        "action": payload.get("action", ""),
        "id": payload.get("id", ""),
        "target": payload.get("target", ""),
        "created_status": payload.get("created_status", ""),
        "active_promotion": bool(payload.get("active_promotion", False)),
        "transaction": {
            "transaction_id": transaction.get("transaction_id", ""),
            "read_only": bool(transaction.get("read_only", False)),
            "write_count": transaction.get(
                "write_count", len(writes) or len(changed_paths) + len(unchanged_paths)
            ),
            "changed_count": transaction.get("changed_count", len(changed_paths)),
            "changed_path_count": len(changed_paths),
            "changed_paths_sample": changed_paths[:5],
            "rolled_back": bool(transaction.get("rolled_back", False)),
            "journal": transaction.get("journal", ""),
        },
        "derived_views": payload.get("derived_views", {}),
        "as_of": payload.get("as_of", ""),
        "dry_run": bool(payload.get("dry_run", False)),
    }
    encoded = json.dumps(summary, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > SUMMARY_JSON_MAX_BYTES:
        summary["transaction"]["changed_paths_sample"] = []
        summary["derived_views"] = {}
    return summary


def _emit(payload: Dict[str, Any], json_output: bool, summary_json: bool = False) -> None:
    if summary_json:
        summary = _capture_summary(payload)
        print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
        return
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            print("{}: {}".format(key, json.dumps(value, ensure_ascii=False)))
        else:
            print("{}: {}".format(key, value))


def _common_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default="")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--summary-json", action="store_true")


def _capture_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("capture", help="Capture a file as a governed item")
    _common_parser(parser)
    parser.add_argument("--source", default="")
    parser.add_argument("--kind", default="")
    parser.add_argument("--tool-asset-candidate", default="")
    parser.add_argument("--scan-tool-assets", action="store_true")
    parser.add_argument("--tool-asset-session-start", action="store_true")
    parser.add_argument("--tool-asset-session-close", action="store_true")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--hub-candidate-out", default="")
    parser.add_argument("--session-state-out", default="")
    parser.add_argument("--session-state", default="")
    parser.add_argument("--session-id", default="")
    parser.add_argument("--observation-ledger", default="")
    parser.add_argument("--used-tool-path", action="append", default=[])
    parser.add_argument("--source-repo", default="")
    parser.add_argument("--session-path", action="append", default=[])
    parser.add_argument("--minimum-score", type=int, default=50)
    parser.add_argument("--unit-tests", choices=("pass", "fail", "not-run", "not-applicable"), default="not-run")
    parser.add_argument("--cli-help", choices=("pass", "fail", "not-run", "not-applicable"), default="not-run")
    parser.add_argument("--candidate-dry-run", choices=("pass", "fail", "not-run", "not-applicable"), default="not-run")
    parser.add_argument("--non-repo-cwd", choices=("pass", "fail", "not-run", "not-applicable"), default="not-run")
    parser.add_argument("--hub-dry-run", action="store_true")
    parser.add_argument("--target", default="inbox")
    parser.add_argument("--id", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--domain", default="")
    parser.add_argument("--owner", default="leiwenjun")
    parser.add_argument("--scope", default="")
    parser.add_argument("--visibility", default="team-internal")
    parser.add_argument("--status", default="reviewing")
    parser.add_argument("--review-after", default="")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--summary-zh", default="")
    parser.add_argument("--generated-by-ai", action="store_true")
    parser.add_argument("--ai-role", default="drafted")
    parser.add_argument("--ai-model-or-tool", default="Codex")
    parser.add_argument("--source-type", default="")
    parser.add_argument("--source-from", default="")


def _transition_parser(subparsers: Any, command: str) -> None:
    parser = subparsers.add_parser(command)
    _common_parser(parser)
    parser.add_argument("--id", required=True)
    if command == "promote":
        parser.add_argument("--target", default="active", choices=("active",))
    else:
        parser.add_argument("--target", default="archived", choices=("archived", "superseded", "rejected"))
    parser.add_argument("--authorization-id", default="")
    parser.add_argument("--forms", "--review-form", dest="review_form", default="")
    parser.add_argument("--expected-sha256", "--expected-item-sha256", dest="expected_item_sha256", default="")
    parser.add_argument("--reason", default="")
    parser.add_argument("--superseded-by", default="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Knowledge Hub shared tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _capture_parser(subparsers)
    _transition_parser(subparsers, "promote")
    _transition_parser(subparsers, "retire")
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv else None)
    if args.apply and args.dry_run:
        parser.error("--apply and --dry-run are mutually exclusive")
    root = repository_root(args.root)
    today, date_source = resolve_today(args.as_of)
    try:
        if args.command == "capture":
            session_mode_count = sum(
                int(value)
                for value in (
                    args.scan_tool_assets,
                    args.tool_asset_session_start,
                    args.tool_asset_session_close,
                    bool(args.tool_asset_candidate),
                )
            )
            if session_mode_count > 1:
                raise KnowledgeHubError("tool asset scan/start/close/import modes are mutually exclusive")
            validation = {
                "unit_tests": args.unit_tests,
                "cli_help": args.cli_help,
                "dry_run": args.candidate_dry_run,
                "non_repo_cwd": args.non_repo_cwd,
            }
            if args.tool_asset_session_start:
                if args.apply or args.hub_dry_run:
                    raise KnowledgeHubError("session start is local runtime state only and cannot apply or plan Hub import")
                if not args.repo_root or not args.session_state_out:
                    raise KnowledgeHubError("session start requires --repo-root and --session-state-out")
                payload = start_tool_asset_session(
                    root,
                    pathlib.Path(args.repo_root),
                    pathlib.Path(args.session_state_out),
                    source_repo=args.source_repo,
                    session_id=args.session_id,
                )
            elif args.tool_asset_session_close:
                if args.apply:
                    raise KnowledgeHubError("session close is report-only and cannot combine with --apply")
                if not args.repo_root or not args.session_state or not args.hub_candidate_out:
                    raise KnowledgeHubError(
                        "session close requires --repo-root, --session-state and --hub-candidate-out"
                    )
                ledger = args.observation_ledger or str(
                    root / ".cache/knowledge-hub/tool-assets/observations.jsonl"
                )
                payload = close_tool_asset_session(
                    root,
                    pathlib.Path(args.repo_root),
                    pathlib.Path(args.session_state),
                    pathlib.Path(args.hub_candidate_out),
                    pathlib.Path(ledger),
                    validation,
                    used_paths=args.used_tool_path,
                    minimum_score=args.minimum_score,
                )
                if args.hub_dry_run and payload.get("hub_candidate_ready") and payload.get("candidate_output"):
                    payload["hub_plan"] = import_candidate(
                        root,
                        pathlib.Path(str(payload["candidate_output"])),
                        today,
                        False,
                        owner=args.owner,
                        review_after=args.review_after,
                    )
                elif args.hub_dry_run:
                    payload["hub_plan"] = {
                        "status": "not-ready",
                        "reason": "cross-session/project aggregation threshold not reached",
                    }
            elif args.scan_tool_assets:
                if args.apply:
                    raise KnowledgeHubError("--scan-tool-assets is report-only and cannot combine with --apply")
                if not args.repo_root or not args.hub_candidate_out:
                    raise KnowledgeHubError("--scan-tool-assets requires --repo-root and --hub-candidate-out")
                if args.source or args.kind or args.tool_asset_candidate:
                    raise KnowledgeHubError("--scan-tool-assets cannot combine with capture/import inputs")
                if args.hub_dry_run and not args.session_path:
                    raise KnowledgeHubError("--hub-dry-run requires at least one explicit --session-path")
                payload = scan_tool_assets(
                    root,
                    pathlib.Path(args.repo_root),
                    pathlib.Path(args.hub_candidate_out),
                    validation,
                    source_repo=args.source_repo,
                    minimum_score=args.minimum_score,
                    session_paths=args.session_path,
                )
                if args.hub_dry_run and payload.get("hub_candidate_generated"):
                    payload["hub_plan"] = import_candidate(
                        root,
                        pathlib.Path(str(payload["candidate_output"])),
                        today,
                        False,
                        owner=args.owner,
                        review_after=args.review_after,
                    )
            elif args.tool_asset_candidate:
                if args.source or args.kind:
                    raise KnowledgeHubError("--tool-asset-candidate cannot combine with --source or --kind")
                payload = import_candidate(
                    root,
                    pathlib.Path(args.tool_asset_candidate),
                    today,
                    args.apply,
                    owner=args.owner,
                    review_after=args.review_after,
                )
            else:
                if not args.source or not args.kind:
                    raise KnowledgeHubError("capture requires --source and --kind unless --tool-asset-candidate is used")
                payload = capture(
                    root,
                    pathlib.Path(args.source),
                    args.kind,
                    args.target,
                    today,
                    args.apply,
                    item_id=args.id,
                    title=args.title,
                    domain=args.domain,
                    owner=args.owner,
                    scope=args.scope,
                    visibility=args.visibility,
                    status=args.status,
                    review_after=args.review_after,
                    tags=args.tag,
                    summary_zh=args.summary_zh,
                    generated_by_ai=args.generated_by_ai,
                    ai_role=args.ai_role,
                    ai_model_or_tool=args.ai_model_or_tool,
                    source_type=args.source_type,
                    source_from=args.source_from,
                )
        else:
            payload = transition(
                root,
                args.id,
                args.target,
                today,
                args.apply,
                authorization_id=args.authorization_id,
                review_form=pathlib.Path(args.review_form) if args.review_form else None,
                expected_item_sha256=args.expected_item_sha256,
                reason=args.reason,
                superseded_by=args.superseded_by,
            )
        payload["as_of"] = today.isoformat()
        payload["date_source"] = date_source
        payload["dry_run"] = not args.apply
        _emit(payload, args.json, args.summary_json)
        return 0 if payload.get("status") != "blocked" else 3
    except KnowledgeHubError as exc:
        payload = {
            "status": "error",
            "error": str(exc),
            "command": args.command,
            "as_of": today.isoformat(),
            "date_source": date_source,
            "dry_run": not args.apply,
        }
        _emit(payload, args.json, args.summary_json)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
