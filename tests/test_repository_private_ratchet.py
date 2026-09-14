import json
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.repository_private_ratchet import (
    GAP_ID,
    build_repository_private_candidate,
)


REVISION = "a" * 40


def _write(path, value):
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def _registry():
    return {
        "schema_version": 2,
        "repository_security_target": {"private_required": True},
        "external_closure_gaps": [
            {
                "id": GAP_ID,
                "owner": "repository-admin",
                "required": True,
                "status": "open",
                "reason": "hosting boundary required",
            },
            {
                "id": "connector-provider-pilot",
                "required": True,
                "status": "open",
                "reason": "provider evidence required",
            },
        ],
    }


def _metadata(private=True):
    return {
        "full_name": "jiying2007/knowledge-hub",
        "private": private,
        "visibility": "private" if private else "public",
        "html_url": "https://github.com/jiying2007/knowledge-hub",
    }


def _build(tmp_path, *, metadata=None, registry=None):
    registry_path = tmp_path / "registry.json"
    metadata_path = tmp_path / "metadata.json"
    _write(registry_path, registry or _registry())
    _write(metadata_path, metadata or _metadata())
    return build_repository_private_candidate(
        registry_path=registry_path,
        repository_metadata_path=metadata_path,
        expected_repository="jiying2007/knowledge-hub",
        source_revision=REVISION,
        run_id=123,
        run_attempt=1,
    )


def test_private_hosting_closes_only_repository_boundary_in_candidate(tmp_path):
    candidate, proposal = _build(tmp_path)
    gaps = {row["id"]: row for row in candidate["external_closure_gaps"]}
    assert gaps[GAP_ID]["status"] == "closed"
    assert gaps[GAP_ID]["evidence"]["private"] is True
    assert gaps["connector-provider-pilot"]["status"] == "open"
    assert proposal["status"] == "ready-for-reviewed-ratchet"
    assert proposal["review_required"] is True
    assert proposal["canonical_write_performed"] is False
    assert proposal["gap_id"] == GAP_ID


def test_public_repository_fails_closed(tmp_path):
    with pytest.raises(KnowledgeHubError, match="private must be true"):
        _build(tmp_path, metadata=_metadata(private=False))


def test_repository_identity_mismatch_fails_closed(tmp_path):
    metadata = _metadata()
    metadata["full_name"] = "other/repository"
    with pytest.raises(KnowledgeHubError, match="does not match"):
        _build(tmp_path, metadata=metadata)


def test_preclosed_or_prepopulated_gap_fails_closed(tmp_path):
    registry = _registry()
    registry["external_closure_gaps"][0]["status"] = "closed"
    with pytest.raises(KnowledgeHubError, match="required/open"):
        _build(tmp_path, registry=registry)

    registry = _registry()
    registry["external_closure_gaps"][0]["evidence_refs"] = ["fake"]
    with pytest.raises(KnowledgeHubError, match="must not contain closure evidence"):
        _build(tmp_path, registry=registry)


def test_workflow_is_manual_read_only_and_canonical_no_write():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/repository-private-ratchet-candidate.yml").read_text(
        encoding="utf-8"
    )
    cli = (
        root / "tools/codex_assets/knowledge_hub/repository_private_ratchet_cli.py"
    ).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "contents: read" in workflow
    assert "contents: write" not in workflow
    assert "pull-requests: write" not in workflow
    assert 'gh api "repos/${GITHUB_REPOSITORY}"' in workflow
    assert "git diff --exit-code -- registry/knowledge-platform-p5-p10.json" in workflow
    assert "repository privacy ratchet must never write the canonical registry" in cli
