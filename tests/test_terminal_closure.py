import json
from pathlib import Path

from tools.codex_assets.knowledge_hub import terminal_closure


def _write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _policy(default_branch_protection_required=False):
    return {
        "schema_version": 1,
        "product_gate": {
            "snapshot": ".cache/knowledge-hub/final-gate-product-full.json",
            "require_status": "pass",
            "require_terminal": True,
        },
        "external_closure": {
            "source": "registry/knowledge-platform-p5-p10.json",
            "required_gap_ids": ["repository-private-boundary"],
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
        {"external_closure_gaps": [row]},
    )
    _write_json(
        tmp_path / ".cache/knowledge-hub/final-gate-product-full.json",
        {"status": "pass", "terminal": True},
    )


def test_terminal_closure_passes_only_when_all_axes_close(monkeypatch, tmp_path):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["status"] == "pass"
    assert report["terminal"] is True
    assert report["blockers"] == []
    assert report["bounded_legacy"]["legacy_module_count"] == 11
    assert report["bounded_legacy"]["legacy_attention_count"] == 11


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
