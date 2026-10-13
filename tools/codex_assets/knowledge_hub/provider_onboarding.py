"""Explicit, authorized project registration and persistent local bindings."""

from __future__ import annotations

import pathlib
import re

from .common import (KnowledgeHubError, load_json, project_rows, route_rows, pretty_json,
                     read_utf8_bounded, file_sha256, resolve_inside)
from .provider_subjects import (BINDINGS_PATH, WORKSPACES_PATH, GRANTS_PATH, authorize,
                               digest, subject, policy)
from .store import RepositoryTransaction, snapshot_inputs
from .context_support import find_git_config, remote_urls_from_config


def binding_rows(root):
    value = load_json(root / BINDINGS_PATH, {"schema_version": 1, "bindings": []})
    from .schemas import validate_instance
    if validate_instance(root, "provider-bindings-v1", value)["status"] != "pass":
        raise KnowledgeHubError("SCHEMA_INVALID")
    if (not isinstance(value, dict) or set(value) != {"schema_version", "bindings"}
            or value["schema_version"] != 1 or not isinstance(value["bindings"], list)):
        raise KnowledgeHubError("SCHEMA_INVALID")
    required = {"binding_id", "workspace_ref", "subject_ref", "path", "requested_path", "coverage",
                "generation", "directory_identity", "authorization_ref", "origin"}
    ids = set()
    for row in value["bindings"]:
        if (not isinstance(row, dict) or set(row) != required or row.get("coverage") not in {"exact-root", "subtree"}
                or type(row.get("generation")) is not int or row["generation"] < 1
                or row.get("origin") != "explicit" or row["binding_id"] in ids):
            raise KnowledgeHubError("SCHEMA_INVALID")
        subject(row["subject_ref"])
        ids.add(row["binding_id"])
    return value["bindings"]


def workspace_rows(root):
    value = load_json(root / WORKSPACES_PATH, {"schema_version": 1, "workspaces": []})
    from .schemas import validate_instance
    if validate_instance(root, "provider-workspaces-v1", value)["status"] != "pass":
        raise KnowledgeHubError("SCHEMA_INVALID")
    if (not isinstance(value, dict) or set(value) != {"schema_version", "workspaces"}
            or value["schema_version"] != 1 or not isinstance(value["workspaces"], list)):
        raise KnowledgeHubError("SCHEMA_INVALID")
    seen = set()
    for row in value["workspaces"]:
        if (not isinstance(row, dict) or set(row) != {"workspace_ref", "subject_ref"}
                or re.fullmatch(r"workspace://[a-z0-9][a-z0-9-]{0,80}", str(row.get("workspace_ref", ""))) is None
                or row["workspace_ref"] in seen):
            raise KnowledgeHubError("SCHEMA_INVALID")
        subject(row["subject_ref"])
        seen.add(row["workspace_ref"])
    return value["workspaces"]


