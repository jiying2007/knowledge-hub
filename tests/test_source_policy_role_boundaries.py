"""Source control policies must keep runtime-only and canonical copy roles distinct."""

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

ROLE_EXPECTATIONS = [
    (
        "codex-history",
        ["raw history", "最小化", "不得自动复制或哈希导出", "reviewing", "active"],
    ),
    (
        "codex-raw-sessions",
        ["runtime-input-reference-summary-only", "raw session", "ACL", "defer"],
    ),
    (
        "pcr02-project-agent-config",
        ["非执行性的审查证据", "源码仓", "AGENTS.md", "运行权威"],
    ),
    (
        "pcr02-project-knowledge",
        ["registry/project-routes.json", "registry/items.jsonl", "唯一项目正文路径", "旧外部"],
    ),
]


@pytest.mark.parametrize("source_id,required", ROLE_EXPECTATIONS)
def test_source_policy_has_explicit_current_role_boundary(source_id, required):
    target = ROOT / "sources" / source_id / "source-policy.md"
    content = target.read_text(encoding="utf-8")
    assert content.count("# " + source_id + " Source 策略") == 1
    assert "## 当前策略" in content and "## 后续维护" in content
    assert "（2026-10-23）" in content
    assert all(fragment in content for fragment in required)
    assert "自动提升" not in content


def test_runtime_inputs_do_not_authorize_raw_body_copies():
    for source_id in ("codex-history", "codex-raw-sessions"):
        content = (ROOT / "sources" / source_id / "source-policy.md").read_text(encoding="utf-8")
        assert "只抽取摘要、候选和证据索引；不复制 raw 全文" in content
        assert "授权" in content
        assert "active" in content


def test_other_source_control_files_are_not_rewritten():
    # A source policy amendment is not a re-execution of a dated coverage check.
    for source_id in ("codex-history", "codex-raw-sessions", "pcr02-project-agent-config", "pcr02-project-knowledge"):
        readme = (ROOT / "sources" / source_id / "README.md").read_text(encoding="utf-8")
        coverage = (ROOT / "sources" / source_id / "coverage.md").read_text(encoding="utf-8")
        assert "## 边界" in readme
        assert "Checked at:" in coverage
        assert "2026-10-23" not in coverage
