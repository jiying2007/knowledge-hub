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


def _records(*names, protected=True):
    return [{"name": name, "protected": protected} for name in names]


def test_remote_branch_inventory_passes_when_retirement_candidates_are_absent(
    monkeypatch, tmp_path
):
    _write_lifecycle(tmp_path)
    monkeypatch.setattr(
        remote_branch_inventory,
        "fetch_remote_branch_records",
        lambda repository, token="": _records(
            "master", "dependabot/pip/example", protected=True
        ),
    )

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="a" * 40,
    )

    assert report["status"] == "pass"
    assert report["remaining_candidates"] == []
    assert report["unexpected_implementation_branches"] == []
    assert report["default_branch"] == "master"
    assert report["default_branch_present"] is True
    assert report["default_branch_protection_observed"] is True
    assert report["default_branch_protected"] is True
    assert report["observation_count"] == 1
    assert report["converged_after_retry"] is False


def test_remote_branch_inventory_keeps_unprotected_default_branch_as_remote_fact(
    monkeypatch, tmp_path
):
    _write_lifecycle(tmp_path)
    monkeypatch.setattr(
        remote_branch_inventory,
        "fetch_remote_branch_records",
        lambda repository, token="": _records("master", protected=False),
    )

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="4" * 40,
    )

    assert report["status"] == "pass"
    assert report["default_branch_present"] is True
    assert report["default_branch_protection_observed"] is True
    assert report["default_branch_protected"] is False


def test_remote_branch_inventory_marks_missing_protection_field_unobserved(
    monkeypatch, tmp_path
):
    _write_lifecycle(tmp_path)
    monkeypatch.setattr(
        remote_branch_inventory,
        "fetch_remote_branch_records",
        lambda repository, token="": [{"name": "master", "protected": None}],
    )

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="5" * 40,
    )

    assert report["status"] == "pass"
    assert report["default_branch_present"] is True
    assert report["default_branch_protection_observed"] is False
    assert report["default_branch_protected"] is False


def test_remote_branch_inventory_marks_missing_default_branch(monkeypatch, tmp_path):
    _write_lifecycle(tmp_path)
    monkeypatch.setattr(
        remote_branch_inventory,
        "fetch_remote_branch_records",
        lambda repository, token="": _records("develop", protected=True),
    )

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="6" * 40,
    )

    assert report["status"] == "pass"
    assert report["default_branch_present"] is False
    assert report["default_branch_protection_observed"] is False
    assert report["default_branch_protected"] is False


def test_fetch_remote_branches_remains_name_projection(monkeypatch):
    monkeypatch.setattr(
        remote_branch_inventory,
        "fetch_remote_branch_records",
        lambda repository, token="": _records("master", "topic", protected=True),
    )

    assert remote_branch_inventory.fetch_remote_branches("example/knowledge-hub") == [
        "master",
        "topic",
    ]


def test_remote_branch_inventory_reports_remaining_candidates(monkeypatch, tmp_path):
    _write_lifecycle(tmp_path)
    monkeypatch.setattr(
        remote_branch_inventory,
        "fetch_remote_branch_records",
        lambda repository, token="": _records("master", "codex/absorbed"),
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
        "fetch_remote_branch_records",
        lambda repository, token="": _records(
            "master",
            "codex/new-unregistered-work",
            "arch/new-unregistered-architecture",
            "dependabot/pip/example",
        ),
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
            _records("master", "codex/just-merged"),
            _records("master"),
        ]
    )
    monkeypatch.setattr(
        remote_branch_inventory,
        "fetch_remote_branch_records",
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
            return _records("master", "codex/just-merged")
        raise KnowledgeHubError("remote branch inventory request failed")

    monkeypatch.setattr(remote_branch_inventory, "fetch_remote_branch_records", _fetch)

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="1" * 40,
        convergence_attempts=3,
        convergence_delay_seconds=0,
    )

    assert report["status"] == "blocked"
    assert report["unexpected_implementation_branches"] == ["codex/just-merged"]
    assert report["default_branch_present"] is True
    assert report["default_branch_protected"] is True
    assert report["observation_count"] == 1
    assert "request failed" in report["error"]


def test_remote_branch_inventory_preserves_blocked_evidence(monkeypatch, tmp_path):
    _write_lifecycle(tmp_path)

    def _blocked(repository, token=""):
        raise KnowledgeHubError("remote branch inventory request failed")

    monkeypatch.setattr(remote_branch_inventory, "fetch_remote_branch_records", _blocked)

    report = remote_branch_inventory.evaluate_remote_branch_inventory(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="c" * 40,
    )

    assert report["status"] == "blocked"
    assert report["remaining_candidates"] == ["arch/retired", "codex/absorbed"]
    assert report["default_branch_present"] is False
    assert report["default_branch_protection_observed"] is False
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

    with pytest.raises(KnowledgeHubError, match="default branch name"):
        remote_branch_inventory.evaluate_remote_branch_inventory(
            tmp_path,
            repository="example/knowledge-hub",
            source_revision="d" * 40,
            default_branch="refs/heads/master",
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