def register_project(root, project_id, name, declaration_file, authorization_id="", apply=False):
    target = subject("project:" + project_id)
    if not isinstance(name, str) or not name.strip() or len(name) > 256:
        raise KnowledgeHubError("SCHEMA_INVALID")
    declaration = read_utf8_bounded(pathlib.Path(declaration_file), 131072, "user declaration")
    from .provider_operations import safe_text
    safe_text(name)
    if "\n" in name or "\r" in name or name.lower() not in declaration.lower():
        raise KnowledgeHubError("DECLARATION_MISMATCH")
    if re.search(r"(?<![a-z0-9-])" + re.escape(project_id) + r"(?![a-z0-9-])", declaration.lower()) is None:
        raise KnowledgeHubError("DECLARATION_MISMATCH")
    import hashlib
    declaration_hash = hashlib.sha256(declaration.encode()).hexdigest()
    request_hash = digest({"action": "register", "subject_ref": target, "name": name, "declaration_sha256": declaration_hash})
    if not apply and not authorization_id:
        return {"status": "PLANNED", "persisted": False, "expected_hash": request_hash,
                "subject_ref": target, "declaration_sha256": declaration_hash, "authorization_required": True}
    authorize(root, "register", target, authorization_id, expected_hash=request_hash)
    from .common import load_jsonl
    grant = next(row for row in load_jsonl(root / GRANTS_PATH) if row.get("id") == authorization_id)
    if grant.get("declaration_sha256") != declaration_hash:
        raise KnowledgeHubError("DECLARATION_MISMATCH")
    inputs = snapshot_inputs(root)
    projects = load_json(root / "registry/projects.json", {"schema_version": 1, "projects": []})
    routes = load_json(root / "registry/project-routes.json", {"schema_version": 2, "routes": []})
    existing = [r for r in projects["projects"] if r.get("id") == project_id]
    workspace = "workspace://" + project_id
    if existing:
        if len(existing) != 1 or existing[0].get("name") != name or not any(r.get("project_id") == project_id for r in routes["routes"]):
            raise KnowledgeHubError("ROUTE_CONFLICT")
        return {"status": "ALREADY_REGISTERED", "persisted": True, "subject_ref": target}
    base = "projects/" + project_id
    paths = {k: base + "/" + k for k in ("current", "archive", "decisions", "validation")}
    entry = base + "/README.md"
    if resolve_inside(root, entry).exists():
        raise KnowledgeHubError("ROUTE_CONFLICT")
    project = {"id": project_id, "name": name, "type": "knowledge-project", "domain": base,
               "entry": entry, **paths, "groups": [], "repo_boundary": "none", "status": "registered",
               "workspace_refs": [workspace], "evidence_profile": "knowledge-project"}
    route = {"project_id": project_id, "name": name, "type": "project", "route_scope": "project",
             "group_id": "", "aliases": [project_id, name], "topic_aliases": [], "repo_refs": [],
             "workspace_refs": [workspace], "hub_entry": entry,
             **{k + "_path": v for k, v in paths.items()}, "domain_refs": [base],
             "default_source_ids": [], "route_key_policy": "subject-workspace"}
    projects["projects"].append(project)
    routes["routes"].append(route)
    workspaces = workspace_rows(root)
    if any(r["workspace_ref"] == workspace for r in workspaces):
        raise KnowledgeHubError("ROUTE_CONFLICT")
    workspaces.append({"workspace_ref": workspace, "subject_ref": target})
    def prepare(transaction):
        # Registration, reviewing readiness slots and logical workspaces commit together.
        transaction.expected_inputs = inputs
        transaction.add_text(WORKSPACES_PATH, pretty_json({"schema_version": 1, "workspaces": workspaces}) + "\n")
        authorize(root, "register", target, authorization_id, expected_hash=request_hash)
    from .project_readiness import generate_project_readiness, _base_item
    import datetime as dt
    from .common import registry_items, render_markdown
    from .model import require_valid_item
    entry_item = _base_item(project, "entry", entry, dt.date.today(), name + " 知识入口", "project-current",
                            "项目身份与知识入口登记；不代表源码验证、owner approval 或产品放行。", "knowledge-project")
    entry_item["id"] = project_id + "-knowledge-entry"
    entry_item["searchable"] = True
    entry_item.pop("readiness_slot", None)
    entry_item["tags"] = [tag for tag in entry_item["tags"] if tag != "project-readiness"]
    entry_item["source"] = {"type": "provider-project-registration", "from": "request-sha256:" + declaration_hash}
    require_valid_item(entry_item)
    text = render_markdown(entry_item, "# " + name + "\n\n项目知识入口。登记身份不代表 owner approval、源码验证或产品放行。\n")
    generated = generate_project_readiness(root, dt.date.today(), apply, projects["projects"], routes["routes"], prepare,
                                           registry_items(root) + [entry_item], {entry: text})
    return {"status": "REGISTERED" if apply else "PLANNED", "persisted": apply, "subject_ref": target, "transaction": generated["transaction"]}


