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


def _fingerprint(value: Any) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:{}".format(hashlib.sha256(raw).hexdigest())


def _valid_reference(value: Any) -> bool:
    return bool(
        isinstance(value, Mapping)
        and str(value.get("kind", "")).strip()
        and str(value.get("ref", "")).strip()
    )


def _same_reference(left: Any, right: Any) -> bool:
    return bool(
        isinstance(left, Mapping)
        and isinstance(right, Mapping)
        and str(left.get("kind", "")) == str(right.get("kind", ""))
        and str(left.get("ref", "")) == str(right.get("ref", ""))
    )


def _proposal_material(row: Mapping[str, Any]) -> Dict[str, Any]:
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


def _proposal_reasons(proposal: Mapping[str, Any]) -> List[str]:
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
        return reasons + ["proposal-rows-invalid"]
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
    for key, value in expected_counts.items():
        if int(proposal.get(key, -1) or 0) != value:
            reasons.append("proposal-{}-mismatch".format(key.replace("_", "-")))
    if proposal.get("status") not in {
        "needs-governed-review",
        "no-change",
        "blocked",
    }:
        reasons.append("proposal-status-invalid")
    return list(dict.fromkeys(reasons))


def _row_reasons(row: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    fingerprint = str(row.get("proposal_fingerprint", ""))
    if not FINGERPRINT_RE.fullmatch(fingerprint):
        reasons.append("proposal-fingerprint-invalid")
    elif _fingerprint(_proposal_material(row)) != fingerprint:
        reasons.append("proposal-fingerprint-mismatch")
    snapshot = row.get("candidate_snapshot", {})
    if not isinstance(snapshot, Mapping) or not snapshot:
        reasons.append("candidate-snapshot-missing")
    else:
        if _fingerprint(dict(snapshot)) != str(
            row.get("candidate_snapshot_fingerprint", "")
        ):
            reasons.append("candidate-snapshot-fingerprint-mismatch")
        for key, expected in (
            ("provider_verified", True),
            ("candidate_only", True),
            ("eligible_for_binding", False),
        ):
            if snapshot.get(key) is not expected:
                reasons.append(
                    "candidate-snapshot-{}-invalid".format(key.replace("_", "-"))
                )
        for key in ("provider", "kind", "ref"):
            if str(snapshot.get(key, "")) != str(row.get(key, "")):
                reasons.append("candidate-snapshot-{}-mismatch".format(key))
    expected_flags = {
        "proposal_status": "ready-for-governed-review",
        "proposal_ready_for_review": True,
        "requires_governed_review": True,
        "proposal_only": True,
        "candidate_only": True,
        "eligible_for_binding": False,
        "canonical_write_performed": False,
        "status_mutation_planned": False,
        "owner_mutation_planned": False,
        "readiness_mutation_planned": False,
    }
    for key, expected in expected_flags.items():
        if row.get(key) != expected:
            reasons.append("proposal-{}-invalid".format(key.replace("_", "-")))
    field = str(row.get("field", ""))
    intent = str(row.get("mutation_intent", ""))
    if field not in ALLOWED_FIELDS:
        reasons.append("proposal-field-unsupported")
    if field in LIST_FIELDS and intent != "append-reference":
        reasons.append("proposal-list-intent-mismatch")
    if field in SINGLE_FIELDS and intent != "set-if-empty":
        reasons.append("proposal-single-intent-mismatch")
    if not _valid_reference(row.get("proposed_reference")):
        reasons.append("proposal-reference-invalid")
    target = row.get("target", {})
    if not isinstance(target, Mapping):
        reasons.append("proposal-target-invalid")
    else:
        checks = {
            "registry_path": "registry/items.jsonl",
            "project_id": str(row.get("project_id", "")),
            "readiness_slot": "validation",
            "contract_field": field,
        }
        for key, expected in checks.items():
            if str(target.get(key, "")) != expected:
                reasons.append(
                    "proposal-target-{}-mismatch".format(key.replace("_", "-"))
                )
        for key in ("item_id", "item_path", "evidence_profile"):
            if not str(target.get(key, "")).strip():
                reasons.append(
                    "proposal-target-{}-missing".format(key.replace("_", "-"))
                )
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
        "reason_codes": list(
            dict.fromkeys(str(reason) for reason in reasons if str(reason))
        ),
    }


