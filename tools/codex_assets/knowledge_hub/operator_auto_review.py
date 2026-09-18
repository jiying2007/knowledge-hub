"""AI-first selection of unambiguous governed binding proposals.

Selection is intentionally not authorization. This module only advances P2.4 proposals
to the existing deterministic patch-plan/review-bundle boundary when each canonical
item+field has exactly one ready proposal and there are no proposal conflicts.
"""

from __future__ import annotations

import pathlib
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Tuple

from .operator_binding_patch_plan import build_binding_patch_plan
from .operator_binding_review_bundle import build_binding_review_bundle


def _target_key(row: Mapping[str, Any]) -> Tuple[str, str]:
    target = row.get("target", {})
    if not isinstance(target, Mapping):
        return "", ""
    return str(target.get("item_id", "")), str(row.get("field", ""))


def build_unique_review_bundle(
    root: pathlib.Path, proposal: Mapping[str, Any]
) -> Dict[str, Any]:
    """Advance only uniquely determined proposal targets to a review bundle."""

    reasons: List[str] = []
    if proposal.get("projection") != "knowledge-operator-binding-proposal-v1":
        reasons.append("proposal-projection-invalid")
    if proposal.get("read_only") is not True:
        reasons.append("proposal-read-only-invalid")
    if proposal.get("canonical_write_performed") is not False:
        reasons.append("proposal-canonical-write-state-invalid")
    if proposal.get("automatic_binding_enabled") is not False:
        reasons.append("proposal-automatic-binding-state-invalid")
    if proposal.get("proposal_only") is not True:
        reasons.append("proposal-only-state-invalid")
    if int(proposal.get("blocked_conflict_count", 0) or 0) != 0:
        reasons.append("proposal-conflicts-present")
    if int(proposal.get("unmappable_count", 0) or 0) != 0:
        reasons.append("proposal-unmappable-present")
    rows = proposal.get("rows", [])
    if not isinstance(rows, list):
        reasons.append("proposal-rows-invalid")
        rows = []
    if reasons:
        return {
            "schema_version": 1,
            "projection": "knowledge-operator-auto-review-v1",
            "status": "blocked",
            "read_only": True,
            "selection_is_authorization": False,
            "canonical_write_performed": False,
            "automatic_binding_enabled": False,
            "automatic_execution_enabled": False,
            "selected_proposal_count": 0,
            "ambiguous_target_count": 0,
            "selected_proposal_fingerprints": [],
            "reason_codes": list(dict.fromkeys(reasons)),
            "review_bundle": {},
        }

    grouped: Dict[Tuple[str, str], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if row.get("proposal_status") != "ready-for-governed-review":
            continue
        if row.get("proposal_ready_for_review") is not True:
            continue
        key = _target_key(row)
        if not all(key):
            continue
        grouped[key].append(row)

    selected: List[str] = []
    ambiguous: List[Dict[str, Any]] = []
    for (item_id, field), candidates in sorted(grouped.items()):
        if len(candidates) != 1:
            ambiguous.append(
                {
                    "item_id": item_id,
                    "field": field,
                    "candidate_count": len(candidates),
                }
            )
            continue
        fingerprint = str(candidates[0].get("proposal_fingerprint", ""))
        if fingerprint:
            selected.append(fingerprint)

    if ambiguous:
        return {
            "schema_version": 1,
            "projection": "knowledge-operator-auto-review-v1",
            "status": "ambiguous",
            "read_only": True,
            "selection_is_authorization": False,
            "canonical_write_performed": False,
            "automatic_binding_enabled": False,
            "automatic_execution_enabled": False,
            "selected_proposal_count": 0,
            "ambiguous_target_count": len(ambiguous),
            "ambiguous_targets": ambiguous,
            "selected_proposal_fingerprints": [],
            "reason_codes": ["ambiguous-proposal-target"],
            "review_bundle": {},
        }
    if not selected:
        return {
            "schema_version": 1,
            "projection": "knowledge-operator-auto-review-v1",
            "status": "no-change",
            "read_only": True,
            "selection_is_authorization": False,
            "canonical_write_performed": False,
            "automatic_binding_enabled": False,
            "automatic_execution_enabled": False,
            "selected_proposal_count": 0,
            "ambiguous_target_count": 0,
            "selected_proposal_fingerprints": [],
            "reason_codes": [],
            "review_bundle": {},
        }

    plan = build_binding_patch_plan(root, proposal, selected)
    if plan.get("status") != "needs-governed-pr":
        return {
            "schema_version": 1,
            "projection": "knowledge-operator-auto-review-v1",
            "status": "blocked",
            "read_only": True,
            "selection_is_authorization": False,
            "canonical_write_performed": False,
            "automatic_binding_enabled": False,
            "automatic_execution_enabled": False,
            "selected_proposal_count": len(selected),
            "ambiguous_target_count": 0,
            "selected_proposal_fingerprints": selected,
            "reason_codes": ["patch-plan-not-ready"],
            "patch_plan": plan,
            "review_bundle": {},
        }
    bundle = build_binding_review_bundle(root, proposal, plan)
    return {
        "schema_version": 1,
        "projection": "knowledge-operator-auto-review-v1",
        "status": (
            "needs-governed-authorization"
            if bundle.get("status") == "needs-governed-authorization"
            else "blocked"
        ),
        "read_only": True,
        "selection_is_authorization": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "selected_proposal_count": len(selected),
        "ambiguous_target_count": 0,
        "selected_proposal_fingerprints": selected,
        "reason_codes": [] if bundle.get("status") == "needs-governed-authorization" else ["review-bundle-not-ready"],
        "patch_plan": plan,
        "review_bundle": bundle,
    }
