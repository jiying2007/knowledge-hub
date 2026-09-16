"""Fail-closed review qualification for read-only Operator provider candidates."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Mapping, Sequence

REVIEW_FIELDS = {"source_refs", "validation_refs", "artifact_refs", "release_ref"}
MAX_REVIEW_CANDIDATES = 400

_EXPECTED_KINDS = {
    "source_refs": {"github-source-revision"},
    "validation_refs": {"github-workflow-run"},
    "artifact_refs": {"github-release-asset", "github-actions-artifact"},
    "release_ref": {"github-release"},
}
_EXPECTED_OPERATIONS = {
    "source_refs": "inspect-repository-source",
    "validation_refs": "list-workflow-runs",
    "artifact_refs": "list-release-assets-and-actions-artifacts",
    "release_ref": "list-releases-and-tags",
}
_EXPECTED_REF_PREFIXES = {
    "github-source-revision": "github://",
    "github-workflow-run": "github-actions://",
    "github-release-asset": "github-release-asset://",
    "github-actions-artifact": "github-actions-artifact://",
    "github-release": "github-release://",
}


def _details(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
    value = candidate.get("details", {})
    return value if isinstance(value, Mapping) else {}


def _upstream_contract_reasons(execution: Mapping[str, Any]) -> List[str]:
    reasons = []
    if execution.get("schema_version") != 1:
        reasons.append("upstream-schema-version-invalid")
    if str(execution.get("projection", "")) != "knowledge-operator-github-provider-v1":
        reasons.append("upstream-projection-identity-invalid")
    if str(execution.get("status", "")) not in {"pass", "error"}:
        reasons.append("upstream-status-invalid")
    if execution.get("read_only") is not True:
        reasons.append("upstream-not-read-only")
    if execution.get("canonical_write_performed") is not False:
        reasons.append("upstream-canonical-write-state-invalid")
    if execution.get("automatic_binding_enabled") is not False:
        reasons.append("upstream-automatic-binding-state-invalid")
    error_count = execution.get("error_count")
    if not isinstance(error_count, int) or isinstance(error_count, bool) or error_count < 0:
        reasons.append("upstream-error-count-invalid")
    if not isinstance(execution.get("results", []), list):
        reasons.append("upstream-results-shape-invalid")
    return reasons


def _result_contract_reasons(result: Mapping[str, Any]) -> List[str]:
    reasons = []
    field = str(result.get("field", ""))
    if not str(result.get("project_id", "")):
        reasons.append("result-project-id-missing")
    if field not in REVIEW_FIELDS:
        reasons.append("result-field-invalid")
    if str(result.get("provider", "")) != "github":
        reasons.append("result-provider-not-github")
    if result.get("executed") is not True:
        reasons.append("result-not-executed")
    if result.get("read_only") is not True:
        reasons.append("result-not-read-only")
    if result.get("network_performed") is not True:
        reasons.append("result-network-state-invalid")
    if result.get("canonical_write_performed") is not False:
        reasons.append("result-canonical-write-state-invalid")
    if result.get("automatic_binding_enabled") is not False:
        reasons.append("result-automatic-binding-state-invalid")
    if not str(result.get("target", "")):
        reasons.append("result-target-missing")
    expected_operation = _EXPECTED_OPERATIONS.get(field)
    if expected_operation and str(result.get("operation", "")) != expected_operation:
        reasons.append("result-operation-does-not-match-field")
    candidates = result.get("candidates", [])
    if not isinstance(candidates, list):
        reasons.append("result-candidates-shape-invalid")
    elif result.get("candidate_count") != len(candidates):
        reasons.append("result-candidate-count-mismatch")
    if candidates and str(result.get("status", "")) != "candidate-found":
        reasons.append("result-status-does-not-match-candidates")
    if not candidates and str(result.get("status", "")) != "no-candidate":
        reasons.append("result-status-does-not-match-candidates")
    return reasons


def _generic_reasons(candidate: Mapping[str, Any]) -> List[str]:
    reasons = []
    if str(candidate.get("provider", "")) != "github":
        reasons.append("provider-not-github")
    if candidate.get("provider_verified") is not True:
        reasons.append("provider-not-verified")
    if candidate.get("candidate_only") is not True:
        reasons.append("candidate-only-state-invalid")
    if candidate.get("eligible_for_binding") is not False:
        reasons.append("binding-state-not-false")
    kind = str(candidate.get("kind", ""))
    ref = str(candidate.get("ref", ""))
    if not kind:
        reasons.append("candidate-kind-missing")
    if not ref:
        reasons.append("candidate-ref-missing")
    elif kind in _EXPECTED_REF_PREFIXES and not ref.startswith(_EXPECTED_REF_PREFIXES[kind]):
        reasons.append("candidate-ref-scheme-mismatch")
    return reasons


def _source_reasons(candidate: Mapping[str, Any]) -> List[str]:
    details = _details(candidate)
    reasons = []
    if details.get("exact_identity") is not True:
        reasons.append("source-exact-identity-missing")
    if not str(details.get("commit_sha", "")):
        reasons.append("source-commit-sha-missing")
    if not str(details.get("repository", "")):
        reasons.append("source-repository-missing")
    return reasons


def _validation_reasons(candidate: Mapping[str, Any]) -> List[str]:
    details = _details(candidate)
    reasons = []
    if str(details.get("conclusion", "")) != "success":
        reasons.append("validation-not-successful")
    if not str(details.get("run_id", "")):
        reasons.append("validation-run-id-missing")
    if not str(details.get("head_sha", "")):
        reasons.append("validation-head-sha-missing")
    return reasons


def _artifact_reasons(candidate: Mapping[str, Any]) -> List[str]:
    details = _details(candidate)
    kind = str(candidate.get("kind", ""))
    reasons = []
    if not str(details.get("digest", "")):
        reasons.append("artifact-digest-missing")
    if kind == "github-actions-artifact":
        if details.get("expired") is not False:
            reasons.append("actions-artifact-expiry-state-invalid")
        if not str(details.get("artifact_id", "")):
            reasons.append("actions-artifact-id-missing")
    elif kind == "github-release-asset":
        if not str(details.get("asset_id", "")):
            reasons.append("release-asset-id-missing")
        if bool(details.get("release_draft", False)):
            reasons.append("release-asset-from-draft")
        if bool(details.get("release_prerelease", False)):
            reasons.append("release-asset-from-prerelease")
    return reasons


def _release_reasons(candidate: Mapping[str, Any]) -> List[str]:
    details = _details(candidate)
    reasons = []
    if details.get("meets_immutable_release_policy") is not True:
        reasons.append("immutable-release-policy-not-met")
    if details.get("immutable") is not True:
        reasons.append("release-not-immutable")
    if bool(details.get("draft", False)):
        reasons.append("release-is-draft")
    if bool(details.get("prerelease", False)):
        reasons.append("release-is-prerelease")
    if not str(details.get("release_id", "")):
        reasons.append("release-id-missing")
    if not str(details.get("tag_name", "")):
        reasons.append("release-tag-missing")
    return reasons


def _field_reasons(field: str, candidate: Mapping[str, Any]) -> List[str]:
    kind = str(candidate.get("kind", ""))
    if field not in REVIEW_FIELDS:
        return ["unsupported-evidence-field"]
    if kind not in _EXPECTED_KINDS[field]:
        return ["candidate-kind-does-not-match-field"]
    if field == "source_refs":
        return _source_reasons(candidate)
    if field == "validation_refs":
        return _validation_reasons(candidate)
    if field == "artifact_refs":
        return _artifact_reasons(candidate)
    return _release_reasons(candidate)


def _qualification_row(
    *,
    result: Mapping[str, Any],
    candidate: Mapping[str, Any],
    upstream_reasons: Sequence[str],
    result_reasons: Sequence[str],
) -> Dict[str, Any]:
    field = str(result.get("field", ""))
    reasons = list(upstream_reasons)
    reasons.extend(result_reasons)
    reasons.extend(_generic_reasons(candidate))
    reasons.extend(_field_reasons(field, candidate))
    reasons = list(dict.fromkeys(reasons))
    reviewable = not reasons
    return {
        "project_id": str(result.get("project_id", "")),
        "field": field,
        "provider": str(result.get("provider", "")),
        "operation": str(result.get("operation", "")),
        "target": str(result.get("target", "")),
        "kind": str(candidate.get("kind", "")),
        "ref": str(candidate.get("ref", "")),
        "qualification_status": "reviewable" if reviewable else "rejected",
        "review_eligible": reviewable,
        "requires_governed_review": True,
        "candidate_only": True,
        "eligible_for_binding": False,
        "reason_codes": ["review-floor-met"] if reviewable else reasons,
        "candidate": dict(candidate),
    }


def qualify_provider_projection(execution: Mapping[str, Any]) -> Dict[str, Any]:
    """Classify provider candidates for governed review without binding evidence."""

    upstream_reasons = _upstream_contract_reasons(execution)
    rows: List[Dict[str, Any]] = []
    result_contract_error_count = 0
    truncated = False
    raw_results = execution.get("results", [])
    results = raw_results if isinstance(raw_results, list) else []
    for result in results:
        if not isinstance(result, Mapping):
            result_contract_error_count += 1
            continue
        result_reasons = _result_contract_reasons(result)
        if result_reasons:
            result_contract_error_count += 1
        raw_candidates = result.get("candidates", [])
        candidates = raw_candidates if isinstance(raw_candidates, list) else []
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                result_contract_error_count += 1
                continue
            if len(rows) >= MAX_REVIEW_CANDIDATES:
                truncated = True
                break
            rows.append(
                _qualification_row(
                    result=result,
                    candidate=candidate,
                    upstream_reasons=upstream_reasons,
                    result_reasons=result_reasons,
                )
            )
        if truncated:
            break
    counts = Counter(str(row.get("qualification_status", "")) for row in rows)
    raw_error_count = execution.get("error_count", 0)
    source_error_count = (
        raw_error_count
        if isinstance(raw_error_count, int)
        and not isinstance(raw_error_count, bool)
        and raw_error_count >= 0
        else 1
    )
    if upstream_reasons or source_error_count or result_contract_error_count:
        status = "upstream-error"
    elif counts.get("reviewable", 0):
        status = "needs-governed-review"
    else:
        status = "no-reviewable-candidate"
    return {
        "schema_version": 1,
        "projection": "knowledge-operator-candidate-qualification-v1",
        "status": status,
        "read_only": True,
        "network_performed": False,
        "source_projection_network_performed": bool(execution.get("network_performed", False)),
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "candidate_only": True,
        "eligible_for_binding": False,
        "requires_governed_review": True,
        "candidate_count": len(rows),
        "reviewable_count": counts.get("reviewable", 0),
        "rejected_count": counts.get("rejected", 0),
        "truncated": truncated,
        "source_error_count": source_error_count,
        "result_contract_error_count": result_contract_error_count,
        "upstream_contract_reason_codes": upstream_reasons,
        "rows": rows,
    }
