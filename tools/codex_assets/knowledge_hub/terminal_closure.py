"""Fail-closed terminal closure evaluation for Knowledge Hub.

Engineering qualification, product maturity, external administration/provider evidence,
and bounded historical debt are deliberately evaluated as separate concerns. A green
quality workflow never implies terminal closure by itself.
"""

from __future__ import annotations

import json
import os
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
    require_evidence_refs = bool(external.get("require_evidence_refs_on_close", False))
    if not source or not isinstance(required_ids, list):
        raise KnowledgeHubError("terminal external closure policy is incomplete")
    policy_required_ids = sorted({str(value) for value in required_ids if str(value).strip()})
    if len(policy_required_ids) != len(required_ids):
        raise KnowledgeHubError("terminal external required_gap_ids must be unique and non-empty")

    platform = _load_object(root / source, "external closure registry")
    rows = platform.get("external_closure_gaps", [])
    if not isinstance(rows, list):
        raise KnowledgeHubError("external_closure_gaps must be a list")
    by_id = {
        str(row.get("id", "")): row
        for row in rows
        if isinstance(row, Mapping) and row.get("id")
    }
    registry_required_ids = sorted(
        gap_id
        for gap_id, row in by_id.items()
        if row.get("required") is True
    )
    unresolved: List[Dict[str, Any]] = []
    if policy_required_ids != registry_required_ids:
        unresolved.append(
            {
                "id": "terminal-policy-required-gap-drift",
                "status": "blocked",
                "owner": "terminal-policy",
                "policy_required_gap_ids": policy_required_ids,
                "registry_required_gap_ids": registry_required_ids,
            }
        )

    for gap_id in policy_required_ids:
        row = by_id.get(gap_id)
        if row is None:
            unresolved.append({"id": gap_id, "status": "missing", "owner": ""})
            continue
        status = str(row.get("status", "open"))
        evidence_refs = row.get("evidence_refs", [])
        valid_refs = (
            isinstance(evidence_refs, list)
            and bool(evidence_refs)
            and all(isinstance(value, str) and value.strip() for value in evidence_refs)
        )
        if status != "closed":
            unresolved.append(
                {
                    "id": gap_id,
                    "status": status,
                    "owner": str(row.get("owner", "")),
                }
            )
        elif require_evidence_refs and not valid_refs:
            unresolved.append(
                {
                    "id": gap_id,
                    "status": "closed-without-evidence",
                    "owner": str(row.get("owner", "")),
                }
            )
    return unresolved


def _legacy_limits(root: pathlib.Path, bounded: Mapping[str, Any]) -> Dict[str, int]:
    source = str(bounded.get("source", "")).strip()
    if not source:
        return {
            "modules": int(bounded.get("max_oversized_legacy_modules", 0) or 0),
            "refs": int(bounded.get("max_legacy_artifact_references", 0) or 0),
        }
    debt = _load_object(root / source, "legacy debt registry")
    modules = debt.get("oversized_modules", {})
    refs = debt.get("legacy_artifact_references", {})
    if not isinstance(modules, Mapping) or not isinstance(refs, Mapping):
        raise KnowledgeHubError("legacy debt registry is incomplete")
    return {
        "modules": int(modules.get("baseline_count", 0) or 0),
        "refs": int(refs.get("baseline_count", 0) or 0),
    }


