"""Historical dangerous runbooks are gated by current navigation warnings."""
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
ENTRY=ROOT/"domains/embedded/README.md"


@pytest.mark.parametrize("path,phrases",[
    ("runbooks/core-dump-capture-guide.md", ("suid_dumpable","core_pattern","chmod 1777","不得执行")),
    ("runbooks/crash-bundle-collection-guide.md", ("原始core","公开Issue","受控引用")),
    ("runbooks/spi-nand-busybox-io-stress-guide.md", ("--extra-cmd","pkill -f","rm -rf","--dmesg-mode clear","断电前")),
    ("runbooks/server-hook-setup-guide.md", ("自托管bare Git服务器","GitHub受保护","Security/Quality")),
])
def test_historical_risky_ops_require_explicit_boundary(path, phrases):
    doc=ENTRY.read_text(encoding="utf-8")
    current=doc.split("## 历史高风险操作的执行阻断（2026-10-25）",1)[1].split("## Hub 候选门禁",1)[0]
    assert (ENTRY.parent/path).is_file()
    assert f"]({path})" in current
    for word in phrases:
        assert word in current


def test_warning_is_not_a_new_execution_or_authorization():
    doc=ENTRY.read_text(encoding="utf-8")
    warning=doc.split("## 历史高风险操作的执行阻断（2026-10-25）",1)[1].split("## Hub 候选门禁",1)[0]
    assert "不是可直接复制执行的当前步骤" in warning
    assert "不修改任何历史正文" in warning
    assert "没有真实执行/制品证明" in warning
    assert "## 旧归档规范的适用性警示" in doc
    assert "## 发布边界" in doc
    assert "workspace://embedded-knowledge" in doc
