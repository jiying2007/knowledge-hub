"""P8 bounded connector SPI with checkpoints, tombstones, ACL propagation, and quarantine."""

from __future__ import annotations

import fcntl
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
MAX_BATCH_BODY_CHARS = 16 * 1024 * 1024
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


def _checkpoint_lock_path(root: pathlib.Path, connector_id: str) -> pathlib.Path:
    path = _checkpoint_path(root, connector_id).with_name("checkpoint.lock")
    if path.exists() and path.is_symlink():
        raise KnowledgeHubError("connector checkpoint lock must not be a symlink")
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
    lock_path = _checkpoint_lock_path(root, connector_id)
    with lock_path.open("a+") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            current = load_checkpoint(root, connector_id)
            current_sequence = int(current.get("sequence", 0) or 0)
            if current_sequence != int(previous_sequence):
                raise KnowledgeHubError("connector checkpoint sequence changed")
            payload = {
                "connector_id": connector_id,
                "cursor": cursor,
                "updated_at": utc_timestamp(),
                "sequence": current_sequence + 1,
            }
            temporary = path.with_name(path.name + ".tmp-{}".format(os.getpid()))
            if temporary.exists() and temporary.is_symlink():
                raise KnowledgeHubError("connector temporary checkpoint must not be a symlink")
            if temporary.exists():
                temporary.unlink()
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
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


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
    tombstone_value = row.get("tombstone", False)
    if type(tombstone_value) is not bool:
        raise KnowledgeHubError("connector tombstone must be boolean")
    tombstone = tombstone_value
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


def _checkpoint_proposal(
    connector_id: str,
    checkpoint: Mapping[str, Any],
    cursor: str,
    accepted: Sequence[Mapping[str, Any]],
    tombstones: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    material = {
        "connector_id": connector_id,
        "previous_sequence": int(checkpoint.get("sequence", 0) or 0),
        "previous_cursor_sha256": _sha256_text(checkpoint.get("cursor", "")),
        "cursor": cursor,
        "accepted": [
            [str(row.get("object_id", "")), str(row.get("version", "")), str(row.get("content_sha256", ""))]
            for row in accepted
        ],
        "tombstones": [
            [str(row.get("object_id", "")), str(row.get("version", ""))]
            for row in tombstones
        ],
    }
    digest = hashlib.sha256(
        json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "knowledge-hub.connector-checkpoint-proposal.v1",
        "connector_id": connector_id,
        "previous_sequence": material["previous_sequence"],
        "previous_cursor_sha256": material["previous_cursor_sha256"],
        "cursor": cursor,
        "batch_sha256": digest,
    }


def acknowledge_connector_sync(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
) -> Dict[str, Any]:
    if proposal.get("schema_version") != "knowledge-hub.connector-checkpoint-proposal.v1":
        raise KnowledgeHubError("invalid connector checkpoint proposal")
    connector_id = str(proposal.get("connector_id", ""))
    previous_sequence = proposal.get("previous_sequence")
    cursor = str(proposal.get("cursor", ""))
    batch_sha256 = str(proposal.get("batch_sha256", ""))
    previous_cursor_sha256 = str(proposal.get("previous_cursor_sha256", ""))
    if type(previous_sequence) is not int or previous_sequence < 0:
        raise KnowledgeHubError("invalid connector checkpoint proposal sequence")
    if len(batch_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in batch_sha256):
        raise KnowledgeHubError("invalid connector checkpoint proposal digest")
    current = load_checkpoint(root, connector_id)
    if _sha256_text(current.get("cursor", "")) != previous_cursor_sha256:
        raise KnowledgeHubError("connector checkpoint cursor changed")
    saved = save_checkpoint(
        root,
        connector_id,
        cursor=cursor,
        previous_sequence=previous_sequence,
    )
    return {
        "schema_version": "knowledge-hub.connector-checkpoint-ack.v1",
        "status": "pass",
        "connector_id": connector_id,
        "batch_sha256": batch_sha256,
        "checkpoint": saved,
        "checkpoint_advanced": True,
    }


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
    if len(changed) > limit or len(changed) > MAX_OBJECTS_PER_BATCH:
        raise KnowledgeHubError("connector returned more rows than requested")
    accepted: List[Dict[str, Any]] = []
    quarantined: List[Dict[str, Any]] = []
    tombstones: List[Dict[str, Any]] = []
    total_body_chars = 0
    for row in changed:
        try:
            normalized = normalize_object(adapter.connector_id, row)
        except KnowledgeHubError as exc:
            quarantined.append(_quarantine_record(row, str(exc)))
            continue
        total_body_chars += len(str(normalized.get("body", "")))
        if total_body_chars > MAX_BATCH_BODY_CHARS:
            raise KnowledgeHubError("connector batch body exceeds budget")
        if normalized["tombstone"]:
            tombstones.append(normalized)
        else:
            accepted.append(normalized)
    saved = dict(checkpoint)
    proposal: Dict[str, Any] = {}
    if not quarantined:
        proposal = _checkpoint_proposal(
            adapter.connector_id,
            checkpoint,
            str(adapter.checkpoint()),
            accepted,
            tombstones,
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
        "checkpoint_proposal": proposal,
        "checkpoint_advanced": False,
        "requires_consumer_ack": not quarantined,
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
        if len(self._rows) > limit:
            raise KnowledgeHubError("static connector fixture exceeds batch limit")
        return self._rows
