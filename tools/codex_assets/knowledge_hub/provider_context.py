"""Provider v4 read scopes and authority-checked private cache."""

from __future__ import annotations

import json
import re
import pathlib
from typing import Dict, List

from .common import KnowledgeHubError, registry_items, read_utf8_bounded, file_sha256, resolve_inside
from .context import assemble_context
from .search import query_terms
from .provider_onboarding import resolve_workspace, workspace_rows
from .provider_subjects import authorize, principal, read_guard, route_subject, signatures, subject, digest, policy


def corpus_signature(root, args, resolution):
    execution, _ = _execution(root, args, resolution)
    scopes = scope_inputs(root, args, execution)
    for scope in scopes:
        authorize(root, "read", scope)
    private_scopes = [scope for scope in scopes if scope["type"] in {"personal", "unassigned"}]
    actor = principal(root) if private_scopes else None
    rows, total = [], 0
    for item in registry_items(root):
        private = item.get("visibility") == "personal-local" or item.get("path", "").startswith("notes/personal/")
        if private and (not actor or item.get("subject_ref") not in private_scopes):
            continue
        if actor and not private:
            continue
        path = resolve_inside(root, item["path"])
        if not path.is_file():
            rows.append([item["id"], item["path"], "absent"])
            continue
        total += path.stat().st_size
        if total > 16 * 1024 * 1024:
            raise KnowledgeHubError("READ_BUDGET_EXCEEDED")
        rows.append([item["id"], item["path"], file_sha256(path)])
    return digest(rows)


def public_item(row):
    value = {
        key: row[key]
        for key in ("id", "item_id", "title", "kind", "status", "path", "manual_validation_pending")
        if key in row
    }
    reasons = []
    for reason in row.get("why_selected", []):
        if isinstance(reason, str):
            normalized = "query-match" if reason.startswith("query") else reason
            if normalized not in reasons:
                reasons.append(normalized)
    if reasons:
        value["why_selected"] = reasons[:4]
    return value


def authority_lanes(groups):
    lanes: Dict[str, List[str]] = {"authoritative": [], "provisional": [], "historical": [], "discovery": []}
    for group in groups:
        for item in group["items"]:
            ident = item.get("id") or item.get("item_id")
            lane = (
                "discovery"
                if group.get("lane") == "discovery" or not ident
                else "authoritative"
                if item.get("status") == "active" and not item.get("manual_validation_pending", False)
                else "historical"
                if item.get("status") in {"archived", "superseded", "rejected"}
                else "provisional"
            )
            if ident:
                lanes[lane].append(ident)
    return lanes


def scope_inputs(root, args, execution):
    if args.personal and args.unassigned:
        raise KnowledgeHubError("SCHEMA_INVALID")
    scopes = [subject("project:" + v) for v in args.retrieval_project]
    if args.retrieval_domain:
        scopes.append(subject("domain:" + args.retrieval_domain))
    if args.personal or args.unassigned:
        if scopes:
            raise KnowledgeHubError("SCHEMA_INVALID")
        scopes = [subject({"type": "personal" if args.personal else "unassigned", "id": principal(root)})]
    return scopes or ([execution] if execution else [])


def source_state(args):
    from .context_support import find_git_config, workspace_git_head
    config, _ = find_git_config(args.cwd)
    return {"vcs": "git" if config else "none", "commit": workspace_git_head(args.cwd, config) or None,
            "verification_state": "unverified"}


