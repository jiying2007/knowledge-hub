import json
from pathlib import Path

from tools.codex_assets.knowledge_hub import terminal_closure, terminal_closure_cli


def _write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _policy(default_branch_protection_required=False):
    return {
        "schema_version": 2,
        "contract": "knowledge-hub-github-terminal-closure-v2",
        "closure_scope": "github-repository",
        "product_gate": {
            "snapshot": ".cache/knowledge-hub/final-gate-product-full.json",
            "required_maturity_axes": ["platform", "delivery"],
            "require_all_hard_checks": True,
            "overall_product_status_informational": True,
            "overall_product_terminal_informational": True,
        },
        "external_closure": {
            "source": "registry/knowledge-platform-p5-p10.json",
            "required_gap_ids": ["repository-private-boundary"],
            "observational_gap_ids": ["production-retrieval-eval"],
            "require_evidence_refs_on_close": True,
        },
        "bounded_legacy": {
            "max_oversized_legacy_modules": 11,
            "max_legacy_artifact_references": 315,
            "growth_allowed": False,
        },
        "branch_gc": {
            "required": True,
            "source": "registry/branch-lifecycle.json",
            "evidence": ".cache/knowledge-hub/remote-branch-inventory.json",
            "require_current_github_sha_when_available": True,
            "require_current_github_repository_when_available": True,
        },
        "hosting_posture": {
            "required": True,
            "evidence": ".cache/knowledge-hub/hosting-posture.json",
            "require_current_github_sha_when_available": True,
            "require_current_github_repository_when_available": True,
        },
        "rules": {
            "default_branch": "master",
            "default_branch_protection_required": default_branch_protection_required,
        },
    }


def _stub_hygiene(
    monkeypatch,
    legacy_modules=11,
    legacy_attention_modules=11,
    legacy_refs=315,
):
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.setattr(
        terminal_closure,
        "evaluate_complexity_budget",
        lambda root: {
            "status": "pass",
            "oversized_module_count": legacy_modules,
            "legacy_attention_count": legacy_attention_modules,
        },
    )
    monkeypatch.setattr(
        terminal_closure,
        "evaluate_artifact_governance",
        lambda root: {
            "status": "pass",
            "immutable_refs": {"legacy_reference_count": legacy_refs},
        },
    )


def _write_branch_gc(
    tmp_path,
    remaining=None,
    revision=None,
    repository=None,
    *,
    default_branch="master",
    default_branch_present=True,
    protection_observed=True,
    protected=True,
):
    candidates = ["codex/old-branch"]
    _write_json(
        tmp_path / "registry/branch-lifecycle.json",
        {
            "status": "needs-external-gc",
            "retirement_candidates": [
                {"branch": "codex/old-branch", "reason": "absorbed"}
            ],
        },
    )
    remaining = [] if remaining is None else remaining
    _write_json(
        tmp_path / ".cache/knowledge-hub/remote-branch-inventory.json",
        {
            "status": "pass" if not remaining else "needs-review",
            "repository": repository or "example/knowledge-hub",
            "source_revision": revision or "a" * 40,
            "retirement_candidates": candidates,
            "remaining_candidates": remaining,
            "default_branch": default_branch,
            "default_branch_present": default_branch_present,
            "default_branch_protection_observed": protection_observed,
            "default_branch_protected": protected,
        },
    )


