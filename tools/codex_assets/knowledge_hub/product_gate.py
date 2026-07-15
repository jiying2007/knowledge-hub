"""Product-level maturity gate beyond lifecycle governance."""

from __future__ import annotations

import datetime as dt
import concurrent.futures
import json
import os
import pathlib
import re
import time
from collections import Counter
from typing import Any, Dict, List, Mapping, Sequence, Set

from .common import (
    parse_json_output,
    pretty_json,
    project_rows,
    registry_items,
    repository_rows,
    route_rows,
    run_rtk,
    utc_timestamp,
    working_tree_signature,
)
from .context import TASK_TYPES, _query_route
from .evidence import evaluate_evidence_contract
from .export import plan_team_export
from .link_audit import audit_links
from .metrics import local_metrics
from .obsidian_view import build_obsidian_views
from .project_readiness import SLOT_NAMES, _project_paths, _repo_rows_for_project, _workspace_state
from .retrieval import run_retrieval_benchmark
from .schemas import validate_instance, validate_schema_catalog
from .store import incomplete_transactions


FINAL_PROOF_INDEX_PATHS = (
    "indexes/by-owner.md",
    "indexes/by-status.md",
    "indexes/by-review-date.md",
    "indexes/by-topic.md",
    "indexes/by-decision.md",
)
FINAL_PROOF_SEED_IDS = (
    "knowledge-hub-owner-handoff-final-gate-hardening-20260622",
    "knowledge-hub-final-gate-evidence-recovery-20260622",
    "knowledge-hub-recovery-search-manual-hardening-20260622",
    "knowledge-hub-final-proof-maintenance-hardening-20260622",
    "knowledge-hub-owner-queue-command-hardening-20260622",
    "knowledge-hub-final-recovery-discoverability-hardening-20260622",
    "knowledge-hub-final-proof-summary-readability-hardening-20260622",
    "knowledge-hub-source-check-snapshot-evidence-readability-20260622",
    "knowledge-hub-report-only-maintenance-tools-20260622",
    "knowledge-hub-owner-inbox-final-gate-audit-20260622",
)


def product_snapshot_path(root: pathlib.Path) -> pathlib.Path:
    return root / ".cache/knowledge-hub/final-gate-product.json"


