"""Build plugin-free Obsidian views over canonical Knowledge Hub Markdown."""

from __future__ import annotations

import pathlib
import posixpath
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .common import encode_jsonl, file_sha256, load_json, registry_items, render_markdown, split_frontmatter
from .store import RepositoryTransaction


HOME_START = "<!-- knowledge-hub-obsidian-views:start -->"
HOME_END = "<!-- knowledge-hub-obsidian-views:end -->"
CONTENT_FIELDS = ("title", "summary_zh", "tags")
LIFECYCLE_FIELDS = (
    "id",
    "kind",
    "domain",
    "path",
    "scope",
    "visibility",
    "status",
    "owner",
    "review_after",
    "review_status",
    "promotion",
    "manual_validation_pending",
    "decision_owner",
)

BASE_FILES = {
    "indexes/obsidian/active-knowledge.base": """filters:
  and:
    - file.ext == "md"
    - status == "active"
properties:
  file.name:
    displayName: 文档
  owner:
    displayName: Owner
  review_after:
    displayName: 复核日期
  aliases:
    displayName: 别名
  related:
    displayName: 相关材料
views:
  - type: table
    name: Active 长期知识
    order:
      - file.name
      - kind
      - owner
      - review_after
      - aliases
      - related
    sort:
      - property: review_after
        direction: ASC
""",
    "indexes/obsidian/reviewing.base": """filters:
  and:
    - file.ext == "md"
    - status == "reviewing"
properties:
  file.name:
    displayName: 文档
  owner:
    displayName: Hub 维护人
  decision_owner:
    displayName: 决策 owner
  review_after:
    displayName: 复核日期
  manual_validation_pending:
    displayName: 人工验证待办
views:
  - type: table
    name: Reviewing 队列
    order:
      - file.name
      - kind
      - owner
      - decision_owner
      - manual_validation_pending
      - review_after
    sort:
      - property: review_after
        direction: ASC
""",
    "indexes/obsidian/project-readiness.base": """filters:
  and:
    - file.ext == "md"
    - tags.contains("project-readiness")
properties:
  file.name:
    displayName: 文档
  project_id:
    displayName: 项目
  readiness_slot:
    displayName: 能力槽位
  status:
    displayName: 状态
  review_after:
    displayName: 复核日期
  decision_owner:
    displayName: 决策 owner
views:
  - type: table
    name: 项目成熟度入口
    order:
      - file.name
      - project_id
      - readiness_slot
      - kind
      - status
      - review_after
      - decision_owner
    sort:
      - property: project_id
        direction: ASC
      - property: readiness_slot
        direction: ASC
""",
}

RUNTIME_ACCEPTANCE_PATH = "local/obsidian-runtime-acceptance.json"
RUNTIME_REQUIRED_CHECKS = (
    "bases_rendered",
    "properties_visible",
    "backlinks_working",
    "moc_navigation_working",
)


def obsidian_runtime_acceptance(root: pathlib.Path) -> Dict[str, Any]:
    path = root / RUNTIME_ACCEPTANCE_PATH
    if not path.is_file():
        return {
            "status": "not-validated",
            "path": RUNTIME_ACCEPTANCE_PATH,
            "tracked": False,
            "missing_fields": [
                "obsidian_version",
                "validated_at",
                "validated_by",
                *RUNTIME_REQUIRED_CHECKS,
                "screenshot_refs",
            ],
        }
    payload = load_json(path, {}) or {}
    missing = [
        field
        for field in ("obsidian_version", "validated_at", "validated_by")
        if not str(payload.get(field, "")).strip()
    ]
    missing.extend(
        field for field in RUNTIME_REQUIRED_CHECKS if payload.get(field) is not True
    )
    screenshots = payload.get("screenshot_refs", [])
    if not isinstance(screenshots, list) or not screenshots:
        missing.append("screenshot_refs")
    return {
        "status": "pass" if not missing else "not-validated",
        "path": RUNTIME_ACCEPTANCE_PATH,
        "tracked": False,
        "obsidian_version": payload.get("obsidian_version", ""),
        "validated_at": payload.get("validated_at", ""),
        "validated_by": payload.get("validated_by", ""),
        "checks": {field: payload.get(field) is True for field in RUNTIME_REQUIRED_CHECKS},
        "screenshot_ref_count": len(screenshots) if isinstance(screenshots, list) else 0,
        "missing_fields": missing,
    }


