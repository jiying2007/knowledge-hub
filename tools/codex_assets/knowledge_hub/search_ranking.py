"""Pure path, lifecycle and preview rules used by search ranking."""

from __future__ import annotations

import re
from typing import Any, Mapping, Tuple


PRIVATE_IPV4_PATTERN = re.compile(
    r"(?<![0-9])(?:10(?:\.[0-9]{1,3}){3}|192\.168(?:\.[0-9]{1,3}){2}|"
    r"172\.(?:1[6-9]|2[0-9]|3[01])(?:\.[0-9]{1,3}){2})"
    r"(?::[0-9]{1,5})?(?![0-9])"
)


def path_priority(relative: str) -> Tuple[int, str]:
    normalized = relative.replace("\\", "/")
    if normalized == "README.md":
        return 100, "root-entry"
    if normalized.startswith("projects/") and any(
        part in normalized for part in ("/current/", "/decisions/", "/validation/")
    ):
        return 120, "project-canonical"
    if normalized.startswith("domains/embedded/") and any(
        part in normalized for part in ("/runbooks/", "/standards/", "/architecture/")
    ):
        return 115, "domain-canonical"
    prefix_scores = (
        ("projects/", "/archive/", 55, "project-archive"),
        ("governance/status/", "", 80, "governance-status"),
        ("governance/", "", 65, "governance"),
        ("indexes/", "", 35, "derived-index"),
        ("tools/", "", 20, "tooling"),
        ("artifacts/manifests/", "", 0, "historical-manifest"),
        ("registry/", "", -20, "registry-ledger"),
    )
    for prefix, required, score, reason in prefix_scores:
        if normalized.startswith(prefix) and (not required or required in normalized):
            return score, reason
    return 40, "body"


def status_priority(status: str) -> int:
    return {
        "active": 100,
        "reviewing": 55,
        "draft": 20,
        "personal": 0,
        "archived": -15,
        "superseded": -80,
        "rejected": -100,
    }.get(status, 0)


def is_historical_result(item: Mapping[str, Any], relative: str) -> bool:
    status = str(item.get("status", ""))
    if status in {
        "archived",
        "superseded",
        "rejected",
    }:
        return True
    # Provider captures reviewing candidates into an archive storage lane.
    # That location is not a historical lifecycle decision. Legacy provenance
    # and manually maintained archive documents retain the existing fallback.
    source = item.get("source") or {}
    candidate = (status in {"reviewing", "draft"} and isinstance(source, Mapping)
                 and source.get("type") == "provider-candidate-archive"
                 and item.get("promotion") == "none")
    return "/archive/" in relative and not candidate


def redact_internal_endpoints(value: str) -> Tuple[str, bool]:
    redacted = PRIVATE_IPV4_PATTERN.sub("[内部端点已脱敏]", value)
    return redacted, redacted != value
