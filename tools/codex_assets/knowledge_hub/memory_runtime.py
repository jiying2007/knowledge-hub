"""P7 private memory runtime with TTL, provenance, tombstones, and consolidation.

Memory never becomes canonical knowledge automatically. Durable promotion remains a
separate owner-governed path.
"""

from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import json
import os
import pathlib
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .common import KnowledgeHubError, ensure_private_directory, utc_timestamp

MEMORY_LEVELS = {"working", "session", "episodic", "semantic", "procedural", "policy"}
DURABLE_LEVELS = {"semantic", "procedural", "policy"}
DEFAULT_LEDGER = pathlib.Path(".cache/knowledge-hub/memory/events.jsonl")
MAX_SUMMARY_CHARS = 4096
MAX_SOURCE_REFS = 32
MAX_LEDGER_BYTES = 32 * 1024 * 1024
MAX_EVENTS = 50000


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _date(value: str) -> dt.datetime:
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise KnowledgeHubError("memory timestamp must be ISO-8601") from exc


def _source_refs(value: Sequence[str]) -> List[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KnowledgeHubError("memory source_refs must be a sequence")
    if len(value) > MAX_SOURCE_REFS:
        raise KnowledgeHubError("memory source_refs exceed budget")
    rows = [str(row).strip() for row in value]
    if any(not row or len(row) > 1024 for row in rows):
        raise KnowledgeHubError("memory source_refs contain invalid value")
    return rows


def memory_event(
    *,
    agent_id: str,
    principal_id: str,
    level: str,
    summary: str,
    scope_ref: str,
    source_refs: Sequence[str],
    ttl_seconds: int = 0,
    event_type: str = "upsert",
    memory_id: str = "",
) -> Dict[str, Any]:
    level = str(level).strip()
    if level not in MEMORY_LEVELS:
        raise KnowledgeHubError("invalid memory level")
    if event_type not in {"upsert", "forget", "supersede"}:
        raise KnowledgeHubError("invalid memory event type")
    summary = str(summary).strip()
    if event_type == "upsert" and (not summary or len(summary) > MAX_SUMMARY_CHARS):
        raise KnowledgeHubError("memory summary must be non-empty and bounded")
    if ttl_seconds < 0 or ttl_seconds > 365 * 24 * 3600:
        raise KnowledgeHubError("memory TTL is outside policy")
    agent_id = str(agent_id).strip()
    principal_id = str(principal_id).strip()
    scope_ref = str(scope_ref).strip()
    if not agent_id or not principal_id or not scope_ref:
        raise KnowledgeHubError("memory identity fields are required")
    refs = _source_refs(source_refs)
    payload = {
        "schema_version": "knowledge-hub.memory-event.v1",
        "event_type": event_type,
        "agent_id": agent_id,
        "principal_id": principal_id,
        "level": level,
        "summary": summary if event_type == "upsert" else "",
        "scope_ref": scope_ref,
        "source_refs": refs,
        "ttl_seconds": int(ttl_seconds),
        "recorded_at": utc_timestamp(),
        "canonical_write": False,
    }
    payload["memory_id"] = str(memory_id) if memory_id else "mem-" + _digest(payload)[:24]
    return payload


def _ledger_path(root: pathlib.Path) -> pathlib.Path:
    path = root / DEFAULT_LEDGER
    ensure_private_directory(path.parent)
    if path.exists() and path.is_symlink():
        raise KnowledgeHubError("memory ledger must not be a symlink")
    return path


def _lock_path(root: pathlib.Path) -> pathlib.Path:
    path = root / DEFAULT_LEDGER.parent / "memory.lock"
    ensure_private_directory(path.parent)
    if path.exists() and path.is_symlink():
        raise KnowledgeHubError("memory lock must not be a symlink")
    return path


def _read_unlocked(root: pathlib.Path) -> List[Dict[str, Any]]:
    path = _ledger_path(root)
    if not path.exists():
        return []
    if path.stat().st_size > MAX_LEDGER_BYTES:
        raise KnowledgeHubError("memory ledger exceeds byte budget")
    rows: List[Dict[str, Any]] = []
    previous = ""
    try:
        handle = path.open("r", encoding="utf-8")
    except OSError as exc:
        raise KnowledgeHubError("memory ledger is unreadable") from exc
    with handle:
        for raw in handle:
            if not raw.strip():
                continue
            if len(rows) >= MAX_EVENTS:
                raise KnowledgeHubError("memory ledger exceeds event budget")
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise KnowledgeHubError("memory ledger contains invalid JSON") from exc
            if not isinstance(row, Mapping):
                raise KnowledgeHubError("memory ledger row must be an object")
            value = dict(row)
            digest = str(value.pop("event_sha256", ""))
            if str(value.get("previous_event_sha256", "")) != previous:
                raise KnowledgeHubError("memory ledger chain link mismatch")
            if digest != _digest(value):
                raise KnowledgeHubError("memory ledger digest mismatch")
            value["event_sha256"] = digest
            rows.append(value)
            previous = digest
    return rows


def read_memory_ledger(root: pathlib.Path) -> List[Dict[str, Any]]:
    lock_path = _lock_path(root)
    with lock_path.open("a+") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_SH)
        try:
            return _read_unlocked(root)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _validate_event(event: Mapping[str, Any]) -> None:
    if event.get("schema_version") != "knowledge-hub.memory-event.v1":
        raise KnowledgeHubError("unsupported memory event schema")
    if str(event.get("event_type", "")) not in {"upsert", "forget", "supersede"}:
        raise KnowledgeHubError("invalid memory event type")
    if str(event.get("level", "")) not in MEMORY_LEVELS:
        raise KnowledgeHubError("invalid memory event level")
    for field in ("agent_id", "principal_id", "scope_ref", "memory_id", "recorded_at"):
        if not str(event.get(field, "")).strip():
            raise KnowledgeHubError("memory event missing {}".format(field))
    _date(str(event.get("recorded_at", "")))
    _source_refs(event.get("source_refs", []))


