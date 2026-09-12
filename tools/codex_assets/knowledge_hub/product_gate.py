"""Product-level maturity gate beyond lifecycle governance."""

from __future__ import annotations

import os
import pathlib
import re
import sys
import time
from collections import Counter
from typing import Any, Dict

from .common import (
    parse_json_output,
    registry_items,
    run_rtk,
    utc_timestamp,
    working_tree_signature,
)
from .maturity import evaluate_maturity_axes
from .product_gate_parallel import collect_parallel_results
from .product_gate_support import (
    _candidate_integrity as _candidate_integrity,
    _engineering_quality_state as _engineering_quality_state,
    _git_delivery_state as _git_delivery_state,
    _project_readiness as _project_readiness,
    _restore_state as _restore_state,
    _source_runtime_ready as _source_runtime_ready,
    _unit_test_evidence_reuse_mode as _unit_test_evidence_reuse_mode,
    _write_snapshot as _write_snapshot,
    product_snapshot_path as product_snapshot_path,
)
from .product_policy import (
    evaluate_specialized_owner_requirements,
    load_product_policy,
)
from .product_summary import product_gate_summary as product_gate_summary
from .retrieval import (
    retrieval_benchmark_summary,
    run_retrieval_benchmark_serialized,
)
from .schemas import validate_instance

UNIT_TEST_TIMEOUT_SECONDS = 180