def cache_is_current(root, value, args, resolution):
    """Cache metadata never replaces the authoritative registry or permissions."""
    try:
        from .schemas import validate_instance
        if validate_instance(root, "provider-context-v4", value)["status"] != "pass":
            return False
        execution, resolved = _execution(root, args, resolution)
        requested = subject(args.archive_subject) if args.archive_subject else execution
        eligible, reasons = _eligibility(root, requested, execution, resolved)
        if (value["execution_subject"] != execution or value["route_resolution"] != {key: resolved[key] for key in ("state", "subject_ref", "reason_codes")}
                or value["archive_eligibility"] != {"eligible": eligible, "subject_ref": requested, "reason_codes": sorted(set(reasons))}):
            return False
        scopes = scope_inputs(root, args, execution)
        if value["source_state"] != source_state(args):
            return False
        if sum(len(group["items"]) for group in value["context"]) > min(args.limit, {"small": 3, "normal": 8, "deep": 16}[args.context_budget]):
            return False
        if args.summary_json and len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()) > 4096 - 128:
            return False
        if value["retrieval_scope"] != scopes or [g["subject_ref"] for g in value["context"]] != (scopes or [None]):
            return False
        rows = {row["id"]: row for row in registry_items(root)}
        from .common import route_rows, project_rows, repository_rows, load_json, source_id
        from .context_support import _route_domains, _route_project_ids
        routes = route_rows(root)
        projects = {row["id"]: row for row in project_rows(root)}
        groups = {row["id"]: row for row in load_json(root / "registry/project-groups.json", {}).get("groups", [])}
        repos = {row["repo_id"]: row for row in repository_rows(root)}
        for group in value["context"]:
            scope = group["subject_ref"]
            domains, sources = set(), set()
            if scope:
                authorize(root, "read", scope)
                if scope["type"] == "project":
                    matching = [row for row in routes if row["project_id"] == scope["id"]]
                    if len(matching) != 1:
                        return False
                    domains = _route_domains(matching[0], _route_project_ids(matching[0], groups, repos), projects)
                    sources = set(matching[0].get("default_source_ids", []))
                elif scope["type"] == "domain":
                    domains = {scope["id"]}
            elif group.get("lane") != "discovery":
                return False
            for item in group["items"]:
                row = rows.get(item.get("id") or item.get("item_id"))
                if not row or any(item.get(key) != row.get(key) for key in ("title", "kind", "status", "path")):
                    return False
                private = row.get("visibility") == "personal-local" or row["path"].startswith("notes/personal/")
                if scope and scope["type"] in {"personal", "unassigned"}:
                    if not private or row.get("subject_ref") != scope:
                        return False
                elif private:
                    return False
                elif domains and not any(row["domain"] == d or row["domain"].startswith(d + "/") for d in domains) and source_id(row) not in sources:
                    return False
        return value["authority_lanes"] == authority_lanes(value["context"])
    except (KnowledgeHubError, KeyError, TypeError, ValueError):
        return False


def private_results(root, typ, query, limit):
    actor = principal(root)
    target = subject({"type": typ, "id": actor})
    authorize(root, "read", target)
    # A separate derived corpus: no private row enters the default team index.
    terms = query_terms(query)
    ranked, total = [], 0
    for row in registry_items(root):
        if row.get("subject_ref") != target or row.get("visibility") != "personal-local":
            continue
        path = resolve_inside(root, row["path"])
        text = read_utf8_bounded(path, 1024 * 1024, "personal knowledge")
        total += len(text.encode())
        if total > 16 * 1024 * 1024:
            raise KnowledgeHubError("READ_BUDGET_EXCEEDED")
        haystack = (row.get("title", "") + "\n" + row.get("summary_zh", "") + "\n" + text).lower()
        score = sum(1 for term in terms if term.lower() in haystack)
        if score:
            ranked.append((score, row))
    ranked.sort(key=lambda r: (-r[0], r[1]["id"]))
    return [{"id": r["id"], "title": r["title"], "status": r["status"], "path": r["path"],
             "subject_ref": target, "kind": r["kind"], "why_selected": ["explicit-private-scope"]} for _, r in ranked[:limit]]


