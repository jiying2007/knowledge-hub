"""Context assembly implementation extracted from the stable public facade."""

from __future__ import annotations

import hashlib
import pathlib
import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Set, Tuple

from .common import load_json, project_rows, registry_items, repository_rows, route_rows, utc_timestamp
from .context_support import (
    BUDGET_LIMITS,
    SUMMARY_JSON_MAX_ITEMS,
    TASK_TYPES,
    _compact_context_item,
    _compact_mapping,
    _current_exclusion_reason,
    _fit_summary_budget,
    _git_head_from_config,
    _public_item,
    _query_route_selection,
    _rank_item,
    _route_domains,
    _route_for_repo,
    _route_project_ids,
    _workspace_for_cwd,
    find_git_config,
    remote_urls_from_config,
)
from .retrieval_telemetry import (
    IMPLEMENTATION_GENERATION,
    INTERACTION_CONTRACT,
    INTERACTIVE_TELEMETRY_SCHEMA_VERSION,
    PERFORMANCE_CONTRACT,
    append_optional_telemetry,
    make_interaction_id,
)
from .search import SearchFilters, query_terms, search


SearchFunction = Callable[..., Dict[str, Any]]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def assemble_context(
    root: pathlib.Path,
    cwd: str,
    query: str,
    task_type: str = "general",
    limit: int = 8,
    context_budget: str = "normal",
    project_hint: str = "",
    _search_fn: Optional[SearchFunction] = None,
) -> Dict[str, Any]:
    started = time.monotonic()
    if task_type not in TASK_TYPES:
        raise ValueError("unsupported task type")
    if context_budget not in BUDGET_LIMITS:
        raise ValueError("unsupported context budget")
    if limit < 1:
        raise ValueError("limit must be >= 1")
    context_search = _search_fn or search
    effective_limit = min(limit, BUDGET_LIMITS[context_budget])
    routes = route_rows(root)
    explicit_route: Optional[Mapping[str, Any]] = None
    if project_hint:
        explicit_matches = [
            route
            for route in routes
            if str(route.get("project_id", "")) == project_hint
        ]
        if len(explicit_matches) != 1:
            raise ValueError("unknown or ambiguous project hint: {}".format(project_hint))
        explicit_route = explicit_matches[0]
    repositories = repository_rows(root)
    projects_list = project_rows(root)
    projects = {str(row.get("id")): row for row in projects_list if row.get("id")}
    repo_by_id = {str(row.get("repo_id")): row for row in repositories if row.get("repo_id")}
    repo_by_remote = {str(row.get("remote_key", "")).lower(): row for row in repositories if row.get("remote_key")}
    groups_payload = _mapping(load_json(root / "registry/project-groups.json", {}))
    groups_list = list(groups_payload.get("groups", []))
    group_by_id = {str(row.get("id")): row for row in groups_list if isinstance(row, Mapping) and row.get("id")}
    workspaces_payload = _mapping(load_json(root / "local/workspaces.json", {}))
    local_workspaces = [row for row in workspaces_payload.get("workspaces", []) if isinstance(row, Mapping)]
    registry_loaded = time.monotonic()

    git_config, git_root = find_git_config(cwd)
    git_remotes = remote_urls_from_config(git_config)
    matched_repo: Optional[Mapping[str, Any]] = None
    matched_remote: Optional[Mapping[str, Any]] = None
    for remote in git_remotes:
        if remote["remote_key"] in repo_by_remote:
            matched_repo = repo_by_remote[remote["remote_key"]]
            matched_remote = remote
            break
    workspace_ref, workspace_match = _workspace_for_cwd(cwd, local_workspaces, repositories, routes)
    workspace_source_evidence = _mapping(workspace_match.get("source_evidence"))
    recorded_workspace_head = str(workspace_source_evidence.get("git_head", ""))
    current_workspace_head = _git_head_from_config(git_config)
    if recorded_workspace_head or current_workspace_head:
        evidence_state = (
            "fresh"
            if recorded_workspace_head and recorded_workspace_head == current_workspace_head
            else "stale"
            if recorded_workspace_head and current_workspace_head
            else "incomplete"
        )
        workspace_match["source_evidence_state"] = evidence_state
        workspace_match["source_evidence_fresh"] = evidence_state == "fresh"
        workspace_match["current_git_head"] = current_workspace_head
    repo_route = _route_for_repo(matched_repo, routes, projects)
    workspace_route: Optional[Mapping[str, Any]] = None
    workspace_matches: List[Dict[str, Any]] = []
    if workspace_ref and not repo_route:
        for route in routes:
            if workspace_ref in route.get("workspace_refs", []):
                workspace_route = route
                workspace_matches.append({"type": "workspace-ref", "value": workspace_ref})
                break
    repo_matches: List[Dict[str, Any]] = []
    if matched_repo and repo_route and matched_remote:
        repo_matches.append(
            {
                "type": "git-remote",
                "remote": matched_remote.get("remote"),
                "remote_key": matched_remote.get("remote_key"),
                "repo_id": matched_repo.get("repo_id"),
            }
        )
    cwd_route = repo_route or workspace_route
    query_selection = _query_route_selection(query, routes)
    initial_query_selection = query_selection
    query_route = query_selection["route"]
    query_score = query_selection["score"]
    query_matches = query_selection["matches"]
    if cwd_route and cwd_route.get("route_key_policy") == "control-plane-query-aware":
        target_selection = _query_route_selection(
            query,
            routes,
            exclude_project_id=str(cwd_route.get("project_id", "")),
        )
        initial_route = _mapping(initial_query_selection.get("route"))
        if (
            target_selection["status"] == "unresolved"
            and initial_route.get("project_id") == cwd_route.get("project_id")
        ):
            query_selection = initial_query_selection
        else:
            query_selection = target_selection
        query_route = query_selection["route"]
        query_score = query_selection["score"]
        query_matches = query_selection["matches"]
    best_route = cwd_route
    best_matches = repo_matches if repo_route else workspace_matches
    selection_source = "cwd" if cwd_route else "none"
    if query_selection["status"] == "ambiguous":
        best_route = None
        best_matches = query_matches
        selection_source = "global-ambiguous-query"
    elif (
        cwd_route
        and cwd_route.get("route_key_policy") == "control-plane-query-aware"
        and query_selection["status"] == "unresolved"
    ):
        best_route = None
        best_matches = []
        selection_source = "global-unresolved-query"
    elif cwd_route and query_route and query_route is not cwd_route and cwd_route.get("route_key_policy") == "control-plane-query-aware":
        best_route = query_route
        best_matches = query_matches + [
            {"type": "control-plane-query-aware", "cwd_project_id": cwd_route.get("project_id"), "query_score": query_score}
        ]
        selection_source = "query"
    elif not cwd_route and query_route:
        best_route, best_matches = query_route, query_matches
        selection_source = "query"
    if explicit_route is not None:
        best_route = explicit_route
        best_matches = [{"type": "explicit-project", "project_id": project_hint}]
        selection_source = "explicit-project"

    project_ids = _route_project_ids(best_route, group_by_id, repo_by_id)
    domain_refs = _route_domains(best_route, project_ids, projects)
    default_source_ids = set(str(value) for value in (best_route or {}).get("default_source_ids", []))
    routing_ready = time.monotonic()
    terms = query_terms(query)
    ranked: List[Tuple[int, Mapping[str, Any], List[str]]] = []
    for item in registry_items(root):
        score, reasons = _rank_item(item, terms, task_type, domain_refs, default_source_ids, bool(best_route))
        if score > 0:
            ranked.append((score, item, reasons))
    ranked.sort(key=lambda row: (-row[0], str(row[1].get("id", ""))))
    ranked_rows = [_public_item(score, item, reasons) for score, item, reasons in ranked[:effective_limit]]
    registry_rank_ready = time.monotonic()

    search_filters = SearchFilters(domains=sorted(domain_refs)) if domain_refs else SearchFilters()
    search_started = time.monotonic()
    search_payload = context_search(root, query, limit=effective_limit, filters=search_filters)
    search_payload["fallback_terms"] = []
    search_payload["fallback_results"] = []
    search_payload["fallback_count"] = 0
    if not search_payload["results"]:
        ignored = {"pcr02", "归档", "路径", "where", "archive"}
        fallback_terms = [term for term in terms if term not in ignored][:4]
        merged: List[Dict[str, Any]] = []
        seen: Set[Tuple[str, int, str]] = set()
        for term in fallback_terms:
            fallback = context_search(root, term, limit=effective_limit, filters=search_filters)
            for result in fallback["results"]:
                key = (str(result.get("path", "")), int(result.get("line", 0)), str(result.get("item_id", "")))
                if key in seen:
                    continue
                seen.add(key)
                row = dict(result)
                row["fallback_term"] = term
                merged.append(row)
                if len(merged) >= effective_limit:
                    break
            if len(merged) >= effective_limit:
                break
        search_payload["fallback_terms"] = fallback_terms
        search_payload["fallback_results"] = merged
        search_payload["fallback_count"] = len(merged)
        zero_hit = search_payload.get("zero_hit")
        if isinstance(zero_hit, dict):
            zero_hit["degraded_terms"] = fallback_terms
    search_ready = time.monotonic()

    current: List[Dict[str, Any]] = []
    recent: List[Dict[str, Any]] = []
    related: List[Dict[str, Any]] = []
    current_kinds = {"project-current", "decision", "runbook", "standard", "validation", "architecture"}
    recent_kinds = {"debug-record", "project-archive", "codex-session"}
    terminal_statuses = {"archived", "superseded", "rejected"}
    current_exclusions: List[Dict[str, Any]] = []
    readiness_current_count = 0
    for row in ranked_rows:
        exclusion = _current_exclusion_reason(row)
        if exclusion:
            current_exclusions.append({"id": row.get("id", ""), "reason": exclusion})
        if row["status"] in terminal_statuses:
            recent.append(row)
        elif not exclusion and (row["status"] == "active" or (row["status"] in {"reviewing", "draft"} and row["kind"] in current_kinds)):
            is_readiness = "project-readiness" in {
                str(value) for value in row.get("tags", [])
            }
            if is_readiness and readiness_current_count >= 1:
                related.append(row)
            else:
                current.append(row)
                readiness_current_count += int(is_readiness)
        elif row["kind"] in recent_kinds:
            recent.append(row)
        else:
            related.append(row)

    canonical_paths: Dict[str, Any] = {}
    route_summary: Optional[Dict[str, Any]] = None
    if best_route:
        canonical_paths = {
            "hub_entry": best_route.get("hub_entry"),
            "current": best_route.get("current_path"),
            "archive": best_route.get("archive_path"),
            "decisions": best_route.get("decisions_path"),
            "validation": best_route.get("validation_path"),
        }
        route_summary = {
            "project_id": best_route.get("project_id"),
            "group_id": best_route.get("group_id"),
            "name": best_route.get("name"),
            "hub_entry": best_route.get("hub_entry"),
            "current_path": best_route.get("current_path"),
            "archive_path": best_route.get("archive_path"),
            "decisions_path": best_route.get("decisions_path"),
            "validation_path": best_route.get("validation_path"),
            "repo_refs": best_route.get("repo_refs", []),
            "workspace_refs": best_route.get("workspace_refs", []),
            "domain_refs": sorted(domain_refs),
            "default_source_ids": best_route.get("default_source_ids", []),
            "route_key_policy": best_route.get("route_key_policy", "git-remote-first"),
            "matched_by": best_matches,
        }
    repo_summary: Optional[Dict[str, Any]] = None
    if matched_repo:
        repo_summary = {
            "repo_id": matched_repo.get("repo_id"),
            "project_id": matched_repo.get("project_id"),
            "remote_key": matched_repo.get("remote_key"),
            "workspace_ref": matched_repo.get("workspace_ref"),
            "groups": matched_repo.get("groups", []),
            "lifecycle": matched_repo.get("lifecycle"),
            "git_root_detected": str(git_root) if git_root else "",
            "git_config_detected": str(git_config) if git_config else "",
        }
    candidate_required = task_type in {"debug", "release", "decision"}
    authority_lanes = {
        "active_ids": [str(row.get("id", "")) for row in current if row.get("status") == "active" and row.get("id")],
        "provisional_ids": [
            str(row.get("id", ""))
            for row in current
            if row.get("status") in {"reviewing", "draft"} and row.get("id")
        ],
        "historical_ids": [
            str(row.get("id", ""))
            for row in recent
            if row.get("status") in terminal_statuses and row.get("id")
        ],
        "contract": "active and provisional are separate authority lanes; provisional items are never current fact authority",
    }
    risks = [
        "工程归档和 Codex archive 只作 historical provenance，不作为新增入口。",
        "memory、raw session、raw log、core、binary 不能高于 Hub 当前事实。",
        "owner gate、active promotion、memory write 和 source project write 必须有授权和证据。",
    ]
    if workspace_match.get("source_evidence_state") == "stale":
        risks.insert(
            0,
            "本机 workspace source_evidence HEAD 已陈旧；先运行 knowledge-workspace-discover.sh --apply 再形成源码结论。",
        )
    payload: Dict[str, Any] = {
        "schema_version": 2,
        "read_only": True,
        "cwd": cwd,
        "query": query,
        "task_type": task_type,
        "context_budget": context_budget,
        "knowledge_preflight": {
            "required": task_type in TASK_TYPES - {"general"},
            "source_of_truth": "registry/repositories.json plus registry/project-groups.json, registry/project-routes.json, registry/items.jsonl and indexed knowledge-search",
        },
        "repo_route": repo_summary,
        "route": route_summary,
        "route_selection": {
            "status": (
                "selected"
                if explicit_route is not None
                else "ambiguous"
                if query_selection["status"] == "ambiguous"
                else "selected"
                if best_route
                else "unresolved"
            ),
            "selection_source": selection_source,
            "cwd_route_project_id": (cwd_route or {}).get("project_id"),
            "query_route_project_id": (query_route or {}).get("project_id"),
            "query_score": query_score,
            "selected_project_id": (best_route or {}).get("project_id"),
            "candidates": [] if explicit_route is not None else query_selection["candidates"],
        },
        "canonical_paths": canonical_paths,
        "workspace_ref": workspace_ref or None,
        "workspace_match": workspace_match,
        "git_remotes_detected": git_remotes,
        "context": {
            "budget": context_budget,
            "effective_limit": effective_limit,
            "selection_order": ["route", "current", "recent", "related", "risk"],
            "canonical_paths": canonical_paths,
            "domain_refs": sorted(domain_refs),
            "current": current[:effective_limit],
            "recent": recent[:effective_limit],
            "related": related[:effective_limit],
            "search_fallback": search_payload.get("fallback_results", [])[:effective_limit],
            "current_exclusions": current_exclusions,
            "authority_lanes": authority_lanes,
            "risks": risks,
            "notes_zh": "context 是只读候选装配；状态分类优先于 kind，archived/superseded/rejected 不会进入 current。why_selected 不代表 active 或 owner 签收。",
        },
        "ranked_items": ranked_rows,
        "search": search_payload,
        "candidate_recommendation": {
            "required": candidate_required,
            "reason_zh": "debug/release/decision 可能形成长期结论；只有结论可复用、证据充分且改变稳定事实时才写 candidate。"
            if candidate_required
            else "普通查询、validation 和 session 不强制生成 Hub candidate；仅在形成耐久结论时提升。",
            "allowed_kinds": ["debug-record", "validation", "decision", "runbook", "codex-session"] if candidate_required else [],
            "threshold": "durable-reusable-evidence-backed",
        },
        "guardrails_zh": [
            "Hub 当前路由优先于 memory、raw session 和 historical archive provenance。",
            "Git remote key 是跨机器长期路由键；本机源码路径只允许出现在未纳管 local/workspaces.json。",
            "raw session、raw log、core、binary 不复制进正文；只写摘要、证据引用和 registry item。",
            "工程归档和 Codex archive 只作 historical provenance，不作为新增入口。",
        ],
    }
    finished = time.monotonic()
    payload["latency_ms"] = round((finished - started) * 1000, 2)
    payload["timing"] = {
        "registry_load_ms": round((registry_loaded - started) * 1000, 2),
        "routing_ms": round((routing_ready - registry_loaded) * 1000, 2),
        "registry_rank_ms": round((registry_rank_ready - routing_ready) * 1000, 2),
        "search_ms": round((search_ready - search_started) * 1000, 2),
        "assembly_ms": round((finished - search_ready) * 1000, 2),
        "total_ms": payload["latency_ms"],
    }
    return payload


