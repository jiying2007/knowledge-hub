"""Candidate policy shared by every terminal Provider write."""

from .common import KnowledgeHubError, load_json
from .schemas import validate_instance

LOW_RISK_KINDS = {"validation", "debug-record", "runbook", "audit", "codex-session", "project-archive", "external-source-note"}
SAFE_METADATA = {"title", "summary_zh", "tags", "primary_language", "source_language", "translation_status", "terminology_status"}


def checked_archive_policy(root, kind=None):
    value = load_json(root / "registry/provider-archive-policy.json", {})
    owners = load_json(root / "registry/owners.json", {}).get("owners", [])
    if (validate_instance(root, "provider-archive-policy-v1", value)["status"] != "pass"
            or value.get("enabled") is not True or value.get("mode") != "candidate-only"
            or value.get("owner_id") not in {row.get("id") for row in owners}
            or kind is not None and (kind not in LOW_RISK_KINDS or kind not in value["allowed_kinds"])):
        raise KnowledgeHubError("POLICY_DENIED")
    return value


def metadata_tags(metadata, kind):
    tags = metadata.get("tags", [])
    if (not isinstance(tags, list) or len(tags) > 32
            or any(not isinstance(tag, str) or not tag.strip() or len(tag) > 128 for tag in tags)
            or not isinstance(metadata.get("summary_zh", ""), str) or len(metadata.get("summary_zh", "")) > 1000):
        raise KnowledgeHubError("SOURCE_REJECTED")
    return tuple(dict.fromkeys(["provider-archive", kind] + tags))
