"""Bounded read-only GitHub provider execution for Operator discovery queries."""

from __future__ import annotations

import http.client
import json
import re
import urllib.parse
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

GITHUB_API_HOST = "api.github.com"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_CANDIDATES = 20
MAX_PROVIDER_QUERIES = 20
READ_ONLY_OPERATIONS = {
    "inspect-repository-source",
    "list-workflow-runs",
    "list-release-assets-and-actions-artifacts",
    "list-releases-and-tags",
}
_TARGET_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

Transport = Callable[[str, str], Any]


class GitHubProviderError(RuntimeError):
    """Raised when a bounded provider query cannot be executed safely."""


def _github_get(path: str, token: str) -> Any:
    if not path.startswith("/repos/"):
        raise GitHubProviderError("GitHub provider path must stay under /repos/")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "knowledge-hub-operator-discovery",
    }
    if token:
        headers["Authorization"] = "Bearer {}".format(token)
    connection = http.client.HTTPSConnection(GITHUB_API_HOST, timeout=10)
    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        payload = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, http.client.HTTPException) as exc:
        raise GitHubProviderError("GitHub provider GET failed: {}".format(exc)) from exc
    finally:
        connection.close()
    if len(payload) > MAX_RESPONSE_BYTES:
        raise GitHubProviderError("GitHub provider response exceeded {} bytes".format(MAX_RESPONSE_BYTES))
    if response.status < 200 or response.status >= 300:
        raise GitHubProviderError("GitHub provider GET returned HTTP {}".format(response.status))
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GitHubProviderError("GitHub provider returned invalid JSON") from exc


def _target(value: object) -> str:
    target = str(value or "")
    if not _TARGET_RE.fullmatch(target):
        raise GitHubProviderError("GitHub target must be an exact owner/repository key")
    return target


def _candidate(kind: str, ref: str, details: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "kind": kind,
        "ref": ref,
        "provenance": "github-read-only-api",
        "provider_verified": True,
        "candidate_only": True,
        "eligible_for_binding": False,
        "details": dict(details),
    }


def _mapping_rows(value: Any, field: str = "") -> List[Mapping[str, Any]]:
    rows = value.get(field, []) if field and isinstance(value, Mapping) else value
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _source_candidates(target: str, token: str, transport: Transport) -> List[Dict[str, Any]]:
    repository = transport("/repos/{}".format(target), token)
    if not isinstance(repository, Mapping):
        return []
    default_branch = str(repository.get("default_branch", ""))
    if not default_branch:
        return []
    commit = transport(
        "/repos/{}/commits/{}".format(target, urllib.parse.quote(default_branch, safe="")),
        token,
    )
    if not isinstance(commit, Mapping):
        return []
    sha = str(commit.get("sha", ""))
    if not sha:
        return []
    return [
        _candidate(
            "github-source-revision",
            "github://{}@{}".format(target, sha),
            {
                "repository": target,
                "default_branch": default_branch,
                "commit_sha": sha,
                "html_url": str(commit.get("html_url", "")),
                "exact_identity": True,
            },
        )
    ]


def _workflow_candidates(target: str, token: str, transport: Transport) -> List[Dict[str, Any]]:
    payload = transport(
        "/repos/{}/actions/runs?status=completed&per_page={}".format(target, MAX_CANDIDATES),
        token,
    )
    result: List[Dict[str, Any]] = []
    for row in _mapping_rows(payload, "workflow_runs"):
        if row.get("status") != "completed" or row.get("conclusion") != "success":
            continue
        run_id = str(row.get("id", ""))
        if not run_id:
            continue
        result.append(
            _candidate(
                "github-workflow-run",
                "github-actions://{}/runs/{}".format(target, run_id),
                {
                    "run_id": run_id,
                    "name": str(row.get("name", "")),
                    "head_sha": str(row.get("head_sha", "")),
                    "event": str(row.get("event", "")),
                    "html_url": str(row.get("html_url", "")),
                    "created_at": str(row.get("created_at", "")),
                    "conclusion": "success",
                },
            )
        )
        if len(result) >= MAX_CANDIDATES:
            break
    return result