def _selected_rows(
    proposal: Mapping[str, Any], selected: Sequence[str]
) -> Tuple[List[Mapping[str, Any]], List[str]]:
    rows = [row for row in proposal.get("rows", []) if isinstance(row, Mapping)]
    index: Dict[str, List[Mapping[str, Any]]] = {}
    for row in rows:
        fingerprint = str(row.get("proposal_fingerprint", ""))
        if fingerprint:
            index.setdefault(fingerprint, []).append(row)
    chosen: List[Mapping[str, Any]] = []
    reasons: List[str] = []
    for fingerprint in selected:
        matches = index.get(fingerprint, [])
        if len(matches) != 1:
            suffix = "not-found" if not matches else "not-unique"
            reasons.append("selected-proposal-{}:{}".format(suffix, fingerprint))
            continue
        row = matches[0]
        reasons.extend(
            "{}:{}".format(fingerprint, reason) for reason in _row_reasons(row)
        )
        chosen.append(row)
    target_counts = Counter(
        (
            str(row.get("target", {}).get("item_id", ""))
            if isinstance(row.get("target"), Mapping)
            else "",
            str(row.get("field", "")),
        )
        for row in chosen
    )
    for (item_id, field), count in target_counts.items():
        if count > 1:
            reasons.append(
                "multiple-proposals-same-target-field:{}:{}".format(item_id, field)
            )
    return chosen, list(dict.fromkeys(reasons))


def _locate_item(
    items: Sequence[Mapping[str, Any]], row: Mapping[str, Any]
) -> Tuple[int, List[str]]:
    target = row.get("target", {})
    if not isinstance(target, Mapping):
        return -1, ["proposal-target-invalid"]
    matches = [
        index
        for index, item in enumerate(items)
        if str(item.get("id", "")) == str(target.get("item_id", ""))
        and str(item.get("project_id", "")) == str(target.get("project_id", ""))
        and str(item.get("readiness_slot", "")) == "validation"
        and str(item.get("path", "")) == str(target.get("item_path", ""))
    ]
    if len(matches) != 1:
        return -1, ["canonical-target-item-not-unique"]
    return matches[0], []


def _apply_reference(item: Dict[str, Any], row: Mapping[str, Any]) -> List[str]:
    contract = item.get("evidence_contract", {})
    if not isinstance(contract, Mapping):
        return ["canonical-evidence-contract-invalid"]
    next_contract = dict(contract)
    if str(next_contract.get("status", "")) != "pending":
        return ["canonical-evidence-contract-not-pending"]
    target = row.get("target", {})
    if not isinstance(target, Mapping):
        return ["proposal-target-invalid"]
    if str(next_contract.get("profile", "")) != str(
        target.get("evidence_profile", "")
    ):
        return ["canonical-evidence-profile-drift"]
    field = str(row.get("field", ""))
    current = next_contract.get(field)
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
        next_contract[field] = list(current) + [dict(proposed)]
    elif field in SINGLE_FIELDS:
        if current is not None:
            return ["canonical-single-value-no-longer-empty"]
        next_contract[field] = dict(proposed)
    else:
        return ["proposal-field-unsupported"]
    evaluation = evaluate_evidence_contract(next_contract)
    if evaluation.get("declared_status") != "pending":
        return ["post-plan-declared-status-drift"]
    if evaluation.get("status") == "ready":
        return ["patch-plan-would-auto-promote-readiness"]
    item["evidence_contract"] = next_contract
    return []