def is_managed_markdown(item: Mapping[str, Any]) -> bool:
    path = str(item.get("path", ""))
    if item.get("status") not in {"active", "reviewing", "draft"}:
        return False
    if item.get("visibility") == "personal-local" or not path.endswith(".md"):
        return False
    if path.startswith("artifacts/manifests/") or "/archive/" in path:
        return False
    return path == "README.md" or path.startswith(
        ("domains/", "governance/", "projects/", "registry/", "templates/", "notes/")
    )


def _as_list(value: Any) -> List[str]:
    values = value if isinstance(value, list) else [value] if value else []
    result: List[str] = []
    for raw in values:
        text = str(raw).strip()
        if text and text not in result:
            result.append(text)
    return result


def _default_related(item: Mapping[str, Any], projects: Sequence[Mapping[str, Any]]) -> List[str]:
    path = str(item["path"])
    domain = str(item.get("domain", ""))
    related = ["indexes/obsidian-home.md"]
    if domain.startswith("projects/"):
        project_id = domain.split("/", 1)[1]
        project = next((row for row in projects if row.get("id") == project_id), None)
        if project and project.get("entry"):
            related.insert(0, str(project["entry"]))
        related.append("indexes/project-readiness.md")
    return [value for value in related if value != path]


def _relative_link(source: str, target: str, label: str) -> str:
    relative = posixpath.relpath(target, posixpath.dirname(source) or ".")
    return "[{}]({})".format(label.replace("[", "\\["), relative)


def _projects_moc(projects: Sequence[Mapping[str, Any]]) -> str:
    path = "indexes/obsidian/projects.md"
    rows = [
        "# 项目 MOC",
        "",
        "本页只提供导航。项目状态、owner、授权和 promotion 仍以 registry 与 product gate 为准。",
        "",
        "| 项目 | 类型 | registry 状态 | readiness |",
        "|---|---|---|---|",
    ]
    for project in sorted(projects, key=lambda row: str(row.get("id", ""))):
        entry = str(project.get("entry", ""))
        rows.append(
            "| {} | `{}` | `{}` | {} |".format(
                _relative_link(path, entry, str(project.get("name", project.get("id", "")))),
                project.get("type", ""),
                project.get("status", ""),
                _relative_link(path, "indexes/project-readiness.md", "4 槽位工作台"),
            )
        )
    return "\n".join(rows) + "\n"


def _topics_moc(items: Sequence[Mapping[str, Any]]) -> str:
    path = "indexes/obsidian/topics.md"
    by_tag: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for item in items:
        for tag in _as_list(item.get("tags")):
            by_tag[tag].append(item)
    rows = [
        "# 主题 MOC",
        "",
        "主题来自 managed Markdown 的 `tags`。本页用于发现，不改变 lifecycle 或权威状态。",
        "",
        "- {}".format(_relative_link(path, "indexes/by-topic.md", "完整主题派生索引")),
        "",
    ]
    for tag in sorted(by_tag, key=lambda value: (-len(by_tag[value]), value.lower())):
        rows.extend(["## {} ({})".format(tag, len(by_tag[tag])), ""])
        selected = sorted(
            by_tag[tag],
            key=lambda row: (0 if row.get("status") == "active" else 1, str(row.get("title", ""))),
        )[:6]
        for item in selected:
            rows.append("- {} · `{}`".format(_relative_link(path, str(item["path"]), str(item["title"])), item["status"]))
        rows.append("")
    return "\n".join(rows).rstrip() + "\n"


def _home_with_views(text: str) -> str:
    block = """{start}
## Obsidian MOC 与只读视图

- [项目 MOC](obsidian/projects.md)
- [主题 MOC](obsidian/topics.md)
- [项目成熟度 Base](obsidian/project-readiness.base)
- [Reviewing Base](obsidian/reviewing.base)
- [Active 知识 Base](obsidian/active-knowledge.base)
{end}""".format(start=HOME_START, end=HOME_END)
    if HOME_START in text and HOME_END in text:
        before, remainder = text.split(HOME_START, 1)
        _, after = remainder.split(HOME_END, 1)
        return before.rstrip() + "\n\n" + block + after.rstrip() + "\n"
    return text.rstrip() + "\n\n" + block + "\n"


def _add_text(transaction: RepositoryTransaction, root: pathlib.Path, path: str, content: str) -> None:
    target = root / path
    transaction.add_text(path, content, expected_sha256=file_sha256(target) if target.exists() else "")


