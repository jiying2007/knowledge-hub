"""The privacy parser is a trust root, even when its caller is unchanged."""
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub.review_risk import (
    classify_review_risk,
    load_review_risk_policy,
)


@pytest.mark.parametrize("path", [
    "tools/codex_assets/knowledge_hub/body_privacy.py",
    "tools/codex_assets/knowledge_hub/content_convergence.py",
    "registry/review-risk-policy.json",
])
def test_privacy_trust_root_requires_independent_security_review(path):
    policy = load_review_risk_policy(Path(__file__).resolve().parents[1])
    assert classify_review_risk(policy, path) == {
        "review_class": "security-critical",
        "stale_severity": "blocked",
        "ai_first_action": "human-review-required",
    }


@pytest.mark.parametrize("path", [
    "tests/test_body_privacy_graph.py",
    "tools/codex_assets/knowledge_hub/body_privacy_notes.md",
])
def test_privacy_trust_root_rule_does_not_widen_to_unrelated_paths(path):
    policy = load_review_risk_policy(Path(__file__).resolve().parents[1])
    assert classify_review_risk(policy, path)["review_class"] == "ordinary"
