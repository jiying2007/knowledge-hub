"""Stable facade for project-aware Knowledge Hub context assembly."""

from __future__ import annotations

import pathlib
from typing import Any, Dict, Mapping

from . import context_support as _support

# Preserve the established context module surface while implementation is split
# into bounded support and assembly modules.
TASK_TYPES = _support.TASK_TYPES
BUDGET_LIMITS = _support.BUDGET_LIMITS
SUMMARY_JSON_MAX_BYTES = _support.SUMMARY_JSON_MAX_BYTES
SUMMARY_JSON_MAX_ITEMS = _support.SUMMARY_JSON_MAX_ITEMS
CONTEXT_RECEIPT_SCHEMA_VERSION = _support.CONTEXT_RECEIPT_SCHEMA_VERSION
CONTEXT_RECEIPT_KEY_PATTERN = _support.CONTEXT_RECEIPT_KEY_PATTERN
CONTEXT_RECEIPT_REGISTRY_PATHS = _support.CONTEXT_RECEIPT_REGISTRY_PATHS
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
_compact_mapping = _support._compact_mapping
_compact_context_item = _support._compact_context_item
_summary_json_size = _support._summary_json_size
_path_signature = _support._path_signature
context_receipt_path = _support.context_receipt_path
context_receipt_request = _support.context_receipt_request
load_context_receipt = _support.load_context_receipt
write_context_receipt = _support.write_context_receipt
attach_context_receipt = _support.attach_context_receipt
_sync_summary_raw_evidence = _support._sync_summary_raw_evidence
_fit_summary_budget = _support._fit_summary_budget
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
    )


def summarize_context(payload: Mapping[str, Any]) -> Dict[str, Any]:
    from .context_assembly import summarize_context as _summarize_context

    return _summarize_context(payload)


def record_context_telemetry(
    root: pathlib.Path,
    payload: Mapping[str, Any],
    enabled: bool = True,
) -> Dict[str, Any]:
    from .context_assembly import record_context_telemetry as _record_context_telemetry

    return _record_context_telemetry(root, payload, enabled=enabled)
