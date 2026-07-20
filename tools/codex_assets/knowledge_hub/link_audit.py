"""Standard Markdown link and optional Obsidian Base audit."""

from __future__ import annotations

import pathlib
import re
import urllib.parse
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

import yaml

from .common import (
    DEFAULT_MARKDOWN_MAX_BYTES,
    load_json,
    project_rows,
    read_repository_utf8_bounded,
    registry_items,
    split_frontmatter,
    utc_timestamp,
)
from .obsidian_view import CONTENT_FIELDS, is_managed_markdown


MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")
WIKI_LINK = re.compile(r"(?<!!)\[\[([^\]\n]+)\]\]")
IMAGE_LINK = re.compile(r"!\[[^\]\n]*\]\(([^)\n]+)\)")
WIKI_EMBED = re.compile(r"!\[\[([^\]\n]+)\]\]")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
EXCLUDED_PARTS = {".git", ".cache", ".tmp", "__pycache__", "artifacts/vault"}
REQUIRED_MANAGED_PROPERTIES = (
    "id",
    "title",
    "kind",
    "domain",
    "path",
    "status",
    "owner",
    "review_after",
    "tags",
    "summary_zh",
    "aliases",
    "related",
)
BASE_ALLOWED_PROPERTIES = {
    "file.name",
    "kind",
    "owner",
    "decision_owner",
    "review_after",
    "status",
    "aliases",
    "related",
    "manual_validation_pending",
    "project_id",
    "readiness_slot",
}
LINK_AUDIT_MAX_FILE_BYTES = DEFAULT_MARKDOWN_MAX_BYTES
LINK_AUDIT_MAX_BASE_BYTES = 1024 * 1024


def _excluded(path: pathlib.Path, root: pathlib.Path) -> bool:
    relative = path.relative_to(root).as_posix()
    return any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts) or relative.startswith("artifacts/vault/")


def _markdown_paths(root: pathlib.Path) -> List[pathlib.Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.is_file() and not path.is_symlink() and not _excluded(path, root)
    )


def _without_fenced_code(text: str) -> str:
    output = []
    fence = ""
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = "```" if stripped.startswith("```") else "~~~" if stripped.startswith("~~~") else ""
        if marker:
            if not fence:
                fence = marker
            elif fence == marker:
                fence = ""
            output.append("")
            continue
        output.append("" if fence else line)
    return "\n".join(output)


