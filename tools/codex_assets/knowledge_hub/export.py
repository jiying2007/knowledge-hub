"""Controlled, atomic local team export of active canonical knowledge."""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import posixpath
import re
import urllib.parse
import uuid
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from .common import KnowledgeHubError, encode_jsonl, file_sha256, pretty_json, registry_items, utc_timestamp
from .security import SCANNER_VERSION, scan_secret_text


DENY_PREFIXES = (
    "registry/",
    "indexes/",
    "tools/",
    "schemas/",
    "sources/",
    "artifacts/manifests/",
    "artifacts/vault/",
    "notes/personal/",
    "local/",
    ".cache/",
    ".tmp/",
)
MARKDOWN_LINK = re.compile(r"(?<!!)\[([^\]\n]+)\]\(([^)\n]+)\)")
IMAGE_LINK = re.compile(r"!\[([^\]\n]*)\]\(([^)\n]+)\)")
WIKI_LINK = re.compile(r"(?<!!)\[\[([^\]\n]+)\]\]")


def _eligible(item: Mapping[str, Any]) -> Tuple[bool, str]:
    path = str(item.get("path", ""))
    if item.get("status") != "active":
        return False, "not-active"
    if item.get("visibility") != "team-internal":
        return False, "not-team-internal"
    if not path.endswith(".md"):
        return False, "not-markdown"
    if path.startswith(DENY_PREFIXES):
        return False, "control-vault-or-personal"
    if item.get("kind") == "decision" and (
        item.get("manual_validation_pending")
        or item.get("decision_owner") in {None, "", "unassigned"}
        or str(item.get("review_status", "")).endswith("pending")
    ):
        return False, "pending-owner-decision"
    return True, "eligible"


def _review_provenance(item: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "owner": item.get("owner", ""),
        "review_status": item.get("review_status", ""),
        "decision_owner": item.get("decision_owner", ""),
        "validation_ref_count": len(item.get("validation_refs", [])),
        "source_type": (item.get("source") or {}).get("type", "")
        if isinstance(item.get("source"), Mapping)
        else "",
    }


def _export_item(item: Mapping[str, Any]) -> Dict[str, Any]:
    fields = (
        "id",
        "title",
        "kind",
        "domain",
        "path",
        "scope",
        "visibility",
        "status",
        "owner",
        "review_after",
        "summary_zh",
        "tags",
    )
    return {field: item[field] for field in fields if field in item}


def plan_team_export(root: pathlib.Path) -> Dict[str, Any]:
    selected: List[Dict[str, Any]] = []
    excluded: Dict[str, int] = {}
    errors: List[Dict[str, Any]] = []
    seen_paths: Set[str] = set()
    for item in registry_items(root):
        eligible, reason = _eligible(item)
        if not eligible:
            excluded[reason] = excluded.get(reason, 0) + 1
            continue
        path = str(item["path"])
        if path in seen_paths:
            continue
        seen_paths.add(path)
        source = root / path
        if not source.is_file():
            errors.append({"id": str(item.get("id", "")), "path": path, "error": "body-missing"})
            continue
        text = source.read_text(encoding="utf-8", errors="ignore")
        findings = scan_secret_text(text)
        if findings:
            errors.append(
                {
                    "id": str(item.get("id", "")),
                    "path": path,
                    "error": "high-confidence-secret-pattern",
                    "scanner_version": SCANNER_VERSION,
                    "findings": findings,
                }
            )
            continue
        selected.append(
            {
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "kind": item.get("kind", ""),
                "domain": item.get("domain", ""),
                "path": path,
                "status": item.get("status", ""),
                "owner": item.get("owner", ""),
                "review_after": item.get("review_after", ""),
                "sha256": file_sha256(source),
                "size": source.stat().st_size,
                "review_provenance": _review_provenance(item),
            }
        )
    return {
        "schema_version": 1,
        "read_only": True,
        "status": "ready" if selected and not errors else "blocked",
        "policy": "active-team-internal-canonical-markdown-only",
        "selected_count": len(selected),
        "selected": sorted(selected, key=lambda row: str(row["path"])),
        "excluded_by_reason": dict(sorted(excluded.items())),
        "secret_scan": {
            "status": "pass" if not errors else "fail",
            "scanner_version": SCANNER_VERSION,
            "finding_count": sum(len(row.get("findings", [])) for row in errors),
        },
        "errors": errors,
        "must_not": [
            "不导出 personal、draft、reviewing、archived、superseded 或 rejected",
            "不导出 registry、manifest、source、tool、vault 或运行时 control 资产",
            "不上传、不发布、不改变远端状态",
        ],
    }


