"""Shared review-risk classification for AI-first maintenance."""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, Mapping

from .common import KnowledgeHubError


DEFAULT_POLICY: Dict[str, Any] = {
    "default_class": "ordinary",
    "classes": {
        "ordinary": {
            "stale_severity": "warning",
            "ai_first_action": "auto-triage",
        }
    },
    "rules": [],
}


def load_review_risk_policy(root: pathlib.Path) -> Dict[str, Any]:
    path = root / "registry/review-risk-policy.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("cannot load review risk policy: {}".format(exc)) from exc
    if not isinstance(payload, Mapping):
        raise KnowledgeHubError("review risk policy must be an object")
    return dict(payload)


def classify_review_risk(policy: Mapping[str, Any], path_value: object) -> Dict[str, str]:
    path_text = str(path_value or "")
    selected = str(policy.get("default_class", "ordinary"))
    for rule in policy.get("rules", []):
        if not isinstance(rule, Mapping):
            continue
        if str(rule.get("path", "")) == path_text and path_text:
            selected = str(rule.get("review_class", selected))
            break
        prefix = str(rule.get("path_prefix", ""))
        if prefix and path_text.startswith(prefix):
            selected = str(rule.get("review_class", selected))
            break
    classes = policy.get("classes", {})
    details = classes.get(selected, {}) if isinstance(classes, Mapping) else {}
    return {
        "review_class": selected,
        "stale_severity": str(details.get("stale_severity", "warning")),
        "ai_first_action": str(details.get("ai_first_action", "auto-triage")),
    }
