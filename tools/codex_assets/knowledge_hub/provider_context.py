"""Version 3 read scopes; execution identity never follows query aliases."""

from __future__ import annotations

import hashlib
import json
import pathlib

from .common import KnowledgeHubError, registry_items, route_rows, read_utf8_bounded, file_sha256, resolve_inside
from .context import assemble_context, summarize_context
from .search import query_terms
from .provider_onboarding import resolve_workspace, workspace_rows
from .provider_subjects import authorize, principal, read_guard, route_subject, signatures, subject, digest


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


def context_v3(root, args):
    from .context_support import context_receipt_request, CONTEXT_RECEIPT_KEY_PATTERN
    from .common import load_json, ensure_private_directory, ensure_private_file
    if not args.receipt_key:
        return _assemble(root, args)
    if not args.summary_json or not CONTEXT_RECEIPT_KEY_PATTERN.fullmatch(args.receipt_key):
        raise KnowledgeHubError("SCHEMA_INVALID")
    with read_guard(root):
        import datetime as dt
        resolution = resolve_workspace(root, args.cwd)
        request = {"version": 3, "parameters": {k: v for k, v in vars(args).items() if k not in {"root", "json", "summary_json"}},
                   "base": context_receipt_request(root, args.cwd, args.query, args.task_type, args.limit, args.context_budget, ""),
                   "provider": signatures(root), "resolution": resolution, "date": dt.date.today().isoformat()}
        # No raw query is retained in a receipt.
        request["parameters"]["query"] = digest(args.query)
        path = root / ".cache/knowledge-hub/context-receipts" / ("v3-" + args.receipt_key + ".json")
        cached = load_json(path, {})
        if isinstance(cached, dict) and cached.get("request") == request:
            evidence = cached.get("evidence", {})
            if (isinstance(evidence, dict) and isinstance(cached.get("summary"), dict)
                    and all(resolve_inside(root, p).is_file() and file_sha256(resolve_inside(root, p)) == sha for p, sha in evidence.items())):
                value = cached["summary"]
                value["cache"] = {"hit": True}
                return value
        value = _assemble(root, args)
        evidence = {item["path"]: file_sha256(root / item["path"]) for group in value["context"] for item in group["items"] if item.get("path")}
        ensure_private_directory(root / ".cache")
        ensure_private_directory(root / ".cache/knowledge-hub")
        ensure_private_directory(path.parent)
        temporary = path.with_suffix(".tmp")
        if path.is_symlink() or temporary.is_symlink():
            raise KnowledgeHubError("SCHEMA_INVALID")
        temporary.write_text(json.dumps({"request": request, "evidence": evidence, "summary": value}, ensure_ascii=False), encoding="utf-8")
        ensure_private_file(temporary)
        temporary.replace(path)
        value["cache"] = {"hit": False}
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
            from .provider_archive import checked_archive_policy
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
    if args.project:
        raise KnowledgeHubError("SCHEMA_INVALID")
    if args.personal and args.unassigned:
        raise KnowledgeHubError("SCHEMA_INVALID")
    with read_guard(root):
        resolution = resolve_workspace(root, args.cwd)
        execution, resolution = _execution(root, args, resolution)
        scopes = [subject("project:" + v) for v in args.retrieval_project]
        if args.retrieval_domain:
            scopes.append(subject("domain:" + args.retrieval_domain))
        if args.personal or args.unassigned:
            if scopes:
                raise KnowledgeHubError("SCHEMA_INVALID")
            scopes = [subject({"type": "personal" if args.personal else "unassigned", "id": principal(root)})]
        if not scopes and execution:
            scopes = [execution]
        groups, seen = [], set()
        remaining = min(args.limit, {"small": 3, "normal": 8, "deep": 16}[args.context_budget])
        for scope in scopes:
            authorize(root, "read", scope)
            if scope["type"] == "project":
                payload = assemble_context(root, args.cwd, args.query, args.task_type, max(1, remaining), args.context_budget, scope["id"])
                rows = payload["context"]["current"] + payload["context"]["recent"] + payload["context"]["related"]
                # The v2 ranker must never inject private rows through metadata ranking.
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
                    unique.append({k: row[k] for k in ("id", "item_id", "title", "kind", "status", "path", "why_selected") if k in row})
                    remaining -= 1
            groups.append({"subject_ref": scope, "items": unique, "zero_hit": not unique})
        if not scopes:
            payload = assemble_context(root, args.cwd, args.query, args.task_type, args.limit, args.context_budget)
            # Unknown cwd gets discovery only, never an execution/archival identity.
            discovered = payload["context"].get("current", []) + payload["context"].get("related", []) + payload.get("search", {}).get("results", [])
            unique = []
            for row in discovered:
                ident = row.get("id", row.get("item_id", row.get("path")))
                if ident not in seen and len(unique) < args.limit:
                    seen.add(ident)
                    unique.append({k: row[k] for k in ("id", "item_id", "title", "kind", "status", "path", "why_selected") if k in row})
            groups = [{"subject_ref": None, "items": unique, "zero_hit": not unique, "lane": "discovery"}]
        requested = subject(args.archive_subject) if args.archive_subject else execution
        eligible, reasons = _eligibility(root, requested, execution, resolution)
        from .context_support import find_git_config, workspace_git_head
        config, _ = find_git_config(args.cwd)
        value = {"schema_version": "knowledge-provider.context/v3", "read_only": True,
                 "execution_subject": execution, "retrieval_scope": scopes, "route_resolution": {
                     k: resolution[k] for k in ("state", "subject_ref", "reason_codes")},
                 "source_state": {"vcs": "git" if config else "none", "commit": workspace_git_head(args.cwd, config) or None,
                                  "verification_state": "unverified"},
                 "archive_eligibility": {"eligible": eligible, "subject_ref": requested, "reason_codes": sorted(set(reasons))},
                 "context": groups, "authority_lanes": {"authoritative": [], "provisional": [], "historical": [], "discovery": []},
                 "next_actions": [] if eligible else ["resolve-explicit-subject-or-register-workspace"]}
        for group in groups:
            for item in group["items"]:
                lane = "discovery" if group.get("lane") == "discovery" else "authoritative" if item.get("status") == "active" else "historical" if item.get("status") in {"archived", "superseded", "rejected"} else "provisional"
                value["authority_lanes"][lane].append(item.get("id", item.get("item_id")))
        if args.summary_json and len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()) > 4096:
            # Keep identity, conflicts and permissions; reduce only result rows.
            for group in reversed(value["context"]):
                while group["items"] and len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()) > 4096:
                    group["items"].pop()
            value["authority_lanes"] = {key: [] for key in value["authority_lanes"]}
            if len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()) > 4096:
                raise KnowledgeHubError("READ_BUDGET_EXCEEDED")
        return value
