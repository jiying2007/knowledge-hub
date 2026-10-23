"""Archived Codex and embedded team entrypoints must retain runtime boundaries."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_codex_archive_has_only_supported_product_gate_arguments():
    doc = (ROOT / "domains/codex/archive/codex-archive/README.md").read_text(encoding="utf-8")
    cli = (ROOT / "tools/codex_assets/knowledge_hub/final_gate_cli.py").read_text(encoding="utf-8")
    assert "--final-profile product --regression-suite full" in doc
    assert "--final-profile mature" not in doc
    assert "--full-regression" not in doc
    assert 'choices=("product",)' in cli
    assert 'choices=("quick", "full")' in cli


def test_embedded_team_skill_commands_are_not_hub_checkout_commands():
    doc = (ROOT / "domains/embedded/README.md").read_text(encoding="utf-8")
    assert "workspace://embedded-knowledge" in doc
    assert "对应的实际团队仓 checkout 根目录执行" in doc
    assert "不得直接在 Knowledge Hub 镜像中执行" in doc
    assert "docs/templates/" in doc and "docs/AGENTS.md" in doc


def test_candidate_and_team_publishing_authority_remain_distinct():
    doc = (ROOT / "domains/embedded/README.md").read_text(encoding="utf-8")
    for phrase in (
        "嵌入式候选与 provenance 域", "团队已发布规范", "不自动 commit/push/merge/tag",
        "不代表团队技能已发布或测试通过",
    ):
        assert phrase in doc
