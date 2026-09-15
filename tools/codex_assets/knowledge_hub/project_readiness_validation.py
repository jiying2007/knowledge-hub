"""Validation-body semantics for deterministic project readiness assets."""

from __future__ import annotations

from typing import Any, List, Mapping

from .common import KnowledgeHubError
from .evidence import project_evidence_profile


PROFILE_VALIDATION_EXPECTATIONS = {
    "embedded-target": (
        "工程验证：在源项目运行适用的构建、单元/集成测试并保留命令、版本和日志摘要。",
        "设备验证：需要硬件行为的结论必须补 HIL/实机、环境条件和可复现实验记录。",
        "发布验证：记录制品身份、版本、回滚路径和端到端验收，不以 Hub 文档替代发布签收。",
    ),
    "software-tool": (
        "工具验证：覆盖 CLI help、错误码、输入边界、制品 hash 和目标平台 smoke test。",
        "发布验证：覆盖可安装/可运行制品、版本信息、回滚和消费者兼容性。",
    ),
    "runtime-assets": (
        "运行态验证：执行声明式 build/doctor/plan/dry-run/apply/check 链路并保留回滚证据。",
    ),
    "control-plane": (
        "控制面验证：执行 check、unit、retrieval、route、link、export 和 restore drill。",
    ),
    "aggregate-group": (
        "项目组验证：每个成员项目分别补齐所需真实证据，组级结论不得替代成员项目 readiness。",
    ),
}


def _expectation_marker(text: str) -> str:
    return text.split("：", 1)[0] + "："


def validation_expectations(
    project: Mapping[str, Any], extension: Mapping[str, Any]
) -> List[str]:
    profile = project_evidence_profile(project)
    rows = [
        "Hub 结构验证：registry、route、正文镜像、链接和检索矩阵通过。",
        "来源验证：确认 Git remote key、当前分支/版本和源码事实，Hub 不代替源仓事实。",
        "责任验证：由真实 decision owner 明确接受、修改或拒绝边界候选。",
    ]
    rows.extend(PROFILE_VALIDATION_EXPECTATIONS[profile])
    rows.extend(str(value) for value in extension.get("validation_expectations_zh", []))
    return rows


def validate_existing_validation_body(
    project: Mapping[str, Any], text: str
) -> None:
    project_id = str(project["id"])
    expected_route = "- [x] 项目 route matrix 能将 `{}` 稳定解析为本项目。".format(
        project_id
    )
    if expected_route not in text:
        raise KnowledgeHubError(
            "existing readiness route statement drift: {}".format(project_id)
        )

    profile = project_evidence_profile(project)
    expected_rows = set(PROFILE_VALIDATION_EXPECTATIONS[profile])
    all_rows = {
        row
        for rows in PROFILE_VALIDATION_EXPECTATIONS.values()
        for row in rows
    }
    all_markers = {_expectation_marker(row) for row in all_rows}
    expected_markers = {_expectation_marker(row) for row in expected_rows}
    actual_markers = {
        _expectation_marker(line[6:])
        for line in text.splitlines()
        if line.startswith(("- [ ] ", "- [x] "))
        and "：" in line[6:]
        and _expectation_marker(line[6:]) in all_markers
    }
    missing_markers = expected_markers - actual_markers
    stale_generated = sorted(
        row
        for row in all_rows - expected_rows
        if "- [ ] {}".format(row) in text
    )
    if missing_markers or stale_generated:
        raise KnowledgeHubError(
            "existing readiness evidence-profile statement drift: {} missing={} stale_generated={}".format(
                project_id,
                sorted(missing_markers),
                stale_generated,
            )
        )
