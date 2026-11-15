import json
import sys
from io import StringIO
from unittest.mock import patch

from tools.codex_assets.knowledge_hub.regression.progress import emit_case_progress


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("KNOWLEDGE_REGRESSION_PROGRESS", raising=False)
    stream = StringIO()
    with patch.object(sys, "stderr", stream):
        emit_case_progress("test_example", "start")
    assert stream.getvalue() == ""


def test_start_end_records_have_bounded_no_secrets(monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_REGRESSION_PROGRESS", "1")
    stream = StringIO()
    with patch.object(sys, "stderr", stream):
        emit_case_progress("test_example", "start")
        emit_case_progress("test_example", "end", duration_sec=4.1236, failed=2)
    lines = [line for line in stream.getvalue().splitlines() if line]
    assert len(lines) == 2
    rows = [json.loads(line.removeprefix("KH_REGRESSION_PROGRESS ")) for line in lines]
    assert rows[0] == {"schema": "kh-regression-case-progress/v1", "test": "test_example", "phase": "start"}
    assert rows[1] == {"schema": "kh-regression-case-progress/v1", "test": "test_example", "phase": "end", "duration_sec": 4.124, "failed_records": 2}


def test_rejects_log_injection(monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_REGRESSION_PROGRESS", "1")
    stream = StringIO()
    with patch.object(sys, "stderr", stream):
        emit_case_progress("test_ok\nsecret", "start")
        emit_case_progress("bad_name", "start")
        emit_case_progress("test_ok", "unknown")
    assert stream.getvalue() == ""


def test_broken_stderr_does_not_change_result(monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_REGRESSION_PROGRESS", "1")

    class Broken:
        def write(self, _):
            raise OSError("closed")

        def flush(self):
            pass

    with patch.object(sys, "stderr", Broken()):
        assert emit_case_progress("test_example", "start") is None
