"""Shared contracts for Knowledge Runtime v3.

This module contains only deterministic registry/configuration helpers. It does
not create a second authority source: canonical Markdown and registry items stay
authoritative and this runtime configuration only controls derived Agent views.
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Mapping

from .common import KnowledgeHubError, load_json

CONFIG_PATH = "registry/knowledge-runtime-v3.json"
MCP_PROTOCOL_VERSION = "2026-07-28"
A2A_PROTOCOL_VERSION = "1.0.0"
DEFAULT_AGENT = "knowledge-reader"
DEFAULT_PROFILE = "hybrid-engineering-v1"
FEEDBACK_OUTCOMES = {
    "accepted",
    "partially-useful",
    "wrong",
    "stale",
    "missing",
    "conflicting",
    "permission-denied",
}
MEMORY_LEVELS = {
    "working",
    "session",
    "episodic",
    "semantic",
    "procedural",
    "policy",
}


def config(root: pathlib.Path) -> Dict[str, Any]:
    value = load_json(root / CONFIG_PATH, None)
    if not isinstance(value, dict):
        raise KnowledgeHubError("missing or invalid {}".format(CONFIG_PATH))
    return value


def rows(root: pathlib.Path, key: str) -> List[Dict[str, Any]]:
    value = config(root).get(key, [])
    if not isinstance(value, list):
        raise KnowledgeHubError("runtime config {} must be a list".format(key))
    return [dict(row) for row in value if isinstance(row, Mapping)]


def agent_profile(
    root: pathlib.Path, agent_id: str = DEFAULT_AGENT
) -> Dict[str, Any]:
    for row in rows(root, "agents"):
        if str(row.get("id", "")) == agent_id:
            return row
    raise KnowledgeHubError("unknown agent profile: {}".format(agent_id))


def capability_catalog(root: pathlib.Path) -> Dict[str, Dict[str, Any]]:
    return {
        str(row["id"]): row
        for row in rows(root, "capabilities")
        if row.get("id")
    }


def require_capability(root: pathlib.Path, agent_id: str, capability: str) -> None:
    profile = agent_profile(root, agent_id)
    catalog = capability_catalog(root)
    if capability not in catalog:
        raise KnowledgeHubError("unknown capability: {}".format(capability))
    if capability not in {str(value) for value in profile.get("capabilities", [])}:
        raise KnowledgeHubError(
            "agent {} is not permitted to use {}".format(agent_id, capability)
        )


def retrieval_profile(
    root: pathlib.Path, profile_id: str = DEFAULT_PROFILE
) -> Dict[str, Any]:
    for row in rows(root, "retrieval_profiles"):
        if str(row.get("id", "")) != profile_id:
            continue
        weights = row.get("weights")
        if not isinstance(weights, Mapping):
            raise KnowledgeHubError("retrieval profile weights must be an object")
        required = {"lexical", "semantic", "authority", "freshness"}
        if set(weights) != required:
            raise KnowledgeHubError("retrieval profile weight contract mismatch")
        normalized = {key: float(weights[key]) for key in required}
        if any(value < 0 for value in normalized.values()):
            raise KnowledgeHubError("retrieval profile weights must not be negative")
        total = sum(normalized.values())
        if total <= 0:
            raise KnowledgeHubError("retrieval profile weights must be positive")
        row["weights"] = {
            key: normalized[key] / total for key in sorted(required)
        }
        return row
    raise KnowledgeHubError("unknown retrieval profile: {}".format(profile_id))
