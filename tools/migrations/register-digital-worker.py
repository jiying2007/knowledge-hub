#!/usr/bin/env python3
"""One-shot, idempotent migration for the digital-worker governed project route.

This file is intentionally temporary. It updates the three canonical registry
files in one checkout, validates cross references, and creates only a project
navigation README. Source-of-truth facts remain in the digital-worker source
repository.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PROJECT = {
    "id": "digital-worker",
    "name": "Digital Worker",
    "type": "git-repository",
    "domain": "projects/digital-worker",
    "entry": "projects/digital-worker/README.md",
    "current": "projects/digital-worker/current",
    "archive": "projects/digital-worker/archive",
    "decisions": "projects/digital-worker/decisions",
    "validation": "projects/digital-worker/validation",
    "groups": ["agent-tools"],
    "repo_boundary": "control-plane",
    "status": "registered",
    "evidence_profile": "software-tool",
}

REPOSITORY = {
    "repo_id": "digital-worker",
    "project_id": "digital-worker",
    "remote_key": "jiying2007/digital-worker",
    "remote_kind": "github",
    "workspace_ref": "workspace://digital-worker",
    "groups": ["agent-tools"],
    "aliases": ["digital-worker", "digital worker"],
    "lifecycle": "first-party",
    "status": "registered",
}

ROUTE = {
    "project_id": "digital-worker",
    "name": "Digital Worker",
    "type": "project",
    "route_scope": "project",
    "group_id": "agent-tools",
    "aliases": ["digital-worker", "Digital Worker", "digital_worker"],
    "topic_aliases": [],
    "repo_refs": ["digital-worker"],
    "workspace_refs": ["workspace://digital-worker"],
    "hub_entry": "projects/digital-worker/README.md",
    "current_path": "projects/digital-worker/current",
    "archive_path": "projects/digital-worker/archive",
    "decisions_path": "projects/digital-worker/decisions",
    "validation_path": "projects/digital-worker/validation",
    "domain_refs": ["projects/digital-worker"],
    "default_source_ids": [],
    "route_key_policy": "git-remote-first",
}

README = """# Digital Worker

- 项目 ID：`digital-worker`
- 所属组：`agent-tools`
- 事实边界：以 `registry/repositories.json` 中 `repo_id=digital-worker` 的 Git remote key `jiying2007/digital-worker` 为准。
- 路由策略：`git-remote-first`
- 当前知识：`projects/digital-worker/current/`
- 决策：`projects/digital-worker/decisions/`
- 验证：`projects/digital-worker/validation/`
- 归档：`projects/digital-worker/archive/`

该入口只提供 Knowledge Hub 的受治理项目导航与检索路由。`digital-worker` 的架构、Contract、Gate、Pilot 与运行证据继续以源仓为事实权威；Hub 不维护平行 canonical copy。
"""


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write(path: str, value: dict) -> None:
    (ROOT / path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def insert_or_verify(rows: list[dict], key: str, expected: dict, after: str) -> None:
    matches = [row for row in rows if row.get(key) == expected[key]]
    if matches:
        if len(matches) != 1 or matches[0] != expected:
            raise SystemExit(f"existing {expected[key]} row does not match migration contract")
        return
    for index, row in enumerate(rows):
        if row.get(key) == after:
            rows.insert(index + 1, expected)
            return
    raise SystemExit(f"anchor row not found: {after}")


def unique(rows: list[dict], key: str, label: str) -> None:
    values = [row.get(key) for row in rows if row.get(key)]
    if len(values) != len(set(values)):
        raise SystemExit(f"duplicate {label} in canonical registry")


def main() -> None:
    projects = load("registry/projects.json")
    repositories = load("registry/repositories.json")
    routes = load("registry/project-routes.json")

    insert_or_verify(projects["projects"], "id", PROJECT, "agent-dev-kit")
    insert_or_verify(repositories["repositories"], "repo_id", REPOSITORY, "agent-dev-kit")
    insert_or_verify(routes["routes"], "project_id", ROUTE, "agent-dev-kit")

    unique(projects["projects"], "id", "project id")
    unique(repositories["repositories"], "repo_id", "repository id")
    unique(repositories["repositories"], "remote_key", "repository remote key")
    unique(routes["routes"], "project_id", "route project id")

    project_ids = {row["id"] for row in projects["projects"]}
    repo_by_id = {row["repo_id"]: row for row in repositories["repositories"]}
    if REPOSITORY["project_id"] not in project_ids:
        raise SystemExit("digital-worker repository has no canonical project")
    if repo_by_id["digital-worker"]["remote_key"] != "jiying2007/digital-worker":
        raise SystemExit("digital-worker remote identity mismatch")
    if ROUTE["repo_refs"] != ["digital-worker"] or ROUTE["route_key_policy"] != "git-remote-first":
        raise SystemExit("digital-worker route is not remote-first")
    if any(ref not in repo_by_id for ref in ROUTE["repo_refs"]):
        raise SystemExit("digital-worker route references an unknown repository")

    write("registry/projects.json", projects)
    write("registry/repositories.json", repositories)
    write("registry/project-routes.json", routes)

    readme = ROOT / "projects" / "digital-worker" / "README.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    if readme.exists() and readme.read_text(encoding="utf-8") != README:
        raise SystemExit("existing digital-worker README does not match migration contract")
    readme.write_text(README, encoding="utf-8")

    print("digital-worker canonical route migration: PASS")


if __name__ == "__main__":
    main()
