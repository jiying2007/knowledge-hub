#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(
    description="Resolve Knowledge Hub context by Git remote key, query aliases, and Hub registries."
)
parser.add_argument("--cwd", default=str(pathlib.Path.cwd()))
parser.add_argument("--query", required=True)
parser.add_argument(
    "--task-type",
    choices=["debug", "archive", "release", "decision", "runbook", "source", "validation", "session", "general"],
    default="general",
)
parser.add_argument("--json", action="store_true")
parser.add_argument("--limit", type=int, default=8)
args = parser.parse_args(argv)

if args.limit < 1:
    parser.error("--limit must be >= 1")

registry_dir = root / "registry"
routes_path = registry_dir / "project-routes.json"
repos_path = registry_dir / "repositories.json"
groups_path = registry_dir / "project-groups.json"
projects_path = registry_dir / "projects.json"
items_path = registry_dir / "items.jsonl"
local_workspaces_path = root / "local" / "workspaces.json"


def read_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


routes = read_json(routes_path, {}).get("routes", [])
repositories = read_json(repos_path, {}).get("repositories", [])
groups = read_json(groups_path, {}).get("groups", [])
projects = read_json(projects_path, {}).get("projects", [])
local_workspaces = read_json(local_workspaces_path, {}).get("workspaces", [])

repo_by_id = {repo.get("repo_id"): repo for repo in repositories if repo.get("repo_id")}
repo_by_remote = {
    repo.get("remote_key", "").lower(): repo
    for repo in repositories
    if repo.get("remote_key")
}
group_by_id = {group.get("id"): group for group in groups if group.get("id")}
project_by_id = {project.get("id"): project for project in projects if project.get("id")}


def normalize_remote_key(value):
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


def expand_safe_workspace_ref(value):
    text = str(value or "")
    allowed = ("~/knowledge-hub", "~/codex", "~/.codex")
    if not text.startswith(allowed):
        return None
    return pathlib.Path(text).expanduser()


def safe_resolve(path_text):
    try:
        return pathlib.Path(path_text).expanduser().resolve(strict=False)
    except Exception:
        return pathlib.Path(path_text).expanduser()


def find_git_config(cwd_text):
    cwd = safe_resolve(cwd_text)
    candidates = [cwd] + list(cwd.parents)
    for directory in candidates:
        git_entry = directory / ".git"
        if git_entry.is_dir():
            config = git_entry / "config"
            if config.exists():
                return config, directory
        if git_entry.is_file():
            try:
                content = git_entry.read_text().strip()
            except Exception:
                continue
            if not content.startswith("gitdir:"):
                continue
            gitdir = content.split(":", 1)[1].strip()
            gitdir_path = pathlib.Path(gitdir)
            if not gitdir_path.is_absolute():
                gitdir_path = directory / gitdir_path
            config = gitdir_path / "config"
            if config.exists():
                return config, directory
    return None, None


def remote_urls_from_config(config_path):
    if not config_path:
        return []
    try:
        text = config_path.read_text()
    except Exception:
        return []
    urls = []
    current_remote = None
    for line in text.splitlines():
        section = re.match(r'\s*\[remote\s+"([^"]+)"\]\s*', line)
        if section:
            current_remote = section.group(1)
            continue
        if line.startswith("["):
            current_remote = None
            continue
        url = re.match(r"\s*url\s*=\s*(.+?)\s*$", line)
        if url and current_remote:
            urls.append({"remote": current_remote, "url": url.group(1), "remote_key": normalize_remote_key(url.group(1))})
    urls.sort(key=lambda row: 0 if row["remote"] == "origin" else 1)
    return urls


def route_for_repo(repo):
    if not repo:
        return None
    repo_id = repo.get("repo_id")
    group_ids = set(repo.get("groups", []))
    for route in routes:
        if repo_id in route.get("repo_refs", []):
            return route
        if route.get("group_id") in group_ids:
            return route
    project_id = repo.get("project_id")
    if project_id:
        project = project_by_id.get(project_id)
        for group_id in project.get("groups", []) if project else []:
            for route in routes:
                if route.get("group_id") == group_id:
                    return route
    return None


