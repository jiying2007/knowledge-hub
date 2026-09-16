"""Proposal-only governed evidence bindings for qualified Operator candidates."""

from __future__ import annotations

import hashlib
import json
import pathlib
from collections import Counter
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError, registry_items, route_rows
from .evidence import evaluate_evidence_contract

PROPOSAL_FIELDS = {"source_refs", "validation_refs", "artifact_refs", "release_ref"}
LIST_FIELDS = {"source_refs", "validation_refs", "artifact_refs"}
MAX_PROPOSAL_ROWS = 400


def _reason_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if str(row)]


def _qualification_contract_reasons(qualification: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    expected = {
        "projection": "knowledge-operator-candidate-qualification-v1",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "candidate_only": True,
        "eligible_for_binding": False,
        "requires_governed_review": True,
    }
    for key, expected_value in expected.items():
        if qualification.get(key) != expected_value:
            reasons.append("qualification-{}-invalid".format(key.replace("_", "-")))
    if qualification.get("truncated") is not False:
        reasons.append("qualification-truncated")
    if int(qualification.get("source_error_count", 0) or 0) != 0:
        reasons.append("qualification-source-errors-present")
    if _reason_list(qualification.get("upstream_contract_reason_codes", [])):
        reasons.append("qualification-upstream-contract-errors-present")

    rows = qualification.get("rows", [])
    if not isinstance(rows, list):
        reasons.append("qualification-rows-invalid")
        return reasons
    mapping_rows = [row for row in rows if isinstance(row, Mapping)]
    if len(mapping_rows) != len(rows):
        reasons.append("qualification-row-type-invalid")
    actual = Counter(str(row.get("qualification_status", "")) for row in mapping_rows)
    if int(qualification.get("candidate_count", -1) or 0) != len(mapping_rows):
        reasons.append("qualification-candidate-count-mismatch")
    if int(qualification.get("reviewable_count", -1) or 0) != actual.get("reviewable", 0):
        reasons.append("qualification-reviewable-count-mismatch")
    if int(qualification.get("rejected_count", -1) or 0) != actual.get("rejected", 0):
        reasons.append("qualification-rejected-count-mismatch")
    expected_status = (
        "needs-governed-review"
        if actual.get("reviewable", 0)
        else "no-reviewable-candidate"
    )
    if qualification.get("status") != expected_status:
        reasons.append("qualification-status-mismatch")
    return list(dict.fromkeys(reasons))


def _reviewable_row_reasons(row: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    if row.get("qualification_status") != "reviewable":
        reasons.append("qualification-row-not-reviewable")
    if row.get("review_eligible") is not True:
        reasons.append("qualification-row-review-eligibility-invalid")
    if row.get("requires_governed_review") is not True:
        reasons.append("qualification-row-governance-state-invalid")
    if row.get("candidate_only") is not True:
        reasons.append("qualification-row-candidate-only-state-invalid")
    if row.get("eligible_for_binding") is not False:
        reasons.append("qualification-row-binding-state-invalid")
    if _reason_list(row.get("reason_codes", [])) != ["review-floor-met"]:
        reasons.append("qualification-row-reason-code-invalid")
    field = str(row.get("field", ""))
    if field not in PROPOSAL_FIELDS:
        reasons.append("unsupported-evidence-field")
    candidate = row.get("candidate", {})
    if not isinstance(candidate, Mapping):
        reasons.append("qualification-candidate-invalid")
        return reasons
    for key in ("provider", "kind", "ref"):
        if str(row.get(key, "")) != str(candidate.get(key, "")):
            reasons.append("qualification-candidate-{}-mismatch".format(key))
    if candidate.get("provider_verified") is not True:
        reasons.append("qualification-candidate-provider-not-verified")
    if candidate.get("candidate_only") is not True:
        reasons.append("qualification-candidate-only-state-invalid")
    if candidate.get("eligible_for_binding") is not False:
        reasons.append("qualification-candidate-binding-state-invalid")
    details = candidate.get("details", {})
    if not isinstance(details, Mapping):
        reasons.append("qualification-candidate-details-invalid")
    try:
        json.dumps(dict(candidate), ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        reasons.append("qualification-candidate-not-json-serializable")
    return list(dict.fromkeys(reasons))


def _approved_not_applicable(contract: Mapping[str, Any], field: str) -> bool:
    rows = contract.get("not_applicable", {})
    if not isinstance(rows, Mapping):
        return False
    row = rows.get(field, {})
    return isinstance(row, Mapping) and all(
        str(row.get(key, "")).strip()
        for key in ("owner_ref", "authorization_id", "reason")
    )


def _reference(row: Mapping[str, Any]) -> Dict[str, str]:
    return {"kind": str(row.get("kind", "")), "ref": str(row.get("ref", ""))}


def _candidate_snapshot(row: Mapping[str, Any]) -> Dict[str, Any]:
    candidate = row.get("candidate", {})
    if not isinstance(candidate, Mapping):
        return {}
    # Deep-copy through JSON to keep the proposal deterministic and detached
    # from the live qualification payload while preserving verified metadata.
    return json.loads(
        json.dumps(
            dict(candidate),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _same_reference(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return str(left.get("kind", "")) == str(right.get("kind", "")) and str(
        left.get("ref", "")
    ) == str(right.get("ref", ""))


def _valid_reference(value: Any) -> bool:
    return isinstance(value, Mapping) and bool(
        str(value.get("kind", "")).strip() and str(value.get("ref", "")).strip()
    )


def _fingerprint(value: Mapping[str, Any]) -> str:
    raw = json.dumps(
        dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:{}".format(hashlib.sha256(raw).hexdigest())


def _target_inventory(
    root: pathlib.Path,
) -> Tuple[Dict[str, List[Mapping[str, Any]]], Dict[str, List[Mapping[str, Any]]]]:
    routes: Dict[str, List[Mapping[str, Any]]] = {}
    for row in route_rows(root):
        project_id = str(row.get("project_id", ""))
        if project_id:
            routes.setdefault(project_id, []).append(row)
    items: Dict[str, List[Mapping[str, Any]]] = {}
    for row in registry_items(root):
        project_id = str(row.get("project_id", ""))
        if project_id:
            items.setdefault(project_id, []).append(row)
    return routes, items


def _canonical_target(
    *,
    project_id: str,
    field: str,
    routes: Mapping[str, Sequence[Mapping[str, Any]]],
    items: Mapping[str, Sequence[Mapping[str, Any]]],
) -> Tuple[Dict[str, Any], Mapping[str, Any], List[str]]:
    reasons: List[str] = []
    project_routes = list(routes.get(project_id, []))
    if len(project_routes) != 1:
        return {}, {}, ["canonical-route-not-unique"]
    validation_path = str(project_routes[0].get("validation_path", "")).rstrip("/")
    if not validation_path:
        return {}, {}, ["canonical-validation-path-missing"]
    expected_path = validation_path + "/project-readiness.md"
    candidates = [
        row
        for row in items.get(project_id, [])
        if str(row.get("path", "")) == expected_path
        and str(row.get("readiness_slot", "")) == "validation"
    ]
    if len(candidates) != 1:
        return {}, {}, ["canonical-validation-item-not-unique"]
    item = candidates[0]
    item_id = str(item.get("id", ""))
    if not item_id:
        reasons.append("canonical-validation-item-id-missing")
    contract = item.get("evidence_contract", {})
    if not isinstance(contract, Mapping):
        reasons.append("canonical-evidence-contract-invalid")
        contract = {}
    evaluation = evaluate_evidence_contract(contract)
    required_fields = {str(value) for value in evaluation.get("required_fields", [])}
    if field not in required_fields:
        reasons.append("field-not-required-by-evidence-profile")
    if field in {str(value) for value in evaluation.get("invalid_fields", [])}:
        reasons.append("canonical-evidence-field-invalid")
    target = {
        "registry_path": "registry/items.jsonl",
        "item_id": item_id,
        "project_id": project_id,
        "readiness_slot": "validation",
        "item_path": expected_path,
        "contract_field": field,
        "evidence_profile": str(contract.get("profile", "")),
    }
    return target, contract, reasons


def _proposal_value(
    contract: Mapping[str, Any], field: str, proposed: Mapping[str, Any]
) -> Tuple[str, Any, str, List[str]]:
    if _approved_not_applicable(contract, field):
        return "blocked-conflict", contract.get(field), "none", [
            "approved-not-applicable-conflict"
        ]
    current = contract.get(field)
    if field in LIST_FIELDS:
        if not isinstance(current, list):
            return "blocked-conflict", current, "none", [
                "canonical-list-field-shape-invalid"
            ]
        if any(not _valid_reference(value) for value in current):
            return "blocked-conflict", current, "none", [
                "canonical-existing-reference-invalid"
            ]
        if any(
            _same_reference(value, proposed)
            for value in current
            if isinstance(value, Mapping)
        ):
            return "already-present", current, "none", ["reference-already-present"]
        next_value = [dict(value) for value in current if isinstance(value, Mapping)]
        next_value.append(dict(proposed))
        return "ready-for-governed-review", next_value, "append-reference", [
            "governed-review-required"
        ]
    if field == "release_ref":
        if current is None:
            return "ready-for-governed-review", dict(proposed), "set-if-empty", [
                "governed-review-required"
            ]
        if not _valid_reference(current):
            return "blocked-conflict", current, "none", [
                "canonical-single-field-shape-invalid"
            ]
        if isinstance(current, Mapping) and _same_reference(current, proposed):
            return "already-present", current, "none", ["reference-already-present"]
        return "blocked-conflict", current, "none", [
            "canonical-single-value-conflict"
        ]
    return "unmappable", current, "none", ["unsupported-evidence-field"]


def _proposal_row(
    *,
    row: Mapping[str, Any],
    routes: Mapping[str, Sequence[Mapping[str, Any]]],
    items: Mapping[str, Sequence[Mapping[str, Any]]],
) -> Dict[str, Any]:
    project_id = str(row.get("project_id", ""))
    field = str(row.get("field", ""))
    proposed = _reference(row)
    row_reasons = _reviewable_row_reasons(row)
    snapshot = _candidate_snapshot(row) if not row_reasons else {}
    target: Dict[str, Any] = {}
    contract: Mapping[str, Any] = {}
    target_reasons: List[str] = []
    if not row_reasons:
        target, contract, target_reasons = _canonical_target(
            project_id=project_id,
            field=field,
            routes=routes,
            items=items,
        )
    reasons = row_reasons + target_reasons
    if reasons:
        status = "unmappable"
        proposed_value: Any = None
        intent = "none"
    else:
        status, proposed_value, intent, value_reasons = _proposal_value(
            contract, field, proposed
        )
        reasons.extend(value_reasons)
    current_value = contract.get(field) if contract else None
    fingerprint_material = {
        "project_id": project_id,
        "field": field,
        "target": target,
        "current_value": current_value,
        "proposed_reference": proposed,
        "proposed_value": proposed_value,
        "mutation_intent": intent,
        "candidate_snapshot": snapshot,
    }
    return {
        "project_id": project_id,
        "field": field,
        "provider": str(row.get("provider", "")),
        "operation": str(row.get("operation", "")),
        "source_target": str(row.get("target", "")),
        "kind": str(row.get("kind", "")),
        "ref": str(row.get("ref", "")),
        "proposal_status": status,
        "proposal_ready_for_review": status == "ready-for-governed-review",
        "requires_governed_review": True,
        "proposal_only": True,
        "candidate_only": True,
        "eligible_for_binding": False,
        "canonical_write_performed": False,
        "target": target,
        "current_value": current_value,
        "proposed_reference": proposed,
        "proposed_value": proposed_value,
        "mutation_intent": intent,
        "candidate_snapshot": snapshot,
        "candidate_snapshot_fingerprint": _fingerprint(snapshot) if snapshot else "",
        "status_mutation_planned": False,
        "owner_mutation_planned": False,
        "readiness_mutation_planned": False,
        "reason_codes": list(dict.fromkeys(reasons)),
        "proposal_fingerprint": _fingerprint(fingerprint_material),
    }


def _unavailable(reasons: Sequence[str]) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": "knowledge-operator-binding-proposal-v1",
        "status": "upstream-error",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "proposal_only": True,
        "eligible_for_binding": False,
        "requires_governed_review": True,
        "candidate_count": 0,
        "proposal_count": 0,
        "already_present_count": 0,
        "blocked_conflict_count": 0,
        "unmappable_count": 0,
        "rows": [],
        "upstream_contract_reason_codes": list(dict.fromkeys(reasons)),
    }


def build_binding_proposal(
    root: pathlib.Path, qualification: Mapping[str, Any]
) -> Dict[str, Any]:
    """Build deterministic governed-review proposals without mutating evidence."""

    upstream_reasons = _qualification_contract_reasons(qualification)
    if upstream_reasons:
        return _unavailable(upstream_reasons)
    try:
        routes, items = _target_inventory(root)
    except KnowledgeHubError as exc:
        return _unavailable(["canonical-target-inventory-unavailable: {}".format(exc)])
    rows: List[Dict[str, Any]] = []
    reviewable_rows = [
        row
        for row in qualification.get("rows", [])
        if isinstance(row, Mapping) and row.get("qualification_status") == "reviewable"
    ]
    if len(reviewable_rows) > MAX_PROPOSAL_ROWS:
        return _unavailable(["proposal-row-budget-exceeded"])
    for row in reviewable_rows:
        rows.append(_proposal_row(row=row, routes=routes, items=items))
    counts = Counter(str(row.get("proposal_status", "")) for row in rows)
    proposal_count = counts.get("ready-for-governed-review", 0)
    blocked_count = counts.get("blocked-conflict", 0)
    unmappable_count = counts.get("unmappable", 0)
    if blocked_count or unmappable_count:
        status = "blocked"
    elif proposal_count:
        status = "needs-governed-review"
    else:
        status = "no-change"
    return {
        "schema_version": 1,
        "projection": "knowledge-operator-binding-proposal-v1",
        "status": status,
        "read_only": True,
        "network_performed": False,
        "source_projection_network_performed": bool(
            qualification.get("source_projection_network_performed", False)
        ),
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "proposal_only": True,
        "candidate_only": True,
        "eligible_for_binding": False,
        "requires_governed_review": True,
        "status_mutation_planned": False,
        "owner_mutation_planned": False,
        "readiness_mutation_planned": False,
        "candidate_count": len(reviewable_rows),
        "proposal_count": proposal_count,
        "already_present_count": counts.get("already-present", 0),
        "blocked_conflict_count": blocked_count,
        "unmappable_count": unmappable_count,
        "rows": rows,
        "upstream_contract_reason_codes": [],
    }
