"""Support helpers for the product maturity gate."""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import time
import uuid
from typing import Any, Dict, Mapping, Set

from .common import (
    KnowledgeHubError,
    ensure_private_directory_tree,
    ensure_private_file,
    load_json,
    pretty_json,
    project_rows,
    registry_items,
    repository_rows,
    route_rows,
    run_rtk,
    working_tree_signature,
)
from .context import TASK_TYPES, _query_route
from .engineering import engineering_snapshot_path
from .evidence import evaluate_evidence_contract
from .project_readiness import (
    SLOT_NAMES,
    _project_paths,
    _repo_rows_for_project,
    _workspace_state,
)
from .recovery_evidence import (
    evidence_matches_current_execution,
    expected_repository_from_registry,
)
from .schemas import validate_instance

def _source_runtime_ready(payload: Mapping[str, Any], exit_code: int) -> bool:
    registry_count = int(payload.get("registry_source_count", 0) or 0)
    row_count = int(payload.get("row_count", 0) or 0)
    executed_count = int(payload.get("executed_count", 0) or 0)
    not_applicable_count = int(payload.get("not_applicable_count", 0) or 0)
    selected_ids = [str(value) for value in payload.get("selected_source_ids", [])]
    expected_ids = [str(value) for value in payload.get("expected_source_ids", [])]
    return bool(
        exit_code == 0
        and payload.get("status") == "pass"
        and payload.get("scope") == "all"
        and payload.get("source_check_health_executed") is True
        and registry_count > 0
        and row_count == registry_count
        and executed_count + not_applicable_count == row_count
        and len(selected_ids) == registry_count
        and selected_ids == expected_ids
    )

def _canonical_source_mapping_ready(
    contract_evaluation: Mapping[str, Any],
) -> bool:
    """Report canonical source evidence independently from host-local workspaces."""
    if contract_evaluation.get("profile") == "aggregate-group":
        return True
    required = set(contract_evaluation.get("required_fields", []))
    missing = set(contract_evaluation.get("missing_fields", []))
    invalid = set(contract_evaluation.get("invalid_fields", []))
    return bool(
        "source_refs" in required
        and "source_refs" not in missing
        and "source_refs" not in invalid
    )


def _unit_test_evidence_reuse_mode(
    regression_suite: str,
    reuse_engineering_evidence: bool,
    engineering_quality: Mapping[str, Any],
) -> str:
    check_statuses = engineering_quality.get("check_statuses", {})
    eligible = bool(
        engineering_quality.get("fresh")
        and isinstance(check_statuses, Mapping)
        and check_statuses.get("coverage") == "pass"
        and check_statuses.get("coverage_report") == "pass"
    )
    if not eligible:
        return "disabled"
    if reuse_engineering_evidence:
        return "explicit"
    if regression_suite == "quick":
        return "automatic-quick"
    return "disabled"

def product_snapshot_path(root: pathlib.Path, regression_suite: str) -> pathlib.Path:
    if regression_suite not in {"quick", "full"}:
        raise ValueError("regression_suite must be quick or full")
    return root / ".cache/knowledge-hub/final-gate-product-{}.json".format(
        regression_suite
    )

def _write_snapshot(
    root: pathlib.Path,
    payload: Mapping[str, Any],
    regression_suite: str,
) -> str:
    path = product_snapshot_path(root, regression_suite)
    ensure_private_directory_tree(root, path.parent)
    temporary = path.with_name("{}.tmp-{}".format(path.name, uuid.uuid4().hex))
    temporary.write_text(pretty_json(dict(payload)) + "\n", encoding="utf-8")
    ensure_private_file(temporary)
    os.replace(str(temporary), str(path))
    ensure_private_file(path)
    return str(path.relative_to(root))

