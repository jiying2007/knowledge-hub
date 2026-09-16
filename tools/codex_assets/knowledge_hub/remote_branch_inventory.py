"""Fetch bounded remote branch inventory for terminal branch-GC evidence."""

from __future__ import annotations

import json
import pathlib
import re
import time
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
_REVISION_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_MAX_PAGES = 10
_PAGE_SIZE = 100
_TIMEOUT_SECONDS = 20
_IMPLEMENTATION_BRANCH_PREFIXES = ("codex/", "arch/")
_DEFAULT_CONVERGENCE_ATTEMPTS = 6
_DEFAULT_CONVERGENCE_DELAY_SECONDS = 2.0
_DEFAULT_BRANCH = "master"


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


def _validate_identity(repository: str, source_revision: str) -> None:
    if not _REPOSITORY_PATTERN.fullmatch(repository):
        raise KnowledgeHubError("repository must use owner/name form")
    if not _REVISION_PATTERN.fullmatch(source_revision):
        raise KnowledgeHubError("source revision must be a full Git object id")


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


def fetch_remote_branch_records(
    repository: str, token: str = ""
) -> List[Dict[str, Any]]:
    if not _REPOSITORY_PATTERN.fullmatch(repository):
        raise KnowledgeHubError("repository must use owner/name form")
    records: Dict[str, Dict[str, Any]] = {}
    for page in range(1, _MAX_PAGES + 1):
        rows = _request_page(repository, token, page)
        for row in rows:
            name = str(row.get("name", ""))
            if not name:
                continue
            protected = row.get("protected")
            records[name] = {
                "name": name,
                "protected": protected if isinstance(protected, bool) else None,
            }
        if len(rows) < _PAGE_SIZE:
            break
    else:
        raise KnowledgeHubError("remote branch inventory exceeds page budget")
    return [records[name] for name in sorted(records)]


def fetch_remote_branches(repository: str, token: str = "") -> List[str]:
    return [row["name"] for row in fetch_remote_branch_records(repository, token)]


def _implementation_branches(branches: List[str]) -> List[str]:
    return sorted(
        branch
        for branch in set(branches)
        if any(branch.startswith(prefix) for prefix in _IMPLEMENTATION_BRANCH_PREFIXES)
    )


def _residue_state(candidates: List[str], branches: List[str]) -> Dict[str, List[str]]:
    candidate_set = set(candidates)
    implementation = _implementation_branches(branches)
    remaining = sorted(candidate_set.intersection(branches))
    unexpected = sorted(set(implementation).difference(candidate_set))
    return {
        "remaining_candidates": remaining,
        "implementation_branches": implementation,
        "unexpected_implementation_branches": unexpected,
    }


def _default_branch_state(
    records: List[Mapping[str, Any]], default_branch: str
) -> Dict[str, Any]:
    matches = [row for row in records if str(row.get("name", "")) == default_branch]
    present = len(matches) == 1
    protected_value = matches[0].get("protected") if present else None
    observed = isinstance(protected_value, bool)
    return {
        "default_branch": default_branch,
        "default_branch_present": present,
        "default_branch_protection_observed": observed,
        "default_branch_protected": protected_value is True,
    }


def evaluate_remote_branch_inventory(
    root: pathlib.Path,
    *,
    repository: str,
    source_revision: str,
    token: str = "",
    lifecycle: str = "registry/branch-lifecycle.json",
    default_branch: str = _DEFAULT_BRANCH,
    convergence_attempts: int = _DEFAULT_CONVERGENCE_ATTEMPTS,
    convergence_delay_seconds: float = _DEFAULT_CONVERGENCE_DELAY_SECONDS,
) -> Dict[str, Any]:
    _validate_identity(repository, source_revision)
    if not default_branch or "/" in default_branch:
        raise KnowledgeHubError("default branch name is invalid")
    if convergence_attempts < 1:
        raise KnowledgeHubError("convergence_attempts must be at least 1")
    if convergence_delay_seconds < 0:
        raise KnowledgeHubError("convergence_delay_seconds must be non-negative")

    candidates = retirement_candidates(root, lifecycle)
    observations: List[Dict[str, Any]] = []
    branches: List[str] = []
    default_state = {
        "default_branch": default_branch,
        "default_branch_present": False,
        "default_branch_protection_observed": False,
        "default_branch_protected": False,
    }
    residue: Dict[str, List[str]] = {
        "remaining_candidates": [],
        "implementation_branches": [],
        "unexpected_implementation_branches": [],
    }

    for attempt in range(1, convergence_attempts + 1):
        try:
            records = fetch_remote_branch_records(repository, token)
            branches = [str(row["name"]) for row in records]
            default_state = _default_branch_state(records, default_branch)
        except KnowledgeHubError as exc:
            remaining = (
                residue["remaining_candidates"] if observations else list(candidates)
            )
            return {
                "schema_version": "knowledge-hub.remote-branch-inventory.v1",
                "generated_at": utc_timestamp(),
                "repository": repository,
                "source_revision": source_revision,
                "status": "blocked",
                "branches": branches,
                "retirement_candidates": candidates,
                "remaining_candidates": remaining,
                "implementation_branch_prefixes": list(_IMPLEMENTATION_BRANCH_PREFIXES),
                "implementation_branches": residue["implementation_branches"],
                "unexpected_implementation_branches": residue[
                    "unexpected_implementation_branches"
                ],
                **default_state,
                "observation_count": len(observations),
                "converged_after_retry": False,
                "observations": observations,
                "error": str(exc),
            }

        residue = _residue_state(candidates, branches)
        observations.append(
            {
                "attempt": attempt,
                "remaining_candidates": residue["remaining_candidates"],
                "unexpected_implementation_branches": residue[
                    "unexpected_implementation_branches"
                ],
                "default_branch_present": default_state["default_branch_present"],
                "default_branch_protection_observed": default_state[
                    "default_branch_protection_observed"
                ],
                "default_branch_protected": default_state[
                    "default_branch_protected"
                ],
            }
        )
        dirty = bool(
            residue["remaining_candidates"]
            or residue["unexpected_implementation_branches"]
        )
        if not dirty:
            return {
                "schema_version": "knowledge-hub.remote-branch-inventory.v1",
                "generated_at": utc_timestamp(),
                "repository": repository,
                "source_revision": source_revision,
                "status": "pass",
                "branches": branches,
                "retirement_candidates": candidates,
                "remaining_candidates": [],
                "implementation_branch_prefixes": list(_IMPLEMENTATION_BRANCH_PREFIXES),
                "implementation_branches": residue["implementation_branches"],
                "unexpected_implementation_branches": [],
                **default_state,
                "observation_count": len(observations),
                "converged_after_retry": attempt > 1,
                "observations": observations,
                "error": "",
            }
        if attempt < convergence_attempts and convergence_delay_seconds:
            time.sleep(convergence_delay_seconds)

    return {
        "schema_version": "knowledge-hub.remote-branch-inventory.v1",
        "generated_at": utc_timestamp(),
        "repository": repository,
        "source_revision": source_revision,
        "status": "needs-review",
        "branches": branches,
        "retirement_candidates": candidates,
        "remaining_candidates": residue["remaining_candidates"],
        "implementation_branch_prefixes": list(_IMPLEMENTATION_BRANCH_PREFIXES),
        "implementation_branches": residue["implementation_branches"],
        "unexpected_implementation_branches": residue[
            "unexpected_implementation_branches"
        ],
        **default_state,
        "observation_count": len(observations),
        "converged_after_retry": False,
        "observations": observations,
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
