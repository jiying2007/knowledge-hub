"""P8 bounded connector SPI with checkpoints, tombstones, ACL propagation, and quarantine."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import time
from typing import Any, Dict, Iterable, List, Mapping, Protocol, Sequence

from .common import KnowledgeHubError, ensure_private_directory, utc_timestamp
from .observability_runtime import (
    append_optional_span,
    new_span_id,
    new_trace_id,
    span_record,
)
from .runtime_p5_security import principal_context

MAX_OBJECTS_PER_BATCH = 1000
MAX_BODY_CHARS = 256 * 1024
CHECKPOINT_ROOT = pathlib.Path(".cache/knowledge-hub/connectors")


class ConnectorAdapter(Protocol):
    connector_id: str

    def checkpoint(self) -> str:
        ...

    def list_changed(self, checkpoint: str, limit: int) -> Any:
        ...


def _checkpoint_path(root: pathlib.Path, connector_id: str) -> pathlib.Path:
    if not connector_id or any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789-_"
        for character in connector_id
    ):
        raise KnowledgeHubError("invalid connector id")
    path = root / CHECKPOINT_ROOT / connector_id / "checkpoint.json"
    ensure_private_directory(path.parent)
    if path.exists() and path.is_symlink():
        raise KnowledgeHubError("connector checkpoint must not be a symlink")
    return path


def load_checkpoint(root: pathlib.Path, connector_id: str) -> Dict[str, Any]:
    path = _checkpoint_path(root, connector_id)
    if not path.exists():
        return {"cursor": "", "updated_at": "", "sequence": 0}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("invalid connector checkpoint") from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("connector checkpoint must be an object")
    return dict(value)


def save_checkpoint(
    root: pathlib.Path,
    connector_id: str,
    *,
    cursor: str,
    previous_sequence: int,
) -> Dict[str, Any]:
    if len(cursor) > 2048:
        raise KnowledgeHubError("connector checkpoint cursor exceeds budget")
    path = _checkpoint_path(root, connector_id)
    payload = {
        "connector_id": connector_id,
        "cursor": cursor,
        "updated_at": utc_timestamp(),
        "sequence": int(previous_sequence) + 1,
    }
    temporary = path.with_name(path.name + ".tmp-{}".format(os.getpid()))
    if temporary.exists() and temporary.is_symlink():
        raise KnowledgeHubError("connector temporary checkpoint must not be a symlink")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(str(temporary), flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(path))
        os.chmod(path, 0o600)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary.exists():
            temporary.unlink()
    return payload


def _normalize_acl(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KnowledgeHubError("connector ACL must be a sequence")
    if len(value) > 64:
        raise KnowledgeHubError("connector ACL exceeds budget")
    rows = [str(row).strip() for row in value]
    if any(not row or len(row) > 256 for row in rows):
        raise KnowledgeHubError("connector ACL contains invalid subject")
    return rows


def normalize_object(connector_id: str, row: Mapping[str, Any]) -> Dict[str, Any]:
    object_id = str(row.get("object_id", "")).strip()
    version = str(row.get("version", "")).strip()
    if not object_id or len(object_id) > 1024:
        raise KnowledgeHubError("connector object_id must be non-empty and bounded")
    body = str(row.get("body", ""))
    if len(body) > MAX_BODY_CHARS:
        raise KnowledgeHubError("connector body exceeds budget")
    tombstone = bool(row.get("tombstone", False))
    content_sha = (
        hashlib.sha256(body.encode("utf-8")).hexdigest() if not tombstone else ""
    )
    return {
        "schema_version": "knowledge-hub.connector-object.v1",
        "connector_id": connector_id,
        "object_id": object_id,
        "version": version,
        "source_uri": str(row.get("source_uri", ""))[:4096],
        "content_type": str(row.get("content_type", "text/unknown"))[:256],
        "visibility": str(row.get("visibility", "team-internal"))[:128],
        "acl": _normalize_acl(row.get("acl", [])),
        "tombstone": tombstone,
        "content_sha256": content_sha,
        "body": "" if tombstone else body,
        "disposition": str(row.get("disposition", "reference-only"))[:128],
        "observed_at": str(row.get("observed_at", ""))[:128],
        "trust_class": "untrusted-external",
        "instruction_authority": False,
    }


def _quarantine_record(row: Mapping[str, Any], reason: str) -> Dict[str, Any]:
    object_id = str(row.get("object_id", ""))
    return {
        "object_id_sha256": hashlib.sha256(object_id.encode("utf-8")).hexdigest(),
        "reason": reason[:512],
        "body_stored": False,
    }


def _changed_rows(value: Any) -> Sequence[Mapping[str, Any]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KnowledgeHubError("connector list_changed must return a sequence")
    result = []
    for row in value:
        if not isinstance(row, Mapping):
            raise KnowledgeHubError("connector changed rows must be objects")
        result.append(row)
    return result


def _sha256_text(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def _sync_observation(
    root: pathlib.Path,
    adapter: ConnectorAdapter,
    principal_id: str,
    checkpoint_before: Mapping[str, Any],
    checkpoint_after: Mapping[str, Any],
    result: Mapping[str, Any],
    latency_ms: float,
) -> Dict[str, Any]:
    origin = str(getattr(adapter, "observation_origin", "unspecified"))[:128]
    span = span_record(
        name="knowledge.connector.sync",
        trace_id=new_trace_id(),
        span_id=new_span_id(),
        status="ok" if result.get("status") == "pass" else "degraded",
        latency_ms=latency_ms,
        attributes={
            "connector_id": adapter.connector_id,
            "observation_origin": origin,
            "principal_id_sha256": _sha256_text(principal_id),
            "checkpoint_before_sha256": _sha256_text(
                checkpoint_before.get("cursor", "")
            ),
            "checkpoint_after_sha256": _sha256_text(
                checkpoint_after.get("cursor", "")
            ),
            "checkpoint_advanced": bool(result.get("checkpoint_advanced", False)),
            "accepted_count": len(result.get("accepted", [])),
            "tombstone_count": len(result.get("tombstones", [])),
            "quarantine_count": len(result.get("quarantine", [])),
            "canonical_write_performed": False,
        },
    )
    observation = append_optional_span(root, span)
    observation["observation_origin"] = origin
    observation["checkpoint_before_sha256"] = span["attributes"][
        "checkpoint_before_sha256"
    ]
    observation["checkpoint_after_sha256"] = span["attributes"][
        "checkpoint_after_sha256"
    ]
    return observation


def sync_connector(
    root: pathlib.Path,
    adapter: ConnectorAdapter,
    principal: Mapping[str, Any],
    *,
    limit: int = 200,
) -> Dict[str, Any]:
    started = time.monotonic()
    principal_value = principal_context(principal)
    if not 1 <= limit <= MAX_OBJECTS_PER_BATCH:
        raise KnowledgeHubError("connector sync limit is outside policy")
    checkpoint = load_checkpoint(root, adapter.connector_id)
    cursor = str(checkpoint.get("cursor", ""))
    changed = _changed_rows(adapter.list_changed(cursor, limit))
    accepted: List[Dict[str, Any]] = []
    quarantined: List[Dict[str, Any]] = []
    tombstones: List[Dict[str, Any]] = []
    for row in changed:
        try:
            normalized = normalize_object(adapter.connector_id, row)
        except KnowledgeHubError as exc:
            quarantined.append(_quarantine_record(row, str(exc)))
            continue
        if normalized["tombstone"]:
            tombstones.append(normalized)
        else:
            accepted.append(normalized)
    saved = dict(checkpoint)
    if not quarantined:
        saved = save_checkpoint(
            root,
            adapter.connector_id,
            cursor=str(adapter.checkpoint()),
            previous_sequence=int(checkpoint.get("sequence", 0) or 0),
        )
    result: Dict[str, Any] = {
        "schema_version": "knowledge-hub.connector-sync.v1",
        "status": "pass" if not quarantined else "needs-review",
        "connector_id": adapter.connector_id,
        "principal_id": principal_value["principal_id"],
        "accepted": accepted,
        "tombstones": tombstones,
        "quarantine": quarantined,
        "checkpoint": saved,
        "checkpoint_advanced": not quarantined,
        "canonical_write_performed": False,
        "hub_core_network_client": False,
        "transport_owned_by_adapter_or_caller": True,
        "promotion_status": "proposal-or-reference-only",
    }
    result["observation"] = _sync_observation(
        root,
        adapter,
        principal_value["principal_id"],
        checkpoint,
        saved,
        result,
        (time.monotonic() - started) * 1000,
    )
    return result


class StaticConnectorAdapter:
    observation_origin = "static-fixture"

    def __init__(
        self,
        connector_id: str,
        rows: Iterable[Mapping[str, Any]],
        next_cursor: str = "static-complete",
    ) -> None:
        self.connector_id = connector_id
        self._rows = [dict(row) for row in rows]
        self._next_cursor = next_cursor

    def checkpoint(self) -> str:
        return self._next_cursor

    def list_changed(
        self, checkpoint: str, limit: int
    ) -> Sequence[Mapping[str, Any]]:
        if checkpoint == self._next_cursor:
            return []
        return self._rows[:limit]
