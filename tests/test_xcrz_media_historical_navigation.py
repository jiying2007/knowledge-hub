"""Project navigation may prefer corrected candidates without rewriting history."""

import pathlib
import re

from tools.codex_assets.knowledge_hub.common import registry_items


ROOT = pathlib.Path(__file__).resolve().parents[1]
README = ROOT / "projects/xcrz-sigmastar-demo/README.md"

IDENTITIES = {
    "pcr02-active-low-1-profile-switch-mode-20260729":
        "current/decisions/active-low-1-profile-switch-mode.md",
    "pcr02-vi-fps-publish-validation-20260731":
        "validation/2026-07-31-vi-fps-publish-validation.md",
    "xcrz-pcr02-warm-current-workload-cmdq-debug-v2-20260815":
        "archive/debug/2026-08-15-warm-current-workload-cmdq-regression-v2.md",
    "xcrz-pcr02-warm-vif-sleep-cmdq-debug-20260814":
        "archive/debug/2026-08-14-warm-vif-sleep-cmdq-regression.md",
}


def test_low_fps_navigation_is_source_bound_and_keeps_owner_gate():
    project_root = README.parent
    text = README.read_text(encoding="utf-8")
    start = "## 低帧媒体切换的历史纠偏导航（不提供产品默认值授权）"
    assert text.count(start) == 1
    section = text.split(start, 1)[1]
    links = re.findall(r"\]\(([^)#]+\.md)\)", section)
    assert set(links) == set(IDENTITIES.values())
    by_id = {row["id"]: row for row in registry_items(ROOT)}
    for identity, relative in IDENTITIES.items():
        item = by_id[identity]
        path = (project_root / relative).resolve(strict=True)
        assert path.is_file()
        assert path.relative_to(ROOT) == pathlib.Path(item["path"])
        assert item["status"] == "reviewing"
        assert item["promotion"] == "none"
        assert item["content_review_status"] == "pending"
    assert "COLD" in section and "WARM" in section and "HOT" in section
    assert "同构建单变量 A/B" in section
    assert "不得单独据此宣称" in section
    assert "不是覆盖原始证据的整篇" in section


def test_old_and_corrected_warm_records_remain_separate_immutable_sources():
    by_id = {row["id"]: row for row in registry_items(ROOT)}
    original = by_id["xcrz-pcr02-warm-vif-sleep-cmdq-debug-20260814"]
    corrected = by_id["xcrz-pcr02-warm-current-workload-cmdq-debug-v2-20260815"]
    assert original["id"] != corrected["id"]
    old_body = (ROOT / original["path"]).read_text(encoding="utf-8")
    new_body = (ROOT / corrected["path"]).read_text(encoding="utf-8")
    assert "suspected" in old_body
    assert "根因尚未完成单变量复验" in new_body
    assert "不能直接外推" in new_body or "不能复用旧 HIL 结论" in new_body
