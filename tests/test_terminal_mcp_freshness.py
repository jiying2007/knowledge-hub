from __future__ import annotations

import hashlib
import json

from tools.codex_assets.knowledge_hub import terminal_closure


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _policy():
    return {
        "mcp_conformance": {
            "required": True,
            "evidence": ".cache/knowledge-hub/mcp-conformance/evidence.json",
            "policy": "registry/mcp-conformance-policy.json",
            "require_current_github_sha_when_available": True,
            "require_current_github_repository_when_available": True,
        }
    }


def _write_valid(tmp_path, *, revision="a" * 40, runner_environment="github-hosted"):
    conformance_policy = {
        "hosted_official_scenarios": ["tools-list"],
        "runner": {
            "package": "@modelcontextprotocol/conformance",
            "version": "0.2.0-alpha.10",
        },
    }
    _write_json(tmp_path / "registry/mcp-conformance-policy.json", conformance_policy)
    evidence = {
        "schema_version": "knowledge-hub.mcp-conformance-evidence.v2",
        "repository": "example/knowledge-hub",
        "source_revision": revision,
        "github_run_id": 123,
        "github_run_attempt": 1,
        "runner_environment": runner_environment,
        "runner_name": "GitHub Actions 1",
        "runner_os": "Linux",
        "protocol_version": "2026-07-28",
        "native_profile": "stateless-2026-07-28",
        "runner": {
            "package": "@modelcontextprotocol/conformance",
            "version": "0.2.0-alpha.10",
            "integrity": "sha512-example",
        },
        "expected_failure_baseline_used": False,
        "hosted_official_scenarios": ["tools-list"],
        "product_resource_read_smoke_passed": True,
        "scenarios": [
            {
                "scenario": "tools-list",
                "profile_applicability_passed": True,
                "applicable_failure_count": 0,
            }
        ],
        "profile_contract_passed": True,
    }
    raw = json.dumps(
        evidence,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    evidence["result_sha256"] = hashlib.sha256(raw).hexdigest()
    path = tmp_path / ".cache/knowledge-hub/mcp-conformance/evidence.json"
    _write_json(path, evidence)
    return path


def test_terminal_mcp_freshness_passes_exact_hosted_receipt(monkeypatch, tmp_path):
    _write_valid(tmp_path)
    monkeypatch.setenv("KNOWLEDGE_SOURCE_REVISION", "a" * 40)
    monkeypatch.setenv("KNOWLEDGE_GITHUB_REPOSITORY", "example/knowledge-hub")

    result = terminal_closure._mcp_conformance_state(tmp_path, _policy())

    assert result["status"] == "pass"
    assert result["revision_matches_current_run"] is True
    assert result["repository_matches_current_run"] is True
    assert result["runner_environment"] == "github-hosted"


def test_terminal_mcp_freshness_rejects_old_source(monkeypatch, tmp_path):
    _write_valid(tmp_path, revision="b" * 40)
    monkeypatch.setenv("KNOWLEDGE_SOURCE_REVISION", "a" * 40)
    monkeypatch.setenv("KNOWLEDGE_GITHUB_REPOSITORY", "example/knowledge-hub")

    result = terminal_closure._mcp_conformance_state(tmp_path, _policy())

    assert result["status"] == "blocked"
    assert "mcp-evidence-revision-mismatch" in result["reason_codes"]


def test_terminal_mcp_freshness_rejects_non_hosted_runner(monkeypatch, tmp_path):
    _write_valid(tmp_path, runner_environment="self-hosted")
    monkeypatch.setenv("KNOWLEDGE_SOURCE_REVISION", "a" * 40)
    monkeypatch.setenv("KNOWLEDGE_GITHUB_REPOSITORY", "example/knowledge-hub")

    result = terminal_closure._mcp_conformance_state(tmp_path, _policy())

    assert result["status"] == "blocked"
    assert "mcp-hosted-runner-not-proven" in result["reason_codes"]


def test_terminal_mcp_freshness_rejects_receipt_tamper(monkeypatch, tmp_path):
    path = _write_valid(tmp_path)
    evidence = json.loads(path.read_text(encoding="utf-8"))
    evidence["profile_contract_passed"] = False
    _write_json(path, evidence)
    monkeypatch.setenv("KNOWLEDGE_SOURCE_REVISION", "a" * 40)
    monkeypatch.setenv("KNOWLEDGE_GITHUB_REPOSITORY", "example/knowledge-hub")

    result = terminal_closure._mcp_conformance_state(tmp_path, _policy())

    assert result["status"] == "blocked"
    assert "mcp-profile-contract-not-passing" in result["reason_codes"]
    assert "mcp-result-digest-mismatch" in result["reason_codes"]
