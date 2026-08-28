"""CLI for v2 local work-activity capture, validation and reporting."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import tempfile
from typing import Iterable

from .activity import build_facts, capture_item, generate_report, load_activity_config, normalize_item, record_item
from .common import KnowledgeHubError, repository_root, resolve_today, read_utf8_bounded


def _within(path: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _output_root(root: pathlib.Path, value: str) -> pathlib.Path:
    output = pathlib.Path(value).expanduser().resolve(strict=False) if value else (root / ".tmp/activity").resolve(strict=False)
    if not (_within(output, (root / ".tmp").resolve(strict=False)) or _within(output, pathlib.Path(tempfile.gettempdir()).resolve(strict=False))):
        raise KnowledgeHubError("activity output must be under Hub .tmp or system /tmp")
    return output


def _optional_date(value: str) -> dt.date | None:
    return dt.date.fromisoformat(value) if value else None


def _report(args: argparse.Namespace, root: pathlib.Path) -> int:
    today, _ = resolve_today(args.as_of)
    config = load_activity_config(root)
    scope = args.scope or str(config.get("default_scope", ""))
    if not scope:
        payload = {
            "schema_version": 2,
            "status": "needs-input",
            "reason": "missing-scope-and-default-scope",
            "question": "请选择 personal、project 或 portfolio 报告范围。",
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 2
    payload = generate_report(
        root,
        period=args.period,
        scope=scope,
        as_of=today,
        start=_optional_date(args.start),
        end=_optional_date(args.end),
        subject_id=args.subject_id,
        project_id=args.project_id,
        codex_root=pathlib.Path(args.codex_root).expanduser(),
        detail=args.detail,
        output_root=_output_root(root, args.output_dir),
        write=not args.stdout_only,
    )
    if args.summary_json or args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.summary_json else 2))
    elif args.stdout_only:
        print(payload["markdown"], end="")
    else:
        print("status: {}".format(payload["status"]))
        print("report_path: {}".format(payload["report_path"]))
        print("facts_path: {}".format(payload["facts_path"]))
    return 0 if payload["status"] == "pass" else 2


def _record(args: argparse.Namespace, root: pathlib.Path) -> int:
    activity_date = _optional_date(args.date)
    if activity_date is None:
        activity_date, _ = resolve_today("")
    payload = record_item(
        root,
        title=args.title,
        activity_date=activity_date,
        subject_id=args.subject_id,
        project_id=args.project_id,
        item_id=args.item_id,
        status=args.status,
        verification=args.verification,
        outcomes=args.outcome,
        evidence_refs=args.evidence_ref,
        blockers=args.blocker,
        next_actions=args.next_action,
        apply=args.apply,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.json else None))
    return 0


def main(argv: Iterable[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    subparsers = parser.add_subparsers(dest="command", required=True)

    report = subparsers.add_parser("report")
    report.add_argument("--period", choices=("daily", "weekly", "custom"), required=True)
    report.add_argument("--scope", choices=("personal", "project", "portfolio"), default="")
    report.add_argument("--detail", choices=("brief", "normal", "full"), default="normal")
    report.add_argument("--as-of", default="")
    report.add_argument("--start", default="")
    report.add_argument("--end", default="")
    report.add_argument("--subject-id", default="")
    report.add_argument("--project-id", default="")
    report.add_argument("--codex-root", default="~/codex")
    report.add_argument("--output-dir", default="")
    report.add_argument("--stdout-only", action="store_true")
    report.add_argument("--json", action="store_true")
    report.add_argument("--summary-json", action="store_true")

    capture = subparsers.add_parser("capture")
    capture.add_argument("--input", required=True)
    capture.add_argument("--apply", action="store_true")
    capture.add_argument("--json", action="store_true")

    record = subparsers.add_parser("record", help="record one sanitized v2 work item without preparing a JSON file")
    record.add_argument("--title", required=True)
    record.add_argument("--date", default="")
    record.add_argument("--subject-id", default="")
    record.add_argument("--project-id", default="")
    record.add_argument("--item-id", default="")
    record.add_argument("--status", choices=("planned", "in_progress", "done", "blocked"), default="done")
    record.add_argument("--verification", choices=("verified", "reported", "missing"), default="reported")
    record.add_argument("--outcome", action="append", default=[])
    record.add_argument("--evidence-ref", action="append", default=[])
    record.add_argument("--blocker", action="append", default=[])
    record.add_argument("--next-action", action="append", default=[])
    record.add_argument("--apply", action="store_true")
    record.add_argument("--json", action="store_true")

    validate = subparsers.add_parser("validate")
    validate.add_argument("--input", required=True)

    coverage = subparsers.add_parser("coverage")
    coverage.add_argument("--period", choices=("daily", "weekly", "custom"), required=True)
    coverage.add_argument("--scope", choices=("personal", "project", "portfolio"), required=True)
    coverage.add_argument("--as-of", default="")
    coverage.add_argument("--start", default="")
    coverage.add_argument("--end", default="")
    coverage.add_argument("--subject-id", default="")
    coverage.add_argument("--project-id", default="")
    coverage.add_argument("--codex-root", default="~/codex")

    args = parser.parse_args(list(argv) if argv else None)
    root = repository_root(args.root)
    if args.command == "report":
        return _report(args, root)
    if args.command == "capture":
        payload = capture_item(root, pathlib.Path(args.input).expanduser(), apply=args.apply)
        print(json.dumps(payload, ensure_ascii=False, indent=2 if args.json else None))
        return 0
    if args.command == "record":
        return _record(args, root)
    if args.command == "validate":
        raw = json.loads(read_utf8_bounded(pathlib.Path(args.input).expanduser(), 128 * 1024, "activity input"))
        item = normalize_item(raw, source_kind="validation", source_ref="input")
        print(json.dumps({"schema_version": 2, "status": "pass", "item_id": item["item_id"]}, ensure_ascii=False))
        return 0
    today, _ = resolve_today(args.as_of)
    facts = build_facts(
        root, period=args.period, scope=args.scope, as_of=today,
        start=_optional_date(args.start), end=_optional_date(args.end),
        subject_id=args.subject_id, project_id=args.project_id,
        codex_root=pathlib.Path(args.codex_root).expanduser(), detail="normal",
    )
    print(json.dumps({"schema_version": 2, "status": facts["status"], "source_coverage": facts["source_coverage"], "warnings": facts["warnings"]}, ensure_ascii=False))
    return 0 if facts["status"] == "pass" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KnowledgeHubError, json.JSONDecodeError, OSError, ValueError) as exc:
        print(json.dumps({"schema_version": 2, "status": "needs-fix", "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
