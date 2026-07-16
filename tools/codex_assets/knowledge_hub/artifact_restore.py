"""Isolated artifact restore drill with a read-only release source."""

from __future__ import annotations

import hashlib
import pathlib
import re
import shutil
import tempfile
from typing import Any, Dict, List, Mapping

from .common import (
    KnowledgeHubError,
    file_sha256,
    normalize_relpath,
    read_bytes_bounded,
)


ARTIFACT_RESTORE_SCHEMA = "knowledge-hub.artifact-restore-drill.v1"
CHECKSUM_LINE = re.compile(r"^([0-9a-f]{64}) ([ *])(.+)$")
MAX_MANIFEST_BYTES = 1024 * 1024
MAX_FILES = 1000
MAX_TOTAL_BYTES = 10 * 1024 * 1024 * 1024
MAX_SOURCE_LABEL_CHARS = 256
MAX_RELATIVE_PATH_CHARS = 4096


def _records(release_root: pathlib.Path) -> tuple[List[Dict[str, Any]], str]:
    manifest = release_root / "SHA256SUMS.txt"
    if manifest.is_symlink() or not manifest.is_file():
        raise KnowledgeHubError("release checksum manifest must be a regular file")
    raw_manifest = read_bytes_bounded(
        manifest,
        MAX_MANIFEST_BYTES,
        "release checksum manifest",
    )
    try:
        manifest_text = raw_manifest.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise KnowledgeHubError("release checksum manifest must be valid UTF-8") from exc
    manifest_sha256 = hashlib.sha256(raw_manifest).hexdigest()
    rows: List[Dict[str, Any]] = []
    seen = set()
    total_bytes = 0
    for line_no, line in enumerate(manifest_text.splitlines(), 1):
        if not line.strip():
            continue
        match = CHECKSUM_LINE.fullmatch(line)
        if not match:
            raise KnowledgeHubError(
                "invalid SHA256SUMS line {}".format(line_no)
            )
        raw_relative = match.group(3)
        if (
            len(raw_relative) > MAX_RELATIVE_PATH_CHARS
            or any(ord(character) < 32 for character in raw_relative)
        ):
            raise KnowledgeHubError(
                "invalid checksum path on line {}".format(line_no)
            )
        relative = normalize_relpath(raw_relative)
        if relative in seen:
            raise KnowledgeHubError("duplicate checksum path: {}".format(relative))
        raw_path = release_root / relative
        cursor = release_root
        path_has_symlink = False
        for part in pathlib.PurePosixPath(relative).parts:
            cursor = cursor / part
            path_has_symlink = path_has_symlink or cursor.is_symlink()
        if path_has_symlink:
            raise KnowledgeHubError("release checksum path must not be a symlink")
        path = raw_path.resolve(strict=False)
        try:
            path.relative_to(release_root)
        except ValueError as exc:
            raise KnowledgeHubError("release checksum path escapes source root") from exc
        if not path.is_file():
            raise KnowledgeHubError("release checksum path is missing: {}".format(relative))
        total_bytes += path.stat().st_size
        if total_bytes > MAX_TOTAL_BYTES:
            raise KnowledgeHubError(
                "release artifact set exceeds {} bytes".format(MAX_TOTAL_BYTES)
            )
        if len(rows) >= MAX_FILES:
            raise KnowledgeHubError(
                "release artifact set exceeds {} files".format(MAX_FILES)
            )
        seen.add(relative)
        rows.append(
            {
                "relative": relative,
                "expected_sha256": match.group(1),
                "source": path,
                "size": path.stat().st_size,
            }
        )
    if not rows:
        raise KnowledgeHubError("release checksum manifest is empty")
    return rows, manifest_sha256


def _verify(base: pathlib.Path, rows: List[Mapping[str, Any]]) -> List[str]:
    mismatches = []
    for row in rows:
        path = base / str(row["relative"])
        if path.is_symlink() or not path.is_file():
            mismatches.append(str(row["relative"]))
            continue
        if file_sha256(path) != row["expected_sha256"]:
            mismatches.append(str(row["relative"]))
    return mismatches


