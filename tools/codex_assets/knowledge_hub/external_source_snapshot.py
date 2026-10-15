"""Bounded source-side file hashes; evidence candidate only, never migration proof.

This intentionally does not read or mutate external knowledge content beyond the
bytes needed to hash it. The local private manifest is *not* a Hub source ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import stat
from typing import Any, Dict, List, Tuple


CONTRACT = "knowledge-hub.external-source-snapshot-candidate/v1"
SOURCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MAX_FILES = 20000
MAX_DIRECTORIES = 20000
MAX_SINGLE_FILE_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_REGISTRY_BYTES = 2 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024


class SourceSnapshotError(ValueError):
    """A source cannot be represented by a complete safe candidate."""


def _canonical(value: Dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _read_control(path: pathlib.Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise SourceSnapshotError("source registry unavailable or linked")
    if path.stat().st_size > MAX_REGISTRY_BYTES:
        raise SourceSnapshotError("source registry exceeds byte budget")
    data = path.read_bytes()
    if len(data) > MAX_REGISTRY_BYTES:
        raise SourceSnapshotError("source registry changed past byte budget")
    return data


def registered_source_ids(hub_root: pathlib.Path) -> set:
    """Current and retired source IDs are both legitimate historical scopes."""
    try:
        current = json.loads(_read_control(hub_root / "registry/sources.json"))
        if (not isinstance(current, dict) or
                not isinstance(current.get("sources"), list)):
            raise SourceSnapshotError("invalid current source registry")
        retired_raw = _read_control(hub_root / "registry/retired-sources.jsonl")
        retired = [json.loads(line) for line in retired_raw.splitlines() if line.strip()]
        identities = []
        for entry in list(current["sources"]) + retired:
            if not isinstance(entry, dict):
                raise SourceSnapshotError("invalid source registry entry")
            identity = entry.get("id")
            if not isinstance(identity, str) or not SOURCE_ID.fullmatch(identity):
                raise SourceSnapshotError("invalid source registry identity")
            identities.append(identity)
        if len(set(identities)) != len(identities):
            raise SourceSnapshotError("duplicate current/retired source identity")
        return set(identities)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SourceSnapshotError("unable to read source registry") from exc


def _identity(path: pathlib.Path) -> Tuple[int, int, int, int, int]:
    """Directory/file identity plus write-relevant metadata."""
    info = path.lstat()
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _hash_file(path: pathlib.Path, remaining: int) -> Tuple[str, int]:
    if not hasattr(os, "O_NOFOLLOW"):
        raise SourceSnapshotError("platform lacks no-follow file reads")
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_nlink < 1:
            raise SourceSnapshotError("source contains linked or nonregular file")
        if before.st_size > MAX_SINGLE_FILE_BYTES or before.st_size > remaining:
            raise SourceSnapshotError("source hashing byte budget exceeded")
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0))
        try:
            opened = os.fstat(fd)
            if (not stat.S_ISREG(opened.st_mode) or
                    (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)):
                raise SourceSnapshotError("source file changed before read")
            result = hashlib.sha256()
            size = 0
            while True:
                chunk = os.read(fd, CHUNK_BYTES)
                if not chunk:
                    break
                size += len(chunk)
                if size > remaining or size > MAX_SINGLE_FILE_BYTES:
                    raise SourceSnapshotError("source file grew past byte budget")
                result.update(chunk)
            after_fd = os.fstat(fd)
        finally:
            os.close(fd)
        after_path = path.lstat()
        def signature(info):
            return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        if (size != before.st_size or signature(before) != signature(opened)
                or signature(before) != signature(after_fd)
                or signature(before) != signature(after_path)):
            raise SourceSnapshotError("source file changed while hashing")
        return result.hexdigest(), size
    except OSError as exc:
        raise SourceSnapshotError("source file unreadable or changed") from exc


def _relative_ok(value: str) -> bool:
    if (not value or "\\" in value or "\x00" in value
            or any(c in value for c in "\r\n")):
        return False
    parts = pathlib.PurePosixPath(value)
    return (not parts.is_absolute() and parts.as_posix() == value
            and all(part not in ("", ".", "..") for part in parts.parts))


def _scan_files(path: pathlib.Path) -> List[Dict[str, Any]]:
    if path.is_symlink():
        raise SourceSnapshotError("source root must not be a symlink")
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise SourceSnapshotError("source root unavailable") from exc
    if stat.S_ISREG(mode):
        sha, size = _hash_file(path, MAX_TOTAL_BYTES)
        if not _relative_ok(path.name):
            raise SourceSnapshotError("unsafe source filename")
        return [{"relative_path": path.name, "size_bytes": size, "sha256": sha}]
    if not stat.S_ISDIR(mode):
        raise SourceSnapshotError("source root must be regular file or directory")

    directory_signatures = []
    file_paths = []

    def _walk_error(_exc: OSError) -> None:
        raise SourceSnapshotError("source directory unreadable during enumeration")

    for directory, dirs, files in os.walk(str(path), topdown=True,
                                          followlinks=False, onerror=_walk_error):
        current = pathlib.Path(directory)
        if len(directory_signatures) >= MAX_DIRECTORIES:
            raise SourceSnapshotError("source directory count exceeds budget")
        try:
            current_identity = _identity(current)
        except OSError as exc:
            raise SourceSnapshotError("source directory unreadable") from exc
        if not stat.S_ISDIR(current.lstat().st_mode):
            raise SourceSnapshotError("source directory changed during scan")
        directory_signatures.append((current, current_identity))
        for name in dirs + files:
            relative = (current / name).relative_to(path).as_posix()
            if not _relative_ok(relative):
                raise SourceSnapshotError("unsafe source filename")
            child = current / name
            try:
                child_stat = child.lstat()
            except OSError as exc:
                raise SourceSnapshotError("source child disappeared") from exc
            if stat.S_ISLNK(child_stat.st_mode):
                raise SourceSnapshotError("source contains symlink (no-follow)")
            if name in dirs and not stat.S_ISDIR(child_stat.st_mode):
                raise SourceSnapshotError("source directory entry changed type")
            if name in files and not stat.S_ISREG(child_stat.st_mode):
                raise SourceSnapshotError("source contains special or nonregular file")
        # Git metadata is the only excluded scope. Other files are either
        # hashed or make the candidate fail closed when outside budgets.
        dirs[:] = sorted(name for name in dirs if name != ".git")
        for name in sorted(files):
            if name == ".git":
                continue
            file_paths.append(current / name)
            if len(file_paths) > MAX_FILES:
                raise SourceSnapshotError("source file count exceeds budget")
    records = []
    remaining = MAX_TOTAL_BYTES
    for file_path in sorted(file_paths, key=lambda p: p.relative_to(path).as_posix()):
        digest, size = _hash_file(file_path, remaining)
        remaining -= size
        records.append({"relative_path": file_path.relative_to(path).as_posix(),
                        "size_bytes": size, "sha256": digest})
    for directory, previous in directory_signatures:
        try:
            if _identity(directory) != previous:
                raise SourceSnapshotError("source directory changed during scan")
        except OSError as exc:
            raise SourceSnapshotError("source directory disappeared") from exc
    return records


def capture_source_snapshot(hub_root: pathlib.Path, source_id: str,
                            source_path: pathlib.Path,
                            claimed_revision: str = "") -> Dict[str, Any]:
    """Scan only an explicitly selected source path; never infer completeness."""
    hub_root = hub_root.resolve(strict=True)
    if (not isinstance(source_id, str) or not SOURCE_ID.fullmatch(source_id)
            or source_id not in registered_source_ids(hub_root)):
        raise SourceSnapshotError("source ID is not registered")
    if claimed_revision and not HEX40.fullmatch(claimed_revision):
        raise SourceSnapshotError("claimed revision must be a 40-character lowercase SHA")
    if not isinstance(source_path, pathlib.Path):
        raise SourceSnapshotError("source path must be explicit")
    kind = "single-file" if source_path.is_file() and not source_path.is_symlink() else "directory"
    records = _scan_files(source_path)
    snapshot = {
        "schema_version": 1,
        "contract": CONTRACT,
        "source_id": source_id,
        "scope": "explicit-source-path; all regular files except .git metadata",
        "source_kind": kind,
        "claimed_revision": claimed_revision,
        "claimed_revision_verified": False,
        "origin_binding_verified": False,
        "atomic_snapshot_verified": False,
        "target_disposition_verified": False,
        "full_external_migration_proven": False,
        "read_only_source": True,
        "private_relative_filenames_present": True,
        "file_count": len(records),
        "total_bytes": sum(entry["size_bytes"] for entry in records),
        "files": records,
    }
    snapshot["capture_sha256"] = hashlib.sha256(_canonical(snapshot)).hexdigest()
    validate_source_snapshot(snapshot)
    return snapshot


def validate_source_snapshot(value: Dict[str, Any]) -> None:
    """Validate internal consistency; NOT external origin or semantic truth."""
    if not isinstance(value, dict):
        raise SourceSnapshotError("snapshot must be an object")
    expected = {"schema_version", "contract", "source_id", "scope", "source_kind",
                "claimed_revision", "claimed_revision_verified", "origin_binding_verified",
                "atomic_snapshot_verified", "target_disposition_verified",
                "full_external_migration_proven", "read_only_source",
                "private_relative_filenames_present", "file_count", "total_bytes",
                "files", "capture_sha256"}
    if set(value) != expected or type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise SourceSnapshotError("snapshot fields or schema version invalid")
    if (value["contract"] != CONTRACT or value["scope"] != "explicit-source-path; all regular files except .git metadata"
            or value["source_kind"] not in ("single-file", "directory")
            or not isinstance(value["source_id"], str) or not SOURCE_ID.fullmatch(value["source_id"])
            or not isinstance(value["claimed_revision"], str)
            or (value["claimed_revision"] and not HEX40.fullmatch(value["claimed_revision"]))):
        raise SourceSnapshotError("snapshot source identity contract invalid")
    if (any(value[field] is not False for field in (
            "claimed_revision_verified", "origin_binding_verified", "atomic_snapshot_verified",
            "target_disposition_verified", "full_external_migration_proven"))
            or value["read_only_source"] is not True
            or value["private_relative_filenames_present"] is not True):
        raise SourceSnapshotError("snapshot must not claim proof or mutation")
    rows = value["files"]
    if not isinstance(rows, list) or len(rows) > MAX_FILES or len(rows) != value["file_count"]:
        raise SourceSnapshotError("snapshot file count invalid")
    total = 0
    preceding = ""
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"relative_path", "sha256", "size_bytes"}:
            raise SourceSnapshotError("invalid snapshot file entry")
        name, digest, size = row["relative_path"], row["sha256"], row["size_bytes"]
        if not isinstance(name, str) or not _relative_ok(name) or name <= preceding:
            raise SourceSnapshotError("unsafe, unordered or duplicate source relative path")
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            raise SourceSnapshotError("invalid source file digest")
        if type(size) is not int or size < 0 or size > MAX_SINGLE_FILE_BYTES:
            raise SourceSnapshotError("invalid source file size")
        total += size
        preceding = name
    if (type(value["total_bytes"]) is not int or value["total_bytes"] != total
            or total > MAX_TOTAL_BYTES or (value["source_kind"] == "single-file" and len(rows) != 1)):
        raise SourceSnapshotError("source snapshot size or kind mismatch")
    capture = dict(value)
    digest = capture.pop("capture_sha256")
    if not isinstance(digest, str) or not HEX64.fullmatch(digest):
        raise SourceSnapshotError("snapshot capture digest invalid")
    if hashlib.sha256(_canonical(capture)).hexdigest() != digest:
        raise SourceSnapshotError("snapshot capture digest mismatch")
    if len(_canonical(value)) > MAX_MANIFEST_BYTES:
        raise SourceSnapshotError("snapshot exceeds manifest byte budget")


def persist_private_snapshot(hub_root: pathlib.Path, snapshot: Dict[str, Any]) -> str:
    """Content-addressed 0600 output only under the Hub-ignored .tmp tree."""
    validate_source_snapshot(snapshot)
    hub_root = hub_root.resolve(strict=True)
    output = hub_root
    for component in (".tmp", "source-snapshots", snapshot["source_id"]):
        output = output / component
        if output.is_symlink():
            raise SourceSnapshotError("private snapshot directory is symlinked")
        output.mkdir(mode=0o700, exist_ok=True)
        if not output.is_dir() or output.is_symlink():
            raise SourceSnapshotError("private snapshot path is not a safe directory")
        if component != ".tmp" and (stat.S_IMODE(output.stat().st_mode) & 0o077):
            raise SourceSnapshotError("private snapshot directory is not owner-only")
    name = snapshot["capture_sha256"] + ".json"
    target = output / name
    payload = _canonical(snapshot)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(target), flags, 0o600)
    except FileExistsError:
        if target.is_symlink() or not target.is_file():
            raise SourceSnapshotError("existing private snapshot differs or is linked")
        existing = target.stat()
        if (existing.st_nlink != 1 or stat.S_IMODE(existing.st_mode) & 0o077
                or target.read_bytes() != payload):
            raise SourceSnapshotError("existing private snapshot is unsafe or differs")
    else:
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
        except BaseException:
            target.unlink(missing_ok=True)
            raise
    return target.relative_to(hub_root).as_posix()