def build_obsidian_views(
    root: pathlib.Path, apply: bool = False, reconcile_content_mirrors: bool = False
) -> Dict[str, Any]:
    items = registry_items(root)
    projects = list((load_json(root / "registry/projects.json", {}) or {}).get("projects", []))
    managed = [item for item in items if is_managed_markdown(item)]
    missing_files: List[str] = []
    content_drifts: List[Dict[str, Any]] = []
    content_reconciliations: List[Dict[str, Any]] = []
    rendered: Dict[str, str] = {}
    property_counts: Counter[str] = Counter()

    for item in managed:
        path = str(item["path"])
        target = root / path
        if not target.exists():
            missing_files.append(path)
            continue
        metadata, body = split_frontmatter(target.read_text(encoding="utf-8"))
        had_frontmatter = bool(metadata)
        for field in CONTENT_FIELDS:
            if field in metadata and metadata[field] != item.get(field):
                row = {"path": path, "field": field, "markdown": metadata[field], "registry": item.get(field)}
                if reconcile_content_mirrors:
                    if field == "tags":
                        metadata[field] = _as_list(metadata[field]) + [
                            value for value in _as_list(item.get(field)) if value not in _as_list(metadata[field])
                        ]
                    item[field] = metadata[field]
                    row["resolution"] = "markdown-authority" if field != "tags" else "ordered-union-to-markdown"
                    row["resolved_value"] = metadata[field]
                    content_reconciliations.append(row)
                else:
                    content_drifts.append(row)
            elif field not in metadata and item.get(field) not in (None, "", []):
                metadata[field] = item[field]
        for field in LIFECYCLE_FIELDS:
            if item.get(field) not in (None, ""):
                metadata[field] = item[field]
        metadata["aliases"] = _as_list(metadata.get("aliases")) or [str(item["title"])]
        metadata["related"] = _as_list(metadata.get("related")) or _default_related(item, projects)
        for field in (*CONTENT_FIELDS, *LIFECYCLE_FIELDS, "aliases", "related"):
            if metadata.get(field) not in (None, "", []):
                property_counts[field] += 1
        rendered[path] = render_markdown(metadata, body if had_frontmatter else target.read_text(encoding="utf-8"))

    transaction = RepositoryTransaction(root)
    for path, content in rendered.items():
        _add_text(transaction, root, path, content)
    if content_reconciliations:
        _add_text(transaction, root, "registry/items.jsonl", encode_jsonl(items))
    _add_text(transaction, root, "indexes/obsidian/projects.md", _projects_moc(projects))
    _add_text(transaction, root, "indexes/obsidian/topics.md", _topics_moc(managed))
    home_path = root / "indexes/obsidian-home.md"
    _add_text(transaction, root, "indexes/obsidian-home.md", _home_with_views(home_path.read_text(encoding="utf-8")))
    for path, content in BASE_FILES.items():
        _add_text(transaction, root, path, content)
    plan = transaction.plan()
    required = (*CONTENT_FIELDS, *LIFECYCLE_FIELDS, "aliases", "related")
    coverage = {
        field: {
            "declared_count": property_counts[field],
            "expected_count": len(managed),
            "coverage_percent": round(property_counts[field] * 100.0 / len(managed), 2) if managed else 100.0,
        }
        for field in required
    }
    blocked = bool(missing_files or content_drifts)
    runtime_acceptance = obsidian_runtime_acceptance(root)
    result: Dict[str, Any] = {
        "schema_version": 1,
        "action": "build-obsidian-views",
        "status": "blocked" if blocked else "planned",
        "read_only_authority": True,
        "community_plugin_required": False,
        "obsidian_private_config_tracked": False,
        "obsidian_runtime_status": runtime_acceptance["status"],
        "runtime_acceptance": runtime_acceptance,
        "managed_document_count": len(managed),
        "missing_file_count": len(missing_files),
        "missing_files": missing_files,
        "content_mirror_drift_count": len(content_drifts),
        "content_mirror_drifts": content_drifts,
        "content_mirror_reconciliation_count": len(content_reconciliations),
        "content_mirror_reconciliations": content_reconciliations,
        "property_coverage": coverage,
        "moc_count": 3,
        "base_count": len(BASE_FILES),
        "transaction": {
            "transaction_id": plan["transaction_id"],
            "write_count": plan["write_count"],
            "changed_count": plan["changed_count"],
        },
    }
    if apply and not blocked:
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
