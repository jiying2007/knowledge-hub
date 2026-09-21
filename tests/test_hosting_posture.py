import io
import json
import urllib.error

import pytest

from tools.codex_assets.knowledge_hub import hosting_posture
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance


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
    assert report["default_branch_required_status_checks_observed"] is False
    assert report["default_branch_required_status_checks"] == []
    assert report["rulesets_capability"]["status"] == "not-probed"
    assert report["canonical_write"] is False


def test_hosting_posture_captures_default_branch_required_status_checks(
    monkeypatch, tmp_path
):
    _write_inventory(tmp_path)
    monkeypatch.setattr(
        hosting_posture,
        "_request_repository_metadata",
        lambda repository, token="": {
            "full_name": repository,
            "private": False,
            "visibility": "public",
            "default_branch": "master",
        },
    )
    monkeypatch.setattr(
        hosting_posture,
        "_rulesets_capability",
        lambda repository, token: {
            "status": "available",
            "reason": "",
            "http_status": 200,
            "ruleset_count": 1,
        },
    )
    monkeypatch.setattr(
        hosting_posture,
        "_request_default_branch_metadata",
        lambda repository, branch, token="": {
            "name": branch,
            "protection": {
                "required_status_checks": {
                    "contexts": ["Quality gate"],
                    "checks": [
                        {"context": "Exact-head security-critical review"}
                    ],
                }
            },
        },
    )

    report = hosting_posture.evaluate_hosting_posture(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="a" * 40,
        token="token",
    )

    assert report["default_branch_required_status_checks_observed"] is True
    assert report["default_branch_required_status_checks"] == [
        "Exact-head security-critical review",
        "Quality gate",
    ]


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


def test_rulesets_capability_classifies_private_plan_gate(monkeypatch):
    body = json.dumps(
        {
            "message": (
                "Upgrade to GitHub Pro or make this repository public "
                "to enable this feature."
            )
        }
    ).encode("utf-8")
    error = urllib.error.HTTPError(
        "https://api.github.com/repos/example/knowledge-hub/rulesets",
        403,
        "Forbidden",
        {},
        io.BytesIO(body),
    )

    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(hosting_posture.urllib.request, "urlopen", fail)

    result = hosting_posture._rulesets_capability(
        "example/knowledge-hub",
        "token",
    )

    assert result["status"] == "plan-gated"
    assert (
        result["reason"]
        == "private-repository-rulesets-require-upgrade-or-public"
    )
    assert result["http_status"] == 403
    assert result["ruleset_count"] == 0


def test_rulesets_capability_never_substitutes_for_branch_protection(
    monkeypatch, tmp_path
):
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
    monkeypatch.setattr(
        hosting_posture,
        "_rulesets_capability",
        lambda repository, token: {
            "status": "plan-gated",
            "reason": "private-repository-rulesets-require-upgrade-or-public",
            "http_status": 403,
            "ruleset_count": 0,
        },
    )
    monkeypatch.setattr(
        hosting_posture,
        "_request_default_branch_metadata",
        lambda repository, branch, token="": {
            "name": branch,
            "protection": {
                "required_status_checks": {
                    "contexts": [],
                    "checks": [],
                }
            },
        },
    )

    report = hosting_posture.evaluate_hosting_posture(
        tmp_path,
        repository="example/knowledge-hub",
        source_revision="a" * 40,
        token="token",
    )

    assert report["rulesets_capability"]["status"] == "plan-gated"
    assert report["default_branch_protected"] is False


def test_hosting_posture_matches_catalog_contract(monkeypatch, tmp_path):
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

    result = validate_instance(
        repository_root(),
        "hosting-posture-v1",
        report,
    )
    assert result["status"] == "pass", result["errors"]


def test_hosting_posture_cli_validates_contract_before_write():
    from pathlib import Path

    text = (
        Path("tools/codex_assets/knowledge_hub/hosting_posture_cli.py")
    ).read_text(encoding="utf-8")
    assert 'validate_instance(root, "hosting-posture-v1", payload)' in text
    assert "hosting posture contract validation failed" in text
