"""Lightweight retrieval telemetry contract and append primitives.

Query producers depend on this module, while aggregate metrics depend on both
this module and the heavier governance evaluators. Keeping that direction
prevents an interactive search from importing the whole operations plane.
"""

from __future__ import annotations

import errno
import fcntl
import hashlib
import os
import pathlib
import secrets
from typing import Any, Dict, Mapping

from .common import compact_json, ensure_private_directory


INTERACTIVE_TELEMETRY_SCHEMA_VERSION = 3
INTERACTION_CONTRACT = "knowledge-retrieval-interaction-v1"
PERFORMANCE_CONTRACT = "knowledge-retrieval-performance-v2"
IMPLEMENTATION_GENERATION = "knowledge-retrieval-implementation-20260731-v1"


def make_interaction_id(
    kind: str,
    query_sha256: str,
    recorded_at: str,
    nonce: str = "",
) -> str:
    payload = "{}\0{}\0{}\0{}\0{}".format(
        INTERACTION_CONTRACT,
        kind,
        query_sha256,
        recorded_at,
        nonce or secrets.token_hex(16),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def telemetry_receipt_sha256(row: Mapping[str, Any]) -> str:
    """Return the digest of the exact privacy-safe telemetry row persisted."""
    return hashlib.sha256(compact_json(row).encode("utf-8")).hexdigest()


def append_telemetry_row(path: pathlib.Path, row: Mapping[str, Any]) -> None:
    """Append one private JSONL telemetry row under an exclusive file lock."""
    ensure_private_directory(path.parent)
    flags = (
        os.O_APPEND
        | os.O_CREAT
        | os.O_WRONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(str(path), flags, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.write(compact_json(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _telemetry_result(
    *,
    status: str,
    recorded: bool,
    reason: str,
    error_code: str,
    receipt_sha256: str = "",
) -> Dict[str, Any]:
    return {
        "status": status,
        "recorded": recorded,
        "non_blocking": True,
        "reason": reason,
        "error_code": error_code,
        "receipt_sha256": receipt_sha256,
        "raw_query_stored": False,
    }


def append_optional_telemetry(
    path: pathlib.Path,
    row: Mapping[str, Any],
    enabled: bool = True,
) -> Dict[str, Any]:
    """Append local telemetry without making observation a command dependency."""
    if not enabled:
        return _telemetry_result(
            status="disabled", recorded=False, reason="cli-disabled", error_code=""
        )
    if os.environ.get("KNOWLEDGE_TELEMETRY", "1").lower() in {
        "0",
        "false",
        "off",
        "no",
    }:
        return _telemetry_result(
            status="disabled",
            recorded=False,
            reason="environment-disabled",
            error_code="",
        )
    receipt = telemetry_receipt_sha256(row)
    try:
        append_telemetry_row(path, row)
    except OSError as exc:
        error_code = errno.errorcode.get(exc.errno or 0, "OSERROR")
        permission_errors = {errno.EACCES, errno.EPERM, errno.EROFS}
        return _telemetry_result(
            status="degraded",
            recorded=False,
            reason=(
                "read-only-or-permission-denied"
                if exc.errno in permission_errors
                else "local-storage-unavailable"
            ),
            error_code=error_code,
        )
    return _telemetry_result(
        status="recorded",
        recorded=True,
        reason="",
        error_code="",
        receipt_sha256=receipt,
    )
