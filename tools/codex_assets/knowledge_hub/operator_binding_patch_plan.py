"""Governed patch planning for explicitly selected Operator binding proposals."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from collections import Counter
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import encode_jsonl, file_sha256, registry_items
from .evidence import evaluate_evidence_contract
from .store import RepositoryTransaction

PROPOSAL_PROJECTION = "knowledge-operator-binding-proposal-v1"
PATCH_PLAN_PROJECTION = "knowledge-operator-binding-patch-plan-v1"
MAX_SELECTED_PROPOSALS = 50
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
LIST_FIELDS = {"source_refs", "validation_refs", "artifact_refs"}
SINGLE_FIELDS = {"release_ref"}
ALLOWED_FIELDS = LIST_FIELDS | SINGLE_FIELDS
ALLOWED_INTENTS = {"append-reference", "set-if-empty"}


def _json_fingerprint(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:{}".format(hashlib.sha256(raw).hexdigest())


def _same_reference(left: Any, right: Any) -> bool:
    return bool(
        isinstance(left, Mapping)
        and isinstance(right, Mapping)
        and str(left.get("kind", "")) == str(right.get("kind", ""))
        and str(left.get("ref", "")) == str(right.get("ref", ""))
    )


def _valid_reference(value: Any) -> bool:
    return bool(
        isinstance(value, Mapping)
        and str(value.get("kind", "")).strip()
        and str(value.get("ref", "")).strip()
    )


def _proposal_fingerprint_material(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "project_id": str(row.get("project_id", "")),
        "field": str(row.get("field", "")),
        "target": row.get("target", {}),
        "current_value": row.get("current_value"),
        "proposed_reference": row.get("proposed_reference", {}),
        "proposed_value": row.get("proposed_value"),
        "mutation_intent": str(row.get("mutation_intent", "")),
        "candidate_snapshot": row.get("candidate_snapshot", {}),
    }


def _proposal_contract_reasons(proposal: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    expected = {
        "projection": PROPOSAL_PROJECTION,
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "proposal_only": True,
        "eligible_for_binding": False,
        "requires_governed_review": True,
    }
    for key, expected_value in expected.items():
        if proposal.get(key) != expected_value:
            reasons.append("proposal-{}-invalid".format(key.replace("_", "-")))
    rows = proposal.get("rows", [])
    if not isinstance(rows, list):
        reasons.append("proposal-rows-invalid")
        return reasons
    mapping_rows = [row for row in rows if isinstance(row, Mapping)]
    if len(mapping_rows) != len(rows):
        reasons.append("proposal-row-type-invalid")
    counts = Counter(str(row.get("proposal_status", "")) for row in mapping_rows)
    expected_counts = {
        "candidate_count": len(mapping_rows),
        "proposal_count": counts.get("ready-for-governed-review", 0),
        "already_present_count": counts.get("already-present", 0),
        "blocked_conflict_count": counts.get("blocked-conflict", 0),
        "unmappable_count": counts.get("unmappable", 0),
    }
    for key, expected_value in expected_counts.items():
        if int(proposal.get(key, -1) or 0) != expected_value:
            reasons.append("proposal-{}-mismatch".format(key.replace("_", "-")))
    if proposal.get("status") not in {
        "needs-governed-review",
        "no-change",
        "blocked",
    }:
        reasons.append("proposal-status-invalid")
    return list(dict.fromkeys(reasons))


def _selected_row_reasons(row: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    fingerprint = str(row.get("proposal_fingerprint", ""))
    if not FINGERPRINT_RE.fullmatch(fingerprint):
        reasons.append("proposal-fingerprint-invalid")
    elif _json_fingerprint(_proposal_fingerprint_material(row)) != fingerprint:
        reasons.append("proposal-fingerprint-mismatch")
    snapshot = row.get("candidate_snapshot", {})
    snapshot_fingerprint = str(row.get("candidate_snapshot_fingerprint", ""))
    if not isinstance(snapshot, Mapping) or not snapshot:
        reasons.append("candidate-snapshot-missing")
    elif _json_fingerprint(dict(snapshot)) != snapshot_fingerprint:
        reasons.append("candidate-snapshot-fingerprint-mismatch")
    if row.get("proposal_status") != "ready-for-governed-review":
        reasons.append("proposal-not-ready-for-governed-review")
    if row.get("proposal_ready_for_review") is not True:
        reasons.append("proposal-review-state-invalid")
    if row.get("requires_governed_review") is not True:
        reasons.append("proposal-governance-state-invalid")
    if row.get("proposal_only") is not True:
        reasons.append("proposal-only-state-invalid")
    if row.get("candidate_only") is not True:
        reasons.append("proposal-candidate-only-state-invalid")
    if row.get("eligible_for_binding") is not False:
        reasons.append("proposal-binding-state-invalid")
    if row.get("canonical_write_performed") is not False:
        reasons.append("proposal-canonical-write-state-invalid")
    if row.get("status_mutation_planned") is not False:
        reasons.append("proposal-status-mutation-invalid")
    if row.get("owner_mutation_planned") is not False:
        reasons.append("proposal-owner-mutation-invalid")
    if row.get("readiness_mutation_planned") is not False:
        reasons.append("proposal-readiness-mutation-invalid")
    field = str(row.get("field", ""))
    if field not in ALLOWED_FIELDS:
        reasons.append("proposal-field-unsupported")
    intent = str(row.get("mutation_intent", ""))
    if intent not in ALLOWED_INTENTS:
        reasons.append("proposal-mutation-intent-unsupported")
    if field in LIST_FIELDS and intent != "append-reference":
        reasons.append("proposal-list-intent-mismatch")
    if field in SINGLE_FIELDS and intent != "set-if-empty":
        reasons.append("proposal-single-intent-mismatch")
    if not _valid_reference(row.get("proposed_reference")):
        reasons.append("proposal-reference-invalid")
    target = row.get("target", {})
    if not isinstance(target, Mapping):
        reasons.append("proposal-target-invalid")
    elif str(target.get("registry_path", "")) != "registry/items.jsonl":
        reasons.append("proposal-registry-target-invalid")
    return list(dict.fromkeys(reasons))


def _blocked(
    reasons: Sequence[str],
    selected: Sequence[str],
    *,
    status: str = "blocked",
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": PATCH_PLAN_PROJECTION,
        "status": status,
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
        "selected_proposal_fingerprints": list(selected),
        "selected_proposal_count": len(selected),
        "planned_item_count": 0,
        "planned_write_count": 0,
        "rows": [],
        "transaction_plan": {},
        "reason_codes": list(dict.fromkeys(str(reason) for reason in reasons if str(reason))),
    }


def _selection_rows(
    proposal: Mapping[str, Any], selected: Sequence[str]
) -> Tuple[List[Mapping[str, Any]], List[str]]:
    reasons: List[str] = []
    rows = [row for row in proposal.get("rows", []) if isinstance(row, Mapping)]
    by_fingerprint: Dict[str, List[Mapping[str, Any]]] = {}
    for row in rows:
        fingerprint = str(row.get("proposal_fingerprint", ""))
        if fingerprint:
            by_fingerprint.setdefault(fingerprint, []).append(row)
    result: List[Mapping[str, Any]] = []
    for fingerprint in selected:
        matches = by_fingerprint.get(fingerprint, [])
        if not matches:
            reasons.append("selected-proposal-not-found:{}".format(fingerprint))
            continue
        if len(matches) != 1:
            reasons.append("selected-proposal-not-unique:{}".format(fingerprint))
            continue
        row = matches[0]
        row_reasons = _selected_row_reasons(row)
        reasons.extend(
            "{}:{}".format(fingerprint, reason) for reason in row_reasons
        )
        result.append(row)
    return result, reasons


def _target_key(row: Mapping[str, Any]) -> Tuple[str, str]:
    target = row.get("target", {})
    if not isinstance(target, Mapping):
        return "", ""
    return str(target.get("item_id", "")), str(row.get("field", ""))


def _selection_conflict_reasons(rows: Sequence[Mapping[str, Any]]) -> List[str]:
    reasons: List[str] = []
    grouped: Dict[Tuple[str, str], List[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(_target_key(row), []).append(row)
    for (item_id, field), group in grouped.items():
        if not item_id or not field:
            reasons.append("selected-target-key-invalid")
            continue
        if field in SINGLE_FIELDS and len(group) > 1:
            refs = {
                _json_fingerprint(row.get("proposed_reference", {}))
                for row in group
            }
            if len(refs) > 1:
                reasons.append(
                    "multiple-single-value-proposals:{}:{}".format(item_id, field)
                )
        canonical_refs: Dict[str, str] = {}
        for row in group:
            reference_key = _json_fingerprint(row.get("proposed_reference", {}))
            fingerprint = str(row.get("proposal_fingerprint", ""))
            previous = canonical_refs.get(reference_key)
            if previous and previous != fingerprint:
                reasons.append(
                    "duplicate-canonical-reference-selection:{}:{}".format(
                        item_id, field
                    )
                )
            canonical_refs[reference_key] = fingerprint
    return list(dict.fromkeys(reasons))


def _find_item_index(
    items: Sequence[Mapping[str, Any]], row: Mapping[str, Any]
) -> Tuple[int, List[str]]:
    target = row.get("target", {})
    if not isinstance(target, Mapping):
        return -1, ["proposal-target-invalid"]
    matches: List[int] = []
    for index, item in enumerate(items):
        if (
            str(item.get("id", "")) == str(target.get("item_id", ""))
            and str(item.get("project_id", "")) == str(target.get("project_id", ""))
            and str(item.get("readiness_slot", "")) == "validation"
            and str(item.get("path", "")) == str(target.get("item_path", ""))
        ):
            matches.append(index)
    if len(matches) != 1:
        return -1, ["canonical-target-item-not-unique"]
    return matches[0], []


def _apply_selected_reference(
    item: Dict[str, Any], row: Mapping[str, Any]
) -> List[str]:
    reasons: List[str] = []
    contract = item.get("evidence_contract", {})
    if not isinstance(contract, Mapping):
        return ["canonical-evidence-contract-invalid"]
    mutable_contract = dict(contract)
    if str(mutable_contract.get("status", "")) != "pending":
        return ["canonical-evidence-contract-not-pending"]
    target = row.get("target", {})
    if not isinstance(target, Mapping):
        return ["proposal-target-invalid"]
    if str(mutable_contract.get("profile", "")) != str(
        target.get("evidence_profile", "")
    ):
        return ["canonical-evidence-profile-drift"]
    field = str(row.get("field", ""))
    current = mutable_contract.get(field)
    if current != row.get("current_value"):
        return ["canonical-field-stale"]
    proposed = row.get("proposed_reference", {})
    if field in LIST_FIELDS:
        if not isinstance(current, list):
            return ["canonical-list-field-shape-invalid"]
        if any(not _valid_reference(value) for value in current):
            return ["canonical-existing-reference-invalid"]
        if any(_same_reference(value, proposed) for value in current):
            return ["canonical-reference-already-present"]
        next_value = [dict(value) for value in current if isinstance(value, Mapping)]
        next_value.append(dict(proposed))
        mutable_contract[field] = next_value
    elif field in SINGLE_FIELDS:
        if current is not None:
            return ["canonical-single-value-no-longer-empty"]
        mutable_contract[field] = dict(proposed)
    else:
        return ["proposal-field-unsupported"]
    after_eval = evaluate_evidence_contract(mutable_contract)
    if after_eval.get("declared_status") != "pending":
        reasons.append("post-plan-declared-status-drift")
    if after_eval.get("status") == "ready":
        reasons.append("patch-plan-would-auto-promote-readiness")
    if reasons:
        return reasons
    item["evidence_contract"] = mutable_contract
    return []


def build_binding_patch_plan(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
    selected_fingerprints: Sequence[str],
) -> Dict[str, Any]:
    """Plan exact canonical row changes for selected proposals without applying them."""

    proposal_reasons = _proposal_contract_reasons(proposal)
    if proposal_reasons:
        return _blocked(proposal_reasons, [], status="upstream-error")

    selected = sorted(
        {
            str(value).strip()
            for value in selected_fingerprints
            if str(value).strip()
        }
    )
    if not selected:
        return _blocked(["proposal-selection-required"], selected)
    if len(selected) > MAX_SELECTED_PROPOSALS:
        return _blocked(["selected-proposal-budget-exceeded"], selected)
    malformed = [value for value in selected if not FINGERPRINT_RE.fullmatch(value)]
    if malformed:
        return _blocked(
            ["selected-proposal-fingerprint-invalid:{}".format(value) for value in malformed],
            selected,
        )

    selected_rows, selection_reasons = _selection_rows(proposal, selected)
    selection_reasons.extend(_selection_conflict_reasons(selected_rows))
    if selection_reasons:
        return _blocked(selection_reasons, selected)

    original_items = registry_items(root)
    working_items = [json.loads(json.dumps(dict(item), ensure_ascii=False)) for item in original_items]
    item_changes: Dict[str, Dict[str, Any]] = {}

    for row in selected_rows:
        index, target_reasons = _find_item_index(working_items, row)
        if target_reasons:
            return _blocked(target_reasons, selected)
        before_item = json.loads(json.dumps(working_items[index], ensure_ascii=False))
        apply_reasons = _apply_selected_reference(working_items[index], row)
        if apply_reasons:
            return _blocked(
                [
                    "{}:{}".format(str(row.get("proposal_fingerprint", "")), reason)
                    for reason in apply_reasons
                ],
                selected,
            )
        after_item = working_items[index]
        item_id = str(after_item.get("id", ""))
        change = item_changes.setdefault(
            item_id,
            {
                "item_id": item_id,
                "project_id": str(after_item.get("project_id", "")),
                "item_path": str(after_item.get("path", "")),
                "registry_path": "registry/items.jsonl",
                "before_row_fingerprint": _json_fingerprint(before_item),
                "after_row_fingerprint": "",
                "changed_fields": [],
                "selected_proposal_fingerprints": [],
            },
        )
        field = str(row.get("field", ""))
        if field not in change["changed_fields"]:
            change["changed_fields"].append(field)
        change["selected_proposal_fingerprints"].append(
            str(row.get("proposal_fingerprint", ""))
        )
        change["after_row_fingerprint"] = _json_fingerprint(after_item)

    registry_path = root / "registry" / "items.jsonl"
    before_sha256 = file_sha256(registry_path)
    rendered = encode_jsonl(working_items)
    transaction = RepositoryTransaction(
        root, transaction_id="kh-operator-binding-patch-plan"
    )
    transaction.add_text(
        "registry/items.jsonl",
        rendered,
        expected_sha256=before_sha256,
    )
    transaction_plan = transaction.plan()
    if transaction_plan.get("changed_count") != 1:
        return _blocked(["registry-patch-plan-change-count-invalid"], selected)

    rows = []
    for item_id in sorted(item_changes):
        change = dict(item_changes[item_id])
        change["changed_fields"] = sorted(change["changed_fields"])
        change["selected_proposal_fingerprints"] = sorted(
            change["selected_proposal_fingerprints"]
        )
        rows.append(change)

    after_sha256 = ""
    writes = transaction_plan.get("writes", [])
    if isinstance(writes, list) and len(writes) == 1 and isinstance(writes[0], Mapping):
        after_sha256 = str(writes[0].get("after_sha256", ""))
    return {
        "schema_version": 1,
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
        "selected_proposal_fingerprints": selected,
        "selected_proposal_count": len(selected),
        "planned_item_count": len(rows),
        "planned_write_count": 1,
        "registry_path": "registry/items.jsonl",
        "registry_before_sha256": before_sha256,
        "registry_after_sha256": after_sha256,
        "rows": rows,
        "transaction_plan": transaction_plan,
        "reason_codes": ["governed-pr-required"],
    }
