"""Guard current navigation without certifying historical claims or hardware."""
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("required", [
    ("同 ID 多行", "重复迁移账本", "不覆盖或重签"),
    ("identity_status", "review_status", "空白骨架不得自动补成人工已签收"),
    ("items.jsonl", "逐条登记", "body-coverage.json", "不为提高比例"),
    ("集合路径 hash 不校验正文内容", "未精确登记文本仍需", "实际检查"),
    ("expected", "planned", "pass-for-handoff", "跳过回归", "分别报告"),
])
def test_governance_history_navigation_keeps_authority_separate(required):
    text = (ROOT / "artifacts/README.md").read_text(encoding="utf-8")
    section = text.split("## Owner 准备包、现行条目与集合覆盖", 1)[1]
    assert all(value in section for value in required)
    assert "```" not in section
    assert "不自动提升 Active、改 Owner 或续期" in section


@pytest.mark.parametrize("required", [
    ("未消费", "未保持原状态", "写反", "不是当前固件已复现"),
    ("state", "code/ret", "size/hash", "总截止时间", "取消完成"),
    ("env expect=any", "零命令发现", "unauthorized", "独立运行时"),
    ("禁用格式检查", "空头文件桩", "不得用关闭门禁或伪造依赖"),
])
def test_project_snippet_findings_do_not_authorize_execution(required):
    text = (ROOT / "projects/xcrz-sigmastar-demo/README.md").read_text(encoding="utf-8")
    section = text.split("### IR 与 Diag：历史示例不得直接作为当前实现", 1)[1]
    assert all(value in section for value in required)
    assert "```" not in section
    assert "不授权源项目写入、设备测试、保护阈值修改或发布" in section
