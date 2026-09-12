import json
from pathlib import Path

from tools.codex_assets.knowledge_hub import terminal_closure


def _write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _policy():
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
        },
    }


def _stub_hygiene(monkeypatch, legacy_modules=11, legacy_refs=315):
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.setattr(
        terminal_closure,
        "evaluate_complexity_budget",
        lambda root: {"status": "pass", "legacy_attention_count": legacy_modules},
    )
    monkeypatch.setattr(
        terminal_closure,
        "evaluate_artifact_governance",
        lambda root: {
            "status": "pass",
            "immutable_refs": {"legacy_reference_count": legacy_refs},
        },
    )


def _write_branch_gc(tmp_path, remaining=None, revision=None):
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
            "repository": "example/knowledge-hub",
            "source_revision": revision or "a" * 40,
            "retirement_candidates": candidates,
            "remaining_candidates": remaining,
        },
    )


def _write_common_ready_state(tmp_path, external_status="closed"):
    _write_json(tmp_path / "registry/terminal-closure.json", _policy())
    _write_branch_gc(tmp_path)
    _write_json(
        tmp_path / "registry/knowledge-platform-p5-p10.json",
        {
            "external_closure_gaps": [
                {
                    "id": "repository-private-boundary",
                    "status": external_status,
                }
            ]
        },
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


def test_terminal_closure_rejects_green_quality_with_external_gap(monkeypatch, tmp_path):
    _stub_hygiene(monkeypatch)
    _write_common_ready_state(tmp_path, external_status="open")

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["status"] == "needs-review"
    assert report["terminal"] is False
    assert "external_closure" in report["blockers"]


def test_terminal_closure_rejects_legacy_growth(monkeypatch, tmp_path):
    _stub_hygiene(monkeypatch, legacy_modules=12, legacy_refs=316)
    _write_common_ready_state(tmp_path)

    report = terminal_closure.evaluate_terminal_closure(tmp_path)

    assert report["terminal"] is False
    assert report["bounded_legacy"]["status"] == "needs-fix"
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
