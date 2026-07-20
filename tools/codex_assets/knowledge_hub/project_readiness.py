"""Deterministic project readiness assets for every registered Hub project."""

from __future__ import annotations

import datetime as dt
import pathlib
import posixpath
from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set

from .common import (
    KnowledgeHubError,
    encode_jsonl,
    file_sha256,
    load_json,
    load_jsonl,
    pretty_json,
    registry_items,
    render_markdown,
    repository_rows,
    route_rows,
    source_id,
    utc_timestamp,
)
from .evidence import merge_evidence_contract, new_evidence_contract, project_evidence_profile
from .indexing import CORE_INDEXES, update_core_indexes, update_project_index, update_topic_index
from .model import frontmatter_mirror, require_valid_item
from .obsidian_view import stage_obsidian_views
from .product_policy import load_product_policy, readiness_extensions_by_project
from .store import RepositoryTransaction


MANAGED_START = "<!-- knowledge-hub-project-readiness:start -->"
MANAGED_END = "<!-- knowledge-hub-project-readiness:end -->"
SLOT_NAMES = ("validation",)
RETIRED_PROJECTION_SLOTS = frozenset({"profile", "runbook", "decision"})


def _project_paths(project: Mapping[str, Any]) -> Dict[str, str]:
    validation = str(project["validation"]).rstrip("/")
    return {
        "validation": validation + "/project-readiness.md",
    }


def _link(from_path: str, to_path: str, label: str) -> str:
    base = posixpath.dirname(from_path) or "."
    relative = posixpath.relpath(to_path, base)
    escaped = label.replace("[", "\\[").replace("]", "\\]")
    return "[{}]({})".format(escaped, relative)


