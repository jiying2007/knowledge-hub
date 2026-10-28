"""Read-only evidence candidate discovery for Operator machine actions."""

from __future__ import annotations

import pathlib
from collections import Counter
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError, load_json, load_jsonl, utc_timestamp

DISCOVERY_FIELDS = {"source_refs", "validation_refs", "artifact_refs", "release_ref"}
MAX_CANDIDATES_PER_ACTION = 20


def _object_rows(
    root: pathlib.Path, relative_path: str, field: str
) -> Tuple[List[Mapping[str, Any]], List[str]]:
    try:
        payload = load_json(root / relative_path, {}) or {}
    except KnowledgeHubError as exc:
        return [], ["{}: {}".format(relative_path, exc)]
    if not isinstance(payload, Mapping) or field not in payload:
        return [], ["{}: missing {} collection".format(relative_path, field)]
    rows = payload[field]
    if not isinstance(rows, list) or any(
        not isinstance(row, Mapping) for row in rows
    ):
        return [], ["{} field {} must be a list of objects".format(relative_path, field)]
    return rows, []


def _item_rows(root: pathlib.Path) -> Tuple[List[Mapping[str, Any]], List[str]]:
    try:
        return load_jsonl(root / "registry/items.jsonl"), []
    except KnowledgeHubError as exc:
        return [], ["registry/items.jsonl: {}".format(exc)]


def _index(rows: Sequence[Mapping[str, Any]], key: str) -> Dict[str, Mapping[str, Any]]:
    result: Dict[str, Mapping[str, Any]] = {}
    for row in rows:
        identity = row.get(key)
        if not isinstance(identity, str) or not identity:
            raise ValueError("registry row missing valid {} identity".format(key))
        if identity in result:
            raise ValueError("duplicate {} registry identity".format(key))
        result[identity] = row
    return result


def _repo_rows(
    route: Mapping[str, Any], repositories: Mapping[str, Mapping[str, Any]]
) -> List[Mapping[str, Any]]:
    result = []
    repo_refs = route.get("repo_refs", [])
    if not isinstance(repo_refs, list) or any(
        not isinstance(ref, str) for ref in repo_refs
    ):
        raise ValueError("project route repo_refs must be a list of strings")
    for repo_id in repo_refs:
        row = repositories.get(repo_id)
        if row is not None:
            result.append(row)
    return result


def _candidate(
    *,
    kind: str,
    ref: str,
    provenance: str,
    details: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "kind": kind,
        "ref": ref,
        "provenance": provenance,
        "candidate_only": True,
        "eligible_for_binding": False,
        "details": dict(details),
    }


