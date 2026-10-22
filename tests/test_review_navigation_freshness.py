"""Navigation and validation templates must not fossilize a past project count or CLI."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readiness_navigation_follows_registered_project_count():
    projects = json.loads((ROOT / "registry/projects.json").read_text(encoding="utf-8"))["projects"]
    dashboard = (ROOT / "indexes/project-readiness.md").read_text(encoding="utf-8")
    table_rows = [line for line in dashboard.splitlines() if line.startswith("| [")]
    assert len(table_rows) == len(projects)

    guide = (ROOT / "indexes/README.md").read_text(encoding="utf-8")
    home = (ROOT / "indexes/obsidian-home.md").read_text(encoding="utf-8")
    assert "项目数以登记与实际生成的表格为准" in guide
    assert "30 个规范项目" not in guide
    assert "[项目成熟度工作台](project-readiness.md)" in home
    assert not re.search(r"\[\d+\s*项目成熟度工作台\]", home)


def test_daily_dashboard_does_not_replay_a_fixed_historical_date():
    home = (ROOT / "indexes/obsidian-home.md").read_text(encoding="utf-8")
    assert "--summary-json --final-profile product" in home
    assert "--as-of 2026-07-19" not in home
    assert "历史复盘才显式传入" in home
    code = (ROOT / "tools/codex_assets/knowledge_hub/final_gate_cli.py").read_text(
        encoding="utf-8"
    )
    assert 'parser.add_argument("--as-of", default="")' in code


def test_asan_validation_template_uses_supported_full_suite_argument():
    template = (ROOT / "templates/asan-validation-report.md").read_text(encoding="utf-8")
    code = (ROOT / "tools/codex_assets/knowledge_hub/final_gate_cli.py").read_text(
        encoding="utf-8"
    )
    assert "--regression-suite full" in template
    assert "--full-regression" not in template
    assert 'output.add_argument("--summary-json"' in code
    assert 'choices=("quick", "full")' in code
