"""Low-latency Knowledge Hub health summary."""

from __future__ import annotations

import datetime as dt
import json
import pathlib
from typing import Any, Dict, List, Mapping, Set, Tuple

from .common import load_json, registry_items, repository_root, run_rtk, source_id, utc_timestamp, working_tree_signature
from .product_gate import product_snapshot_path, run_product_gate
from .store import incomplete_transactions


BODY_PREFIXES = ("projects/", "domains/", "governance/", "notes/")
EXCLUDED_BODY_PATHS = {"projects/pcr02/archive/engineering-archive/pcr02/decision-index.md"}


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


def _review_queue(items: List[Dict[str, Any]]) -> Dict[str, int]:
    ai_pending = 0
    external_pending = 0
    active_blockers = 0
    for item in items:
        status = str(item.get("status", ""))
        decision = str(item.get("human_review_decision", ""))
        review_status = str(item.get("review_status", ""))
        pending = not decision or decision in {"needs-edits", "defer"}
        queue_eligible = status in {"draft", "reviewing"}
        if queue_eligible and item.get("generated_by_ai") and pending:
            ai_pending += 1
        if queue_eligible and item.get("kind") == "external-source-note" and pending and not item.get("generated_by_ai"):
            external_pending += 1
        if status == "active" and (pending or "pending" in review_status):
            active_blockers += 1
    return {
        "pending_total": ai_pending + external_pending,
        "ai_generated_pending": ai_pending,
        "external_source_pending": external_pending,
        "active_or_promotion_blocker_count": active_blockers,
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
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        timeout=10,
        accepted_exit_codes=(0, 128),
    )
    tracked_result = run_rtk(root, ["git", "ls-files"], timeout=10, accepted_exit_codes=(0, 128))
    registered_paths = {str(item.get("path", "")) for item in items if item.get("path")}
    tracked = {line.strip() for line in tracked_result.get("stdout", "").splitlines() if line.strip()}
    collections = list((load_json(root / "registry/body-coverage.json", {}) or {}).get("collections", []))
    prefixes = [str(row.get("path_prefix", "")).rstrip("/") + "/" for row in collections if row.get("path_prefix")]
    changed: List[str] = []
    for line in status_result.get("stdout", "").splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if _is_body_markdown(path):
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
        "missing_registry_count": len(missing),
        "missing_registry": missing,
        "collection_covered": collection_covered,
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


def _load_snapshot(root: pathlib.Path, as_of: str, max_age_hours: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    path = product_snapshot_path(root)
    if not path.exists():
        return {}, {"state": "missing", "path": str(path.relative_to(root)), "age_seconds": None, "fresh": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, {"state": "invalid", "path": str(path.relative_to(root)), "age_seconds": None, "fresh": False}
    age = max(0.0, dt.datetime.now().timestamp() - path.stat().st_mtime)
    current_signature = working_tree_signature(root)
    signature_matches = payload.get("working_tree_signature") == current_signature
    fresh = (
        age <= max_age_hours * 3600
        and payload.get("as_of") == as_of
        and payload.get("final_profile") == "product"
        and signature_matches
    )
    return payload, {
        "state": "fresh" if fresh else "stale",
        "path": str(path.relative_to(root)),
        "age_seconds": round(age, 1),
        "fresh": fresh,
        "signature_matches": signature_matches,
        "generated_at": payload.get("generated_at", ""),
    }


def health_summary(
    root: pathlib.Path,
    as_of: dt.date,
    refresh_gate: bool = False,
    skip_final_gate: bool = False,
    snapshot_max_age_hours: int = 24,
) -> Dict[str, Any]:
    items = registry_items(root)
    registry = _registry_summary(items)
    review_queue = _review_queue(items)
    review_after = _review_after(items, root, as_of)
    body_coverage = _body_coverage(root, items)
    triage = _reviewing_triage(items, as_of)
    if refresh_gate and not skip_final_gate:
        run_product_gate(root, as_of.isoformat(), regression_suite="quick")
    snapshot, snapshot_meta = _load_snapshot(root, as_of.isoformat(), snapshot_max_age_hours)
    review_queue["source"] = "registry-direct-fast"
    final_gate = {
        "skipped": skip_final_gate,
        "command": "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of {}".format(
            as_of.isoformat()
        ),
        "exit_code": None if skip_final_gate or not snapshot else (0 if snapshot.get("gate_status") == "pass" else 1),
        "final_status": "skipped" if skip_final_gate else snapshot.get("overall_status", "snapshot-missing"),
        "parse_error": "",
        "blocker_count": len(snapshot.get("blockers", [])) if snapshot else 0,
        "gap_count": len(snapshot.get("gap_map", [])) if snapshot else 0,
        "snapshot": snapshot_meta,
    }
    owner = snapshot.get("owner_and_real_evidence", {}) if snapshot else {}
    incomplete = incomplete_transactions(root)
    health_status = "ok"
    if registry["summary_gap_total"] or body_coverage["missing_registry_count"] or incomplete:
        health_status = "needs-fix"
    elif not skip_final_gate and (not snapshot_meta["fresh"] or snapshot.get("gate_status") != "pass"):
        health_status = "needs-fix"
    elif not skip_final_gate and snapshot.get("overall_status") in {"needs-owner-review", "partial"}:
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
            "terminal_maturity": snapshot.get("terminal_maturity", False),
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
