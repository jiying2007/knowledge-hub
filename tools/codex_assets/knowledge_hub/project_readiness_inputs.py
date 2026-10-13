"""Bounded registration and workspace inputs for project readiness generation."""
import pathlib

from .common import KnowledgeHubError, load_json


def registration_projects(root, projects_override):
    if projects_override is None:
        from .project_readiness import _registered_projects
        return _registered_projects(root)
    projects = [dict(row) for row in projects_override]
    ids = [str(row["id"]) for row in projects]
    if not projects or len(ids) != len(set(ids)):
        raise KnowledgeHubError("invalid project registration overlay")
    return projects, ids


def local_workspace_inputs(root):
    rows = list((load_json(root / "local/workspaces.json", {}) or {}).get("workspaces", []))
    workspaces = {str(row.get("workspace_ref", "")): row for row in rows if row.get("workspace_ref")}
    from .provider_onboarding import binding_rows
    for binding in binding_rows(root):
        candidate = pathlib.Path(binding["path"])
        if candidate.is_dir() and [candidate.stat().st_dev, candidate.stat().st_ino] == binding["directory_identity"]:
            workspaces[binding["workspace_ref"]] = {"path": binding["path"]}
    return workspaces


def aggregate_members(group, project_id, evidence_profile):
    members = [str(value) for value in group.get("member_project_ids", []) if str(value) != project_id] if evidence_profile == "aggregate-group" else []
    if evidence_profile == "aggregate-group" and not members:
        raise KnowledgeHubError("aggregate-group project must declare at least one non-self member project: {}".format(project_id))
    return members
