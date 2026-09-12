"""Fetch bounded remote branch inventory for terminal branch-GC evidence."""

from __future__ import annotations

import json
import pathlib
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Mapping

from .common import (
    KnowledgeHubError,
    ensure_private_directory_tree,
    ensure_private_file,
    resolve_inside,
    utc_timestamp,
)

_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_MAX_PAGES = 10
_PAGE_SIZE = 100
_TIMEOUT_SECONDS = 20


def _load_lifecycle(root: pathlib.Path, relative: str) -> Mapping[str, Any]:
    path = resolve_inside(root, relative)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("branch lifecycle registry is unavailable") from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("branch lifecycle registry must be an object")
    return value


def retirement_candidates(root: pathlib.Path, relative: str) -> List[str]:
    lifecycle = _load_lifecycle(root, relative)
    rows = lifecycle.get("retirement_candidates", [])
    if not isinstance(rows, list):
        raise KnowledgeHubError("retirement_candidates must be a list")
    result = []
    for row in rows:
        if isinstance(row, Mapping) and row.get("branch"):
            result.append(str(row["branch"]))
    return sorted(set(result))


def _request_page(repository: str, token: str, page: int) -> List[Mapping[str, Any]]:
    url = "https://api.github.com/repos/{}/branches?per_page={}&page={}".format(
        repository,
        _PAGE_SIZE,
        page,
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "knowledge-hub-terminal-closure",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer {}".format(token)
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:  # nosec B310
            raw = response.read(2 * 1024 * 1024 + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        raise KnowledgeHubError("remote branch inventory request failed") from exc
    if len(raw) > 2 * 1024 * 1024:
        raise KnowledgeHubError("remote branch inventory response exceeds byte budget")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("remote branch inventory response is invalid") from exc
    if not isinstance(value, list):
        raise KnowledgeHubError("remote branch inventory response must be a list")
    return [row for row in value if isinstance(row, Mapping)]


def fetch_remote_branches(repository: str, token: str = "") -> List[str]:
    if not _REPOSITORY_PATTERN.fullmatch(repository):
        raise KnowledgeHubError("repository must use owner/name form")
    names: List[str] = []
    for page in range(1, _MAX_PAGES + 1):
        rows = _request_page(repository, token, page)
        names.extend(str(row.get("name", "")) for row in rows if row.get("name"))
        if len(rows) < _PAGE_SIZE:
            break
    else:
        raise KnowledgeHubError("remote branch inventory exceeds page budget")
    return sorted(set(names))


def evaluate_remote_branch_inventory(
    root: pathlib.Path,
    *,
    repository: str,
    source_revision: str,
    token: str = "",
    lifecycle: str = "registry/branch-lifecycle.json",
) -> Dict[str, Any]:
    candidates = retirement_candidates(root, lifecycle)
    try:
        branches = fetch_remote_branches(repository, token)
    except KnowledgeHubError as exc:
        return {
            "schema_version": "knowledge-hub.remote-branch-inventory.v1",
            "generated_at": utc_timestamp(),
            "repository": repository,
            "source_revision": source_revision,
            "status": "blocked",
            "branches": [],
            "retirement_candidates": candidates,
            "remaining_candidates": candidates,
            "error": str(exc),
        }
    remaining = sorted(set(candidates).intersection(branches))
    return {
        "schema_version": "knowledge-hub.remote-branch-inventory.v1",
        "generated_at": utc_timestamp(),
        "repository": repository,
        "source_revision": source_revision,
        "status": "pass" if not remaining else "needs-review",
        "branches": branches,
        "retirement_candidates": candidates,
        "remaining_candidates": remaining,
        "error": "",
    }


def write_inventory(root: pathlib.Path, relative: str, payload: Mapping[str, Any]) -> str:
    path = resolve_inside(root, relative)
    ensure_private_directory_tree(root, path.parent)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    ensure_private_file(path)
    return str(path.relative_to(root))
