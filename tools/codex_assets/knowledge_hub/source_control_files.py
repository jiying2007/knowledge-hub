"""Create missing source controls only; retained evidence is never overwritten."""
from __future__ import annotations

import os
import pathlib
import re
import stat
from contextlib import contextmanager


_NAMES = frozenset({"README.md", "coverage.md", "source-policy.md", "inventory.jsonl"})
_SOURCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}\Z")


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


def materialize_source_file(root: pathlib.Path, source_id: str, name: str,
                            content: str, *, apply: bool = False) -> str:
    """Return created/missing/preserved; never read or replace existing content."""
    if name not in _NAMES or type(apply) is not bool or not isinstance(content, str):
        raise ValueError("invalid-source-control-operation")
    try:
        with _source_directory(root, source_id, apply) as directory:
            if directory is None:
                return "missing"
            if apply:
                try:
                    descriptor = os.open(
                        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o644, dir_fd=directory,
                    )
                except FileExistsError:
                    pass
                else:
                    with os.fdopen(descriptor, "wb") as stream:
                        stream.write(content.encode("utf-8"))
                        stream.flush()
                        os.fsync(stream.fileno())
                    return "created"
            try:
                descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                     dir_fd=directory)
            except FileNotFoundError:
                if apply:
                    raise ValueError("source-control-path-changed") from None
                return "missing"
            try:
                if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                    raise ValueError("source-control-not-regular")
            finally:
                os.close(descriptor)
            return "preserved"
    except OSError:
        raise ValueError("unsafe-source-control-path") from None