def _safe_output(root: pathlib.Path, output: pathlib.Path) -> pathlib.Path:
    resolved = output.expanduser().resolve(strict=False)
    allowed = [root / ".cache" / "knowledge-hub" / "exports", pathlib.Path("/tmp")]
    for base in allowed:
        try:
            resolved.relative_to(base.resolve(strict=False))
            return resolved
        except ValueError:
            continue
    raise KnowledgeHubError("export output must stay under .cache/knowledge-hub/exports or /tmp")


def _local_target(source_path: str, raw_target: str) -> Optional[str]:
    target = raw_target.strip().strip("<>")
    if not target or target.startswith("#"):
        return None
    parsed = urllib.parse.urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    decoded = urllib.parse.unquote(parsed.path)
    if not decoded:
        return None
    normalized = posixpath.normpath(posixpath.join(posixpath.dirname(source_path), decoded))
    if normalized == ".." or normalized.startswith("../") or normalized.startswith("/"):
        return "__unsafe__"
    return normalized


def _rewrite_links(
    text: str,
    source_path: str,
    selected_paths: Set[str],
) -> Tuple[str, List[Dict[str, str]]]:
    rewrites: List[Dict[str, str]] = []

    def image_replacement(match: re.Match) -> str:
        target = _local_target(source_path, match.group(2))
        if target is None:
            return match.group(0)
        rewrites.append({"source": source_path, "target": target, "reason": "local-attachment-excluded"})
        return match.group(1) or "附件"

    def markdown_replacement(match: re.Match) -> str:
        target = _local_target(source_path, match.group(2))
        if target is None or target in selected_paths:
            return match.group(0)
        reason = "unsafe-target" if target == "__unsafe__" else "target-not-exported"
        rewrites.append({"source": source_path, "target": target, "reason": reason})
        return match.group(1)

    rewritten = IMAGE_LINK.sub(image_replacement, text)
    rewritten = MARKDOWN_LINK.sub(markdown_replacement, rewritten)

    def wiki_replacement(match: re.Match) -> str:
        raw = match.group(1)
        target_text, _, label = raw.partition("|")
        target_text = target_text.split("#", 1)[0].strip()
        label = label.strip() or pathlib.PurePosixPath(target_text).stem
        candidates = [
            path
            for path in selected_paths
            if path == target_text
            or path == target_text + ".md"
            or pathlib.PurePosixPath(path).stem == target_text
        ]
        if len(candidates) == 1:
            relative = posixpath.relpath(candidates[0], posixpath.dirname(source_path) or ".")
            return "[{}]({})".format(label, relative)
        rewrites.append({"source": source_path, "target": target_text, "reason": "wiki-target-not-exported"})
        return label

    return WIKI_LINK.sub(wiki_replacement, rewritten), rewrites


def _link_closure(root: pathlib.Path, paths: Sequence[str]) -> Dict[str, Any]:
    broken: List[Dict[str, str]] = []
    checked = 0
    for relative in paths:
        text = (root / relative).read_text(encoding="utf-8", errors="ignore")
        for match in MARKDOWN_LINK.finditer(text):
            target = _local_target(relative, match.group(2))
            if target is None:
                continue
            checked += 1
            if target == "__unsafe__" or not (root / target).exists():
                broken.append({"source": relative, "target": target})
        for match in WIKI_LINK.finditer(text):
            checked += 1
            broken.append({"source": relative, "target": match.group(1)})
    return {
        "status": "pass" if not broken else "fail",
        "checked_link_count": checked,
        "broken_count": len(broken),
        "broken": broken,
    }


def _write_incomplete(staging: pathlib.Path, destination: pathlib.Path, reason: str) -> None:
    try:
        staging.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "status": "incomplete",
            "destination": destination.name,
            "reason": reason,
            "generated_at": utc_timestamp(),
        }
        (staging / ".incomplete.json").write_text(pretty_json(payload) + "\n", encoding="utf-8")
    except OSError:
        pass