def _base_payload(
    source_label: str,
    manifest_sha256: str,
    rows: List[Mapping[str, Any]],
) -> Dict[str, Any]:
    snapshot = hashlib.sha256()
    for row in sorted(rows, key=lambda value: str(value["relative"])):
        snapshot.update(str(row["relative"]).encode("utf-8"))
        snapshot.update(b"\0")
        snapshot.update(str(row["expected_sha256"]).encode("ascii"))
        snapshot.update(b"\n")
    return {
        "schema_version": ARTIFACT_RESTORE_SCHEMA,
        "read_only_source": True,
        "status": "fail",
        "source_label": source_label,
        "checksum_manifest_sha256": manifest_sha256,
        "artifact_set_sha256": snapshot.hexdigest(),
        "file_count": len(rows),
        "total_bytes": sum(int(row["size"]) for row in rows),
        "source_mismatch_count": 0,
        "deployment_mismatch_count": 0,
        "restore_mismatch_count": 0,
        "mutated_path_sha256": "",
        "phases": {
            "source_integrity": False,
            "deployment_copy_integrity": False,
            "negative_corruption_detection": False,
            "restore_integrity": False,
            "source_unchanged": False,
        },
        "temporary_cleanup": True,
        "content_echoed": False,
        "authority_contract": {
            "source_written": False,
            "remote_retention_verified": False,
            "device_rollback_verified": False,
            "production_rollback_verified": False,
        },
    }


def run_artifact_restore_drill(
    release_root: pathlib.Path,
    source_label: str,
) -> Dict[str, Any]:
    if not isinstance(source_label, str) or not source_label.strip():
        raise KnowledgeHubError("source_label must be non-empty")
    if len(source_label) > MAX_SOURCE_LABEL_CHARS:
        raise KnowledgeHubError(
            "source_label exceeds {} characters".format(MAX_SOURCE_LABEL_CHARS)
        )
    if any(ord(character) < 32 for character in source_label):
        raise KnowledgeHubError("source_label must not contain control characters")
    raw_root = pathlib.Path(release_root).expanduser()
    if raw_root.is_symlink():
        raise KnowledgeHubError("release_root must not be a symlink")
    root = raw_root.resolve(strict=False)
    if not root.is_dir():
        raise KnowledgeHubError("release_root must be a regular directory")
    rows, parsed_manifest_sha256 = _records(root)
    manifest = root / "SHA256SUMS.txt"
    payload = _base_payload(source_label, parsed_manifest_sha256, rows)
    source_before = {
        str(row["relative"]): file_sha256(pathlib.Path(row["source"]))
        for row in rows
    }
    source_mismatches = [
        str(row["relative"])
        for row in rows
        if source_before[str(row["relative"])] != row["expected_sha256"]
    ]
    manifest_before = file_sha256(manifest)
    if manifest_before != parsed_manifest_sha256:
        source_mismatches.append("SHA256SUMS.txt")
    payload["source_mismatch_count"] = len(source_mismatches)
    payload["phases"]["source_integrity"] = not source_mismatches
    if source_mismatches:
        return payload
    with tempfile.TemporaryDirectory(prefix="knowledge-artifact-restore-") as temporary:
        deployment = pathlib.Path(temporary) / "deployment"
        for row in rows:
            target = deployment / str(row["relative"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pathlib.Path(row["source"]), target)
        deployment_mismatches = _verify(deployment, rows)
        payload["deployment_mismatch_count"] = len(deployment_mismatches)
        payload["phases"]["deployment_copy_integrity"] = not deployment_mismatches
        mutation = min(rows, key=lambda row: (int(row["size"]), str(row["relative"])))
        mutation_target = deployment / str(mutation["relative"])
        with mutation_target.open("ab") as handle:
            handle.write(b"\nknowledge-hub-rollback-negative-fixture\n")
        payload["mutated_path_sha256"] = hashlib.sha256(
            str(mutation["relative"]).encode("utf-8")
        ).hexdigest()
        payload["phases"]["negative_corruption_detection"] = (
            file_sha256(mutation_target) != mutation["expected_sha256"]
        )
        shutil.copy2(pathlib.Path(mutation["source"]), mutation_target)
        restore_mismatches = _verify(deployment, rows)
        payload["restore_mismatch_count"] = len(restore_mismatches)
        payload["phases"]["restore_integrity"] = not restore_mismatches
    source_after = {
        str(row["relative"]): file_sha256(pathlib.Path(row["source"]))
        for row in rows
    }
    payload["phases"]["source_unchanged"] = (
        source_before == source_after and manifest_before == file_sha256(manifest)
    )
    payload["status"] = (
        "pass" if all(payload["phases"].values()) else "fail"
    )
    return payload
