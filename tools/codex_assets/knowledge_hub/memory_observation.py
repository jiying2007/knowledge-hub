"""Privacy-safe read-side receipts for P7 memory lifecycle observations.

This module observes the existing private memory runtime without persisting a second
ledger or claiming production provenance. Callers may retain the returned receipt in
an independently governed source artifact for later strict pilot evidence assembly.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any, Dict

from .common import KnowledgeHubError, utc_timestamp
from .memory_runtime import active_memories

EXPECTED_STATES = {"any", "present", "absent"}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _digest(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def observe_memory_state(
    root: pathlib.Path,
    *,
    principal_id: str,
    agent_id: str,
    scope_ref: str,
    memory_id: str = "",
    expected_state: str = "any",
) -> Dict[str, Any]:
    """Return a bounded receipt for one exact principal/agent/scope read.

    Raw memory summaries and raw identity values are intentionally omitted. When a
    target memory id is supplied, only its SHA-256 appears in the result.
    """

    principal_id = str(principal_id).strip()
    agent_id = str(agent_id).strip()
    scope_ref = str(scope_ref).strip()
    memory_id = str(memory_id).strip()
    expected_state = str(expected_state).strip()
    if not principal_id or not agent_id or not scope_ref:
        raise KnowledgeHubError("memory observation identity fields are required")
    if expected_state not in EXPECTED_STATES:
        raise KnowledgeHubError("memory observation expected_state is invalid")
    if expected_state != "any" and not memory_id:
        raise KnowledgeHubError("memory observation target memory_id is required")

    rows = active_memories(
        root,
        principal_id=principal_id,
        agent_id=agent_id,
        scope_ref=scope_ref,
    )
    active_ids = sorted(str(row.get("memory_id", "")) for row in rows)
    target_present = memory_id in active_ids if memory_id else False
    expectation_met = (
        expected_state == "any"
        or (expected_state == "present" and target_present)
        or (expected_state == "absent" and not target_present)
    )
    state_material = {
        "active_count": len(active_ids),
        "active_memory_id_sha256": [_sha256(value) for value in active_ids],
    }
    result: Dict[str, Any] = {
        "schema_version": "knowledge-hub.memory-observation.v1",
        "status": "pass" if expectation_met else "fail",
        "observed_at": utc_timestamp(),
        "principal_id_sha256": _sha256(principal_id),
        "agent_id_sha256": _sha256(agent_id),
        "scope_ref_sha256": _sha256(scope_ref),
        "target_memory_id_sha256": _sha256(memory_id) if memory_id else "",
        "expected_state": expected_state,
        "target_present": target_present,
        "active_count": len(active_ids),
        "state_sha256": _digest(state_material),
        "event_count": 1,
        "raw_summary_stored": False,
        "raw_identity_stored": False,
        "raw_memory_id_stored": False,
        "canonical_write_performed": False,
    }
    result["receipt_sha256"] = _digest(result)
    return result
