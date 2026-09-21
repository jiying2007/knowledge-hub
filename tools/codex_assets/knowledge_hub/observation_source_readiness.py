"""Report explicit real-observation workflow registration readiness."""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any, Dict, List, Mapping, Tuple

from .common import KnowledgeHubError

PROJECTION = "knowledge-hub-observation-source-readiness-v1"
WORKFLOW_PREFIX = ".github/workflows/real-observation-"


def _load_object(path: pathlib.Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("{} is unavailable or invalid".format(label)) from exc
    if not isinstance(payload, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return dict(payload)


def _fingerprint(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        dict(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _policy_config(
    policy: Mapping[str, Any],
) -> Tuple[List[str], Mapping[str, Any], str]:
    external = policy.get("external_evidence", {})
    if not isinstance(external, Mapping):
        raise KnowledgeHubError("external_evidence policy must be an object")
    supported = external.get("supported_gaps", [])
    allowlists = external.get("observation_source_workflow_allowlist", {})
    prefix = str(external.get("observation_source_workflow_prefix") or "")
    if prefix != WORKFLOW_PREFIX:
        raise KnowledgeHubError(
            "observation source workflow namespace policy is invalid"
        )
    if not isinstance(supported, list) or not isinstance(allowlists, Mapping):
        raise KnowledgeHubError("observation source registration policy is invalid")
    gap_ids = [str(value) for value in supported if str(value)]
    if len(gap_ids) != len(supported) or len(gap_ids) != len(set(gap_ids)):
        raise KnowledgeHubError(
            "supported external gaps must be unique and non-empty"
        )
    if set(allowlists) != set(gap_ids):
        raise KnowledgeHubError(
            "observation source allowlist must match supported gaps"
        )
    return gap_ids, allowlists, prefix


def _canonical_statuses(
    platform: Mapping[str, Any],
    gap_ids: List[str],
) -> Dict[str, str]:
    canonical_rows = platform.get("external_closure_gaps", [])
    if not isinstance(canonical_rows, list):
        raise KnowledgeHubError("external_closure_gaps must be a list")
    canonical: Dict[str, str] = {}
    counts: Dict[str, int] = {}
    for row in canonical_rows:
        if not isinstance(row, Mapping) or not row.get("id"):
            continue
        gap_id = str(row["id"])
        counts[gap_id] = counts.get(gap_id, 0) + 1
        canonical[gap_id] = str(row.get("status", ""))
    for gap_id in gap_ids:
        if counts.get(gap_id, 0) != 1:
            raise KnowledgeHubError(
                "supported external gap {} must exist exactly once".format(
                    gap_id
                )
            )
        if canonical[gap_id] not in {"open", "closed"}:
            raise KnowledgeHubError(
                "supported external gap {} has invalid status".format(gap_id)
            )
    return canonical


def _gap_row(
    gap_id: str,
    workflows: Any,
    *,
    prefix: str,
    canonical_status: str,
) -> Dict[str, Any]:
    if not isinstance(workflows, list):
        raise KnowledgeHubError(
            "observation source allowlist for {} must be a list".format(gap_id)
        )
    normalized = sorted({str(value) for value in workflows if str(value)})
    if any(not value.startswith(prefix) for value in normalized):
        raise KnowledgeHubError(
            "observation source workflow for {} is outside the reserved namespace".format(
                gap_id
            )
        )
    if len(normalized) != len(workflows):
        raise KnowledgeHubError(
            "observation source allowlist for {} must be unique/non-empty".format(
                gap_id
            )
        )
    if canonical_status == "closed":
        status, next_action = "closed", "none"
    elif normalized:
        status, next_action = "registered", "produce-real-observation"
    else:
        status = "unregistered"
        next_action = "register-real-observation-workflow"
    row = {
        "gap_id": gap_id,
        "canonical_gap_status": canonical_status,
        "status": status,
        "registered_workflow_count": len(normalized),
        "registered_workflows": normalized,
        "next_action": next_action,
    }
    row["row_fingerprint"] = _fingerprint(row)
    return row


def _report(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    report = {
        "schema_version": 1,
        "projection": PROJECTION,
        "status": (
            "needs-registration"
            if any(row["status"] == "unregistered" for row in rows)
            else (
                "ready-for-observation"
                if any(row["status"] == "registered" for row in rows)
                else "closed"
            )
        ),
        "read_only": True,
        "canonical_write_performed": False,
        "owner_decision_generated": False,
        "gap_count": len(rows),
        "unregistered_count": sum(
            1 for row in rows if row["status"] == "unregistered"
        ),
        "registered_open_count": sum(
            1 for row in rows if row["status"] == "registered"
        ),
        "rows": rows,
    }
    by_gap = {row["gap_id"]: row for row in rows}
    connector = by_gap.get("connector-provider-pilot", {})
    production = [
        by_gap.get("production-retrieval-eval", {}),
        by_gap.get("memory-lifecycle-pilot", {}),
        by_gap.get("real-adoption-evidence", {}),
    ]
    report["connector_tracker_fingerprint"] = _fingerprint(connector)
    report["production_tracker_fingerprint"] = _fingerprint(
        {"rows": production}
    )
    report["packet_fingerprint"] = _fingerprint(report)
    return report


def build_observation_source_readiness(root: pathlib.Path) -> Dict[str, Any]:
    root = pathlib.Path(root).resolve()
    policy = _load_object(
        root / "registry/ai-operations-policy.json",
        "AI operations policy",
    )
    platform = _load_object(
        root / "registry/knowledge-platform-p5-p10.json",
        "knowledge platform registry",
    )
    gap_ids, allowlists, prefix = _policy_config(policy)
    canonical = _canonical_statuses(platform, gap_ids)
    rows = [
        _gap_row(
            gap_id,
            allowlists.get(gap_id),
            prefix=prefix,
            canonical_status=canonical[gap_id],
        )
        for gap_id in gap_ids
    ]
    return _report(rows)