def _source_candidates(
    route: Mapping[str, Any],
    repositories: Mapping[str, Mapping[str, Any]],
    sources: Mapping[str, Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for repo in _repo_rows(route, repositories):
        repo_id = str(repo.get("repo_id", ""))
        candidates.append(
            _candidate(
                kind="repository-route",
                ref="repo://{}".format(repo_id),
                provenance="registry/project-routes.json+registry/repositories.json",
                details={
                    "repo_id": repo_id,
                    "remote_kind": str(repo.get("remote_kind", "")),
                    "remote_key": repo.get("remote_key"),
                    "workspace_ref": str(repo.get("workspace_ref", "")),
                    "lifecycle": str(repo.get("lifecycle", "")),
                },
            )
        )
    source_ids = route.get("default_source_ids", [])
    if not isinstance(source_ids, list) or any(
        not isinstance(ref, str) for ref in source_ids
    ):
        raise ValueError("project route default_source_ids must be a list of strings")
    for source_id in source_ids:
        source = sources.get(source_id)
        if source is None:
            continue
        candidates.append(
            _candidate(
                kind="registered-source",
                ref="source://{}".format(source_id),
                provenance="registry/project-routes.json+registry/sources.json",
                details={
                    "source_id": str(source_id),
                    "path": str(source.get("path", "")),
                    "status": str(source.get("status", "")),
                    "owner": str(source.get("owner", "")),
                },
            )
        )
    return candidates[:MAX_CANDIDATES_PER_ACTION]


def _validation_candidates(
    route: Mapping[str, Any], items: Sequence[Mapping[str, Any]]
) -> List[Dict[str, Any]]:
    validation_path = str(route.get("validation_path", "")).rstrip("/")
    if not validation_path:
        return []
    prefix = validation_path + "/"
    result: List[Dict[str, Any]] = []
    for row in items:
        path = str(row.get("path", ""))
        if not path or (path != validation_path and not path.startswith(prefix)):
            continue
        item_id = str(row.get("id", ""))
        result.append(
            _candidate(
                kind="validation-registry-item",
                ref="item://{}".format(item_id) if item_id else path,
                provenance="registry/items.jsonl",
                details={
                    "item_id": item_id,
                    "path": path,
                    "kind": str(row.get("kind", "")),
                    "status": str(row.get("status", "")),
                },
            )
        )
        if len(result) >= MAX_CANDIDATES_PER_ACTION:
            break
    return result


def _operation(field: str, remote_kind: str) -> str:
    if field == "release_ref":
        return (
            "list-releases-and-tags"
            if remote_kind in {"github", "gitee"}
            else "list-release-identities-and-tags"
        )
    if field == "artifact_refs":
        return (
            "list-release-assets-and-actions-artifacts"
            if remote_kind == "github"
            else "list-build-artifacts"
        )
    if field == "validation_refs":
        return "list-workflow-runs" if remote_kind == "github" else "list-ci-runs"
    return "inspect-repository-source"


def _provider_queries(
    field: str, repos: Sequence[Mapping[str, Any]]
) -> List[Dict[str, Any]]:
    queries = []
    for repo in repos:
        remote_key = repo.get("remote_key", {})
        if remote_key is None or remote_key == {}:
            continue
        if not isinstance(remote_key, Mapping):
            raise ValueError("repository remote_key must be an object")
        target = remote_key.get("repository_path")
        if not isinstance(target, str) or not target:
            raise ValueError("repository remote_key missing repository_path")
        remote_kind = str(repo.get("remote_kind", ""))
        queries.append(
            {
                "provider": remote_kind or "repository-provider",
                "operation": _operation(field, remote_kind),
                "target": target,
                "executed": False,
                "read_only": True,
                "transport_owned_by_provider": True,
            }
        )
    return queries[:MAX_CANDIDATES_PER_ACTION]


def _discover_action(
    action: Mapping[str, Any],
    routes: Mapping[str, Mapping[str, Any]],
    repositories: Mapping[str, Mapping[str, Any]],
    sources: Mapping[str, Mapping[str, Any]],
    items: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    project_id = str(action.get("project_id", ""))
    field = str(action.get("field", ""))
    route = routes.get(project_id, {})
    repos = _repo_rows(route, repositories)
    candidates: List[Dict[str, Any]] = []
    if field == "source_refs":
        candidates = _source_candidates(route, repositories, sources)
    elif field == "validation_refs":
        candidates = _validation_candidates(route, items)
    queries = _provider_queries(field, repos) if field in DISCOVERY_FIELDS else []
    status = (
        "candidate-found"
        if candidates
        else "provider-required"
        if queries
        else "no-candidate"
    )
    return {
        "action_id": str(action.get("id", "")),
        "project_id": project_id,
        "field": field,
        "status": status,
        "candidate_count": len(candidates),
        "provider_query_count": len(queries),
        "candidates": candidates,
        "provider_queries": queries,
        "escalation_class": str(action.get("escalation_class", "")),
        "canonical_write_performed": False,
        "network_performed": False,
    }


def _unavailable(errors: Sequence[str]) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "unavailable",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "action_count": 0,
        "candidate_found_count": 0,
        "provider_required_count": 0,
        "no_candidate_count": 0,
        "provider_query_count": 0,
        "rows": [],
        "errors": list(errors),
    }


def build_discovery_projection(
    root: pathlib.Path, action_queue: Mapping[str, Any]
) -> Dict[str, Any]:
    route_rows, route_errors = _object_rows(
        root, "registry/project-routes.json", "routes"
    )
    repo_rows, repo_errors = _object_rows(
        root, "registry/repositories.json", "repositories"
    )
    source_rows, source_errors = _object_rows(
        root, "registry/sources.json", "sources"
    )
    items, item_errors = _item_rows(root)
    errors = route_errors + repo_errors + source_errors + item_errors
    if errors:
        return _unavailable(errors)
    action_rows = action_queue.get("actions", [])
    if not isinstance(action_rows, list) or any(
        not isinstance(row, Mapping) for row in action_rows
    ):
        return _unavailable(["operator action queue must contain object actions"])
    try:
        routes = _index(route_rows, "project_id")
        repositories = _index(repo_rows, "repo_id")
        sources = _index(source_rows, "id")
        machine_actions = [
            row
            for row in action_rows
            if row.get("execution_class") == "machine-discovery"
        ]
        rows = [
            _discover_action(row, routes, repositories, sources, items)
            for row in machine_actions
        ]
    except (KeyError, TypeError, ValueError) as exc:
        return _unavailable(["invalid discovery input: {}".format(exc)])
    counts = Counter(str(row.get("status", "")) for row in rows)
    provider_query_count = sum(
        int(row.get("provider_query_count", 0) or 0) for row in rows
    )
    return {
        "schema_version": 1,
        "projection": "knowledge-operator-discovery-v1",
        "generated_at": utc_timestamp(),
        "status": "pass" if not rows else "needs-provider"
        if counts.get("provider-required", 0)
        else "candidates-found",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "action_count": len(rows),
        "candidate_found_count": counts.get("candidate-found", 0),
        "provider_required_count": counts.get("provider-required", 0),
        "no_candidate_count": counts.get("no-candidate", 0),
        "provider_query_count": provider_query_count,
        "rows": rows,
        "errors": [],
    }