def _write_common_ready_state(
    tmp_path,
    external_status="closed",
    include_external_evidence=True,
    *,
    default_branch_protection_required=False,
    protected=True,
    protection_observed=True,
    default_branch_present=True,
):
    _write_json(
        tmp_path / "registry/terminal-closure.json",
        _policy(default_branch_protection_required),
    )
    _write_branch_gc(
        tmp_path,
        protected=protected,
        protection_observed=protection_observed,
        default_branch_present=default_branch_present,
    )
    row = {
        "id": "repository-private-boundary",
        "required": True,
        "status": external_status,
    }
    if include_external_evidence:
        row["evidence_refs"] = ["artifact://repository-posture/example.json"]
    _write_json(
        tmp_path / "registry/knowledge-platform-p5-p10.json",
        {
            "external_closure_gaps": [
                row,
                {
                    "id": "production-retrieval-eval",
                    "required": False,
                    "status": "open",
                    "owner": "runtime-owner",
                },
            ]
        },
    )
    _write_json(
        tmp_path / ".cache/knowledge-hub/hosting-posture.json",
        {
            "schema_version": "knowledge-hub.hosting-posture.v1",
            "status": "pass",
            "generated_at": "2026-09-20T00:00:00Z",
            "repository": "example/knowledge-hub",
            "source_revision": "a" * 40,
            "repository_private": True,
            "repository_visibility": "private",
            "default_branch": "master",
            "default_branch_present": default_branch_present,
            "default_branch_protection_observed": protection_observed,
            "default_branch_protected": protected,
            "rulesets_capability": {
                "status": "not-probed",
                "reason": "github-token-unavailable",
                "http_status": 0,
                "ruleset_count": 0,
            },
            "branch_inventory": (
                ".cache/knowledge-hub/remote-branch-inventory.json"
            ),
            "canonical_write": False,
        },
    )
    _write_json(
        tmp_path / ".cache/knowledge-hub/final-gate-product-full.json",
        {
            "status": "needs-review",
            "terminal": False,
            "maturity_axes": {
                "platform": {"status": "pass"},
                "delivery": {"status": "pass"},
                "project_evidence": {"status": "needs-review"},
                "adoption": {"status": "needs-review"},
            },
            "platform_status": {
                "status": "pass",
                "hard_checks": {
                    "knowledge_check": True,
                    "engineering_quality": True,
                    "full_regression": True,
                    "restore_drill": True,
                },
            },
        },
    )


def test_github_terminal_ignores_open_operational_production_observation(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["schema_version"] == 2
    assert report["contract"] == "knowledge-hub-github-terminal-closure-v2"
    assert report["closure_scope"] == "github-repository"
    assert report["status"] == "pass"
    assert report["terminal"] is True
    assert report["blockers"] == []
    assert report["product"]["status"] == "needs-review"
    assert report["product"]["terminal"] is False
    assert report["product"]["repository_readiness"]["status"] == "pass"
    assert report["operational_qualification"]["status"] == "needs-review"
    assert report["operational_qualification"]["blocking"] is False
    assert report["operational_qualification"]["open_count"] == 1
    assert report["operational_qualification"]["open_gaps"][0]["id"] == (
        "production-retrieval-eval"
    )
    assert report["bounded_legacy"]["legacy_module_count"] == 11
    assert report["bounded_legacy"]["legacy_attention_count"] == 11

    summary = terminal_closure_cli._summary(report)
    assert summary["schema_version"] == 2
    assert summary["projection"] == "knowledge-hub-github-terminal-closure-summary-v2"
    assert summary["terminal"] is True
    assert summary["product_status"] == "needs-review"
    assert summary["product_terminal"] is False
    assert summary["operational_open_count"] == 1
    assert summary["operational_blocking"] is False


def test_github_terminal_uses_product_v5_platform_status_hard_checks(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)
    readiness = report["product"]["repository_readiness"]

    assert readiness["hard_check_source"] == "platform_status.hard_checks"
    assert readiness["all_hard_checks_pass"] is True
    assert readiness["failed_hard_checks"] == []


def test_github_terminal_fails_closed_when_product_v5_platform_hard_checks_missing(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path)
    snapshot_path = tmp_path / ".cache/knowledge-hub/final-gate-product-full.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot.pop("platform_status")
    snapshot["hard_checks"] = {"legacy-top-level-shape": True}
    _write_json(snapshot_path, snapshot)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)
    readiness = report["product"]["repository_readiness"]

    assert report["terminal"] is False
    assert readiness["all_hard_checks_pass"] is False
    assert readiness["failed_hard_checks"] == ["platform-status-hard-checks-missing"]
    assert "product_repository_readiness" in report["blockers"]


def test_github_terminal_blocks_when_required_product_repository_axis_fails(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path)
    snapshot_path = tmp_path / ".cache/knowledge-hub/final-gate-product-full.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot["maturity_axes"]["delivery"]["status"] = "needs-review"
    _write_json(snapshot_path, snapshot)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["product"]["repository_readiness"]["status"] == "needs-review"
    assert "product_repository_readiness" in report["blockers"]


