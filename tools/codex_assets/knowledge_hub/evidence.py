"""Project evidence profiles and deterministic readiness evaluation."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

from .common import KnowledgeHubError


EVIDENCE_PROFILE_REQUIREMENTS = {
    "control-plane": (
        "owner_ref",
        "source_refs",
        "validation_refs",
        "release_ref",
        "rollback_ref",
    ),
    "runtime-assets": (
        "owner_ref",
        "source_refs",
        "validation_refs",
        "release_ref",
        "rollback_ref",
    ),
    "software-tool": (
        "owner_ref",
        "source_refs",
        "validation_refs",
        "artifact_refs",
        "release_ref",
        "rollback_ref",
    ),
    "embedded-target": (
        "owner_ref",
        "source_refs",
        "validation_refs",
        "artifact_refs",
        "device_refs",
        "release_ref",
        "rollback_ref",
    ),
    "aggregate-group": (
        "owner_ref",
        "member_project_ids",
    ),
}


def project_evidence_profile(project: Mapping[str, Any]) -> str:
    declared = str(project.get("evidence_profile", "")).strip()
    if declared:
        if declared not in EVIDENCE_PROFILE_REQUIREMENTS:
            raise KnowledgeHubError("unknown evidence profile: {}".format(declared))
        return declared
    project_type = str(project.get("type", ""))
    boundary = str(project.get("repo_boundary", ""))
    groups = {str(value) for value in project.get("groups", [])}
    if project_type == "knowledge-control-plane" or boundary == "control-plane":
        return "control-plane"
    if project_type == "runtime-repository" or boundary == "runtime-assets":
        return "runtime-assets"
    if project_type == "product-group" or boundary == "group":
        return "aggregate-group"
    if boundary in {"tooling", "subrepo"} or "agent-tools" in groups:
        return "software-tool"
    if boundary in {"primary", "module", "application", "firmware"}:
        return "embedded-target"
    raise KnowledgeHubError(
        "cannot derive evidence profile for project {}".format(project.get("id", "unknown"))
    )


def new_evidence_contract(
    profile: str,
    member_project_ids: Sequence[str] = (),
) -> Dict[str, Any]:
    if profile not in EVIDENCE_PROFILE_REQUIREMENTS:
        raise KnowledgeHubError("unknown evidence profile: {}".format(profile))
    return {
        "schema_version": 1,
        "profile": profile,
        "status": "pending",
        "owner_ref": None,
        "source_refs": [],
        "validation_refs": [],
        "artifact_refs": [],
        "device_refs": [],
        "release_ref": None,
        "rollback_ref": None,
        "not_applicable": {},
        "member_project_ids": sorted(
            {str(value) for value in member_project_ids if str(value).strip()}
        ),
    }


def merge_evidence_contract(
    existing: Mapping[str, Any],
    profile: str,
    member_project_ids: Sequence[str] = (),
) -> Dict[str, Any]:
    if not existing:
        return new_evidence_contract(profile, member_project_ids)
    contract = dict(existing)
    if contract.get("profile") != profile:
        raise KnowledgeHubError(
            "evidence profile drift: expected {}, found {}".format(
                profile, contract.get("profile", "missing")
            )
        )
    defaults = new_evidence_contract(profile, member_project_ids)
    for key, value in defaults.items():
        contract.setdefault(key, value)
    if profile == "aggregate-group" and not contract.get("member_project_ids"):
        contract["member_project_ids"] = defaults["member_project_ids"]
    return contract


def _has_reference(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value) and all(_has_reference(row) for row in value)
    if not isinstance(value, Mapping):
        return False
    return bool(str(value.get("ref", "")).strip() and str(value.get("kind", "")).strip())


def _approved_not_applicable(contract: Mapping[str, Any], field: str) -> bool:
    row = contract.get("not_applicable", {}).get(field, {})
    return isinstance(row, Mapping) and all(
        str(row.get(key, "")).strip()
        for key in ("owner_ref", "authorization_id", "reason")
    )


def evaluate_evidence_contract(
    contract: Mapping[str, Any],
    ready_member_ids: Sequence[str] = (),
    current_project_id: str = "",
) -> Dict[str, Any]:
    profile = str(contract.get("profile", ""))
    requirements = EVIDENCE_PROFILE_REQUIREMENTS.get(profile)
    if requirements is None:
        return {
            "status": "invalid",
            "profile": profile,
            "missing_fields": ["profile"],
            "invalid_fields": ["profile"],
        }
    ready_members = set(str(value) for value in ready_member_ids)
    current_project = str(current_project_id).strip()
    missing: List[str] = []
    invalid: List[str] = []
    for field in requirements:
        value = contract.get(field)
        if field == "member_project_ids":
            members = {str(row) for row in value or []}
            dependency_members = (
                members - {current_project} if current_project else members
            )
            if not members:
                missing.append(field)
            elif not dependency_members.issubset(ready_members):
                missing.append(field)
            continue
        if field == "owner_ref":
            if not _has_reference(value):
                missing.append(field)
            continue
        if _has_reference(value):
            continue
        if _approved_not_applicable(contract, field):
            continue
        missing.append(field)
    declared_status = str(contract.get("status", "pending"))
    if declared_status not in {"pending", "ready", "invalidated"}:
        invalid.append("status")
    if declared_status == "ready" and missing:
        invalid.append("status")
    status = "ready" if not missing and not invalid and declared_status == "ready" else "pending"
    return {
        "status": status,
        "profile": profile,
        "declared_status": declared_status,
        "missing_fields": sorted(set(missing)),
        "invalid_fields": sorted(set(invalid)),
        "required_fields": list(requirements),
    }