def summarize_context(payload: Mapping[str, Any]) -> Dict[str, Any]:
    context = _mapping(payload.get("context"))
    route_selection = _mapping(payload.get("route_selection"))
    search_payload = _mapping(payload.get("search"))
    zero_hit = _mapping(search_payload.get("zero_hit"))
    search_trace = _mapping(search_payload.get("search_trace"))
    search_index = _mapping(search_payload.get("index"))
    preflight = _mapping(payload.get("knowledge_preflight"))

    compact_sections: Dict[str, List[Dict[str, Any]]] = {}
    seen_items: Set[str] = set()
    selected_item_count = 0
    raw_evidence: List[str] = []
    seen_evidence: Set[str] = set()
    for section in ("current", "recent", "related", "search_fallback"):
        compact_rows: List[Dict[str, Any]] = []
        rows = context.get(section, [])
        if not isinstance(rows, list):
            rows = []
        for row in rows:
            if selected_item_count >= SUMMARY_JSON_MAX_ITEMS:
                break
            if not isinstance(row, Mapping):
                continue
            compact = _compact_context_item(row)
            dedupe_key = str(compact.get("id") or compact.get("path") or "")
            if dedupe_key and dedupe_key in seen_items:
                continue
            if dedupe_key:
                seen_items.add(dedupe_key)
            compact_rows.append(compact)
            selected_item_count += 1
            path = str(compact.get("path") or "")
            if path and path not in seen_evidence:
                seen_evidence.add(path)
                raw_evidence.append(path)
        compact_sections[section] = compact_rows

    candidates: List[Dict[str, Any]] = []
    raw_candidates = route_selection.get("candidates", [])
    if not isinstance(raw_candidates, list):
        raw_candidates = []
    for candidate in raw_candidates:
        compact_candidate = _compact_mapping(candidate, ("project_id", "score"))
        if compact_candidate:
            candidates.append(compact_candidate)
    compact_route_selection = _compact_mapping(
        route_selection,
        (
            "status",
            "selection_source",
            "cwd_route_project_id",
            "query_route_project_id",
            "selected_project_id",
        ),
    ) or {}
    if candidates:
        compact_route_selection["candidates"] = candidates

    route_status = str(route_selection.get("status", "unresolved"))
    confidence = {"selected": "high", "ambiguous": "medium", "unresolved": "low"}.get(
        route_status,
        "low",
    )
    telemetry = _mapping(payload.get("telemetry"))
    candidate_recommendation = _mapping(payload.get("candidate_recommendation"))

    search_results = search_payload.get("results", [])
    if not isinstance(search_results, list):
        search_results = []
    risks = context.get("risks", [])
    if not isinstance(risks, list):
        risks = []
    summary = {
        "schema_version": payload.get("schema_version", 2),
        "projection": "agent-summary-v1",
        "read_only": bool(payload.get("read_only", True)),
        "task_type": payload.get("task_type", "general"),
        "context_budget": payload.get("context_budget", "normal"),
        "knowledge_preflight": _compact_mapping(preflight, ("required",)) or {},
        "repo_route": _compact_mapping(
            payload.get("repo_route"),
            ("repo_id", "project_id", "workspace_ref"),
        ),
        "route": _compact_mapping(
            payload.get("route"),
            (
                "project_id",
                "hub_entry",
                "current_path",
                "archive_path",
                "decisions_path",
                "validation_path",
            ),
        ),
        "route_selection": compact_route_selection,
        "context": {
            "budget": context.get("budget", payload.get("context_budget", "normal")),
            "effective_limit": context.get("effective_limit", 0),
            **compact_sections,
            "authority_lanes": _compact_mapping(
                context.get("authority_lanes"),
                ("active_ids", "provisional_ids", "historical_ids"),
            )
            or {},
            "risks": risks[:2],
        },
        "search_summary": {
            "status": search_payload.get("status", ""),
            "count": search_payload.get("count", len(search_results)),
            "total_matches": search_payload.get("total_matches", 0),
            "fallback_count": search_payload.get("fallback_count", 0),
            "latency_ms": search_payload.get("latency_ms", 0),
            "index": _compact_mapping(search_index, ("state", "mode", "fresh", "rebuilt")) or {},
            "zero_hit": _compact_mapping(zero_hit, ("is_zero_hit", "reason")) or {},
            "search_trace": _compact_mapping(
                search_trace,
                (
                    "schema_version",
                    "excluded_by_filters_total",
                    "excluded_truncated",
                ),
            )
            or {},
        },
        "candidate_recommendation": _compact_mapping(
            candidate_recommendation,
            ("required", "allowed_kinds", "threshold"),
        )
        or {},
        "context_contract": {
            "read_tier": "L1",
            "budget_profile": payload.get("context_budget", "normal"),
            "confidence": confidence,
            "raw_evidence": raw_evidence,
            "raw_required_for_conclusion": bool(preflight.get("required", False)),
            "fallback_condition": "歧义、低置信度或高风险时读取 --json 与 raw_evidence。",
        },
        "latency_ms": payload.get("latency_ms", 0),
        "telemetry": _compact_mapping(
            telemetry,
            ("status", "recorded", "reason", "error_code"),
        )
        or {},
    }
    return _fit_summary_budget(summary)


