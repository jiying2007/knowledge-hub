"""Capture exact hosted repository posture without making it canonical."""

from __future__ import annotations

import fnmatch
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Mapping

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


def _request_default_branch_metadata(
    repository: str,
    branch: str,
    token: str = "",
) -> Dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "knowledge-hub-hosting-posture",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer {}".format(token)
    encoded = urllib.parse.quote(branch, safe="")
    request = urllib.request.Request(
        "https://api.github.com/repos/{}/branches/{}".format(
            repository,
            encoded,
        ),
        headers=headers,
        method="GET",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=_TIMEOUT_SECONDS,
        ) as response:  # nosec B310
            raw = response.read(_MAX_BYTES + 1)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
    ) as exc:
        raise KnowledgeHubError(
            "default branch hosting posture request failed"
        ) from exc
    if len(raw) > _MAX_BYTES:
        raise KnowledgeHubError(
            "default branch hosting posture response exceeds byte budget"
        )
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError(
            "default branch hosting posture response is invalid"
        ) from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError(
            "default branch hosting posture response must be an object"
        )
    return dict(value)


def _branch_required_status_checks(
    branch: Mapping[str, Any],
) -> Dict[str, Any]:
    protection = branch.get("protection")
    if not isinstance(protection, Mapping):
        return {"observed": False, "contexts": []}
    required = protection.get("required_status_checks")
    if not isinstance(required, Mapping):
        return {"observed": False, "contexts": []}
    contexts: List[str] = []
    for value in required.get("contexts", []):
        if isinstance(value, str) and value.strip():
            contexts.append(value.strip())
    for value in required.get("checks", []):
        if not isinstance(value, Mapping):
            continue
        context = str(value.get("context", "")).strip()
        if context:
            contexts.append(context)
    return {
        "observed": True,
        "contexts": sorted(set(contexts)),
    }


def _ruleset_headers(token: str) -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "knowledge-hub-hosting-posture",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer {}".format(token)
    return headers


def _request_rulesets_list(
    repository: str,
    token: str,
) -> List[Mapping[str, Any]]:
    request = urllib.request.Request(
        "https://api.github.com/repos/{}/rulesets?per_page=100".format(
            repository
        ),
        headers=_ruleset_headers(token),
        method="GET",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=_TIMEOUT_SECONDS,
        ) as response:  # nosec B310
            raw = response.read(_MAX_BYTES + 1)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
    ) as exc:
        raise KnowledgeHubError("rulesets list request failed") from exc
    if len(raw) > _MAX_BYTES:
        raise KnowledgeHubError("rulesets list response exceeds byte budget")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("rulesets list response is invalid") from exc
    if not isinstance(payload, list):
        raise KnowledgeHubError("rulesets list response must be an array")
    return [row for row in payload if isinstance(row, Mapping)]


def _request_ruleset_detail(
    repository: str,
    ruleset_id: int,
    token: str,
) -> Mapping[str, Any]:
    request = urllib.request.Request(
        "https://api.github.com/repos/{}/rulesets/{}".format(
            repository,
            ruleset_id,
        ),
        headers=_ruleset_headers(token),
        method="GET",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=_TIMEOUT_SECONDS,
        ) as response:  # nosec B310
            raw = response.read(_MAX_BYTES + 1)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
    ) as exc:
        raise KnowledgeHubError("ruleset detail request failed") from exc
    if len(raw) > _MAX_BYTES:
        raise KnowledgeHubError("ruleset detail response exceeds byte budget")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("ruleset detail response is invalid") from exc
    if not isinstance(payload, Mapping):
        raise KnowledgeHubError("ruleset detail response must be an object")
    return payload


def _ruleset_ref_matches(pattern: str, branch: str) -> bool:
    ref = "refs/heads/{}".format(branch)
    if pattern == "~ALL":
        return True
    if pattern == "~DEFAULT_BRANCH":
        return True
    return fnmatch.fnmatchcase(ref, pattern)


def _ruleset_applies_to_branch(
    ruleset: Mapping[str, Any],
    branch: str,
) -> bool:
    conditions = ruleset.get("conditions")
    if not isinstance(conditions, Mapping):
        return False
    ref_name = conditions.get("ref_name")
    if not isinstance(ref_name, Mapping):
        return False
    includes = ref_name.get("include", [])
    excludes = ref_name.get("exclude", [])
    if not isinstance(includes, list) or not isinstance(excludes, list):
        return False
    included = any(
        isinstance(value, str) and _ruleset_ref_matches(value, branch)
        for value in includes
    )
    excluded = any(
        isinstance(value, str) and _ruleset_ref_matches(value, branch)
        for value in excludes
    )
    return included and not excluded


