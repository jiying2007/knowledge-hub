"""Materialize a non-canonical candidate for machine-routed evidence bindings."""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .common import bytes_sha256, encode_jsonl, file_sha256
from .operator_auto_route import (
    MACHINE_RATCHET_FIELDS,
    PROJECTION as ROUTE_PROJECTION,
    build_unique_execution_routes,
)
from .operator_binding_patch_plan import _materialize, _selected_rows

PROJECTION = "knowledge-operator-machine-ratchet-candidate-v1"
REGISTRY_PATH = "registry/items.jsonl"


def _blocked(reasons: Sequence[str]) -> Tuple[str, Dict[str, Any]]:
    return "", {
        "schema_version": 1,
        "projection": PROJECTION,
        "status": "blocked",
        "read_only": True,
        "canonical_write_performed": False,
        "automatic_execution_enabled": False,
        "candidate_only": True,
        "selected_proposal_count": 0,
        "selected_proposal_fingerprints": [],
        "registry_path": REGISTRY_PATH,
        "registry_before_sha256": "",
        "registry_after_sha256": "",
        "candidate_sha256": "",
        "rows": [],
        "reason_codes": list(dict.fromkeys(str(value) for value in reasons if str(value))),
    }


def _route_reasons(route: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    expected = {
        "projection": ROUTE_PROJECTION,
        "read_only": True,
        "selection_is_authorization": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "ambiguous_target_count": 0,
    }
    for key, value in expected.items():
        if route.get(key) != value:
            reasons.append("route-{}-invalid".format(key.replace("_", "-")))
    if route.get("status") not in {
        "ready-for-machine-ratchet",
        "mixed-routing",
    }:
        reasons.append("route-machine-status-not-ready")
    machine = route.get("machine_route", {})
    if not isinstance(machine, Mapping):
        reasons.append("machine-route-invalid")
    elif machine.get("status") != "ready-for-machine-ratchet":
        reasons.append("machine-subroute-not-ready")
    return reasons


def _plan_reasons(
    root: pathlib.Path,
    machine: Mapping[str, Any],
    content: str,
    rows: Sequence[Mapping[str, Any]],
    selected: Sequence[str],
) -> List[str]:
    reasons: List[str] = []
    plan = machine.get("patch_plan", {})
    if not isinstance(plan, Mapping):
        return ["machine-patch-plan-invalid"]
    before = file_sha256(root / REGISTRY_PATH)
    after = bytes_sha256(content.encode("utf-8"))
    if plan.get("registry_path") != REGISTRY_PATH:
        reasons.append("machine-registry-path-invalid")
    if str(plan.get("registry_before_sha256", "")) != before:
        reasons.append("machine-registry-before-sha256-mismatch")
    if str(plan.get("registry_after_sha256", "")) != after:
        reasons.append("machine-registry-after-sha256-mismatch")
    if list(plan.get("selected_proposal_fingerprints", [])) != list(selected):
        reasons.append("machine-selection-patch-plan-mismatch")
    if int(plan.get("planned_write_count", 0) or 0) != 1:
        reasons.append("machine-planned-write-count-invalid")
    if int(plan.get("planned_item_count", 0) or 0) != len(rows):
        reasons.append("machine-planned-item-count-mismatch")
    for row in rows:
        changed = {str(value) for value in row.get("changed_fields", [])}
        if not changed or not changed.issubset(MACHINE_RATCHET_FIELDS):
            reasons.append("machine-changed-field-outside-allowlist")
    return list(dict.fromkeys(reasons))


def build_machine_ratchet_candidate(
    root: pathlib.Path,
    proposal: Mapping[str, Any],
    route: Optional[Mapping[str, Any]] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Recompute and materialize the exact machine route without applying it."""

    root = pathlib.Path(root).resolve()
    resolved_route = (
        dict(route)
        if isinstance(route, Mapping)
        else build_unique_execution_routes(root, proposal)
    )
    reasons = _route_reasons(resolved_route)
    if reasons:
        return _blocked(reasons)

    machine = resolved_route["machine_route"]
    selected = [
        str(value)
        for value in machine.get("selected_proposal_fingerprints", [])
        if str(value)
    ]
    if not selected:
        return _blocked(["machine-selection-empty"])
    chosen, reasons = _selected_rows(proposal, selected)
    if reasons:
        return _blocked(["machine-selection-revalidation:{}".format(value) for value in reasons])
    items, rows, reasons = _materialize(root, chosen)
    if reasons:
        return _blocked(["machine-materialization:{}".format(value) for value in reasons])
    content = encode_jsonl(items)
    reasons = _plan_reasons(root, machine, content, rows, selected)
    if reasons:
        return _blocked(reasons)

    before = file_sha256(root / REGISTRY_PATH)
    after = bytes_sha256(content.encode("utf-8"))
    return content, {
        "schema_version": 1,
        "projection": PROJECTION,
        "status": "ready-for-machine-ratchet",
        "read_only": True,
        "canonical_write_performed": False,
        "automatic_execution_enabled": False,
        "candidate_only": True,
        "authorization_class": "autonomous-low-risk-ratchet",
        "selected_proposal_count": len(selected),
        "selected_proposal_fingerprints": selected,
        "registry_path": REGISTRY_PATH,
        "registry_before_sha256": before,
        "registry_after_sha256": after,
        "candidate_sha256": after,
        "rows": [dict(row) for row in rows],
        "reason_codes": [],
    }
