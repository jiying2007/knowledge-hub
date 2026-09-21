from __future__ import annotations

import json
from pathlib import Path


def _load(root: Path, relative: str):
    return json.loads((root / relative).read_text(encoding="utf-8"))


def test_default_branch_protection_target_matches_terminal_policy():
    root = Path(__file__).resolve().parents[1]
    terminal = _load(root, "registry/terminal-closure.json")
    platform = _load(root, "registry/knowledge-platform-p5-p10.json")

    rules = terminal["rules"]
    target = platform["repository_security_target"]

    assert rules["default_branch"] == "master"
    assert rules["default_branch_protection_required"] is True
    assert target["protected_default_branch_required"] is True
    assert target["default_branch_protection_policy"] == (
        "required-for-terminal-closure-external-admin"
    )


def test_master_ruleset_row_is_not_a_duplicate_terminal_closure_source():
    root = Path(__file__).resolve().parents[1]
    terminal = _load(root, "registry/terminal-closure.json")
    platform = _load(root, "registry/knowledge-platform-p5-p10.json")

    rows = {
        row["id"]: row
        for row in platform["external_closure_gaps"]
        if isinstance(row, dict) and row.get("id")
    }
    ruleset = rows["master-ruleset-enforcement"]
    required_ids = set(terminal["external_closure"]["required_gap_ids"])

    assert ruleset["required"] is False
    assert ruleset["status"] == "not-required"
    assert "default_branch_protection" in ruleset["reason"]
    assert "master-ruleset-enforcement" not in required_ids

def test_operational_observation_gaps_do_not_block_github_terminal():
    root = Path(__file__).resolve().parents[1]
    terminal = _load(root, "registry/terminal-closure.json")
    platform = _load(root, "registry/knowledge-platform-p5-p10.json")

    rows = {
        row["id"]: row
        for row in platform["external_closure_gaps"]
        if isinstance(row, dict) and row.get("id")
    }
    required_ids = set(terminal["external_closure"]["required_gap_ids"])
    observational_ids = set(terminal["external_closure"]["observational_gap_ids"])

    assert terminal["closure_scope"] == "github-repository"
    assert terminal["rules"]["production_observation_may_block_github_terminal"] is False
    assert observational_ids == {
        "connector-provider-pilot",
        "production-retrieval-eval",
        "memory-lifecycle-pilot",
        "real-adoption-evidence",
    }
    assert required_ids == {"attestation-signing-identity"}
    assert rows["repository-private-boundary"]["required"] is False
    assert rows["repository-private-boundary"]["github_terminal_blocking"] is False
    assert rows["mcp-official-conformance"]["required"] is False
    assert rows["mcp-official-conformance"]["github_terminal_blocking"] is False
    assert rows["mcp-official-conformance"]["qualification_scope"] == "historical-capability"
    assert terminal["mcp_conformance"]["required"] is True
    for gap_id in observational_ids:
        assert rows[gap_id]["required"] is False
        assert rows[gap_id]["github_terminal_blocking"] is False
        assert rows[gap_id]["qualification_scope"] == "operational"

