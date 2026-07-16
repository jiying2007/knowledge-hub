import json

from tools.codex_assets.knowledge_hub.proposal_routing import (
    assess_proposal,
    record_shadow_assessment,
)
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def _root(tmp_path, policy):
    (tmp_path / "registry").mkdir()
    (tmp_path / "registry/items.jsonl").write_text("")
    (tmp_path / "registry/agent-review-policy.json").write_text(json.dumps(policy))
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes/source.md").write_text("Observed the exact behavior.\n")
    return tmp_path


def _policy(enabled=False):
    return {
        "schema_version": 1,
        "mode": "shadow",
        "enabled": enabled,
        "trusted_clients": ["host:collector"] if enabled else [],
        "eligible_kinds": ["debug-record"] if enabled else [],
        "eligible_runtime_roles": ["assertion"],
        "daily_limit": 10 if enabled else 0,
        "human_sample_percent": 0 if enabled else 100,
        "sample_seed": "fixture",
        "evidence_verifier": "hub-file-exact-quote",
        "target_status": "reviewing",
    }


def _proposal():
    return {
        "id": "observed-behavior",
        "kind": "debug-record",
        "status": "reviewing",
        "promotion": "none",
        "agent_contract": {
            "schema_version": 1,
            "role": "assertion",
            "force": "advisory",
            "capabilities": ["shadow_auto_stage_eligible"],
        },
        "evidence": {
            "source_path": "notes/source.md",
            "quote": "Observed the exact behavior.",
        },
    }


def test_default_disabled_policy_keeps_everything_human_review(tmp_path):
    root = _root(tmp_path, _policy(False))
    result = assess_proposal(root, _proposal(), client_id="host:collector")
    assert result["actual_route"] == "human-review"
    assert result["eligible_route"] == "human-review"
    assert "policy_disabled" in result["reason_codes"]


def test_enabled_policy_only_reports_shadow_auto_stage_eligibility(tmp_path):
    root = _root(tmp_path, _policy(True))
    result = assess_proposal(
        root,
        _proposal(),
        client_id="host:collector",
        write_auto_granted=True,
    )
    assert result["eligible_route"] == "auto-stage-reviewing"
    assert result["actual_route"] == "human-review"
    assert result["would_apply_with_write_auto"] is True
    assert result["authority_contract"]["can_promote_active"] is False
    assert validate_instance(repository_root(), "agent-proposal-route-v1", result)["status"] == "pass"


def test_shadow_audit_stores_no_proposal_content_or_identity(tmp_path):
    root = _root(tmp_path, _policy(True))
    result = assess_proposal(root, _proposal(), client_id="host:collector")
    path = record_shadow_assessment(root, result)
    text = path.read_text()
    assert "Observed the exact behavior" not in text
    assert "host:collector" not in text
    assert "notes/source.md" not in text
