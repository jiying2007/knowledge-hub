"""Exact, append-only repository identity registration for existing projects."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from .common import KnowledgeHubError, load_json, pretty_json, file_sha256
from .provider_subjects import subject, digest, authorize, read_guard
from .remote_identity import parse_remote, identity_key
from .store import RepositoryTransaction, snapshot_inputs


RESPONSE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "status", "persisted", "write_performed", "read_only",
                 "subject_ref", "repository_id", "remote_key", "expected_hash"],
    "properties": {
        "schema_version": {"const": "knowledge-provider.repository-registration/v1"},
        "status": {"enum": ["PLANNED", "REGISTERED", "ALREADY_REGISTERED"]},
        "persisted": {"type": "boolean"}, "write_performed": {"type": "boolean"},
        "read_only": {"type": "boolean"}, "authorization_required": {"type": "boolean"},
        "repository_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{0,80}$"},
        "expected_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "subject_ref": {"type": "object", "additionalProperties": False, "required": ["type", "id"],
                        "properties": {"type": {"const": "project"}, "id": {"type": "string"}}},
        "remote_key": {"type": "object", "additionalProperties": False,
                       "required": ["provider_id", "repository_path"],
                       "properties": {"provider_id": {"type": "string"}, "repository_path": {"type": "string"}}},
        # Transaction format is the existing Provider transaction contract.
        "transaction": {"type": "object"},
    },
}


def _receipt(**value):
    value["schema_version"] = "knowledge-provider.repository-registration/v1"
    value.setdefault("write_performed", False)
    value.setdefault("read_only", not value["write_performed"])
    from jsonschema import Draft202012Validator
    if list(Draft202012Validator(RESPONSE_SCHEMA).iter_errors(value)):
        raise KnowledgeHubError("SCHEMA_INVALID")
    return value



def _registration_remote(repository_id, remote_url):
    if not isinstance(repository_id, str) or re.fullmatch(r"[a-z0-9][a-z0-9-]{0,80}", repository_id) is None:
        raise KnowledgeHubError("SCHEMA_INVALID")
    if not isinstance(remote_url, str):
        raise KnowledgeHubError("SCHEMA_INVALID")
    try:
        parsed = urlsplit(remote_url)
        remote = parse_remote(remote_url)
    except ValueError:
        raise KnowledgeHubError("SOURCE_REJECTED") from None
    if (not remote or (parsed.scheme in {"http", "https"} and parsed.username)
            or any(char.isspace() for char in remote_url)):
        raise KnowledgeHubError("SOURCE_REJECTED")
    return remote


def _registration_catalogs(root, project_id, repository_id, remote):
    inputs = snapshot_inputs(root)
    projects = load_json(root / "registry/projects.json", {}).get("projects", [])
    routes = load_json(root / "registry/project-routes.json", {})
    matches = [row for row in routes.get("routes", []) if row.get("project_id") == project_id]
    if len(matches) != 1 or len([row for row in projects if row.get("id") == project_id]) != 1:
        raise KnowledgeHubError("PROJECT_UNREGISTERED")
    route = matches[0]
    repositories = load_json(root / "registry/repositories.json", {})
    rows = repositories.get("repositories")
    if not isinstance(rows, list):
        raise KnowledgeHubError("SCHEMA_INVALID")
    seen_ids, seen_remotes = set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise KnowledgeHubError("SCHEMA_INVALID")
        key = identity_key(row.get("remote_key"))
        if not isinstance(row.get("repo_id"), str) or row["repo_id"] in seen_ids or (key and key in seen_remotes):
            raise KnowledgeHubError("ROUTE_CONFLICT")
        # Existing catalogs contain reserved IDs without a remote identity.
        # Preserve those rows; they are not candidates for remote matching.
        if not key and row.get("remote_key") is not None:
            raise KnowledgeHubError("SCHEMA_INVALID")
        seen_ids.add(row["repo_id"])
        if key:
            seen_remotes.add(key)
    existing = [row for row in rows if row.get("repo_id") == repository_id or row.get("remote_key") == remote]
    if existing and (len(existing) != 1 or existing[0].get("repo_id") != repository_id
                     or existing[0].get("remote_key") != remote or existing[0].get("project_id") != project_id
                     or existing[0].get("status") != "registered"):
        raise KnowledgeHubError("ROUTE_CONFLICT")
    refs = route.get("repo_refs", [])
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs) or len(set(refs)) != len(refs):
        raise KnowledgeHubError("SCHEMA_INVALID")
    if any(repository_id in other.get("repo_refs", []) for other in routes.get("routes", []) if other is not route):
        raise KnowledgeHubError("ROUTE_CONFLICT")
    return inputs, routes, route, repositories, rows, existing, refs

def registration(root, project_id, repository_id, remote_url, authorization_id="", apply=False):
    """Plan or atomically append one repository and its route reference.

    No local checkout path is stored. Existing identities cannot be reassigned.
    The existing register policy/grant is reused with a distinct request hash.
    """
    target = subject("project:" + project_id)
    remote = _registration_remote(repository_id, remote_url)
    with read_guard(root):
        inputs, routes, route, repositories, rows, existing, refs = _registration_catalogs(
            root, project_id, repository_id, remote)
        proposal = {"action": "register", "registration_type": "repository/v1", "subject_ref": target,
                    "repository_id": repository_id, "remote_key": remote}
        request_hash = digest(proposal)
        if not apply and not authorization_id:
            return _receipt(status="PLANNED", persisted=False, subject_ref=target,
                            repository_id=repository_id, remote_key=remote, expected_hash=request_hash,
                            authorization_required=True)
        authorize(root, "register", target, authorization_id, expected_hash=request_hash)
        if existing and repository_id in refs:
            return _receipt(status="ALREADY_REGISTERED", persisted=True, subject_ref=target,
                            repository_id=repository_id, remote_key=remote, expected_hash=request_hash)
        if not existing:
            rows.append({"repo_id": repository_id, "project_id": project_id, "remote_key": remote,
                         "remote_kind": "internal-git", "workspace_ref": "workspace://" + project_id,
                         "groups": [], "aliases": [], "lifecycle": "first-party", "status": "registered"})
        if repository_id not in refs:
            route["repo_refs"] = refs + [repository_id]
        # Both outputs have optimistic preconditions and commit under one lock.
        before = {name: file_sha256(root / name) for name in
                  ("registry/repositories.json", "registry/project-routes.json")}
    transaction = RepositoryTransaction(root, expected_inputs=inputs)
    transaction.add_text("registry/repositories.json", pretty_json(repositories) + "\n",
                         expected_sha256=before["registry/repositories.json"])
    transaction.add_text("registry/project-routes.json", pretty_json(routes) + "\n",
                         expected_sha256=before["registry/project-routes.json"])
    # Recheck authorization after the snapshot; the transaction checks inputs.
    authorize(root, "register", target, authorization_id, expected_hash=request_hash)
    result = transaction.apply().to_dict() if apply else transaction.plan()
    return _receipt(status="REGISTERED" if apply else "PLANNED", persisted=bool(apply),
                    write_performed=bool(apply), subject_ref=target, repository_id=repository_id,
                    remote_key=remote, expected_hash=request_hash, transaction=result)
