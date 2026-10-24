"""Orphan helper failures must remain structured failures, not context crashes."""
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tools.codex_assets.knowledge_hub.check_validation_post import (
    _index_security_3,
    run_body_coverage,
)


def _context(stdout, returncode=1, stderr="SYNTHETIC_PRIVATE_VALUE"):
    runner = SimpleNamespace(PIPE=subprocess.PIPE, run=Mock(return_value=
        subprocess.CompletedProcess(["synthetic-helper"], returncode, stdout, stderr)))
    return {"root": Path("."), "subprocess": runner, "json": json,
            "errors": [], "body_coverage_health": {"status": "not-run"}}


@pytest.mark.parametrize("raw", ["", "{", "null", "[]", '"text"', "1", "true", "{}"])
def test_malformed_or_empty_helper_output_fails_without_context_exception(raw):
    ctx = _context(raw)
    run_body_coverage(ctx)
    assert ctx["errors"]
    assert ctx["body_coverage_payload"] == {}
    assert ctx["body_coverage_health"]["status"] != "ok"
    assert "SYNTHETIC_PRIVATE_VALUE" not in "\n".join(ctx["errors"])


@pytest.mark.parametrize("payload", [
    {"status": "ok", "coverage_errors": "not-a-list"},
    {"status": "ok", "coverage_errors": [None]},
    {"status": "ok", "missing_registry": {}},
    {"status": "ok", "missing_registry": [1]},
])
def test_invalid_findings_are_not_projected_as_success(payload):
    ctx = _context(json.dumps(payload), returncode=0)
    run_body_coverage(ctx)
    assert ctx["errors"]
    assert ctx["body_coverage_health"]["status"] != "ok"


def test_valid_success_retains_projection_and_strict_invocation():
    payload = {"schema_version": 1, "status": "ok", "checked_count": 12,
               "coverage_errors": [], "missing_registry": []}
    ctx = _context(json.dumps(payload), returncode=0)
    run_body_coverage(ctx)
    assert ctx["errors"] == []
    assert ctx["body_coverage_health"] == payload
    command = ctx["subprocess"].run.call_args[0][0]
    assert "--all" in command and "--strict" in command and "--json" in command


def test_structured_failures_preserve_the_original_diagnostics():
    payload = {"status": "needs-fix", "coverage_errors": ["frozen inventory mismatch"],
               "missing_registry": ["projects/synthetic/new.md"]}
    ctx = _context(json.dumps(payload))
    run_body_coverage(ctx)
    assert "body-coverage:frozen inventory mismatch" in ctx["errors"]
    assert any("projects/synthetic/new.md" in error for error in ctx["errors"])


def test_zero_exit_cannot_upgrade_a_non_ok_status():
    ctx = _context('{"status":"needs-fix"}', returncode=0)
    run_body_coverage(ctx)
    assert ctx["errors"]
    assert ctx["body_coverage_health"]["status"] == "needs-fix"


def test_nonzero_exit_cannot_be_hidden_by_an_ok_label():
    ctx = _context('{"status":"ok"}', returncode=2)
    run_body_coverage(ctx)
    assert any("exit=2" in error for error in ctx["errors"])
    assert ctx["body_coverage_health"]["status"] == "needs-fix"
    assert "SYNTHETIC_PRIVATE_VALUE" not in "\n".join(ctx["errors"])


def test_findings_remain_bounded():
    ctx = _context(json.dumps({"status": "needs-fix", "coverage_errors": ["x"] * 20,
                              "missing_registry": ["synthetic"] * 20}))
    run_body_coverage(ctx)
    assert len(ctx["errors"]) == 20


def test_unreadable_text_does_not_access_missing_exception_context():
    path = Mock()
    path.read_text.side_effect = OSError("SYNTHETIC_PRIVATE_VALUE")
    ctx = {"iter_text_files": lambda roots: [path], "scan_roots": [],
           "warnings": [], "errors": [], "display_path": lambda value: "synthetic.md"}
    _index_security_3(ctx)
    assert ctx["warnings"] == ["synthetic.md: unreadable repository text"]
