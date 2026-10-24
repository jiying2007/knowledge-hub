"""Template examples must never constitute evidence, authorization, or promotion."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_inbox_template_explicitly_requires_real_classification():
    doc = (ROOT / "templates/inbox-note.md").read_text(encoding="utf-8")
    assert doc.startswith("---\n")
    assert doc.count("\n---\n") == 1
    assert "## 结论摘要" in doc
    assert "待分类草稿模板" in doc
    assert "不代表项目归属、身份或来源已验证" in doc
    for field in ("kind/domain/path/owner", "完整填写时间", "私有分类", "禁止提升 Active"):
        assert field in doc


def test_tool_asset_template_boolean_examples_are_not_trusted_evidence():
    doc = (ROOT / "templates/tool-asset-candidate.md").read_text(encoding="utf-8")
    assert doc.startswith("---\n")
    assert doc.count("\n---\n") == 1
    assert "schema: knowledge-hub.tool-asset-candidate.v1" in doc
    for flag in (
        "source_identity_verified: true",
        "sanitization.endpoint_removed: true",
        "credentials_found: false",
        "raw_logs_archived: false",
        "generated_by_ai: false",
    ):
        assert flag in doc
    assert "未验证的模板，禁止直接提交为已通过证据" in doc
    assert "不要复制示例布尔值冒充实测" in doc
    assert "team-internal" in doc
    assert "not-run" in doc and "pending" in doc


def test_templates_dont_confer_owner_or_source_permissions():
    docs = [
        (ROOT / "templates/inbox-note.md").read_text(encoding="utf-8"),
        (ROOT / "templates/tool-asset-candidate.md").read_text(encoding="utf-8"),
    ]
    assert all("禁止" in d and "证据" in d for d in docs)
    assert "不表示任何真实文件、权限、脱敏或测试已被验证" in docs[1]