def _target_text(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    if " " in value:
        value = value.split(" ", 1)[0]
    return value


def _resolve_target(root: pathlib.Path, source: pathlib.Path, raw: str) -> Tuple[Optional[pathlib.Path], str]:
    target = urllib.parse.unquote(_target_text(raw)).strip()
    if not target or target.startswith(("http://", "https://", "mailto:", "obsidian://", "data:")):
        return None, "external"
    if target.startswith("#"):
        return source, "present-anchor"
    path_text = target.split("#", 1)[0].split("?", 1)[0]
    if not path_text:
        return None, "anchor"
    candidate = root / path_text.lstrip("/") if path_text.startswith("/") else source.parent / path_text
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return candidate, "outside-root"
    if resolved.exists():
        return resolved, "present"
    if not resolved.suffix and resolved.with_suffix(".md").exists():
        return resolved.with_suffix(".md"), "present-md-extension"
    return resolved, "missing"


def _fragment(raw: str) -> str:
    target = urllib.parse.unquote(_target_text(raw)).strip()
    return target.split("#", 1)[1].strip() if "#" in target else ""


def _slug(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"[`*_~]", "", value).strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return re.sub(r"[\s-]+", "-", value).strip("-")


def _document_anchors(root: pathlib.Path, path: pathlib.Path) -> Set[str]:
    relative = path.relative_to(root).as_posix()
    text = _without_fenced_code(
        read_repository_utf8_bounded(
            root, relative, LINK_AUDIT_MAX_FILE_BYTES, "link audit Markdown"
        )
    )
    anchors: Set[str] = set()
    occurrences: Dict[str, int] = {}
    for raw in HEADING.findall(text):
        heading = raw.strip()
        slug = _slug(heading)
        count = occurrences.get(slug, 0)
        occurrences[slug] = count + 1
        anchors.add(heading)
        anchors.add(heading.lower())
        if slug:
            anchors.add(slug if count == 0 else "{}-{}".format(slug, count))
    anchors.update(re.findall(r"\s\^([A-Za-z0-9-]+)\s*$", text, flags=re.MULTILINE))
    return anchors


def _anchor_present(
    root: pathlib.Path,
    path: pathlib.Path,
    fragment: str,
    cache: Dict[pathlib.Path, Set[str]],
) -> bool:
    if not fragment or path.suffix.lower() != ".md":
        return True
    if path not in cache:
        cache[path] = _document_anchors(root, path)
    candidate = fragment.lstrip("^").strip()
    return candidate in cache[path] or candidate.lower() in cache[path] or _slug(candidate) in cache[path]


def _blocking_source(relative_source: str, source_status: str) -> bool:
    return (
        source_status in {"active", "reviewing", "draft"}
        or relative_source == "README.md"
        or relative_source.startswith("indexes/")
        or relative_source.endswith("/README.md")
    )


def _resolve_wiki_target(
    root: pathlib.Path, source: pathlib.Path, raw: str, all_files: Sequence[pathlib.Path]
) -> Tuple[Optional[pathlib.Path], str, str]:
    value = raw.split("|", 1)[0].strip()
    fragment = value.split("#", 1)[1].strip() if "#" in value else ""
    target_text = value.split("#", 1)[0].strip()
    if not target_text:
        return source, "present-anchor", fragment
    direct, state = _resolve_target(root, source, target_text)
    if direct is not None and state.startswith("present"):
        return direct, state, fragment
    target_without_suffix = target_text[:-3] if target_text.endswith(".md") else target_text
    matches = [
        path
        for path in all_files
        if path.stem == pathlib.PurePosixPath(target_without_suffix).name
        or path.relative_to(root).with_suffix("").as_posix() == target_without_suffix.lstrip("/")
    ]
    if len(matches) == 1:
        return matches[0], "present-wiki", fragment
    return None, "ambiguous-wiki" if matches else "missing-wiki", fragment


def _base_audit(root: pathlib.Path) -> List[Dict[str, Any]]:
    rows = []
    for path in sorted(root.rglob("*.base")):
        if _excluded(path, root):
            continue
        errors = []
        try:
            payload = yaml.safe_load(
                read_repository_utf8_bounded(
                    root,
                    path.relative_to(root).as_posix(),
                    LINK_AUDIT_MAX_BASE_BYTES,
                    "Obsidian Base",
                )
            ) or {}
        except (OSError, yaml.YAMLError) as exc:
            payload = {}
            errors.append("invalid YAML: {}".format(exc))
        if not isinstance(payload, dict):
            errors.append("root must be a mapping")
        elif not isinstance(payload.get("views"), list) or not payload.get("views"):
            errors.append("views must be a non-empty list")
        else:
            properties = payload.get("properties", {})
            if not isinstance(properties, dict) or not properties:
                errors.append("properties must be a non-empty mapping")
            else:
                unknown = sorted(set(str(value) for value in properties) - BASE_ALLOWED_PROPERTIES)
                if unknown:
                    errors.append("unsupported properties: {}".format(", ".join(unknown)))
            for index, view in enumerate(payload["views"], 1):
                if not isinstance(view, dict) or not view.get("type") or not view.get("name"):
                    errors.append("view {} must define type and name".format(index))
                elif view.get("type") not in {"table", "list", "cards", "map"}:
                    errors.append("view {} uses unsupported type {}".format(index, view.get("type")))
        serialized = str(payload).lower()
        if any(token in serialized for token in ("command:", "script:", "write:", "update:", "delete:")):
            errors.append("view must remain declarative and read-only")
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "status": "pass" if not errors else "fail",
                "errors": errors,
                "read_only_contract": True,
            }
        )
    return rows


