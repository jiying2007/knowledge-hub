"""Historical release navigation must preserve provenance and qualification boundaries."""
from pathlib import Path

from tools.codex_assets.knowledge_hub.common import split_frontmatter


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects/gd32l235"
HISTORICAL = (
    "archive/release/2026-07-30-gd32l235-v1.1.40-nas-release.md",
    "archive/release/2026-08-05-gd32l235-v1.1.41-nas-release.md",
    "archive/release/2026-08-20-gd32l235-v1.2.0-nas-release.md",
    "archive/design/2026-07-13-pa12-fast-slow-charge-compatibility.md",
)


def test_gd32_release_navigation_references_real_reviewing_documents():
    readme = (PROJECT / "README.md").read_text(encoding="utf-8")
    assert "历史软件发布索引" in readme
    for relative in HISTORICAL:
        target = PROJECT / relative
        assert target.is_file()
        assert "](" + relative + ")" in readme
        metadata, body = split_frontmatter(target.read_text(encoding="utf-8"))
        assert metadata["status"] == "reviewing"
        assert metadata["promotion"] == "none"
        assert body.strip()
    assert "不等于当前量产固件" in readme
    assert "v1.1.42" in readme
    assert "不得为减少条目数而覆盖或删除" in readme


def test_gd32_pa12_archive_preserves_certification_failure_and_hardware_boundary():
    pa12 = (PROJECT / HISTORICAL[-1]).read_text(encoding="utf-8")
    assert "charge-cert profile" in pa12
    assert "未通过 flash headroom 门禁" in pa12
    assert "不能验证真实充电电流" in pa12
    release = (PROJECT / HISTORICAL[2]).read_text(encoding="utf-8")
    assert "相对 `v1.1.42`" in release
    assert "未新增真实板卡烧录" in release


def test_gd32_charging_wakeup_historical_variants_do_not_promote_current_fact():
    readme = (PROJECT / "README.md").read_text(encoding="utf-8")
    history = (
        "current/soc-low-power-contract.md",
        "archive/design/2026-07-30-smart-reserve-charge-wakeup.md",
        "archive/session/2026-08-04-power-switch-uart-handoff-implementation.md",
    )
    for relative in history:
        source = PROJECT / relative
        assert source.is_file()
        assert "](" + relative + ")" in readme
        metadata, body = split_frontmatter(source.read_text(encoding="utf-8"))
        assert metadata["status"] == "reviewing"
        assert body.strip()

    old = (PROJECT / history[0]).read_text(encoding="utf-8")
    both = (PROJECT / history[1]).read_text(encoding="utf-8")
    deep_only = (PROJECT / history[2]).read_text(encoding="utf-8")
    assert "WiFi；SoC RTC 独立有效" in old
    assert "SLEEP/DEEP_SLEEP 的强制硬件唤醒源" in both
    assert "只有 `DEEP_SLEEP` 智能留电状态支持充电恢复" in deep_only
    assert "不判定当前固件" in readme
    assert "不能仅选择日期较晚的一篇" in readme
    assert "真实 owner" in readme
