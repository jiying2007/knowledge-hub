#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(
    prog="knowledge-mature-auto-approval.sh",
    description="Apply a narrow user-authorized mature-profile auto approval batch.",
)
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument("--dry-run", action="store_true")
mode.add_argument("--apply", action="store_true")
parser.add_argument("--json", action="store_true")
args = parser.parse_args(argv)

today = dt.date(2026, 6, 29).isoformat()
authorization_id = "auth-20260629-mature-auto-approval"
automation_run_id = "knowledge-hub-mature-auto-approval-20260629"

archive_ids = set("""
pcr02-prog-tool-ci-smoke-session-ref-20260618
chinese-developer-long-term-assets-20260618
pcr02-owner-resolution-playbook-20260618
pcr02-owner-resolution-schema-20260618
embedded-knowledge-owner-review-gate-20260619
codex-memories-auxiliary-boundary-20260619
pcr02-owner-decision-intake-execution-20260620
knowledge-hub-owner-landing-ready-gate-20260620
knowledge-hub-status-owner-landing-command-20260620
pcr02-tools-boundary-20260620
pcr02-knowledge-secret-config-boundary-20260620
pcr02-product-test-artifact-config-interface-boundary-20260620
pcr02-scratch-archive-boundary-20260620
pcr02-root-artifacts-boundary-20260620
pcr02-module-agent-rules-boundary-20260620
pcr02-agent-config-boundary-20260620
knowledge-hub-source-check-coverage-draft-20260621
knowledge-hub-source-check-docs-search-limit-20260621
knowledge-hub-owner-target-landing-validation-20260621
knowledge-hub-owner-ready-command-stability-20260621
knowledge-hub-final-gap-readability-index-20260621
knowledge-hub-owner-dispatch-readability-sync-20260621
knowledge-hub-status-dispatch-notes-zh-20260621
knowledge-hub-terminal-contract-template-sync-20260621
knowledge-hub-asof-coverage-contract-20260621
knowledge-hub-owner-routing-recovery-20260621
knowledge-hub-manifest-profile-index-plan-20260621
knowledge-hub-source-selection-owner-warning-20260621
knowledge-hub-owner-evidence-readiness-20260621
knowledge-hub-owner-landing-audit-manual-index-20260621
knowledge-hub-source-boundary-health-20260621
pcr02-product-test-artifact-config-interface-identity-20260621
pcr02-p1-source-identity-20260621
knowledge-hub-owner-landing-index-completeness-20260621
knowledge-hub-final-gate-regression-skip-blocker-20260621
pcr02-p2-archive-rule-identity-20260621
knowledge-hub-manual-entry-source-boundary-sync-20260621
pcr02-level2-source-check-execution-snapshot-20260621
knowledge-hub-manual-recovery-boundary-hardening-20260621
knowledge-hub-owner-automation-template-hardening-20260621
knowledge-hub-source-review-template-entry-hardening-20260622
knowledge-hub-owner-handoff-final-gate-hardening-20260622
knowledge-hub-final-gate-evidence-recovery-20260622
knowledge-hub-recovery-search-manual-hardening-20260622
knowledge-hub-final-proof-maintenance-hardening-20260622
knowledge-hub-owner-queue-command-hardening-20260622
knowledge-hub-final-recovery-discoverability-hardening-20260622
knowledge-hub-final-proof-summary-readability-hardening-20260622
knowledge-hub-source-check-snapshot-evidence-readability-20260622
knowledge-hub-review-after-near-due-snapshot-20260622
knowledge-hub-report-only-maintenance-tools-20260622
knowledge-hub-owner-inbox-final-gate-audit-20260622
knowledge-hub-manual-source-kind-contract-20260622
knowledge-hub-offline-manifest-profile-hardening-20260622
knowledge-hub-final-proof-runtime-recovery-hardening-20260622
knowledge-hub-owner-target-manifest-recovery-hardening-20260622
knowledge-hub-review-after-topic-owner-hardening-20260622
knowledge-hub-owner-status-review-proof-hardening-20260622
knowledge-hub-proof-search-runtime-hardening-20260622
knowledge-hub-maintenance-linking-audit-hardening-20260622
knowledge-hub-final-proof-date-rollover-hardening-20260623
knowledge-hub-owner-inbox-linking-maintenance-hardening-20260623
knowledge-hub-manual-entry-owner-personal-source-recommendation-20260623
knowledge-hub-proof-alias-owner-coverage-hardening-20260623
knowledge-hub-owner-ready-status-source-hardening-20260623
knowledge-hub-owner-archive-form-readability-hardening-20260623
knowledge-hub-final-state-handoff-supersede-20260623
knowledge-hub-review-queue-topic-readability-20260623
knowledge-hub-offline-review-queue-claiming-hardening-20260623
knowledge-hub-owner-dispatch-regression-count-hardening-20260623
knowledge-hub-owner-handoff-profile-advisory-hardening-20260623
knowledge-hub-review-queue-recovery-packet-hardening-20260623
knowledge-hub-review-queue-forms-jsonl-hardening-20260623
knowledge-hub-review-queue-forms-validation-hardening-20260623
knowledge-hub-offline-maintenance-audit-hardening-20260623
knowledge-hub-final-gate-requirement-map-hardening-20260623
pcr02-project-docs-owner-decision-landing-20260623
knowledge-hub-owner-source-subagent-boundary-hardening-20260623
knowledge-hub-simplified-main-source-coverage-20260624
knowledge-hub-git-automation-permission-20260624
knowledge-hub-user-path-boundary-20260624
knowledge-hub-canonical-registry-boundary-20260624
knowledge-hub-source-control-unification-20260624
patent-disclosure-canonical-archive-corpus
patent-disclosure-artifact-ref-manifest-20260619
""".split())