def context(root, args):
    from .common import load_json
    from .private_io import atomic_private_write
    if "read" not in policy(root)["actions"]:
        raise KnowledgeHubError("POLICY_DENIED")
    if not args.receipt_key:
        return _assemble(root, args)
    if not args.summary_json or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", args.receipt_key):
        raise KnowledgeHubError("SCHEMA_INVALID")
    with read_guard(root):
        import datetime as dt
        resolution = resolve_workspace(root, args.cwd)
        registry_paths = ("registry/items.jsonl", "registry/sources.json", "registry/projects.json",
                          "registry/repositories.json", "registry/project-groups.json", "registry/project-routes.json",
                          "registry/retired-sources.jsonl", "local/workspaces.json", "registry/product-policy.json")
        request = {"version": 4, "cwd": str(pathlib.Path(args.cwd).expanduser().resolve()),
                   "query_sha256": digest(args.query), "task_type": args.task_type, "limit": args.limit,
                   "context_budget": args.context_budget,
                   "scopes": {key: getattr(args, key) for key in
                              ("workspace", "execution_project", "retrieval_project", "retrieval_domain",
                               "archive_subject", "personal", "unassigned")},
                   "registry": {path: file_sha256(root / path) if (root / path).is_file() else "absent"
                                for path in registry_paths},
                   "provider": signatures(root), "resolution": resolution, "corpus": corpus_signature(root, args, resolution),
                   "date": dt.date.today().isoformat()}
        path = root / ".cache/knowledge-hub/context-receipts" / ("v4-" + args.receipt_key + ".json")
        try:
            cached = load_json(path, {})
        except (KnowledgeHubError, OSError):
            cached = {}
        if isinstance(cached, dict) and cached.get("request") == request:
            evidence = cached.get("evidence", {})
            if (isinstance(evidence, dict) and isinstance(cached.get("summary"), dict) and cache_is_current(root, cached["summary"], args, resolution)
                    and all(resolve_inside(root, p).is_file() and file_sha256(resolve_inside(root, p)) == sha for p, sha in evidence.items())):
                value = cached["summary"]
                value["cache"] = {"hit": True}
                return value
        value = _assemble(root, args)
        evidence = {item["path"]: file_sha256(root / item["path"]) for group in value["context"] for item in group["items"] if item.get("path")}
        try:
            atomic_private_write(path, json.dumps({"request": request, "evidence": evidence, "summary": value}, ensure_ascii=False))
            value["cache"] = {"hit": False, "status": "written"}
        except (KnowledgeHubError, OSError):
            value["cache"] = {"hit": False, "status": "unavailable"}
        return value


def _execution(root, args, resolution):
    execution, explicit = resolution["subject_ref"], None
    if args.execution_project:
        explicit = subject("project:" + args.execution_project)
        route_subject(root, explicit)
    if args.workspace:
        choices = [r for r in workspace_rows(root) if r["workspace_ref"] == args.workspace]
        if len(choices) != 1:
            raise KnowledgeHubError("WORKSPACE_UNREGISTERED")
        if explicit and explicit != choices[0]["subject_ref"]:
            raise KnowledgeHubError("ROUTE_CONFLICT")
        explicit = choices[0]["subject_ref"]
    if explicit:
        if execution and execution != explicit or resolution["state"] == "conflict":
            resolution = dict(resolution, state="conflict", reason_codes=["ROUTE_CONFLICT"])
        else:
            execution = explicit
            resolution = dict(resolution, state="resolved", subject_ref=explicit, reason_codes=[])
    return execution, resolution


def _eligibility(root, requested, execution, resolution):
    reasons = list(resolution["reason_codes"]) if resolution["state"] != "resolved" else []
    eligible = False
    if requested:
        try:
            from .provider_policy import checked_archive_policy
            try:
                checked_archive_policy(root, None)
            except KnowledgeHubError as exc:
                raise KnowledgeHubError("POLICY_DENIED") from exc
            authorize(root, "archive", requested)
            route_subject(root, requested)
            eligible = resolution["state"] != "conflict"
            if execution and requested["type"] == "project" and execution != requested:
                eligible = False
                reasons.append("ROUTE_CONFLICT")
        except KnowledgeHubError as exc:
            reasons.append(str(exc))
    else:
        reasons.append("ARCHIVE_SUBJECT_REQUIRED")
    return eligible, [] if eligible else sorted(set(reasons))


