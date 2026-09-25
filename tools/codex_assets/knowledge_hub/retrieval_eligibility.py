"""Shared governed eligibility rules for user-facing retrieval surfaces."""

from __future__ import annotations

import datetime as dt
from typing import Any, Mapping, Sequence

from .common import KnowledgeHubError
from .search_core import _item_is_default_searchable

SERVICEABLE_STATUSES = frozenset({"active", "reviewing", "draft"})


def _date(value: Any, label: str):
    if value in (None, ""):
        return None
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError as exc:
        raise KnowledgeHubError("{} must use YYYY-MM-DD".format(label)) from exc


def serviceable_item(item: Mapping[str, Any], today: dt.date) -> bool:
    """Apply corpus, lifecycle and temporal eligibility without granting ACL."""

    if not _item_is_default_searchable(item):
        return False
    if str(item.get("status", "")) not in SERVICEABLE_STATUSES:
        return False
    valid_from = _date(item.get("valid_from"), "valid_from")
    valid_to = _date(item.get("valid_to"), "valid_to")
    if valid_from and valid_to and valid_from > valid_to:
        raise KnowledgeHubError("valid_from must not exceed valid_to")
    if valid_from and today < valid_from:
        return False
    if valid_to and today > valid_to:
        return False
    return True


def scope_matches(item: Mapping[str, Any], scopes: Sequence[str]) -> bool:
    """Apply Agent domain/path scopes; empty scopes mean no extra restriction."""

    if not scopes:
        return True
    domain = str(item.get("domain", "")).rstrip("/")
    path = str(item.get("path", ""))
    return any(
        bool(str(scope).strip())
        and (
            domain == str(scope).rstrip("/")
            or domain.startswith(str(scope).rstrip("/") + "/")
            or path.startswith(str(scope).rstrip("/") + "/")
        )
        for scope in scopes
    )