def workspace_ref_for_cwd(cwd_text):
    cwd = safe_resolve(cwd_text)
    for workspace in local_workspaces:
        path = workspace.get("path")
        if not path:
            continue
        base = safe_resolve(path)
        if cwd == base or str(cwd).startswith(str(base).rstrip("/") + "/"):
            return workspace.get("workspace_ref"), workspace
    for repo in repositories:
        base = expand_safe_workspace_ref(repo.get("workspace_ref"))
        if base and (cwd == base or str(cwd).startswith(str(base).rstrip("/") + "/")):
            return repo.get("workspace_ref"), {"repo_id": repo.get("repo_id")}
    for route in routes:
        for workspace_ref in route.get("workspace_refs", []):
            base = expand_safe_workspace_ref(workspace_ref)
            if base and (cwd == base or str(cwd).startswith(str(base).rstrip("/") + "/")):
                return workspace_ref, {"project_id": route.get("project_id")}
    return None, None


git_config, git_root = find_git_config(args.cwd)
git_remotes = remote_urls_from_config(git_config)
matched_repo = None
matched_remote = None
for remote in git_remotes:
    repo = repo_by_remote.get(remote["remote_key"])
    if repo:
        matched_repo = repo
        matched_remote = remote
        break

workspace_ref, workspace_match = workspace_ref_for_cwd(args.cwd)
best_route = route_for_repo(matched_repo)
best_matches = []
best_score = 0

if matched_repo:
    best_score += 100
    best_matches.append({
        "type": "git-remote",
        "remote": matched_remote.get("remote"),
        "remote_key": matched_remote.get("remote_key"),
        "repo_id": matched_repo.get("repo_id"),
    })
if workspace_ref and not best_route:
    for route in routes:
        if workspace_ref in route.get("workspace_refs", []):
            best_route = route
            best_score += 60
            best_matches.append({"type": "workspace-ref", "value": workspace_ref})
            break

query_lower = args.query.lower()
if not best_route:
    for route in routes:
        score = 0
        matches = []
        for alias in route.get("aliases", []):
            if alias.lower() in query_lower:
                score += 20 + len(alias)
                matches.append({"type": "alias", "value": alias})
        if score > best_score:
            best_route = route
            best_score = score
            best_matches = matches


def load_items():
    rows = []
    if not items_path.exists():
        return rows
    for line in items_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


items = load_items()
query_terms = [part.lower() for part in re.split(r"[/_\-\s]+", args.query) if len(part) >= 3]


def source_id(item):
    source = item.get("source")
    if isinstance(source, dict):
        return source.get("source_id", "")
    return ""


def route_project_ids(route):
    if not route:
        return set()
    ids = set()
    if route.get("project_id"):
        ids.add(route.get("project_id"))
    group = group_by_id.get(route.get("group_id"))
    if group:
        ids.update(group.get("member_project_ids", []))
    for repo_id in route.get("repo_refs", []):
        repo = repo_by_id.get(repo_id, {})
        if repo.get("project_id"):
            ids.add(repo.get("project_id"))
    return ids


active_project_ids = route_project_ids(best_route)
active_source_ids = set(best_route.get("default_source_ids", [])) if best_route else set()


def item_score(item):
    haystack = "\n".join(
        str(value)
        for value in [
            item.get("id", ""),
            item.get("title", ""),
            item.get("path", ""),
            item.get("domain", ""),
            item.get("kind", ""),
            item.get("summary_zh", ""),
            source_id(item),
            " ".join(str(tag) for tag in item.get("tags", []) if isinstance(tag, str)),
        ]
    ).lower()
    score = 0
    for term in query_terms:
        if term in haystack:
            score += 1
    domain = item.get("domain", "")
    route_matched = False
    for project_id in active_project_ids:
        if domain == f"projects/{project_id}" or domain.startswith(f"projects/{project_id}/"):
            score += 2
            route_matched = True
            break
    if source_id(item) in active_source_ids:
        score += 1
        route_matched = True
    if best_route and active_project_ids and not route_matched:
        return 0
    if score <= 0 and not route_matched:
        return 0
    if args.task_type == "debug" and item.get("kind") == "debug-record":
        score += 2
    if args.task_type == "runbook" and item.get("kind") == "runbook":
        score += 2
    if args.task_type == "decision" and item.get("kind") == "decision":
        score += 2
    if args.task_type == "validation" and item.get("kind") == "validation":
        score += 2
    return score