def bind_workspace(root, workspace_ref, path, coverage="subtree", expected_generation=0, authorization_id="", apply=False):
    matches = [row for row in workspace_rows(root) if row["workspace_ref"] == workspace_ref]
    if len(matches) != 1 or coverage not in {"exact-root", "subtree"}:
        raise KnowledgeHubError("WORKSPACE_UNREGISTERED")
    target = matches[0]["subject_ref"]
    requested = pathlib.Path(path).expanduser().absolute()
    canonical = requested.resolve()
    if not canonical.is_dir():
        raise KnowledgeHubError("WORKSPACE_MISSING")
    directory = canonical.stat()
    proposal = {"action": "bind", "subject_ref": target, "workspace_ref": workspace_ref,
                "path_sha256": digest(str(canonical)), "coverage": coverage, "expected_generation": expected_generation,
                "directory_identity": [directory.st_dev, directory.st_ino]}
    request_hash = digest(proposal)
    if not apply and not authorization_id:
        return {"status": "PLANNED", "persisted": False, "expected_hash": request_hash,
                "subject_ref": target, "binding_path_sha256": proposal["path_sha256"], "authorization_required": True}
    authorize(root, "bind", target, authorization_id, expected_hash=request_hash)
    from .common import load_jsonl
    grant = next(r for r in load_jsonl(root / GRANTS_PATH) if r.get("id") == authorization_id)
    if grant.get("binding_path_sha256") != proposal["path_sha256"]:
        raise KnowledgeHubError("POLICY_DENIED")
    inputs = snapshot_inputs(root)
    rows = binding_rows(root)
    authorize(root, "bind", target, authorization_id, expected_hash=request_hash)
    existing = [r for r in rows if r["workspace_ref"] == workspace_ref and r["path"] == str(canonical)]
    if len(existing) > 1:
        raise KnowledgeHubError("ROUTE_CONFLICT")
    if any(r["path"] == str(canonical) and r["subject_ref"] != target for r in rows):
        raise KnowledgeHubError("ROUTE_CONFLICT")
    current = existing[0] if existing else None
    if current and current["coverage"] == coverage and current["directory_identity"] == proposal["directory_identity"]:
        if expected_generation not in {current["generation"], current["generation"] - 1}:
            raise KnowledgeHubError("STALE_GENERATION")
        return {"status": "ALREADY_BOUND", "persisted": True, "generation": current["generation"]}
    if expected_generation != (current["generation"] if current else 0):
        raise KnowledgeHubError("STALE_GENERATION")
    row = {"binding_id": "binding-" + digest([workspace_ref, str(canonical)]), "workspace_ref": workspace_ref,
           "subject_ref": target, "path": str(canonical), "requested_path": str(requested), "coverage": coverage,
           "generation": expected_generation + 1, "directory_identity": proposal["directory_identity"],
           "authorization_ref": authorization_id, "origin": "explicit"}
    rows = [r for r in rows if not current or r["binding_id"] != current["binding_id"]] + [row]
    transaction = RepositoryTransaction(root, expected_inputs=inputs)
    local = root / BINDINGS_PATH
    transaction.add_text(BINDINGS_PATH, pretty_json({"schema_version": 1, "bindings": rows}) + "\n",
                         expected_sha256=file_sha256(local) if local.is_file() else "")
    result = transaction.apply().to_dict() if apply else transaction.plan()
    return {"status": "BOUND" if apply else "PLANNED", "persisted": apply, "generation": row["generation"], "transaction": result}


def resolve_workspace(root, cwd):
    cwd = pathlib.Path(cwd).expanduser().resolve()
    candidates, stale = [], []
    for row in binding_rows(root):
        base = pathlib.Path(row["path"])
        if cwd != base and (row["coverage"] != "subtree" or base not in cwd.parents):
            continue
        try:
            st = base.stat()
            fresh = (pathlib.Path(row["requested_path"]).resolve() == base and [st.st_dev, st.st_ino] == row["directory_identity"])
        except OSError:
            fresh = False
        (candidates if fresh else stale).append(row)
    config, git_root = find_git_config(str(cwd))
    from .common import repository_rows
    remotes = remote_urls_from_config(config)
    repos = repository_rows(root)
    known = [r for r in repos if any(m["remote_key"] == r.get("remote_key") for m in remotes)]
    projects = {r.get("project_id") for r in known if r.get("project_id")}
    deepest = max((len(pathlib.Path(r["path"]).parts) for r in candidates), default=0)
    selected = [r for r in candidates if len(pathlib.Path(r["path"]).parts) == deepest]
    subjects = {digest(r["subject_ref"]) for r in selected}
    if len(projects) > 1 or len(subjects) > 1:
        return {"state": "conflict", "subject_ref": None, "reason_codes": ["ROUTE_CONFLICT"], "binding": None}
    target = selected[0]["subject_ref"] if selected else None
    if projects:
        remote_target = {"type": "project", "id": next(iter(projects))}
        # A separately registered child repository has its own boundary.
        if selected and git_root and pathlib.Path(selected[0]["path"]) in git_root.parents:
            target, selected = remote_target, []
        elif target and target != remote_target:
            return {"state": "conflict", "subject_ref": None, "reason_codes": ["ROUTE_CONFLICT"], "binding": None}
        else:
            target = remote_target
    elif git_root and selected and pathlib.Path(selected[0]["path"]) in git_root.parents:
        return {"state": "unresolved", "subject_ref": None, "reason_codes": ["BOUNDARY_UNKNOWN"], "binding": None}
    if target:
        return {"state": "resolved", "subject_ref": target, "reason_codes": [], "binding": selected[0] if selected else None}
    return {"state": "unresolved", "subject_ref": None, "reason_codes": ["WORKSPACE_STALE" if stale else "WORKSPACE_UNBOUND"], "binding": None}
