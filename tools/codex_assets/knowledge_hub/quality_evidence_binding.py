"""Build and verify an exact-revision Quality evidence binding."""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any, Dict, Mapping, Sequence

from .common import KnowledgeHubError, file_sha256, resolve_inside, utc_timestamp

SOURCE_RE = re.compile(r"^[0-9a-f]{40}$")
DEFAULT_OUTPUT = ".cache/knowledge-hub/quality-evidence-binding.json"
MAX_EVIDENCE_BYTES = 32 * 1024 * 1024
QUALITY_EVIDENCE_PATHS = (
    ".tmp/engineering/knowledge-hub.cdx.json",
    ".cache/knowledge-hub/engineering-quality.json",
    ".cache/knowledge-hub/compliance-eval.json",
    ".cache/knowledge-hub/restore-drill-head.json",
    ".cache/knowledge-hub/final-gate-product-full.json",
)


def _inside(root: pathlib.Path, relative: str) -> pathlib.Path:
    return resolve_inside(root, relative)


def _evidence_row(root: pathlib.Path, relative: str) -> Dict[str, Any]:
    path = _inside(root, relative)
    if not path.is_file() or path.is_symlink():
        raise KnowledgeHubError("quality evidence is unavailable: {}".format(relative))
    size = path.stat().st_size
    if size <= 0:
        raise KnowledgeHubError("quality evidence is empty: {}".format(relative))
    if size > MAX_EVIDENCE_BYTES:
        raise KnowledgeHubError("quality evidence exceeds byte budget: {}".format(relative))
    return {
        "path": relative,
        "size": size,
        "sha256": file_sha256(path),
    }


def build_quality_evidence_binding(
    root: pathlib.Path,
    *,
    source_revision: str,
    evidence_paths: Sequence[str] = QUALITY_EVIDENCE_PATHS,
) -> Dict[str, Any]:
    root = pathlib.Path(root).resolve()
    revision = str(source_revision).strip().lower()
    if not SOURCE_RE.fullmatch(revision):
        raise KnowledgeHubError("source revision must be a lowercase 40-character git SHA")
    rows = [_evidence_row(root, relative) for relative in evidence_paths]
    return {
        "schema_version": "knowledge-hub.quality-evidence-binding.v1",
        "status": "pass",
        "source_revision": revision,
        "generated_at": utc_timestamp(),
        "evidence": rows,
        "canonical_write": False,
    }


def verify_quality_evidence_binding(
    root: pathlib.Path,
    binding: Mapping[str, Any],
    *,
    source_revision: str,
    evidence_paths: Sequence[str] = QUALITY_EVIDENCE_PATHS,
) -> Dict[str, Any]:
    root = pathlib.Path(root).resolve()
    revision = str(source_revision).strip().lower()
    if not SOURCE_RE.fullmatch(revision):
        raise KnowledgeHubError("source revision must be a lowercase 40-character git SHA")
    if binding.get("schema_version") != "knowledge-hub.quality-evidence-binding.v1":
        raise KnowledgeHubError("quality evidence binding schema is invalid")
    if binding.get("status") != "pass":
        raise KnowledgeHubError("quality evidence binding is not passing")
    if str(binding.get("source_revision", "")).lower() != revision:
        raise KnowledgeHubError("quality evidence binding source revision mismatch")
    if binding.get("canonical_write") is not False:
        raise KnowledgeHubError("quality evidence binding canonical-write state is invalid")
    rows = binding.get("evidence", [])
    if not isinstance(rows, list):
        raise KnowledgeHubError("quality evidence binding rows must be a list")
    expected_paths = list(evidence_paths)
    observed_paths = [
        str(row.get("path", "")) for row in rows if isinstance(row, Mapping)
    ]
    if observed_paths != expected_paths:
        raise KnowledgeHubError("quality evidence binding path set/order mismatch")
    recomputed = [_evidence_row(root, relative) for relative in expected_paths]
    normalized = [
        {
            "path": str(row.get("path", "")),
            "size": int(row.get("size", 0) or 0),
            "sha256": str(row.get("sha256", "")),
        }
        for row in rows
        if isinstance(row, Mapping)
    ]
    if normalized != recomputed:
        raise KnowledgeHubError("quality evidence binding digest/size mismatch")
    return {
        "schema_version": "knowledge-hub.quality-evidence-binding-verification.v1",
        "status": "pass",
        "source_revision": revision,
        "evidence_count": len(recomputed),
        "canonical_write": False,
    }


def load_binding(path: pathlib.Path) -> Dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise KnowledgeHubError("quality evidence binding is unavailable")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("quality evidence binding is invalid JSON") from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("quality evidence binding must be an object")
    return dict(value)


def write_binding(root: pathlib.Path, relative: str, payload: Mapping[str, Any]) -> str:
    root = pathlib.Path(root).resolve()
    path = _inside(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return str(path.relative_to(root))