def record_context_telemetry(
    root: pathlib.Path,
    payload: Mapping[str, Any],
    enabled: bool = True,
) -> Dict[str, Any]:
    query = str(payload.get("query", ""))
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    recorded_at = utc_timestamp()
    context = _mapping(payload.get("context"))
    result_ids: List[str] = []
    for section in ("current", "recent", "related", "search_fallback"):
        results = context.get(section, [])
        if not isinstance(results, list):
            continue
        for result in results:
            if not isinstance(result, Mapping):
                continue
            result_id = str(result.get("item_id") or result.get("id") or "")
            if result_id and result_id not in result_ids:
                result_ids.append(result_id)
    search_payload = _mapping(payload.get("search"))
    search_index = _mapping(search_payload.get("index"))
    route = _mapping(payload.get("route"))
    timing = _mapping(payload.get("timing"))
    search_timing = _mapping(search_payload.get("timing"))
    current_rows = context.get("current", [])
    recent_rows = context.get("recent", [])
    current_count = len(current_rows) if isinstance(current_rows, list) else 0
    recent_count = len(recent_rows) if isinstance(recent_rows, list) else 0
    row = {
        "schema_version": INTERACTIVE_TELEMETRY_SCHEMA_VERSION,
        "sample_kind": "interactive",
        "interaction_contract": INTERACTION_CONTRACT,
        "performance_contract": PERFORMANCE_CONTRACT,
        "implementation_generation": IMPLEMENTATION_GENERATION,
        "interaction_id": make_interaction_id("context", query_hash, recorded_at),
        "retrieval_kind": "context",
        "recorded_at": recorded_at,
        "query_sha256": query_hash,
        "task_type": payload.get("task_type", ""),
        "selected_project_id": route.get("project_id", ""),
        "current_count": current_count,
        "recent_count": recent_count,
        "result_ids": result_ids,
        "latency_ms": payload.get("latency_ms", 0),
        "index_state": search_index.get("state", ""),
        "index_rebuilt": bool(search_index.get("rebuilt", False)),
        "index_build_ms": search_index.get("build_duration_ms", 0),
        "token_cache_status": search_index.get("token_cache_status", ""),
        "token_cache_hits": search_index.get("token_cache_hits", 0),
        "token_cache_misses": search_index.get("token_cache_misses", 0),
        "stage_timing": dict(timing),
        "search_stage_timing": dict(search_timing),
        "raw_query_stored": False,
    }
    path = root / ".cache/knowledge-hub/context-telemetry.jsonl"
    return append_optional_telemetry(path, row, enabled=enabled)