def append_memory_event(root: pathlib.Path, event: Mapping[str, Any]) -> Dict[str, Any]:
    _validate_event(event)
    path = _ledger_path(root)
    lock_path = _lock_path(root)
    with lock_path.open("a+") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            rows = _read_unlocked(root)
            previous = str(rows[-1].get("event_sha256", "")) if rows else ""
            record = dict(event)
            record["previous_event_sha256"] = previous
            record["event_sha256"] = _digest(record)
            flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(str(path), flags, 0o600)
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return {"status": "recorded", "record": record, "canonical_write_performed": False}


def _expired(row: Mapping[str, Any], now: dt.datetime) -> bool:
    ttl = int(row.get("ttl_seconds", 0) or 0)
    if ttl <= 0:
        return False
    recorded = _date(str(row.get("recorded_at", "")))
    if recorded.tzinfo is None:
        recorded = recorded.replace(tzinfo=dt.timezone.utc)
    return recorded + dt.timedelta(seconds=ttl) <= now


def active_memories(
    root: pathlib.Path,
    *,
    principal_id: str,
    agent_id: str,
    scope_ref: str = "",
    now: Optional[dt.datetime] = None,
) -> List[Dict[str, Any]]:
    current = now or dt.datetime.now(dt.timezone.utc)
    state: Dict[str, Dict[str, Any]] = {}
    for row in read_memory_ledger(root):
        memory_id = str(row.get("memory_id", ""))
        if str(row.get("principal_id", "")) != principal_id:
            continue
        if str(row.get("agent_id", "")) != agent_id:
            continue
        if scope_ref and str(row.get("scope_ref", "")) != scope_ref:
            continue
        if row.get("event_type") in {"forget", "supersede"}:
            state.pop(memory_id, None)
            continue
        if not _expired(row, current):
            state[memory_id] = dict(row)
        else:
            state.pop(memory_id, None)
    return sorted(state.values(), key=lambda row: str(row.get("recorded_at", "")))


def forget_memory(
    root: pathlib.Path,
    *,
    memory_id: str,
    principal_id: str,
    agent_id: str,
    scope_ref: str,
) -> Dict[str, Any]:
    event = memory_event(
        agent_id=agent_id,
        principal_id=principal_id,
        level="working",
        summary="",
        scope_ref=scope_ref,
        source_refs=(),
        event_type="forget",
        memory_id=memory_id,
    )
    return append_memory_event(root, event)


def supersede_memory(
    root: pathlib.Path,
    *,
    memory_id: str,
    principal_id: str,
    agent_id: str,
    scope_ref: str,
) -> Dict[str, Any]:
    event = memory_event(
        agent_id=agent_id,
        principal_id=principal_id,
        level="working",
        summary="",
        scope_ref=scope_ref,
        source_refs=(),
        event_type="supersede",
        memory_id=memory_id,
    )
    return append_memory_event(root, event)


def consolidation_candidates(
    root: pathlib.Path,
    *,
    principal_id: str,
    agent_id: str,
    scope_ref: str = "",
) -> Dict[str, Any]:
    rows = active_memories(root, principal_id=principal_id, agent_id=agent_id, scope_ref=scope_ref)
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for row in rows:
        key = (str(row.get("level", "")), str(row.get("scope_ref", "")))
        groups.setdefault(key, []).append(row)
    candidates = []
    for (level, scope), group in sorted(groups.items()):
        if level not in DURABLE_LEVELS or len(group) < 2:
            continue
        refs = sorted({str(ref) for row in group for ref in row.get("source_refs", [])})
        summaries = [str(row.get("summary", "")) for row in group]
        candidates.append(
            {
                "level": level,
                "scope_ref": scope,
                "source_refs": refs[:MAX_SOURCE_REFS],
                "memory_ids": [str(row.get("memory_id", "")) for row in group],
                "summary_sha256": hashlib.sha256("\n".join(summaries).encode("utf-8")).hexdigest(),
                "promotion_status": "candidate-only",
                "requires": ["provenance", "dedup", "evidence", "human-or-owner-gate"],
            }
        )
    return {
        "schema_version": "knowledge-hub.memory-consolidation.v1",
        "status": "pass",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "canonical_write_performed": False,
    }
