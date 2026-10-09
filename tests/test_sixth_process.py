"""Escaped pipe holders must not produce success or retain launcher drain resources."""

import os
import pathlib
import subprocess
import sys
import threading
import time

import pytest

from tools.codex_assets.knowledge_hub.bounded_process import run_bounded


@pytest.mark.skipif(not hasattr(os, 'waitid') or not hasattr(os, 'fork'), reason='POSIX session ownership')
def test_escaped_pipe_holder_is_deadline_failure_without_threads_or_fds(tmp_path, monkeypatch):
    before_threads = {thread.ident for thread in threading.enumerate()}
    before_fds = len(list(pathlib.Path('/proc/self/fd').iterdir()))
    ready_path = tmp_path / 'escaped-ready'
    ready_at = []
    real_popen = subprocess.Popen

    def launch_ready(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        startup_deadline = time.monotonic() + 3
        while not ready_path.exists():
            if time.monotonic() >= startup_deadline:
                process.wait(timeout=2)
                pytest.fail('escaped fixture did not report readiness')
            time.sleep(.005)
        ready_at.append(time.monotonic())
        return process

    # The deadline must exercise an established escaped pipe holder, rather
    # than race Python startup under coverage or a loaded CI runner.
    monkeypatch.setattr(subprocess, 'Popen', launch_ready)
    code = ('import os,time,sys,pathlib; child=os.fork(); '
            'os._exit(0) if child else None; os.setsid(); '
            'print("escaped-pipe-proof",flush=True); pathlib.Path(sys.argv[1]).touch(); '
            'time.sleep(1); os._exit(0)')
    with pytest.raises(subprocess.TimeoutExpired) as captured:
        run_bounded([sys.executable, '-c', code, str(ready_path)],
                    cwd=tmp_path, env=os.environ.copy(), timeout=.15)
    assert time.monotonic() - ready_at[0] < 1
    assert captured.value.output_incomplete is True
    assert b'escaped-pipe-proof' in captured.value.output
    assert {thread.ident for thread in threading.enumerate()} == before_threads
    assert len(list(pathlib.Path('/proc/self/fd').iterdir())) <= before_fds
    # The deliberately escaped fixture owns its session and self-exits; the
    # launcher does not claim authority to kill an unrelated/new session.
    time.sleep(1.05)


def test_normal_completion_waits_for_eof_and_preserves_both_streams(tmp_path):
    result, overflow = run_bounded([sys.executable, '-c',
                                   'import sys; print("out"); print("err",file=sys.stderr)'],
                                  cwd=tmp_path, env=os.environ.copy(), timeout=2)
    assert result.returncode == 0 and result.stdout == 'out\n' and result.stderr == 'err\n'
    assert overflow is False


def test_lost_child_ownership_does_not_signal_a_process_group(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import bounded_process

    def ownership_lost(*args):
        raise ChildProcessError('external reaper')

    created = []
    real_popen = subprocess.Popen

    def launch(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        created.append(process)
        return process

    signalled = []
    monkeypatch.setattr(bounded_process.subprocess, 'Popen', launch)
    monkeypatch.setattr(bounded_process.os, 'waitid', ownership_lost)
    monkeypatch.setattr(bounded_process.os, 'killpg', lambda *args: signalled.append(args))
    with pytest.raises(ChildProcessError):
        run_bounded([sys.executable, '-c', 'pass'], cwd=tmp_path, env=os.environ.copy(), timeout=2)
    for process in created:
        process.wait(timeout=2)
    assert not signalled