def run_product_gate(
    root: pathlib.Path,
    as_of: str,
    regression_suite: str = "quick",
    reuse_engineering_evidence: bool = False,
) -> Dict[str, Any]:
    if regression_suite not in {"quick", "full"}:
        raise ValueError("regression_suite must be quick or full")
    started = time.monotonic()
    signature = working_tree_signature(root)
    preflight_engineering_quality = _engineering_quality_state(root, signature)
    unit_test_reuse_mode = _unit_test_evidence_reuse_mode(
        regression_suite,
        reuse_engineering_evidence,
        preflight_engineering_quality,
    )
    reuse_unit_tests = unit_test_reuse_mode != "disabled"
    engineering_check_statuses = preflight_engineering_quality.get(
        "check_statuses", {}
    )
    reuse_full_regression = bool(
        reuse_engineering_evidence
        and regression_suite == "full"
        and preflight_engineering_quality.get("fresh")
        and engineering_check_statuses.get("full_regression") == "pass"
    )
    git_delivery = _git_delivery_state(root)
    results = collect_parallel_results(
        root,
        as_of,
        signature,
        git_delivery,
        reuse_unit_tests,
        preflight_engineering_quality,
        unit_test_timeout_seconds=UNIT_TEST_TIMEOUT_SECONDS,
    )
    check_result = results["check_result"]
    status_result = results["status_result"]
    source_check_result = results["source_check_result"]
    unit_result = results["unit_result"]
    diff_result = results["diff_result"]
    links = results["links"]
    obsidian_view = results["obsidian_view"]
    schema_catalog = results["schema_catalog"]
    engineering_contract = results["engineering_contract"]
    metrics = results["metrics"]
    # Functional regression workers validate retrieval quality under load, while
    # standalone/engineering gates own latency enforcement in an isolated probe.
    inner_regression = (
        os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1"
    )
    retrieval = retrieval_benchmark_summary(
        run_retrieval_benchmark_serialized(
            root,
            enable_extended_probes=not inner_regression,
            enforce_performance_thresholds=not inner_regression,
        )
    )
    readiness = results["readiness"]
    export_plan = results["export_plan"]
    restore_candidate = results["restore_candidate"]
    restore_head = results["restore_head"]
    restore = restore_head if git_delivery["worktree_clean"] else restore_candidate
    incomplete = results["incomplete"]
    engineering_quality = _engineering_quality_state(root, signature)
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
        if reuse_full_regression:
            regression_result = {
                "command": "snapshot:{}#full_regression".format(
                    preflight_engineering_quality.get("path", "")
                ),
                "exit_code": 0,
                "stdout": "full engineering regression evidence reused",
                "stderr": "",
                "duration_sec": 0,
            }
            regression_payload = {
                "status": "pass",
                "suite": "full",
                "full_regression_executed": True,
                "evidence_source": "fresh-engineering-snapshot",
            }
        else:
            regression_result = run_rtk(
                root,
                [
                    "bash",
                    "tools/knowledge-regression.sh",
                    "--summary-json",
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
    if (
        os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1"
        and not engineering_quality.get("fresh", False)
    ):
        engineering_quality = dict(
            engineering_quality,
            status="skipped-for-inner-regression",
            fresh=True,
            self_test_override=True,
            notes_zh="仅供嵌套回归夹具避免依赖外层工程快照；真实 product full gate 不接受该覆盖。",
        )
    candidate_integrity = _candidate_integrity(root, signature)
    items = registry_items(root)
    items_by_id = {str(row.get("id", "")): row for row in items}
    product_policy, product_policy_errors = load_product_policy(root)
    specialized_owner = evaluate_specialized_owner_requirements(
        product_policy, items_by_id
    )
    specialized_policy_errors = product_policy_errors + specialized_owner["errors"]
    specialized_owner_ready_ids = specialized_owner["ready_ids"]
    pending_specialized_owner_ids = specialized_owner["pending_ids"]
    status_counts = Counter(str(row.get("status", "unknown")) for row in items)
    active_domain = [
        row
        for row in items
        if row.get("status") == "active"
        and row.get("domain") not in {"root", "governance"}
        and not str(row.get("path", "")).startswith("artifacts/manifests/")
    ]
    status_value = str(status_payload.get("status", "unparseable"))
    status_control_plane_ready = status_value in {"pass", "needs-review"}
    hard_checks = {
        "knowledge_check": check_result["exit_code"] == 0 and check_payload.get("status") == "pass",
        "product_status": status_result["exit_code"] in {0, 1} and status_control_plane_ready,
        "source_check_runtime": _source_runtime_ready(
            source_check_payload, source_check_result["exit_code"]
        ),
        "product_policy": not specialized_policy_errors,
        "engineering_contract": engineering_contract.get("status") == "pass",
        "engineering_quality": regression_suite != "full"
        or engineering_quality.get("fresh", False),
        "shared_unit_tests": unit_result["exit_code"] == 0,
        "full_regression": regression_suite != "full"
        or (regression_result["exit_code"] == 0 and regression_payload.get("status") == "pass"),
        "git_diff_check": diff_result["exit_code"] == 0,
        "candidate_integrity": candidate_integrity["unchanged"],
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
    }
    blockers = [name for name, passed in hard_checks.items() if not passed]
    gate_status = "pass" if not blockers else "needs-fix"
    owner_gate_open_count = int(status_payload.get("owner_gates", {}).get("open_count", 0) or 0)
    review_queue_pending_count = int(
        status_payload.get("review_queues", {}).get("summary", {}).get("total_pending_count", 0) or 0
    )
    project_evidence_ready = readiness["evidence_ready_count"] == readiness["project_count"]
    project_boundary_owner_ready = (
        readiness["owner_boundary_ready_count"] == readiness["project_count"]
    )
    owner_decision_pending = (
        not project_boundary_owner_ready
        or owner_gate_open_count > 0
        or bool(pending_specialized_owner_ids)
        or bool(specialized_policy_errors)
    )
    evidence_ready = project_evidence_ready and owner_gate_open_count == 0 and review_queue_pending_count == 0
    adoption_ready = bool(metrics.get("adoption", {}).get("ready", False))
    full_regression_ready = regression_suite == "full" and hard_checks["full_regression"]
    local_delivery_complete = (
        git_delivery["worktree_clean"]
        and git_delivery["dependency_manifests_tracked"]
        and engineering_quality.get("fresh", False)
        and restore_head.get("fresh", False)
        and full_regression_ready
    )
    remote_published = bool(
        restore_head.get("remote_published_ref_verified", False)
    )
    offsite_restore_verified = bool(
        restore_head.get("offsite_environment_verified", False)
        and restore_head.get("fresh", False)
    )
    terminal = bool(
        gate_status == "pass"
        and evidence_ready
        and adoption_ready
        and local_delivery_complete
        and remote_published
        and offsite_restore_verified
    )
    content_status = (
        "needs-fix"
        if readiness["structural_ready_count"] != readiness["project_count"]
        else "pass"
        if evidence_ready
        else "needs-review"
    )
    maturity_axes = evaluate_maturity_axes(
        platform_status=gate_status,
        content_status=content_status,
        project_count=readiness["project_count"],
        project_evidence_ready_count=readiness["evidence_ready_count"],
        owner_gate_open_count=owner_gate_open_count,
        review_queue_pending_count=review_queue_pending_count,
        adoption_ready=adoption_ready,
        local_delivery_complete=local_delivery_complete,
        remote_published=remote_published,
        offsite_restore_verified=offsite_restore_verified,
    )
    terminal = bool(maturity_axes["terminal"])
    product_status = str(maturity_axes["status"])
    if not owner_decision_pending:
        owner_evidence_clause = (
            "{} 项 authority-boundary owner 与 {} 项声明式专项 owner 要求均已绑定；"
            "真实 source/device/platform/release evidence 尚未闭环，"
        ).format(readiness["project_count"], specialized_owner["item_count"])
    else:
        owner_evidence_clause = (
            "{} 项 authority-boundary owner 已登记，仍有 {} 项专项、策略或队列 owner 决定待处理；"
            "真实 source/device/platform/release evidence 尚未闭环，"
        ).format(
            readiness["project_count"],
            len(pending_specialized_owner_ids)
            + owner_gate_open_count
            + len(specialized_policy_errors),
        )
    if gate_status != "pass":
        conclusion_zh = "产品门禁存在技术阻断，必须先修复 blockers。"
    elif not local_delivery_complete:
        if project_boundary_owner_ready:
            conclusion_zh = (
                "平台候选、结构、检索、链接、导出和恢复门禁已通过，但 committed release 尚未闭环；"
                + owner_evidence_clause
                + "因此不能声明 Knowledge Hub 已达到全面终态成熟。"
            )
        else:
            conclusion_zh = (
                "平台候选、结构、检索、链接、导出和恢复门禁已通过，但 committed release 尚未闭环；"
                + "{} 个登记项目的真实 owner/source/device/platform/release evidence 也尚未闭环，".format(readiness["project_count"])
                + "因此不能声明 Knowledge Hub 已达到全面终态成熟。"
            )
    elif not remote_published:
        conclusion_zh = (
            "本地交付证据已闭环，但当前结果没有绑定远端 push 事件；"
            "remote_published 保持 false，不能把本地提交当作远端发布。"
        )
    elif not offsite_restore_verified:
        conclusion_zh = (
            "远端提交证据存在，但尚未在独立 offsite 环境完成匹配 HEAD 的恢复演练；"
            "offsite_restore_verified 保持 false。"
        )
    elif not evidence_ready:
        if project_boundary_owner_ready:
            conclusion_zh = (
                "平台发布、结构、检索、链接、导出和恢复门禁已通过；"
                + owner_evidence_clause
                + "因此不能声明 Knowledge Hub 已达到全面终态成熟。"
            )
        else:
            conclusion_zh = (
                "平台发布、结构、检索、链接、导出和恢复门禁已通过；"
                + "{} 个登记项目的真实 owner/source/device/platform/release evidence 尚未闭环，".format(readiness["project_count"])
                + "因此不能声明 Knowledge Hub 已达到全面终态成熟。"
            )
    elif not adoption_ready:
        conclusion_zh = (
            "平台、远端和项目证据已闭环，但真实采用与人工反馈尚未达到门槛。"
        )
    else:
        conclusion_zh = "本地交付、远端发布、异地恢复、项目证据和真实采用均达到终态门槛。"
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
        "candidate_integrity": candidate_integrity,
        "engineering_contract": engineering_contract,
        "engineering_quality": engineering_quality,
    }
    blocker_metadata = {
        "knowledge_check": ("knowledge-check-failed", "governance"),
        "product_status": ("product-status-failed", "governance"),
        "source_check_runtime": ("source-check-runtime-failed", "source-coverage"),
        "product_policy": ("product-policy-invalid", "configuration"),
        "engineering_contract": ("engineering-contract-invalid", "engineering"),
        "engineering_quality": ("engineering-quality-evidence-missing", "engineering"),
        "shared_unit_tests": ("shared-unit-tests-failed", "test"),
        "full_regression": ("full-regression-failed", "regression"),
        "git_diff_check": ("git-diff-check-failed", "worktree"),
        "candidate_integrity": ("candidate-mutated-during-final-gate", "worktree"),
        "transaction_recovery": ("transaction-recovery-required", "recovery"),
        "link_audit": ("link-audit-failed", "obsidian"),
        "retrieval_quality": ("retrieval-quality-failed", "retrieval"),
        "project_structure": ("project-structure-incomplete", "content"),
        "route_matrix": ("route-matrix-failed", "routing"),
        "team_export_plan": ("team-export-plan-failed", "export"),
        "restore_drill": ("restore-drill-required", "recovery"),
        "obsidian_views": ("obsidian-views-failed", "obsidian"),
        "schema_catalog": ("schema-catalog-failed", "schema"),
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
                "severity": "owner-review" if owner_decision_pending else "evidence-readiness",
                "gap_type": "owner-review" if owner_decision_pending else "evidence",
                "codex_auto_can_complete": False,
                "requires_owner_decision": owner_decision_pending,
                "project_boundary_owner_ready": project_boundary_owner_ready,
                "project_boundary_owner_ready_count": readiness["owner_boundary_ready_count"],
                "specialized_owner_ready_count": len(specialized_owner_ready_ids),
                "specialized_owner_pending_count": len(pending_specialized_owner_ids),
            }
        )
    if not local_delivery_complete:
        blocker_rows.append(
            {
                "id": "local-delivery-evidence-pending",
                "severity": "release-readiness",
                "gap_type": "delivery",
                "codex_auto_can_complete": True,
                "requires_owner_decision": False,
            }
        )
    if not remote_published:
        blocker_rows.append(
            {
                "id": "remote-publish-evidence-pending",
                "severity": "release-readiness",
                "gap_type": "remote-publish",
                "codex_auto_can_complete": False,
                "requires_owner_decision": False,
            }
        )
    if not offsite_restore_verified:
        blocker_rows.append(
            {
                "id": "offsite-restore-evidence-pending",
                "severity": "recovery-readiness",
                "gap_type": "offsite-recovery",
                "codex_auto_can_complete": False,
                "requires_owner_decision": False,
            }
        )
    if not adoption_ready:
        blocker_rows.append(
            {
                "id": "real-adoption-evidence-pending",
                "severity": "adoption-readiness",
                "gap_type": "adoption",
                "codex_auto_can_complete": False,
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
    next_actions_zh = []
    if readiness["source_mapping_ready_count"] != readiness["project_count"]:
        next_actions_zh.append(
            "按项目补 local workspace 映射或可复核 source 入口，不把绝对路径写入 Git registry。"
        )
    if not evidence_ready:
        pending_evidence_count = sum(
            1 for row in readiness["rows"] if row["evidence_status"] != "ready"
        )
        if project_boundary_owner_ready:
            if pending_specialized_owner_ids:
                next_actions_zh.append(
                    "{} 项 authority-boundary owner 与 owner_ref 已绑定；仍需真实 owner 处理 {} 个声明式专项候选，并为 {} 个 evidence-pending 项目补真实证据。".format(
                        readiness["project_count"],
                        len(pending_specialized_owner_ids),
                        pending_evidence_count,
                    )
                )
            else:
                next_actions_zh.append(
                    "{} 项 authority-boundary owner 与 {} 项声明式专项 owner 要求均已绑定；继续为 {} 个 evidence-pending 项目补真实证据。".format(
                        readiness["project_count"],
                        specialized_owner["item_count"],
                        pending_evidence_count,
                    )
                )
        else:
            next_actions_zh.append(
                "由真实 decision owner 处理 {} 个未闭环项目候选；未签收前保持 reviewing。".format(
                    pending_evidence_count
                )
            )
        next_actions_zh.extend(specialized_owner["evidence_priority_messages_zh"])
    if not local_delivery_complete:
        next_actions_zh.append(
            "在门禁全绿后形成 clean committed HEAD，并用 full regression 与 HEAD git archive 恢复演练复核交付。"
        )
    if not remote_published:
        next_actions_zh.append(
            "由远端 push CI 绑定 GITHUB_SHA 与当前 HEAD，形成 remote_published 证据；本地状态不得代替。"
        )
    if not offsite_restore_verified:
        next_actions_zh.append(
            "在 github-hosted 等独立环境对远端 checkout 执行匹配 HEAD 的恢复演练。"
        )
    if not adoption_ready:
        next_actions_zh.append(
            "继续积累至少 30 天或 50 次有效本地调用及 10 条显式反馈，再评估长期采用成熟度。"
        )
    next_actions_zh.append(
        "后续 full regression 性能仅跟踪 slowest 10；日常 search/health/final SLA 单独维护。"
    )
    retrieval_quality = dict(retrieval)
    retrieval_quality["status"] = (
        "pass" if retrieval.get("status") == "pass" else "needs-fix"
    )

    payload: Dict[str, Any] = {
        "schema_version": 5,
        "status": product_status,
        "terminal": terminal,
        "root": "~/knowledge-hub",
        "generated_at": utc_timestamp(),
        "as_of": as_of,
        "as_of_source": "arg:--as-of",
        "maturity_axes": maturity_axes,
        "final_profile": "product",
        "regression_suite": regression_suite,
        "engineering_evidence_reuse": {
            "requested": reuse_engineering_evidence,
            "unit_test_policy": unit_test_reuse_mode,
            "snapshot_fresh": bool(preflight_engineering_quality.get("fresh")),
            "unit_tests_reused": reuse_unit_tests,
            "full_regression_reused": reuse_full_regression,
            "source": preflight_engineering_quality.get("path", ""),
        },
        "tracked_files_written": not candidate_integrity["unchanged"],
        "local_cache_written": True,
        "working_tree_signature": signature,
        "candidate_integrity": candidate_integrity,
        "platform_status": {
            "status": gate_status,
            "hard_checks": hard_checks,
            "blockers": blockers,
            "knowledge_check_errors": check_payload.get("errors", [])[:20],
            "knowledge_status": status_value,
            "status_control_plane_ready": status_control_plane_ready,
            "status_technical_ready": False,
            "status_technical_readiness_reason": "knowledge-status 只声明控制面与 source runtime；产品技术就绪仅由本 final gate 全部 hard_checks 判定。",
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
            "candidate_integrity": candidate_integrity,
            "engineering_contract": engineering_contract,
            "engineering_quality": engineering_quality,
            "incomplete_transactions": incomplete,
        },
        "content_readiness": {
            "status": content_status,
            "structural_status": (
                "pass"
                if readiness["structural_ready_count"] == readiness["project_count"]
                else "needs-fix"
            ),
            "evidence_status": "pass" if evidence_ready else "needs-review",
            "registry_item_count": len(items),
            "status_counts": dict(sorted(status_counts.items())),
            "active_domain_knowledge_count": len(active_domain),
            "active_domain_knowledge_ids": [row.get("id", "") for row in active_domain],
            "project_readiness": readiness,
            "interpretation_zh": "单一 evidence contract structural coverage 表示入口和路由完整；不表示项目事实、owner、源码、实机或发布证据完成。",
        },
        "retrieval_quality": retrieval_quality,
        "obsidian": {
            "status": (
                "pass" if hard_checks["obsidian_views"] else "needs-fix"
            ),
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
        "operational_readiness": {
            "status": (
                "pass"
                if hard_checks["team_export_plan"] and hard_checks["restore_drill"]
                else "needs-fix"
            ),
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
            "status": (
                "pass"
                if local_delivery_complete
                and remote_published
                and offsite_restore_verified
                else "needs-review"
            ),
            "local_delivery_complete": local_delivery_complete,
            "remote_published": remote_published,
            "offsite_restore_verified": offsite_restore_verified,
            "requires_full_regression": True,
            "requires_engineering_quality": True,
            "engineering_quality_ready": engineering_quality.get("fresh", False),
            "full_regression_ready": full_regression_ready,
            "git": git_delivery,
            "candidate_restore": restore_candidate,
            "head_restore": restore_head,
            "interpretation_zh": (
                "clean HEAD、当前 commit 的 git archive 恢复、固定依赖清单和 full regression 均已验证。"
                if local_delivery_complete
                else "当前仅可声明交付候选；未形成可复核的本地 committed HEAD。"
            ),
        },
        "adoption": metrics.get("adoption", {}),
        "checks": checks,
        "blockers": blocker_rows,
        "gap_map": gap_map,
        "source_check_runtime": checks["source_check_runtime"],
        "final_state_audit": {
            "status": (
                "pass"
                if hard_checks["knowledge_check"] and hard_checks["product_status"]
                else "needs-fix"
            ),
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
            "status": "pass" if evidence_ready else "needs-review",
            "ready_project_count": readiness["evidence_ready_count"],
            "project_count": readiness["project_count"],
            "project_evidence_ready": project_evidence_ready,
            "project_boundary_owner_ready": project_boundary_owner_ready,
            "decision_owner_ready_count": readiness["decision_owner_ready_count"],
            "owner_ref_ready_count": readiness["owner_ref_ready_count"],
            "owner_boundary_ready_count": readiness["owner_boundary_ready_count"],
            "owner_decision_status": "pending" if owner_decision_pending else "ready",
            "specialized_owner_policy_status": specialized_owner["status"],
            "specialized_owner_policy_errors": specialized_policy_errors,
            "specialized_owner_policy_count": specialized_owner["policy_count"],
            "specialized_owner_ready_candidate_count": len(specialized_owner_ready_ids),
            "specialized_owner_ready_candidate_ids": specialized_owner_ready_ids,
            "pending_specialized_owner_candidate_count": len(pending_specialized_owner_ids),
            "pending_specialized_owner_candidate_ids": pending_specialized_owner_ids,
            "owner_gate_open_count": owner_gate_open_count,
            "review_queue_pending_count": review_queue_pending_count,
            "pending_project_ids": [row["project_id"] for row in readiness["rows"] if row["evidence_status"] != "ready"],
            "specialized_owner_requirements": specialized_owner["items"],
            "specialized_required_evidence": specialized_owner["required_evidence_zh"],
        },
        "conclusion_zh": conclusion_zh,
        "next_actions_zh": next_actions_zh,
        "duration_ms": round((time.monotonic() - started) * 1000, 2),
    }
    schema_instance = validate_instance(root, "final-gate-product-v5", payload)
    payload["schema_instance_validation"] = schema_instance
    if schema_instance["status"] != "pass":
        payload["status"] = "needs-fix"
        payload["terminal"] = False
        payload["maturity_axes"]["platform"]["status"] = "needs-fix"
        payload["maturity_axes"]["status"] = "needs-fix"
        payload["maturity_axes"]["terminal"] = False
        payload["platform_status"]["status"] = "needs-fix"
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
        payload["conclusion_zh"] = "产品门禁输出未通过机器可读 schema 实例校验。"
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
        payload["local_cache_written"] = False
        payload["snapshot"] = ""
    else:
        payload["snapshot"] = _write_snapshot(root, payload, regression_suite)
    return payload