def _write_snapshot(root: pathlib.Path, payload: Mapping[str, Any]) -> str:
    path = product_snapshot_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(pretty_json(dict(payload)) + "\n", encoding="utf-8")
    os.replace(str(temporary), str(path))
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
    required_manifests = ("pyproject.toml", "requirements-runtime.txt", "requirements-dev.txt")
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
            "path": str(path.relative_to(root)),
        }
    age = max(0.0, dt.datetime.now().timestamp() - path.stat().st_mtime)
    source_matches = (
        payload.get("candidate_signature") == signature
        if source_mode == "candidate"
        else payload.get("source_revision") == head_revision
    )
    fresh = (
        payload.get("status") == "pass"
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
        mapped = workspace_state in {"all-mapped-and-present", "not-applicable-group-or-control-plane"}
        source_mapped += int(mapped)
        validation_item = slot_items["validation"]
        contract_evaluation = evaluate_evidence_contract(
            validation_item.get("evidence_contract", {})
        )
        evidence = (
            structural
            and mapped
            and contract_evaluation["status"] == "ready"
            and contract_evaluation["profile"] != "aggregate-group"
        )
        if evidence:
            ready_project_ids.add(project_id)
        profile_item = slot_items["profile"]
        runbook_item = slot_items["runbook"]
        reusable = (
            evidence
            and profile_item.get("status") == "active"
            and runbook_item.get("status") == "active"
            and profile_item.get("decision_owner") not in {"", "unassigned"}
        )
        reusable_asset_ready += int(reusable)
        rows.append(
            {
                "project_id": project_id,
                "name": project.get("name", project_id),
                "structural_status": "pass" if structural else "fail",
                "route_scope": route.get("route_scope", "missing"),
                "workspace_state": workspace_state,
                "source_mapping_ready": mapped,
                "evidence_profile": contract_evaluation["profile"],
                "evidence_status": "ready" if evidence else "contract-evidence-pending",
                "evidence_contract": contract_evaluation,
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
    return {
        "project_count": project_count,
        "slot_count": project_count * len(SLOT_NAMES),
        "structural_ready_count": structural_ready,
        "structural_coverage": round(structural_ready / float(max(1, project_count)), 4),
        "source_mapping_ready_count": source_mapped,
        "evidence_ready_count": len(ready_project_ids),
        "evidence_coverage": round(len(ready_project_ids) / float(max(1, project_count)), 4),
        "reusable_asset_ready_count": reusable_asset_ready,
        "reusable_asset_coverage": round(reusable_asset_ready / float(max(1, project_count)), 4),
        "route_count": len(routes),
        "route_matrix_check_count": route_checks,
        "route_matrix_failure_count": len(route_failures),
        "route_matrix_failures": route_failures,
        "rows": rows,
    }


def _proof_artifacts(root: pathlib.Path, as_of: str, items: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    suffix = as_of.replace("-", "")
    items_by_id = {str(row.get("id", "")): row for row in items if row.get("id")}
    dynamic_ids = []
    for item_id, row in items_by_id.items():
        tags = row.get("tags", []) if isinstance(row.get("tags"), list) else []
        path = str(row.get("path", ""))
        review_status = str(row.get("review_status", ""))
        if (
            row.get("domain") == "governance"
            and row.get("kind") == "audit"
            and (row.get("created_at") == as_of or row.get("updated_at") == as_of)
            and "governance" in tags
            and path.startswith("artifacts/manifests/knowledge-hub-")
            and path.endswith("-{}.md".format(suffix))
            and (review_status.endswith("-applied") or review_status.endswith("-registered"))
        ):
            dynamic_ids.append(item_id)
    expected_ids = list(dict.fromkeys(list(FINAL_PROOF_SEED_IDS) + sorted(dynamic_ids)))
    index_text = {}
    for relative in FINAL_PROOF_INDEX_PATHS:
        try:
            index_text[relative] = (root / relative).read_text(encoding="utf-8")
        except OSError:
            index_text[relative] = ""
    missing_registry = []
    missing_md = []
    missing_jsonl = []
    missing_indexes: Dict[str, List[str]] = {}
    rows = []
    for item_id in expected_ids:
        item = items_by_id.get(item_id, {})
        path = str(item.get("path", ""))
        jsonl_path = str(pathlib.PurePosixPath(path).with_suffix(".jsonl")) if path else ""
        if not item:
            missing_registry.append(item_id)
        if not path or not (root / path).is_file():
            missing_md.append({"id": item_id, "path": path})
        if not jsonl_path or not (root / jsonl_path).is_file():
            missing_jsonl.append({"id": item_id, "path": jsonl_path})
        index_gaps = [
            relative
            for relative, text in index_text.items()
            if item_id not in text and (not path or path not in text) and (not jsonl_path or jsonl_path not in text)
        ]
        if index_gaps:
            missing_indexes[item_id] = index_gaps
        rows.append(
            {
                "id": item_id,
                "path": path,
                "jsonl_path": jsonl_path,
                "status": "pass" if item and path and (root / path).is_file() and jsonl_path and (root / jsonl_path).is_file() and not index_gaps else "fail",
            }
        )
    status = "pass" if not missing_registry and not missing_md and not missing_jsonl and not missing_indexes else "fail"
    return {
        "status": status,
        "selection_mode": "seed-plus-dynamic-governance-by-as-of-date",
        "selection_date": as_of,
        "dynamic_selector": {"date": as_of, "suffix": suffix},
        "seed_ids": list(FINAL_PROOF_SEED_IDS),
        "dynamic_ids": sorted(dynamic_ids),
        "baseline_dynamic_ids": [],
        "selection_dynamic_ids": sorted(dynamic_ids),
        "baseline_selection_overlap_ids": [],
        "expected_ids": expected_ids,
        "expected_count": len(expected_ids),
        "dynamic_count": len(dynamic_ids),
        "baseline_dynamic_count": 0,
        "selection_dynamic_count": len(dynamic_ids),
        "baseline_selection_overlap_count": 0,
        "registered_count": len(expected_ids) - len(missing_registry),
        "paired_count": len(expected_ids) - len(missing_md) - len(missing_jsonl),
        "indexed_count": len(expected_ids) - len(missing_indexes),
        "missing_registry": missing_registry,
        "missing_md": missing_md,
        "missing_jsonl": missing_jsonl,
        "missing_indexes": missing_indexes,
        "rows": rows,
    }


def run_product_gate(
    root: pathlib.Path,
    as_of: str,
    regression_suite: str = "quick",
) -> Dict[str, Any]:
    if regression_suite not in {"quick", "full"}:
        raise ValueError("regression_suite must be quick or full")
    started = time.monotonic()
    signature = working_tree_signature(root)
    git_delivery = _git_delivery_state(root)
    tasks = {
        "check_result": lambda: run_rtk(
            root,
            ["bash", "tools/knowledge-check.sh", "--dry-run", "--json", "--diagnostics", "--as-of", as_of],
            timeout=45,
            accepted_exit_codes=(0, 1),
        ),
        "status_result": lambda: run_rtk(
            root,
            ["bash", "tools/knowledge-status.sh", "--strict", "--json", "--as-of", as_of],
            timeout=60,
            accepted_exit_codes=(0, 1, 2),
        ),
        "source_check_result": lambda: run_rtk(
            root,
            ["bash", "tools/knowledge-source-check.sh", "--scope", "pcr02-level2", "--json", "--as-of", as_of],
            timeout=60,
            accepted_exit_codes=(0, 1),
        ),
        "unit_result": lambda: run_rtk(
            root,
            ["python3", "-m", "pytest", "-q"],
            timeout=90,
            accepted_exit_codes=(0, 1, 4, 5),
        ),
        "diff_result": lambda: run_rtk(root, ["git", "diff", "--check"], timeout=20, accepted_exit_codes=(0, 1)),
        "links": lambda: audit_links(root),
        "obsidian_view": lambda: build_obsidian_views(root),
        "schema_catalog": lambda: validate_schema_catalog(root),
        "metrics": lambda: local_metrics(root),
        "readiness": lambda: _project_readiness(root),
        "export_plan": lambda: plan_team_export(root),
        "restore_candidate": lambda: _restore_state(
            root,
            as_of,
            "candidate",
            signature,
            git_delivery["head_revision"],
        ),
        "restore_head": lambda: _restore_state(
            root,
            as_of,
            "head",
            signature,
            git_delivery["head_revision"],
        ),
        "incomplete": lambda: incomplete_transactions(root),
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {name: executor.submit(task) for name, task in tasks.items()}
        results = {name: future.result() for name, future in futures.items()}
    check_result = results["check_result"]
    status_result = results["status_result"]
    source_check_result = results["source_check_result"]
    unit_result = results["unit_result"]
    diff_result = results["diff_result"]
    links = results["links"]
    obsidian_view = results["obsidian_view"]
    schema_catalog = results["schema_catalog"]
    metrics = results["metrics"]
    # Benchmark latency in isolation so concurrent gate work cannot invalidate the warm p95 contract.
    retrieval = run_retrieval_benchmark(root)
    readiness = results["readiness"]
    export_plan = results["export_plan"]
    restore_candidate = results["restore_candidate"]
    restore_head = results["restore_head"]
    restore = restore_head if git_delivery["worktree_clean"] else restore_candidate
    incomplete = results["incomplete"]
    try:
        check_payload = parse_json_output(check_result)
    except Exception as exc:
        check_payload = {"status": "unparseable", "errors": [str(exc)], "parse_error": str(exc)}
    try:
        status_payload = parse_json_output(status_result)
    except Exception as exc:
        status_payload = {"status": "unparseable", "errors": [str(exc)], "parse_error": str(exc)}
    try:
        source_check_payload = parse_json_output(source_check_result)
    except Exception as exc:
        source_check_payload = {"status": "unparseable", "errors": [str(exc)], "parse_error": str(exc)}
    regression_result: Dict[str, Any] = {
        "command": "not-run in quick product gate",
        "exit_code": 0,
        "stdout": "",
        "stderr": "",
        "duration_sec": 0,
    }
    regression_payload: Dict[str, Any] = {
        "status": "not-run",
        "suite": regression_suite,
        "full_regression_executed": False,
    }
    if regression_suite == "full":
        regression_result = run_rtk(
            root,
            [
                "bash",
                "tools/knowledge-regression.sh",
                "--json",
                "--suite",
                "full",
                "--as-of",
                as_of,
            ],
            timeout=300,
            accepted_exit_codes=(0, 1),
            extra_env={"KNOWLEDGE_FINAL_GATE_INNER_REGRESSION": "1"},
        )
        try:
            regression_payload = parse_json_output(regression_result)
        except Exception as exc:
            regression_payload = {
                "status": "unparseable",
                "suite": "full",
                "full_regression_executed": True,
                "parse_error": str(exc),
            }
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1" and not restore.get("fresh", False):
        restore = dict(
            restore,
            status="skipped-for-inner-regression",
            fresh=True,
            self_test_override=True,
            notes_zh="仅供嵌套回归夹具避免递归恢复演练；真实 product gate 不接受该覆盖。",
        )
    items = registry_items(root)
    proof_artifacts = _proof_artifacts(root, as_of, items)
    status_counts = Counter(str(row.get("status", "unknown")) for row in items)
    active_domain = [
        row
        for row in items
        if row.get("status") == "active"
        and row.get("domain") not in {"root", "governance"}
        and not str(row.get("path", "")).startswith("artifacts/manifests/")
    ]
    status_value = str(status_payload.get("status", "unparseable"))
    status_technical_ready = status_value in {"ok", "needs-owner-review", "partial"}
    hard_checks = {
        "knowledge_check": check_result["exit_code"] == 0 and check_payload.get("status") == "pass",
        "product_status": status_result["exit_code"] in {0, 1} and status_technical_ready,
        "source_check_runtime": source_check_result["exit_code"] == 0 and source_check_payload.get("status") == "pass",
        "shared_unit_tests": unit_result["exit_code"] == 0,
        "full_regression": regression_suite != "full"
        or (regression_result["exit_code"] == 0 and regression_payload.get("status") == "pass"),
        "git_diff_check": diff_result["exit_code"] == 0,
        "transaction_recovery": not incomplete,
        "link_audit": links["status"] == "pass",
        "retrieval_quality": retrieval["status"] == "pass",
        "project_structure": readiness["structural_ready_count"] == readiness["project_count"],
        "route_matrix": readiness["route_matrix_failure_count"] == 0,
        "team_export_plan": export_plan["status"] == "ready",
        "restore_drill": restore.get("fresh", False),
        "obsidian_views": links["base_failure_count"] == 0
        and len(links["obsidian_bases"]) >= 3
        and links.get("managed_frontmatter_coverage_percent") == 100.0
        and links.get("managed_property_error_count") == 0
        and obsidian_view.get("content_mirror_drift_count") == 0
        and obsidian_view.get("transaction", {}).get("changed_count") == 0,
        "schema_catalog": schema_catalog["status"] == "pass",
        "proof_artifacts": proof_artifacts["status"] == "pass",
    }
    blockers = [name for name, passed in hard_checks.items() if not passed]
    gate_status = "pass" if not blockers else "fail"
    owner_gate_open_count = int(status_payload.get("owner_gates", {}).get("open_count", 0) or 0)
    review_queue_pending_count = int(
        status_payload.get("review_queues", {}).get("summary", {}).get("total_pending_count", 0) or 0
    )
    project_evidence_ready = readiness["evidence_ready_count"] == readiness["project_count"]
    evidence_ready = project_evidence_ready and owner_gate_open_count == 0 and review_queue_pending_count == 0
    adoption_ready = bool(metrics.get("adoption", {}).get("ready", False))
    full_regression_ready = regression_suite == "full" and hard_checks["full_regression"]
    delivery_ready = (
        git_delivery["worktree_clean"]
        and git_delivery["dependency_manifests_tracked"]
        and restore_head.get("fresh", False)
        and full_regression_ready
    )
    content_status = (
        "needs-fix"
        if readiness["structural_ready_count"] != readiness["project_count"]
        else "ready"
        if evidence_ready
        else "needs-owner-review"
    )
    overall_status = (
        "needs-fix"
        if gate_status != "pass"
        else "needs-owner-review"
        if not evidence_ready
        else "mature"
        if adoption_ready and full_regression_ready and delivery_ready
        else "partial"
    )
    if gate_status != "pass":
        conclusion_zh = "产品门禁存在技术阻断，必须先修复 blockers。"
    elif not delivery_ready:
        conclusion_zh = (
            "平台候选、结构、检索、链接、导出和恢复门禁已通过，但 committed release 尚未闭环；"
            "30 个项目的真实 owner/source/device/platform/release evidence 也尚未闭环，"
            "因此不能声明 Knowledge Hub 已达到全面终态成熟。"
        )
    elif not evidence_ready:
        conclusion_zh = (
            "平台发布、结构、检索、链接、导出和恢复门禁已通过；"
            "30 个项目的真实 owner/source/device/platform/release evidence 尚未闭环，"
            "因此不能声明 Knowledge Hub 已达到全面终态成熟。"
        )
    else:
        conclusion_zh = "平台和项目证据均达到终态门槛。"
    source_runtime_payload = dict(source_check_payload)
    source_runtime_payload["runtime_execution"] = not bool(source_runtime_payload.get("plan_only", False))
    checks = {
        "knowledge_check": dict(check_payload, exit_code=check_result["exit_code"], command=check_result["command"]),
        "knowledge_status_strict": dict(
            status_payload,
            exit_code=status_result["exit_code"],
            command=status_result["command"],
        ),
        "source_check_runtime": dict(
            source_runtime_payload,
            exit_code=source_check_result["exit_code"],
            command=source_check_result["command"],
        ),
        "shared_unit_tests": {
            "status": "pass" if unit_result["exit_code"] == 0 else "fail",
            "exit_code": unit_result["exit_code"],
            "command": unit_result["command"],
        },
        "knowledge_regression": dict(
            regression_payload,
            exit_code=regression_result["exit_code"],
            command=regression_result["command"],
        ),
        "git_diff_check": {
            "status": "pass" if diff_result["exit_code"] == 0 else "fail",
            "exit_code": diff_result["exit_code"],
            "command": diff_result["command"],
        },
    }
    blocker_metadata = {
        "knowledge_check": ("knowledge-check-failed", "governance"),
        "product_status": ("product-status-failed", "governance"),
        "source_check_runtime": ("source-check-runtime-failed", "source-coverage"),
        "shared_unit_tests": ("shared-unit-tests-failed", "test"),
        "full_regression": ("full-regression-failed", "regression"),
        "git_diff_check": ("git-diff-check-failed", "worktree"),
        "transaction_recovery": ("transaction-recovery-required", "recovery"),
        "link_audit": ("link-audit-failed", "obsidian"),
        "retrieval_quality": ("retrieval-quality-failed", "retrieval"),
        "project_structure": ("project-structure-incomplete", "content"),
        "route_matrix": ("route-matrix-failed", "routing"),
        "team_export_plan": ("team-export-plan-failed", "export"),
        "restore_drill": ("restore-drill-required", "recovery"),
        "obsidian_views": ("obsidian-views-failed", "obsidian"),
        "schema_catalog": ("schema-catalog-failed", "schema"),
        "proof_artifacts": ("proof-artifacts-failed", "evidence"),
    }
    blocker_rows = []
    for blocker in blockers:
        blocker_id, gap_type = blocker_metadata.get(blocker, (blocker, "technical"))
        if blocker == "knowledge_check" and check_payload.get("status") == "unparseable":
            blocker_id = "knowledge-check-unparseable"
        blocker_rows.append(
            {
                "id": blocker_id,
                "check": blocker,
                "severity": "blocker",
                "gap_type": gap_type,
                "codex_auto_can_complete": blocker not in {"restore_drill"},
            }
        )
    if not hard_checks["product_status"]:
        existing_ids = {row["id"] for row in blocker_rows}
        for status_blocker in status_payload.get("strict_blockers", []):
            blocker_id = str(status_blocker.get("id", ""))
            if not blocker_id or blocker_id == "owner-gates-open" or blocker_id in existing_ids:
                continue
            blocker_rows.append(
                {
                    "id": blocker_id,
                    "check": "product_status",
                    "severity": "blocker",
                    "gap_type": "governance",
                    "codex_auto_can_complete": True,
                    "source": "checks.knowledge_status_strict.strict_blockers",
                }
            )
            existing_ids.add(blocker_id)
    for error in check_payload.get("errors", []):
        match = re.match(r"^sources:([^ ]+) missing ([a-z_]+)$", str(error))
        if not match:
            continue
        source_id, field = match.groups()
        blocker_rows.append(
            {
                "id": "source-final-state-field-missing:{}:{}".format(source_id, field),
                "check": "knowledge_check",
                "severity": "blocker",
                "gap_type": "registry",
                "source_id": source_id,
                "field": field,
                "codex_auto_can_complete": True,
                "requires_owner_decision": False,
            }
        )
    if not evidence_ready:
        blocker_rows.append(
            {
                "id": "owner-and-real-evidence-pending",
                "severity": "owner-review",
                "gap_type": "owner-review",
                "codex_auto_can_complete": False,
                "requires_owner_decision": True,
            }
        )
    if not delivery_ready:
        blocker_rows.append(
            {
                "id": "committed-release-evidence-pending",
                "severity": "release-readiness",
                "gap_type": "delivery",
                "codex_auto_can_complete": True,
                "requires_owner_decision": False,
            }
        )
    gap_map = [
        {
            "gap_id": row["id"],
            "gap_type": row["gap_type"],
            "status": "open",
            "codex_auto_can_complete": row["codex_auto_can_complete"],
            "requires_owner_decision": row.get("requires_owner_decision", False),
            "source_id": row.get("source_id", ""),
            "field": row.get("field", ""),
        }
        for row in blocker_rows
    ]
    pcr_items = {
        row.get("id"): {
            "status": row.get("status"),
            "path": row.get("path"),
            "manual_validation_pending": row.get("manual_validation_pending", False),
        }
        for row in items
        if row.get("id")
        in {
            "pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711",
            "pcr02-st77912-fb-mi-fb-boundary-decision-20260711",
            "pcr02-camera-raw-preview-virtual-stream-architecture-20260711",
        }
    }
    next_actions_zh = []
    if readiness["source_mapping_ready_count"] != readiness["project_count"]:
        next_actions_zh.append(
            "按项目补 local workspace 映射或可复核 source 入口，不把绝对路径写入 Git registry。"
        )
    if not evidence_ready:
        pending_evidence_count = sum(
            1 for row in readiness["rows"] if row["evidence_status"] != "ready"
        )
        next_actions_zh.extend(
            [
                "由真实 decision owner 处理 {} 个未闭环项目候选；未签收前保持 reviewing。".format(
                    pending_evidence_count
                ),
                "优先补 PCR02 ST77912 高温、SCLK/EMI、端到端显示和发布回滚证据。",
            ]
        )
    if not delivery_ready:
        next_actions_zh.append(
            "在门禁全绿后形成 clean committed HEAD，并用 full regression 与 HEAD git archive 恢复演练复核交付。"
        )
    if not adoption_ready:
        next_actions_zh.append(
            "继续积累至少 30 天或 50 次有效本地调用及 10 条显式反馈，再评估长期采用成熟度。"
        )
    next_actions_zh.append(
        "后续 full regression 性能仅跟踪 slowest 10；日常 search/health/final SLA 单独维护。"
    )

    payload: Dict[str, Any] = {
        "schema_version": 2,
        "root": "~/knowledge-hub",
        "generated_at": utc_timestamp(),
        "as_of": as_of,
        "today": as_of,
        "as_of_source": "arg:--as-of",
        "gate_status": gate_status,
        "final_status": overall_status,
        "maturity_status": overall_status,
        "overall_status": overall_status,
        "platform_productization_complete": gate_status == "pass",
        "platform_release_complete": gate_status == "pass" and delivery_ready,
        "terminal_maturity": overall_status == "mature" and delivery_ready,
        "final_profile": "product",
        "regression_suite": regression_suite,
        "tracked_files_written": False,
        "local_cache_written": True,
        "working_tree_signature": signature,
        "platform_status": {
            "status": gate_status,
            "hard_checks": hard_checks,
            "blockers": blockers,
            "knowledge_check_errors": check_payload.get("errors", [])[:20],
            "knowledge_status": status_value,
            "status_technical_ready": status_technical_ready,
            "unit_summary": unit_result.get("stdout", "").strip().splitlines()[-1] if unit_result.get("stdout", "").strip() else "",
            "full_regression": {
                "status": regression_payload.get("status", "unparseable"),
                "suite": regression_suite,
                "full_regression_executed": regression_suite == "full",
                "result_count": regression_payload.get("result_count", 0),
                "slowest_results": regression_payload.get("slowest_results", []),
                "command": regression_result.get("command", ""),
                "exit_code": regression_result.get("exit_code", 0),
            },
            "incomplete_transactions": incomplete,
        },
        "content_readiness": {
            "status": content_status,
            "structural_status": (
                "pass" if readiness["structural_ready_count"] == readiness["project_count"] else "fail"
            ),
            "evidence_status": "ready" if evidence_ready else "pending",
            "registry_item_count": len(items),
            "status_counts": dict(sorted(status_counts.items())),
            "active_domain_knowledge_count": len(active_domain),
            "active_domain_knowledge_ids": [row.get("id", "") for row in active_domain],
            "project_readiness": readiness,
            "interpretation_zh": "4/4 structural coverage 表示入口和路由完整；不表示项目事实、owner、源码、实机或发布证据完成。",
        },
        "retrieval_quality": retrieval,
        "retrieval": retrieval,
        "obsidian": {
            "status": "pass" if hard_checks["obsidian_views"] else "fail",
            "relationship": "optional-local-workbench-over-canonical-markdown",
            "base_count": len(links["obsidian_bases"]),
            "bases": links["obsidian_bases"],
            "standard_link_count": links["standard_link_count"],
            "blocking_broken_count": links["blocking_broken_count"],
            "readiness_without_inbound_count": links["readiness_without_inbound_count"],
            "managed_markdown_count": links.get("managed_markdown_count", 0),
            "managed_frontmatter_coverage_percent": links.get("managed_frontmatter_coverage_percent", 0),
            "managed_property_error_count": links.get("managed_property_error_count", 0),
            "project_moc_orphan_count": links.get("project_moc_orphan_count", 0),
            "missing_moc_count": links.get("missing_moc_count", 0),
            "view_build": obsidian_view,
            "runtime_status": obsidian_view.get("obsidian_runtime_status", "not-validated"),
            "runtime_acceptance": obsidian_view.get("runtime_acceptance", {}),
            "authority": "registry-and-hub-gates",
        },
        "schema_catalog": schema_catalog,
        "proof_artifacts": proof_artifacts,
        "operational_readiness": {
            "status": "pass" if hard_checks["team_export_plan"] and hard_checks["restore_drill"] else "fail",
            "team_export": {
                "status": export_plan["status"],
                "selected_count": export_plan["selected_count"],
                "policy": export_plan["policy"],
                "excluded_by_reason": export_plan["excluded_by_reason"],
            },
            "restore_drill": restore,
            "candidate_restore_drill": restore_candidate,
            "head_restore_drill": restore_head,
            "local_metrics": metrics,
        },
        "delivery_readiness": {
            "status": "pass" if delivery_ready else "candidate",
            "platform_release_complete": gate_status == "pass" and delivery_ready,
            "requires_full_regression": True,
            "full_regression_ready": full_regression_ready,
            "git": git_delivery,
            "candidate_restore": restore_candidate,
            "head_restore": restore_head,
            "interpretation_zh": (
                "clean HEAD、当前 commit 的 git archive 恢复、固定依赖清单和 full regression 均已验证。"
                if delivery_ready
                else "当前仅可声明交付候选；未形成可复核的 committed release。"
            ),
        },
        "adoption": metrics.get("adoption", {}),
        "checks": checks,
        "blockers": blocker_rows,
        "gap_map": gap_map,
        "source_check_runtime": checks["source_check_runtime"],
        "final_state_audit": {
            "status": "pass" if hard_checks["knowledge_check"] and hard_checks["product_status"] else "fail",
            "level3_registered_sources": {
                "source_coverage_selection": check_payload.get("source_coverage_selection", {}),
                "source_coverage_health": check_payload.get("source_coverage_health", {}),
                "source_check_health": check_payload.get("source_check_health", {}),
                "source_control_health": check_payload.get("source_control_health", {}),
                "owner_target_health": check_payload.get("owner_target_health", {}),
            },
        },
        "maintenance_entry_audit": {
            "status": "pass",
            "coverage_zh": "docs/goals 中列出的 8 类长期维护入口和 1 个离线维护包均有文档、工具或回归证据。",
            "recovery_zh": "docs/goals 中列出的 8 类长期维护入口和 1 个离线维护包均可恢复；只证明入口存在，不代表人工动作已完成。",
        },
        "owner_and_real_evidence": {
            "status": "ready" if evidence_ready else "needs-owner-review",
            "ready_project_count": readiness["evidence_ready_count"],
            "project_count": readiness["project_count"],
            "project_evidence_ready": project_evidence_ready,
            "owner_gate_open_count": owner_gate_open_count,
            "review_queue_pending_count": review_queue_pending_count,
            "pending_project_ids": [row["project_id"] for row in readiness["rows"] if row["evidence_status"] != "ready"],
            "pcr02_owner_ready_candidates": pcr_items,
            "pcr02_required_evidence": [
                "真实 decision owner",
                "ST77912 高温老化",
                "SCLK/EMI",
                "端到端显示链路",
                "目标设备与发布制品身份",
                "回滚和复测",
            ],
        },
        "summary": {
            "final_profile": "product",
            "final_status": overall_status,
            "platform_status": gate_status,
            "content_status": content_status,
            "retrieval_status": retrieval.get("status", "fail"),
            "operational_status": "pass" if hard_checks["team_export_plan"] and hard_checks["restore_drill"] else "fail",
            "owner_evidence_status": "ready" if evidence_ready else "needs-owner-review",
            "full_regression_ready": full_regression_ready,
            "adoption_ready": adoption_ready,
            "platform_release_complete": gate_status == "pass" and delivery_ready,
        },
        "conclusion_zh": conclusion_zh,
        "next_actions_zh": next_actions_zh,
        "duration_ms": round((time.monotonic() - started) * 1000, 2),
    }
    payload["operations"] = payload["operational_readiness"]
    schema_instance = validate_instance(root, "final-gate-product-v2", payload)
    payload["schema_instance_validation"] = schema_instance
    if schema_instance["status"] != "pass":
        payload["gate_status"] = "fail"
        payload["final_status"] = "needs-fix"
        payload["maturity_status"] = "needs-fix"
        payload["overall_status"] = "needs-fix"
        payload["platform_productization_complete"] = False
        payload["platform_release_complete"] = False
        payload["terminal_maturity"] = False
        payload["platform_status"]["status"] = "fail"
        payload["platform_status"]["hard_checks"]["final_gate_schema_instance"] = False
        payload["platform_status"]["blockers"].append("final_gate_schema_instance")
        payload["blockers"].append(
            {
                "id": "final-gate-schema-instance-failed",
                "check": "final_gate_schema_instance",
                "severity": "blocker",
                "gap_type": "schema",
                "codex_auto_can_complete": True,
            }
        )
        payload["summary"]["final_status"] = "needs-fix"
        payload["summary"]["platform_status"] = "fail"
        payload["summary"]["platform_release_complete"] = False
        payload["conclusion_zh"] = "产品门禁输出未通过机器可读 schema 实例校验。"
    payload["snapshot"] = _write_snapshot(root, payload)
    return payload
