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
    assert payload["adoption_status"] == "external-closure-required"
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
    assert {
        "repository-private-boundary",
        "mcp-official-conformance",
        "connector-provider-pilot",
        "production-retrieval-eval",
        "memory-lifecycle-pilot",
        "real-adoption-evidence",
        "attestation-signing-identity",
    } == required_open
    assert gaps["master-ruleset-enforcement"]["required"] is False
    assert gaps["master-ruleset-enforcement"]["status"] == "not-required"
    repository_target = payload["repository_security_target"]
    assert repository_target["protected_default_branch_required"] is False
    assert repository_target["required_status_checks"] == []
    assert repository_target["block_force_push"] is False
    assert repository_target["block_branch_deletion"] is False
    assert repository_target["require_pull_request"] is False
    assert repository_target["require_conversation_resolution"] is False
    assert (
        repository_target["default_branch_protection_policy"]
        == "intentionally-unprotected-at-current-stage"
    )


def test_mcp_registry_marks_native_default_and_legacy_explicit_only():
    payload = _load("registry/knowledge-platform-p5-p10.json")
    mcp = payload["protocols"]["mcp"]
    assert mcp["native_default"] is True
    assert mcp["legacy_compatibility_adapter"] is True
    assert mcp["legacy_default"] is False
    assert mcp["legacy_opt_in_flag"] == "--legacy-compat"
