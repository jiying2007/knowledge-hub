import pytest

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.final_gate_cli import main as final_gate_main
from tools.codex_assets.knowledge_hub.common import run_rtk
from tools.codex_assets.knowledge_hub.product_gate import _git_delivery_state
from tools.codex_assets.knowledge_hub.product_gate import _project_readiness
from tools.codex_assets.knowledge_hub.product_gate import _restore_state


def test_product_readiness_separates_structure_from_real_evidence():
    payload = _project_readiness(repository_root())
    assert payload["project_count"] == 31
    assert payload["slot_count"] == 124
    assert payload["structural_ready_count"] == 31
    assert "source_mapping_ready_count" in payload
    assert payload["route_matrix_failure_count"] == 0
    assert payload["evidence_ready_count"] < payload["project_count"]


def test_product_is_the_only_executable_final_profile():
    root = repository_root()
    assert not (root / "tools/knowledge-product-gate.sh").exists()
    assert not (root / "tools/knowledge-mature-auto-approval.sh").exists()
    with pytest.raises(SystemExit) as error:
        final_gate_main(["--final-profile", "mature", "--json"])
    assert error.value.code == 2


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