active_ids = set("""
knowledge-hub-chinese-readability-rules
knowledge-hub-glossary-rules
knowledge-hub-evidence-rules
knowledge-hub-commit-changelog-pr-rules
knowledge-hub-owner-review-rules
knowledge-hub-debug-record-rules
knowledge-hub-command-tooling-rules
knowledge-hub-external-source-absorption-rules
knowledge-hub-naming-boundaries
knowledge-hub-ai-content-labeling-rules
knowledge-hub-path-routing-rules
knowledge-hub-zh-template-set-20260618
knowledge-hub-registry-schema-readability-extension
""".split())

if archive_ids & active_ids:
    raise SystemExit("internal error: target sets overlap")

items_path = root / "registry" / "items.jsonl"
status_index_path = root / "indexes" / "by-status.md"
authorizations_path = root / "registry" / "authorizations.jsonl"
automation_runs_path = root / "registry" / "automation-runs.jsonl"

rows = []
for line_no, line in enumerate(items_path.read_text().splitlines(), 1):
    if not line.strip():
        continue
    try:
        row = json.loads(line)
    except Exception as exc:
        raise SystemExit(f"registry/items.jsonl:{line_no}: invalid JSON: {exc}")
    rows.append(row)

by_id = {str(row.get("id", "")): row for row in rows}
missing = sorted((archive_ids | active_ids) - set(by_id))
if missing:
    raise SystemExit(f"missing target ids: {missing}")

diagnostics = []
updates = []
already_applied = []

archive_review_status = {
    "patent-disclosure-canonical-archive-corpus": "archive-corpus-materialized",
}

def require(condition, code, item_id, message):
    if not condition:
        diagnostics.append({"code": code, "id": item_id, "message_zh": message})

for item_id in sorted(archive_ids):
    item = by_id[item_id]
    path = str(item.get("path", ""))
    review_status = str(item.get("review_status", ""))
    status = str(item.get("status", ""))
    require(status in {"reviewing", "archived"}, "unexpected-status", item_id, "归档批次只允许从 reviewing 转 archived，或识别已 archived 的幂等状态。")
    require(item.get("promotion") == "none", "unexpected-promotion", item_id, "归档批次不得包含 promotion 非 none 的条目。")
    is_artifact_manifest = path.startswith("artifacts/manifests/")
    is_safe_extra = item_id in {
        "pcr02-prog-tool-ci-smoke-session-ref-20260618",
        "patent-disclosure-canonical-archive-corpus",
        "patent-disclosure-artifact-ref-manifest-20260619",
    }
    require(is_artifact_manifest or is_safe_extra, "unsafe-archive-path", item_id, "归档批次只允许历史证据 manifest 或明确白名单 ref/archive 条目。")
    require(
        review_status in {"", "human-reviewed-accepted", "human-reviewed-archive-only", "owner-decision-landing-applied", "markdown-corpus-materialized", "archive-corpus-materialized"},
        "unsafe-review-status",
        item_id,
        "归档批次只允许已受托复核或已 materialized 的低风险状态。",
    )
    row = {"id": item_id, "status_before": status, "status_after": "archived"}
    if status == "archived":
        row["no_op"] = True
        already_applied.append(row)
    else:
        updates.append(row)

