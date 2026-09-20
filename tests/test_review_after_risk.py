from __future__ import annotations

import json
import pathlib
import subprocess
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub.review_risk import (
    classify_review_risk,
    load_review_risk_policy,
)


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "tools/codex_assets/knowledge_hub/review_after_cli.py"


def test_review_after_risk_classifies_security_and_ordinary(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir()
    (tmp_path / "artifacts/manifests").mkdir(parents=True)
    (tmp_path / "SECURITY.md").write_text("# security\n", encoding="utf-8")
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes/note.md").write_text("# note\n", encoding="utf-8")
    rows = [
        {
            "id": "security",
            "path": "SECURITY.md",
            "owner": "owner",
            "status": "active",
            "review_after": "2026-09-01",
            "source": {},
        },
        {
            "id": "ordinary",
            "path": "notes/note.md",
            "owner": "owner",
            "status": "active",
            "review_after": "2026-09-01",
            "source": {},
        },
    ]
    (registry / "items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    (registry / "sources.json").write_text('{"sources": []}\n', encoding="utf-8")
    (registry / "review-risk-policy.json").write_text(
        json.dumps(
            {
                "default_class": "ordinary",
                "classes": {
                    "ordinary": {
                        "stale_severity": "warning",
                        "ai_first_action": "auto-triage",
                    },
                    "security-critical": {
                        "stale_severity": "blocked",
                        "ai_first_action": "human-review-required",
                    },
                },
                "rules": [
                    {"path": "SECURITY.md", "review_class": "security-critical"}
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "artifacts/manifests/example-owner-decision-worksheets-1.jsonl").write_text(
        "", encoding="utf-8"
    )

    result = subprocess.run(
        ["rtk", "python3", str(SCRIPT), str(tmp_path), "--json", "--as-of", "2026-09-18"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    by_id = {row["item_id"]: row for row in payload["rows"]}
    assert by_id["security"]["review_class"] == "security-critical"
    assert by_id["security"]["stale_severity"] == "blocked"
    assert by_id["ordinary"]["review_class"] == "ordinary"
    assert payload["groups"]["by_review_class"]["security-critical"]["count"] == 1


def test_ai_operations_policy_is_security_critical():
    root = Path(__file__).resolve().parents[1]
    policy = load_review_risk_policy(root)

    result = classify_review_risk(
        policy,
        "registry/ai-operations-policy.json",
    )

    assert result["review_class"] == "security-critical"
    assert result["stale_severity"] == "blocked"
    assert result["ai_first_action"] == "human-review-required"


@pytest.mark.parametrize(
    "path_value",
    [
        "registry/ai-operations-policy.json",
        "registry/review-risk-policy.json",
        "schemas/ai-operations-policy.schema.json",
        "schemas/review-risk-policy.schema.json",
        "schemas/security-change-review.schema.json",
    ],
)
def test_trust_root_policies_are_security_critical(path_value):
    root = Path(__file__).resolve().parents[1]
    policy = load_review_risk_policy(root)

    result = classify_review_risk(policy, path_value)

    assert result["review_class"] == "security-critical"
    assert result["stale_severity"] == "blocked"
    assert result["ai_first_action"] == "human-review-required"


@pytest.mark.parametrize(
    "path_value",
    [
        ".github/workflows/quality.yml",
        ".github/workflows/security-critical-change-review.yml",
        "registry/authorizations.jsonl",
        "schemas/authorization.schema.json",
        "tools/codex_assets/knowledge_hub/authorization.py",
        "tools/codex_assets/knowledge_hub/review_attestation.py",
        "tools/codex_assets/knowledge_hub/review_risk.py",
        "tools/codex_assets/knowledge_hub/security_change_review.py",
        "tools/codex_assets/knowledge_hub/schemas.py",
        "tools/codex_assets/knowledge_hub/hosting_posture.py",
        "tools/codex_assets/knowledge_hub/terminal_closure.py",
        "tools/codex_assets/knowledge_hub/terminal_hosted_evidence.py",
        "tools/codex_assets/knowledge_hub/repository_private_ratchet.py",
        "tools/codex_assets/knowledge_hub/operator_auto_route.py",
        "tools/codex_assets/knowledge_hub/operator_machine_ratchet.py",
        "tools/codex_assets/knowledge_hub/operator_machine_ratchet_verify.py",
        "tools/codex_assets/knowledge_hub/external_evidence.py",
        "tools/codex_assets/knowledge_hub/external_evidence_ratchet.py",
        "tools/codex_assets/knowledge_hub/external_evidence_ratchet_verify.py",
    ],
)
def test_execution_trust_roots_are_security_critical(path_value):
    root = Path(__file__).resolve().parents[1]
    policy = load_review_risk_policy(root)

    result = classify_review_risk(policy, path_value)

    assert result["review_class"] == "security-critical"
    assert result["stale_severity"] == "blocked"
    assert result["ai_first_action"] == "human-review-required"