def _artifact_candidates(target: str, token: str, transport: Transport) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    releases = transport("/repos/{}/releases?per_page=10".format(target), token)
    for release in _mapping_rows(releases):
        tag_name = str(release.get("tag_name", ""))
        immutable = release.get("immutable") is True
        tag_commit_sha = ""
        if (
            tag_name
            and immutable
            and release.get("draft") is False
            and release.get("prerelease") is False
        ):
            tag_commit = transport(
                "/repos/{}/commits/{}".format(
                    target, urllib.parse.quote(tag_name, safe="")
                ),
                token,
            )
            if isinstance(tag_commit, Mapping):
                tag_commit_sha = str(tag_commit.get("sha", ""))
        for asset in _mapping_rows(release.get("assets", [])):
            asset_id = str(asset.get("id", ""))
            if not asset_id:
                continue
            result.append(
                _candidate(
                    "github-release-asset",
                    "github-release-asset://{}/{}".format(target, asset_id),
                    {
                        "asset_id": asset_id,
                        "name": str(asset.get("name", "")),
                        "digest": str(asset.get("digest", "")),
                        "browser_download_url": str(asset.get("browser_download_url", "")),
                        "release_id": str(release.get("id", "")),
                        "tag_name": tag_name,
                        "release_immutable": immutable,
                        "release_tag_commit_sha": tag_commit_sha,
                        "release_draft": bool(release.get("draft", False)),
                        "release_prerelease": bool(release.get("prerelease", False)),
                    },
                )
            )
            if len(result) >= MAX_CANDIDATES:
                return result
    artifacts = transport(
        "/repos/{}/actions/artifacts?per_page={}".format(target, MAX_CANDIDATES),
        token,
    )
    for artifact in _mapping_rows(artifacts, "artifacts"):
        if bool(artifact.get("expired", False)):
            continue
        artifact_id = str(artifact.get("id", ""))
        if not artifact_id:
            continue
        workflow_run = artifact.get("workflow_run", {})
        if not isinstance(workflow_run, Mapping):
            workflow_run = {}
        result.append(
            _candidate(
                "github-actions-artifact",
                "github-actions-artifact://{}/{}".format(target, artifact_id),
                {
                    "artifact_id": artifact_id,
                    "name": str(artifact.get("name", "")),
                    "digest": str(artifact.get("digest", "")),
                    "created_at": str(artifact.get("created_at", "")),
                    "expires_at": str(artifact.get("expires_at", "")),
                    "expired": False,
                    "workflow_run_id": str(workflow_run.get("id", "")),
                    "workflow_run_head_sha": str(
                        workflow_run.get("head_sha", "")
                    ),
                    "workflow_run_head_branch": str(
                        workflow_run.get("head_branch", "")
                    ),
                },
            )
        )
        if len(result) >= MAX_CANDIDATES:
            break
    return result


def _release_candidates(target: str, token: str, transport: Transport) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    releases = transport("/repos/{}/releases?per_page={}".format(target, MAX_CANDIDATES), token)
    for release in _mapping_rows(releases):
        release_id = str(release.get("id", ""))
        if not release_id:
            continue
        immutable = release.get("immutable") is True
        draft = bool(release.get("draft", False))
        prerelease = bool(release.get("prerelease", False))
        result.append(
            _candidate(
                "github-release",
                "github-release://{}/{}".format(target, release_id),
                {
                    "release_id": release_id,
                    "tag_name": str(release.get("tag_name", "")),
                    "html_url": str(release.get("html_url", "")),
                    "draft": draft,
                    "prerelease": prerelease,
                    "immutable": immutable,
                    "meets_immutable_release_policy": immutable and not draft and not prerelease,
                },
            )
        )
        if len(result) >= MAX_CANDIDATES:
            return result
    tags = transport("/repos/{}/tags?per_page={}".format(target, MAX_CANDIDATES), token)
    for tag in _mapping_rows(tags):
        name = str(tag.get("name", ""))
        commit = tag.get("commit", {})
        sha = str(commit.get("sha", "")) if isinstance(commit, Mapping) else ""
        if not name:
            continue
        result.append(
            _candidate(
                "github-tag",
                "github-tag://{}/{}".format(target, urllib.parse.quote(name, safe="")),
                {
                    "tag_name": name,
                    "commit_sha": sha,
                    "meets_immutable_release_policy": False,
                },
            )
        )
        if len(result) >= MAX_CANDIDATES:
            break
    return result