def _assemble(root, args):
    policy(root)
    if args.project:
        raise KnowledgeHubError("SCHEMA_INVALID")
    if args.personal and args.unassigned:
        raise KnowledgeHubError("SCHEMA_INVALID")
    with read_guard(root):
        resolution = resolve_workspace(root, args.cwd)
        execution, resolution = _execution(root, args, resolution)
        scopes = scope_inputs(root, args, execution)
        groups, seen = [], set()
        remaining = min(args.limit, {"small": 3, "normal": 8, "deep": 16}[args.context_budget])
        for scope in scopes:
            authorize(root, "read", scope)
            if scope["type"] == "project":
                payload = assemble_context(root, args.cwd, args.query, args.task_type, max(1, remaining), args.context_budget, scope["id"])
                rows = payload["search"].get("results", []) + payload["search"].get("fallback_results", [])
                rows += payload["context"]["current"] + payload["context"]["recent"] + payload["context"]["related"]
                # Metadata ranking must not inject private rows into project retrieval.
                rows = [r for r in rows if r.get("visibility") != "personal-local" and not r.get("path", "").startswith("notes/personal/")]
            elif scope["type"] in {"personal", "unassigned"}:
                rows = private_results(root, scope["type"], args.query, max(1, remaining))
            else:
                route = route_subject(root, scope)
                from .search import search, SearchFilters
                rows = search(root, args.query, limit=max(1, remaining), filters=SearchFilters(domains=[route["domain"]]))["results"]
            unique = []
            for row in rows:
                ident = row.get("id", row.get("item_id", row.get("path")))
                if ident not in seen and remaining:
                    seen.add(ident)
                    unique.append(public_item(row))
                    remaining -= 1
            groups.append({"subject_ref": scope, "items": unique, "zero_hit": not rows,
                           "truncated": bool(rows) and len(unique) < len({r.get("id", r.get("item_id", r.get("path"))) for r in rows})})
        if not scopes:
            payload = assemble_context(root, args.cwd, args.query, args.task_type, args.limit, args.context_budget)
            # Unknown cwd gets discovery only, never an execution/archival identity.
            discovered = payload["context"].get("current", []) + payload["context"].get("related", []) + payload.get("search", {}).get("results", [])
            discovered = [r for r in discovered if r.get("visibility") != "personal-local" and not r.get("path", "").startswith("notes/personal/")]
            unique = []
            for row in discovered:
                ident = row.get("id", row.get("item_id", row.get("path")))
                if ident not in seen and len(unique) < remaining:
                    seen.add(ident)
                    unique.append(public_item(row))
            groups = [{"subject_ref": None, "items": unique, "zero_hit": not unique, "lane": "discovery"}]
        requested = subject(args.archive_subject) if args.archive_subject else execution
        eligible, reasons = _eligibility(root, requested, execution, resolution)
        value = {"schema_version": "knowledge-provider.context/v4", "read_only": True,
                 "execution_subject": execution, "retrieval_scope": scopes, "route_resolution": {
                     k: resolution[k] for k in ("state", "subject_ref", "reason_codes")},
                 "source_state": source_state(args),
                 "archive_eligibility": {"eligible": eligible, "subject_ref": requested, "reason_codes": sorted(set(reasons))},
                 "context": groups, "authority_lanes": {"authoritative": [], "provisional": [], "historical": [], "discovery": []},
                 "next_actions": [] if eligible else ["resolve-explicit-subject-or-register-workspace"]}
        value["authority_lanes"] = authority_lanes(groups)
        summary_limit = 4096 - (128 if args.receipt_key else 0)
        if args.summary_json and len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()) > summary_limit:
            # Keep identity, conflicts and permissions; reduce only result rows.
            for group in reversed(value["context"]):
                while group["items"] and len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()) > summary_limit:
                    group["items"].pop()
                    group["truncated"] = True
            remaining_ids = {item.get("id", item.get("item_id")) for group in value["context"] for item in group["items"]}
            value["authority_lanes"] = {key: [ident for ident in ids if ident in remaining_ids]
                                        for key, ids in value["authority_lanes"].items()}
            if len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()) > summary_limit:
                raise KnowledgeHubError("READ_BUDGET_EXCEEDED")
        return value
