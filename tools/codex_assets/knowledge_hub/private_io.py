"""Private, durable local writes with serialized identity conflict checks."""

from __future__ import annotations

import fcntl
import hashlib
import os
import pathlib
import tempfile
from contextlib import contextmanager

from .common import KnowledgeHubError, ensure_private_directory, ensure_private_file


class PrivateWriteUncertain(KnowledgeHubError):
    """Replace may be visible but durable acknowledgement was not established."""


def _sync_directory(path):
    descriptor = os.open(str(path), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _prepare_private_parent(path):
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise KnowledgeHubError("private output ancestors must not be symlinks")
    missing = []
    current = path.parent
    while not current.exists():
        missing.append(current)
        current = current.parent
    if current.is_symlink():
        raise KnowledgeHubError("private output directory must not be a symlink")
    for directory in reversed(missing):
        ensure_private_directory(directory)
        parent_fd = os.open(str(directory.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    ensure_private_directory(path.parent)
    for parent in path.parents:
        if parent.is_symlink():
            raise KnowledgeHubError("private output ancestors must not be symlinks")


@contextmanager
def private_execution_lock(path):
    """Claim a plan execution without replacing the shared lock inode."""
    _prepare_private_parent(path)
    descriptor = os.open(str(path), os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "a+") as guard:
        ensure_private_file(path)
        try:
            fcntl.flock(guard.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise KnowledgeHubError('operation plan execution is already in progress') from exc
        yield


def atomic_private_write(path: pathlib.Path, content: str, *, immutable=False, expected_sha256=None):
    _prepare_private_parent(path)
    encoded = content.encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    lock = path.parent / ".write.lock"
    if lock.is_symlink() or path.is_symlink():
        raise KnowledgeHubError("private output must not be a symlink")
    lock_fd = os.open(str(lock), os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(lock_fd, "a+") as guard:
        ensure_private_file(lock)
        fcntl.flock(guard.fileno(), fcntl.LOCK_EX)
        if path.is_symlink():
            raise KnowledgeHubError("private output must not be a symlink")
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""
        if expected_sha256 is not None and actual != expected_sha256:
            raise KnowledgeHubError("private write expected hash conflict")
        if actual == digest:
            ensure_private_file(path)
            try:
                with path.open('rb') as handle:
                    os.fsync(handle.fileno())
                _sync_directory(path.parent)
                if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    raise KnowledgeHubError('private output readback mismatch')
            except (OSError, KnowledgeHubError) as exc:
                raise PrivateWriteUncertain('idempotent output durability is unknown') from exc
            return False
        if immutable and actual and expected_sha256 is None:
            raise KnowledgeHubError("identity conflict: same identity has different content")
        descriptor, temporary = tempfile.mkstemp(prefix=".{}-".format(path.name), dir=str(path.parent))
        replaced = False
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            replaced = True
            _sync_directory(path.parent)
            ensure_private_file(path)
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise KnowledgeHubError("private output readback mismatch")
        except (OSError, KnowledgeHubError) as exc:
            if replaced:
                raise PrivateWriteUncertain('output replaced; durability/readback needs reconciliation') from exc
            raise
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return True
