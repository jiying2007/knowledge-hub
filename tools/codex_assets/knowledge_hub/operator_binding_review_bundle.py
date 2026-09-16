"""Deterministic human-review bundles for governed Operator binding patch plans."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .operator_binding_patch_plan import build_binding_patch_plan

PATCH_PLAN_PROJECTION = "knowledge-operator-binding-patch-plan-v1"
REVIEW_BUNDLE_PROJECTION = "knowledge-operator-binding-review-bundle-v1"
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
MAX_REVIEW_ROWS = 50
MAX_REVIEW_BYTES = 131072


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:{}".format(hashlib.sha256(raw).hexdigest())


def _blocked(
    reasons: Sequence[str],
    *,
    status: str = "blocked",
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": REVIEW_BUNDLE_PROJECTION,
        "status": status,
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "apply_enabled": False,
        "selection_is_authorization": False,
        "authorization_state": "not-provided",
        "requires_governed_authorization": True,
        "requires_governed_pr": True,
        "review_bundle_only": True,
        "status_mutation_planned": False,
        "owner_mutation_planned": False,
        "readiness_mutation_planned": False,
        "selected_proposal_count": 0,
        "review_row_count": 0,
        "rows": [],
        "patch_plan_fingerprint": "",
        "review_bundle_fingerprint": "",
        "pr_review": {},
        "reason_codes": list(dict.fromkeys(str(value) for value in reasons if str(value))),
    }


def _patch_plan_contract_reasons(patch_plan: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    expected = {
        "projection": PATCH_PLAN_PROJECTION,
        "status": "needs-governed-pr",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "apply_enabled": False,
        "patch_plan_only": True,
        "selection_is_authorization": False,
        "requires_governed_pr": True,
        "status_mutation_planned": False,
        "owner_mutation_planned": False,
        "readiness_mutation_planned": False,
        "planned_write_count": 1,
        "registry_path": "registry/items.jsonl",
    }
    for key, expected_value in expected.items():
        if patch_plan.get(key) != expected_value:
            reasons.append("patch-plan-{}-invalid".format(key.replace("_", "-")))
    selected = patch_plan.get("selected_proposal_fingerprints", [])
    rows = patch_plan.get("rows", [])
    if not isinstance(selected, list) or not selected:
        reasons.append("patch-plan-selection-invalid")
    elif len(selected) > MAX_REVIEW_ROWS:
        reasons.append("patch-plan-selection-budget-exceeded")
    elif any(not FINGERPRINT_RE.fullmatch(str(value)) for value in selected):
        reasons.append("patch-plan-selection-fingerprint-invalid")
    elif selected != sorted(set(str(value) for value in selected)):
        reasons.append("patch-plan-selection-not-canonical")
    if int(patch_plan.get("selected_proposal_count", -1) or 0) != len(selected):
        reasons.append("patch-plan-selection-count-mismatch")
    if not isinstance(rows, list):
        reasons.append("patch-plan-rows-invalid")
        rows = []
    if int(patch_plan.get("planned_item_count", -1) or 0) != len(rows):
        reasons.append("patch-plan-item-count-mismatch")
    for key in ("registry_before_sha256", "registry_after_sha256"):
        value = str(patch_plan.get(key, ""))
        if not re.fullmatch(r"[0-9a-f]{64}", value):
            reasons.append("patch-plan-{}-invalid".format(key.replace("_", "-")))
    transaction = patch_plan.get("transaction_plan", {})
    if not isinstance(transaction, Mapping):
        reasons.append("patch-plan-transaction-invalid")
    else:
        if transaction.get("read_only") is not True:
            reasons.append("patch-plan-transaction-not-read-only")
        if int(transaction.get("changed_count", -1) or 0) != 1:
            reasons.append("patch-plan-transaction-change-count-invalid")
    if patch_plan.get("reason_codes") != ["governed-pr-required"]:
        reasons.append("patch-plan-reason-codes-invalid")
    return list(dict.fromkeys(reasons))


def _selected_proposal_rows(
    proposal: Mapping[str, Any], selected: Sequence[str]
) -> Tuple[List[Mapping[str, Any]], List[str]]:
    rows = proposal.get("rows", [])
    if not isinstance(rows, list):
        return [], ["proposal-rows-invalid"]
    by_fingerprint: Dict[str, List[Mapping[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        fingerprint = str(row.get("proposal_fingerprint", ""))
        if fingerprint:
            by_fingerprint.setdefault(fingerprint, []).append(row)
    chosen: List[Mapping[str, Any]] = []
    reasons: List[str] = []
    for fingerprint in selected:
        matches = by_fingerprint.get(fingerprint, [])
        if len(matches) != 1:
            reasons.append("selected-proposal-not-unique:{}".format(fingerprint))
            continue
        row = matches[0]
        if row.get("proposal_status") != "ready-for-governed-review":
            reasons.append("selected-proposal-not-reviewable:{}".format(fingerprint))
        chosen.append(row)
    return chosen, reasons


def _coverage_reasons(
    patch_plan: Mapping[str, Any],
    selected_rows: Sequence[Mapping[str, Any]],
    selected: Sequence[str],
) -> List[str]:
    reasons: List[str] = []
    plan_rows = [row for row in patch_plan.get("rows", []) if isinstance(row, Mapping)]
    covered: List[str] = []
    for row in plan_rows:
        values = row.get("selected_proposal_fingerprints", [])
        if isinstance(values, list):
            covered.extend(str(value) for value in values)
    if sorted(covered) != sorted(selected):
        reasons.append("patch-plan-proposal-coverage-mismatch")
    for proposal_row in selected_rows:
        target = proposal_row.get("target", {})
        if not isinstance(target, Mapping):
            reasons.append("selected-proposal-target-invalid")
            continue
        field = str(proposal_row.get("field", ""))
        matches = [
            row
            for row in plan_rows
            if str(row.get("item_id", "")) == str(target.get("item_id", ""))
            and str(row.get("project_id", "")) == str(target.get("project_id", ""))
            and str(row.get("item_path", "")) == str(target.get("item_path", ""))
            and field in row.get("changed_fields", [])
        ]
        if len(matches) != 1:
            reasons.append(
                "patch-plan-target-coverage-invalid:{}".format(
                    str(proposal_row.get("proposal_fingerprint", ""))
                )
            )
    return list(dict.fromkeys(reasons))


def _review_rows(selected_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for row in selected_rows:
        target = row.get("target", {})
        if not isinstance(target, Mapping):
            target = {}
        rows.append(
            {
                "proposal_fingerprint": str(row.get("proposal_fingerprint", "")),
                "candidate_snapshot_fingerprint": str(
                    row.get("candidate_snapshot_fingerprint", "")
                ),
                "project_id": str(row.get("project_id", "")),
                "item_id": str(target.get("item_id", "")),
                "item_path": str(target.get("item_path", "")),
                "field": str(row.get("field", "")),
                "mutation_intent": str(row.get("mutation_intent", "")),
                "current_value": row.get("current_value"),
                "proposed_reference": row.get("proposed_reference", {}),
                "proposed_value": row.get("proposed_value"),
                "provider": str(row.get("provider", "")),
                "source_target": str(row.get("source_target", "")),
            }
        )
    return sorted(
        rows,
        key=lambda value: (
            value["project_id"],
            value["item_id"],
            value["field"],
            value["proposal_fingerprint"],
        ),
    )


def _pr_review(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    projects = sorted({str(row.get("project_id", "")) for row in rows if row.get("project_id")})
    summary = [
        "{}: {} via {}".format(
            str(row.get("project_id", "")),
            str(row.get("field", "")),
            str(row.get("mutation_intent", "")),
        )
        for row in rows
    ]
    return {
        "title": "Bind governed evidence for {}".format(
            ", ".join(projects) if projects else "selected projects"
        ),
        "summary_lines": summary,
        "authorization_required": True,
        "merge_automatically": False,
    }


def build_binding_review_bundle(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
    patch_plan: Mapping[str, Any],
) -> Dict[str, Any]:
    """Bind selected proposals and an exact patch plan into a review-only bundle."""

    reasons = _patch_plan_contract_reasons(patch_plan)
    if reasons:
        return _blocked(reasons, status="upstream-error")
    selected = [str(value) for value in patch_plan["selected_proposal_fingerprints"]]
    recomputed = build_binding_patch_plan(root, proposal, selected)
    if recomputed.get("status") != "needs-governed-pr":
        return _blocked(["patch-plan-recompute-not-ready"], status="upstream-error")
    patch_plan_fingerprint = _fingerprint(dict(patch_plan))
    if _fingerprint(recomputed) != patch_plan_fingerprint:
        return _blocked(["patch-plan-recompute-mismatch"], status="upstream-error")
    selected_rows, reasons = _selected_proposal_rows(proposal, selected)
    reasons.extend(_coverage_reasons(patch_plan, selected_rows, selected))
    if reasons:
        return _blocked(reasons, status="upstream-error")
    review_rows = _review_rows(selected_rows)
    review_size = len(
        json.dumps(review_rows, ensure_ascii=False, sort_keys=True).encode("utf-8")
    )
    if review_size > MAX_REVIEW_BYTES:
        return _blocked(["review-bundle-byte-budget-exceeded"])
    material = {
        "patch_plan_fingerprint": patch_plan_fingerprint,
        "registry_before_sha256": str(patch_plan["registry_before_sha256"]),
        "registry_after_sha256": str(patch_plan["registry_after_sha256"]),
        "selected_proposal_fingerprints": selected,
        "rows": review_rows,
    }
    return {
        "schema_version": 1,
        "projection": REVIEW_BUNDLE_PROJECTION,
        "status": "needs-governed-authorization",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "apply_enabled": False,
        "selection_is_authorization": False,
        "authorization_state": "not-provided",
        "requires_governed_authorization": True,
        "requires_governed_pr": True,
        "review_bundle_only": True,
        "status_mutation_planned": False,
        "owner_mutation_planned": False,
        "readiness_mutation_planned": False,
        "selected_proposal_count": len(selected),
        "review_row_count": len(review_rows),
        "registry_before_sha256": str(patch_plan["registry_before_sha256"]),
        "registry_after_sha256": str(patch_plan["registry_after_sha256"]),
        "selected_proposal_fingerprints": selected,
        "patch_plan_fingerprint": patch_plan_fingerprint,
        "review_bundle_fingerprint": _fingerprint(material),
        "rows": review_rows,
        "pr_review": _pr_review(review_rows),
        "reason_codes": ["governed-authorization-required"],
    }