ranked = []
for item in items:
    score = item_score(item)
    if score <= 0:
        continue
    ranked.append((score, item))
ranked.sort(key=lambda pair: (-pair[0], pair[1].get("id", "")))


def search_matches():
    cmd = [
        "rtk",
        "bash",
        str(root / "tools" / "knowledge-search.sh"),
        args.query,
        "--json",
        "--limit",
        str(args.limit),
    ]
    completed = subprocess.run(cmd, cwd=str(root), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode not in (0, 1):
        return {"error": completed.stderr.strip(), "results": []}
    try:
        return json.loads(completed.stdout)
    except Exception:
        return {"error": "knowledge-search output was not valid JSON", "results": []}


search_payload = search_matches()

candidate_required_types = {"debug", "release", "decision", "validation", "session"}
candidate_recommendation = {
    "required": args.task_type in candidate_required_types,
    "reason_zh": "该任务类型可能产生长期项目事实、证据或会话结论；完成或中断时应写 Hub candidate，或明确无可归档结论。"
    if args.task_type in candidate_required_types
    else "普通查询不强制生成 Hub candidate。",
    "allowed_kinds": ["debug-record", "validation", "decision", "runbook", "codex-session"]
    if args.task_type in candidate_required_types
    else [],
}

repo_summary = None
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

route_summary = None
if best_route:
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
        "default_source_ids": best_route.get("default_source_ids", []),
        "retired_route_ids": best_route.get("retired_route_ids", []),
        "route_key_policy": best_route.get("route_key_policy", "git-remote-first"),
        "matched_by": best_matches,
    }

payload = {
    "schema_version": 2,
    "read_only": True,
    "cwd": args.cwd,
    "query": args.query,
    "task_type": args.task_type,
    "knowledge_preflight": {
        "required": args.task_type in {"debug", "archive", "release", "decision", "runbook", "source", "validation", "session"},
        "source_of_truth": "registry/repositories.json plus registry/project-groups.json, registry/project-routes.json, registry/items.jsonl and knowledge-search",
    },
    "repo_route": repo_summary,
    "route": route_summary,
    "workspace_ref": workspace_ref,
    "workspace_match": workspace_match or {},
    "git_remotes_detected": git_remotes,
    "ranked_items": [
        {
            "score": score,
            "id": item.get("id", ""),
            "title": item.get("title", ""),
            "kind": item.get("kind", ""),
            "domain": item.get("domain", ""),
            "path": item.get("path", ""),
            "status": item.get("status", ""),
            "source_id": source_id(item),
        }
        for score, item in ranked[: args.limit]
    ],
    "search": search_payload,
    "candidate_recommendation": candidate_recommendation,
    "guardrails_zh": [
        "Hub 当前路由优先于 memory、raw session 和旧 archive 入口。",
        "Git remote key 是跨机器长期路由键；本机源码路径只允许出现在未纳管 local/workspaces.json。",
        "raw session、raw log、core、binary 不复制进正文；只写摘要、证据引用和 registry item。",
        "旧工程归档和旧 Codex archive 路径只作 retired provenance，不作为新增入口。",
    ],
}

if args.json:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
else:
    route = payload.get("route") or {}
    repo = payload.get("repo_route") or {}
    print(f"query: {args.query}")
    print(f"task_type: {args.task_type}")
    if repo:
        print(f"repo: {repo.get('repo_id')} ({repo.get('remote_key')})")
    else:
        print("repo: unresolved")
    if route:
        print(f"project: {route.get('project_id')} ({route.get('name')})")
        print(f"hub_entry: {route.get('hub_entry')}")
        print(f"archive_path: {route.get('archive_path')}")
    else:
        print("project: unresolved")
    print("ranked_items:")
    for item in payload["ranked_items"]:
        print(f"- {item['id']} [{item['kind']}] {item['path']}")
    print(f"candidate_required: {payload['candidate_recommendation']['required']}")

sys.exit(0)
PY
