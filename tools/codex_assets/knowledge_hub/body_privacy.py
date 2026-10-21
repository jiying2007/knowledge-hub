"""Bounded frontmatter checks before body hashing; never a publication grant.

The caller must already select an authorized Hub corpus. Legacy text without
privacy fields retains that selection, but explicit private metadata overrides
it. Ambiguous privacy syntax fails closed. No body or identity is exported.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import stat
from contextlib import contextmanager
from typing import BinaryIO, Iterator, Tuple

import yaml
from yaml.events import AliasEvent, CollectionEndEvent, CollectionStartEvent
from yaml.nodes import MappingNode, ScalarNode

MAX_HEADER_BYTES = 65536
MAX_LINE_BYTES = 4096
PRIVATE_VALUES = frozenset({"private", "personal-local", "personal"})
PUBLIC_VALUES = frozenset({"team-internal", "public"})
STATUS_VALUES = frozenset({
    "draft", "reviewing", "active", "archived", "superseded", "rejected", "deprecated", "personal",
})


class BodyPrivacyError(ValueError):
    """An identifying filename or body must never be included in this error."""


def _relative_path(relative: str) -> pathlib.PurePosixPath:
    if not isinstance(relative, str) or not relative:
        raise BodyPrivacyError("invalid-body-path")
    path = pathlib.PurePosixPath(relative)
    if (path.is_absolute() or relative != path.as_posix() or relative == "."
            or ".." in path.parts or "\\" in relative
            or any(ord(char) < 32 for char in relative)):
        raise BodyPrivacyError("invalid-body-path")
    if path.parts[:2] == ("notes", "personal"):
        raise BodyPrivacyError("reserved-private-body")
    return path


@contextmanager
def _open_body(root: pathlib.Path, relative: str) -> Iterator[BinaryIO]:
    path = _relative_path(relative)
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise BodyPrivacyError("unsupported-safe-file-open")
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    leaf = -1
    try:
        for part in path.parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        leaf = os.open(path.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                       dir_fd=directory)
        if not stat.S_ISREG(os.fstat(leaf).st_mode):
            raise BodyPrivacyError("not-a-regular-body")
        with os.fdopen(leaf, "rb", buffering=0) as handle:
            leaf = -1
            yield handle
    finally:
        if leaf >= 0:
            os.close(leaf)
        os.close(directory)


def _classify_header(data: bytes) -> bool:
    text = data.decode("utf-8")
    if "\ufeff" in text:
        raise BodyPrivacyError("ambiguous-header-byte-order-mark")
    depth = 0
    for count, event in enumerate(yaml.parse(text, Loader=yaml.SafeLoader), 1):
        if count > 10000 or isinstance(event, AliasEvent):
            raise BodyPrivacyError("header-event-or-alias-budget")
        if isinstance(event, CollectionStartEvent):
            depth += 1
            if depth > 32:
                raise BodyPrivacyError("header-depth-budget")
        elif isinstance(event, CollectionEndEvent):
            depth -= 1
    node = yaml.compose(text, Loader=yaml.SafeLoader)
    if node is None:
        return False
    if not isinstance(node, MappingNode):
        raise BodyPrivacyError("header-must-be-a-mapping")
    seen = set()
    for key, value in node.value:
        if not isinstance(key, ScalarNode) or key.tag != "tag:yaml.org,2002:str":
            raise BodyPrivacyError("unsupported-header-key")
        name = key.value.lower()
        if name in seen:
            raise BodyPrivacyError("duplicate-header-key")
        seen.add(name)
        if name not in {"visibility", "status"}:
            continue
        if not isinstance(value, ScalarNode) or value.tag != "tag:yaml.org,2002:str":
            raise BodyPrivacyError("ambiguous-privacy-value")
        classification = value.value.strip().lower()
        if (name == "visibility" and classification in PRIVATE_VALUES
                or name == "status" and classification == "personal"):
            return True
        allowed = PUBLIC_VALUES if name == "visibility" else STATUS_VALUES
        if classification not in allowed:
            raise BodyPrivacyError("unknown-privacy-classification")
    return False


def _header(handle: BinaryIO) -> Tuple[bool, bytes]:
    first = handle.readline(MAX_LINE_BYTES + 1)
    if len(first) > MAX_LINE_BYTES:
        raise BodyPrivacyError("first-line-budget")
    marker = first[3:] if first.startswith(b"\xef\xbb\xbf") else first
    if marker.rstrip(b"\r\n") != b"---":
        if marker.strip().startswith(b"---"):
            raise BodyPrivacyError("ambiguous-header-delimiter")
        return False, first
    chunks = []
    length = len(first)
    while True:
        raw = handle.readline(min(MAX_LINE_BYTES + 1, MAX_HEADER_BYTES - length + 1))
        length += len(raw)
        if not raw or len(raw) > MAX_LINE_BYTES or length > MAX_HEADER_BYTES:
            raise BodyPrivacyError("header-incomplete-or-over-budget")
        if raw.rstrip(b"\r\n").rstrip(b" \t") == b"---":
            private = _classify_header(b"".join(chunks))
            return (True, b"") if private else (False, first + b"".join(chunks) + raw)
        chunks.append(raw)


def declared_private(root: pathlib.Path, relative: str) -> bool:
    """Read bounded header lines only; a declaration excludes before hashing."""
    try:
        with _open_body(root, relative) as handle:
            return _header(handle)[0]
    except (OSError, UnicodeError, ValueError, yaml.YAMLError, RecursionError):
        raise BodyPrivacyError("unavailable-or-ambiguous-body-metadata") from None


def _identity(value: os.stat_result) -> Tuple[int, int, int, int, int]:
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def digest_public_body(root: pathlib.Path, relative: str, budget: int) -> Tuple[str, int]:
    """Reclassify and hash on the same descriptor, rejecting classification races."""
    if type(budget) is not int or budget < 0:
        raise BodyPrivacyError("invalid-body-budget")
    try:
        with _open_body(root, relative) as handle:
            before = os.fstat(handle.fileno())
            if before.st_size > budget:
                raise BodyPrivacyError("body-byte-budget")
            private, prefix = _header(handle)
            if private:
                raise BodyPrivacyError("private-body-must-not-be-hashed")
            if len(prefix) > budget:
                raise BodyPrivacyError("body-byte-budget")
            digest = hashlib.sha256()
            digest.update(prefix)
            size = len(prefix)
            while True:
                chunk = handle.read(min(65536, budget - size + 1))
                if not chunk:
                    break
                size += len(chunk)
                if size > budget:
                    raise BodyPrivacyError("body-byte-budget")
                digest.update(chunk)
            after = os.fstat(handle.fileno())
            if _identity(before) != _identity(after) or size != before.st_size:
                raise BodyPrivacyError("body-changed-during-read")
        return digest.hexdigest(), size
    except (OSError, UnicodeError, ValueError, yaml.YAMLError, RecursionError):
        raise BodyPrivacyError("unsafe-or-changing-public-body") from None
