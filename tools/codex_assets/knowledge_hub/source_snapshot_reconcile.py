"""Read-only reconciliation between a private source candidate and Hub provenance.

The comparison is metadata-level: it neither verifies a source revision nor
proves complete migration, semantic correctness, or owner approval.
"""

from __future__ import annotations

import json
import os
import pathlib
import stat
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from .content_convergence import _jsonl
from .external_source_snapshot import (
    CHUNK_BYTES, HEX64, MAX_MANIFEST_BYTES, SOURCE_ID, SourceSnapshotError,
    _canonical, _read_control, _relative_ok, registered_source_ids,
    validate_source_snapshot,
)


def _bounded_private_candidate(root: pathlib.Path, reference: pathlib.Path) -> Dict[str, Any]:
    """Read only a Hub-private content-addressed manifest, never an arbitrary file."""
    if ".." in reference.parts:
        raise SourceSnapshotError("private snapshot reference contains traversal")
    target = reference if reference.is_absolute() else root / reference
    private = root / ".tmp" / "source-snapshots"
    try:
        parts = target.relative_to(private).parts
    except ValueError as exc:
        raise SourceSnapshotError("snapshot must be under Hub private snapshots") from exc
    if (len(parts) != 2 or not SOURCE_ID.fullmatch(parts[0])
            or not parts[1].endswith(".json") or not HEX64.fullmatch(parts[1][:-5])):
        raise SourceSnapshotError("private snapshot path identity invalid")
    for directory in (root / ".tmp", private, private / parts[0]):
        if not directory.is_dir() or directory.is_symlink():
            raise SourceSnapshotError("private snapshot directory unavailable or linked")
        if directory != root / ".tmp" and stat.S_IMODE(directory.stat().st_mode) & 0o077:
            raise SourceSnapshotError("private snapshot directory is not owner-only")
    if target.is_symlink():
        raise SourceSnapshotError("private snapshot file must not be linked")
    if not hasattr(os, "O_NOFOLLOW"):
        raise SourceSnapshotError("platform lacks no-follow private reads")
    try:
        fd = os.open(str(target), os.O_RDONLY | os.O_NOFOLLOW |
                     getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0))
        try:
            before = os.fstat(fd)
            if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                    or stat.S_IMODE(before.st_mode) & 0o077
                    or before.st_size > MAX_MANIFEST_BYTES):
                raise SourceSnapshotError("private snapshot file safety check failed")
            chunks = []
            size = 0
            while True:
                part = os.read(fd, CHUNK_BYTES)
                if not part:
                    break
                size += len(part)
                if size > MAX_MANIFEST_BYTES:
                    raise SourceSnapshotError("private snapshot byte budget exceeded")
                chunks.append(part)
            after = os.fstat(fd)
            if (size != before.st_size or
                    (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
                     before.st_ctime_ns) !=
                    (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
                     after.st_ctime_ns)):
                raise SourceSnapshotError("private snapshot changed during read")
        finally:
            os.close(fd)
    except OSError as exc:
        raise SourceSnapshotError("private snapshot inaccessible or changed") from exc
    raw = b"".join(chunks)
    try:
        candidate = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise SourceSnapshotError("private snapshot is not JSON") from exc
    validate_source_snapshot(candidate)
    if (candidate["source_id"] != parts[0] or
            candidate["capture_sha256"] + ".json" != parts[1] or
            raw != _canonical(candidate)):
        raise SourceSnapshotError("private snapshot identity/content mismatch")
    return candidate


def _origin_root(root: pathlib.Path, source_id: str) -> Tuple[str, str]:
    """Read existing canonical source-control metadata, without external access."""
    if source_id not in registered_source_ids(root):
        raise SourceSnapshotError("source is no longer registered")
    current = json.loads(_read_control(root / "registry/sources.json"))
    retired = [json.loads(line) for line in _read_control(
        root / "registry/retired-sources.jsonl").splitlines() if line.strip()]
    matches = [("current", row) for row in current["sources"] if row.get("id") == source_id]
    matches += [("retired", row) for row in retired if row.get("id") == source_id]
    if len(matches) != 1:
        raise SourceSnapshotError("source control identity is ambiguous")
    category, record = matches[0]
    origin = record.get("origin_path", "")
    if not isinstance(origin, str):
        raise SourceSnapshotError("registered origin path is invalid")
    return category, origin.rstrip("/")


