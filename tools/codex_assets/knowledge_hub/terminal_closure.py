"""Fail-closed terminal closure evaluation for Knowledge Hub.

Engineering qualification, product maturity, external administration/provider evidence,
and bounded historical debt are deliberately evaluated as separate concerns. A green
quality workflow never implies terminal closure by itself.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Mapping

from .artifact_governance import evaluate_artifact_governance
from .common import KnowledgeHubError, utc_timestamp
from .complexity_budget import evaluate_complexity_budget

DEFAULT_POLICY = "registry/terminal-closure.json"


def _load_object(path: pathlib.Path, label: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("{} is unavailable or invalid".format(label)) from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be a JSON object".format(label))
    return dict(value)


def _external_gaps(root: pathlib.Path, policy: Mapping[str, Any]) -> List[Dict[str, Any]]:
    external = policy.get("external_closure", {})
    if not isinstance(external, Mapping):
        raise KnowledgeHubError("terminal external_closure policy must be an object")
    source = str(external.get("source", "")).strip()
    required_ids = external.get("required_gap_ids", [])
    if not source or not isinstance(required_ids, list):
        raise KnowledgeHubError("terminal external closure policy is incomplete")
    platform = _load_object(root / source, "external closure registry")
    rows = platform.get("external_closure_gaps", [])
    if not isinstance(rows, list):
        raise KnowledgeHubError("external_closure_gaps must be a list")
    by_id = {
        str(row.get("id", "")): row
        for row in rows
        if isinstance(row, Mapping) and row.get("id")
    }
    unresolved = []
    for gap_id in [str(value) for value in required_ids]:
        row = by_id.get(gap_id)
        if row is None:
            unresolved.append({"id": gap_id, "status": "missing", "owner": ""})
        elif str(row.get("status", "")) != "closed":
            unresolved.append(
                {
                    "id": gap_id,
                    "status": str(row.get("status", "open")),
                    "owner": str(row.get("owner", "")),
                }
            )
    return unresolved


def _bounded_legacy_state(
    policy: Mapping[str, Any],
    complexity: Mapping[str, Any],
    artifacts: Mapping[str, Any],
) -> Dict[str, Any]:
    bounded = policy.get("bounded_legacy", {})
    if not isinstance(bounded, Mapping):
        raise KnowledgeHubError("bounded_legacy policy must be an object")
    max_modules = int(bounded.get("max_oversized_legacy_modules", 0) or 0)
    max_refs = int(bounded.get("max_legacy_artifact_references", 0) or 0)
    module_count = int(complexity.get("legacy_attention_count", 0) or 0)
    immutable_refs = artifacts.get("immutable_refs", {})
    if not isinstance(immutable_refs, Mapping):
        immutable_refs = {}
    ref_count = int(immutable_refs.get("legacy_reference_count", 0) or 0)
    return {
        "status": "pass" if module_count <= max_modules and ref_count <= max_refs else "needs-fix",
        "legacy_module_count": module_count,
        "legacy_module_max": max_modules,
        "legacy_artifact_reference_count": ref_count,
        "legacy_artifact_reference_max": max_refs,
        "growth_allowed": bool(bounded.get("growth_allowed", False)),
    }


def evaluate_terminal_closure(
    root: pathlib.Path,
    *,
    policy_path: str = DEFAULT_POLICY,
    snapshot_path: str = "",
) -> Dict[str, Any]:
    policy = _load_object(root / policy_path, "terminal closure policy")
    product_policy = policy.get("product_gate", {})
    if not isinstance(product_policy, Mapping):
        raise KnowledgeHubError("product_gate terminal policy must be an object")
    snapshot_name = snapshot_path or str(product_policy.get("snapshot", "")).strip()
    if not snapshot_name:
        raise KnowledgeHubError("terminal product snapshot path is missing")
    snapshot = _load_object(root / snapshot_name, "product final gate snapshot")
    external_gaps = _external_gaps(root, policy)
    complexity = evaluate_complexity_budget(root)
    artifacts = evaluate_artifact_governance(root)
    legacy = _bounded_legacy_state(policy, complexity, artifacts)
    branch_gc = policy.get("branch_gc", {})
    if not isinstance(branch_gc, Mapping):
        raise KnowledgeHubError("branch_gc terminal policy must be an object")

    checks = {
        "product_status": snapshot.get("status") == product_policy.get("require_status", "pass"),
        "product_terminal": snapshot.get("terminal") is True,
        "external_closure": not external_gaps,
        "complexity_no_regression": complexity.get("status") == "pass",
        "artifact_governance": artifacts.get("status") == "pass",
        "bounded_legacy": legacy.get("status") == "pass",
        "branch_gc": (not bool(branch_gc.get("required", False))) or branch_gc.get("status") == "closed",
    }
    blockers = [name for name, passed in checks.items() if not passed]
    terminal = not blockers
    return {
        "schema_version": 1,
        "contract": "knowledge-hub-terminal-closure-v1",
        "generated_at": utc_timestamp(),
        "status": "pass" if terminal else "needs-review",
        "terminal": terminal,
        "checks": checks,
        "blockers": blockers,
        "product": {
            "snapshot": snapshot_name,
            "status": snapshot.get("status", ""),
            "terminal": bool(snapshot.get("terminal", False)),
        },
        "external_closure": {
            "status": "pass" if not external_gaps else "needs-review",
            "open_count": len(external_gaps),
            "open_gaps": external_gaps,
        },
        "bounded_legacy": legacy,
        "branch_gc": {
            "status": str(branch_gc.get("status", "open")),
            "required": bool(branch_gc.get("required", False)),
            "retire_prefixes": list(branch_gc.get("retire_prefixes", [])),
        },
    }
