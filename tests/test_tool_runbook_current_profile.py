"""Tool runbook examples track the supported CLI and current project registry."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_live_final_gate_examples_use_current_date_and_supported_profile():
    content = (ROOT / "tools/README.md").read_text(encoding="utf-8")
    section = content.split("## 产品成熟度入口", 1)[1].split("## ", 1)[0]
    assert "运行当日" in section
    assert "--final-profile product" in section
    assert "--final-profile mature" not in section
    assert "--full-regression" not in section
    assert not re.search(r"--as-of\s+20\d{2}-\d\d-\d\d", section)
    cli = (ROOT / "tools/codex_assets/knowledge_hub/final_gate_cli.py").read_text(
        encoding="utf-8"
    )
    assert 'choices=("product",)' in cli
    assert 'choices=("quick", "full")' in cli


def test_project_counts_come_from_registry_not_an_old_packet():
    content = (ROOT / "tools/README.md").read_text(encoding="utf-8")
    projects = json.loads((ROOT / "registry/projects.json").read_text(encoding="utf-8"))["projects"]
    dashboard = (ROOT / "indexes/project-readiness.md").read_text(encoding="utf-8")
    assert len(projects) == len([s for s in dashboard.splitlines() if s.startswith("| [")])
    assert "当前登记的规范项目" in content
    assert "30 个规范项目" not in content
    assert "30 项目结构" not in content
    assert "历史批次中的 30 个项目" in content
    assert "后续新增项目的 Owner 决定" in content


def test_current_review_commands_do_not_hardcode_june_2026():
    content = (ROOT / "tools/README.md").read_text(encoding="utf-8")
    assert "--as-of 2026-07-13" not in content
    assert "--as-of 2026-06-22" not in content
    assert "2026-10-17 主线登记元数据" in content
    assert content.count("rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict\n") == 1
