"""Own a process session and drain bounded output, including on timeout."""

from __future__ import annotations

import os
import signal
import subprocess
import selectors
import tempfile
import time


class BoundedTimeoutExpired(subprocess.TimeoutExpired):
    """Timeout with explicit bounded capture completeness."""

    output_truncated = False
    output_incomplete = True


def _launch(command, cwd, env, input_bytes, output_limit):
    arguments = dict(cwd=cwd, env=env, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, start_new_session=True)
    if input_bytes is None:
        return subprocess.Popen(command, **arguments)
    if not isinstance(input_bytes, bytes) or len(input_bytes) > output_limit:
        raise ValueError("input must be bytes within the capture budget")
    # A private file avoids pipe-writer threads and input/output deadlocks.
    # Popen duplicates the descriptor; the launcher closes its copy immediately.
    with tempfile.TemporaryFile() as stream:
        stream.write(input_bytes)
        stream.seek(0)
        return subprocess.Popen(command, stdin=stream, **arguments)


def run_bounded(command, *, cwd, env, timeout=None, output_limit=8 * 1024 * 1024,
                input_bytes=None, raw_output=False):
    if output_limit < 1:
        raise ValueError("output limit must be positive")
    process = _launch(command, cwd, env, input_bytes, output_limit)
    buffers = [bytearray(), bytearray()]
    overflow = [False, False]

    def terminate_group():
        try:
            os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        except ChildProcessError:
            # An external reaper or SIGCHLD=SIG_IGN invalidates PID ownership.
            # Close our pipes, but never signal a potentially reused group ID.
            return
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()

    deadline = time.monotonic() + timeout if timeout is not None else None
    stdout_pipe, stderr_pipe = process.stdout, process.stderr
    assert stdout_pipe is not None and stderr_pipe is not None
    streams = (stdout_pipe, stderr_pipe)
    try:
        with selectors.DefaultSelector() as selector:
            for index, stream in enumerate(streams):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, index)
            _capture(process, selector, buffers, overflow, output_limit, deadline, timeout)
        process.wait()
    except BaseException as exc:
        terminate_group()
        if isinstance(exc, BoundedTimeoutExpired):
            exc.output = bytes(buffers[0])
            exc.stderr = bytes(buffers[1])
            exc.output_truncated = any(overflow)
        raise
    finally:
        for stream in streams:
            stream.close()
    stdout, stderr = [bytes(value) if raw_output else value.decode("utf-8", errors="replace")
                      for value in buffers]
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr), any(overflow)


def _capture(process, selector, buffers, overflow, output_limit, deadline, timeout):
    """Keep the parent unreaped until cleanup so its owned process-group ID stays reserved."""
    parent_done = False
    drain_deadline = None
    while selector.get_map() or not parent_done:
        if not parent_done:
            status = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            parent_done = status is not None
            if parent_done:
                drain_deadline = time.monotonic() + 1
        now = time.monotonic()
        limit = deadline if deadline is not None else drain_deadline
        if limit is not None and now >= limit:
            raise BoundedTimeoutExpired(process.args, timeout if timeout is not None else 1)
        interval = min(.05, max(0, limit - now)) if limit is not None else .05
        for key, _ in selector.select(interval):
            stream, index = key.fileobj, key.data
            try:
                chunk = os.read(stream.fileno(), 65536)
            except BlockingIOError:
                continue
            if not chunk:
                selector.unregister(stream)
                stream.close()
                continue
            buffers[index].extend(chunk)
            if len(buffers[index]) > output_limit:
                del buffers[index][:-output_limit]
                overflow[index] = True
