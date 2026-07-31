"""Trust-bound execution evidence for remote and offsite restore drills."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
from typing import Any, Dict, Mapping


def expected_repository_from_registry(root: pathlib.Path) -> str:
    """Resolve the trusted GitHub identity from the governed repository registry."""

    try:
        payload = json.loads(
            (root / "registry/repositories.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return ""
    for row in payload.get("repositories", []):
        if (
            isinstance(row, Mapping)
            and row.get("repo_id") == "knowledge-hub"
            and row.get("status") == "registered"
        ):
            return str(row.get("remote_key", ""))
    return ""


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _environment_values(environment: Mapping[str, str] | None) -> Mapping[str, str]:
    return environment if environment is not None else os.environ


def execution_environment_evidence(
    source_mode: str,
    source_revision: str,
    *,
    expected_repository: str,
    environment: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    """Create fail-closed evidence; local variables alone never prove offsite."""

    values = _environment_values(environment)
    github_actions = values.get("GITHUB_ACTIONS", "").lower() == "true"
    repository = values.get("GITHUB_REPOSITORY", "")
    revision = values.get("GITHUB_SHA", "")
    event = values.get("GITHUB_EVENT_NAME", "")
    ref = values.get("GITHUB_REF", "")
    run_id = values.get("GITHUB_RUN_ID", "")
    run_attempt = values.get("GITHUB_RUN_ATTEMPT", "")
    workflow_ref = values.get("GITHUB_WORKFLOW_REF", "")
    workflow_sha = values.get("GITHUB_WORKFLOW_SHA", "")
    runner_environment = values.get("RUNNER_ENVIRONMENT", "")
    run_identity_ready = bool(
        run_id.isdigit()
        and run_attempt.isdigit()
        and workflow_ref.startswith(repository + "/.github/workflows/")
        and workflow_sha == revision
    )
    remote_checkout = bool(
        source_mode == "head"
        and github_actions
        and repository == expected_repository
        and revision == source_revision
        and run_identity_ready
    )
    remote_published = bool(
        remote_checkout
        and event in {"push", "schedule", "workflow_dispatch"}
        and ref.startswith(("refs/heads/", "refs/tags/"))
    )
    offsite = bool(
        remote_checkout
        and runner_environment == "github-hosted"
        and run_identity_ready
    )
    payload: Dict[str, Any] = {
        "provider": "github-actions" if github_actions else "local",
        "repository": repository,
        "expected_repository": expected_repository,
        "revision": revision,
        "event": event,
        "ref": ref,
        "runner_environment": runner_environment,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "workflow_ref": workflow_ref,
        "workflow_sha": workflow_sha,
        "remote_checkout_verified": remote_checkout,
        "remote_published_ref_verified": remote_published,
        "offsite_environment_verified": offsite,
        "trust_contract": "github-hosted-matching-revision-current-run-v1",
    }
    payload["evidence_sha256"] = _canonical_sha256(payload)
    return payload


def evidence_matches_current_execution(
    evidence: Mapping[str, Any],
    source_revision: str,
    *,
    expected_repository: str,
    environment: Mapping[str, str] | None = None,
) -> bool:
    """Require the consumer to run in the same trusted execution as the producer."""

    digest = str(evidence.get("evidence_sha256", ""))
    unsigned = dict(evidence)
    unsigned.pop("evidence_sha256", None)
    if digest != _canonical_sha256(unsigned):
        return False
    current = execution_environment_evidence(
        "head",
        source_revision,
        expected_repository=expected_repository,
        environment=environment,
    )
    binding_fields = (
        "provider",
        "repository",
        "revision",
        "run_id",
        "run_attempt",
        "workflow_ref",
        "workflow_sha",
    )
    return bool(
        evidence.get("offsite_environment_verified") is True
        and all(evidence.get(field) == current.get(field) for field in binding_fields)
    )
