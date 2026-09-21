"""AI-first selection of unambiguous governed binding proposals.

Selection is intentionally not authorization. This module only advances P2.4 proposals
to the existing deterministic patch-plan/review-bundle boundary when each canonical
item+field has exactly one ready proposal and there are no proposal conflicts.
"""

from __future__ import annotations

import pathlib
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .operator_binding_patch_plan import build_binding_patch_plan
from .operator_binding_review_bundle import build_binding_review_bundle

PROJECTION = "knowledge-operator-auto-review-v1"


def _target_key(row: Mapping[str, Any]) -> Tuple[str, str]:
    target = row.get("target", {})
    if not isinstance(target, Mapping):
        return "", ""
    return str(target.get("item_id", "")), str(row.get("field", ""))


def _result(
    status: str,
    *,
    selected: Sequence[str] = (),
    ambiguous: Sequence[Mapping[str, Any]] = (),
    reasons: Sequence[str] = (),
    patch_plan: Optional[Mapping[str, Any]] = None,
    review_bundle: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "schema_version": 1,
        "projection": PROJECTION,
        "status": status,
        "read_only": True,
        "selection_is_authorization": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "selected_proposal_count": len(selected),
        "ambiguous_target_count": len(ambiguous),
        "selected_proposal_fingerprints": list(selected),
        "reason_codes": list(dict.fromkeys(str(value) for value in reasons)),
        "review_bundle": dict(review_bundle or {}),
    }
    if ambiguous:
        payload["ambiguous_targets"] = [dict(row) for row in ambiguous]
    if patch_plan is not None:
        payload["patch_plan"] = dict(patch_plan)
    return payload


def _proposal_reasons(proposal: Mapping[str, Any]) -> Tuple[List[str], List[Any]]:
    reasons: List[str] = []
    checks = (
        (
            proposal.get("projection")
            == "knowledge-operator-binding-proposal-v1",
            "proposal-projection-invalid",
        ),
        (
            proposal.get("read_only") is True,
            "proposal-read-only-invalid",
        ),
        (
            proposal.get("canonical_write_performed") is False,
            "proposal-canonical-write-state-invalid",
        ),
        (
            proposal.get("automatic_binding_enabled") is False,
            "proposal-automatic-binding-state-invalid",
        ),
        (
            proposal.get("proposal_only") is True,
            "proposal-only-state-invalid",
        ),
    )
    reasons.extend(reason for passed, reason in checks if not passed)
    if int(proposal.get("blocked_conflict_count", 0) or 0) != 0:
        reasons.append("proposal-conflicts-present")
    if int(proposal.get("unmappable_count", 0) or 0) != 0:
        reasons.append("proposal-unmappable-present")
    rows = proposal.get("rows", [])
    if not isinstance(rows, list):
        reasons.append("proposal-rows-invalid")
        rows = []
    return reasons, rows


def _select_unique(
    rows: Sequence[Any],
) -> Tuple[List[str], List[Dict[str, Any]]]:
    grouped: Dict[Tuple[str, str], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if row.get("proposal_status") != "ready-for-governed-review":
            continue
        if row.get("proposal_ready_for_review") is not True:
            continue
        key = _target_key(row)
        if all(key):
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
    return selected, ambiguous


def _review_result(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
    selected: Sequence[str],
) -> Dict[str, Any]:
    plan = build_binding_patch_plan(root, proposal, selected)
    if plan.get("status") != "needs-governed-pr":
        return _result(
            "blocked",
            selected=selected,
            reasons=["patch-plan-not-ready"],
            patch_plan=plan,
        )
    bundle = build_binding_review_bundle(root, proposal, plan)
    ready = bundle.get("status") == "needs-governed-authorization"
    return _result(
        "needs-governed-authorization" if ready else "blocked",
        selected=selected,
        reasons=[] if ready else ["review-bundle-not-ready"],
        patch_plan=plan,
        review_bundle=bundle,
    )


def build_unique_review_bundle(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
) -> Dict[str, Any]:
    """Advance only uniquely determined proposal targets to a review bundle."""

    reasons, rows = _proposal_reasons(proposal)
    if reasons:
        return _result("blocked", reasons=reasons)

    selected, ambiguous = _select_unique(rows)
    if ambiguous:
        return _result(
            "ambiguous",
            ambiguous=ambiguous,
            reasons=["ambiguous-proposal-target"],
        )
    if not selected:
        return _result("no-change")
    return _review_result(root, proposal, selected)
