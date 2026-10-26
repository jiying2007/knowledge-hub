"""Keep dated project records from silently becoming operating authority."""
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "projects/xcrz-sigmastar-demo/README.md"


@pytest.mark.parametrize("required", [
    ("archive/reports/2026-05-29-motor-mcu-debug-record.md",
     "不得据此取消 MCU 本地保护", "尚未实现", "通信失效处理", "不选定电流或时间阈值"),
    ("decisions/gros-single-track-cross-platform-build-hard-cut-20260830-v1.md",
     "build-policy", "gros-future-boundary", "2026-09-05", "不能从旧段落"),
    ("archive/reports/2026-08-23-pcr02-aispeech-algorithm-source-analysis.md",
     "dev/vad", "master", "gain=1.6", "gain=1.25", "当前 BuildID", "资源数值的时间单位"),
    ("不改写历史正文", "review_after", "不授予源项目写入、设备操作或发布权限"),
])
def test_project_history_has_explicit_scope_and_evidence_boundaries(required):
    text = README.read_text(encoding="utf-8")
    section = text.split("## 电机、构建与音频历史记录的复用边界", 1)[1]
    assert all(value in section for value in required)
    assert "```" not in section  # No executable historic operating examples.


def test_existing_project_authority_and_version_navigation_are_retained():
    text = README.read_text(encoding="utf-8")
    for value in ("repo_id=xcrz-sigmastar-demo", "projects/pcr02-ssc305/",
                  "knowledge-hub-project-readiness:start", "knowledge-hub-project-readiness:end",
                  "hdi-hal-cross-platform-host-development-architecture-20260813-v4.md",
                  "diag-observability-maintenance-cross-platform-plane-20260813-v3.md",
                  "## 低帧媒体切换的历史纠偏导航"):
        assert value in text