def _git_delivery_state(root: pathlib.Path) -> Dict[str, Any]:
    status_result = run_rtk(
        root,
        ["git", "-c", "core.quotePath=false", "status", "--porcelain=v1", "--untracked-files=all"],
        timeout=30,
    )
    revision_result = run_rtk(
        root,
        ["git", "rev-parse", "HEAD"],
        timeout=15,
        accepted_exit_codes=(0, 128),
    )
    dirty_rows = [line for line in status_result["stdout"].splitlines() if line.strip()]
    if dirty_rows == ["ok"]:
        dirty_rows = []
    required_manifests = (
        "pyproject.toml",
        "requirements-runtime.txt",
        "requirements-dev.txt",
        "requirements-runtime.lock",
        "requirements-dev.lock",
        ".github/workflows/quality.yml",
        ".github/dependabot.yml",
        "tools/ci/rtk",
        "tools/ci/bootstrap-path.sh",
        "tools/ci/python-runtime.sh",
    )
    tracked_result = run_rtk(
        root,
        ["git", "ls-files", "--"] + list(required_manifests),
        timeout=15,
    )
    tracked = {line.strip() for line in tracked_result["stdout"].splitlines() if line.strip()}
    return {
        "head_revision": revision_result["stdout"].strip() if revision_result["exit_code"] == 0 else "",
        "head_present": revision_result["exit_code"] == 0,
        "worktree_clean": not dirty_rows,
        "dirty_path_count": len(dirty_rows),
        "dirty_paths": dirty_rows[:100],
        "required_dependency_manifests": list(required_manifests),
        "tracked_dependency_manifests": sorted(tracked),
        "dependency_manifests_tracked": tracked == set(required_manifests),
        "required_release_contract_files": list(required_manifests),
        "tracked_release_contract_files": sorted(tracked),
        "release_contract_files_tracked": tracked == set(required_manifests),
    }

def _engineering_quality_state(
    root: pathlib.Path,
    signature: str,
    max_age_hours: int = 24,
) -> Dict[str, Any]:
    path = engineering_snapshot_path(root)
    if not path.is_file() or path.is_symlink():
        return {
            "status": "missing",
            "fresh": False,
            "signature_matches": False,
            "path": str(path.relative_to(root)),
        }
    try:
        payload = load_json(path, {}) or {}
        age_seconds = max(0.0, time.time() - path.stat().st_mtime)
    except (KnowledgeHubError, OSError, ValueError):
        return {
            "status": "invalid",
            "fresh": False,
            "signature_matches": False,
            "path": str(path.relative_to(root)),
        }
    integrity = payload.get("candidate_integrity", {})
    signature_matches = (
        isinstance(integrity, Mapping)
        and integrity.get("before_signature") == signature
        and integrity.get("after_signature") == signature
    )
    fresh = bool(
        payload.get("status") == "pass"
        and payload.get("mode") == "full"
        and isinstance(integrity, Mapping)
        and integrity.get("unchanged") is True
        and signature_matches
        and age_seconds <= max_age_hours * 3600
    )
    return {
        "status": payload.get("status", "invalid"),
        "mode": payload.get("mode", ""),
        "fresh": fresh,
        "signature_matches": signature_matches,
        "age_seconds": round(age_seconds, 1),
        "path": str(path.relative_to(root)),
        "generated_at": payload.get("generated_at", ""),
        "failed_checks": list(payload.get("errors", []))[:20],
        "check_statuses": {
            str(name): str(row.get("status", ""))
            for name, row in (payload.get("checks", {}) or {}).items()
            if isinstance(row, Mapping)
        },
        "sbom": payload.get("sbom", {}),
    }

def _candidate_integrity(root: pathlib.Path, before_signature: str) -> Dict[str, Any]:
    after_signature = working_tree_signature(root)
    unchanged = after_signature == before_signature
    return {
        "status": "pass" if unchanged else "fail",
        "unchanged": unchanged,
        "before_signature": before_signature,
        "after_signature": after_signature,
        "scope": "tracked-and-untracked-nonignored-candidate",
    }

