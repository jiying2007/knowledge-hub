from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest

from tools.codex_assets.knowledge_hub import operator_github_provider


class FakeTransport:
    def __init__(self, payloads: Dict[str, Any]) -> None:
        self.payloads = payloads
        self.calls: List[Tuple[str, str]] = []

    def __call__(self, path: str, token: str) -> Any:
        self.calls.append((path, token))
        if path not in self.payloads:
            raise AssertionError("unexpected provider path: {}".format(path))
        return self.payloads[path]


def _query(operation: str, target: str = "example/tool") -> dict:
    return {
        "provider": "github",
        "operation": operation,
        "target": target,
        "executed": False,
        "read_only": True,
        "transport_owned_by_provider": True,
    }


def test_source_discovery_resolves_exact_default_branch_revision() -> None:
    transport = FakeTransport(
        {
            "/repos/example/tool": {"default_branch": "main"},
            "/repos/example/tool/commits/main": {
                "sha": "abc123",
                "html_url": "https://github.com/example/tool/commit/abc123",
            },
        }
    )
    result = operator_github_provider.execute_query(
        _query("inspect-repository-source"), token="secret", transport=transport
    )

    assert result["status"] == "candidate-found"
    assert result["read_only"] is True
    assert result["network_performed"] is True
    assert result["canonical_write_performed"] is False
    assert result["automatic_binding_enabled"] is False
    assert result["candidate_count"] == 1
    candidate = result["candidates"][0]
    assert candidate["ref"] == "github://example/tool@abc123"
    assert candidate["provider_verified"] is True
    assert candidate["candidate_only"] is True
    assert candidate["eligible_for_binding"] is False
    assert transport.calls == [
        ("/repos/example/tool", "secret"),
        ("/repos/example/tool/commits/main", "secret"),
    ]


def test_workflow_discovery_keeps_only_completed_success_runs() -> None:
    path = "/repos/example/tool/actions/runs?status=completed&per_page=20"
    transport = FakeTransport(
        {
            path: {
                "workflow_runs": [
                    {
                        "id": 10,
                        "name": "quality",
                        "status": "completed",
                        "conclusion": "success",
                        "head_sha": "good",
                        "html_url": "https://github.com/example/tool/actions/runs/10",
                    },
                    {
                        "id": 11,
                        "name": "quality",
                        "status": "completed",
                        "conclusion": "failure",
                        "head_sha": "bad",
                    },
                ]
            }
        }
    )
    result = operator_github_provider.execute_query(
        _query("list-workflow-runs"), transport=transport
    )
    assert [row["ref"] for row in result["candidates"]] == [
        "github-actions://example/tool/runs/10"
    ]


def test_artifact_discovery_ignores_expired_actions_artifacts() -> None:
    transport = FakeTransport(
        {
            "/repos/example/tool/releases?per_page=10": [
                {
                    "id": 3,
                    "tag_name": "v1.0.0",
                    "draft": False,
                    "prerelease": False,
                    "assets": [
                        {
                            "id": 31,
                            "name": "bundle.tgz",
                            "digest": "sha256:asset",
                            "browser_download_url": "https://github.com/example/tool/releases/download/v1.0.0/bundle.tgz",
                        }
                    ],
                }
            ],
            "/repos/example/tool/actions/artifacts?per_page=20": {
                "artifacts": [
                    {
                        "id": 41,
                        "name": "signed",
                        "digest": "sha256:good",
                        "expired": False,
                    },
                    {
                        "id": 42,
                        "name": "old",
                        "digest": "sha256:old",
                        "expired": True,
                    },
                ]
            },
        }
    )
    result = operator_github_provider.execute_query(
        _query("list-release-assets-and-actions-artifacts"), transport=transport
    )
    refs = {row["ref"] for row in result["candidates"]}
    assert "github-release-asset://example/tool/31" in refs
    assert "github-actions-artifact://example/tool/41" in refs
    assert "github-actions-artifact://example/tool/42" not in refs
    assert all(row["eligible_for_binding"] is False for row in result["candidates"])


def test_release_discovery_distinguishes_immutable_release_from_tag() -> None:
    transport = FakeTransport(
        {
            "/repos/example/tool/releases?per_page=20": [
                {
                    "id": 5,
                    "tag_name": "v2.0.0",
                    "immutable": True,
                    "draft": False,
                    "prerelease": False,
                    "html_url": "https://github.com/example/tool/releases/tag/v2.0.0",
                },
                {
                    "id": 6,
                    "tag_name": "v2.1.0-rc1",
                    "immutable": True,
                    "draft": False,
                    "prerelease": True,
                },
            ],
            "/repos/example/tool/tags?per_page=20": [
                {"name": "v2.0.0", "commit": {"sha": "def456"}}
            ],
        }
    )
    result = operator_github_provider.execute_query(
        _query("list-releases-and-tags"), transport=transport
    )
    assert result["immutable_release_candidate_count"] == 1
    by_ref = {row["ref"]: row for row in result["candidates"]}
    assert by_ref["github-release://example/tool/5"]["details"][
        "meets_immutable_release_policy"
    ] is True
    assert by_ref["github-release://example/tool/6"]["details"][
        "meets_immutable_release_policy"
    ] is False
    assert by_ref["github-tag://example/tool/v2.0.0"]["details"][
        "meets_immutable_release_policy"
    ] is False


def test_projection_executes_only_github_queries_and_never_binds() -> None:
    path = "/repos/example/tool/actions/runs?status=completed&per_page=20"
    transport = FakeTransport({path: {"workflow_runs": []}})
    discovery = {
        "rows": [
            {
                "project_id": "tool",
                "field": "validation_refs",
                "provider_queries": [_query("list-workflow-runs")],
            },
            {
                "project_id": "internal",
                "field": "validation_refs",
                "provider_queries": [
                    {
                        "provider": "internal-git",
                        "operation": "list-ci-runs",
                        "target": "internal/tool",
                        "executed": False,
                        "read_only": True,
                    }
                ],
            },
        ]
    }
    result = operator_github_provider.execute_projection_queries(
        discovery, transport=transport
    )
    assert result["status"] == "pass"
    assert result["selected_query_count"] == 1
    assert result["executed_query_count"] == 1
    assert result["unsupported_query_count"] == 1
    assert result["canonical_write_performed"] is False
    assert result["automatic_binding_enabled"] is False
    assert result["unsupported"][0]["executed"] is False


def test_query_validation_fails_closed_before_transport() -> None:
    transport = FakeTransport({})
    with pytest.raises(operator_github_provider.GitHubProviderError):
        operator_github_provider.execute_query(
            _query("list-releases-and-tags", "https://evil.example/repo"),
            transport=transport,
        )
    assert transport.calls == []

    bad = _query("list-releases-and-tags")
    bad["read_only"] = False
    with pytest.raises(operator_github_provider.GitHubProviderError):
        operator_github_provider.execute_query(bad, transport=transport)
    assert transport.calls == []
