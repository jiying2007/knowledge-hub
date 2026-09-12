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
    required_open = {
        row["id"]
        for row in payload["external_closure_gaps"]
        if row["required"] and row["status"] == "open"
    }
    assert {
        "repository-private-boundary",
        "master-ruleset-enforcement",
        "mcp-official-conformance",
        "connector-provider-pilot",
    }.issubset(required_open)


def test_mcp_registry_marks_native_default_and_legacy_explicit_only():
    payload = _load("registry/knowledge-platform-p5-p10.json")
    mcp = payload["protocols"]["mcp"]
    assert mcp["native_default"] is True
    assert mcp["legacy_compatibility_adapter"] is True
    assert mcp["legacy_default"] is False
    assert mcp["legacy_opt_in_flag"] == "--legacy-compat"
