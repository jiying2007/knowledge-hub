"""Low-latency Knowledge Hub health summary."""

from __future__ import annotations

import datetime as dt
import json
import pathlib
from typing import Any, Dict, List, Mapping, Tuple

from .common import (
    KnowledgeHubError,
    load_json,
    parse_json_output,
    registry_items,
    run_rtk,
    utc_timestamp,
    working_tree_signature,
)
from .product_gate import product_snapshot_path, run_product_gate
from .store import incomplete_transactions


BODY_PREFIXES = ("projects/", "domains/", "governance/", "notes/")
EXCLUDED_BODY_PATHS = {"projects/pcr02-ssc305/archive/engineering-archive/pcr02/decision-index.md"}


def _is_body_markdown(path: str) -> bool:
    return (
        path.endswith(".md")
        and pathlib.PurePosixPath(path).name != "README.md"
        and path not in EXCLUDED_BODY_PATHS
        and path.startswith(BODY_PREFIXES)
    )


def _registry_summary(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_status: Dict[str, int] = {}
    gaps: Dict[str, int] = {}
    for item in items:
        status = str(item.get("status", ""))
        by_status[status] = by_status.get(status, 0) + 1
        if not item.get("summary_zh"):
            gaps[status] = gaps.get(status, 0) + 1
    return {
        "item_count": len(items),
        "by_status": dict(sorted(by_status.items())),
        "summary_gap_total": sum(gaps.values()),
        "summary_gap_by_status": dict(sorted(gaps.items())),
    }


def _review_queue(root: pathlib.Path) -> Dict[str, Any]:
    """Read the canonical review queue projection instead of reimplementing it."""
    result = run_rtk(
        root,
        [
            "bash",
            "tools/knowledge-index-plan.sh",
            "--section",
            "review-queue",
            "--summary-json",
        ],
        timeout=15,
        accepted_exit_codes=(0, 1),
    )
    try:
        payload = parse_json_output(result)
        summary = payload["indexes"]["by_review_queue"]["summary"]
        if not isinstance(summary, Mapping):
            raise TypeError("review queue summary must be an object")
        pending_total = int(summary.get("row_count", -1))
        ai_pending = int(summary.get("ai_generated_pending_count", -1))
        external_pending = int(summary.get("external_source_pending_count", -1))
        active_blockers = int(summary.get("active_or_promotion_blocker_count", -1))
        if min(pending_total, ai_pending, external_pending, active_blockers) < 0:
            raise ValueError("review queue summary contains invalid counts")
        parse_error = ""
    except (KeyError, KnowledgeHubError, TypeError, ValueError) as exc:
        pending_total = ai_pending = external_pending = active_blockers = 0
        parse_error = str(exc)
    return {
        "status": "pass" if result["exit_code"] == 0 and not parse_error else "fail",
        "command": result["command"],
        "exit_code": result["exit_code"],
        "pending_total": pending_total,
        "ai_generated_pending": ai_pending,
        "external_source_pending": external_pending,
        "active_or_promotion_blocker_count": active_blockers,
        "parse_error": parse_error,
        "source": "canonical-index-plan",
    }


def _review_after(items: List[Dict[str, Any]], root: pathlib.Path, as_of: dt.date) -> Dict[str, Any]:
    stale_items = 0
    for item in items:
        try:
            if dt.date.fromisoformat(str(item.get("review_after", ""))) < as_of:
                stale_items += 1
        except ValueError:
            stale_items += 1
    sources = list((load_json(root / "registry/sources.json", {}) or {}).get("sources", []))
    stale_sources = 0
    for source in sources:
        try:
            if dt.date.fromisoformat(str(source.get("review_after", ""))) < as_of:
                stale_sources += 1
        except ValueError:
            stale_sources += 1
    return {
        "stale_item_count": stale_items,
        "stale_source_count": stale_sources,
        "near_due_command": "rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --window-days 30 --json --as-of {}".format(
            as_of.isoformat()
        ),
    }


def _body_coverage(root: pathlib.Path, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    status_result = run_rtk(
        root,
        [
            "git",
            "-c",
            "core.quotePath=false",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ],
        timeout=10,
        accepted_exit_codes=(0, 128),
    )
    tracked_result = run_rtk(
        root,
        ["git", "-c", "core.quotePath=false", "ls-files", "-z"],
        timeout=10,
        accepted_exit_codes=(0, 128),
    )
    registered_paths = {str(item.get("path", "")) for item in items if item.get("path")}
    tracked = {
        path
        for path in tracked_result.get("stdout", "").split("\0")
        if path
    }
    collections = list((load_json(root / "registry/body-coverage.json", {}) or {}).get("collections", []))
    prefixes = [str(row.get("path_prefix", "")).rstrip("/") + "/" for row in collections if row.get("path_prefix")]
    changed: List[str] = []
    deleted: List[str] = []
    status_entries = status_result.get("stdout", "").split("\0")
    entry_index = 0
    while entry_index < len(status_entries):
        entry = status_entries[entry_index]
        entry_index += 1
        if len(entry) < 4:
            continue
        status_code = entry[:2]
        path = entry[3:]
        if "R" in status_code or "C" in status_code:
            entry_index += 1
        if not _is_body_markdown(path):
            continue
        if "D" in status_code or not (root / path).is_file():
            deleted.append(path)
            continue
        changed.append(path)
    missing = []
    collection_covered = []
    for path in sorted(set(changed)):
        if path in registered_paths:
            continue
        if path in tracked and any(path.startswith(prefix) for prefix in prefixes):
            collection_covered.append(path)
            continue
        missing.append(path)
    return {
        "command": status_result["command"],
        "exit_code": status_result["exit_code"],
        "status": "pass" if status_result["exit_code"] == 0 and not missing else "fail",
        "checked_count": len(set(changed)),
        "deleted_body_count": len(set(deleted)),
        "deleted_body_sample": sorted(set(deleted))[:20],
        "missing_registry_count": len(missing),
        "missing_registry": missing,
        "collection_covered_count": len(collection_covered),
        "collection_covered": collection_covered[:20],
        "parse_error": "",
        "mode": "changed-only-fast",
        "strict_followup": "rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --all --strict --json",
    }


def _reviewing_triage(items: List[Dict[str, Any]], as_of: dt.date) -> Dict[str, Any]:
    reviewing = [item for item in items if item.get("status") == "reviewing"]
    by_bucket: Dict[str, int] = {}
    by_action: Dict[str, int] = {}
    near_due = 0
    for item in reviewing:
        tags = set(str(value) for value in item.get("tags", []))
        if "owner-ready" in tags or "owner-ready-validation-pending" in tags:
            bucket, action = "owner-ready", "owner-review-and-validation"
        elif item.get("manual_validation_pending") or "manual-validation-pending" in tags:
            bucket, action = "evidence-needed", "evidence-backed-validation-pending"
        else:
            bucket, action = "routine-review", "keep-reviewing"
        by_bucket[bucket] = by_bucket.get(bucket, 0) + 1
        by_action[action] = by_action.get(action, 0) + 1
        try:
            review_date = dt.date.fromisoformat(str(item.get("review_after", "")))
            if review_date <= as_of + dt.timedelta(days=30):
                near_due += 1
        except ValueError:
            near_due += 1
    return {
        "command": "direct registry/items.jsonl triage",
        "exit_code": 0,
        "reviewing_count": len(reviewing),
        "near_due_count": near_due,
        "by_bucket": dict(sorted(by_bucket.items())),
        "by_recommended_action": dict(sorted(by_action.items())),
        "parse_error": "",
        "mode": "registry-direct-fast",
    }


def _load_snapshot_candidate(
    root: pathlib.Path,
    as_of: str,
    max_age_hours: int,
    regression_suite: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    path = product_snapshot_path(root, regression_suite)
    if not path.exists():
        return {}, {
            "state": "missing",
            "path": str(path.relative_to(root)),
            "age_seconds": None,
            "fresh": False,
            "suite": regression_suite,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, {
            "state": "invalid",
            "path": str(path.relative_to(root)),
            "age_seconds": None,
            "fresh": False,
            "suite": regression_suite,
        }
    age = max(0.0, dt.datetime.now().timestamp() - path.stat().st_mtime)
    current_signature = working_tree_signature(root)
    signature_matches = payload.get("working_tree_signature") == current_signature
    operational_readiness = payload.get("operational_readiness")
    operational_structure_valid = isinstance(operational_readiness, Mapping)
    if not operational_structure_valid:
        operational_readiness = {}
    restore_drill = operational_readiness.get("restore_drill")
    restore_structure_valid = isinstance(restore_drill, Mapping)
    if not restore_structure_valid:
        restore_drill = {}
    platform_status = payload.get("platform_status")
    platform_structure_valid = isinstance(platform_status, Mapping)
    if not platform_structure_valid:
        platform_status = {}
    engineering_quality = platform_status.get("engineering_quality")
    engineering_structure_valid = isinstance(engineering_quality, Mapping)
    if not engineering_structure_valid:
        engineering_quality = {}
    production_evidence = (
        payload.get("regression_suite") == regression_suite
        and payload.get("local_cache_written") is True
        and operational_structure_valid
        and restore_structure_valid
        and platform_structure_valid
        and engineering_structure_valid
        and not restore_drill.get("self_test_override", False)
        and not engineering_quality.get("self_test_override", False)
    )
    fresh = (
        age <= max_age_hours * 3600
        and payload.get("as_of") == as_of
        and payload.get("final_profile") == "product"
        and signature_matches
        and production_evidence
    )
    return payload, {
        "state": "fresh" if fresh else "stale",
        "path": str(path.relative_to(root)),
        "age_seconds": round(age, 1),
        "fresh": fresh,
        "signature_matches": signature_matches,
        "production_evidence": production_evidence,
        "generated_at": payload.get("generated_at", ""),
        "suite": regression_suite,
    }


def _load_snapshot(
    root: pathlib.Path,
    as_of: str,
    max_age_hours: int,
    regression_suite: str = "auto",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if regression_suite not in {"auto", "quick", "full"}:
        raise ValueError("regression_suite must be auto, quick or full")
    suites = ["full", "quick"] if regression_suite == "auto" else [regression_suite]
    candidates = [
        _load_snapshot_candidate(root, as_of, max_age_hours, suite)
        for suite in suites
    ]
    selected = next(
        (candidate for candidate in candidates if candidate[1].get("fresh")),
        None,
    )
    if selected is None:
        selected = next(
            (candidate for candidate in candidates if candidate[1].get("state") != "missing"),
            candidates[-1],
        )
    payload, metadata = selected
    metadata = dict(metadata)
    metadata["requested_suite"] = regression_suite
    metadata["candidate_states"] = {
        candidate[1]["suite"]: candidate[1]["state"]
        for candidate in candidates
    }
    return payload, metadata


def health_summary(
    root: pathlib.Path,
    as_of: dt.date,
    refresh_gate: bool = False,
    snapshot_max_age_hours: int = 24,
    gate_suite: str = "auto",
) -> Dict[str, Any]:
    if gate_suite not in {"auto", "quick", "full"}:
        raise ValueError("gate_suite must be auto, quick or full")
    items = registry_items(root)
    registry = _registry_summary(items)
    review_queue = _review_queue(root)
    review_after = _review_after(items, root, as_of)
    body_coverage = _body_coverage(root, items)
    triage = _reviewing_triage(items, as_of)
    if refresh_gate:
        run_product_gate(
            root,
            as_of.isoformat(),
            regression_suite="quick" if gate_suite == "auto" else gate_suite,
        )
    snapshot, snapshot_meta = _load_snapshot(
        root,
        as_of.isoformat(),
        snapshot_max_age_hours,
        regression_suite=gate_suite,
    )
    selected_suite = str(snapshot_meta.get("suite", "quick"))
    final_gate = {
        "command": "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite {} --as-of {}".format(
            selected_suite,
            as_of.isoformat(),
        ),
        "exit_code": None if not snapshot else (0 if snapshot.get("gate_status") == "pass" else 1),
        "final_status": snapshot.get("overall_status", "snapshot-missing"),
        "parse_error": "",
        "blocker_count": len(snapshot.get("blockers", [])) if snapshot else 0,
        "gap_count": len(snapshot.get("gap_map", [])) if snapshot else 0,
        "snapshot": snapshot_meta,
    }
    owner = snapshot.get("owner_and_real_evidence", {}) if snapshot else {}
    incomplete = incomplete_transactions(root)
    health_status = "ok"
    if (
        registry["summary_gap_total"]
        or body_coverage["missing_registry_count"]
        or review_queue["status"] != "pass"
        or review_queue["active_or_promotion_blocker_count"]
        or incomplete
    ):
        health_status = "needs-fix"
    elif not snapshot_meta["fresh"] or snapshot.get("gate_status") != "pass":
        health_status = "needs-fix"
    elif snapshot.get("overall_status") in {"needs-owner-review", "partial"}:
        health_status = str(snapshot["overall_status"])
    output = {
        "schema_version": 2,
        "read_only": True,
        "tracked_files_written": False,
        "root": "~/knowledge-hub",
        "generated_at": utc_timestamp(),
        "as_of": as_of.isoformat(),
        "final_profile": "product",
        "health_status": health_status,
        "registry": registry,
        "review_queue": review_queue,
        "review_after": review_after,
        "changed_orphan_files": body_coverage,
        "reviewing_triage": triage,
        "owner_gates": {
            "open_count": int(owner.get("owner_gate_open_count", 0) or 0),
            "pending_project_count": len(owner.get("pending_project_ids", [])),
            "review_queue_pending_count": int(owner.get("review_queue_pending_count", 0) or 0),
            "active_exposure_count": 0,
            "snapshot_available": bool(snapshot),
        },
        "product_maturity": {
            "platform_status": (snapshot.get("platform_status") or {}).get("status", "snapshot-missing"),
            "overall_status": snapshot.get("overall_status", "snapshot-missing"),
            "platform_productization_complete": snapshot.get("platform_productization_complete", False),
            "local_delivery_complete": snapshot.get("local_delivery_complete", False),
            "remote_published": snapshot.get("remote_published", False),
            "offsite_restore_verified": snapshot.get("offsite_restore_verified", False),
            "adoption_ready": snapshot.get("adoption_ready", False),
            "terminal": snapshot.get("terminal", False),
            "snapshot_suite": selected_suite,
            "full_regression_evidence": selected_suite == "full" and snapshot_meta["fresh"],
        },
        "status_dashboard": {
            "command": "snapshot:{}".format(snapshot_meta["path"]),
            "exit_code": None if not snapshot else (0 if snapshot.get("gate_status") == "pass" else 1),
            "status": snapshot.get("gate_status", "snapshot-missing"),
            "strict_blocker_count": len((snapshot.get("platform_status") or {}).get("blockers", [])),
            "parse_error": "",
        },
        "transaction_recovery": {"status": "pass" if not incomplete else "fail", "incomplete": incomplete},
        "final_gate": final_gate,
        "must_not": [
            "不生成 owner decision",
            "不关闭 owner gate",
            "不提升 active",
            "不写 memory",
            "不修改源项目",
        ],
    }
    return output
