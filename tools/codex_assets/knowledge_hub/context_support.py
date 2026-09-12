"""Routing, receipt, and summary helpers for Knowledge Hub context assembly."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import urllib.parse
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from .common import ensure_private_directory, ensure_private_file, file_sha256, source_id


TASK_TYPES = {"debug", "archive", "release", "decision", "runbook", "source", "validation", "session", "general"}
BUDGET_LIMITS = {"small": 3, "normal": 8, "deep": 16}
SUMMARY_JSON_MAX_BYTES = 2048
SUMMARY_JSON_MAX_ITEMS = 3
CONTEXT_RECEIPT_SCHEMA_VERSION = 1
CONTEXT_RECEIPT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
CONTEXT_RECEIPT_REGISTRY_PATHS = (
    "registry/items.jsonl",
    "registry/sources.json",
    "registry/projects.json",
    "registry/repositories.json",
    "registry/project-groups.json",
    "registry/project-routes.json",
    "local/workspaces.json",
)
TASK_KIND_WEIGHTS: Dict[str, Dict[str, int]] = {
    "debug": {"debug-record": 10, "runbook": 5, "validation": 3, "project-archive": 2},
    "archive": {"project-archive": 10, "codex-session": 7, "audit": 4, "debug-record": 3},
    "release": {"validation": 10, "runbook": 8, "project-current": 6, "decision": 5, "project-archive": 2},
    "decision": {"decision": 10, "architecture": 6, "validation": 4, "audit": 2},
    "runbook": {"runbook": 10, "standard": 5, "validation": 3},
    "source": {"artifact-ref": 10, "external-source-note": 8, "project-current": 5, "audit": 4},
    "validation": {"validation": 10, "debug-record": 5, "runbook": 3, "project-archive": 2},
    "session": {"codex-session": 10, "project-archive": 6, "debug-record": 3},
    "general": {"project-current": 5, "runbook": 4, "decision": 4, "architecture": 3, "standard": 3},
}


def normalize_remote_key(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if re.match(r"^[^/@:]+@[^/:]+:.+", text):
        text = text.split(":", 1)[1]
    else:
        parsed = urllib.parse.urlparse(text)
        if parsed.scheme and parsed.path:
            text = parsed.path
    text = text.strip().strip("/")
    if text.endswith(".git"):
        text = text[:-4]
    return text.lower()


def _safe_resolve(value: str) -> pathlib.Path:
    try:
        return pathlib.Path(value).expanduser().resolve(strict=False)
    except OSError:
        return pathlib.Path(value).expanduser()


def find_git_config(cwd_text: str) -> Tuple[Optional[pathlib.Path], Optional[pathlib.Path]]:
    cwd = _safe_resolve(cwd_text)
    for directory in [cwd] + list(cwd.parents):
        git_entry = directory / ".git"
        if git_entry.is_dir() and (git_entry / "config").exists():
            return git_entry / "config", directory
        if not git_entry.is_file():
            continue
        try:
            content = git_entry.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not content.startswith("gitdir:"):
            continue
        gitdir = pathlib.Path(content.split(":", 1)[1].strip())
        if not gitdir.is_absolute():
            gitdir = directory / gitdir
        if (gitdir / "config").exists():
            return gitdir / "config", directory
    return None, None


def _git_head_from_config(config_path: Optional[pathlib.Path]) -> str:
    if not config_path:
        return ""
    git_dir = config_path.parent
    try:
        head = (git_dir / "HEAD").read_text(encoding="ascii", errors="replace").strip()
    except OSError:
        return ""
    if not head.startswith("ref:"):
        return head if re.fullmatch(r"[0-9a-f]{40}", head) else ""
    ref = head.split(":", 1)[1].strip()
    try:
        commit = (git_dir / ref).read_text(encoding="ascii", errors="replace").strip()
    except OSError:
        commit = ""
        try:
            for line in (git_dir / "packed-refs").read_text(
                encoding="ascii", errors="replace"
            ).splitlines():
                if not line or line.startswith(("#", "^")):
                    continue
                value, name = line.split(" ", 1)
                if name == ref:
                    commit = value
                    break
        except (OSError, ValueError):
            commit = ""
    return commit if re.fullmatch(r"[0-9a-f]{40}", commit) else ""


def remote_urls_from_config(config_path: Optional[pathlib.Path]) -> List[Dict[str, str]]:
    if not config_path:
        return []
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError:
        return []
    rows: List[Dict[str, str]] = []
    current_remote = ""
    for line in text.splitlines():
        section = re.match(r'\s*\[remote\s+"([^"]+)"\]\s*', line)
        if section:
            current_remote = section.group(1)
            continue
        if line.startswith("["):
            current_remote = ""
            continue
        match = re.match(r"\s*url\s*=\s*(.+?)\s*$", line)
        if match and current_remote:
            rows.append(
                {"remote": current_remote, "url": match.group(1), "remote_key": normalize_remote_key(match.group(1))}
            )
    return sorted(rows, key=lambda row: (0 if row["remote"] == "origin" else 1, row["remote"]))


def _route_for_repo(repo: Optional[Mapping[str, Any]], routes: Sequence[Mapping[str, Any]], projects: Mapping[str, Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
    if not repo:
        return None
    repo_id = repo.get("repo_id")
    project_id = str(repo.get("project_id", ""))
    groups = set(repo.get("groups", []))
    for route in routes:
        if project_id and route.get("project_id") == project_id:
            return route
    for route in routes:
        if repo_id in route.get("repo_refs", []) or route.get("group_id") in groups:
            return route
    project = projects.get(project_id, {})
    for group_id in project.get("groups", []):
        for route in routes:
            if route.get("group_id") == group_id:
                return route
    return None


def _query_route(
    query: str,
    routes: Sequence[Mapping[str, Any]],
    exclude_project_id: str = "",
) -> Tuple[Optional[Mapping[str, Any]], int, List[Dict[str, Any]]]:
    selection = _query_route_selection(query, routes, exclude_project_id=exclude_project_id)
    return selection["route"], selection["score"], selection["matches"]


def _phrase_matches(query: str, phrase: str, identifier: bool = False) -> bool:
    normalized_query = " ".join(query.casefold().split())
    normalized_phrase = " ".join(phrase.casefold().split())
    if not normalized_phrase:
        return False
    if not re.search(r"[a-z0-9]", normalized_phrase):
        return normalized_phrase in normalized_query
    boundary_chars = r"a-z0-9_-"
    pattern = r"(?<![{}]){}(?![{}])".format(
        boundary_chars,
        re.escape(normalized_phrase),
        boundary_chars,
    )
    if re.search(pattern, normalized_query):
        return True
    if identifier:
        alternative = normalized_phrase.replace("-", "_")
        if alternative != normalized_phrase:
            alternative_pattern = r"(?<![{}]){}(?![{}])".format(
                boundary_chars,
                re.escape(alternative),
                boundary_chars,
            )
            return bool(re.search(alternative_pattern, normalized_query))
    return False


def _query_route_selection(
    query: str,
    routes: Sequence[Mapping[str, Any]],
    exclude_project_id: str = "",
) -> Dict[str, Any]:
    alias_owners: Dict[str, Set[str]] = {}
    alias_display: Dict[str, str] = {}
    for route in routes:
        project_id = str(route.get("project_id", ""))
        if exclude_project_id and project_id == exclude_project_id:
            continue
        for alias in route.get("aliases", []):
            normalized = " ".join(str(alias).casefold().split())
            if normalized:
                alias_owners.setdefault(normalized, set()).add(project_id)
                alias_display.setdefault(normalized, str(alias))
    ambiguous_aliases = [
        (alias, owners)
        for alias, owners in alias_owners.items()
        if len(owners) > 1 and _phrase_matches(query, alias_display[alias])
    ]
    candidates: List[Dict[str, Any]] = []
    for route in routes:
        if exclude_project_id and route.get("project_id") == exclude_project_id:
            continue
        score = 0
        matches: List[Dict[str, Any]] = []
        project_id = str(route.get("project_id", ""))
        if project_id and _phrase_matches(query, project_id, identifier=True):
            score = 10000 + len(project_id)
            matches.append({"type": "project-id", "value": route.get("project_id")})
        seen_aliases: Set[str] = set()
        for alias in route.get("aliases", []):
            normalized = str(alias).casefold()
            if normalized in seen_aliases:
                continue
            seen_aliases.add(normalized)
            if normalized == project_id.casefold():
                continue
            if score < 10000 and _phrase_matches(query, str(alias)):
                score = max(score, 100 + len(normalized))
                matches.append({"type": "alias", "value": alias})
        for alias in route.get("topic_aliases", []):
            normalized = str(alias).casefold()
            if normalized and _phrase_matches(query, str(alias)):
                score = max(score, 500 + len(normalized))
                matches.append({"type": "topic-alias", "value": alias})
        if score:
            candidates.append(
                {
                    "route": route,
                    "project_id": route.get("project_id"),
                    "score": score,
                    "matches": matches,
                }
            )
    candidates.sort(key=lambda row: (-row["score"], str(row["project_id"])))
    if not candidates:
        return {
            "status": "unresolved",
            "route": None,
            "score": 0,
            "matches": [],
            "candidates": [],
        }
    best_score = candidates[0]["score"]
    public_candidates = [
        {
            "project_id": row["project_id"],
            "score": row["score"],
            "matches": row["matches"],
        }
        for row in candidates[:10]
    ]
    if best_score < 500 and ambiguous_aliases:
        project_ids = sorted(
            {
                project_id
                for _, owners in ambiguous_aliases
                for project_id in owners
            }
        )
        return {
            "status": "ambiguous",
            "route": None,
            "score": best_score,
            "matches": [
                {
                    "type": "ambiguous-alias",
                    "values": sorted(alias_display[alias] for alias, _ in ambiguous_aliases),
                    "project_ids": project_ids,
                }
            ],
            "candidates": public_candidates,
        }
    best = [row for row in candidates if row["score"] == best_score]
    if len(best) > 1:
        project_ids = [str(row["project_id"]) for row in best]
        return {
            "status": "ambiguous",
            "route": None,
            "score": best_score,
            "matches": [{"type": "ambiguous", "project_ids": project_ids}],
            "candidates": public_candidates,
        }
    return {
        "status": "selected",
        "route": best[0]["route"],
        "score": best_score,
        "matches": best[0]["matches"],
        "candidates": public_candidates,
    }


def _expand_workspace_ref(value: str) -> Optional[pathlib.Path]:
    if value.startswith("~/"):
        return pathlib.Path(value).expanduser()
    return None


def _workspace_for_cwd(
    cwd_text: str,
    local_workspaces: Sequence[Mapping[str, Any]],
    repositories: Sequence[Mapping[str, Any]],
    routes: Sequence[Mapping[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    cwd = _safe_resolve(cwd_text)
    for workspace in local_workspaces:
        path = str(workspace.get("path", ""))
        if not path:
            continue
        workspace_base = _safe_resolve(path)
        if cwd == workspace_base or str(cwd).startswith(str(workspace_base).rstrip("/") + "/"):
            return str(workspace.get("workspace_ref", "")), dict(workspace)
    for repo in repositories:
        repo_base = _expand_workspace_ref(str(repo.get("workspace_ref", "")))
        if repo_base and (cwd == repo_base or str(cwd).startswith(str(repo_base).rstrip("/") + "/")):
            return str(repo.get("workspace_ref", "")), {"repo_id": repo.get("repo_id")}
    for route in routes:
        for workspace_ref in route.get("workspace_refs", []):
            route_base = _expand_workspace_ref(str(workspace_ref))
            if route_base and (cwd == route_base or str(cwd).startswith(str(route_base).rstrip("/") + "/")):
                return str(workspace_ref), {"project_id": route.get("project_id")}
    return "", {}


def _route_project_ids(
    route: Optional[Mapping[str, Any]],
    group_by_id: Mapping[str, Mapping[str, Any]],
    repo_by_id: Mapping[str, Mapping[str, Any]],
) -> Set[str]:
    if not route:
        return set()
    ids = {str(route.get("project_id"))} if route.get("project_id") else set()
    if route.get("route_scope") == "project":
        return ids
    group = group_by_id.get(str(route.get("group_id", "")), {})
    ids.update(str(value) for value in group.get("member_project_ids", []))
    for repo_id in route.get("repo_refs", []):
        project_id = repo_by_id.get(str(repo_id), {}).get("project_id")
        if project_id:
            ids.add(str(project_id))
    return ids


def _route_domains(
    route: Optional[Mapping[str, Any]],
    project_ids: Set[str],
    projects: Mapping[str, Mapping[str, Any]],
) -> Set[str]:
    if not route:
        return set()
    explicit = {str(value) for value in route.get("domain_refs", []) if str(value)}
    if explicit:
        return explicit
    result: Set[str] = set()
    for project_id in project_ids:
        domain = str(projects.get(project_id, {}).get("domain", ""))
        if domain.startswith("domains/"):
            domain = domain.split("/", 1)[1]
        result.add(domain or "projects/{}".format(project_id))
    return result


def _route_matches_domain(domain: str, refs: Iterable[str]) -> Optional[str]:
    for ref in refs:
        if domain == ref or domain.startswith(ref + "/"):
            return ref
    return None


def _rank_item(
    item: Mapping[str, Any],
    terms: Sequence[str],
    task_type: str,
    domain_refs: Set[str],
    source_ids: Set[str],
    route_selected: bool,
) -> Tuple[int, List[str]]:
    haystack = "\n".join(
        str(value)
        for value in (
            item.get("id", ""),
            item.get("title", ""),
            item.get("path", ""),
            item.get("domain", ""),
            item.get("kind", ""),
            item.get("summary_zh", ""),
            source_id(item),
            " ".join(str(tag) for tag in item.get("tags", []) if isinstance(tag, str)),
        )
    ).lower()
    score = 0
    reasons: List[str] = []
    for term in terms:
        if term in haystack:
            score += 3
            reasons.append("query-term:{}".format(term))
    matched_domain = _route_matches_domain(str(item.get("domain", "")), domain_refs)
    route_matched = bool(matched_domain)
    if matched_domain:
        score += 6
        reasons.append("domain:{}".format(matched_domain))
    item_source = source_id(item)
    if item_source and item_source in source_ids:
        score += 3
        route_matched = True
        reasons.append("source:{}".format(item_source))
    if route_selected and not route_matched:
        return 0, []
    if not route_matched and not reasons:
        return 0, []
    kind = str(item.get("kind", ""))
    kind_weight = TASK_KIND_WEIGHTS.get(task_type, {}).get(kind, 0)
    if kind_weight:
        score += kind_weight
        reasons.append("task-kind:{}:{}".format(task_type, kind))
    status = str(item.get("status", ""))
    status_weight = {"active": 9, "reviewing": 4, "draft": 1, "personal": -2, "archived": -4, "superseded": -8, "rejected": -10}.get(status, 0)
    score += status_weight
    reasons.append("status:{}".format(status))
    if str(item.get("path", "")).startswith("artifacts/manifests/"):
        score -= 3
        reasons.append("manifest-evidence-lower-priority")
    return score, reasons


def _public_item(score: int, item: Mapping[str, Any], reasons: Sequence[str]) -> Dict[str, Any]:
    source_value = item.get("source")
    source: Mapping[str, Any] = source_value if isinstance(source_value, Mapping) else {}
    return {
        "score": score,
        "id": item.get("id", ""),
        "title": item.get("title", ""),
        "kind": item.get("kind", ""),
        "domain": item.get("domain", ""),
        "path": item.get("path", ""),
        "status": item.get("status", ""),
        "source_id": source_id(item),
        "source_type": source.get("type", ""),
        "tags": item.get("tags", []),
        "evidence_strength": item.get("evidence_strength", ""),
        "manual_validation_pending": bool(item.get("manual_validation_pending", False)),
        "why_selected": list(reasons),
    }


def _compact_mapping(value: Any, fields: Sequence[str]) -> Optional[Dict[str, Any]]:
    if not isinstance(value, Mapping):
        return None
    compact: Dict[str, Any] = {}
    for field in fields:
        candidate = value.get(field)
        if candidate is None or candidate == "" or candidate == [] or candidate == {}:
            continue
        compact[field] = candidate
    return compact


def _compact_context_item(row: Mapping[str, Any]) -> Dict[str, Any]:
    compact = {
        "id": row.get("id") or row.get("item_id", ""),
        "title": row.get("title", ""),
        "kind": row.get("kind", ""),
        "status": row.get("status", ""),
        "path": row.get("path", ""),
    }
    source = row.get("source_id")
    if source:
        compact["source_id"] = source
    reasons = [str(reason) for reason in row.get("why_selected", []) if str(reason)][:3]
    if reasons:
        compact["why_selected"] = reasons
    return compact


def _summary_json_size(summary: Mapping[str, Any]) -> int:
    return len(
        json.dumps(summary, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def _path_signature(path: pathlib.Path) -> str:
    return file_sha256(path) if path.is_file() else "absent"


def context_receipt_path(root: pathlib.Path, key: str) -> pathlib.Path:
    if not CONTEXT_RECEIPT_KEY_PATTERN.fullmatch(key):
        raise ValueError("receipt key must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}")
    return root / ".cache/knowledge-hub/context-receipts" / "{}.json".format(key)


def context_receipt_request(
    root: pathlib.Path,
    cwd: str,
    query: str,
    task_type: str,
    limit: int,
    context_budget: str,
    project_hint: str,
) -> Dict[str, Any]:
    git_config, _ = find_git_config(cwd)
    return {
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "cwd": str(_safe_resolve(cwd)),
        "task_type": task_type,
        "limit": limit,
        "context_budget": context_budget,
        "project_hint": project_hint,
        "workspace_git_head": _git_head_from_config(git_config),
        "registry_signatures": {
            relative: _path_signature(root / relative)
            for relative in CONTEXT_RECEIPT_REGISTRY_PATHS
        },
    }


def load_context_receipt(
    root: pathlib.Path, key: str, request: Mapping[str, Any]
) -> Tuple[Optional[Dict[str, Any]], str]:
    path = context_receipt_path(root, key)
    if not path.is_file():
        return None, "missing"
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "invalid"
    if receipt.get("schema_version") != CONTEXT_RECEIPT_SCHEMA_VERSION:
        return None, "schema-mismatch"
    if receipt.get("request") != dict(request):
        return None, "request-signature-changed"
    evidence = receipt.get("evidence_signatures")
    if not isinstance(evidence, dict):
        return None, "evidence-signatures-missing"
    for relative, expected in evidence.items():
        target = (root / str(relative)).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            return None, "unsafe-evidence-path"
        if _path_signature(target) != expected:
            return None, "selected-evidence-changed"
    summary = receipt.get("summary")
    if not isinstance(summary, dict):
        return None, "summary-missing"
    return dict(summary), "hit"


def write_context_receipt(
    root: pathlib.Path,
    key: str,
    request: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> pathlib.Path:
    path = context_receipt_path(root, key)
    raw_paths = ((summary.get("context_contract") or {}).get("raw_evidence") or [])
    evidence_signatures: Dict[str, str] = {}
    for value in raw_paths:
        relative = str(value)
        target = (root / relative).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            continue
        evidence_signatures[relative] = _path_signature(target)
    payload = {
        "schema_version": CONTEXT_RECEIPT_SCHEMA_VERSION,
        "key": key,
        "request": dict(request),
        "evidence_signatures": evidence_signatures,
        "summary": dict(summary),
        "raw_query_stored": False,
    }
    ensure_private_directory(path.parent)
    temporary = path.with_name(".{}.{}.tmp".format(path.name, os.getpid()))
    temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    ensure_private_file(temporary)
    os.replace(str(temporary), str(path))
    ensure_private_file(path)
    return path


def attach_context_receipt(
    summary: Dict[str, Any], key: str, reused: bool, reason: str
) -> Dict[str, Any]:
    summary["context_receipt"] = {
        "key": key,
        "reused": reused,
        "reason": reason,
        "raw_query_stored": False,
    }
    return _fit_summary_budget(summary)


def _sync_summary_raw_evidence(summary: Dict[str, Any]) -> None:
    context = summary.get("context", {})
    contract = summary.get("context_contract", {})
    paths: List[str] = []
    for section in ("current", "recent", "related", "search_fallback"):
        for row in context.get(section, []):
            path = str(row.get("path", ""))
            if path and path not in paths:
                paths.append(path)
    contract["raw_evidence"] = paths


def _fit_summary_budget(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Keep the L1 projection valid and traceable within its byte contract."""
    if _summary_json_size(summary) <= SUMMARY_JSON_MAX_BYTES:
        return summary
    context = summary["context"]
    sections = ("current", "recent", "related", "search_fallback")

    for section in reversed(sections):
        for row in reversed(context.get(section, [])):
            reasons = row.get("why_selected", [])
            if len(reasons) > 1:
                row["why_selected"] = reasons[:1]
    if _summary_json_size(summary) <= SUMMARY_JSON_MAX_BYTES:
        return summary

    risks = context.get("risks", [])
    while len(risks) > 2 and _summary_json_size(summary) > SUMMARY_JSON_MAX_BYTES:
        risks.pop(-2)

    while _summary_json_size(summary) > SUMMARY_JSON_MAX_BYTES:
        row_count = sum(len(context.get(section, [])) for section in sections)
        if row_count <= 1:
            break
        removed = False
        for section in reversed(sections):
            rows = context.get(section, [])
            if rows:
                rows.pop()
                removed = True
                break
        if not removed:
            break
        _sync_summary_raw_evidence(summary)

    optional_paths = (
        (summary.get("search_summary", {}).get("search_trace", {}), "excluded_by_filters"),
        (summary.get("search_summary", {}).get("search_trace", {}), "retry_queries"),
        (summary.get("search_summary", {}), "latency_ms"),
        (summary, "latency_ms"),
        (summary.get("candidate_recommendation", {}), "reason_zh"),
        (summary.get("telemetry", {}), "error_code"),
    )
    for mapping, field in optional_paths:
        if _summary_json_size(summary) <= SUMMARY_JSON_MAX_BYTES:
            break
        mapping.pop(field, None)

    for section in reversed(sections):
        for row in reversed(context.get(section, [])):
            if _summary_json_size(summary) <= SUMMARY_JSON_MAX_BYTES:
                break
            row.pop("title", None)
            row.pop("why_selected", None)

    if _summary_json_size(summary) > SUMMARY_JSON_MAX_BYTES:
        context["risks"] = []
        summary.get("route_selection", {}).pop("candidates", None)
        repo_route = summary.get("repo_route")
        if isinstance(repo_route, dict):
            repo_route.pop("groups", None)
            repo_route.pop("lifecycle", None)
        route = summary.get("route")
        if isinstance(route, dict):
            route.pop("name", None)

    return summary


def _current_exclusion_reason(row: Mapping[str, Any]) -> str:
    status = str(row.get("status", ""))
    if status in {"archived", "superseded", "rejected"}:
        return "terminal-status"
    if str(row.get("kind", "")) in {"audit", "artifact-ref", "project-archive", "codex-session"}:
        return "audit-or-provenance-kind"
    path = str(row.get("path", ""))
    if path.startswith("artifacts/manifests/") or "/archive/" in path:
        return "historical-path"
    tags = {str(value) for value in row.get("tags", []) if isinstance(value, str)}
    if tags.intersection({"archive-only", "provenance", "tombstone", "historical-session", "historical-release"}):
        return "historical-tag"
    if str(row.get("source_type", "")) in {"retired-source-provenance", "artifact-ref", "archive"}:
        return "provenance-source"
    return ""