def _restore_state(
    root: pathlib.Path,
    as_of: str,
    source_mode: str,
    signature: str,
    head_revision: str,
    max_age_hours: int = 24,
) -> Dict[str, Any]:
    path = root / ".cache/knowledge-hub/restore-drill-{}.json".format(source_mode)
    if not path.exists():
        return {
            "status": "missing",
            "source_mode": source_mode,
            "fresh": False,
            "source_matches": False,
            "remote_checkout_verified": False,
            "remote_published_ref_verified": False,
            "offsite_environment_verified": False,
            "path": str(path.relative_to(root)),
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "status": "invalid",
            "source_mode": source_mode,
            "fresh": False,
            "source_matches": False,
            "remote_checkout_verified": False,
            "remote_published_ref_verified": False,
            "offsite_environment_verified": False,
            "path": str(path.relative_to(root)),
        }
    age = max(0.0, dt.datetime.now().timestamp() - path.stat().st_mtime)
    source_matches = (
        payload.get("candidate_signature") == signature
        if source_mode == "candidate"
        else payload.get("source_revision") == head_revision
    )
    schema_validation = validate_instance(root, "restore-drill-v4", payload)
    expected_repository = expected_repository_from_registry(root)
    execution_bound = bool(
        source_mode == "head"
        and schema_validation["status"] == "pass"
        and evidence_matches_current_execution(
            payload.get("execution_environment", {}),
            head_revision,
            expected_repository=expected_repository,
        )
    )
    fresh = (
        payload.get("status") == "pass"
        and schema_validation["status"] == "pass"
        and payload.get("source_mode") == source_mode
        and payload.get("as_of") == as_of
        and age <= max_age_hours * 3600
        and source_matches
    )
    return {
        "status": payload.get("status", "invalid"),
        "source_mode": source_mode,
        "fresh": fresh,
        "source_matches": source_matches,
        "signature_matches": source_matches,
        "age_seconds": round(age, 1),
        "path": str(path.relative_to(root)),
        "source_revision": payload.get("source_revision", ""),
        "candidate_path_count": payload.get("candidate_path_count", 0),
        "copied_file_count": payload.get("copied_file_count", 0),
        "failed_checks": payload.get("failed_checks", []),
        "generated_at": payload.get("generated_at", ""),
        "execution_environment": payload.get("execution_environment", {}),
        "schema_validation": schema_validation,
        "evidence_matches_current_execution": execution_bound,
        "remote_checkout_verified": bool(
            fresh
            and execution_bound
            and payload.get("remote_checkout_verified", False)
        ),
        "remote_published_ref_verified": bool(
            fresh
            and execution_bound
            and payload.get("remote_published_ref_verified", False)
        ),
        "offsite_environment_verified": bool(
            fresh
            and execution_bound
            and payload.get("offsite_environment_verified", False)
        ),
    }

