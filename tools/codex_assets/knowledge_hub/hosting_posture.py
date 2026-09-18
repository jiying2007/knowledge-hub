"""Capture exact hosted repository posture without making it canonical."""

from __future__ import annotations

import json
import pathlib
import re
import urllib.error
import urllib.request
from typing import Any, Dict, Mapping

from .common import KnowledgeHubError, ensure_private_directory_tree, ensure_private_file, resolve_inside, utc_timestamp

_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_TIMEOUT_SECONDS = 20
_MAX_BYTES = 2 * 1024 * 1024


def _load_object(path: pathlib.Path, label: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("{} is unavailable or invalid".format(label)) from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return dict(value)


def _request_repository_metadata(repository: str, token: str = "") -> Dict[str, Any]:
    if not _REPOSITORY_PATTERN.fullmatch(repository):
        raise KnowledgeHubError("repository must use owner/name form")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "knowledge-hub-hosting-posture",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer {}".format(token)
    request = urllib.request.Request(
        "https://api.github.com/repos/{}".format(repository),
        headers=headers,
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:  # nosec B310
            raw = response.read(_MAX_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        raise KnowledgeHubError("repository hosting posture request failed") from exc
    if len(raw) > _MAX_BYTES:
        raise KnowledgeHubError("repository hosting posture response exceeds byte budget")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("repository hosting posture response is invalid") from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("repository hosting posture response must be an object")
    return dict(value)


def evaluate_hosting_posture(
    root: pathlib.Path,
    *,
    repository: str,
    source_revision: str,
    branch_inventory: str = ".cache/knowledge-hub/remote-branch-inventory.json",
    token: str = "",
) -> Dict[str, Any]:
    if not _REPOSITORY_PATTERN.fullmatch(repository):
        raise KnowledgeHubError("repository must use owner/name form")
    if not _REVISION_PATTERN.fullmatch(source_revision):
        raise KnowledgeHubError("source revision must be a lowercase 40-character git SHA")
    inventory = _load_object(root / branch_inventory, "remote branch inventory")
    if inventory.get("repository") != repository:
        raise KnowledgeHubError("branch inventory repository identity mismatch")
    if inventory.get("source_revision") != source_revision:
        raise KnowledgeHubError("branch inventory source revision mismatch")
    metadata = _request_repository_metadata(repository, token)
    if metadata.get("full_name") != repository:
        raise KnowledgeHubError("repository metadata identity mismatch")
    private_value = metadata.get("private")
    visibility = str(metadata.get("visibility") or "")
    default_branch = str(metadata.get("default_branch") or "")
    if not isinstance(private_value, bool):
        raise KnowledgeHubError("repository metadata private field is missing")
    if not visibility or not default_branch:
        raise KnowledgeHubError("repository metadata hosting fields are incomplete")
    if str(inventory.get("default_branch") or "") != default_branch:
        raise KnowledgeHubError("branch inventory default branch does not match repository metadata")
    return {
        "schema_version": "knowledge-hub.hosting-posture.v1",
        "status": "pass",
        "generated_at": utc_timestamp(),
        "repository": repository,
        "source_revision": source_revision,
        "repository_private": private_value,
        "repository_visibility": visibility,
        "default_branch": default_branch,
        "default_branch_present": inventory.get("default_branch_present") is True,
        "default_branch_protection_observed": inventory.get("default_branch_protection_observed") is True,
        "default_branch_protected": inventory.get("default_branch_protected") is True,
        "branch_inventory": branch_inventory,
        "canonical_write": False,
    }


def write_hosting_posture(root: pathlib.Path, relative: str, payload: Mapping[str, Any]) -> str:
    path = resolve_inside(root, relative)
    ensure_private_directory_tree(root, path.parent)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ensure_private_file(path)
    return str(path.relative_to(root))