def _materialize(
    root: pathlib.Path,
    selected_rows: Sequence[Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    items = [
        json.loads(json.dumps(dict(item), ensure_ascii=False))
        for item in registry_items(root)
    ]
    changes: Dict[str, Dict[str, Any]] = {}
    for row in selected_rows:
        index, reasons = _locate_item(items, row)
        if reasons:
            return [], [], reasons
        before = json.loads(json.dumps(items[index], ensure_ascii=False))
        reasons = _apply_reference(items[index], row)
        if reasons:
            fingerprint = str(row.get("proposal_fingerprint", ""))
            return [], [], [
                "{}:{}".format(fingerprint, reason) for reason in reasons
            ]
        after = items[index]
        item_id = str(after.get("id", ""))
        change = changes.setdefault(
            item_id,
            {
                "item_id": item_id,
                "project_id": str(after.get("project_id", "")),
                "item_path": str(after.get("path", "")),
                "registry_path": "registry/items.jsonl",
                "before_row_fingerprint": _fingerprint(before),
                "after_row_fingerprint": "",
                "changed_fields": [],
                "selected_proposal_fingerprints": [],
            },
        )
        change["changed_fields"].append(str(row.get("field", "")))
        change["selected_proposal_fingerprints"].append(
            str(row.get("proposal_fingerprint", ""))
        )
        change["after_row_fingerprint"] = _fingerprint(after)
    rows = []
    for item_id in sorted(changes):
        row = dict(changes[item_id])
        row["changed_fields"] = sorted(set(row["changed_fields"]))
        row["selected_proposal_fingerprints"] = sorted(
            set(row["selected_proposal_fingerprints"])
        )
        rows.append(row)
    return items, rows, []


def _transaction_plan(
    root: pathlib.Path, items: Sequence[Mapping[str, Any]]
) -> Tuple[Dict[str, Any], str, str, List[str]]:
    registry_path = root / "registry" / "items.jsonl"
    before_sha256 = file_sha256(registry_path)
    transaction = RepositoryTransaction(
        root, transaction_id="kh-operator-binding-patch-plan"
    )
    transaction.add_text(
        "registry/items.jsonl",
        encode_jsonl(items),
        expected_sha256=before_sha256,
    )
    plan = transaction.plan()
    writes = plan.get("writes", [])
    if plan.get("changed_count") != 1:
        return {}, "", "", ["registry-patch-plan-change-count-invalid"]
    if not (
        isinstance(writes, list)
        and len(writes) == 1
        and isinstance(writes[0], Mapping)
    ):
        return {}, "", "", ["registry-patch-plan-write-shape-invalid"]
    after_sha256 = str(writes[0].get("after_sha256", ""))
    if not after_sha256:
        return {}, "", "", ["registry-after-sha256-missing"]
    return plan, before_sha256, after_sha256, []


def _success(
    selected: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
    plan: Mapping[str, Any],
    before_sha256: str,
    after_sha256: str,
) -> Dict[str, Any]:
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
        "selected_proposal_fingerprints": list(selected),
        "selected_proposal_count": len(selected),
        "planned_item_count": len(rows),
        "planned_write_count": 1,
        "registry_path": "registry/items.jsonl",
        "registry_before_sha256": before_sha256,
        "registry_after_sha256": after_sha256,
        "rows": [dict(row) for row in rows],
        "transaction_plan": dict(plan),
        "reason_codes": ["governed-pr-required"],
    }


def build_binding_patch_plan(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
    selected_fingerprints: Sequence[str],
) -> Dict[str, Any]:
    """Plan exact canonical row changes for selected proposals without applying them."""

    reasons = _proposal_reasons(proposal)
    if reasons:
        return _blocked(reasons, [], status="upstream-error")
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
        reasons = [
            "selected-proposal-fingerprint-invalid:{}".format(value)
            for value in malformed
        ]
        return _blocked(reasons, selected)
    chosen, reasons = _selected_rows(proposal, selected)
    if reasons:
        return _blocked(reasons, selected)
    items, rows, reasons = _materialize(root, chosen)
    if reasons:
        return _blocked(reasons, selected)
    plan, before_sha256, after_sha256, reasons = _transaction_plan(root, items)
    if reasons:
        return _blocked(reasons, selected)
    return _success(selected, rows, plan, before_sha256, after_sha256)
