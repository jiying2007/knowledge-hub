"""Project-aware Knowledge Hub context assembly."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import time
import urllib.parse
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from .common import (
    ensure_private_directory,
    ensure_private_file,
    file_sha256,
    load_json,
    project_rows,
    registry_items,
    repository_rows,
    route_rows,
    source_id,
    utc_timestamp,
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
        base = _safe_resolve(path)
        if cwd == base or str(cwd).startswith(str(base).rstrip("/") + "/"):
            return str(workspace.get("workspace_ref", "")), dict(workspace)
    for repo in repositories:
        base = _expand_workspace_ref(str(repo.get("workspace_ref", "")))
        if base and (cwd == base or str(cwd).startswith(str(base).rstrip("/") + "/")):
            return str(repo.get("workspace_ref", "")), {"repo_id": repo.get("repo_id")}
    for route in routes:
        for workspace_ref in route.get("workspace_refs", []):
            base = _expand_workspace_ref(str(workspace_ref))
            if base and (cwd == base or str(cwd).startswith(str(base).rstrip("/") + "/")):
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
    source = item.get("source") if isinstance(item.get("source"), dict) else {}
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


def assemble_context(
    root: pathlib.Path,
    cwd: str,
    query: str,
    task_type: str = "general",
    limit: int = 8,
    context_budget: str = "normal",
    project_hint: str = "",
) -> Dict[str, Any]:
    started = time.monotonic()
    if task_type not in TASK_TYPES:
        raise ValueError("unsupported task type")
    if context_budget not in BUDGET_LIMITS:
        raise ValueError("unsupported context budget")
    if limit < 1:
        raise ValueError("limit must be >= 1")
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
    groups_list = list((load_json(root / "registry/project-groups.json", {}) or {}).get("groups", []))
    group_by_id = {str(row.get("id")): row for row in groups_list if row.get("id")}
    local_workspaces = list((load_json(root / "local/workspaces.json", {}) or {}).get("workspaces", []))
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
    recorded_workspace_head = str(
        (workspace_match.get("source_evidence") or {}).get("git_head", "")
    ) if isinstance(workspace_match.get("source_evidence"), Mapping) else ""
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
        if (
            target_selection["status"] == "unresolved"
            and (initial_query_selection.get("route") or {}).get("project_id")
            == cwd_route.get("project_id")
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
    search_payload = search(root, query, limit=effective_limit, filters=search_filters)
    search_payload["fallback_terms"] = []
    search_payload["fallback_results"] = []
    search_payload["fallback_count"] = 0
    if not search_payload["results"]:
        ignored = {"pcr02", "归档", "路径", "where", "archive"}
        fallback_terms = [term for term in terms if term not in ignored][:4]
        merged: List[Dict[str, Any]] = []
        seen: Set[Tuple[str, int, str]] = set()
        for term in fallback_terms:
            fallback = search(root, term, limit=effective_limit, filters=search_filters)
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
        search_payload["zero_hit"]["degraded_terms"] = fallback_terms
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
    context = payload.get("context") if isinstance(payload.get("context"), Mapping) else {}
    route_selection = (
        payload.get("route_selection") if isinstance(payload.get("route_selection"), Mapping) else {}
    )
    search_payload = payload.get("search") if isinstance(payload.get("search"), Mapping) else {}
    zero_hit = search_payload.get("zero_hit") if isinstance(search_payload.get("zero_hit"), Mapping) else {}
    search_trace = (
        search_payload.get("search_trace")
        if isinstance(search_payload.get("search_trace"), Mapping)
        else {}
    )
    search_index = search_payload.get("index") if isinstance(search_payload.get("index"), Mapping) else {}
    preflight = (
        payload.get("knowledge_preflight")
        if isinstance(payload.get("knowledge_preflight"), Mapping)
        else {}
    )

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
    for candidate in route_selection.get("candidates", []):
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
    telemetry = payload.get("telemetry") if isinstance(payload.get("telemetry"), Mapping) else {}
    candidate_recommendation = (
        payload.get("candidate_recommendation")
        if isinstance(payload.get("candidate_recommendation"), Mapping)
        else {}
    )

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
            "risks": list(context.get("risks", []))[:2],
        },
        "search_summary": {
            "status": search_payload.get("status", ""),
            "count": search_payload.get("count", len(search_payload.get("results", []))),
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
    context = payload.get("context") or {}
    result_ids = []
    for section in ("current", "recent", "related", "search_fallback"):
        for result in context.get(section, []):
            result_id = str(result.get("item_id") or result.get("id") or "")
            if result_id and result_id not in result_ids:
                result_ids.append(result_id)
    search_index = ((payload.get("search") or {}).get("index") or {})
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
        "selected_project_id": (payload.get("route") or {}).get("project_id", ""),
        "current_count": len(context.get("current", [])),
        "recent_count": len(context.get("recent", [])),
        "result_ids": result_ids,
        "latency_ms": payload.get("latency_ms", 0),
        "index_state": search_index.get("state", ""),
        "index_rebuilt": bool(search_index.get("rebuilt", False)),
        "index_build_ms": search_index.get("build_duration_ms", 0),
        "token_cache_status": search_index.get("token_cache_status", ""),
        "token_cache_hits": search_index.get("token_cache_hits", 0),
        "token_cache_misses": search_index.get("token_cache_misses", 0),
        "stage_timing": dict(payload.get("timing") or {}),
        "search_stage_timing": dict(((payload.get("search") or {}).get("timing") or {})),
        "raw_query_stored": False,
    }
    path = root / ".cache/knowledge-hub/context-telemetry.jsonl"
    return append_optional_telemetry(path, row, enabled=enabled)