def _project_readiness(root: pathlib.Path) -> Dict[str, Any]:
    projects = project_rows(root)
    routes = route_rows(root)
    items = registry_items(root)
    repositories = repository_rows(root)
    items_by_path = {str(row.get("path", "")): row for row in items if row.get("path")}
    routes_by_id = {str(row.get("project_id", "")): row for row in routes}
    local_doc = root / "local/workspaces.json"
    local_rows = []
    if local_doc.exists():
        try:
            local_rows = list(json.loads(local_doc.read_text(encoding="utf-8")).get("workspaces", []))
        except (OSError, json.JSONDecodeError):
            local_rows = []
    local_workspaces = {str(row.get("workspace_ref", "")): row for row in local_rows if row.get("workspace_ref")}
    rows = []
    structural_ready = 0
    source_mapped = 0
    local_workspace_ready = 0
    decision_owner_ready = 0
    owner_ref_ready = 0
    owner_boundary_ready = 0
    reusable_asset_ready = 0
    ready_project_ids: Set[str] = set()
    for project in projects:
        project_id = str(project["id"])
        paths = _project_paths(project)
        slot_rows = []
        slot_items: Dict[str, Mapping[str, Any]] = {}
        for slot in SLOT_NAMES:
            item = items_by_path.get(paths[slot], {})
            slot_items[slot] = item
            slot_rows.append(
                {
                    "slot": slot,
                    "item_id": item.get("id", ""),
                    "path": paths[slot],
                    "item_present": bool(item),
                    "body_present": (root / paths[slot]).is_file(),
                    "status": item.get("status", "missing"),
                    "manual_validation_pending": item.get("manual_validation_pending", True),
                    "decision_owner": item.get("decision_owner", "unassigned"),
                    "evidence_contract_present": bool(item.get("evidence_contract"))
                    if slot == "validation"
                    else None,
                }
            )
        route = routes_by_id.get(project_id, {})
        structural = bool(route) and all(row["item_present"] and row["body_present"] for row in slot_rows)
        structural_ready += int(structural)
        repos = _repo_rows_for_project(project, repositories)
        workspace_state = _workspace_state(repos, local_workspaces)
        local_workspace_mapped = workspace_state in {
            "all-mapped-and-present",
            "not-applicable-group-or-control-plane",
        }
        local_workspace_ready += int(local_workspace_mapped)
        validation_item = slot_items["validation"]
        contract_evaluation = evaluate_evidence_contract(
            validation_item.get("evidence_contract", {})
        )
        source_mapping_ready = _canonical_source_mapping_ready(contract_evaluation)
        source_mapped += int(source_mapping_ready)
        decision_owner_values = {
            str(item.get("decision_owner", "unassigned")) for item in slot_items.values()
        }
        project_decision_owner_ready = (
            len(decision_owner_values) == 1
            and next(iter(decision_owner_values)) not in {"", "unassigned"}
        )
        project_owner_ref_ready = (
            "owner_ref" not in contract_evaluation["missing_fields"]
            and "owner_ref" not in contract_evaluation["invalid_fields"]
        )
        project_owner_boundary_ready = project_decision_owner_ready and project_owner_ref_ready
        decision_owner_ready += int(project_decision_owner_ready)
        owner_ref_ready += int(project_owner_ref_ready)
        owner_boundary_ready += int(project_owner_boundary_ready)
        evidence = (
            structural
            and source_mapping_ready
            and contract_evaluation["status"] == "ready"
            and contract_evaluation["profile"] != "aggregate-group"
        )
        if evidence:
            ready_project_ids.add(project_id)
        reusable = (
            evidence
            and validation_item.get("status") == "active"
            and validation_item.get("decision_owner") not in {"", "unassigned"}
        )
        reusable_asset_ready += int(reusable)
        rows.append(
            {
                "project_id": project_id,
                "name": project.get("name", project_id),
                "structural_status": "pass" if structural else "fail",
                "route_scope": route.get("route_scope", "missing"),
                "workspace_state": workspace_state,
                "local_workspace_ready": local_workspace_mapped,
                "source_mapping_ready": source_mapping_ready,
                "evidence_profile": contract_evaluation["profile"],
                "evidence_status": "ready" if evidence else "contract-evidence-pending",
                "evidence_contract": contract_evaluation,
                "evidence_field_status": (
                    "complete-awaiting-declaration"
                    if not contract_evaluation["missing_fields"]
                    and not contract_evaluation["invalid_fields"]
                    else "incomplete"
                ),
                "decision_owner_status": "ready" if project_decision_owner_ready else "pending",
                "owner_ref_status": "ready" if project_owner_ref_ready else "pending",
                "owner_boundary_status": "ready" if project_owner_boundary_ready else "pending",
                "reusable_asset_status": "ready" if reusable else "pending",
                "slots": slot_rows,
            }
        )
    rows_by_id = {row["project_id"]: row for row in rows}
    for project in projects:
        project_id = str(project["id"])
        row = rows_by_id[project_id]
        if row["evidence_profile"] != "aggregate-group":
            continue
        validation_path = _project_paths(project)["validation"]
        validation_item = items_by_path.get(validation_path, {})
        evaluation = evaluate_evidence_contract(
            validation_item.get("evidence_contract", {}),
            ready_member_ids=sorted(ready_project_ids),
        )
        evidence = (
            row["structural_status"] == "pass"
            and row["source_mapping_ready"]
            and evaluation["status"] == "ready"
        )
        row["evidence_contract"] = evaluation
        row["evidence_field_status"] = (
            "complete-awaiting-declaration"
            if not evaluation["missing_fields"] and not evaluation["invalid_fields"]
            else "incomplete"
        )
        row["evidence_status"] = "ready" if evidence else "member-contract-evidence-pending"
        if evidence:
            ready_project_ids.add(project_id)
    route_failures = []
    route_checks = 0
    for project in projects:
        for task_type in sorted(TASK_TYPES):
            selected, score, _ = _query_route("{} {}".format(project["id"], task_type), routes)
            route_checks += 1
            if not selected or selected.get("project_id") != project["id"] or score <= 0:
                route_failures.append({"project_id": project["id"], "task_type": task_type})
    project_count = len(projects)
    evidence_field_complete_count = sum(
        1 for row in rows if row["evidence_field_status"] == "complete-awaiting-declaration"
    )
    return {
        "project_count": project_count,
        "slot_count": project_count * len(SLOT_NAMES),
        "structural_ready_count": structural_ready,
        "structural_coverage": round(structural_ready / float(max(1, project_count)), 4),
        "source_mapping_ready_count": source_mapped,
        "local_workspace_ready_count": local_workspace_ready,
        "decision_owner_ready_count": decision_owner_ready,
        "owner_ref_ready_count": owner_ref_ready,
        "owner_boundary_ready_count": owner_boundary_ready,
        "owner_boundary_coverage": round(owner_boundary_ready / float(max(1, project_count)), 4),
        "evidence_ready_count": len(ready_project_ids),
        "evidence_coverage": round(len(ready_project_ids) / float(max(1, project_count)), 4),
        "evidence_field_complete_count": evidence_field_complete_count,
        "evidence_field_complete_coverage": round(
            evidence_field_complete_count / float(max(1, project_count)), 4
        ),
        "reusable_asset_ready_count": reusable_asset_ready,
        "reusable_asset_coverage": round(reusable_asset_ready / float(max(1, project_count)), 4),
        "route_count": len(routes),
        "route_matrix_check_count": route_checks,
        "route_matrix_failure_count": len(route_failures),
        "route_matrix_failures": route_failures,
        "rows": rows,
    }
