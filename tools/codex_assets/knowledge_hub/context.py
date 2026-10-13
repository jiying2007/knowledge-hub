"""Stable facade for project-aware Knowledge Hub context assembly."""

from __future__ import annotations

import pathlib
from typing import Any, Dict, Mapping

from . import context_support as _support
from .search import search

# Shared ranking interface used by Provider and repository diagnostics.
TASK_TYPES = _support.TASK_TYPES
BUDGET_LIMITS = _support.BUDGET_LIMITS
TASK_KIND_WEIGHTS = _support.TASK_KIND_WEIGHTS

normalize_remote_key = _support.normalize_remote_key
_safe_resolve = _support._safe_resolve
find_git_config = _support.find_git_config
_git_head_from_config = _support._git_head_from_config
remote_urls_from_config = _support.remote_urls_from_config
_route_for_repo = _support._route_for_repo
_query_route = _support._query_route
_phrase_matches = _support._phrase_matches
_query_route_selection = _support._query_route_selection
_expand_workspace_ref = _support._expand_workspace_ref
_workspace_for_cwd = _support._workspace_for_cwd
_route_project_ids = _support._route_project_ids
_route_domains = _support._route_domains
_route_matches_domain = _support._route_matches_domain
_rank_item = _support._rank_item
_public_item = _support._public_item
_current_exclusion_reason = _support._current_exclusion_reason


def assemble_context(
    root: pathlib.Path,
    cwd: str,
    query: str,
    task_type: str = "general",
    limit: int = 8,
    context_budget: str = "normal",
    project_hint: str = "",
) -> Dict[str, Any]:
    from .context_assembly import assemble_context as _assemble_context

    return _assemble_context(
        root,
        cwd,
        query,
        task_type=task_type,
        limit=limit,
        context_budget=context_budget,
        project_hint=project_hint,
        _search_fn=search,
    )


def record_context_telemetry(
    root: pathlib.Path,
    payload: Mapping[str, Any],
    enabled: bool = True,
) -> Dict[str, Any]:
    from .context_assembly import record_context_telemetry as _record_context_telemetry

    return _record_context_telemetry(root, payload, enabled=enabled)
