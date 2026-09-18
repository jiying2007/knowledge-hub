import json

import pytest

from tools.codex_assets.knowledge_hub import hosting_posture
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


def _write_inventory(tmp_path, repository="example/knowledge-hub", revision=None):
    path = tmp_path / ".cache/knowledge-hub/remote-branch-inventory.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "repository": repository,
                "source_revision": revision or "a" * 40,
                "default_branch": "master",
                "default_branch_present": True,
                "default_branch_protection_observed": True,
                "default_branch_protected": False,
            }
        ),
        encoding="utf-8",
    )


def test_hosting_posture_binds_private_fact_and_branch_inventory(monkeypatch, tmp_path):
    _write_inventory(tmp_path)
    monkeypatch.setattr(
        hosting_posture,
        "_request_repository_metadata",
        lambda repository, token="": {
            "full_name": repository,
            "private": True,
            "visibility": "private",
            "default_branch": "master",
        },
    )

    report = hosting_posture.evaluate_hosting_posture(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="a" * 40,
    )

    assert report["status"] == "pass"
    assert report["repository_private"] is True
    assert report["repository_visibility"] == "private"
    assert report["default_branch_protected"] is False
    assert report["canonical_write"] is False


def test_hosting_posture_rejects_stale_branch_inventory(monkeypatch, tmp_path):
    _write_inventory(tmp_path, revision="b" * 40)
    monkeypatch.setattr(
        hosting_posture,
        "_request_repository_metadata",
        lambda repository, token="": {
            "full_name": repository,
            "private": True,
            "visibility": "private",
            "default_branch": "master",
        },
    )

    with pytest.raises(KnowledgeHubError, match="source revision mismatch"):
        hosting_posture.evaluate_hosting_posture(
            tmp_path,
            repository="example/knowledge-hub",
            source_revision="a" * 40,
        )


def test_hosting_posture_rejects_default_branch_drift(monkeypatch, tmp_path):
    _write_inventory(tmp_path)
    monkeypatch.setattr(
        hosting_posture,
        "_request_repository_metadata",
        lambda repository, token="": {
            "full_name": repository,
            "private": True,
            "visibility": "private",
            "default_branch": "main",
        },
    )

    with pytest.raises(KnowledgeHubError, match="default branch"):
        hosting_posture.evaluate_hosting_posture(
            tmp_path,
            repository="example/knowledge-hub",
            source_revision="a" * 40,
        )


def test_hosting_posture_rejects_branch_inventory_path_escape(tmp_path):
    outside = tmp_path.parent / "outside.json"
    outside.write_text("{}", encoding="utf-8")

    with pytest.raises(KnowledgeHubError):
        hosting_posture.evaluate_hosting_posture(
            tmp_path,
            repository="example/knowledge-hub",
            source_revision="a" * 40,
            branch_inventory="../outside.json",
        )