def _dedupe(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen: Set[str] = set()
    for value in values:
        text = str(value).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return result


def _repo_rows_for_project(
    project: Mapping[str, Any], repositories: Sequence[Mapping[str, Any]]
) -> List[Dict[str, Any]]:
    project_id = str(project["id"])
    groups = set(str(value) for value in project.get("groups", []))
    if project.get("type") == "product-group":
        return [
            dict(row)
            for row in repositories
            if row.get("project_id") and groups.intersection(str(value) for value in row.get("groups", []))
        ]
    return [dict(row) for row in repositories if row.get("project_id") == project_id]


def _workspace_state(rows: Sequence[Mapping[str, Any]], local_workspaces: Mapping[str, Mapping[str, Any]]) -> str:
    mapped = 0
    available = 0
    for row in rows:
        workspace_ref = str(row.get("workspace_ref", ""))
        if workspace_ref.startswith("~/"):
            mapped += 1
            if pathlib.Path(workspace_ref).expanduser().exists():
                available += 1
        elif workspace_ref in local_workspaces:
            mapped += 1
            candidate = str(local_workspaces[workspace_ref].get("path", ""))
            if candidate and pathlib.Path(candidate).expanduser().exists():
                available += 1
    if not rows:
        return "not-applicable-group-or-control-plane"
    if available == len(rows):
        return "all-mapped-and-present"
    if available:
        return "partially-mapped-and-present"
    if mapped:
        return "mapped-but-not-present"
    return "local-workspace-mapping-pending"


def _item_inventory(
    project: Mapping[str, Any], items: Sequence[Mapping[str, Any]]
) -> List[Dict[str, Any]]:
    """Return registered project knowledge used to derive stable route bindings."""
    domain = str(project["domain"])
    if project["id"] == "knowledge-hub":
        selected = [
            row for row in items if row.get("domain") in {"root", "governance"}
        ]
    else:
        selected = [row for row in items if row.get("domain") == domain]
    return [dict(row) for row in selected]


def _item_domain(project: Mapping[str, Any]) -> str:
    if project["id"] == "knowledge-hub":
        return "governance"
    domain = str(project["domain"])
    if domain == "domains/codex":
        return "codex"
    return domain


def _validation_expectations(
    project: Mapping[str, Any], extension: Mapping[str, Any]
) -> List[str]:
    boundary = str(project.get("repo_boundary", ""))
    project_type = str(project.get("type", ""))
    rows = [
        "Hub 结构验证：registry、route、正文镜像、链接和检索矩阵通过。",
        "来源验证：确认 Git remote key、当前分支/版本和源码事实，Hub 不代替源仓事实。",
        "责任验证：由真实 decision owner 明确接受、修改或拒绝边界候选。",
    ]
    if boundary in {"firmware", "module", "application", "primary"}:
        rows.extend(
            [
                "工程验证：在源项目运行适用的构建、单元/集成测试并保留命令、版本和日志摘要。",
                "设备验证：需要硬件行为的结论必须补 HIL/实机、环境条件和可复现实验记录。",
                "发布验证：记录制品身份、版本、回滚路径和端到端验收，不以 Hub 文档替代发布签收。",
            ]
        )
    elif boundary == "tooling":
        rows.extend(
            [
                "工具验证：覆盖 CLI help、错误码、输入边界、制品 hash 和目标平台 smoke test。",
                "发布验证：覆盖可安装/可运行制品、版本信息、回滚和消费者兼容性。",
            ]
        )
    elif boundary == "runtime-assets":
        rows.append("运行态验证：执行声明式 build/doctor/plan/dry-run/apply/check 链路并保留回滚证据。")
    elif boundary == "control-plane" or project_type == "knowledge-control-plane":
        rows.append("控制面验证：执行 check、unit、retrieval、route、link、export 和 restore drill。")
    else:
        rows.append("项目组验证：每个成员仓分别补源码、设备/平台和发布证据，不能用组级结论替代。")
    rows.extend(str(value) for value in extension.get("validation_expectations_zh", []))
    return rows


def _base_item(
    project: Mapping[str, Any],
    slot: str,
    path: str,
    today: dt.date,
    title: str,
    kind: str,
    summary: str,
    evidence_profile: str,
    member_project_ids: Sequence[str] = (),
) -> Dict[str, Any]:
    project_id = str(project["id"])
    review_after = (today + dt.timedelta(days=92)).isoformat()
    item: Dict[str, Any] = {
        "id": "{}-readiness-{}-{}".format(project_id, slot, today.strftime("%Y%m%d")),
        "title": title,
        "kind": kind,
        "domain": _item_domain(project),
        "path": path,
        "project_id": project_id,
        "readiness_slot": slot,
        "evidence_profile": evidence_profile,
        "scope": "project-specific" if str(project["domain"]).startswith("projects/") else "team-general",
        "visibility": "team-internal",
        "status": "reviewing",
        # Per-project readiness bodies are machine-governed evidence contracts.
        # The aggregate index is the human retrieval surface, so these repeated
        # projections must not compete with canonical project knowledge.
        "searchable": project_id == "knowledge-hub" and slot == "validation",
        "owner": "leiwenjun",
        "source": {
            "type": "generated-control-plane",
            "from": "registry/projects.json + registry/repositories.json + existing registry items",
            "fact_scope": "registered-metadata-and-existing-hub-evidence-only",
        },
        "review_after": review_after,
        "validation_refs": [
            path,
            "registry/projects.json",
            "registry/repositories.json",
            "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics",
            "rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of {}".format(
                today.isoformat()
            ),
        ],
        "summary_zh": summary,
        "primary_language": "zh-CN",
        "source_language": "zh-CN",
        "translation_status": "not-required",
        "terminology_status": "pending-review",
        "review_status": "ai-generated-project-readiness-pending-owner-and-real-validation",
        "content_review_status": "pending",
        "evidence_validation_status": "pending",
        "evidence_strength": "generated-readiness-contract-pending-owner-validation",
        "evidence_refs": [
            path,
            "registry/projects.json",
            "registry/repositories.json",
        ],
        "promotion_decision": "none; structural readiness asset only, no active promotion or owner decision",
        "generated_by_ai": True,
        "ai_role": "drafted",
        "ai_model_or_tool": "Codex",
        "ai_generated_at": today.isoformat(),
        "manual_validation_pending": True,
        "decision_owner": "unassigned",
        "tags": [
            project_id,
            "project-readiness",
            slot,
            "ai-generated",
            "owner-review-pending",
            "manual-validation-pending",
            "no-active-promotion",
        ],
        "promotion": "none",
        "created_at": today.isoformat(),
        "updated_at": today.isoformat(),
    }
    if slot == "validation":
        item["evidence_contract"] = new_evidence_contract(
            evidence_profile,
            member_project_ids,
        )
    return item


def _preserve_existing_readiness_item(
    existing: Mapping[str, Any],
    project: Mapping[str, Any],
    slot: str,
    path: str,
    evidence_profile: str,
    member_project_ids: Sequence[str] = (),
) -> Dict[str, Any]:
    item = dict(existing)
    project_id = str(project["id"])
    if item.get("path") != path:
        raise KnowledgeHubError("existing readiness path drift: {}".format(item.get("id", "")))
    if item.get("project_id") not in {None, "", project_id}:
        raise KnowledgeHubError("existing readiness project drift: {}".format(item.get("id", "")))
    if item.get("readiness_slot") not in {None, "", slot}:
        raise KnowledgeHubError("existing readiness slot drift: {}".format(item.get("id", "")))
    if item.get("evidence_profile") not in {None, "", evidence_profile}:
        raise KnowledgeHubError("existing readiness profile drift: {}".format(item.get("id", "")))
    item.setdefault("project_id", project_id)
    item.setdefault("readiness_slot", slot)
    item.setdefault("evidence_profile", evidence_profile)
    item["searchable"] = project_id == "knowledge-hub" and slot == "validation"
    item.setdefault("primary_language", "zh-CN")
    item.setdefault("source_language", "zh-CN")
    item.setdefault("translation_status", "not-required")
    item.setdefault("terminology_status", "pending-review")
    item.setdefault("content_review_status", "pending")
    item.setdefault("evidence_validation_status", "pending")
    item.setdefault(
        "evidence_strength",
        "generated-readiness-contract-pending-owner-validation",
    )
    item.setdefault(
        "evidence_refs",
        [path, "registry/projects.json", "registry/repositories.json"],
    )
    if slot == "validation":
        item["evidence_contract"] = merge_evidence_contract(
            item.get("evidence_contract", {}),
            evidence_profile,
            member_project_ids,
        )
    return item


def _frontmatter(
    item: Mapping[str, Any], project: Mapping[str, Any], slot: str, paths: Mapping[str, str]
) -> Dict[str, Any]:
    metadata = frontmatter_mirror(item)
    metadata["path"] = item["path"]
    metadata["summary_zh"] = item["summary_zh"]
    project_id = str(project["id"])
    metadata["project_id"] = project_id
    metadata["readiness_slot"] = slot
    metadata["aliases"] = ["{} {}".format(project_id, slot), "{}-{}".format(project_id, slot)]
    metadata["related"] = [
        str(project["entry"]),
        "indexes/project-readiness.md",
    ]
    return metadata




def _validation_body(
    project: Mapping[str, Any],
    path: str,
    paths: Mapping[str, str],
    project_count: int,
    extension: Mapping[str, Any],
) -> str:
    expectations = "\n".join(
        "- [ ] {}".format(value)
        for value in _validation_expectations(project, extension)
    )
    related_extension = "".join(
        "\n- {}".format(
            _link(path, str(row["path"]), str(row["label_zh"]))
        )
        for row in extension.get("related_links", [])
    )
    return """# {name} readiness validation

## 结论

结构性工作台已建立；本机 source 定位由未跟踪 local mapping 动态报告，真实 owner、工程验证、实机/目标平台和发布证据尚未由本页完成。当前结论是 `structurally-ready / evidence-pending`，不是 release-ready。

## 自动结构检查

- [x] registry item 与正文 frontmatter 镜像一致。
- [x] {project_count} 项目 route matrix 能将 `{project_id}` 稳定解析为本项目。
- [x] 单一 evidence contract 已登记，统一 dashboard 可从项目入口访问。
- [x] search known-answer 与 link audit 通过。
- [ ] 本机 source 定位：运行 `knowledge-workspace-discover.sh --plan --json`，由 project gate 动态读取；结果不得复制到 tracked Markdown。

## 人工/真实环境门禁

{expectations}

## 证据记录模板

| 字段 | 待填写 |
|---|---|
| decision owner | `unassigned` |
| source repo / commit / version | pending |
| 执行环境与设备 | pending |
| 命令与返回码 | pending |
| 日志/截图/制品 hash | pending |
| 回滚验证 | pending |
| 结论和适用边界 | pending |

## Related

- {dashboard_link}{related_extension}
- {project_entry_link}
""".format(
        name=project["name"],
        project_id=project["id"],
        project_count=project_count,
        expectations=expectations,
        dashboard_link=_link(path, "indexes/project-readiness.md", "统一 readiness dashboard"),
        related_extension=related_extension,
        project_entry_link=_link(path, str(project["entry"]), "项目入口"),
    )


def _managed_readme(readme_path: str, text: str, project: Mapping[str, Any], paths: Mapping[str, str]) -> str:
    block = """{start}
## 成熟度工作台

以下入口是单一 `reviewing` evidence contract 与统一 dashboard；不代表 owner 签收或发布就绪。

- {validation}
- {dashboard}
{end}""".format(
        start=MANAGED_START,
        validation=_link(readme_path, paths["validation"], "项目 evidence contract"),
        dashboard=_link(readme_path, "indexes/project-readiness.md", "统一 readiness dashboard"),
        end=MANAGED_END,
    )
    if MANAGED_START in text and MANAGED_END in text:
        before, remainder = text.split(MANAGED_START, 1)
        _, after = remainder.split(MANAGED_END, 1)
        return before.rstrip() + "\n\n" + block + after.rstrip() + "\n"
    return text.rstrip() + "\n\n" + block + "\n"


def _route_document(
    projects: Sequence[Mapping[str, Any]], repositories: Sequence[Mapping[str, Any]],
    groups: Sequence[Mapping[str, Any]], existing_routes: Sequence[Mapping[str, Any]],
    items: Sequence[Mapping[str, Any]], current_source_ids: Set[str],
) -> Dict[str, Any]:
    existing_by_project = {str(row.get("project_id")): row for row in existing_routes if row.get("project_id")}
    group_by_id = {str(row.get("id")): row for row in groups if row.get("id")}
    routes: List[Dict[str, Any]] = []
    for project in projects:
        project_id = str(project["id"])
        groups_for_project = [str(value) for value in project.get("groups", [])]
        group_id = groups_for_project[0] if groups_for_project else project_id
        existing = existing_by_project.get(project_id, {})
        repos = _repo_rows_for_project(project, repositories)
        repo_refs = _dedupe(str(row.get("repo_id", "")) for row in repos)
        workspace_refs = _dedupe(str(row.get("workspace_ref", "")) for row in repos)
        if not repo_refs or not workspace_refs:
            raise KnowledgeHubError("project route lacks repository/workspace references: {}".format(project_id))
        aliases = _dedupe(
            list(existing.get("aliases", []))
            + [project_id, str(project.get("name", "")), project_id.replace("-", "_")]
        )
        topic_aliases = _dedupe(existing.get("topic_aliases", []))
        inventory = _item_inventory(project, items)
        source_ids = _dedupe(source_id(row) for row in inventory if source_id(row))
        configured_source_ids = _dedupe(
            list(existing["default_source_ids"])
            if "default_source_ids" in existing
            else source_ids
        )
        is_group_route = project.get("type") == "product-group" or existing.get("type") == "project-group"
        if is_group_route:
            members = [str(value) for value in group_by_id.get(group_id, {}).get("member_project_ids", [])]
            domain_refs = _dedupe(
                str(row.get("domain", ""))
                for row in projects
                if str(row.get("id", "")) in set(members + [project_id])
            )
        elif project_id == "knowledge-hub":
            domain_refs = ["governance", "root"]
        elif project.get("domain") == "domains/codex":
            domain_refs = ["codex"]
        else:
            domain_refs = [str(project.get("domain", "projects/{}".format(project_id)))]
        routes.append(
            {
                "project_id": project_id,
                "name": project.get("name", project_id),
                "type": existing.get("type", "project-group" if is_group_route else "project"),
                "route_scope": "group" if is_group_route else "project",
                "group_id": group_id,
                "aliases": aliases,
                "topic_aliases": topic_aliases,
                "repo_refs": repo_refs,
                "workspace_refs": workspace_refs,
                "hub_entry": project["entry"],
                "current_path": project["current"],
                "archive_path": project["archive"],
                "decisions_path": project["decisions"],
                "validation_path": project["validation"],
                "domain_refs": domain_refs,
                "default_source_ids": [
                    value for value in configured_source_ids if value in current_source_ids
                ],
                "route_key_policy": existing.get(
                    "route_key_policy", "control-plane-query-aware" if project_id == "knowledge-hub" else "git-remote-first"
                ),
            }
        )
    return {"schema_version": 2, "routes": routes}


def _readiness_index(projects: Sequence[Mapping[str, Any]], project_paths: Mapping[str, Mapping[str, str]]) -> str:
    rows = [
        "# 项目成熟度工作台",
        "",
        "本页由 `knowledge-project-readiness.sh` 确定性生成。每项目只保留一份 evidence contract；结构存在不代表 owner、源码、实机或发布证据完备。",
        "",
        "| 项目 | evidence contract | 源码定位 |",
        "|---|---|---|",
    ]
    index_path = "indexes/project-readiness.md"
    for project in projects:
        project_id = str(project["id"])
        paths = project_paths[project_id]
        rows.append(
            "| {} | {} | `{}` |".format(
                _link(index_path, str(project["entry"]), str(project["name"])),
                _link(index_path, paths["validation"], "evidence contract"),
                "local-only",
            )
        )
    rows.extend(
        [
            "",
            "## 判定边界",
            "",
            "- structural coverage：{} 项目均有一份 reviewing evidence contract；group 元数据不重复计入项目数。".format(len(projects)),
            "- source discovery：运行时从未跟踪的 `local/workspaces.json` 读取；本页不固化绝对路径、HEAD 或本机映射状态。",
            "- evidence readiness：由 product gate 按 owner、source、manual/device/platform/release evidence 独立判定。",
            "- lifecycle：不得从目录、表格、Obsidian Base 或 Graph 自动推断 active。",
        ]
    )
    return "\n".join(rows) + "\n"


def _add_text(transaction: RepositoryTransaction, root: pathlib.Path, path: str, content: str) -> None:
    target = root / path
    transaction.add_text(path, content, expected_sha256=file_sha256(target) if target.exists() else "")


def generate_project_readiness(root: pathlib.Path, today: dt.date, apply: bool = False) -> Dict[str, Any]:
    projects_doc = load_json(root / "registry/projects.json", {}) or {}
    projects = [dict(row) for row in projects_doc.get("projects", [])]
    if not projects:
        raise KnowledgeHubError("registry/projects.json must contain at least one project")
    project_ids = [str(project.get("id", "")) for project in projects]
    if any(not project_id for project_id in project_ids):
        raise KnowledgeHubError("every registered project must define a non-empty id")
    if len(set(project_ids)) != len(project_ids):
        raise KnowledgeHubError("registry/projects.json contains duplicate project ids")
    product_policy, policy_errors = load_product_policy(root)
    readiness_extensions, extension_errors = readiness_extensions_by_project(
        product_policy, project_ids
    )
    if policy_errors or extension_errors:
        raise KnowledgeHubError(
            "invalid product readiness policy: {}".format(
                "; ".join(policy_errors + extension_errors)
            )
        )

    all_items = registry_items(root)
    retired_projection_items = [
        row
        for row in all_items
        if row.get("readiness_slot") in RETIRED_PROJECTION_SLOTS
        and "project-readiness" in row.get("tags", [])
    ]
    retired_projection_ids = {
        str(row.get("id", "")) for row in retired_projection_items
    }
    items = [
        row for row in all_items if str(row.get("id", "")) not in retired_projection_ids
    ]
    repositories = repository_rows(root)
    groups = list((load_json(root / "registry/project-groups.json", {}) or {}).get("groups", []))
    groups_by_id = {str(row.get("id", "")): row for row in groups if row.get("id")}
    existing_routes = route_rows(root)
    local_rows = list((load_json(root / "local/workspaces.json", {}) or {}).get("workspaces", []))
    local_workspaces = {str(row.get("workspace_ref", "")): row for row in local_rows if row.get("workspace_ref")}
    item_ids = {str(row.get("id")) for row in items}
    item_paths = {str(row.get("path")) for row in items}
    items_by_path = {str(row.get("path")): row for row in items if row.get("path")}
    if len(items_by_path) != len(item_paths):
        raise KnowledgeHubError("registry contains duplicate item paths")
    next_items = list(items)
    next_item_indexes = {str(row.get("id")): index for index, row in enumerate(next_items)}
    project_paths: Dict[str, Dict[str, str]] = {}
    workspace_states: Dict[str, str] = {}
    rendered_docs: Dict[str, str] = {}
    new_items: List[Dict[str, Any]] = []
    metadata_updated_items: List[str] = []
    readme_updates: Dict[str, str] = {}

    for project in projects:
        project_id = str(project["id"])
        readiness_extension = readiness_extensions.get(project_id, {})
        evidence_profile = project_evidence_profile(project)
        project["evidence_profile"] = evidence_profile
        group_ids = [str(value) for value in project.get("groups", [])]
        group = groups_by_id.get(group_ids[0], {}) if group_ids else {}
        member_project_ids = (
            [
                str(value)
                for value in group.get("member_project_ids", [])
                if str(value) != project_id
            ]
            if evidence_profile == "aggregate-group"
            else []
        )
        paths = _project_paths(project)
        project_paths[project_id] = paths
        repos = _repo_rows_for_project(project, repositories)
        workspace_state = _workspace_state(repos, local_workspaces)
        workspace_states[project_id] = workspace_state
        definitions = {
            "validation": (
                "{} readiness validation".format(project["name"]),
                "validation",
                "记录 {} 的结构成熟度、本机 source 发现流程和真实 owner、工程/设备及发布验证待办；源码可定位不等于验证完成。".format(project["name"]),
                _validation_body(
                    project,
                    paths["validation"],
                    paths,
                    len(projects),
                    readiness_extension,
                ),
            ),
        }
        for slot in SLOT_NAMES:
            title, kind, summary, body = definitions[slot]
            generated_item = _base_item(
                project,
                slot,
                paths[slot],
                today,
                title,
                kind,
                summary,
                evidence_profile,
                member_project_ids,
            )
            existing_item = items_by_path.get(paths[slot])
            target_exists = (root / paths[slot]).exists()
            if existing_item:
                if not target_exists:
                    raise KnowledgeHubError(
                        "existing readiness body is missing: {}".format(existing_item.get("id", ""))
                    )
                item = _preserve_existing_readiness_item(
                    existing_item,
                    project,
                    slot,
                    paths[slot],
                    evidence_profile,
                    member_project_ids,
                )
                item_id = str(item["id"])
                require_valid_item(
                    item,
                    existing_ids=item_ids - {item_id},
                    existing_paths=item_paths - {paths[slot]},
                )
                next_items[next_item_indexes[item_id]] = item
                if item != existing_item:
                    metadata_updated_items.append(item_id)
            else:
                item = generated_item
                if paths[slot] in item_paths or target_exists:
                    raise KnowledgeHubError("readiness path exists without matching generated item: {}".format(paths[slot]))
                require_valid_item(
                    item,
                    existing_ids=item_ids,
                    existing_paths=item_paths,
                )
                item_ids.add(item["id"])
                item_paths.add(paths[slot])
                next_item_indexes[item["id"]] = len(next_items)
                next_items.append(item)
                new_items.append(item)
                rendered_docs[paths[slot]] = render_markdown(
                    _frontmatter(item, project, slot, paths),
                    body,
                )

        readme_path = str(project["entry"])
        readme = root / readme_path
        if not readme.exists():
            raise KnowledgeHubError("project entry is missing: {}".format(readme_path))
        readme_updates[readme_path] = _managed_readme(readme_path, readme.read_text(encoding="utf-8"), project, paths)

    core_contents = {path: (root / path).read_text(encoding="utf-8") for path in CORE_INDEXES}
    project_index = (root / "indexes/by-project.md").read_text(encoding="utf-8")
    topic_index = (root / "indexes/by-topic.md").read_text(encoding="utf-8")
    retired_markers = {"`{}`".format(item_id) for item_id in retired_projection_ids}
    if retired_markers:
        def without_retired(text: str) -> str:
            return "\n".join(
                line
                for line in text.splitlines()
                if not any(marker in line for marker in retired_markers)
            ).rstrip() + "\n"

        core_contents = {
            path: without_retired(content)
            for path, content in core_contents.items()
        }
        project_index = without_retired(project_index)
        topic_index = without_retired(topic_index)
    project_names = {str(row["id"]): str(row["name"]) for row in projects}
    for item in new_items:
        core_contents = update_core_indexes(core_contents, item)
        if str(item["domain"]).startswith("projects/"):
            project_id = str(item["domain"]).split("/", 1)[1]
            project_index = update_project_index(project_index, item, project_names.get(project_id, project_id))
        topic_index = update_topic_index(topic_index, item)

    lifecycle_rows = load_jsonl(root / "registry/lifecycle-events.jsonl")
    for item in new_items:
        lifecycle_rows.append(
            {
                "event_id": "project-readiness-{}-{}".format(today.strftime("%Y%m%d"), item["id"]),
                "event_type": "capture",
                "item_id": item["id"],
                "before_status": "missing",
                "after_status": "reviewing",
                "authorization_id": "",
                "executed_by": "knowledge-project-readiness",
                "executed_at": utc_timestamp(),
                "evidence_refs": item["validation_refs"],
            }
        )

    current_source_ids = {
        str(row.get("id", ""))
        for row in (load_json(root / "registry/sources.json", {}) or {}).get("sources", [])
        if row.get("id") and row.get("status") == "registered"
    }
    routes_doc = _route_document(
        projects,
        repositories,
        groups,
        existing_routes,
        next_items,
        current_source_ids,
    )
    readiness_index = _readiness_index(projects, project_paths)
    transaction = RepositoryTransaction(root)
    for path, content in rendered_docs.items():
        _add_text(transaction, root, path, content)
    for path, content in readme_updates.items():
        _add_text(transaction, root, path, content)
    _add_text(transaction, root, "registry/projects.json", pretty_json({"schema_version": 1, "projects": projects}) + "\n")
    _add_text(transaction, root, "registry/project-routes.json", pretty_json(routes_doc) + "\n")
    _add_text(transaction, root, "registry/items.jsonl", encode_jsonl(next_items))
    _add_text(transaction, root, "registry/lifecycle-events.jsonl", encode_jsonl(lifecycle_rows))
    for path, content in core_contents.items():
        _add_text(transaction, root, path, content)
    _add_text(transaction, root, "indexes/by-project.md", project_index)
    _add_text(transaction, root, "indexes/by-topic.md", topic_index)
    _add_text(transaction, root, "indexes/project-readiness.md", readiness_index)
    obsidian_stage = stage_obsidian_views(
        root,
        transaction,
        items=next_items,
        document_overrides={**rendered_docs, **readme_updates},
    )
    if obsidian_stage["missing_files"] or obsidian_stage["content_drifts"]:
        raise KnowledgeHubError(
            "project readiness cannot atomically rebuild Obsidian views: "
            "missing={} drifts={}".format(
                obsidian_stage["missing_files"],
                obsidian_stage["content_drifts"],
            )
        )
    plan = transaction.plan()
    result: Dict[str, Any] = {
        "schema_version": 1,
        "action": "generate-project-readiness",
        "status": "planned" if not apply else "applying",
        "apply_supported": True,
        "project_count": len(projects),
        "route_count": len(routes_doc["routes"]),
        "slot_count": len(projects) * len(SLOT_NAMES),
        "evidence_contract_count": len(projects),
        "retired_projection_item_count": len(retired_projection_items),
        "new_item_count": len(new_items),
        "new_document_count": len(new_items),
        "rendered_document_count": len(rendered_docs),
        "preserved_existing_item_count": len(projects) * len(SLOT_NAMES) - len(new_items),
        "metadata_updated_item_count": len(metadata_updated_items),
        "metadata_updated_item_ids": sorted(metadata_updated_items),
        "readme_count": len(readme_updates),
        "obsidian_managed_document_count": len(obsidian_stage["managed"]),
        "derived_views_transactional": True,
        "reviewing_only": True,
        "active_promotion": False,
        "source_project_write": False,
        "decision_owner_default": "unassigned",
        "workspace_state_counts": dict(sorted(Counter(workspace_states.values()).items())),
        "transaction": {
            "transaction_id": plan["transaction_id"],
            "write_count": plan["write_count"],
            "changed_count": plan["changed_count"],
            "write_paths": [row["path"] for row in plan["writes"]],
        },
    }
    if apply:
        applied = transaction.apply()
        result["status"] = applied.status
        result["transaction"].update(
            {
                "journal": applied.journal,
                "changed_count": len(applied.changed_paths),
                "unchanged_count": len(applied.unchanged_paths),
            }
        )
    return result