def audit_links(root: pathlib.Path) -> Dict[str, Any]:
    items = registry_items(root)
    body_coverage = load_json(root / "registry/body-coverage.json", {}) or {}
    external_attachment_prefixes = tuple(
        str(row.get("path_prefix", ""))
        for row in body_coverage.get("collections", [])
        if isinstance(row, Mapping)
        and row.get("attachment_policy") == "external-not-retained"
        and str(row.get("path_prefix", ""))
    )
    item_by_path = {str(row.get("path", "")): row for row in items if row.get("path")}
    item_by_id = {str(row.get("id", "")): row for row in items if row.get("id")}
    markdown_paths = _markdown_paths(root)
    all_files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink() and not _excluded(path, root)
    )
    incoming: Dict[str, int] = {}
    broken: List[Dict[str, Any]] = []
    warning_broken: List[Dict[str, Any]] = []
    anchor_cache: Dict[pathlib.Path, Set[str]] = {}
    standard_count = 0
    external_count = 0
    wiki_count = 0
    anchor_count = 0
    broken_anchor_count = 0
    attachment_count = 0
    external_attachment_count = 0
    declared_external_attachment_count = 0
    declared_external_attachments: List[Dict[str, Any]] = []
    wiki_embed_count = 0
    for source in markdown_paths:
        relative_source = source.relative_to(root).as_posix()
        try:
            text = _without_fenced_code(
                read_repository_utf8_bounded(
                    root,
                    relative_source,
                    LINK_AUDIT_MAX_FILE_BYTES,
                    "link audit Markdown",
                )
            )
        except OSError as exc:
            broken.append({"source": relative_source, "target": "", "reason": str(exc), "status": "blocking"})
            continue
        wiki_count += len(WIKI_LINK.findall(text))
        for raw in MARKDOWN_LINK.findall(text):
            standard_count += 1
            target, state = _resolve_target(root, source, raw)
            if target is None:
                external_count += 1
                continue
            if state.startswith("present"):
                relative_target = target.relative_to(root).as_posix()
                incoming[relative_target] = incoming.get(relative_target, 0) + 1
                fragment = _fragment(raw)
                if fragment:
                    anchor_count += 1
                    if not _anchor_present(root, target, fragment, anchor_cache):
                        source_item = item_by_path.get(relative_source, {})
                        source_status = str(source_item.get("status", ""))
                        blocking = _blocking_source(relative_source, source_status)
                        row = {
                            "source": relative_source,
                            "target": _target_text(raw),
                            "reason": "missing-anchor",
                            "source_status": source_status or "unregistered",
                            "status": "blocking" if blocking else "historical-warning",
                        }
                        broken_anchor_count += 1
                        (broken if blocking else warning_broken).append(row)
                continue
            source_item = item_by_path.get(relative_source, {})
            source_status = str(source_item.get("status", ""))
            blocking = _blocking_source(relative_source, source_status)
            row = {
                "source": relative_source,
                "target": _target_text(raw),
                "reason": state,
                "source_status": source_status or "unregistered",
                "status": "blocking" if blocking else "historical-warning",
            }
            (broken if blocking else warning_broken).append(row)

        for raw in IMAGE_LINK.findall(text):
            attachment_count += 1
            target, state = _resolve_target(root, source, raw)
            if target is None:
                external_attachment_count += 1
                continue
            if state.startswith("present"):
                continue
            source_item = item_by_path.get(relative_source, {})
            source_status = str(source_item.get("status", ""))
            if relative_source.startswith(external_attachment_prefixes):
                declared_external_attachment_count += 1
                if len(declared_external_attachments) < 20:
                    declared_external_attachments.append(
                        {
                            "source": relative_source,
                            "target": _target_text(raw),
                            "reason": "attachment-external-not-retained",
                            "source_status": source_status or "unregistered",
                            "status": "declared-external",
                        }
                    )
                continue
            blocking = _blocking_source(relative_source, source_status)
            row = {
                "source": relative_source,
                "target": _target_text(raw),
                "reason": "attachment-{}".format(state),
                "source_status": source_status or "unregistered",
                "status": "blocking" if blocking else "historical-warning",
            }
            (broken if blocking else warning_broken).append(row)

        for raw in WIKI_LINK.findall(text):
            target, state, fragment = _resolve_wiki_target(root, source, raw, all_files)
            if target is not None and state.startswith("present"):
                relative_target = target.relative_to(root).as_posix()
                incoming[relative_target] = incoming.get(relative_target, 0) + 1
                if fragment:
                    anchor_count += 1
                    if not _anchor_present(root, target, fragment, anchor_cache):
                        state = "missing-anchor"
                    else:
                        continue
                else:
                    continue
            source_item = item_by_path.get(relative_source, {})
            source_status = str(source_item.get("status", ""))
            blocking = _blocking_source(relative_source, source_status)
            row = {
                "source": relative_source,
                "target": raw,
                "reason": state,
                "source_status": source_status or "unregistered",
                "status": "blocking" if blocking else "historical-warning",
            }
            (broken if blocking else warning_broken).append(row)

        for raw in WIKI_EMBED.findall(text):
            wiki_embed_count += 1
            target, state, _ = _resolve_wiki_target(root, source, raw, all_files)
            if target is not None and state.startswith("present"):
                continue
            source_item = item_by_path.get(relative_source, {})
            source_status = str(source_item.get("status", ""))
            if relative_source.startswith(external_attachment_prefixes):
                declared_external_attachment_count += 1
                if len(declared_external_attachments) < 20:
                    declared_external_attachments.append(
                        {
                            "source": relative_source,
                            "target": raw,
                            "reason": "attachment-external-not-retained",
                            "source_status": source_status or "unregistered",
                            "status": "declared-external",
                        }
                    )
                continue
            blocking = _blocking_source(relative_source, source_status)
            row = {
                "source": relative_source,
                "target": raw,
                "reason": "attachment-{}".format(state),
                "source_status": source_status or "unregistered",
                "status": "blocking" if blocking else "historical-warning",
            }
            (broken if blocking else warning_broken).append(row)

    managed_items = [item for item in items if is_managed_markdown(item)]
    managed_property_errors: List[Dict[str, Any]] = []
    managed_with_frontmatter = 0
    related_target_count = 0
    for item in managed_items:
        relative_path = str(item["path"])
        target = root / relative_path
        if not target.exists():
            managed_property_errors.append({"path": relative_path, "reason": "missing-managed-document"})
            continue
        try:
            metadata, _ = split_frontmatter(
                read_repository_utf8_bounded(
                    root,
                    relative_path,
                    LINK_AUDIT_MAX_FILE_BYTES,
                    "managed Markdown",
                )
            )
        except (OSError, ValueError) as exc:
            managed_property_errors.append({"path": relative_path, "reason": "invalid-frontmatter", "detail": str(exc)})
            continue
        if metadata:
            managed_with_frontmatter += 1
        missing_properties = [field for field in REQUIRED_MANAGED_PROPERTIES if metadata.get(field) in (None, "", [])]
        if missing_properties:
            managed_property_errors.append(
                {"path": relative_path, "reason": "missing-properties", "fields": missing_properties}
            )
        for field in (*CONTENT_FIELDS, "id", "path", "status", "owner", "review_after"):
            if metadata.get(field) != item.get(field):
                managed_property_errors.append(
                    {
                        "path": relative_path,
                        "reason": "property-mirror-drift",
                        "field": field,
                        "markdown": metadata.get(field),
                        "registry": item.get(field),
                    }
                )
        related = metadata.get("related", [])
        if not isinstance(related, list):
            managed_property_errors.append({"path": relative_path, "reason": "related-must-be-list"})
            related = []
        for raw in related:
            related_target_count += 1
            value = str(raw).strip().split("#", 1)[0]
            related_candidates = [root / value, target.parent / value]
            if value in item_by_id:
                related_candidates.insert(0, root / str(item_by_id[value].get("path", "")))
            expanded_candidates = []
            for candidate in related_candidates:
                expanded_candidates.append(candidate)
                if not candidate.suffix:
                    expanded_candidates.append(candidate.with_suffix(".md"))
            if not value or not any(candidate.exists() for candidate in expanded_candidates):
                managed_property_errors.append(
                    {"path": relative_path, "reason": "missing-related-target", "target": str(raw)}
                )

    readiness_paths = {
        str(row["path"])
        for row in items
        if "project-readiness" in set(str(value) for value in row.get("tags", []))
    }
    readiness_without_inbound = sorted(path for path in readiness_paths if incoming.get(path, 0) == 0)
    registered_without_inbound = sorted(
        path
        for path, item in item_by_path.items()
        if path.endswith(".md") and incoming.get(path, 0) == 0 and item.get("status") in {"active", "reviewing"}
    )
    bases = _base_audit(root)
    base_failures = [row for row in bases if row["status"] != "pass"]
    obsidian_contract_enabled = (root / "registry/projects.json").exists() or bool(bases)
    project_entries = (
        {str(row.get("entry", "")) for row in project_rows(root) if row.get("entry")}
        if obsidian_contract_enabled
        else set()
    )
    project_moc_orphans = sorted(path for path in project_entries if incoming.get(path, 0) == 0)
    required_mocs = {
        "indexes/obsidian-home.md",
        "indexes/obsidian/projects.md",
        "indexes/obsidian/topics.md",
        "indexes/obsidian/catalog.md",
        "indexes/project-readiness.md",
        "indexes/by-topic.md",
    } if obsidian_contract_enabled else set()
    missing_mocs = sorted(path for path in required_mocs if not (root / path).exists())
    gitignore = (
        read_repository_utf8_bounded(
            root, ".gitignore", LINK_AUDIT_MAX_BASE_BYTES, "gitignore"
        )
        if (root / ".gitignore").exists()
        else ""
    )
    private_config_ignored = not obsidian_contract_enabled or any(
        line.strip().rstrip("/") == ".obsidian" for line in gitignore.splitlines() if not line.lstrip().startswith("#")
    )
    status = (
        "pass"
        if not broken
        and not readiness_without_inbound
        and not base_failures
        and not managed_property_errors
        and not project_moc_orphans
        and not missing_mocs
        and private_config_ignored
        else "fail"
    )
    return {
        "schema_version": 1,
        "read_only": True,
        "tracked_files_written": False,
        "root": "~/knowledge-hub",
        "generated_at": utc_timestamp(),
        "status": status,
        "markdown_file_count": len(markdown_paths),
        "standard_link_count": standard_count,
        "external_or_anchor_count": external_count,
        "wiki_link_count": wiki_count,
        "anchor_link_count": anchor_count,
        "broken_anchor_count": broken_anchor_count,
        "attachment_reference_count": attachment_count,
        "external_attachment_count": external_attachment_count,
        "declared_external_attachment_count": declared_external_attachment_count,
        "declared_external_attachment_sample": declared_external_attachments,
        "wiki_embed_count": wiki_embed_count,
        "blocking_broken_count": len(broken),
        "blocking_broken": broken,
        "historical_warning_count": len(warning_broken),
        "historical_warnings": warning_broken,
        "readiness_document_count": len(readiness_paths),
        "readiness_without_inbound_count": len(readiness_without_inbound),
        "readiness_without_inbound": readiness_without_inbound,
        "active_or_reviewing_without_inbound_count": len(registered_without_inbound),
        "active_or_reviewing_without_inbound": registered_without_inbound,
        "managed_markdown_count": len(managed_items),
        "managed_frontmatter_count": managed_with_frontmatter,
        "managed_frontmatter_coverage_percent": round(
            managed_with_frontmatter * 100.0 / len(managed_items), 2
        )
        if managed_items
        else 100.0,
        "managed_property_error_count": len(managed_property_errors),
        "managed_property_errors": managed_property_errors,
        "related_target_count": related_target_count,
        "project_moc_orphan_count": len(project_moc_orphans),
        "project_moc_orphans": project_moc_orphans,
        "missing_moc_count": len(missing_mocs),
        "missing_mocs": missing_mocs,
        "obsidian_private_config_ignored": private_config_ignored,
        "community_plugin_required": False,
        "obsidian_bases": bases,
        "base_failure_count": len(base_failures),
        "notes_zh": "标准链接、锚点、附件、Properties、related、MOC 和 Base 均受审计；明确声明 external-not-retained 的冻结归档附件单独计数，不伪装成已恢复，也不制造历史告警。Backlinks 和 Graph 只用于发现关系，不决定生命周期。",
    }