for item_id in sorted(active_ids):
    item = by_id[item_id]
    path = str(item.get("path", ""))
    status = str(item.get("status", ""))
    require(status in {"reviewing", "active"}, "unexpected-status", item_id, "治理规范批复只允许从 reviewing 转 active，或识别已 active 的幂等状态。")
    require(item.get("kind") == "standard", "unexpected-kind", item_id, "active 批复批次只允许 standard 条目。")
    require(item.get("promotion") == "none", "unexpected-promotion", item_id, "active 批复不改变 promotion 字段。")
    require(
        path.startswith("governance/") or path in {"templates/README.md", "registry/schema.md"},
        "unsafe-active-path",
        item_id,
        "active 批复只允许当前治理规范、模板说明或 registry schema。",
    )
    row = {"id": item_id, "status_before": status, "status_after": "active"}
    if status == "active":
        row["no_op"] = True
        already_applied.append(row)
    else:
        updates.append(row)

if diagnostics:
    result = {
        "status": "invalid",
        "applied": False,
        "diagnostic_count": len(diagnostics),
        "diagnostics": diagnostics,
        "planned_update_count": len(updates),
        "planned_updates": updates,
        "already_applied_count": len(already_applied),
        "already_applied": sorted(already_applied, key=lambda row: row["id"]),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"invalid: {len(diagnostics)} diagnostics")
    sys.exit(1)

review_basis_archive = (
    "用户在 2026-06-29 本会话明确要求按建议落地、使用 subagents 并自动批复；"
    "Codex 依据两个只读 subagent 审计结果，仅将历史审计/证据条目转 archived，"
    "不生成 owner decision、不关闭 owner gate、不提升项目 current、不写 memory、不改源项目。"
)
review_basis_active = (
    "用户在 2026-06-29 本会话明确要求自动批复；"
    "Codex 依据当前 AGENTS.md、registry/schema.md 和治理规则引用关系，"
    "仅将已作为当前控制面使用的治理规范条目批复为 active，"
    "不生成 owner decision、不关闭 owner gate、不写 memory、不改源项目。"
)

for item_id in archive_ids:
    item = by_id[item_id]
    item["status"] = "archived"
    item["updated_at"] = today
    item["human_reviewed_by"] = item.get("human_reviewed_by") or "leiwenjun-via-codex-delegation"
    item["human_reviewed_at"] = item.get("human_reviewed_at") or today
    item["review_basis"] = item.get("review_basis") or review_basis_archive
    item["human_review_decision"] = item.get("human_review_decision") or "archive-only"
    item["review_status"] = archive_review_status.get(item_id, item.get("review_status") or "human-reviewed-archive-only")
    item["promotion_decision"] = item.get("promotion_decision") or "none"

for item_id in active_ids:
    item = by_id[item_id]
    item["status"] = "active"
    item["updated_at"] = today
    item["review_status"] = "human-reviewed-accepted"
    item["human_reviewed_by"] = "leiwenjun-via-codex-delegation"
    item["human_reviewed_at"] = today
    item["review_basis"] = review_basis_active
    item["human_review_decision"] = "accept-as-review-record"
    item["promotion_decision"] = (
        "用户授权将当前治理控制面规范批复为 active；promotion 字段仍为 none，"
        "不代表 owner gate、source project write 或 memory write 授权。"
    )

status_text = status_index_path.read_text()
status_line_re = re.compile(r"^- (active|reviewing|archived|draft|superseded|rejected|personal): `([^`]+)`(.*)$")
seen_status_ids = set()
new_status_lines = []
for line in status_text.splitlines():
    match = status_line_re.match(line)
    if not match:
        new_status_lines.append(line)
        continue
    bucket, item_id, suffix = match.groups()
    seen_status_ids.add(item_id)
    if item_id in archive_ids:
        new_status_lines.append(f"- archived: `{item_id}`{suffix}")
    elif item_id in active_ids:
        new_status_lines.append(f"- active: `{item_id}`{suffix}")
    else:
        new_status_lines.append(line)

