"""Canonical template guide statements must match the governed CLI contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "templates/README.md"
CLI = ROOT / "tools/codex_assets/knowledge_hub/new_cli.py"


def test_knowledge_new_guide_vs_governed_apply_is_not_confused():
    doc = DOC.read_text(encoding="utf-8")
    cli = CLI.read_text(encoding="utf-8")
    assert "在未提供完整条目参数时是只读人工新增向导" in doc
    assert "默认行为是受治理 dry-run 计划" in doc
    assert "只有显式" in doc and "--apply" in doc
    assert "draft" in doc and "reviewing" in doc and "personal" in doc
    assert "source 写入" in doc
    assert 'parser.add_argument("--apply", action="store_true")' in cli
    assert "source registration remains review-only" in cli
    assert "knowledge-new --apply creates draft/reviewing/personal items only" in cli


def test_removed_source_status_option_is_not_promised_as_supported():
    doc = DOC.read_text(encoding="utf-8")
    cli = CLI.read_text(encoding="utf-8")
    assert "已移除" in doc and "--source-status" in doc
    assert "ERROR unknown argument: --source-status" in doc
    assert "registered-pending-classification" in doc
    assert "deprecated-pending-classification" not in doc
    assert "retired-pending-classification" not in doc
    assert 'parser.add_argument("--source-status"' not in cli


def test_active_review_identity_not_changed_by_cli_documentation():
    doc = DOC.read_text(encoding="utf-8")
    frontmatter = doc.split("---", 2)[1]
    assert "id: knowledge-hub-zh-template-set-20260618" in frontmatter
    assert "status: active" in frontmatter
    assert "review_status: human-reviewed-accepted" in frontmatter
    assert "review_after: '2026-09-18'" in frontmatter
    assert "进入" in doc and "active" in doc
    assert "不会自动提升 active" in doc
