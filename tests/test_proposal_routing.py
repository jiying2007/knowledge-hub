import json

import pytest

from tools.codex_assets.knowledge_hub.proposal_routing import (
    assess_proposal,
    record_shadow_assessment,
    shadow_audit_stats,
)
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


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
    assert path.stat().st_mode & 0o777 == 0o600
    assert "Observed the exact behavior" not in text
    assert "host:collector" not in text
    assert "notes/source.md" not in text
    stats = shadow_audit_stats(root)
    assert stats["status"] == "pass"
    assert stats["sample_count"] == 1
    assert stats["safety"]["actual_non_human_route_count"] == 0
    assert stats["safety"]["content_leak_row_count"] == 0
    assert stats["integrity"]["hash_chain_valid"] is True
    assert validate_instance(
        repository_root(), "agent-proposal-shadow-stats-v1", stats
    )["status"] == "pass"


def test_shadow_stats_are_pending_without_real_observations(tmp_path):
    root = _root(tmp_path, _policy(False))

    stats = shadow_audit_stats(root)

    assert stats["status"] == "pending"
    assert stats["sample_count"] == 0
    assert stats["policy_enabled"] is False


def test_shadow_audit_sequence_and_hash_chain_support_multiple_rows(tmp_path):
    root = _root(tmp_path, _policy(True))
    result = assess_proposal(root, _proposal(), client_id="host:collector")

    path = record_shadow_assessment(root, result)
    record_shadow_assessment(root, result)

    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert [row["sequence"] for row in rows] == [1, 2]
    assert rows[1]["previous_hash"] == rows[0]["event_hash"]
    stats = shadow_audit_stats(root)
    assert stats["status"] == "pass"
    assert stats["sample_count"] == 2
    assert stats["integrity"]["duplicate_proposal_hash_count"] == 1


def test_shadow_stats_fail_on_route_or_content_tampering(tmp_path):
    root = _root(tmp_path, _policy(True))
    result = assess_proposal(root, _proposal(), client_id="host:collector")
    path = record_shadow_assessment(root, result)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "schema_version": "knowledge-hub.proposal-shadow-audit.v1",
                    "recorded_at": "2026-07-16T00:00:00Z",
                    "proposal_hash": "a" * 64,
                    "client_fingerprint": "b" * 16,
                    "actual_route": "auto-stage-reviewing",
                    "eligible_route": "auto-stage-reviewing",
                    "reason_codes": ["high_risk_kind_human_only"],
                    "sample": {},
                    "proposal_content": "must never be stored",
                    "previous_hash": "",
                    "event_hash": "c" * 64,
                }
            )
            + "\n"
        )

    stats = shadow_audit_stats(root)

    assert stats["status"] == "fail"
    assert stats["safety"]["actual_non_human_route_count"] == 1
    assert stats["safety"]["high_risk_non_human_eligible_count"] == 1
    assert stats["safety"]["content_leak_row_count"] == 1
    assert stats["integrity"]["hash_chain_valid"] is False
    assert "must never be stored" not in json.dumps(stats)


def test_shadow_audit_rejects_unbounded_metadata_symlink_and_truncated_tail(tmp_path):
    root = _root(tmp_path, _policy(True))
    result = assess_proposal(root, _proposal(), client_id="host:collector")
    unsafe = dict(result)
    unsafe["reason_codes"] = ["proposal body must not become a reason code"]
    with pytest.raises(KnowledgeHubError, match="metadata is invalid"):
        record_shadow_assessment(root, unsafe)

    cache = root / ".cache/knowledge-hub"
    cache.mkdir(parents=True, exist_ok=True)
    target = root / "shadow-target.jsonl"
    target.write_text("")
    (cache / "proposal-route-shadow.jsonl").symlink_to(target)
    with pytest.raises(KnowledgeHubError, match="symlinks"):
        record_shadow_assessment(root, result)

    (cache / "proposal-route-shadow.jsonl").unlink()
    path = record_shadow_assessment(root, result)
    path.write_bytes(path.read_bytes().rstrip(b"\n"))
    assert shadow_audit_stats(root)["status"] == "fail"
    with pytest.raises(KnowledgeHubError, match="truncated tail"):
        record_shadow_assessment(root, result)


def test_proposal_routing_rejects_unsafe_policy_and_unbounded_inputs(tmp_path):
    bad_policy = _policy(True)
    bad_policy["human_sample_percent"] = 101
    root = _root(tmp_path, bad_policy)
    with pytest.raises(KnowledgeHubError, match="human_sample_percent"):
        assess_proposal(root, _proposal(), client_id="host:collector")

    extra = tmp_path / "extra-policy"
    extra.mkdir()
    extra_policy = _policy(True)
    extra_policy["unknown_override"] = True
    root = _root(extra, extra_policy)
    with pytest.raises(KnowledgeHubError, match="policy fields"):
        assess_proposal(root, _proposal(), client_id="host:collector")

    typed = tmp_path / "typed-policy"
    typed.mkdir()
    typed_policy = _policy(True)
    typed_policy["daily_limit"] = "10"
    root = _root(typed, typed_policy)
    with pytest.raises(KnowledgeHubError, match="limits must be integers"):
        assess_proposal(root, _proposal(), client_id="host:collector")

    bounded = tmp_path / "bounded"
    bounded.mkdir()
    root = _root(bounded, _policy(True))
    with pytest.raises(KnowledgeHubError, match="proposal exceeds"):
        assess_proposal(root, {"padding": "x" * (128 * 1024)}, client_id="host:collector")
    with pytest.raises(KnowledgeHubError, match="client_id exceeds"):
        assess_proposal(root, _proposal(), client_id="x" * 257)
    with pytest.raises(KnowledgeHubError, match="staged_today"):
        assess_proposal(root, _proposal(), staged_today=-1)


def test_proposal_quote_budget_fails_closed(tmp_path):
    root = _root(tmp_path, _policy(True))
    proposal = _proposal()
    proposal["evidence"]["quote"] = "x" * 4097
    result = assess_proposal(root, proposal, client_id="host:collector")
    assert result["actual_route"] == "human-review"
    assert result["evidence_verification"]["reason"] == "quote_exceeds_limit"
    assert "evidence_not_exactly_verified" in result["reason_codes"]
