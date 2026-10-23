"""Team tool mirrors are navigation, not device command authorization."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_tool_navigation_sets_team_checkout_and_execution_boundary():
    text = (ROOT / "domains/embedded/tools/README.md").read_text(encoding="utf-8")
    for token in ("workspace://embedded-knowledge", "实际 checkout 根目录", "隔离测试介质",
                  "不代表实际设备验证", "不能从此处复制历史示例"):
        assert token in text


def test_device_pressure_examples_are_no_longer_executable_from_hub():
    doc = (ROOT / "domains/embedded/tools/debug/README.md").read_text(encoding="utf-8")
    start = doc.split("### 3) SPI NAND 压测", 1)[1].split("如果已拷回设备动态库", 1)[0]
    assert "not-run" in start
    assert "不提供可直接执行" in doc
    assert "busybox-nand-io-pressure.sh" in doc
    assert "busybox-nand-stress-suite.sh" in doc
    assert "/data/app_ota/ota_upgrade.sh" in start  # Provenance only.
    assert chr(96) * 3 not in start  # No runnable NAND stress / OTA command block.
    assert "--dmesg-mode snapshot" in doc


def test_source_control_does_not_claim_source_tool_execution_authority():
    doc = (ROOT / "sources/pcr02-project-tools/source-policy.md").read_text(encoding="utf-8")
    for token in ("工具源码与Hub文本身份", "真实脚本", "对应PCR02源码仓",
                  "脱敏、不可执行", "coverage=hub-canonical", "不表示脚本的安全性"):
        assert token in doc
    assert "不从旧工具目录复制代码" in doc


def test_other_content_and_registry_are_not_changed_by_this_contract():
    source = (ROOT / "sources/pcr02-project-tools/README.md").read_text(encoding="utf-8")
    assert "工具代码不作为 Hub 正文源" in source
    team = (ROOT / "domains/embedded/README.md").read_text(encoding="utf-8")
    assert "团队已发布规范" in team
    assert "Hub 不直接写团队仓 remote" in team
