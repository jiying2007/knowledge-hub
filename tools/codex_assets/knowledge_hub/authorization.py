"""Authorization and human-review form validation."""

from __future__ import annotations

import datetime as dt
import json
import pathlib
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .common import KnowledgeHubError, load_jsonl


def authorization_rows(root: pathlib.Path) -> List[Dict[str, Any]]:
    return load_jsonl(root / "registry" / "authorizations.jsonl")


def require_authorization(
    root: pathlib.Path,
    authorization_id: str,
    allowed_actions: Sequence[str],
    as_of: dt.date,
    scope_refs: Iterable[str],
) -> Dict[str, Any]:
    rows = [row for row in authorization_rows(root) if str(row.get("authorization_id", "")) == authorization_id]
    if len(rows) != 1:
        raise KnowledgeHubError("authorization_id must resolve to exactly one ledger row: {}".format(authorization_id))
    row = rows[0]
    if row.get("status") != "active":
        raise KnowledgeHubError("authorization is not active: {} ({})".format(authorization_id, row.get("status")))
    try:
        authorized_at = dt.date.fromisoformat(str(row.get("authorized_at", "")))
        expires_at = dt.date.fromisoformat(str(row.get("expires_at", "")))
    except ValueError as exc:
        raise KnowledgeHubError("authorization has invalid date fields: {}".format(authorization_id)) from exc
    if not (authorized_at <= as_of <= expires_at):
        raise KnowledgeHubError("authorization is outside its validity window: {}".format(authorization_id))
    row_actions = set(str(value) for value in row.get("allowed_actions", []))
    if not row_actions.intersection(allowed_actions):
        raise KnowledgeHubError(
            "authorization {} does not allow any of: {}".format(authorization_id, ", ".join(allowed_actions))
        )
    scope = str(row.get("scope", ""))
    normalized_refs = [str(value) for value in scope_refs if str(value)]
    if normalized_refs and not any(value in scope for value in normalized_refs):
        raise KnowledgeHubError(
            "authorization scope does not identify the requested item/path: {}".format(authorization_id)
        )
    return dict(row)


def load_review_form(path: pathlib.Path, item_id: str) -> Dict[str, Any]:
    if not path.exists():
        raise KnowledgeHubError("review form does not exist: {}".format(path))
    text = path.read_text(encoding="utf-8")
    rows: List[Mapping[str, Any]] = []
    if path.suffix == ".jsonl":
        for line_no, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise KnowledgeHubError("invalid review JSONL {}:{}".format(path, line_no)) from exc
            if isinstance(value, dict):
                rows.append(value)
    else:
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise KnowledgeHubError("invalid review JSON: {}".format(path)) from exc
        if isinstance(value, dict):
            rows = [value]
        elif isinstance(value, list):
            rows = [row for row in value if isinstance(row, dict)]
    matches = [dict(row) for row in rows if str(row.get("item_id", row.get("id", ""))) == item_id]
    if len(matches) != 1:
        raise KnowledgeHubError("review form must contain exactly one row for {}".format(item_id))
    row = matches[0]
    required = ("reviewed_by", "reviewed_at", "review_decision", "review_basis", "validation_refs", "authorization_id")
    missing = [field for field in required if row.get(field) in (None, "", [])]
    if missing:
        raise KnowledgeHubError("review form missing: {}".format(", ".join(missing)))
    if row["review_decision"] not in {"accept", "accept-active", "retire", "supersede", "reject"}:
        raise KnowledgeHubError("unsupported review_decision: {}".format(row["review_decision"]))
    try:
        dt.date.fromisoformat(str(row["reviewed_at"]))
    except ValueError as exc:
        raise KnowledgeHubError("reviewed_at must use YYYY-MM-DD") from exc
    if not isinstance(row.get("validation_refs"), list) or not all(str(value).strip() for value in row["validation_refs"]):
        raise KnowledgeHubError("review form validation_refs must be a non-empty list")
    return row
