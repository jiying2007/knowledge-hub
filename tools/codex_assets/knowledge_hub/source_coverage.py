"""Shared source-coverage closeout selection."""

from __future__ import annotations

import datetime as dt
import pathlib
import re
from typing import Any, Dict


SOURCE_COVERAGE_RE = re.compile(
    r"^knowledge-hub-source-coverage-closeout-(\d{8})\.jsonl$"
)


def select_source_coverage_closeout(
    root: pathlib.Path,
) -> tuple[Dict[str, Any], pathlib.Path | None]:
    """Select only an explicitly date-stamped closeout, never a latest alias."""

    paths = sorted(
        (root / "artifacts/manifests").glob(
            "knowledge-hub-source-coverage-closeout-*.jsonl"
        )
    )
    dated = []
    ignored = []
    for path in paths:
        relative = str(path.relative_to(root))
        match = SOURCE_COVERAGE_RE.match(path.name)
        if not match:
            ignored.append(relative)
            continue
        date_text = match.group(1)
        try:
            dt.datetime.strptime(date_text, "%Y%m%d").date()
        except ValueError:
            ignored.append(relative)
            continue
        dated.append((date_text, relative, path))
    dated.sort(key=lambda row: (row[0], row[1]))
    return {
        "pattern": (
            "artifacts/manifests/"
            "knowledge-hub-source-coverage-closeout-*.jsonl"
        ),
        "required_filename": (
            "knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl"
        ),
        "strategy": "filename-yyyymmdd-sort-last",
        "candidate_count": len(paths),
        "candidates": [str(path.relative_to(root)) for path in paths],
        "dated_candidate_count": len(dated),
        "dated_candidates": [row[1] for row in dated],
        "ignored_non_date_candidates": ignored,
        "selected": dated[-1][1] if dated else "",
        "reason_zh": (
            "只按日期字段选择最新 closeout；非日期候选会被忽略，"
            "避免 future/latest 等文件名被静默选中。"
        ),
    }, dated[-1][2] if dated else None
