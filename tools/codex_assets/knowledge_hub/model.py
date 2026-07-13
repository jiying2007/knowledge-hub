"""Registry item model validation and lifecycle rules."""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .common import KnowledgeHubError, normalize_relpath


ITEM_KINDS = {
    "standard",
    "runbook",
    "architecture",
    "decision",
    "project-current",
    "project-archive",
    "validation",
    "audit",
    "patent",
    "debug-record",
    "external-source-note",
    "owner-decision-worksheet",
    "patent-disclosure",
    "codex-session",
    "codex-workflow",
    "personal-note",
    "artifact-ref",
    "authorization",
    "automation-run",
}
ITEM_STATUSES = {"draft", "active", "reviewing", "archived", "superseded", "rejected", "personal"}
ITEM_SCOPES = {"team-general", "project-specific", "codex-memory-curation-governance"}
ITEM_VISIBILITIES = {"team-internal", "personal-local"}
ITEM_PROMOTIONS = {"none"}
REQUIRED_ITEM_FIELDS = {
    "id",
    "title",
    "kind",
    "domain",
    "path",
    "scope",
    "visibility",
    "status",
    "owner",
    "source",
    "review_after",
    "validation_refs",
    "review_status",
    "created_at",
    "updated_at",
    "promotion",
    "tags",
}
AI_ROLES = {"drafted", "summarized", "translated", "rewritten", "classified", "extracted"}
TERMINAL_STATUSES = {"archived", "superseded", "rejected"}


def _iso_date(value: Any, field: str) -> dt.date:
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError as exc:
        raise KnowledgeHubError("{} must use YYYY-MM-DD: {}".format(field, value)) from exc


def domain_root(domain: str) -> str:
    return domain.split("/", 1)[0]


def validate_item(item: Mapping[str, Any], existing_ids: Optional[Iterable[str]] = None) -> List[str]:
    """Return deterministic validation errors for one registry item."""

    errors: List[str] = []
    missing = sorted(field for field in REQUIRED_ITEM_FIELDS if item.get(field) in (None, "", []))
    errors.extend("missing {}".format(field) for field in missing)

    item_id = str(item.get("id", ""))
    if item_id and not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", item_id):
        errors.append("id must be a lowercase stable identifier")
    if existing_ids is not None and item_id in set(existing_ids):
        errors.append("duplicate id {}".format(item_id))

    kind = str(item.get("kind", ""))
    status = str(item.get("status", ""))
    scope = str(item.get("scope", ""))
    visibility = str(item.get("visibility", ""))
    promotion = str(item.get("promotion", ""))
    if kind and kind not in ITEM_KINDS:
        errors.append("invalid kind {}".format(kind))
    if status and status not in ITEM_STATUSES:
        errors.append("invalid status {}".format(status))
    if scope and scope not in ITEM_SCOPES:
        errors.append("invalid scope {}".format(scope))
    if visibility and visibility not in ITEM_VISIBILITIES:
        errors.append("invalid visibility {}".format(visibility))
    if promotion and promotion not in ITEM_PROMOTIONS:
        errors.append("invalid promotion {}".format(promotion))

    path = str(item.get("path", ""))
    if path:
        try:
            path = normalize_relpath(path)
        except KnowledgeHubError as exc:
            errors.append(str(exc))
    domain = str(item.get("domain", ""))
    root = domain_root(domain) if domain else ""
    if root not in {"root", "governance", "projects", "notes", "embedded", "patents", "codex"}:
        errors.append("invalid domain {}".format(domain))
    elif path:
        if root == "root" and path not in {"README.md", "AGENTS.md"}:
            errors.append("root domain must target README.md or AGENTS.md")
        if root == "projects" and not (domain.startswith("projects/") and (path.startswith(domain + "/") or path.startswith("artifacts/manifests/"))):
            errors.append("project domain/path mismatch")
        if root == "notes" and not (path.startswith("notes/") or path.startswith("artifacts/manifests/")):
            errors.append("notes domain/path mismatch")
        expected_roots = {"embedded": "domains/embedded/", "patents": "domains/patents/", "codex": "domains/codex/"}
        if root in expected_roots and not (path.startswith(expected_roots[root]) or path.startswith("artifacts/manifests/")):
            errors.append("{} domain/path mismatch".format(root))
        if root == "governance" and not path.startswith(
            ("governance/", "registry/", "indexes/", "tools/", "templates/", "docs/goals/", "artifacts/manifests/")
        ):
            errors.append("governance domain/path mismatch")

    if scope == "project-specific" and not domain.startswith("projects/"):
        errors.append("project-specific scope requires projects/<project> domain")
    if scope == "codex-memory-curation-governance" and domain != "codex":
        errors.append("codex memory scope requires codex domain")
    if status == "personal" and visibility != "personal-local":
        errors.append("personal status requires personal-local visibility")
    if visibility == "personal-local" and not path.startswith("notes/personal/"):
        errors.append("personal-local visibility requires notes/personal path")

    source = item.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    validation_refs = item.get("validation_refs")
    if not isinstance(validation_refs, list) or any(not str(value).strip() for value in validation_refs):
        errors.append("validation_refs must be a list of non-empty strings")
    if status in {"active", "reviewing"} and not validation_refs:
        errors.append("active/reviewing item requires validation_refs")
    tags = item.get("tags")
    if not isinstance(tags, list) or not tags or any(not str(value).strip() for value in tags):
        errors.append("tags must be a non-empty list")

    created = updated = None
    for field in ("created_at", "updated_at", "review_after"):
        if item.get(field):
            try:
                parsed = _iso_date(item[field], field)
                if field == "created_at":
                    created = parsed
                elif field == "updated_at":
                    updated = parsed
            except KnowledgeHubError as exc:
                errors.append(str(exc))
    if created and updated and updated < created:
        errors.append("updated_at must not precede created_at")

    if item.get("generated_by_ai"):
        for field in ("ai_role", "ai_model_or_tool", "ai_generated_at"):
            if not item.get(field):
                errors.append("AI-generated item missing {}".format(field))
        if item.get("ai_role") and item.get("ai_role") not in AI_ROLES:
            errors.append("invalid ai_role {}".format(item.get("ai_role")))
    return errors


def require_valid_item(item: Mapping[str, Any], existing_ids: Optional[Iterable[str]] = None) -> None:
    errors = validate_item(item, existing_ids=existing_ids)
    if errors:
        raise KnowledgeHubError("invalid registry item {}: {}".format(item.get("id", "<unknown>"), "; ".join(errors)))


def assert_transition(before: str, after: str) -> None:
    allowed = {
        "draft": {"reviewing", "archived", "rejected"},
        "reviewing": {"active", "archived", "rejected"},
        "active": {"archived", "superseded"},
        "personal": {"archived"},
        "archived": set(),
        "superseded": set(),
        "rejected": set(),
    }
    if after not in allowed.get(before, set()):
        raise KnowledgeHubError("unsupported lifecycle transition: {} -> {}".format(before, after))


def frontmatter_mirror(item: Mapping[str, Any]) -> Dict[str, Any]:
    keys = [
        "id",
        "title",
        "kind",
        "domain",
        "scope",
        "visibility",
        "status",
        "owner",
        "review_after",
        "review_status",
        "promotion",
        "tags",
        "generated_by_ai",
        "ai_role",
        "ai_model_or_tool",
        "ai_generated_at",
        "manual_validation_pending",
        "decision_owner",
        "summary_zh",
        "primary_language",
        "source_language",
        "translation_status",
        "terminology_status",
        "promotion_decision",
    ]
    return {key: item[key] for key in keys if key in item}
