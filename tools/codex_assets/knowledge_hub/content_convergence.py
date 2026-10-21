"""Read-only, bounded evidence for single-canonical body and source convergence.

This is a projection of existing registry and source-control inputs, NOT a
new lifecycle ledger, owner decision, or repository/Product terminal verdict.
Never read an external source directory or promote an archived body.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from collections import defaultdict
from typing import Any, Dict, Mapping, Sequence

from .common import KnowledgeHubError

SHA256 = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FILE_EXTENSIONS = frozenset({
    ".md", ".txt", ".json", ".jsonl", ".pdf", ".doc", ".docx",
    ".png", ".jpg", ".jpeg", ".yaml", ".yml",
})
MAX_FILES = 5000
MAX_HASH_BYTES = 128 * 1024 * 1024
MAX_INVENTORY_ROWS = 10000
MAX_INVENTORY_LINE_BYTES = 65536
MAX_INVENTORY_FILE_BYTES = 2 * 1024 * 1024


def _require_hub_file(root: pathlib.Path, path: pathlib.Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise KnowledgeHubError("missing or symlinked Hub evidence file: " + path.name)
    try:
        path.resolve(strict=True).relative_to(root)
    except ValueError as exc:
        raise KnowledgeHubError("Hub evidence file escapes repository: " + path.name) from exc


def _json(root: pathlib.Path, path: pathlib.Path) -> Any:
    _require_hub_file(root, path)
    if path.stat().st_size > 2 * 1024 * 1024:
        raise KnowledgeHubError("convergence registry exceeds 2MiB: " + path.name)
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(root: pathlib.Path, path: pathlib.Path) -> list:
    _require_hub_file(root, path)
    if path.stat().st_size > MAX_INVENTORY_FILE_BYTES:
        raise KnowledgeHubError("convergence ledger file exceeds byte budget: " + path.name)
    rows = []
    total_bytes = 0
    with path.open("rb") as handle:
        while True:
            # Bound the read itself, not just a length check after allocation.
            raw = handle.readline(MAX_INVENTORY_LINE_BYTES + 1)
            if not raw:
                break
            total_bytes += len(raw)
            if total_bytes > MAX_INVENTORY_FILE_BYTES:
                raise KnowledgeHubError("convergence ledger file exceeds byte budget: " + path.name)
            if len(raw) > MAX_INVENTORY_LINE_BYTES:
                raise KnowledgeHubError("convergence ledger line exceeds budget: " + path.name)
            if not raw.strip():
                continue
            if len(rows) >= MAX_INVENTORY_ROWS:
                raise KnowledgeHubError("convergence ledger row budget exceeded: " + path.name)
            row = json.loads(raw)
            if not isinstance(row, dict):
                raise KnowledgeHubError("convergence ledger row is not an object: " + path.name)
            rows.append(row)
    return rows


def _file_digest(root: pathlib.Path, relative: str, remaining: int):
    relative_path = pathlib.PurePosixPath(relative)
    if (not relative or relative_path.is_absolute()
            or ".." in relative_path.parts or "\\" in relative):
        raise KnowledgeHubError("invalid canonical body path")
    path = root / relative
    if path.is_symlink() or not path.is_file():
        raise KnowledgeHubError("canonical body missing or symlinked: " + relative)
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise KnowledgeHubError("canonical body escapes repository: " + relative) from exc
    before = path.stat()
    if before.st_size > remaining:
        raise KnowledgeHubError("canonical body digest byte budget exhausted")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            size += len(chunk)
            if size > remaining:
                raise KnowledgeHubError("canonical body changed past digest budget")
            digest.update(chunk)
    after = path.stat()
    if size != before.st_size or size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise KnowledgeHubError("canonical body changed during digest: " + relative)
    return digest.hexdigest(), size


def _source_control(root: pathlib.Path) -> Dict[str, Any]:
    current = _json(root, root / "registry/sources.json")
    if not isinstance(current, dict) or not isinstance(current.get("sources"), list):
        raise KnowledgeHubError("invalid current source registry")
    retired = _jsonl(root, root / "registry/retired-sources.jsonl")
    sources = [("current", row) for row in current["sources"]]
    sources += [("retired", row) for row in retired]
    seen = set()
    details = []
    totals = {
        "current_source_count": 0,
        "retired_source_count": 0,
        "inventory_rows": 0,
        "root_or_batch_rows": 0,
        "file_level_candidate_rows": 0,
        "file_level_sha256_rows": 0,
        "rows_without_sha256": 0,
    }
    for bucket, row in sorted(
        sources,
        key=lambda pair: str(pair[1].get("id", "")) if isinstance(pair[1], dict) else "",
    ):
        if not isinstance(row, dict):
            raise KnowledgeHubError("invalid source control row")
        source_id = row.get("id")
        if not isinstance(source_id, str) or not SOURCE_ID.fullmatch(source_id) or source_id in seen:
            raise KnowledgeHubError("duplicate or invalid source identity")
        seen.add(source_id)
        inventory_path = root / "sources" / source_id / "inventory.jsonl"
        inventory = _jsonl(root, inventory_path)
        file_candidates, hashes, roots = 0, 0, 0
        for item in inventory:
            if item.get("source_id") != source_id:
                raise KnowledgeHubError("source inventory identity mismatch: " + source_id)
            origin = str(item.get("origin_path", ""))
            suffix = pathlib.PurePosixPath(origin).suffix.lower()
            looks_file_level = suffix in FILE_EXTENSIONS
            sha = item.get("sha256", "")
            hashed = isinstance(sha, str) and bool(SHA256.fullmatch(sha))
            if sha and not hashed:
                raise KnowledgeHubError("invalid source inventory SHA256: " + source_id)
            if looks_file_level:
                file_candidates += 1
                if hashed and type(item.get("size_bytes")) is int and item["size_bytes"] > 0:
                    hashes += 1
            else:
                roots += 1
            if not hashed:
                totals["rows_without_sha256"] += 1
        totals[bucket + "_source_count"] += 1
        totals["inventory_rows"] += len(inventory)
        totals["root_or_batch_rows"] += roots
        totals["file_level_candidate_rows"] += file_candidates
        totals["file_level_sha256_rows"] += hashes
        details.append({
            "source_id": source_id,
            "registry_bucket": bucket,
            "inventory_rows": len(inventory),
            "root_or_batch_rows": roots,
            "file_level_candidate_rows": file_candidates,
            "file_level_sha256_rows": hashes,
        })
    return {
        **totals,
        "sources": details,
        "external_source_snapshot_observed": False,
        "full_external_migration_proven": False,
        "proof_boundary": (
            "Source inventory rows and digest candidates are Hub-side provenance only. "
            "No external source filesystem, revision or provider was observed. "
            "Root/batch hashes never prove per-file completeness."
        ),
    }


def build_content_convergence(
    root: pathlib.Path,
    body_paths: Sequence[str],
    registry_ids_by_path: Mapping[str, Sequence[str]],
    collection_ids_by_path: Mapping[str, str],
) -> Dict[str, Any]:
    """Hash only tracked Hub Markdown; do not scan or mutate external paths."""
    root = root.resolve()
    if len(body_paths) > MAX_FILES:
        raise KnowledgeHubError("canonical body file count exceeds budget")
    if len(set(body_paths)) != len(body_paths):
        raise KnowledgeHubError("duplicate canonical body path in scan")
    groups = defaultdict(list)
    rows = []
    hashed_bytes = 0
    for relative in sorted(body_paths):
        sha, size = _file_digest(root, relative, MAX_HASH_BYTES - hashed_bytes)
        hashed_bytes += size
        ids = list(registry_ids_by_path.get(relative, []))
        collection_id = collection_ids_by_path.get(relative, "")
        if ids and collection_id:
            raise KnowledgeHubError("body has duplicate registry and collection ownership")
        if len(ids) > 1:
            raise KnowledgeHubError("body has duplicate exact registry identities")
        coverage = "exact-registry" if ids else "frozen-collection" if collection_id else "missing"
        row = {
            "path": relative,
            "sha256": sha,
            "size_bytes": size,
            "coverage": coverage,
            "registry_ids": ids,
            "collection_id": collection_id,
        }
        rows.append(row)
        groups[sha].append(row)
    duplicate_candidates = [
        {"sha256": sha, "paths": [row["path"] for row in members]}
        for sha, members in sorted(groups.items())
        if len(members) > 1
    ]
    sources = _source_control(root)
    return {
        "schema_version": 1,
        "contract": "knowledge-hub-content-convergence-observation-v1",
        "read_only": True,
        "scope": "tracked-Hub-Markdown-only",
        "canonical_authority": "Markdown + registry",
        "new_status_source": False,
        "body_count": len(rows),
        "hashed_bytes": hashed_bytes,
        "exact_registry_count": sum(row["coverage"] == "exact-registry" for row in rows),
        "frozen_collection_count": sum(row["coverage"] == "frozen-collection" for row in rows),
        "uncovered_count": sum(row["coverage"] == "missing" for row in rows),
        "body_records": rows,
        "exact_duplicate_candidate_count": len(duplicate_candidates),
        "exact_duplicate_candidates": duplicate_candidates,
        "duplicate_action": "review-only; no automatic deletion, merge or promotion",
        "source_controls": sources,
        "full_external_migration_proven": False,
        "full_content_review_proven": False,
        "owner_decisions_generated": False,
        "canonical_mutations": 0,
        "notes_zh": (
            "本报告是仓库内正文的逐文件只读取证，不会证明外部原始目录当前文件全集。"
            "冻结集合覆盖、source 根目录记录或同哈希均不得自动提升 active、删除正文或签署 owner。"
            "仓库级 Terminal 和 Product/Content Terminal 必须继续使用各自现有机器门禁。"
        ),
    }
