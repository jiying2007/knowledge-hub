"""Binary input must remain bounded and release descriptors on every exit."""

import os
import pathlib
import subprocess
import sys
import threading

import pytest

from tools.codex_assets.knowledge_hub.bounded_process import run_bounded


def test_binary_input_output_preserves_invalid_utf8_and_nuls(tmp_path):
    data = b"\x00\xff\xe4\xb8\xad\n"
    result, overflow = run_bounded(
        [sys.executable, "-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())"],
        cwd=tmp_path, env=os.environ.copy(), input_bytes=data, raw_output=True, timeout=2,
    )
    assert result.returncode == 0 and result.stdout == data and result.stderr == b""
    assert overflow is False


def test_input_budget_rejects_before_launch(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("oversized input must not launch a process")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    with pytest.raises(ValueError, match="capture budget"):
        run_bounded([sys.executable], cwd=tmp_path, env=os.environ.copy(),
                    input_bytes=b"12345", output_limit=4)


@pytest.mark.skipif(not pathlib.Path('/proc/self/fd').exists(), reason='Linux FD accounting')
def test_input_timeout_releases_file_and_drain_resources(tmp_path):
    before_fds = len(list(pathlib.Path('/proc/self/fd').iterdir()))
    before_threads = {thread.ident for thread in threading.enumerate()}
    with pytest.raises(subprocess.TimeoutExpired):
        run_bounded([sys.executable, "-c", "import time; time.sleep(2)"],
                    cwd=tmp_path, env=os.environ.copy(), input_bytes=b"input", timeout=.1)
    assert len(list(pathlib.Path('/proc/self/fd').iterdir())) <= before_fds
    assert {thread.ident for thread in threading.enumerate()} == before_threads


def test_launch_failure_closes_private_input(tmp_path, monkeypatch):
    captured = []

    def failed(*args, **kwargs):
        captured.append(kwargs["stdin"])
        raise OSError("launch failed")

    monkeypatch.setattr(subprocess, "Popen", failed)
    with pytest.raises(OSError, match="launch failed"):
        run_bounded([sys.executable], cwd=tmp_path, env=os.environ.copy(), input_bytes=b"input")
    assert captured[0].closed
