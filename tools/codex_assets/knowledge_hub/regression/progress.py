"""Opt-in, bounded stderr progress for long Knowledge Hub regression suites.

Progress only describes the deterministic regression fixture execution; it
never substitutes for the suite's final result or Quality status.
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading

_LOCK = threading.Lock()
_NAME = re.compile(r"test_[a-zA-Z0-9_]{1,120}\Z")


def emit_case_progress(name: str, phase: str, *, duration_sec: float = 0.0, failed: int = 0) -> None:
    """Emit safe, optional start/end records without influencing test outcomes."""
    if os.environ.get("KNOWLEDGE_REGRESSION_PROGRESS") != "1":
        return
    if not isinstance(name, str) or _NAME.fullmatch(name) is None or phase not in ("start", "end"):
        return
    row = {
        "schema": "kh-regression-case-progress/v1",
        "test": name,
        "phase": phase,
    }
    if phase == "end":
        row["duration_sec"] = round(float(duration_sec), 3)
        row["failed_records"] = max(0, int(failed))
    try:
        with _LOCK:
            print("KH_REGRESSION_PROGRESS " + json.dumps(row, sort_keys=True), file=sys.stderr, flush=True)
    except (OSError, ValueError, TypeError, OverflowError):
        # Diagnostics cannot change the result of the regression test itself.
        return
