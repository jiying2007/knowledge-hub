"""P5 principal authorization, trust classification, and repository posture.

This module is deliberately policy-only. It never grants canonical write authority,
performs network access, or treats repository metadata as a substitute for source ACLs.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

from .common import KnowledgeHubError

MAX_ID_CHARS = 256
MAX_GROUPS = 64
READ_OPERATIONS = {"read", "search", "context", "evidence"}
TRUST_CLASSES = {
    "canonical-trusted",
    "reviewed-external",
    "untrusted-external",
    "personal",
    "quarantine",
}
_INJECTION_PATTERNS = (
    re.compile(r"\bignore\s+(?:all\s+)?previous\s+instructions\b", re.IGNORECASE),
    re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE),
    re.compile(r"\bdeveloper\s+message\b", re.IGNORECASE),
    re.compile(r"\btool\s+(?:call|invocation)\b", re.IGNORECASE),
    re.compile(r"\bexfiltrat(?:e|ion)\b", re.IGNORECASE),
)


def _text(value: Any, label: str, maximum: int = MAX_ID_CHARS) -> str:
    text = str(value or "").strip()
    if not text or len(text) > maximum:
        raise KnowledgeHubError("{} must be non-empty and bounded".format(label))
    return text


def _strings(value: Any, label: str, maximum: int = MAX_GROUPS) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KnowledgeHubError("{} must be a sequence".format(label))
    if len(value) > maximum:
        raise KnowledgeHubError("{} exceeds {} values".format(label, maximum))
    return tuple(_text(row, label) for row in value)


def principal_context(value: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("principal must be an object")
    principal_id = _text(value.get("principal_id"), "principal_id")
    organization_id = str(value.get("organization_id", "")).strip()
    if organization_id and len(organization_id) > MAX_ID_CHARS:
        raise KnowledgeHubError("organization_id is too long")
    agent_id = str(value.get("agent_id", "")).strip()
    if agent_id and len(agent_id) > MAX_ID_CHARS:
        raise KnowledgeHubError("agent_id is too long")
    return {
        "principal_id": principal_id,
        "organization_id": organization_id,
        "agent_id": agent_id,
        "groups": list(_strings(value.get("groups", ()), "groups")),
        "scopes": list(_strings(value.get("scopes", ()), "scopes")),
        "delegated_by": str(value.get("delegated_by", ""))[:MAX_ID_CHARS],
        "purpose": str(value.get("purpose", ""))[:MAX_ID_CHARS],
    }


def _source_acl(item: Mapping[str, Any]) -> Tuple[str, ...]:
    direct = item.get("acl")
    if direct is not None:
        return _strings(direct, "item acl")
    source = item.get("source", {})
    if isinstance(source, Mapping) and source.get("acl") is not None:
        return _strings(source.get("acl"), "source acl")
    return ()


def _scope_match(item: Mapping[str, Any], scopes: Sequence[str]) -> bool:
    if not scopes:
        return True
    domain = str(item.get("domain", "")).rstrip("/")
    path = str(item.get("path", "")).rstrip("/")
    for raw in scopes:
        scope = str(raw).strip().rstrip("/")
        if not scope:
            continue
        if domain == scope or domain.startswith(scope + "/"):
            return True
        if path == scope or path.startswith(scope + "/"):
            return True
    return False


def trust_class(item: Mapping[str, Any]) -> str:
    visibility = str(item.get("visibility", ""))
    if visibility == "personal-local":
        return "personal"
    status = str(item.get("status", ""))
    if status in {"rejected", "archived"}:
        return "quarantine"
    kind = str(item.get("kind", ""))
    source = item.get("source", {})
    source_type = str(source.get("type", "")) if isinstance(source, Mapping) else ""
    external = kind == "external-source-note" or source_type in {
        "external",
        "connector",
        "web",
        "import",
    }
    if external:
        reviewed = (
            str(item.get("content_review_status", "")) == "accepted"
            and str(item.get("evidence_validation_status", "")) == "verified"
        )
        return "reviewed-external" if reviewed else "untrusted-external"
    return "canonical-trusted"


def authorize_item(
    item: Mapping[str, Any],
    principal: Mapping[str, Any],
    *,
    operation: str = "read",
    agent_scopes: Sequence[str] = (),
) -> Dict[str, Any]:
    principal_value = principal_context(principal)
    operation = str(operation).strip().lower()
    if operation not in READ_OPERATIONS:
        return {
            "status": "blocked",
            "authorized": False,
            "reason": "unsupported-or-write-operation",
            "trust_class": trust_class(item),
        }
    if not _scope_match(item, agent_scopes):
        return {
            "status": "blocked",
            "authorized": False,
            "reason": "outside-agent-scope",
            "trust_class": trust_class(item),
        }
    visibility = str(item.get("visibility", ""))
    if visibility == "personal-local":
        owner = str(item.get("owner", "")).strip()
        if principal_value["principal_id"] != owner:
            return {
                "status": "blocked",
                "authorized": False,
                "reason": "personal-owner-mismatch",
                "trust_class": "personal",
            }
    acl = set(_source_acl(item))
    if acl:
        subjects: Set[str] = {
            principal_value["principal_id"],
            *principal_value["groups"],
        }
        if principal_value["organization_id"]:
            subjects.add("org:" + principal_value["organization_id"])
        if not subjects.intersection(acl):
            return {
                "status": "blocked",
                "authorized": False,
                "reason": "source-acl-denied",
                "trust_class": trust_class(item),
            }
    return {
        "status": "pass",
        "authorized": True,
        "reason": "" if acl else "legacy-team-default",
        "trust_class": trust_class(item),
        "acl_explicit": bool(acl),
    }


def instruction_risk(text: str, *, item_trust_class: str) -> Dict[str, Any]:
    if item_trust_class not in TRUST_CLASSES:
        raise KnowledgeHubError("unknown trust class")
    bounded = str(text or "")
    if len(bounded) > 1024 * 1024:
        raise KnowledgeHubError("content exceeds instruction-risk budget")
    signals = sorted(
        {
            pattern.pattern
            for pattern in _INJECTION_PATTERNS
            if pattern.search(bounded)
        }
    )
    instruction_authority = item_trust_class == "canonical-trusted"
    if item_trust_class in {"reviewed-external", "untrusted-external", "quarantine"}:
        instruction_authority = False
    return {
        "schema_version": "knowledge-hub.instruction-risk.v1",
        "trust_class": item_trust_class,
        "signals": signals,
        "signal_count": len(signals),
        "data_only": not instruction_authority,
        "instruction_authority": instruction_authority,
        "content_sha256": hashlib.sha256(bounded.encode("utf-8")).hexdigest(),
    }


def repository_posture(
    observed: Mapping[str, Any],
    target: Mapping[str, Any],
) -> Dict[str, Any]:
    if not isinstance(observed, Mapping) or not isinstance(target, Mapping):
        raise KnowledgeHubError("repository posture inputs must be objects")
    failures: List[str] = []
    if bool(target.get("private_required", False)) and not bool(observed.get("private", False)):
        failures.append("repository-must-be-private")
    if bool(target.get("protected_default_branch_required", False)) and not bool(
        observed.get("default_branch_protected", False)
    ):
        failures.append("default-branch-protection-required")
    required_checks = {
        str(value)
        for value in _strings(target.get("required_status_checks", ()), "required_status_checks")
    }
    actual_checks = {
        str(value)
        for value in _strings(observed.get("required_status_checks", ()), "observed checks")
    }
    missing_checks = sorted(required_checks - actual_checks)
    if missing_checks:
        failures.append("required-status-checks-missing")
    if bool(target.get("block_force_push", False)) and not bool(
        observed.get("force_push_blocked", False)
    ):
        failures.append("force-push-must-be-blocked")
    if bool(target.get("block_branch_deletion", False)) and not bool(
        observed.get("branch_deletion_blocked", False)
    ):
        failures.append("branch-deletion-must-be-blocked")
    if bool(target.get("require_pull_request", False)) and not bool(
        observed.get("pull_request_required", False)
    ):
        failures.append("pull-request-must-be-required")
    if bool(target.get("require_conversation_resolution", False)) and not bool(
        observed.get("conversation_resolution_required", False)
    ):
        failures.append("conversation-resolution-must-be-required")
    return {
        "schema_version": "knowledge-hub.repository-posture.v1",
        "status": "pass" if not failures else "blocked",
        "failures": failures,
        "missing_status_checks": missing_checks,
        "external_admin_action_required": bool(failures),
    }
