import json

import pytest

from tools.codex_assets.knowledge_hub import terminal_closure
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


def _write_debt(tmp_path, *, baseline=11, current=10, history=None):
    if history is None:
        history = [11, 10]
    path = tmp_path / "registry/legacy-debt-burndown.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "oversized_modules": {
                    "baseline_count": baseline,
                    "current_upper_bound_count": current,
                    "ratchet_history": [
                        {"upper_bound_count": value} for value in history
                    ],
                },
                "legacy_artifact_references": {"baseline_count": 315},
            }
        ),
        encoding="utf-8",
    )
    return {"source": "registry/legacy-debt-burndown.json"}


def test_legacy_debt_ratchet_preserves_historical_baseline_and_enforces_current_ceiling(tmp_path):
    limits = terminal_closure._legacy_limits(tmp_path, _write_debt(tmp_path))

    assert limits == {
        "modules": 10,
        "modules_baseline": 11,
        "refs": 315,
        "refs_baseline": 315,
    }


def test_legacy_debt_ratchet_rejects_upward_step(tmp_path):
    bounded = _write_debt(tmp_path, current=11, history=[11, 10, 11])

    with pytest.raises(KnowledgeHubError, match="non-increasing"):
        terminal_closure._legacy_limits(tmp_path, bounded)


def test_legacy_debt_ratchet_rejects_current_ceiling_above_baseline(tmp_path):
    bounded = _write_debt(tmp_path, baseline=11, current=12, history=[11, 12])

    with pytest.raises(KnowledgeHubError, match="may not exceed historical baseline"):
        terminal_closure._legacy_limits(tmp_path, bounded)


def test_legacy_debt_ratchet_rejects_history_current_mismatch(tmp_path):
    bounded = _write_debt(tmp_path, current=10, history=[11, 9])

    with pytest.raises(KnowledgeHubError, match="must match latest ratchet"):
        terminal_closure._legacy_limits(tmp_path, bounded)
