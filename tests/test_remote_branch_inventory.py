import json

import pytest

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
    assert report["unexpected_implementation_branches"] == []
    assert report["observation_count"] == 1
    assert report["converged_after_retry"] is False


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
        convergence_attempts=1,
    )

    assert report["status"] == "needs-review"
    assert report["remaining_candidates"] == ["codex/absorbed"]
    assert report["unexpected_implementation_branches"] == []


def test_remote_branch_inventory_detects_unknown_implementation_residue(
    monkeypatch, tmp_path
):
    _write_lifecycle(tmp_path)
    monkeypatch.setattr(
        remote_branch_inventory,
        "fetch_remote_branches",
        lambda repository, token="": [
            "master",
            "codex/new-unregistered-work",
            "arch/new-unregistered-architecture",
            "dependabot/pip/example",
        ],
    )

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="e" * 40,
        convergence_attempts=1,
    )

    assert report["status"] == "needs-review"
    assert report["remaining_candidates"] == []
    assert report["implementation_branches"] == [
        "arch/new-unregistered-architecture",
        "codex/new-unregistered-work",
    ]
    assert report["unexpected_implementation_branches"] == [
        "arch/new-unregistered-architecture",
        "codex/new-unregistered-work",
    ]


def test_remote_branch_inventory_allows_bounded_gc_convergence(monkeypatch, tmp_path):
    _write_lifecycle(tmp_path)
    observations = iter(
        [
            ["master", "codex/just-merged"],
            ["master"],
        ]
    )
    monkeypatch.setattr(
        remote_branch_inventory,
        "fetch_remote_branches",
        lambda repository, token="": next(observations),
    )

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="f" * 40,
        convergence_attempts=3,
        convergence_delay_seconds=0,
    )

    assert report["status"] == "pass"
    assert report["branches"] == ["master"]
    assert report["observation_count"] == 2
    assert report["converged_after_retry"] is True
    assert report["observations"][0]["unexpected_implementation_branches"] == [
        "codex/just-merged"
    ]
    assert report["observations"][1]["unexpected_implementation_branches"] == []


def test_remote_branch_inventory_blocks_if_retry_request_fails(monkeypatch, tmp_path):
    _write_lifecycle(tmp_path)
    calls = {"count": 0}

    def _fetch(repository, token=""):
        calls["count"] += 1
        if calls["count"] == 1:
            return ["master", "codex/just-merged"]
        raise KnowledgeHubError("remote branch inventory request failed")

    monkeypatch.setattr(remote_branch_inventory, "fetch_remote_branches", _fetch)

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="1" * 40,
        convergence_attempts=3,
        convergence_delay_seconds=0,
    )

    assert report["status"] == "blocked"
    assert report["unexpected_implementation_branches"] == ["codex/just-merged"]
    assert report["observation_count"] == 1
    assert "request failed" in report["error"]


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
    assert report["observation_count"] == 0
    assert "request failed" in report["error"]


def test_remote_branch_inventory_rejects_unbound_identity(tmp_path):
    _write_lifecycle(tmp_path)

    with pytest.raises(KnowledgeHubError, match="repository must use owner/name form"):
        remote_branch_inventory.evaluate_remote_branch_inventory(
            tmp_path,
            repository="https://github.com/example/knowledge-hub",
            source_revision="d" * 40,
        )

    with pytest.raises(KnowledgeHubError, match="source revision must be a full Git object id"):
        remote_branch_inventory.evaluate_remote_branch_inventory(
            tmp_path,
            repository="example/knowledge-hub",
            source_revision="main",
        )


def test_remote_branch_inventory_rejects_invalid_convergence_budget(tmp_path):
    _write_lifecycle(tmp_path)

    with pytest.raises(KnowledgeHubError, match="convergence_attempts"):
        remote_branch_inventory.evaluate_remote_branch_inventory(
            tmp_path,
            repository="example/knowledge-hub",
            source_revision="2" * 40,
            convergence_attempts=0,
        )

    with pytest.raises(KnowledgeHubError, match="convergence_delay_seconds"):
        remote_branch_inventory.evaluate_remote_branch_inventory(
            tmp_path,
            repository="example/knowledge-hub",
            source_revision="3" * 40,
            convergence_delay_seconds=-1,
        )
