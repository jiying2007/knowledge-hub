"""Route unique provider evidence proposals to machine or human boundaries.

This module does not apply canonical changes. It partitions already-qualified,
unambiguous proposal rows so append-only, provider-verifiable references can be
handled by a later machine-ratchet execution plane while semantic/single-value
changes continue through the governed human authorization path.
"""

from __future__ import annotations

import json
import pathlib
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

from .common import KnowledgeHubError
from .operator_binding_patch_plan import build_binding_patch_plan
from .operator_binding_review_bundle import build_binding_review_bundle

PROJECTION = "knowledge-operator-auto-route-v1"
MACHINE_RATCHET_FIELDS = {
    "source_refs",
    "validation_refs",
    "artifact_refs",
}
POLICY_PATH = "registry/ai-operations-policy.json"





def _machine_policy(root: pathlib.Path) -> Tuple[Set[str], str]:
    path = root / POLICY_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("AI operations policy is unavailable or invalid") from exc
    if not isinstance(payload, Mapping):
        raise KnowledgeHubError("AI operations policy must be an object")
    boundary = payload.get("evidence_binding", {})
    if not isinstance(boundary, Mapping):
        raise KnowledgeHubError("AI evidence binding policy must be an object")
    fields = boundary.get("machine_ratchet_fields", [])
    if not isinstance(fields, list):
        raise KnowledgeHubError("machine ratchet fields must be a list")
    selected = {str(value) for value in fields if str(value)}
    if selected != MACHINE_RATCHET_FIELDS:
        raise KnowledgeHubError("machine ratchet field policy does not match the supported surface")
    if boundary.get("human_authorization_fields") != ["release_ref"]:
        raise KnowledgeHubError("release_ref must remain a human authorization field")
    intent = str(boundary.get("machine_ratchet_mutation_intent", ""))
    if intent != "append-reference":
        raise KnowledgeHubError("machine ratchet mutation intent must be append-reference")
    for key in (
        "machine_ratchet_may_change_owner",
        "machine_ratchet_may_change_status",
        "machine_ratchet_may_change_readiness",
        "machine_ratchet_may_auto_promote_evidence_ready",
    ):
        if boundary.get(key) is not False:
            raise KnowledgeHubError("{} must remain false".format(key))
    return selected, intent


def _target_key(row: Mapping[str, Any]) -> Tuple[str, str]:
    target = row.get("target", {})
    if not isinstance(target, Mapping):
        return "", ""
    return str(target.get("item_id", "")), str(row.get("field", ""))


def _proposal_reasons(proposal: Mapping[str, Any]) -> List[str]:
    expected = {
        "projection": "knowledge-operator-binding-proposal-v1",
        "read_only": True,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "proposal_only": True,
    }
    reasons = [
        "proposal-{}-invalid".format(key.replace("_", "-"))
        for key, value in expected.items()
        if proposal.get(key) != value
    ]
    if int(proposal.get("blocked_conflict_count", 0) or 0) != 0:
        reasons.append("proposal-conflicts-present")
    if int(proposal.get("unmappable_count", 0) or 0) != 0:
        reasons.append("proposal-unmappable-present")
    if not isinstance(proposal.get("rows", []), list):
        reasons.append("proposal-rows-invalid")
    return list(dict.fromkeys(reasons))


def _unique_rows(
    proposal: Mapping[str, Any],
) -> Tuple[List[Mapping[str, Any]], List[Dict[str, Any]]]:
    raw_rows = proposal.get("rows", [])
    rows = raw_rows if isinstance(raw_rows, list) else []
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

    selected: List[Mapping[str, Any]] = []
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
        selected.append(candidates[0])
    return selected, ambiguous


def _machine_eligible(
    row: Mapping[str, Any],
    machine_fields: Set[str],
    mutation_intent: str,
) -> bool:
    field = str(row.get("field", ""))
    if field not in machine_fields:
        return False
    if row.get("mutation_intent") != mutation_intent:
        return False
    if str(row.get("provider", "")) != "github":
        return False
    if any(
        row.get(name) is not False
        for name in (
            "status_mutation_planned",
            "owner_mutation_planned",
            "readiness_mutation_planned",
        )
    ):
        return False
    target = row.get("target", {})
    if not isinstance(target, Mapping):
        return False
    if str(target.get("registry_path", "")) != "registry/items.jsonl":
        return False
    if not str(target.get("item_id", "")):
        return False
    if not isinstance(row.get("current_value"), list):
        return False
    proposed = row.get("proposed_reference", {})
    if not isinstance(proposed, Mapping):
        return False
    if not str(proposed.get("kind", "")) or not str(proposed.get("ref", "")):
        return False
    snapshot = row.get("candidate_snapshot", {})
    if not isinstance(snapshot, Mapping):
        return False
    return all(
        (
            snapshot.get("provider") == "github",
            snapshot.get("provider_verified") is True,
            snapshot.get("candidate_only") is True,
            snapshot.get("eligible_for_binding") is False,
            snapshot.get("provenance") == "github-read-only-api",
            str(snapshot.get("kind", "")) == str(proposed.get("kind", "")),
            str(snapshot.get("ref", "")) == str(proposed.get("ref", "")),
        )
    )


def _fingerprints(rows: Sequence[Mapping[str, Any]]) -> List[str]:
    return sorted(
        {
            str(row.get("proposal_fingerprint", ""))
            for row in rows
            if str(row.get("proposal_fingerprint", ""))
        }
    )


