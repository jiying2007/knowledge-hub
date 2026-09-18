import json

from tools.codex_assets.knowledge_hub.common import repository_root


def _load(relative: str):
    return json.loads((repository_root() / relative).read_text(encoding="utf-8"))


def test_p0_p3_registry_records_qualified_implementation_without_claiming_promotion():
    payload = _load("registry/knowledge-runtime-v3.json")
    assert payload["status"] == "qualified-compatibility-runtime"
    assert payload["implementation_status"] == "qualified"
    assert payload["adoption_status"] == "stable-compatibility-surface"
    assert payload["qualification_evidence"]["pr"] == 15
    assert payload["qualification_evidence"]["post_merge_status"] == "success"
    assert payload["authority_contract"]["auto_promotion"] is False


def test_p5_p10_registry_separates_qualified_code_from_open_adoption():
    payload = _load("registry/knowledge-platform-p5-p10.json")
    assert payload["status"] == "qualified-implementation"
    assert payload["implementation_status"] == "qualified"
    assert payload["adoption_status"] == "operational-observation-pending"
    assert payload["qualification_evidence"]["pr"] == 22
    assert payload["qualification_evidence"]["post_merge_status"] == "success"
    assert all(
        phase["implementation_status"] == "qualified"
        for phase in payload["phases"].values()
    )
    gaps = {row["id"]: row for row in payload["external_closure_gaps"]}
    required_open = {
        gap_id
        for gap_id, row in gaps.items()
        if row["required"] and row["status"] == "open"
    }
    assert {"repository-private-boundary"} == required_open
    operational_open = {
        gap_id
        for gap_id, row in gaps.items()
        if (
            row.get("qualification_scope") == "operational"
            and row["status"] == "open"
        )
    }
    assert operational_open == {
        "connector-provider-pilot",
        "production-retrieval-eval",
        "memory-lifecycle-pilot",
        "real-adoption-evidence",
    }
    assert all(
        gaps[gap_id]["required"] is False
        and gaps[gap_id]["github_terminal_blocking"] is False
        for gap_id in operational_open
    )
    mcp_gap = gaps["mcp-official-conformance"]
    assert mcp_gap["required"] is True
    assert mcp_gap["status"] == "closed"
    assert mcp_gap["evidence_refs"]
    evidence = mcp_gap["evidence"]
    assert evidence["source_revision"] == "73d050aae8adae51092c2ac580094d506ae066ac"
    assert evidence["protocol_version"] == "2026-07-28"
    assert evidence["native_profile"] == "stateless-2026-07-28"
    assert evidence["runner"]["package"] == "@modelcontextprotocol/conformance"
    assert evidence["runner"]["version"] == "0.2.0-alpha.10"
    assert evidence["profile_contract_passed"] is True
    assert evidence["applicable_failure_count"] == 0
    assert evidence["product_resource_read_smoke_passed"] is True
    assert evidence["expected_failure_baseline_used"] is False
    signing_gap = gaps["attestation-signing-identity"]
    assert signing_gap["required"] is True
    assert signing_gap["status"] == "closed"
    assert signing_gap["evidence_refs"]
    signing_evidence = signing_gap["evidence"]
    assert signing_evidence["source_revision"] == "7bab61c64f19977c7a30ccd4a15b58f1f6278c69"
    assert signing_evidence["github_run_id"] == 34797968706
    assert signing_evidence["artifact_id"] == 10330542489
    assert signing_evidence["attestation_id"] == "47234390"
    assert signing_evidence["sigstore_identity_verified"] is True
    assert signing_evidence["private_key_used"] is False
    assert signing_evidence["self_hosted_runner_allowed"] is False
    assert signing_evidence["product_gate_status"] == "needs-review"
    assert signing_evidence["terminal_closure_status"] == "needs-review"
    assert signing_evidence["terminal_closure_terminal"] is False
    assert gaps["master-ruleset-enforcement"]["required"] is False
    assert gaps["master-ruleset-enforcement"]["status"] == "not-required"
    repository_target = payload["repository_security_target"]
    assert repository_target["protected_default_branch_required"] is True
    assert repository_target["required_status_checks"] == []
    assert repository_target["block_force_push"] is False
    assert repository_target["block_branch_deletion"] is False
    assert repository_target["require_pull_request"] is False
    assert repository_target["require_conversation_resolution"] is False
    assert (
        repository_target["default_branch_protection_policy"]
        == "required-for-terminal-closure-external-admin"
    )


def test_mcp_registry_is_native_only():
    payload = _load("registry/knowledge-platform-p5-p10.json")
    mcp = payload["protocols"]["mcp"]
    assert mcp["native_default"] is True
    assert mcp["native_profile"] == "stateless-2026-07-28"
    assert mcp["official_conformance_evidence_required"] is True
    for retired_key in (
        "legacy_compatibility_adapter",
        "legacy_default",
        "legacy_opt_in_flag",
        "legacy_deprecation_status",
    ):
        assert retired_key not in mcp