def apply_team_export(
    root: pathlib.Path,
    today: dt.date,
    output: pathlib.Path = None,
) -> Dict[str, Any]:
    plan = plan_team_export(root)
    if plan["status"] != "ready":
        raise KnowledgeHubError("team export plan is blocked")
    if output is None:
        output = root / ".cache" / "knowledge-hub" / "exports" / "team-active-{}-{}".format(
            today.strftime("%Y%m%d"), uuid.uuid4().hex[:8]
        )
    destination = _safe_output(root, output)
    if destination.exists():
        raise KnowledgeHubError("export destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / "{}.staging-{}".format(destination.name, uuid.uuid4().hex[:8])
    staging.mkdir()
    try:
        rows: List[Dict[str, Any]] = []
        rewrites: List[Dict[str, str]] = []
        selected_items: List[Dict[str, Any]] = []
        item_by_id = {str(row.get("id", "")): row for row in registry_items(root)}
        selected_paths = {str(row["path"]) for row in plan["selected"]}
        for row in plan["selected"]:
            source = root / row["path"]
            target = staging / row["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            rewritten, file_rewrites = _rewrite_links(
                source.read_text(encoding="utf-8"),
                str(row["path"]),
                selected_paths,
            )
            target.write_text(rewritten, encoding="utf-8")
            rewrites.extend(file_rewrites)
            exported = dict(row)
            exported["source_sha256"] = exported.pop("sha256")
            exported["exported_sha256"] = file_sha256(target)
            exported["size"] = target.stat().st_size
            rows.append(exported)
            selected_items.append(_export_item(item_by_id[str(row["id"])]))
        registry_dir = staging / "registry"
        registry_dir.mkdir(parents=True)
        (registry_dir / "items.jsonl").write_text(encode_jsonl(selected_items), encoding="utf-8")
        indexes_dir = staging / "indexes"
        indexes_dir.mkdir(parents=True)
        index_rows = [
            "# Team export index",
            "",
            "本页只索引本次导出的 reviewed active canonical Markdown，不改变源 Hub 生命周期。",
            "",
        ]
        for row in sorted(rows, key=lambda value: str(value["path"])):
            index_rows.append("- [{}](../{}) · `{}`".format(row["title"], row["path"], row["id"]))
        (indexes_dir / "team-index.md").write_text("\n".join(index_rows) + "\n", encoding="utf-8")
        (staging / "EXPORT.md").write_text(
            "# Knowledge Hub team export\n\n"
            "该目录只包含导出时为 active、team-internal 且通过 owner-decision 排除规则的 canonical Markdown。"
            "它不是完整备份，不包含 reviewing/历史/control/vault，也不授予 owner decision 或发布权限。\n",
            encoding="utf-8",
        )
        supporting_paths = ("registry/items.jsonl", "indexes/team-index.md", "EXPORT.md")
        closure = _link_closure(
            staging,
            [str(row["path"]) for row in rows] + list(supporting_paths),
        )
        if closure["status"] != "pass":
            raise KnowledgeHubError("export link closure failed")
        secret_findings: List[Dict[str, Any]] = []
        for relative in [str(row["path"]) for row in rows] + list(supporting_paths):
            findings = scan_secret_text(
                (staging / relative).read_text(encoding="utf-8", errors="ignore")
            )
            if findings:
                secret_findings.append({"path": relative, "findings": findings})
        if secret_findings:
            raise KnowledgeHubError("secret scan failed after export")
        supporting = [
            {
                "path": relative,
                "sha256": file_sha256(staging / relative),
                "size": (staging / relative).stat().st_size,
                "role": "supporting-index",
            }
            for relative in supporting_paths
        ]
        manifest = {
            "schema_version": 2,
            "export_id": destination.name,
            "generated_at": utc_timestamp(),
            "policy": plan["policy"],
            "content_file_count": len(rows),
            "supporting_file_count": len(supporting),
            "file_count": len(rows) + len(supporting),
            "files": rows + supporting,
            "excluded_by_reason": plan["excluded_by_reason"],
            "source_root": "~/knowledge-hub",
            "remote_publish": False,
            "incomplete": False,
            "review_provenance": {
                "mode": "registry-owner-review-status-and-validation-ref-count",
                "content_row_count": len(rows),
            },
            "link_closure": dict(closure, rewrite_count=len(rewrites), rewrites=rewrites),
            "secret_scan": {
                "status": "pass",
                "scanner_version": SCANNER_VERSION,
                "finding_count": 0,
            },
        }
        (staging / "manifest.json").write_text(pretty_json(manifest) + "\n", encoding="utf-8")
        os.replace(str(staging), str(destination))
    except Exception as exc:
        _write_incomplete(staging, destination, type(exc).__name__)
        if isinstance(exc, KnowledgeHubError):
            raise
        raise KnowledgeHubError("team export staging failed: {}".format(type(exc).__name__)) from exc
    return {
        "schema_version": 1,
        "status": "exported",
        "tracked_files_written": False,
        "remote_publish": False,
        "output": str(destination.relative_to(root))
        if str(destination).startswith(str(root) + os.sep)
        else str(destination),
        "content_file_count": len(rows),
        "supporting_file_count": len(supporting),
        "file_count": len(rows) + len(supporting),
        "manifest_sha256": file_sha256(destination / "manifest.json"),
        "secret_scan": manifest["secret_scan"],
        "link_closure": manifest["link_closure"],
        "policy": plan["policy"],
    }