def test_terminal_closure_passes_branch_protection_axis_when_protected(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(
        tmp_path,
        default_branch_protection_required=True,
        protected=True,
    )

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is True
    assert report["default_branch_protection"]["status"] == "pass"
    assert report["default_branch_protection"]["protected"] is True
    assert report["checks"]["default_branch_protection"] is True


def test_terminal_closure_blocks_terminal_claim_when_default_branch_unprotected(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(
        tmp_path,
        default_branch_protection_required=True,
        protected=False,
    )

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["default_branch_protection"]["status"] == "needs-review"
    assert report["default_branch_protection"]["reason"] == "default-branch-unprotected"
    assert report["default_branch_protection"]["owner"] == "repository-admin"
    assert "default_branch_protection" in report["blockers"]


def test_terminal_closure_fails_closed_without_protection_observation(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(
        tmp_path,
        default_branch_protection_required=True,
        protection_observed=False,
        protected=False,
    )

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["default_branch_protection"]["status"] == "blocked"
    assert (
        report["default_branch_protection"]["reason"]
        == "default-branch-protection-evidence-missing"
    )
    assert "default_branch_protection" in report["blockers"]


def test_terminal_closure_fails_closed_when_default_branch_missing(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(
        tmp_path,
        default_branch_protection_required=True,
        default_branch_present=False,
        protection_observed=False,
        protected=False,
    )

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["default_branch_protection"]["status"] == "blocked"
    assert report["default_branch_protection"]["reason"] == "default-branch-missing"


def test_terminal_closure_rejects_green_quality_with_external_gap(monkeypatch, tmp_path):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path, external_status="open")

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["status"] == "needs-review"
    assert report["terminal"] is False
    assert "external_closure" in report["blockers"]


def test_terminal_closure_rejects_evidence_free_external_close(monkeypatch, tmp_path):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path, include_external_evidence=False)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["external_closure"]["open_gaps"][0]["status"] == "closed-without-evidence"
    assert "external_closure" in report["blockers"]


def test_terminal_closure_rejects_required_gap_policy_drift(monkeypatch, tmp_path):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path)
    _write_json(
        tmp_path / "registry/knowledge-platform-p5-p10.json",
        {
            "external_closure_gaps": [
                {
                    "id": "repository-private-boundary",
                    "required": True,
                    "status": "closed",
                    "evidence_refs": ["artifact://repository-posture/example.json"],
                },
                {
                    "id": "new-required-gap",
                    "required": True,
                    "status": "closed",
                    "evidence_refs": ["artifact://new-gap/evidence.json"],
                },
            ]
        },
    )

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["external_closure"]["open_gaps"][0]["id"] == "terminal-policy-required-gap-drift"
    assert "external_closure" in report["blockers"]


def test_terminal_closure_rejects_legacy_growth(monkeypatch, tmp_path):
    _stub_hygiene(
        monkeypatch,
        legacy_modules=12,
        legacy_attention_modules=12,
        legacy_refs=316,
    )
    _write_common_ready_state(tmp_path)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["bounded_legacy"]["status"] == "needs-fix"
    assert report["bounded_legacy"]["legacy_module_count"] == 12
    assert "bounded_legacy" in report["blockers"]


def test_terminal_closure_uses_explicit_total_oversized_count(monkeypatch, tmp_path):
    _stub_hygiene(
        monkeypatch,
        legacy_modules=12,
        legacy_attention_modules=11,
        legacy_refs=315,
    )
    _write_common_ready_state(tmp_path)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["bounded_legacy"]["legacy_module_count"] == 12
    assert report["bounded_legacy"]["legacy_attention_count"] == 11
    assert "bounded_legacy" in report["blockers"]


def test_terminal_closure_rejects_branch_gc_without_remote_clean_inventory(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path)
    _write_branch_gc(tmp_path, remaining=["codex/old-branch"])

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["branch_gc"]["status"] == "needs-review"
    assert "branch_gc" in report["blockers"]


def test_terminal_closure_rejects_branch_inventory_from_another_run(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path)
    monkeypatch.setenv("GITHUB_SHA", "b" * 40)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["branch_gc"]["status"] == "blocked"
    assert report["branch_gc"]["reason"] == "branch-inventory-revision-mismatch"
    assert "branch_gc" in report["blockers"]


def test_terminal_closure_rejects_protection_evidence_from_another_run(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(
        tmp_path,
        default_branch_protection_required=True,
        protected=True,
    )
    monkeypatch.setenv("GITHUB_SHA", "b" * 40)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["default_branch_protection"]["status"] == "blocked"
    assert (
        report["default_branch_protection"]["reason"]
        == "default-branch-protection-revision-mismatch"
    )
    assert "default_branch_protection" in report["blockers"]


def test_terminal_closure_rejects_branch_inventory_from_another_repository(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", "expected/knowledge-hub")

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["branch_gc"]["status"] == "blocked"
    assert report["branch_gc"]["reason"] == "branch-inventory-repository-mismatch"
    assert report["branch_gc"]["repository_matches_current_run"] is False
    assert "branch_gc" in report["blockers"]


def test_terminal_closure_rejects_protection_evidence_from_another_repository(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(
        tmp_path,
        default_branch_protection_required=True,
        protected=True,
    )
    monkeypatch.setenv("GITHUB_REPOSITORY", "expected/knowledge-hub")

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["default_branch_protection"]["status"] == "blocked"
    assert (
        report["default_branch_protection"]["reason"]
        == "default-branch-protection-repository-mismatch"
    )
    assert report["default_branch_protection"]["repository_matches_current_run"] is False
    assert "default_branch_protection" in report["blockers"]


def test_terminal_closure_reports_live_private_fact_ahead_of_canonical(monkeypatch, tmp_path):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path, external_status="open")

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["hosting_posture"]["status"] == "pass"
    assert report["hosting_posture"]["fact_drift"] == [
        {
            "id": "repository-private-boundary",
            "type": "live-fact-ahead-of-canonical",
            "live_private": True,
            "canonical_status": "open",
            "recommended_action": "machine-ratchet-candidate",
        }
    ]
    assert "external_closure" in report["blockers"]


def test_terminal_closure_allows_public_hosting_when_private_not_required(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path, external_status="closed")
    platform_path = tmp_path / "registry/knowledge-platform-p5-p10.json"
    platform = json.loads(platform_path.read_text(encoding="utf-8"))
    platform["repository_security_target"] = {"private_required": False}
    _write_json(platform_path, platform)
    posture_path = tmp_path / ".cache/knowledge-hub/hosting-posture.json"
    posture = json.loads(posture_path.read_text(encoding="utf-8"))
    posture["repository_private"] = False
    posture["repository_visibility"] = "public"
    _write_json(posture_path, posture)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["hosting_posture"]["status"] == "pass"
    assert report["hosting_posture"]["fact_drift"] == []


def test_terminal_closure_blocks_if_private_boundary_regresses_after_canonical_close(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path, external_status="closed")
    posture_path = tmp_path / ".cache/knowledge-hub/hosting-posture.json"
    posture = json.loads(posture_path.read_text(encoding="utf-8"))
    posture["repository_private"] = False
    posture["repository_visibility"] = "public"
    _write_json(posture_path, posture)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["hosting_posture"]["status"] == "needs-review"
    assert report["hosting_posture"]["reason"] == "repository-private-boundary-not-observed"
    assert "hosting_posture" in report["blockers"]


def test_terminal_closure_prefers_explicit_workflow_source_identity(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path)
    monkeypatch.setenv("GITHUB_SHA", "b" * 40)
    monkeypatch.setenv("GITHUB_REPOSITORY", "wrong/repository")
    monkeypatch.setenv("KNOWLEDGE_SOURCE_REVISION", "a" * 40)
    monkeypatch.setenv("KNOWLEDGE_GITHUB_REPOSITORY", "example/knowledge-hub")

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["branch_gc"]["revision_matches_current_run"] is True
    assert report["branch_gc"]["repository_matches_current_run"] is True
    assert report["hosting_posture"]["revision_matches_current_run"] is True
    assert report["hosting_posture"]["repository_matches_current_run"] is True


def test_terminal_closure_surfaces_rulesets_capability_without_weakening_gate(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(
        tmp_path,
        default_branch_protection_required=True,
        protected=False,
    )
    posture_path = tmp_path / ".cache/knowledge-hub/hosting-posture.json"
    posture = json.loads(posture_path.read_text(encoding="utf-8"))
    posture["rulesets_capability"] = {
        "status": "plan-gated",
        "reason": "private-repository-rulesets-require-upgrade-or-public",
        "http_status": 403,
        "ruleset_count": 0,
    }
    _write_json(posture_path, posture)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["hosting_posture"]["rulesets_capability"]["status"] == (
        "plan-gated"
    )
    assert report["default_branch_protection"]["status"] == "needs-review"
    assert report["terminal"] is False
    assert "default_branch_protection" in report["blockers"]


def test_terminal_closure_rejects_invalid_hosting_posture_contract(
    monkeypatch, tmp_path
):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path)
    posture_path = tmp_path / ".cache/knowledge-hub/hosting-posture.json"
    posture = json.loads(posture_path.read_text(encoding="utf-8"))
    posture.pop("rulesets_capability")
    _write_json(posture_path, posture)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["hosting_posture"]["status"] == "blocked"
    assert (
        report["hosting_posture"]["reason"]
        == "hosting-posture-contract-invalid"
    )
    assert report["hosting_posture"]["contract_validation"]["status"] == "fail"
    assert "hosting_posture" in report["blockers"]
