"""Timeout evidence must survive process-group cleanup without enabling retry."""

import os
import subprocess
import sys

import pytest

from tools.codex_assets.knowledge_hub.bounded_process import run_bounded
from tools.codex_assets.knowledge_hub.engineering import _run_quality_command
from tools.codex_assets.knowledge_hub import engineering


def test_timeout_keeps_bounded_partial_output(tmp_path):
    code = ('import sys,time; print("x"*4096+"stage-tail",flush=True); '
            'print("error-tail",file=sys.stderr,flush=True); time.sleep(10)')
    with pytest.raises(subprocess.TimeoutExpired) as captured:
        run_bounded([sys.executable, '-c', code], cwd=tmp_path,
                    env=os.environ.copy(), timeout=.3, output_limit=128)
    error = captured.value
    assert isinstance(error.output, bytes)
    assert len(error.output) <= 128 and error.output.endswith(b'stage-tail\n')
    assert error.stderr == b'error-tail\n'
    assert error.output_truncated is True


def test_engineering_timeout_retains_evidence_and_never_retries(tmp_path, monkeypatch):
    calls = []

    def timeout(*args, **kwargs):
        calls.append(1)
        error = subprocess.TimeoutExpired('fixture', 3, output=b'stage-proof\n', stderr=b'error-proof\n')
        error.output_truncated = True
        raise error

    monkeypatch.setattr(engineering, 'run_rtk', timeout)
    result = _run_quality_command(tmp_path, ['python3'], 3, max_attempts=3)
    assert result['status'] == 'fail' and calls == [1]
    attempt = result['attempts'][0]
    assert attempt['timed_out'] is True and attempt['timeout_sec'] == 3
    assert attempt['stdout_tail'] == ['stage-proof']
    assert attempt['stderr_tail'] == ['error-proof']
    assert attempt['output_truncated'] is True and attempt['retry_eligible'] is False
