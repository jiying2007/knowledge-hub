"""Archived embedded mirrors must not be treated as live team standards."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "domains/embedded/README.md"


def test_archived_verified_mirror_does_not_gain_publication_authority():
    body = ENTRY.read_text(encoding="utf-8")
    section = body.split("## 旧归档规范的适用性警示（2026-10-25）", 1)[1].split(
        "## Hub 候选门禁", 1
    )[0]
    for required in (
        "maturity: verified", "status: archived", "searchable: false",
        "不得", "团队发布权限", "当前生效", "旧团队仓",
    ):
        assert required in section
    assert "绝不在 Hub 镜像执行或据此发布" in section
    assert "不更新 Owner/Active/" in section
    assert "不授权设备、发布、源仓写入" in section


def test_legacy_archive_identifiers_and_sdk_ratings_are_explicitly_qualified():
    body = ENTRY.read_text(encoding="utf-8")
    for text in (
        "__API_LIST_H__", "_List_t", "_LIST_IsEmpty",
        "C/C++ 实现保留标识符", "不能直接复制到新代码",
        "scripts/release.sh", "完整／强／中", "不是最新SDK",
        "<PID>", "参数占位",
    ):
        assert text in body
    for path in (
        "standards/c-coding-standards.md",
        "standards/release-versioning-guide.md",
        "governance/docs-index.md",
        "architecture/sigmastar-platform-capability-matrix.md",
        "standards/thread-troubleshooting-optimization.md",
    ):
        assert (ENTRY.parent / path).is_file()
        assert f"]({path})" in body


def test_current_navigation_and_governed_promotion_remain_intact():
    body = ENTRY.read_text(encoding="utf-8")
    assert "workspace://embedded-knowledge" in body
    assert "docs/governance/promotion-contract.md" in body
    assert "## 首次使用" in body
    assert "## Hub 候选门禁" in body
    assert "## 发布边界" in body
    assert "不自动 commit/push/merge/tag" in body
