"""Authorization and human-review form validation."""

from __future__ import annotations

import datetime as dt
import json
import pathlib
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .common import KnowledgeHubError, bytes_sha256, load_jsonl
from .review_attestation import (
    FORM_KIND as CONTENT_REVIEW_ATTESTATION,
    TARGET_DECISIONS,
    attestation_review_basis,
)


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
    if row.get("form_kind") != CONTENT_REVIEW_ATTESTATION:
        raise KnowledgeHubError(
            "unsupported review form kind; content-review-attestation is required"
        )
    required = ["reviewed_by", "reviewed_at", "review_decision", "review_basis", "validation_refs"]
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
    _validate_content_review_attestation(row)
    return row


def _validate_content_review_attestation(row: Mapping[str, Any]) -> None:
    required = (
        "schema_version",
        "attestation_id",
        "attestation_mode",
        "attested_by",
        "attested_at",
        "attestation_source_ref",
        "attestation_statement",
        "attestation_statement_sha256",
        "confirmation_token",
        "content_sha256",
        "expected_before_status",
        "target_status",
        "generated_by",
    )
    missing = [field for field in required if row.get(field) in (None, "", [])]
    if missing:
        raise KnowledgeHubError("content review attestation missing: {}".format(", ".join(missing)))
    if row.get("authorization_id") not in (None, "") or row.get("execution_authorization_embedded") is not False:
        raise KnowledgeHubError("content review attestation must not embed execution authorization")
    if row.get("schema_version") != 1:
        raise KnowledgeHubError("unsupported content review attestation schema_version")
    if row.get("generated_mechanically") is not True or row.get("generated_by") != "knowledge-review-attest":
        raise KnowledgeHubError("content review attestation must preserve mechanical generation provenance")
    mode = str(row.get("attestation_mode", ""))
    if mode not in {"human-reviewed", "human-directed-delegation"}:
        raise KnowledgeHubError("unsupported attestation_mode: {}".format(mode))
    target_status = str(row.get("target_status", ""))
    if target_status not in TARGET_DECISIONS:
        raise KnowledgeHubError("unsupported attestation target_status: {}".format(target_status))
    if row.get("review_decision") != TARGET_DECISIONS[target_status]:
        raise KnowledgeHubError("content review attestation decision does not match target_status")
    if target_status == "active" and mode != "human-reviewed":
        raise KnowledgeHubError("active promotion requires direct human-reviewed attestation")
    attested_by = str(row.get("attested_by", ""))
    if attested_by.lower() in {"ai", "automation", "codex", "script", "system", "unassigned", "unknown"}:
        raise KnowledgeHubError("content review attestation must identify a human attested_by")
    if len(attested_by) > 128 or any(character in attested_by for character in "\r\n\t"):
        raise KnowledgeHubError("content review attestation attested_by is invalid")
    expected_reviewer = (
        attested_by
        if mode == "human-reviewed"
        else "{}-via-codex-delegation".format(attested_by)
    )
    if row.get("reviewed_by") != expected_reviewer:
        raise KnowledgeHubError("content review attestation reviewer identity does not match its mode")
    if row.get("reviewed_at") != row.get("attested_at"):
        raise KnowledgeHubError("reviewed_at must match attested_at")
    try:
        dt.date.fromisoformat(str(row.get("attested_at", "")))
    except ValueError as exc:
        raise KnowledgeHubError("attested_at must use YYYY-MM-DD") from exc
    content_sha = str(row.get("content_sha256", ""))
    statement_sha = str(row.get("attestation_statement_sha256", ""))
    if len(content_sha) != 64 or any(character not in "0123456789abcdef" for character in content_sha):
        raise KnowledgeHubError("content review attestation content_sha256 is invalid")
    statement = str(row.get("attestation_statement", ""))
    source_ref = str(row.get("attestation_source_ref", ""))
    if len(statement) > 4096:
        raise KnowledgeHubError("content review attestation statement is too long")
    if len(source_ref) > 500 or any(character in source_ref for character in "\r\n\t"):
        raise KnowledgeHubError("content review attestation source ref is invalid")
    if bytes_sha256(statement.encode("utf-8")) != statement_sha:
        raise KnowledgeHubError("content review attestation statement SHA256 does not match")
    token = str(row.get("confirmation_token", ""))
    if (
        not token.startswith("KH-ATTEST-")
        or len(token) != 30
        or any(character not in "0123456789abcdef" for character in token[len("KH-ATTEST-"):])
    ):
        raise KnowledgeHubError("content review attestation confirmation token is invalid")
    if row.get("review_basis") != attestation_review_basis(mode, token, source_ref):
        raise KnowledgeHubError("content review attestation review_basis does not match its provenance")
    bindings = (
        str(row.get("item_id", "")),
        str(row.get("expected_before_status", "")),
        target_status,
        content_sha,
        token,
    )
    if any(value not in statement for value in bindings):
        raise KnowledgeHubError("content review attestation statement is missing exact packet bindings")