def execute_query(
    query: Mapping[str, Any],
    token: str = "",
    transport: Optional[Transport] = None,
) -> Dict[str, Any]:
    if str(query.get("provider", "")) != "github":
        raise GitHubProviderError("only github provider queries are supported")
    if query.get("read_only") is not True or query.get("executed") is not False:
        raise GitHubProviderError("provider query must be an unexecuted read-only query")
    operation = str(query.get("operation", ""))
    if operation not in READ_ONLY_OPERATIONS:
        raise GitHubProviderError("unsupported GitHub read-only operation: {}".format(operation))
    target = _target(query.get("target"))
    caller = transport or _github_get
    if operation == "inspect-repository-source":
        candidates = _source_candidates(target, token, caller)
    elif operation == "list-workflow-runs":
        candidates = _workflow_candidates(target, token, caller)
    elif operation == "list-release-assets-and-actions-artifacts":
        candidates = _artifact_candidates(target, token, caller)
    else:
        candidates = _release_candidates(target, token, caller)
    immutable_count = sum(
        1
        for candidate in candidates
        if candidate.get("details", {}).get("meets_immutable_release_policy") is True
    )
    return {
        "schema_version": 1,
        "provider": "github",
        "operation": operation,
        "target": target,
        "status": "candidate-found" if candidates else "no-candidate",
        "executed": True,
        "read_only": True,
        "network_performed": True,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "candidate_count": len(candidates),
        "immutable_release_candidate_count": immutable_count,
        "candidates": candidates,
    }


def execute_projection_queries(
    discovery: Mapping[str, Any],
    token: str = "",
    project_id: str = "",
    field: str = "",
    transport: Optional[Transport] = None,
) -> Dict[str, Any]:
    selected: List[Tuple[str, str, Mapping[str, Any]]] = []
    unsupported: List[Dict[str, Any]] = []
    for row in discovery.get("rows", []):
        if not isinstance(row, Mapping):
            continue
        row_project = str(row.get("project_id", ""))
        row_field = str(row.get("field", ""))
        if project_id and row_project != project_id:
            continue
        if field and row_field != field:
            continue
        for query in row.get("provider_queries", []):
            if not isinstance(query, Mapping):
                continue
            if str(query.get("provider", "")) != "github":
                unsupported.append(
                    {
                        "project_id": row_project,
                        "field": row_field,
                        "provider": str(query.get("provider", "")),
                        "operation": str(query.get("operation", "")),
                        "target": str(query.get("target", "")),
                        "status": "unsupported-provider",
                        "executed": False,
                    }
                )
                continue
            selected.append((row_project, row_field, query))
            if len(selected) >= MAX_PROVIDER_QUERIES:
                break
        if len(selected) >= MAX_PROVIDER_QUERIES:
            break
    results = []
    errors = []
    for row_project, row_field, query in selected:
        try:
            result = execute_query(query, token=token, transport=transport)
            result["project_id"] = row_project
            result["field"] = row_field
            results.append(result)
        except GitHubProviderError as exc:
            errors.append(
                {
                    "project_id": row_project,
                    "field": row_field,
                    "provider": "github",
                    "operation": str(query.get("operation", "")),
                    "target": str(query.get("target", "")),
                    "error": str(exc),
                }
            )
    return {
        "schema_version": 1,
        "projection": "knowledge-operator-github-provider-v1",
        "status": "error" if errors else "pass",
        "read_only": True,
        "network_performed": bool(selected),
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "selected_query_count": len(selected),
        "executed_query_count": len(results),
        "unsupported_query_count": len(unsupported),
        "error_count": len(errors),
        "results": results,
        "unsupported": unsupported,
        "errors": errors,
    }
