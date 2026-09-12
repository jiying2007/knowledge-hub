import copy
import json

import pytest

from tools.codex_assets.knowledge_hub import health
from tools.codex_assets.knowledge_hub.common import (
    project_rows,
    registry_items,
    repository_root,
    run_rtk,
    working_tree_signature,
)
from tools.codex_assets.knowledge_hub.final_gate_cli import main as final_gate_main
from tools.codex_assets.knowledge_hub.product_gate import _candidate_integrity
from tools.codex_assets.knowledge_hub.product_gate import (
    _engineering_quality_state,
    _write_snapshot,
    product_gate_summary,
    product_snapshot_path,
)
from tools.codex_assets.knowledge_hub.product_gate import _git_delivery_state
from tools.codex_assets.knowledge_hub.product_gate import _project_readiness
from tools.codex_assets.knowledge_hub.product_gate import _restore_state
from tools.codex_assets.knowledge_hub.product_gate import _source_runtime_ready
from tools.codex_assets.knowledge_hub.product_gate import _unit_test_evidence_reuse_mode
from tools.codex_assets.knowledge_hub.product_policy import (
    evaluate_specialized_owner_requirements,
    load_product_policy,
)


def test_product_readiness_separates_structure_from_real_evidence():
    root = repository_root()
    expected_project_count = len(project_rows(root))
    payload = _project_readiness(root)
    assert payload["project_count"] == expected_project_count
    assert payload["slot_count"] == expected_project_count
    assert payload["structural_ready_count"] == expected_project_count
    assert "source_mapping_ready_count" in payload
    assert payload["route_matrix_failure_count"] == 0
    assert payload["evidence_ready_count"] < payload["project_count"]
    assert 0 <= payload["evidence_field_complete_count"] <= payload["project_count"]
    assert all(
        row["evidence_field_status"] in {"incomplete", "complete-awaiting-declaration"}
        for row in payload["rows"]
    )


def test_product_is_the_only_executable_final_profile():
    root = repository_root()
    assert not (root / "tools/knowledge-product-gate.sh").exists()
    assert not (root / "tools/knowledge-mature-auto-approval.sh").exists()
    with pytest.raises(SystemExit) as error:
        final_gate_main(["--final-profile", "mature", "--json"])
    assert error.value.code == 2
    with pytest.raises(SystemExit) as removed_alias:
        final_gate_main(["--full-regression", "--json"])
    assert removed_alias.value.code == 2