def _ruleset_required_status_checks(
    repository: str,
    branch: str,
    token: str,
) -> Dict[str, Any]:
    if not token:
        return {"observed": False, "contexts": []}
    try:
        rows = _request_rulesets_list(repository, token)
        contexts: List[str] = []
        for row in rows:
            if row.get("target") != "branch":
                continue
            if row.get("enforcement") != "active":
                continue
            ruleset_id = row.get("id")
            if not isinstance(ruleset_id, int) or ruleset_id < 1:
                return {"observed": False, "contexts": []}
            detail = _request_ruleset_detail(
                repository,
                ruleset_id,
                token,
            )
            if not _ruleset_applies_to_branch(detail, branch):
                continue
            rules = detail.get("rules", [])
            if not isinstance(rules, list):
                return {"observed": False, "contexts": []}
            for rule in rules:
                if not isinstance(rule, Mapping):
                    continue
                if rule.get("type") != "required_status_checks":
                    continue
                parameters = rule.get("parameters")
                if not isinstance(parameters, Mapping):
                    return {"observed": False, "contexts": []}
                checks = parameters.get("required_status_checks", [])
                if not isinstance(checks, list):
                    return {"observed": False, "contexts": []}
                for check in checks:
                    if not isinstance(check, Mapping):
                        continue
                    context = str(check.get("context") or "").strip()
                    if context:
                        contexts.append(context)
        return {
            "observed": True,
            "contexts": sorted(set(contexts)),
        }
    except KnowledgeHubError:
        return {"observed": False, "contexts": []}


def _rulesets_http_error(
    exc: urllib.error.HTTPError,
) -> Dict[str, Any]:
    try:
        raw = exc.read(_MAX_BYTES + 1)
        payload = json.loads(raw.decode("utf-8"))
        message = (
            str(payload.get("message", ""))
            if isinstance(payload, Mapping)
            else ""
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        message = ""
    if exc.code == 403 and "Upgrade to GitHub Pro" in message:
        status = "plan-gated"
        reason = "private-repository-rulesets-require-upgrade-or-public"
    elif exc.code == 403:
        status = "integration-forbidden"
        reason = "rulesets-not-readable-by-current-token"
    else:
        status = "unavailable"
        reason = "rulesets-api-http-error"
    return {
        "status": status,
        "reason": reason,
        "http_status": int(exc.code),
        "ruleset_count": 0,
        "message": message,
    }


def _rulesets_payload_result(
    raw: bytes,
    http_status: int,
) -> Dict[str, Any]:
    if len(raw) > _MAX_BYTES:
        return {
            "status": "unavailable",
            "reason": "rulesets-response-exceeds-byte-budget",
            "http_status": http_status,
            "ruleset_count": 0,
        }
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "status": "unavailable",
            "reason": "rulesets-response-invalid",
            "http_status": http_status,
            "ruleset_count": 0,
        }
    if not isinstance(payload, list):
        return {
            "status": "unavailable",
            "reason": "rulesets-response-not-list",
            "http_status": http_status,
            "ruleset_count": 0,
        }
    return {
        "status": "available",
        "reason": "",
        "http_status": http_status,
        "ruleset_count": len(payload),
    }


def _rulesets_capability(
    repository: str,
    token: str,
) -> Dict[str, Any]:
    if not token:
        return {
            "status": "not-probed",
            "reason": "github-token-unavailable",
            "http_status": 0,
            "ruleset_count": 0,
        }
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer {}".format(token),
        "User-Agent": "knowledge-hub-hosting-posture",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    request = urllib.request.Request(
        "https://api.github.com/repos/{}/rulesets".format(repository),
        headers=headers,
        method="GET",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=_TIMEOUT_SECONDS,
        ) as response:  # nosec B310
            raw = response.read(_MAX_BYTES + 1)
            status = int(getattr(response, "status", 200) or 200)
    except urllib.error.HTTPError as exc:
        return _rulesets_http_error(exc)
    except (urllib.error.URLError, TimeoutError, OSError):
        return {
            "status": "unavailable",
            "reason": "rulesets-api-network-error",
            "http_status": 0,
            "ruleset_count": 0,
        }
    return _rulesets_payload_result(raw, status)

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
    inventory_path = resolve_inside(root, branch_inventory)
    inventory = _load_object(inventory_path, "remote branch inventory")
    if inventory.get("repository") != repository:
        raise KnowledgeHubError("branch inventory repository identity mismatch")
    if inventory.get("source_revision") != source_revision:
        raise KnowledgeHubError("branch inventory source revision mismatch")
    metadata = _request_repository_metadata(repository, token)
    rulesets = _rulesets_capability(repository, token)
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
    branch_checks = {"observed": False, "contexts": []}
    ruleset_checks = {"observed": False, "contexts": []}
    if token:
        branch_metadata = _request_default_branch_metadata(
            repository,
            default_branch,
            token,
        )
        if str(branch_metadata.get("name") or "") != default_branch:
            raise KnowledgeHubError("default branch metadata identity mismatch")
        branch_checks = _branch_required_status_checks(branch_metadata)
        if rulesets.get("status") == "available":
            ruleset_checks = _ruleset_required_status_checks(
                repository,
                default_branch,
                token,
            )
    ruleset_observed = (
        ruleset_checks["observed"]
        if rulesets.get("status") == "available"
        else rulesets.get("status") == "plan-gated"
    )
    checks_observed = branch_checks["observed"] and ruleset_observed
    check_contexts = sorted(
        set(branch_checks["contexts"]).union(ruleset_checks["contexts"])
    )
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
        "default_branch_required_status_checks_observed": checks_observed,
        "default_branch_required_status_checks": check_contexts,
        "rulesets_capability": rulesets,
        "branch_inventory": branch_inventory,
        "canonical_write": False,
    }


def write_hosting_posture(root: pathlib.Path, relative: str, payload: Mapping[str, Any]) -> str:
    path = resolve_inside(root, relative)
    ensure_private_directory_tree(root, path.parent)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ensure_private_file(path)
    return str(path.relative_to(root))