def link_audit_summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": "link-audit-summary-v1",
        "generated_at": payload.get("generated_at", ""),
        "status": payload.get("status", "fail"),
        "markdown_file_count": payload.get("markdown_file_count", 0),
        "standard_link_count": payload.get("standard_link_count", 0),
        "blocking_broken_count": payload.get("blocking_broken_count", 0),
        "blocking_broken_sample": list(payload.get("blocking_broken", []))[:20],
        "historical_warning_count": payload.get("historical_warning_count", 0),
        "historical_warning_sample": list(payload.get("historical_warnings", []))[:10],
        "declared_external_attachment_count": payload.get(
            "declared_external_attachment_count", 0
        ),
        "declared_external_attachment_sample": list(
            payload.get("declared_external_attachment_sample", [])
        )[:10],
        "readiness_without_inbound_count": payload.get(
            "readiness_without_inbound_count", 0
        ),
        "active_or_reviewing_without_inbound_count": payload.get(
            "active_or_reviewing_without_inbound_count", 0
        ),
        "managed_frontmatter_coverage_percent": payload.get(
            "managed_frontmatter_coverage_percent", 0
        ),
        "managed_property_error_count": payload.get(
            "managed_property_error_count", 0
        ),
        "project_moc_orphan_count": payload.get("project_moc_orphan_count", 0),
        "missing_moc_count": payload.get("missing_moc_count", 0),
        "base_failure_count": payload.get("base_failure_count", 0),
        "obsidian_base_count": len(payload.get("obsidian_bases", [])),
    }
