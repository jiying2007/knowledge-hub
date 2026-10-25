"""Source file writers require the same independent approval as source governance."""

from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub.review_risk import (
    classify_review_risk,
    load_review_risk_policy,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("path", [
    "tools/codex_assets/knowledge_hub/source_control_cli.py",
    "tools/codex_assets/knowledge_hub/source_control_files.py",
])
def test_governed_source_file_writers_are_security_critical(path):
    actual = classify_review_risk(load_review_risk_policy(ROOT), path)
    assert actual == {
        "review_class": "security-critical",
        "stale_severity": "blocked",
        "ai_first_action": "human-review-required",
    }


@pytest.mark.parametrize("path", [
    "tools/codex_assets/knowledge_hub/source_control_files.py.md",
    "tests/test_source_control_atomic.py",
])
def test_exact_source_writer_rule_does_not_expand_to_unrelated_paths(path):
    actual = classify_review_risk(load_review_risk_policy(ROOT), path)
    assert actual["review_class"] == "ordinary"
