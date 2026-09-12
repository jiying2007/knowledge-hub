"""P8 provider payload adapters.

These adapters normalize already-fetched provider payloads. Credential handling and
network transport stay in the calling integration; Knowledge Hub receives bounded
objects and remains provider-neutral.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence

from .common import KnowledgeHubError


def _text(row: Mapping[str, Any], key: str, maximum: int = 4096) -> str:
    value = str(row.get(key, "")).strip()
    if len(value) > maximum:
        raise KnowledgeHubError("{} exceeds provider adapter budget".format(key))
    return value


def _acl(row: Mapping[str, Any]) -> Sequence[str]:
    value = row.get("acl", [])
    if value is None:
        return []
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KnowledgeHubError("provider ACL must be a sequence")
    return [str(item) for item in value][:64]


def github_object(row: Mapping[str, Any]) -> Dict[str, Any]:
    repo = _text(row, "repository", 512)
    path = _text(row, "path", 2048)
    sha = _text(row, "sha", 128)
    if not repo or not path or not sha:
        raise KnowledgeHubError("GitHub object requires repository/path/sha")
    return {
        "object_id": "{}:{}".format(repo, path),
        "version": sha,
        "source_uri": "github://{}/{}@{}".format(repo, path, sha),
        "body": _text(row, "body", 256 * 1024),
        "content_type": _text(row, "content_type", 128) or "text/plain",
        "visibility": _text(row, "visibility", 128) or "team-internal",
        "acl": list(_acl(row)),
        "disposition": "reference-only",
        "tombstone": bool(row.get("deleted", False)),
        "observed_at": _text(row, "observed_at", 128),
    }


def feishu_object(row: Mapping[str, Any]) -> Dict[str, Any]:
    token = _text(row, "document_token", 512)
    version = _text(row, "version", 512)
    if not token or not version:
        raise KnowledgeHubError("Feishu object requires document_token/version")
    return {
        "object_id": token,
        "version": version,
        "source_uri": "feishu://{}".format(token),
        "body": _text(row, "text", 256 * 1024),
        "content_type": "text/markdown",
        "visibility": _text(row, "visibility", 128) or "team-internal",
        "acl": list(_acl(row)),
        "disposition": "summary-only",
        "tombstone": bool(row.get("deleted", False)),
        "observed_at": _text(row, "updated_at", 128),
    }


def tapd_object(row: Mapping[str, Any]) -> Dict[str, Any]:
    object_id = _text(row, "id", 512)
    updated_at = _text(row, "updated_at", 128)
    if not object_id or not updated_at:
        raise KnowledgeHubError("TAPD object requires id/updated_at")
    return {
        "object_id": object_id,
        "version": updated_at,
        "source_uri": "tapd://{}".format(object_id),
        "body": _text(row, "description", 256 * 1024),
        "content_type": "text/plain",
        "visibility": _text(row, "visibility", 128) or "team-internal",
        "acl": list(_acl(row)),
        "disposition": "reference-only",
        "tombstone": bool(row.get("deleted", False)),
        "observed_at": updated_at,
    }


def ci_object(row: Mapping[str, Any]) -> Dict[str, Any]:
    run_id = _text(row, "run_id", 256)
    artifact_id = _text(row, "artifact_id", 256)
    if not run_id:
        raise KnowledgeHubError("CI object requires run_id")
    object_id = "{}:{}".format(run_id, artifact_id or "run")
    return {
        "object_id": object_id,
        "version": _text(row, "sha", 128) or run_id,
        "source_uri": "ci://{}".format(object_id),
        "body": "",
        "content_type": "application/vnd.knowledge-hub.artifact-ref",
        "visibility": _text(row, "visibility", 128) or "team-internal",
        "acl": list(_acl(row)),
        "disposition": "artifact-ref",
        "tombstone": bool(row.get("deleted", False)),
        "observed_at": _text(row, "updated_at", 128),
    }


def google_drive_object(row: Mapping[str, Any]) -> Dict[str, Any]:
    file_id = _text(row, "file_id", 512)
    version = _text(row, "version", 512)
    if not file_id or not version:
        raise KnowledgeHubError("Google Drive object requires file_id/version")
    return {
        "object_id": file_id,
        "version": version,
        "source_uri": "gdrive://{}".format(file_id),
        "body": _text(row, "text", 256 * 1024),
        "content_type": _text(row, "mime_type", 128) or "text/plain",
        "visibility": _text(row, "visibility", 128) or "team-internal",
        "acl": list(_acl(row)),
        "disposition": "summary-only",
        "tombstone": bool(row.get("trashed", False)),
        "observed_at": _text(row, "modified_time", 128),
    }