missing_index_ids = sorted((archive_ids | active_ids) - seen_status_ids)
if missing_index_ids:
    raise SystemExit(f"indexes/by-status.md missing target ids: {missing_index_ids}")

authorization_record = {
    "authorization_id": authorization_id,
    "authorized_by": "leiwenjun",
    "authorized_at": today,
    "scope": "Knowledge Hub mature profile auto approval: archive low-risk reviewed audit evidence and activate current governance standards only; no push, no owner gate closure, no memory write, no source project write.",
    "allowed_actions": ["active-promotion", "automation-apply-with-review"],
    "expires_at": "2026-06-30",
    "evidence_refs": [
        "current-session user instruction: 按建议处理落地，使用subagents，自动批复，并且给出下一步的建议",
        "subagent 019f111a-f48f-7e02-b9d1-ef63ab0981c7 reviewed blank review_status queue",
        "subagent 019f111b-50f7-77b1-8afb-541596354d76 reviewed non-empty review_status queue",
        "tools/knowledge-mature-auto-approval.sh --dry-run --json",
    ],
    "rollback_path": "git revert local commit or restore registry/items.jsonl, indexes/by-status.md, registry/authorizations.jsonl and registry/automation-runs.jsonl from pre-apply diff",
    "validation_commands": [
        "rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics",
        "rtk bash tools/knowledge-status.sh --json --final-profile mature",
        "rtk bash tools/knowledge-final-gate.sh --json",
        "rtk git diff --check",
    ],
    "status": "used" if args.apply else "planned",
}

automation_record = {
    "run_id": automation_run_id,
    "automation_id": "knowledge-hub-mature-auto-approval",
    "project_id": "knowledge-hub",
    "trigger": "user-authorized-auto-approval",
    "mode": "apply-with-subagent-review" if args.apply else "dry-run",
    "status": "completed" if args.apply else "planned",
    "started_at": today,
    "input_refs": [
        "registry/items.jsonl",
        "indexes/by-status.md",
        "current-session subagent audit results",
    ],
    "output_refs": [
        "registry/items.jsonl",
        "indexes/by-status.md",
        "registry/authorizations.jsonl",
        "registry/automation-runs.jsonl",
    ],
    "validation_refs": [
        "rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics",
        "rtk bash tools/knowledge-status.sh --json --final-profile mature",
        "rtk bash tools/knowledge-final-gate.sh --json",
        "rtk git diff --check",
    ],
    "session_id": "current-session",
    "source_ids": ["codex-history", "knowledge-hub-current"],
    "authorization_id": authorization_id,
    "rollback_ref": authorization_record["rollback_path"],
    "notes_zh": "按用户本会话授权和 subagent 只读审计结果执行 mature profile 自动批复；仅处理白名单条目，不关闭 owner gate，不提升项目 current，不写 memory，不改源项目。",
}

def append_jsonl_if_missing(path, key, value, record):
    existing = []
    if path.exists():
        existing = [line for line in path.read_text().splitlines() if line.strip()]
    for line in existing:
        try:
            if json.loads(line).get(key) == value:
                return
        except Exception:
            pass
    existing.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
    path.write_text("\n".join(existing) + "\n")

if args.apply:
    items_path.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n")
    status_index_path.write_text("\n".join(new_status_lines) + "\n")
    append_jsonl_if_missing(authorizations_path, "authorization_id", authorization_id, authorization_record)
    append_jsonl_if_missing(automation_runs_path, "run_id", automation_run_id, automation_record)

result = {
    "status": "applied" if args.apply else "planned",
    "applied": bool(args.apply),
    "archive_count": len(archive_ids),
    "active_count": len(active_ids),
    "planned_update_count": len(updates),
    "planned_updates": sorted(updates, key=lambda row: row["id"]),
    "already_applied_count": len(already_applied),
    "already_applied": sorted(already_applied, key=lambda row: row["id"]),
    "guardrails": {
        "owner_gate_mutation": False,
        "memory_write": False,
        "source_project_write": False,
        "active_project_current_promotion": False,
        "remote_publish": False,
    },
    "authorization_id": authorization_id,
    "automation_run_id": automation_run_id,
    "notes_zh": "低风险证据归档和当前治理规范 active 批复分离执行；本工具不处理项目 current、decision、runbook、tool 或 route registry。",
}
print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"{result['status']}: {len(updates)} updates")
PY