def _relative_origin(kind: str, origin_root: str, origin: Any,
                     single_name: str) -> Optional[str]:
    if not isinstance(origin, str) or not origin_root:
        return None
    if kind == "single-file":
        return single_name if origin == origin_root else None
    prefix = origin_root + "/"
    if origin.startswith(prefix):
        candidate = origin[len(prefix):]
        return candidate if _relative_ok(candidate) else None
    return None


def _inventory_index(root: pathlib.Path, source_id: str, kind: str,
                     origin_root: str, single_name: str) -> Tuple[Dict[str, List[dict]], int]:
    inventory = _jsonl(root, root / "sources" / source_id / "inventory.jsonl")
    index: Dict[str, List[dict]] = defaultdict(list)
    for row in inventory:
        if row.get("source_id") != source_id:
            raise SourceSnapshotError("source inventory identity mismatch")
        relative = _relative_origin(kind, origin_root, row.get("origin_path"), single_name)
        if relative is not None:
            index[relative].append(row)
    return index, len(inventory)


def reconcile_private_snapshot(root: pathlib.Path,
                               reference: pathlib.Path) -> Dict[str, Any]:
    """Compare candidate file hashes to source inventory, with NO terminal verdict."""
    root = root.resolve(strict=True)
    snapshot = _bounded_private_candidate(root, reference)
    source_id = snapshot["source_id"]
    bucket, origin_root = _origin_root(root, source_id)
    single_name = snapshot["files"][0]["relative_path"] if snapshot["source_kind"] == "single-file" else ""
    scoped, inventory_count = _inventory_index(
        root, source_id, snapshot["source_kind"], origin_root, single_name)
    counts = {"exact_hash_size_candidates": 0, "no_file_row": 0,
              "file_row_without_digest": 0, "hash_or_size_mismatch": 0,
              "ambiguous_file_rows": 0}
    present = set()
    for file in snapshot["files"]:
        name = file["relative_path"]
        present.add(name)
        candidates = scoped.get(name, [])
        if not candidates:
            counts["no_file_row"] += 1
        elif len(candidates) > 1:
            counts["ambiguous_file_rows"] += 1
        else:
            row = candidates[0]
            size, sha = row.get("size_bytes"), row.get("sha256")
            if type(size) is not int or size < 0 or not isinstance(sha, str) or not HEX64.fullmatch(sha):
                counts["file_row_without_digest"] += 1
            elif size == file["size_bytes"] and sha == file["sha256"]:
                counts["exact_hash_size_candidates"] += 1
            else:
                counts["hash_or_size_mismatch"] += 1
    extra = sum(len(rows) for name, rows in scoped.items() if name not in present)
    ambiguous = counts["ambiguous_file_rows"] > 0
    conflicting = counts["hash_or_size_mismatch"] > 0 or ambiguous
    candidate_all = bool(snapshot["file_count"]) and not extra and (
        counts["exact_hash_size_candidates"] == snapshot["file_count"])
    return {
        "schema_version": 1,
        "contract": "knowledge-hub.source-snapshot-reconciliation-observation/v1",
        "status": "needs-fix" if conflicting else "needs-review",
        "read_only": True,
        "report_only": True,
        "source_id": source_id,
        "source_registry_bucket": bucket,
        "snapshot_sha256": snapshot["capture_sha256"],
        "snapshot_file_count": snapshot["file_count"],
        "source_inventory_row_count": inventory_count,
        "file_scoped_inventory_row_count": sum(len(v) for v in scoped.values()),
        "root_batch_or_out_of_scope_row_count": inventory_count - sum(len(v) for v in scoped.values()),
        "file_scoped_inventory_rows_not_in_snapshot": extra,
        **counts,
        "all_candidate_files_have_exact_inventory_hash": candidate_all,
        "actual_source_origin_verified": False,
        "source_revision_verified": False,
        "atomic_source_snapshot_verified": False,
        "snapshot_rechecked_against_live_source": False,
        "target_disposition_verified": False,
        "full_external_migration_proven": False,
        "full_content_review_proven": False,
        "owner_decisions_generated": False,
        "canonical_mutations": 0,
        "raw_paths_exposed": False,
        "notes_zh": (
            "文件匹配仅是本机候选与 Hub inventory 的字节级元数据比较。"
            "无可信源修订、原子源快照、逐项处置及 owner 审查，不得宣称外部迁移或产品终态。"
        ),
    }
