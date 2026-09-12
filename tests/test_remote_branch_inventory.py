import json

from tools.codex_assets.knowledge_hub import remote_branch_inventory
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


def _write_lifecycle(tmp_path):
    path = tmp_path / "registry/branch-lifecycle.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "retirement_candidates": [
                    {"branch": "codex/absorbed", "reason": "absorbed"},
                    {"branch": "arch/retired", "reason": "retired"},
                ]
            }
        ),
        encoding="utf-8",
    )


def test_remote_branch_inventory_passes_when_retirement_candidates_are_absent(
    monkeypatch, tmp_path
):
    _write_lifecycle(tmp_path)
    monkeypatch.setattr(
        remote_branch_inventory,
        "fetch_remote_branches",
        lambda repository, token="": ["master", "dependabot/pip/example"],
    )

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="a" * 40,
    )

    assert report["status"] == "pass"
    assert report["remaining_candidates"] == []


def test_remote_branch_inventory_reports_remaining_candidates(monkeypatch, tmp_path):
    _write_lifecycle(tmp_path)
    monkeypatch.setattr(
        remote_branch_inventory,
        "fetch_remote_branches",
        lambda repository, token="": ["master", "codex/absorbed"],
    )

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="b" * 40,
    )

    assert report["status"] == "needs-review"
    assert report["remaining_candidates"] == ["codex/absorbed"]


def test_remote_branch_inventory_preserves_blocked_evidence(monkeypatch, tmp_path):
    _write_lifecycle(tmp_path)

    def _blocked(repository, token=""):
        raise KnowledgeHubError("remote branch inventory request failed")

    monkeypatch.setattr(remote_branch_inventory, "fetch_remote_branches", _blocked)

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="c" * 40,
    )

    assert report["status"] == "blocked"
    assert report["remaining_candidates"] == ["arch/retired", "codex/absorbed"]
    assert "request failed" in report["error"]
