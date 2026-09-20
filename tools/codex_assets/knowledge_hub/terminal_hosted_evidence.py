"""Hosted GitHub evidence checks used by terminal closure."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
from typing import Any, Dict, List, Mapping, Tuple

from .common import KnowledgeHubError


def _load_object(path: pathlib.Path, label: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError(
            "{} is unavailable or invalid".format(label)
        ) from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be a JSON object".format(label))
    return dict(value)


def _inventory_identity(
    config: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> Tuple[bool, bool]:
    current_sha = (
        os.environ.get("KNOWLEDGE_SOURCE_REVISION", "").strip()
        or os.environ.get("GITHUB_SHA", "").strip()
    )
    current_repository = (
        os.environ.get("KNOWLEDGE_GITHUB_REPOSITORY", "").strip()
        or os.environ.get("GITHUB_REPOSITORY", "").strip()
    )
    revision_matches = True
    repository_matches = True
    if (
        bool(config.get("require_current_github_sha_when_available", False))
        and current_sha
    ):
        revision_matches = (
            str(evidence.get("source_revision", "")) == current_sha
        )
    if (
        bool(
            config.get(
                "require_current_github_repository_when_available",
                False,
            )
        )
        and current_repository
    ):
        repository_matches = (
            str(evidence.get("repository", "")) == current_repository
        )
    return revision_matches, repository_matches


def default_branch_protection_state(
    root: pathlib.Path,
    policy: Mapping[str, Any],
) -> Dict[str, Any]:
    rules = policy.get("rules", {})
    if not isinstance(rules, Mapping):
        raise KnowledgeHubError("terminal rules policy must be an object")
    required = bool(rules.get("default_branch_protection_required", False))
    branch = str(rules.get("default_branch", "master")).strip()
    if not required:
        return {
            "required": False,
            "status": "pass",
            "branch": branch,
            "owner": "repository-admin",
            "reason": "",
        }
    if not branch:
        raise KnowledgeHubError("terminal default branch name is missing")
    config = policy.get("branch_gc", {})
    if not isinstance(config, Mapping):
        raise KnowledgeHubError("branch_gc terminal policy must be an object")
    evidence_path = str(config.get("evidence", "")).strip()
    if not evidence_path:
        raise KnowledgeHubError("branch_gc evidence is missing")
    try:
        evidence = _load_object(
            root / evidence_path,
            "remote branch inventory",
        )
    except KnowledgeHubError:
        return {
            "required": True,
            "status": "blocked",
            "branch": branch,
            "owner": "repository-admin",
            "protected": False,
            "protection_observed": False,
            "reason": "fresh-remote-branch-inventory-missing",
            "snapshot": evidence_path,
        }
    return _protection_result(config, evidence, branch, evidence_path)


def _protection_result(
    config: Mapping[str, Any],
    evidence: Mapping[str, Any],
    branch: str,
    evidence_path: str,
) -> Dict[str, Any]:
    revision_matches, repository_matches = _inventory_identity(
        config,
        evidence,
    )
    snapshot_branch = str(evidence.get("default_branch", ""))
    present = evidence.get("default_branch_present") is True
    observed = evidence.get("default_branch_protection_observed") is True
    protected = evidence.get("default_branch_protected") is True
    status = "pass"
    reason = ""
    if evidence.get("status") == "blocked":
        status, reason = "blocked", "remote-branch-inventory-unavailable"
    elif not revision_matches:
        status, reason = (
            "blocked",
            "default-branch-protection-revision-mismatch",
        )
    elif not repository_matches:
        status, reason = (
            "blocked",
            "default-branch-protection-repository-mismatch",
        )
    elif snapshot_branch != branch:
        status, reason = "blocked", "default-branch-identity-mismatch"
    elif not present:
        status, reason = "blocked", "default-branch-missing"
    elif not observed:
        status, reason = (
            "blocked",
            "default-branch-protection-evidence-missing",
        )
    elif not protected:
        status, reason = "needs-review", "default-branch-unprotected"
    return {
        "required": True,
        "status": status,
        "branch": branch,
        "owner": "repository-admin",
        "repository": str(evidence.get("repository", "")),
        "repository_matches_current_run": repository_matches,
        "source_revision": str(evidence.get("source_revision", "")),
        "revision_matches_current_run": revision_matches,
        "present": present,
        "protection_observed": observed,
        "protected": protected,
        "reason": reason,
        "snapshot": evidence_path,
    }


def _mcp_basic_reasons(
    evidence: Mapping[str, Any],
    revision_matches: bool,
    repository_matches: bool,
) -> List[str]:
    reasons: List[str] = []
    if evidence.get("schema_version") != (
        "knowledge-hub.mcp-conformance-evidence.v2"
    ):
        reasons.append("mcp-evidence-schema-invalid")
    if not revision_matches:
        reasons.append("mcp-evidence-revision-mismatch")
    if not repository_matches:
        reasons.append("mcp-evidence-repository-mismatch")
    if evidence.get("runner_environment") != "github-hosted":
        reasons.append("mcp-hosted-runner-not-proven")
    if int(evidence.get("github_run_id", 0) or 0) < 1:
        reasons.append("mcp-github-run-id-missing")
    if int(evidence.get("github_run_attempt", 0) or 0) < 1:
        reasons.append("mcp-github-run-attempt-missing")
    if evidence.get("profile_contract_passed") is not True:
        reasons.append("mcp-profile-contract-not-passing")
    if evidence.get("product_resource_read_smoke_passed") is not True:
        reasons.append("mcp-product-resource-smoke-not-passing")
    if evidence.get("expected_failure_baseline_used") is not False:
        reasons.append("mcp-expected-failure-baseline-forbidden")
    return reasons


def _mcp_runner_reasons(
    evidence: Mapping[str, Any],
    conformance_policy: Mapping[str, Any],
) -> List[str]:
    expected = conformance_policy.get("runner", {})
    observed = evidence.get("runner", {})
    if not isinstance(expected, Mapping) or not isinstance(observed, Mapping):
        return ["mcp-runner-contract-invalid"]
    reasons: List[str] = []
    if str(observed.get("package", "")) != str(expected.get("package", "")):
        reasons.append("mcp-runner-package-drift")
    if str(observed.get("version", "")) != str(expected.get("version", "")):
        reasons.append("mcp-runner-version-drift")
    if not str(observed.get("integrity", "")).strip():
        reasons.append("mcp-runner-integrity-missing")
    return reasons


def _mcp_scenario_reasons(
    evidence: Mapping[str, Any],
    expected_scenarios: Any,
) -> List[str]:
    reasons: List[str] = []
    observed_scenarios = evidence.get("hosted_official_scenarios", [])
    if (
        not isinstance(expected_scenarios, list)
        or observed_scenarios != expected_scenarios
    ):
        reasons.append("mcp-scenario-set-drift")
    rows = evidence.get("scenarios", [])
    if not isinstance(rows, list):
        return reasons + ["mcp-scenario-rows-invalid"]
    names = [
        str(row.get("scenario", ""))
        for row in rows
        if isinstance(row, Mapping)
    ]
    if names != expected_scenarios:
        reasons.append("mcp-scenario-row-order-drift")
    for row in rows:
        if not isinstance(row, Mapping):
            reasons.append("mcp-scenario-row-invalid")
            continue
        if row.get("profile_applicability_passed") is not True:
            reasons.append("mcp-scenario-applicability-failed")
        if int(row.get("applicable_failure_count", -1)) != 0:
            reasons.append("mcp-applicable-failure-present")
    return reasons


def _mcp_digest_matches(evidence: Mapping[str, Any]) -> Tuple[str, bool]:
    expected = str(evidence.get("result_sha256", ""))
    material = dict(evidence)
    material.pop("result_sha256", None)
    actual = hashlib.sha256(
        json.dumps(
            material,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return expected, expected == actual


def mcp_conformance_state(
    root: pathlib.Path,
    policy: Mapping[str, Any],
) -> Dict[str, Any]:
    config = policy.get("mcp_conformance", {})
    if not isinstance(config, Mapping):
        raise KnowledgeHubError(
            "mcp_conformance terminal policy must be an object"
        )
    if not bool(config.get("required", False)):
        return {"required": False, "status": "pass", "reason": ""}
    evidence_path = str(config.get("evidence", "")).strip()
    policy_path = str(config.get("policy", "")).strip()
    if not evidence_path or not policy_path:
        raise KnowledgeHubError(
            "mcp_conformance terminal policy is incomplete"
        )
    try:
        evidence = _load_object(
            root / evidence_path,
            "MCP conformance evidence",
        )
        conformance_policy = _load_object(
            root / policy_path,
            "MCP conformance policy",
        )
    except KnowledgeHubError:
        return {
            "required": True,
            "status": "blocked",
            "reason": "fresh-mcp-conformance-evidence-missing",
            "snapshot": evidence_path,
        }
    return _mcp_result(
        evidence,
        conformance_policy,
        config,
        evidence_path,
    )


def _mcp_result(
    evidence: Mapping[str, Any],
    conformance_policy: Mapping[str, Any],
    config: Mapping[str, Any],
    evidence_path: str,
) -> Dict[str, Any]:
    revision_matches, repository_matches = _inventory_identity(
        config,
        evidence,
    )
    reasons = _mcp_basic_reasons(
        evidence,
        revision_matches,
        repository_matches,
    )
    expected_scenarios = conformance_policy.get(
        "hosted_official_scenarios",
        [],
    )
    reasons.extend(_mcp_runner_reasons(evidence, conformance_policy))
    reasons.extend(_mcp_scenario_reasons(evidence, expected_scenarios))
    expected_digest, digest_matches = _mcp_digest_matches(evidence)
    if not digest_matches:
        reasons.append("mcp-result-digest-mismatch")
    reasons = list(dict.fromkeys(reasons))
    return {
        "required": True,
        "status": "pass" if not reasons else "blocked",
        "reason": reasons[0] if reasons else "",
        "reason_codes": reasons,
        "repository": str(evidence.get("repository", "")),
        "repository_matches_current_run": repository_matches,
        "source_revision": str(evidence.get("source_revision", "")),
        "revision_matches_current_run": revision_matches,
        "runner_environment": str(evidence.get("runner_environment", "")),
        "github_run_id": int(evidence.get("github_run_id", 0) or 0),
        "github_run_attempt": int(
            evidence.get("github_run_attempt", 0) or 0
        ),
        "profile_contract_passed": (
            evidence.get("profile_contract_passed") is True
        ),
        "result_sha256": expected_digest,
        "snapshot": evidence_path,
    }


def _hosting_status(
    evidence: Mapping[str, Any],
    revision_matches: bool,
    repository_matches: bool,
    expected_branch: str,
) -> Tuple[str, str]:
    if evidence.get("status") != "pass":
        return "blocked", "hosting-posture-capture-not-passing"
    if not revision_matches:
        return "blocked", "hosting-posture-revision-mismatch"
    if not repository_matches:
        return "blocked", "hosting-posture-repository-mismatch"
    private = evidence.get("repository_private") is True
    visibility = str(evidence.get("repository_visibility", ""))
    if not private or visibility != "private":
        return "needs-review", "repository-private-boundary-not-observed"
    if str(evidence.get("default_branch", "")) != expected_branch:
        return "blocked", "hosting-posture-default-branch-mismatch"
    return "pass", ""


def _hosting_drift(
    root: pathlib.Path,
    policy: Mapping[str, Any],
    *,
    private: bool,
) -> List[Dict[str, Any]]:
    external = policy.get("external_closure", {})
    source = (
        str(external.get("source", "")).strip()
        if isinstance(external, Mapping)
        else ""
    )
    if not source:
        return []
    platform = _load_object(root / source, "external closure registry")
    rows = platform.get("external_closure_gaps", [])
    if not isinstance(rows, list):
        return []
    matches = [
        row
        for row in rows
        if isinstance(row, Mapping)
        and row.get("id") == "repository-private-boundary"
    ]
    if len(matches) != 1:
        return []
    canonical_status = str(matches[0].get("status", "open"))
    if private and canonical_status != "closed":
        return [{
            "id": "repository-private-boundary",
            "type": "live-fact-ahead-of-canonical",
            "live_private": True,
            "canonical_status": canonical_status,
            "recommended_action": "machine-ratchet-candidate",
        }]
    if (not private) and canonical_status == "closed":
        return [{
            "id": "repository-private-boundary",
            "type": "hosting-regression",
            "live_private": False,
            "canonical_status": canonical_status,
            "recommended_action": "external-administration",
        }]
    return []


def hosting_posture_state(
    root: pathlib.Path,
    policy: Mapping[str, Any],
) -> Dict[str, Any]:
    config = policy.get("hosting_posture", {})
    if not isinstance(config, Mapping):
        raise KnowledgeHubError(
            "hosting_posture terminal policy must be an object"
        )
    if not bool(config.get("required", False)):
        return {"required": False, "status": "pass", "fact_drift": []}
    evidence_path = str(config.get("evidence", "")).strip()
    if not evidence_path:
        raise KnowledgeHubError("hosting_posture evidence path is missing")
    try:
        evidence = _load_object(
            root / evidence_path,
            "hosting posture evidence",
        )
    except KnowledgeHubError:
        return {
            "required": True,
            "status": "blocked",
            "reason": "fresh-hosting-posture-missing",
            "fact_drift": [],
            "snapshot": evidence_path,
        }
    return _hosting_result(root, policy, config, evidence, evidence_path)


def _hosting_result(
    root: pathlib.Path,
    policy: Mapping[str, Any],
    config: Mapping[str, Any],
    evidence: Mapping[str, Any],
    evidence_path: str,
) -> Dict[str, Any]:
    revision_matches, repository_matches = _inventory_identity(
        config,
        evidence,
    )
    rules = policy.get("rules", {})
    expected_branch = (
        str(rules.get("default_branch", "master")).strip()
        if isinstance(rules, Mapping)
        else "master"
    )
    status, reason = _hosting_status(
        evidence,
        revision_matches,
        repository_matches,
        expected_branch,
    )
    private = evidence.get("repository_private") is True
    return {
        "required": True,
        "status": status,
        "reason": reason,
        "repository": str(evidence.get("repository", "")),
        "repository_matches_current_run": repository_matches,
        "source_revision": str(evidence.get("source_revision", "")),
        "revision_matches_current_run": revision_matches,
        "repository_private": private,
        "repository_visibility": str(
            evidence.get("repository_visibility", "")
        ),
        "default_branch": str(evidence.get("default_branch", "")),
        "default_branch_protected": (
            evidence.get("default_branch_protected") is True
        ),
        "rulesets_capability": (
            dict(evidence.get("rulesets_capability", {}))
            if isinstance(evidence.get("rulesets_capability"), Mapping)
            else {}
        ),
        "fact_drift": _hosting_drift(
            root,
            policy,
            private=private,
        ),
        "snapshot": evidence_path,
    }
