"""Fail-closed action classification for the read-only Operator UI."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Mapping, Sequence


HUMAN_EXECUTION_CLASSES = {
    "human-authorization",
    "real-world-evidence",
    "external-environment",
    "governance-review",
}
MACHINE_EXECUTION_CLASSES = {
    "machine-discovery",
    "machine-after-prerequisite",
    "dependency-gate",
}

_FIELD_RULES = {
    "source_refs": (
        "machine-discovery",
        "自动检索 canonical source/remote 候选；找不到时保持 open，不伪造来源。",
        "external-environment",
    ),
    "validation_refs": (
        "machine-discovery",
        "自动检索 hosted validation/CI receipt 候选；只接受可验证的真实证据。",
        "real-world-evidence",
    ),
    "artifact_refs": (
        "machine-discovery",
        "自动检索 immutable artifact 候选；不存在时保持 open，不自动制造制品。",
        "real-world-evidence",
    ),
    "release_ref": (
        "machine-discovery",
        "先自动检索现有 immutable release；不存在时不得自动发布，升级为显式授权。",
        "human-authorization",
    ),
    "rollback_ref": (
        "machine-after-prerequisite",
        "release/artifact 身份就绪后可自动执行 clean-room restore/rollback drill；前置未满足时保持阻塞。",
        "governance-review",
    ),
    "device_refs": (
        "real-world-evidence",
        "需要真实设备/目标平台证据，不能由仓库或 CI 合成。",
        "",
    ),
    "owner_ref": (
        "human-authorization",
        "需要明确的真实 owner/decision owner 绑定，不能从 routing owner 推断。",
        "",
    ),
    "member_project_ids": (
        "dependency-gate",
        "聚合项目等待真实成员项目 evidence ready；不通过补字段绕过成员依赖。",
        "",
    ),
}

_EXTERNAL_RULES = {
    "connector-provider-pilot": (
        "external-environment",
        "需要真实 provider/ACL 环境和传播回执。",
    ),
    "memory-lifecycle-pilot": (
        "real-world-evidence",
        "需要真实 memory lifecycle/isolation 运行证据。",
    ),
    "production-retrieval-eval": (
        "real-world-evidence",
        "需要真实 production-derived retrieval evaluation。",
    ),
    "real-adoption-evidence": (
        "real-world-evidence",
        "需要真实使用窗口、调用量与反馈证据。",
    ),
    "repository-private-boundary": (
        "external-environment",
        "需要 repository administrator 在真实托管环境完成 private-boundary 变更并取证。",
    ),
}

_EXECUTION_ORDER = {
    "human-authorization": 0,
    "real-world-evidence": 1,
    "external-environment": 2,
    "governance-review": 3,
    "machine-discovery": 4,
    "machine-after-prerequisite": 5,
    "dependency-gate": 6,
}


def _action(
    *,
    action_id: str,
    execution_class: str,
    summary_zh: str,
    scope: str,
    project_id: str = "",
    field: str = "",
    owner: str = "",
    escalation_class: str = "",
) -> Dict[str, Any]:
    return {
        "id": action_id,
        "scope": scope,
        "project_id": project_id,
        "field": field,
        "owner": owner,
        "execution_class": execution_class,
        "escalation_class": escalation_class,
        "summary_zh": summary_zh,
        "automatic_execution_enabled": False,
    }


def project_actions(row: Mapping[str, Any]) -> List[Dict[str, Any]]:
    project_id = str(row.get("project_id", ""))
    missing = {str(value) for value in row.get("missing_fields", []) if str(value)}
    invalid = {str(value) for value in row.get("invalid_fields", []) if str(value)}
    actions: List[Dict[str, Any]] = []
    if row.get("owner_boundary_status") != "ready" and "owner_ref" not in missing:
        actions.append(
            _action(
                action_id="{}:owner-boundary".format(project_id),
                execution_class="human-authorization",
                summary_zh="需要显式 decision owner/owner boundary；不得从 routing owner 推断。",
                scope="project",
                project_id=project_id,
                field="owner-boundary",
            )
        )
    if row.get("evidence_field_status") == "complete-awaiting-declaration":
        actions.append(
            _action(
                action_id="{}:owner-declaration".format(project_id),
                execution_class="human-authorization",
                summary_zh="evidence 字段已完整，等待授权 owner 明确声明 ready。",
                scope="project",
                project_id=project_id,
                field="owner-declaration",
            )
        )
    for field in sorted(missing):
        execution_class, summary_zh, escalation_class = _FIELD_RULES.get(
            field,
            (
                "governance-review",
                "未知 evidence 缺口；需要先确认 contract 语义，不能自动填充。",
                "",
            ),
        )
        actions.append(
            _action(
                action_id="{}:missing:{}".format(project_id, field),
                execution_class=execution_class,
                escalation_class=escalation_class,
                summary_zh=summary_zh,
                scope="project",
                project_id=project_id,
                field=field,
            )
        )
    for field in sorted(invalid):
        actions.append(
            _action(
                action_id="{}:invalid:{}".format(project_id, field),
                execution_class="governance-review",
                summary_zh="已有 evidence 字段无效；需要审计现有值而不是自动覆盖。",
                scope="project",
                project_id=project_id,
                field=field,
            )
        )
    return actions


def external_actions(external: Mapping[str, Any]) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    for row in external.get("open_gaps", []):
        if not isinstance(row, Mapping):
            continue
        gap_id = str(row.get("id", ""))
        if not gap_id:
            continue
        execution_class, summary_zh = _EXTERNAL_RULES.get(
            gap_id,
            ("external-environment", "需要真实外部环境/事实证据；不能由本仓 CI 自动关闭。"),
        )
        actions.append(
            _action(
                action_id="external:{}".format(gap_id),
                execution_class=execution_class,
                summary_zh=summary_zh,
                scope="external",
                field=gap_id,
                owner=str(row.get("owner", "")),
            )
        )
    return actions


def _sort_key(row: Mapping[str, Any]) -> tuple:
    return (
        _EXECUTION_ORDER.get(str(row.get("execution_class", "")), 99),
        str(row.get("scope", "")),
        str(row.get("project_id", "")),
        str(row.get("field", "")),
    )


def build_action_queue(
    projects: Sequence[Mapping[str, Any]], external: Mapping[str, Any]
) -> Dict[str, Any]:
    actions: List[Dict[str, Any]] = []
    for row in projects:
        project_rows = row.get("operator_actions")
        if isinstance(project_rows, list):
            actions.extend(dict(value) for value in project_rows if isinstance(value, Mapping))
        else:
            actions.extend(project_actions(row))
    actions.extend(external_actions(external))
    actions.sort(key=_sort_key)
    counts = Counter(str(row.get("execution_class", "")) for row in actions)
    human_project_ids = sorted(
        {
            str(row.get("project_id", ""))
            for row in actions
            if row.get("project_id")
            and row.get("execution_class") in HUMAN_EXECUTION_CLASSES
        }
    )
    machine_project_ids = sorted(
        {
            str(row.get("project_id", ""))
            for row in actions
            if row.get("project_id")
            and row.get("execution_class") in MACHINE_EXECUTION_CLASSES
        }
    )
    return {
        "schema_version": 1,
        "read_only": True,
        "automatic_execution_enabled": False,
        "status": "needs-attention" if actions else "pass",
        "action_count": len(actions),
        "by_execution_class": dict(sorted(counts.items())),
        "machine_candidate_count": counts.get("machine-discovery", 0),
        "machine_blocked_count": counts.get("machine-after-prerequisite", 0)
        + counts.get("dependency-gate", 0),
        "manual_action_count": sum(counts.get(name, 0) for name in HUMAN_EXECUTION_CLASSES),
        "human_project_count": len(human_project_ids),
        "human_project_ids": human_project_ids,
        "machine_project_count": len(machine_project_ids),
        "machine_project_ids": machine_project_ids,
        "actions": actions,
    }