def _bounded_legacy_state(
    root: pathlib.Path,
    policy: Mapping[str, Any],
    complexity: Mapping[str, Any],
    artifacts: Mapping[str, Any],
) -> Dict[str, Any]:
    bounded = policy.get("bounded_legacy", {})
    if not isinstance(bounded, Mapping):
        raise KnowledgeHubError("bounded_legacy policy must be an object")
    limits = _legacy_limits(root, bounded)
    module_count = int(complexity.get("legacy_attention_count", 0) or 0)
    immutable_refs = artifacts.get("immutable_refs", {})
    if not isinstance(immutable_refs, Mapping):
        immutable_refs = {}
    ref_count = int(immutable_refs.get("legacy_reference_count", 0) or 0)
    return {
        "status": "pass"
        if module_count <= limits["modules"] and ref_count <= limits["refs"]
        else "needs-fix",
        "legacy_module_count": module_count,
        "legacy_module_max": limits["modules"],
        "legacy_artifact_reference_count": ref_count,
        "legacy_artifact_reference_max": limits["refs"],
        "growth_allowed": bool(bounded.get("growth_allowed", False)),
    }


def _branch_candidates(lifecycle: Mapping[str, Any]) -> List[str]:
    rows = lifecycle.get("retirement_candidates", [])
    if not isinstance(rows, list):
        raise KnowledgeHubError("branch retirement candidates must be a list")
    return sorted(
        {
            str(row.get("branch", ""))
            for row in rows
            if isinstance(row, Mapping) and row.get("branch")
        }
    )


def _branch_gc_state(root: pathlib.Path, policy: Mapping[str, Any]) -> Dict[str, Any]:
    config = policy.get("branch_gc", {})
    if not isinstance(config, Mapping):
        raise KnowledgeHubError("branch_gc terminal policy must be an object")
    if not bool(config.get("required", False)):
        return {"required": False, "status": "pass", "remaining_candidates": []}
    source = str(config.get("source", "")).strip()
    evidence_path = str(config.get("evidence", "")).strip()
    if not source or not evidence_path:
        raise KnowledgeHubError("branch_gc source/evidence is missing")
    lifecycle = _load_object(root / source, "branch lifecycle registry")
    candidates = _branch_candidates(lifecycle)
    try:
        evidence = _load_object(root / evidence_path, "remote branch inventory")
    except KnowledgeHubError:
        return {
            "required": True,
            "status": "blocked",
            "retirement_candidates": candidates,
            "remaining_candidates": candidates,
            "reason": "fresh-remote-branch-inventory-missing",
        }
    evidence_candidates = sorted(
        str(value) for value in evidence.get("retirement_candidates", [])
    )
    remaining = sorted(str(value) for value in evidence.get("remaining_candidates", []))
    current_sha = os.environ.get("GITHUB_SHA", "").strip()
    revision_matches = True
    if bool(config.get("require_current_github_sha_when_available", False)) and current_sha:
        revision_matches = str(evidence.get("source_revision", "")) == current_sha
    status = "pass"
    reason = ""
    if evidence.get("status") != "pass":
        status = "needs-review"
        reason = "remote-branch-inventory-not-clean"
    elif evidence_candidates != candidates:
        status = "blocked"
        reason = "branch-inventory-candidate-set-drift"
    elif remaining:
        status = "needs-review"
        reason = "retirement-candidates-still-present"
    elif not revision_matches:
        status = "blocked"
        reason = "branch-inventory-revision-mismatch"
    return {
        "required": True,
        "status": status,
        "repository": str(evidence.get("repository", "")),
        "source_revision": str(evidence.get("source_revision", "")),
        "revision_matches_current_run": revision_matches,
        "retirement_candidates": candidates,
        "remaining_candidates": remaining,
        "reason": reason,
        "snapshot": evidence_path,
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
    legacy = _bounded_legacy_state(root, policy, complexity, artifacts)
    branch_gc = _branch_gc_state(root, policy)

    checks = {
        "product_status": snapshot.get("status") == product_policy.get("require_status", "pass"),
        "product_terminal": snapshot.get("terminal") is True,
        "external_closure": not external_gaps,
        "complexity_no_regression": complexity.get("status") == "pass",
        "artifact_governance": artifacts.get("status") == "pass",
        "bounded_legacy": legacy.get("status") == "pass",
        "branch_gc": branch_gc.get("status") == "pass",
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
        "branch_gc": branch_gc,
    }