def test_restore_state_requires_matching_source_mode(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    (cache / "restore-drill-head.json").write_text(
        '{"status":"pass","source_mode":"candidate","as_of":"2026-07-13","source_revision":"abc"}',
        encoding="utf-8",
    )
    payload = _restore_state(tmp_path, "2026-07-13", "head", "sig", "abc")
    assert payload["fresh"] is False


def test_git_delivery_state_treats_unborn_repository_as_candidate(tmp_path):
    run_rtk(tmp_path, ["git", "init"])
    payload = _git_delivery_state(tmp_path)
    assert payload["head_present"] is False
    assert payload["head_revision"] == ""
    assert payload["worktree_clean"] is True
    assert "requirements-runtime.lock" in payload["required_release_contract_files"]
    assert ".github/workflows/quality.yml" in payload["required_release_contract_files"]
    assert "tools/ci/python-runtime.sh" in payload["required_release_contract_files"]


def test_engineering_quality_state_requires_matching_candidate_signature(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    (cache / "engineering-quality.json").write_text(
        '{"status":"pass","mode":"full","candidate_integrity":'
        '{"unchanged":true,"before_signature":"sig-a","after_signature":"sig-a"},'
        '"checks":{"coverage":{"status":"pass"},"full_regression":{"status":"pass"}}}',
        encoding="utf-8",
    )

    current = _engineering_quality_state(tmp_path, "sig-a")
    assert current["fresh"] is True
    assert current["check_statuses"] == {
        "coverage": "pass",
        "full_regression": "pass",
    }
    assert _engineering_quality_state(tmp_path, "sig-b")["fresh"] is False


def test_engineering_quality_state_fails_closed_on_invalid_or_symlink_snapshot(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    snapshot = cache / "engineering-quality.json"
    snapshot.write_text("{invalid", encoding="utf-8")
    assert _engineering_quality_state(tmp_path, "sig")["status"] == "invalid"

    snapshot.unlink()
    outside = tmp_path / "outside.json"
    outside.write_text('{"status":"pass"}', encoding="utf-8")
    snapshot.symlink_to(outside)
    assert _engineering_quality_state(tmp_path, "sig")["status"] == "missing"


def test_quick_gate_automatically_reuses_fresh_signature_bound_unit_evidence():
    engineering_quality = {
        "fresh": True,
        "check_statuses": {"coverage": "pass", "coverage_report": "pass"},
    }

    assert (
        _unit_test_evidence_reuse_mode("quick", False, engineering_quality)
        == "automatic-quick"
    )
    assert _unit_test_evidence_reuse_mode("full", False, engineering_quality) == "disabled"
    assert _unit_test_evidence_reuse_mode("full", True, engineering_quality) == "explicit"


def test_quick_gate_does_not_reuse_stale_or_incomplete_unit_evidence():
    stale = {
        "fresh": False,
        "check_statuses": {"coverage": "pass", "coverage_report": "pass"},
    }
    incomplete = {"fresh": True, "check_statuses": {"coverage": "pass"}}

    assert _unit_test_evidence_reuse_mode("quick", False, stale) == "disabled"
    assert _unit_test_evidence_reuse_mode("quick", False, incomplete) == "disabled"


def test_product_snapshot_is_atomic_private_and_replaces_old_content(tmp_path):
    snapshot = tmp_path / ".cache/knowledge-hub/final-gate-product-quick.json"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_text('{"status":"old"}\n')
    snapshot.chmod(0o644)

    relative = _write_snapshot(tmp_path, {"status": "pass"}, "quick")

    assert relative == ".cache/knowledge-hub/final-gate-product-quick.json"
    assert json.loads(snapshot.read_text()) == {"status": "pass"}
    assert snapshot.stat().st_mode & 0o777 == 0o600
    assert snapshot.parent.stat().st_mode & 0o777 == 0o700
    assert not list(snapshot.parent.glob("*.tmp-*"))


def test_product_snapshot_paths_isolate_quick_and_full_runs(tmp_path):
    quick = product_snapshot_path(tmp_path, "quick")
    full = product_snapshot_path(tmp_path, "full")

    assert quick.name == "final-gate-product-quick.json"
    assert full.name == "final-gate-product-full.json"
    assert quick != full
    with pytest.raises(ValueError, match="quick or full"):
        product_snapshot_path(tmp_path, "fixture")


def test_health_snapshot_rejects_malformed_production_evidence(tmp_path, monkeypatch):
    snapshot = product_snapshot_path(tmp_path, "quick")
    snapshot.parent.mkdir(parents=True)
    snapshot.write_text(
        json.dumps(
            {
                "as_of": "2026-07-19",
                "final_profile": "product",
                "regression_suite": "quick",
                "local_cache_written": True,
                "working_tree_signature": "sig",
                "operational_readiness": "invalid",
                "platform_status": {"engineering_quality": []},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(health, "working_tree_signature", lambda _root: "sig")

    _, metadata = health._load_snapshot(
        tmp_path,
        as_of="2026-07-19",
        max_age_hours=24,
    )

    assert metadata["state"] == "stale"
    assert metadata["production_evidence"] is False


def test_health_snapshot_auto_prefers_fresh_full_evidence(tmp_path, monkeypatch):
    base = {
        "schema_version": 5,
        "status": "needs-review",
        "as_of": "2026-07-19",
        "final_profile": "product",
        "local_cache_written": True,
        "working_tree_signature": "sig",
        "operational_readiness": {"restore_drill": {"status": "pass"}},
        "platform_status": {"engineering_quality": {"status": "pass"}},
    }
    for suite in ("quick", "full"):
        snapshot = product_snapshot_path(tmp_path, suite)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_text(
            json.dumps({**base, "regression_suite": suite}),
            encoding="utf-8",
        )
    monkeypatch.setattr(health, "working_tree_signature", lambda _root: "sig")

    payload, metadata = health._load_snapshot(
        tmp_path,
        as_of="2026-07-19",
        max_age_hours=24,
    )

    assert payload["regression_suite"] == "full"
    assert metadata["suite"] == "full"
    assert metadata["fresh"] is True
    assert metadata["candidate_states"] == {"full": "fresh", "quick": "fresh"}


def test_product_gate_summary_is_bounded_and_excludes_heavy_evidence():
    payload = {
        "generated_at": "2026-07-19T00:00:00Z",
        "as_of": "2026-07-19",
        "final_profile": "product",
        "regression_suite": "full",
        "status": "needs-review",
        "terminal": False,
        "maturity_axes": {
            "schema_version": 2,
            "status": "needs-review",
            "terminal": False,
        },
        "platform_status": {
            "status": "pass",
            "hard_checks": {"knowledge_check": True},
        },
        "content_readiness": {
            "status": "needs-review",
            "project_readiness": {
                "project_count": 30,
                "structural_ready_count": 30,
                "evidence_ready_count": 0,
                "rows": [{"large": "x" * 10000}],
            },
        },
        "owner_and_real_evidence": {
            "pending_project_ids": ["p1", "p2"],
            "specialized_owner_requirements": [{"large": "x" * 10000}],
        },
        "operational_readiness": {
            "local_metrics": {
                "usage": {"invocation_count": 17, "observation_days": 4},
                "retrieval": {"feedback_count": 9},
            }
        },
        "adoption": {"ready": False, "evaluable": True},
        "blockers": [{"id": "owner-and-real-evidence-pending", "gap_type": "owner-review"}],
        "checks": {"large": "x" * 10000},
    }

    summary = product_gate_summary(payload)

    assert summary["schema_version"] == 4
    assert summary["projection"] == "product-final-gate-summary-v4"
    assert summary["status"] == "needs-review"
    assert summary["content"]["project_count"] == 30
    assert summary["owner_and_real_evidence"]["pending_project_count"] == 2
    assert summary["adoption"] == {
        "ready": False,
        "evaluable": True,
        "invocation_count": 17,
        "feedback_count": 9,
        "observation_days": 4,
    }
    for removed in (
        "gate_status",
        "final_status",
        "maturity_status",
        "overall_status",
        "platform_productization_complete",
        "local_delivery_complete",
        "remote_published",
        "offsite_restore_verified",
        "adoption_ready",
    ):
        assert removed not in summary
    assert "checks" not in summary
    assert "rows" not in summary["content"]
    assert len(json.dumps(summary, ensure_ascii=False)) < 10000


def test_candidate_integrity_detects_test_side_effects(tmp_path):
    run_rtk(tmp_path, ["git", "init"])
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("before\n", encoding="utf-8")
    run_rtk(tmp_path, ["git", "add", "tracked.txt"])
    before = working_tree_signature(tmp_path)

    assert _candidate_integrity(tmp_path, before)["status"] == "pass"
    tracked.write_text("after-change\n", encoding="utf-8")
    payload = _candidate_integrity(tmp_path, before)

    assert payload["status"] == "fail"
    assert payload["unchanged"] is False


def test_source_runtime_gate_requires_complete_all_registry_execution():
    complete = {
        "status": "pass",
        "scope": "all",
        "source_check_health_executed": True,
        "registry_source_count": 18,
        "row_count": 18,
        "executed_count": 18,
        "not_applicable_count": 0,
        "selected_source_ids": ["source-{}".format(index) for index in range(18)],
        "expected_source_ids": ["source-{}".format(index) for index in range(18)],
    }
    partial = dict(complete, row_count=7, executed_count=7)

    assert _source_runtime_ready(complete, 0) is True
    assert _source_runtime_ready(partial, 0) is False


def test_specialized_owner_requirements_are_manifest_driven():
    root = repository_root()
    policy, errors = load_product_policy(root)
    items_by_id = {row["id"]: row for row in registry_items(root)}

    assert errors == []
    baseline = evaluate_specialized_owner_requirements(policy, items_by_id)
    assert baseline["status"] == "pass"
    assert baseline["item_count"] == 3
    assert len(baseline["ready_ids"]) == 3

    extended = copy.deepcopy(policy)
    extended["specialized_owner_requirements"].append(
        {
            "id": "fixture-fourth-specialized-policy",
            "label_zh": "fixture",
            "item_requirements": [
                {
                    "item_id": "knowledge-hub-readiness-validation-20260713",
                    "expected": {"decision_status": "fixture-not-satisfied"},
                }
            ],
        }
    )
    result = evaluate_specialized_owner_requirements(extended, items_by_id)

    assert result["status"] == "pass"
    assert result["item_count"] == 4
    assert result["pending_ids"] == ["knowledge-hub-readiness-validation-20260713"]


def test_product_gate_split_keeps_helper_facade_and_module_budget():
    from tools.codex_assets.knowledge_hub import product_gate, product_gate_support

    assert product_gate._project_readiness is product_gate_support._project_readiness
    assert product_gate._restore_state is product_gate_support._restore_state
    root = repository_root()
    for relative in (
        "tools/codex_assets/knowledge_hub/product_gate.py",
        "tools/codex_assets/knowledge_hub/product_gate_support.py",
        "tools/codex_assets/knowledge_hub/product_gate_parallel.py",
    ):
        assert len((root / relative).read_text(encoding="utf-8").splitlines()) <= 800
