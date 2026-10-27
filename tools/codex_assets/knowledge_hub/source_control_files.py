"""Create missing source controls atomically; never overwrite retained evidence."""
from __future__ import annotations

import os
import pathlib
import re
import secrets
import stat
from contextlib import contextmanager

_NAMES = frozenset({"README.md", "coverage.md", "source-policy.md", "inventory.jsonl"})
_SOURCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}\Z")
MAX_CONTROL_BYTES = 128 * 1024


def valid_source_id(value):
    return isinstance(value, str) and _SOURCE_ID.fullmatch(value) is not None


@contextmanager
def _source_directory(root, source_id, apply):
    if not valid_source_id(source_id):
        raise ValueError("invalid-source-control-id")
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("safe-source-control-open-unavailable")
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in ("sources", source_id):
            if apply:
                try:
                    os.mkdir(part, dir_fd=descriptor)
                except FileExistsError:
                    pass
            try:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=descriptor)
            except FileNotFoundError:
                yield None
                return
            os.close(descriptor)
            descriptor = child
        yield descriptor
    finally:
        os.close(descriptor)


def _publish_complete_file(directory: int, name: str, content: bytes) -> bool:
    """Link a fully fsynced temporary inode only if the canonical name is absent.

    Partial writes never create the final filename. A concurrent winner is
    preserved without reading its content; the caller verifies it is regular.
    """
    staging = ".source-control-" + secrets.token_hex(16) + ".tmp"
    fd = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o644, dir_fd=directory)
    try:
        try:
            offset = 0
            view = memoryview(content)
            while offset < len(view):
                n = os.write(fd, view[offset:])
                if n <= 0:
                    raise OSError("source-control-short-write")
                offset += n
            os.fsync(fd)
        finally:
            os.close(fd)
        try:
            os.link(staging, name, src_dir_fd=directory, dst_dir_fd=directory,
                    follow_symlinks=False)
        except FileExistsError:
            return False
        os.fsync(directory)
        return True
    finally:
        os.unlink(staging, dir_fd=directory)
        os.fsync(directory)


def _existing_regular_file(directory: int, name: str) -> bool:
    """Probe the canonical name before any staging I/O; never follow symlinks."""
    try:
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=directory)
    except FileNotFoundError:
        return False
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("source-control-not-regular")
    finally:
        os.close(descriptor)
    return True


def materialize_source_file(root: pathlib.Path, source_id: str, name: str,
                            content: str, *, apply: bool = False) -> str:
    """Return created/missing/preserved; never read or replace existing content."""
    if name not in _NAMES or type(apply) is not bool or not isinstance(content, str):
        raise ValueError("invalid-source-control-operation")
    payload = content.encode("utf-8")
    if len(payload) > MAX_CONTROL_BYTES:
        raise ValueError("source-control-content-budget")
    try:
        with _source_directory(root, source_id, apply) as directory:
            if directory is None:
                return "missing"
            if _existing_regular_file(directory, name):
                return "preserved"
            if not apply:
                return "missing"
            if _publish_complete_file(directory, name, payload):
                return "created"
            # Another writer won the no-overwrite link race. Verify its target
            # without reading or modifying its content.
            if _existing_regular_file(directory, name):
                return "preserved"
            raise ValueError("source-control-path-changed")
    except OSError:
        raise ValueError("unsafe-source-control-path") from None
