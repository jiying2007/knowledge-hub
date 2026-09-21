from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/ai-maintenance-sweep.yml")


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_ai_maintenance_has_only_trusted_scheduled_or_manual_triggers():
    payload = _workflow()
    assert set(payload["on"]) == {"schedule", "workflow_dispatch"}
    assert "pull_request" not in payload["on"]
    assert "pull_request_target" not in payload["on"]


def test_ai_maintenance_routes_only_critical_items_to_human():
    payload = _workflow()
    assert payload["permissions"] == {"contents": "read", "issues": "write"}
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "security-critical" in text
    assert "governance-critical" in text
    assert "ordinary_and_governance_routed_to_ai" in text
    assert "human_required" in text
    assert "git push" not in text
    assert "gh pr merge" not in text
    assert "knowledge-promote" not in text


def test_ai_maintenance_closes_stale_critical_issue_after_recovery():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Close stale critical maintenance issue when recovered" in text
    assert "gh issue close" in text
    assert "no longer requires a critical human decision" in text


def test_ai_maintenance_accepts_health_status_exit_codes_for_analysis():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '[[ "${health_rc}" -eq 0 || "${health_rc}" -eq 1 ]]' in text
    assert '[[ "${review_rc}" -eq 0 || "${review_rc}" -eq 1 ]]' in text
    assert "health-exit-code.txt" in text
    assert "review-exit-code.txt" in text
    assert "json.loads" in text


def test_ai_maintenance_materializes_machine_owned_triage_outputs():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Materialize machine triage and governance review packet" in text
    assert "build_maintenance_triage" in text
    assert "triage-receipt.json" in text
    assert "governance-review-packet.json" in text
    assert '"machine_triage_receipt": "triage-receipt.json"' in text
    assert (
        '"governance_review_packet": "governance-review-packet.json"'
        in text
    )
    assert "canonical_write_performed" in text
    assert "git push" not in text


def test_ai_maintenance_exposes_policy_error_when_escalating():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '"policy_error": policy_error' in text
    assert 'handle.write("policy_error={}\\\\n"' in text or 'handle.write("policy_error={}\\n"' in text
    assert "POLICY_ERROR" in text
    assert "policy-error=${POLICY_ERROR}" in text


def test_ai_maintenance_reconciles_external_operational_trackers():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Reconcile operational qualification trackers" in text
    assert "connector-provider-pilot" in text
    assert "production-retrieval-eval" in text
    assert "memory-lifecycle-pilot" in text
    assert "real-adoption-evidence" in text
    assert "gh issue close 20" in text
    assert "gh issue close 21" in text
    assert "operational-trackers.json" in text


def test_ai_maintenance_reconciles_owner_trackers_without_generating_decisions():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Materialize owner qualification packet" in text
    assert "build_owner_qualification_packet" in text
    assert "owner-qualification-packet-v1" in text
    assert "owner-qualification-packet.json" in text
    assert "Reconcile owner and project qualification trackers" in text
    assert "does not infer or generate owner approval" in text
    assert "gh issue close 74" in text
    assert "gh issue close 96" in text
    assert "gh issue reopen 74" in text
    assert "gh issue reopen 96" in text
    assert "PACKET_FINGERPRINT" in text
    assert "comment_once" in text


def test_ai_maintenance_owner_tracker_close_conditions_are_bounded():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'OWNER_DECLARATION_PENDING}" == "0" && "${OWNER_BOUNDARY_PENDING}" == "0"' in text
    assert 'QUALIFICATION_PASS}" == "true"' in text
    assert "No project readiness, owner decision, or real-world evidence was synthesized." in text


def test_ai_maintenance_issue_writes_are_bound_to_current_master():
    payload = _workflow()
    job = payload["jobs"]["sweep"]
    condition = job["if"]
    assert "github.event_name == 'schedule'" in condition
    assert "github.event_name == 'workflow_dispatch'" in condition
    assert "github.ref == 'refs/heads/master'" in condition
    assert job["env"]["SOURCE_REVISION"] == "${{ github.sha }}"

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Verify current master identity" in text
    assert 'ref: ${{ env.SOURCE_REVISION }}' in text
    assert "maintenance source is stale relative to current master" in text


def test_ai_maintenance_owner_tracker_reconciliation_matches_policy():
    import json

    policy = json.loads(
        Path("registry/ai-operations-policy.json").read_text(encoding="utf-8")
    )
    boundary = policy["owner_qualification"]
    assert boundary["packet_generation_class"] == "autonomous-read"
    assert boundary["owner_decision_generated"] is False
    assert boundary["canonical_write_performed"] is False
    assert boundary["tracker_reconciliation_enabled"] is True
    assert boundary["owner_gate_tracker_issue"] == 74
    assert boundary["qualification_tracker_issue"] == 96
    assert boundary[
        "owner_gate_close_requires_zero_owner_declaration_pending"
    ] is True
    assert boundary[
        "owner_gate_close_requires_zero_owner_boundary_pending"
    ] is True
    assert boundary["qualification_close_requires_pass"] is True
    assert boundary["reopen_on_regression"] is True


def test_ai_maintenance_materializes_observation_source_readiness():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Materialize observation source readiness" in text
    assert "build_observation_source_readiness" in text
    assert "observation-source-readiness-v1" in text
    assert "observation-source-readiness.json" in text


def test_ai_maintenance_operational_tracker_comments_are_scoped_and_non_evidence():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "connector_tracker_fingerprint" in text
    assert "production_tracker_fingerprint" in text
    assert "comment_once 20" in text
    assert "comment_once 21" in text
    assert "Registration is not evidence" in text
    assert "no production result was synthesized" in text
    assert "no production/adoption result was synthesized" in text
    assert "gh issue reopen 20" in text
    assert "gh issue reopen 21" in text
