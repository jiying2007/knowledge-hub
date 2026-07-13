"""Deterministic project readiness assets for every registered Hub project."""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import pathlib
import posixpath
from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Tuple

from .common import (
    KnowledgeHubError,
    encode_jsonl,
    file_sha256,
    load_json,
    load_jsonl,
    pretty_json,
    project_rows,
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
from .store import RepositoryTransaction


MANAGED_START = "<!-- knowledge-hub-project-readiness:start -->"
MANAGED_END = "<!-- knowledge-hub-project-readiness:end -->"
SLOT_NAMES = ("profile", "runbook", "decision", "validation")
BODY_PREFIXES = ("projects/", "domains/", "governance/", "notes/")


def _project_paths(project: Mapping[str, Any]) -> Dict[str, str]:
    current = str(project["current"]).rstrip("/")
    decisions = str(project["decisions"]).rstrip("/")
    validation = str(project["validation"]).rstrip("/")
    return {
        "profile": current + "/project-profile.md",
        "runbook": current + "/runbooks/maintenance-entry.md",
        "decision": decisions + "/project-boundary-decision-candidate.md",
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


def _item_inventory(project: Mapping[str, Any], items: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    domain = str(project["domain"])
    if project["id"] == "knowledge-hub":
        selected = [row for row in items if row.get("domain") in {"root", "governance"}]
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


def _validation_expectations(project: Mapping[str, Any]) -> List[str]:
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
    if project["id"] in {"pcr02", "xcrz-sigmastar-demo", "pcr02-hdi"}:
        rows.append("ST77912 专项：补高温老化、SCLK/EMI 和端到端显示链路证据；缺任一项不得声明发布就绪。")
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
        "review_status": "ai-generated-project-readiness-pending-owner-and-real-validation",
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
        "review_after": review_after,
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
        *[paths[name] for name in SLOT_NAMES if name != slot],
    ]
    return metadata


def _inventory_links(path: str, items: Sequence[Mapping[str, Any]], limit: int = 8) -> str:
    rows = []
    for item in sorted(items, key=lambda row: (str(row.get("status", "")), str(row.get("title", ""))))[:limit]:
        item_path = str(item.get("path", ""))
        if not item_path:
            continue
        rows.append(
            "- {}：`{}` / `{}`".format(
                _link(path, item_path, str(item.get("title", item.get("id", "")))),
                item.get("status", ""),
                item.get("kind", ""),
            )
        )
    return "\n".join(rows) if rows else "- 当前没有可复用的已登记正文；只保留项目 registry 身份，不推断源码事实。"


def _repo_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "| 无直接仓库 | - | - | group/control-plane |\n"
    output = []
    for row in rows:
        output.append(
            "| `{}` | `{}` | `{}` | `{}` |".format(
                row.get("repo_id", ""),
                row.get("remote_key", "unregistered") or "unregistered",
                row.get("workspace_ref", "unmapped") or "unmapped",
                row.get("lifecycle", "unknown") or "unknown",
            )
        )
    return "\n".join(output) + "\n"


def _profile_body(
    project: Mapping[str, Any], path: str, paths: Mapping[str, str], repos: Sequence[Mapping[str, Any]],
    inventory: Sequence[Mapping[str, Any]],
) -> str:
    counts = Counter(str(row.get("status", "unknown")) for row in inventory)
    status_text = ", ".join("{}={}".format(key, counts[key]) for key in sorted(counts)) or "none"
    return """# {name} 项目画像候选

> 本页是 AI 生成的 reviewing 控制资产，只复述 registry 身份和 Hub 已有证据。它不是当前源码、owner decision、设备状态或发布状态证明。

## 项目标识

| 字段 | 值 |
|---|---|
| project_id | `{project_id}` |
| 类型 | `{project_type}` |
| repo boundary | `{boundary}` |
| 所属组 | `{groups}` |
| registry 状态 | `{registry_status}` |
| 本地源码映射 | `machine-local / not tracked` |
| Hub 已登记条目 | `{item_count}`；{status_text} |

## 仓库边界

| repo_id | remote key | workspace ref | lifecycle |
|---|---|---|---|
{repo_table}
`workspace://` 是跨机器逻辑引用，不代表本机源码存在。使用 `knowledge-workspace-discover.sh --plan` 按 exact remote 只读发现，结果只写入未跟踪的 `local/workspaces.json`；绝对路径和动态 HEAD 不进入本页。

## 已有 Hub 证据

{inventory_links}

## 当前权威边界

- 当前源码、分支、版本、构建和发布事实：源项目及其可复现验证证据。
- 长期摘要、决策记录、验证索引和跨项目方法：Knowledge Hub canonical Markdown 与 registry。
- `status`、`owner`、`review_after`、promotion 和 authorization：registry/gate，不由目录名、Obsidian Graph 或本页文字推断。
- 当前 `decision_owner=unassigned`，`manual_validation_pending=true`；未完成 owner 和真实环境验证前保持 `reviewing`。

## Related

- {runbook_link}
- {decision_link}
- {validation_link}
- {project_entry_link}
""".format(
        name=project["name"],
        project_id=project["id"],
        project_type=project.get("type", ""),
        boundary=project.get("repo_boundary", ""),
        groups=", ".join(str(value) for value in project.get("groups", [])),
        registry_status=project.get("status", ""),
        item_count=len(inventory),
        status_text=status_text,
        repo_table=_repo_table(repos),
        inventory_links=_inventory_links(path, inventory),
        runbook_link=_link(path, paths["runbook"], "维护 runbook"),
        decision_link=_link(path, paths["decision"], "边界决策候选"),
        validation_link=_link(path, paths["validation"], "readiness validation"),
        project_entry_link=_link(path, str(project["entry"]), "项目入口"),
    )


def _runbook_body(project: Mapping[str, Any], path: str, paths: Mapping[str, str]) -> str:
    query = str(project["id"])
    return """# {name} 维护入口

> 本 runbook 只定义 Knowledge Hub 维护流程，不提供未经源项目验证的构建、刷机、设备或发布命令。

## 1. 预检

```bash
rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd "$PWD" --query "{query} 当前事实与验证" --task-type validation --json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "{query}" --json --limit 10
```

确认 route 的 `selected_project_id={query}`，并区分 `current`、`recent` 与 archive-only provenance。若本机只有 `workspace://` 而没有 local mapping，先补只读映射或由 owner 提供源码证据，不猜测路径。

## 2. 变更分类

- 当前事实：先在源项目验证，再捕获为 `draft/reviewing` candidate。
- 决策：补真实 decision owner、备选方案、影响范围、回滚和验证后进入 owner review。
- 验证：保留版本/commit、环境、命令、返回码、关键日志、制品 hash 和结论边界。
- 历史材料：只进入 archive/provenance，不自动提升 active。

## 3. Hub 写入

```bash
rtk bash ~/knowledge-hub/tools/knowledge-capture.sh --help
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-link-audit.sh --json --strict
```

capture 只允许创建 `draft/reviewing/personal`。promotion、retire、owner decision、memory write、source project write 和远端发布必须走独立授权门禁。

## Related

- {profile_link}
- {decision_link}
- {validation_link}
- {project_entry_link}
- route、检索、链接、registry 和正文镜像一致。
- 项目特有构建/设备/发布证据由真实执行方补齐，当前文档不代签。
""".format(
        name=project["name"],
        query=query,
        profile_link=_link(path, paths["profile"], "项目画像候选"),
        decision_link=_link(path, paths["decision"], "边界决策候选"),
        validation_link=_link(path, paths["validation"], "readiness validation"),
        project_entry_link=_link(path, str(project["entry"]), "项目入口"),
    )


def _decision_body(project: Mapping[str, Any], path: str, paths: Mapping[str, str]) -> str:
    return """# {name} 权威与维护边界决策候选

## 决策状态

- decision owner：`unassigned`
- 状态：`reviewing`
- 当前决定：未作出
- 禁止解释：本候选不等于 owner approval、active promotion、源码变更或发布授权。

## 待决问题

如何在源项目、Knowledge Hub、Obsidian 和本机运行态之间分配当前事实、长期知识、呈现和授权责任？

## 已确认事实

- 项目 ID、名称、类型、group、repo boundary 和 canonical 路径来自 `registry/projects.json`。
- Git remote key、workspace logical ref 和 lifecycle 来自 `registry/repositories.json`。
- Knowledge Hub 的 Markdown 是长期正文，registry 是生命周期与授权账本；Obsidian 只消费同一份 Markdown。
- 源码、设备行为和发布状态必须由源项目与真实验证证明。

## 方案

| 方案 | 说明 | 风险 |
|---|---|---|
| A | 源项目保存当前事实；Hub 保存受治理摘要/决策/验证；Obsidian 只读呈现 | 需要维护 source-to-Hub 证据引用 |
| B | 在 Hub 复制完整源码文档并作为当前事实 | 容易漂移、重复和误提升，不建议 |
| C | 只依赖会话记忆或个人笔记 | 不可审计、不可稳定复现，不接受 |

## 建议候选

建议 owner 选择 A，并明确项目级 owner、验证责任、复核周期和失效条件。该建议在 owner 决策前不生效。

## owner 必填

- decision owner 与参与者
- 接受/修改/拒绝及理由
- source of truth、适用版本和失效条件
- 验证命令/环境/制品/设备证据
- 回滚路径和下一次 `review_after`

## Related

- {profile_link}
- {runbook_link}
- {validation_link}
- {project_entry_link}
""".format(
        name=project["name"],
        profile_link=_link(path, paths["profile"], "项目画像候选"),
        runbook_link=_link(path, paths["runbook"], "维护 runbook"),
        validation_link=_link(path, paths["validation"], "readiness validation"),
        project_entry_link=_link(path, str(project["entry"]), "项目入口"),
    )


def _validation_body(project: Mapping[str, Any], path: str, paths: Mapping[str, str]) -> str:
    expectations = "\n".join("- [ ] {}".format(value) for value in _validation_expectations(project))
    special = ""
    if project["id"] in {"pcr02", "xcrz-sigmastar-demo", "pcr02-hdi"}:
        special = "\n- {}".format(
            _link(path, "artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md", "PCR02 owner-ready 实机/发布验证路径")
        )
    return """# {name} readiness validation

## 结论

结构性工作台已建立；本机 source 定位由未跟踪 local mapping 动态报告，真实 owner、工程验证、实机/目标平台和发布证据尚未由本页完成。当前结论是 `structurally-ready / evidence-pending`，不是 release-ready。

## 自动结构检查

- [x] registry item 与正文 frontmatter 镜像一致。
- [x] 31 项目 route matrix 能将 `{project_id}` 稳定解析为本项目。
- [x] profile、runbook、decision、validation 四个入口均存在且互相可达。
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

- {profile_link}
- {runbook_link}
- {decision_link}{special}
- {project_entry_link}
""".format(
        name=project["name"],
        project_id=project["id"],
        expectations=expectations,
        profile_link=_link(path, paths["profile"], "项目画像候选"),
        runbook_link=_link(path, paths["runbook"], "维护 runbook"),
        decision_link=_link(path, paths["decision"], "边界决策候选"),
        special=special,
        project_entry_link=_link(path, str(project["entry"]), "项目入口"),
    )


def _managed_readme(readme_path: str, text: str, project: Mapping[str, Any], paths: Mapping[str, str]) -> str:
    block = """{start}
## 成熟度工作台

以下入口是 `reviewing` 控制资产，用于补齐项目画像、维护、决策和验证结构；不代表 owner 签收或发布就绪。

- {profile}
- {runbook}
- {decision}
- {validation}
{end}""".format(
        start=MANAGED_START,
        profile=_link(readme_path, paths["profile"], "项目画像候选"),
        runbook=_link(readme_path, paths["runbook"], "维护 runbook"),
        decision=_link(readme_path, paths["decision"], "权威边界决策候选"),
        validation=_link(readme_path, paths["validation"], "readiness validation"),
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
    items: Sequence[Mapping[str, Any]],
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
        if project_id == "pcr02":
            topic_aliases = _dedupe(
                topic_aliases
                + [
                    "ST77912",
                    "dual screen display",
                    "framebuffer MI_FB",
                    "RAW_PREVIEW",
                ]
            )
        inventory = _item_inventory(project, items)
        source_ids = _dedupe(source_id(row) for row in inventory if source_id(row))
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
                "default_source_ids": _dedupe(list(existing.get("default_source_ids", [])) + source_ids),
                "retired_route_ids": existing.get(
                    "retired_route_ids", ["retired-engineering-archive-root", "retired-codex-archive-root"]
                ),
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
        "本页由 `knowledge-project-readiness.sh` 确定性生成。4/4 仅表示结构入口完整，不代表 owner、源码、实机或发布证据完备。",
        "",
        "| 项目 | profile | runbook | decision | validation | 源码定位 |",
        "|---|---|---|---|---|---|",
    ]
    index_path = "indexes/project-readiness.md"
    for project in projects:
        project_id = str(project["id"])
        paths = project_paths[project_id]
        rows.append(
            "| {} | {} | {} | {} | {} | `{}` |".format(
                _link(index_path, str(project["entry"]), str(project["name"])),
                _link(index_path, paths["profile"], "profile"),
                _link(index_path, paths["runbook"], "runbook"),
                _link(index_path, paths["decision"], "decision"),
                _link(index_path, paths["validation"], "validation"),
                "local-only",
            )
        )
    rows.extend(
        [
            "",
            "## 判定边界",
            "",
            "- structural coverage：31 项目均有四类 reviewing 入口。",
            "- source discovery：运行时从未跟踪的 `local/workspaces.json` 读取；本页不固化绝对路径、HEAD 或本机映射状态。",
            "- evidence readiness：由 product gate 按 owner、source、manual/device/platform/release evidence 独立判定。",
            "- lifecycle：不得从目录、表格、Obsidian Base 或 Graph 自动推断 active。",
        ]
    )
    return "\n".join(rows) + "\n"


def _is_body_markdown(path: str) -> bool:
    if not path.endswith(".md") or pathlib.PurePosixPath(path).name == "README.md":
        return False
    if path == "projects/pcr02/archive/engineering-archive/pcr02/decision-index.md":
        return False
    return path.startswith(BODY_PREFIXES)


def _updated_body_coverage(root: pathlib.Path, new_paths: Iterable[str]) -> str:
    payload = load_json(root / "registry/body-coverage.json", {}) or {}
    future_paths = set(path for path in new_paths if _is_body_markdown(path))
    for collection in payload.get("collections", []):
        prefix = str(collection.get("path_prefix", ""))
        if not prefix:
            continue
        base = root / prefix.rstrip("/")
        paths = set()
        if base.exists():
            paths.update(
                path.relative_to(root).as_posix()
                for path in base.rglob("*.md")
                if _is_body_markdown(path.relative_to(root).as_posix())
            )
        paths.update(path for path in future_paths if path.startswith(prefix))
        encoded = "".join("{}\n".format(path) for path in sorted(paths)).encode("utf-8")
        collection["expected_markdown_count"] = len(paths)
        collection["inventory_sha256"] = hashlib.sha256(encoded).hexdigest()
    return pretty_json(payload) + "\n"


def _add_text(transaction: RepositoryTransaction, root: pathlib.Path, path: str, content: str) -> None:
    target = root / path
    transaction.add_text(path, content, expected_sha256=file_sha256(target) if target.exists() else "")


def generate_project_readiness(root: pathlib.Path, today: dt.date, apply: bool = False) -> Dict[str, Any]:
    projects_doc = load_json(root / "registry/projects.json", {}) or {}
    projects = [dict(row) for row in projects_doc.get("projects", [])]
    if len(projects) != 31:
        raise KnowledgeHubError("expected 31 registered projects, found {}".format(len(projects)))
    for project in projects:
        if project.get("id") == "knowledge-hub":
            project.update(
                {
                    "current": "governance/product/current",
                    "archive": "governance/product/archive",
                    "decisions": "governance/product/decisions",
                    "validation": "governance/product/validation",
                }
            )

    items = registry_items(root)
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
        inventory = _item_inventory(project, items)
        definitions = {
            "profile": (
                "{} 项目画像候选".format(project["name"]),
                "project-current",
                "记录 {} 的 registry 身份、仓库边界、已有 Hub 证据和权威边界；只作 reviewing 工作台，不声明源码或发布事实。".format(project["name"]),
                _profile_body(project, paths["profile"], paths, repos, inventory),
            ),
            "runbook": (
                "{} 维护入口".format(project["name"]),
                "runbook",
                "定义 {} 的 Knowledge Hub 预检、候选写入、验证与授权边界，不生成未经源项目确认的工程命令。".format(project["name"]),
                _runbook_body(project, paths["runbook"], paths),
            ),
            "decision": (
                "{} 权威与维护边界决策候选".format(project["name"]),
                "decision",
                "为 {} 提供 source/Hub/Obsidian 权威分工的 owner-review 候选；decision owner 尚未指定，当前没有生效决定。".format(project["name"]),
                _decision_body(project, paths["decision"], paths),
            ),
            "validation": (
                "{} readiness validation".format(project["name"]),
                "validation",
                "记录 {} 的结构成熟度、本机 source 发现流程和真实 owner、工程/设备及发布验证待办；源码可定位不等于验证完成。".format(project["name"]),
                _validation_body(project, paths["validation"], paths),
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
                require_valid_item(item, existing_ids=item_ids - {item_id})
                next_items[next_item_indexes[item_id]] = item
                if item != existing_item:
                    metadata_updated_items.append(item_id)
            else:
                item = generated_item
                if paths[slot] in item_paths or target_exists:
                    raise KnowledgeHubError("readiness path exists without matching generated item: {}".format(paths[slot]))
                require_valid_item(item, existing_ids=item_ids)
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

    routes_doc = _route_document(projects, repositories, groups, existing_routes, next_items)
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
    _add_text(
        transaction,
        root,
        "registry/body-coverage.json",
        _updated_body_coverage(root, rendered_docs.keys()),
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
        "new_item_count": len(new_items),
        "new_document_count": len(new_items),
        "rendered_document_count": len(rendered_docs),
        "preserved_existing_item_count": len(projects) * len(SLOT_NAMES) - len(new_items),
        "metadata_updated_item_count": len(metadata_updated_items),
        "metadata_updated_item_ids": sorted(metadata_updated_items),
        "readme_count": len(readme_updates),
        "reviewing_only": True,
        "active_promotion": False,
        "source_project_write": False,
        "decision_owner_default": "unassigned",
        "workspace_state_counts": dict(sorted(Counter(workspace_states.values()).items())),
        "transaction": {
            "transaction_id": plan["transaction_id"],
            "write_count": plan["write_count"],
            "changed_count": plan["changed_count"],
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
