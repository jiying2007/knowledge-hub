"""CLI for privacy-preserving local Knowledge Hub metrics."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import tempfile
from typing import Iterable

from .activity_report import generate_activity_report
from .common import KnowledgeHubError, repository_root, resolve_today
from .metrics import local_metrics, local_metrics_summary


def _is_within(path: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _activity_output_dir(root: pathlib.Path, value: str) -> pathlib.Path:
    output = pathlib.Path(value).expanduser().resolve(strict=False) if value else root / ".tmp/reports"
    allowed = (root / ".tmp").resolve(strict=False)
    system_tmp = pathlib.Path(tempfile.gettempdir()).resolve(strict=False)
    if not (_is_within(output, allowed) or _is_within(output, system_tmp)):
        raise KnowledgeHubError("activity report output must be under the Hub .tmp directory or system /tmp")
    return output


def _activity_report(args: argparse.Namespace, root: pathlib.Path, today: dt.date) -> int:
    payload = generate_activity_report(
        root,
        args.activity_report,
        today,
        pathlib.Path(args.codex_root).expanduser(),
        pathlib.Path(args.memory_root).expanduser(),
        _activity_output_dir(root, args.output_dir),
        write=not args.stdout_only,
    )
    if args.json or args.summary_json:
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.summary_json else 2))
    elif args.stdout_only:
        print(payload["markdown"], end="")
    else:
        print("status: {}".format(payload["status"]))
        print("report_path: {}".format(payload["report_path"]))
        print("facts_path: {}".format(payload["facts_path"]))
        print("report_sha256: {}".format(payload["report_sha256"]))
    return 0


def main(argv: Iterable[str] = ()) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--summary-json", action="store_true")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--activity-report", choices=("daily", "weekly"), default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--codex-root", default="~/codex")
    parser.add_argument("--memory-root", default="~/.codex/memories")
    parser.add_argument("--stdout-only", action="store_true")
    args = parser.parse_args(list(argv) if argv else None)
    today, _ = resolve_today(args.as_of)
    root = repository_root(args.root)
    if args.stdout_only and not args.activity_report:
        parser.error("--stdout-only requires --activity-report")
    if args.activity_report:
        return _activity_report(args, root, today)
    if args.output_dir:
        parser.error("--output-dir requires --activity-report")
    payload = local_metrics(root, today)
    if args.json or args.summary_json:
        projection = local_metrics_summary(payload) if args.summary_json else payload
        print(json.dumps(projection, ensure_ascii=False, indent=2))
    else:
        print("# Knowledge Hub Local Metrics")
        print()
        print("- invocations: {}".format(payload["usage"]["invocation_count"]))
        print("- observation_days: {}".format(payload["usage"]["observation_days"]))
        print("- found_rate: {}".format(payload["retrieval"]["found_rate"]))
        print("- performance_status: {}".format(payload["performance"]["status"]))
        print(
            "- performance_samples: search={} context={}".format(
                payload["performance"]["search_sample_count"],
                payload["performance"]["context_sample_count"],
            )
        )
        print("- adoption_ready: {}".format(str(payload["adoption"]["ready"]).lower()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