def _machine_route(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    selected = _fingerprints(rows)
    if not selected:
        return {"status": "no-change", "selected_proposal_count": 0}
    plan = build_binding_patch_plan(root, proposal, selected)
    reasons: List[str] = []
    if plan.get("status") != "needs-governed-pr":
        reasons.append("machine-patch-plan-not-ready")
    if int(plan.get("planned_write_count", 0) or 0) != 1:
        reasons.append("machine-patch-plan-write-count-invalid")
    for field in (
        "status_mutation_planned",
        "owner_mutation_planned",
        "readiness_mutation_planned",
    ):
        if plan.get(field) is not False:
            reasons.append("machine-{}-invalid".format(field.replace("_", "-")))
    return {
        "status": "blocked" if reasons else "ready-for-machine-ratchet",
        "authorization_class": "autonomous-low-risk-ratchet",
        "canonical_write_performed": False,
        "automatic_execution_enabled": False,
        "selected_proposal_count": len(selected),
        "selected_proposal_fingerprints": selected,
        "allowed_fields": sorted(MACHINE_RATCHET_FIELDS),
        "patch_plan": plan,
        "reason_codes": reasons,
    }


def _human_route(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    selected = _fingerprints(rows)
    if not selected:
        return {"status": "no-change", "selected_proposal_count": 0}
    plan = build_binding_patch_plan(root, proposal, selected)
    if plan.get("status") != "needs-governed-pr":
        return {
            "status": "blocked",
            "selected_proposal_count": len(selected),
            "selected_proposal_fingerprints": selected,
            "patch_plan": plan,
            "reason_codes": ["human-patch-plan-not-ready"],
        }
    bundle = build_binding_review_bundle(root, proposal, plan)
    ready = bundle.get("status") == "needs-governed-authorization"
    return {
        "status": "needs-governed-authorization" if ready else "blocked",
        "authorization_class": "human-authorization",
        "canonical_write_performed": False,
        "automatic_execution_enabled": False,
        "selected_proposal_count": len(selected),
        "selected_proposal_fingerprints": selected,
        "patch_plan": plan,
        "review_bundle": bundle,
        "reason_codes": [] if ready else ["human-review-bundle-not-ready"],
    }


def build_unique_execution_routes(
    root: pathlib.Path, proposal: Mapping[str, Any]
) -> Dict[str, Any]:
    """Partition unique proposals without authorizing or applying any mutation."""

    reasons = _proposal_reasons(proposal)
    if reasons:
        return {
            "schema_version": 1,
            "projection": PROJECTION,
            "status": "blocked",
            "read_only": True,
            "selection_is_authorization": False,
            "canonical_write_performed": False,
            "automatic_binding_enabled": False,
            "automatic_execution_enabled": False,
            "selected_proposal_count": 0,
            "machine_ratchet_count": 0,
            "human_authorization_count": 0,
            "ambiguous_target_count": 0,
            "machine_route": {},
            "human_route": {},
            "reason_codes": reasons,
        }

    selected, ambiguous = _unique_rows(proposal)
    if ambiguous:
        return {
            "schema_version": 1,
            "projection": PROJECTION,
            "status": "ambiguous",
            "read_only": True,
            "selection_is_authorization": False,
            "canonical_write_performed": False,
            "automatic_binding_enabled": False,
            "automatic_execution_enabled": False,
            "selected_proposal_count": 0,
            "machine_ratchet_count": 0,
            "human_authorization_count": 0,
            "ambiguous_target_count": len(ambiguous),
            "ambiguous_targets": ambiguous,
            "machine_route": {},
            "human_route": {},
            "reason_codes": ["ambiguous-proposal-target"],
        }

    try:
        machine_fields, mutation_intent = _machine_policy(root)
    except KnowledgeHubError as exc:
        return {
            "schema_version": 1,
            "projection": PROJECTION,
            "status": "blocked",
            "read_only": True,
            "selection_is_authorization": False,
            "canonical_write_performed": False,
            "automatic_binding_enabled": False,
            "automatic_execution_enabled": False,
            "selected_proposal_count": 0,
            "machine_ratchet_count": 0,
            "human_authorization_count": 0,
            "ambiguous_target_count": 0,
            "machine_route": {},
            "human_route": {},
            "reason_codes": ["machine-policy-invalid: {}".format(exc)],
        }
    machine_rows = [
        row
        for row in selected
        if _machine_eligible(row, machine_fields, mutation_intent)
    ]
    human_rows = [
        row
        for row in selected
        if not _machine_eligible(row, machine_fields, mutation_intent)
    ]
    machine = _machine_route(root, proposal, machine_rows)
    human = _human_route(root, proposal, human_rows)
    blocked = "blocked" in {machine.get("status"), human.get("status")}
    if blocked:
        status = "blocked"
    elif machine_rows and human_rows:
        status = "mixed-routing"
    elif machine_rows:
        status = "ready-for-machine-ratchet"
    elif human_rows:
        status = "needs-governed-authorization"
    else:
        status = "no-change"
    return {
        "schema_version": 1,
        "projection": PROJECTION,
        "status": status,
        "read_only": True,
        "selection_is_authorization": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "selected_proposal_count": len(selected),
        "machine_ratchet_count": len(machine_rows),
        "human_authorization_count": len(human_rows),
        "ambiguous_target_count": 0,
        "machine_route": machine,
        "human_route": human,
        "reason_codes": ["subroute-blocked"] if blocked else [],
    }
