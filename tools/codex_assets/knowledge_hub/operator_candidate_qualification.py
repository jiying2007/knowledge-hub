"""Fail-closed review qualification for read-only Operator provider candidates."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Mapping, Sequence

REVIEW_FIELDS = {"source_refs", "validation_refs", "artifact_refs", "release_ref"}
MAX_REVIEW_CANDIDATES = 400
MAX_PROVIDER_RESULTS = 20
MAX_PROVIDER_CANDIDATES_PER_RESULT = 20

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
_GIT_OBJECT_ID = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
_SHA256_DIGEST = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
_TARGET = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _details(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
    value = candidate.get("details", {})
    return value if isinstance(value, Mapping) else {}


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _upstream_contract_reasons(execution: Mapping[str, Any]) -> List[str]:
    reasons = []
    if execution.get("schema_version") != 1:
        reasons.append("upstream-schema-version-invalid")
    if str(execution.get("projection", "")) != "knowledge-operator-github-provider-v1":
        reasons.append("upstream-projection-identity-invalid")
    if execution.get("read_only") is not True:
        reasons.append("upstream-not-read-only")
    if execution.get("canonical_write_performed") is not False:
        reasons.append("upstream-canonical-write-state-invalid")
    if execution.get("automatic_binding_enabled") is not False:
        reasons.append("upstream-automatic-binding-state-invalid")

    count_fields = (
        "selected_query_count",
        "executed_query_count",
        "unsupported_query_count",
        "error_count",
    )
    counts = {}
    for field in count_fields:
        value = execution.get(field)
        if not _is_nonnegative_int(value):
            reasons.append("upstream-{}-invalid".format(field.replace("_", "-")))
        else:
            counts[field] = int(value)

    raw_results = execution.get("results", [])
    raw_unsupported = execution.get("unsupported", [])
    raw_errors = execution.get("errors", [])
    if not isinstance(raw_results, list):
        reasons.append("upstream-results-shape-invalid")
    if not isinstance(raw_unsupported, list):
        reasons.append("upstream-unsupported-shape-invalid")
    if not isinstance(raw_errors, list):
        reasons.append("upstream-errors-shape-invalid")

    selected = counts.get("selected_query_count")
    executed = counts.get("executed_query_count")
    unsupported_count = counts.get("unsupported_query_count")
    error_count = counts.get("error_count")
    if selected is not None and selected > MAX_PROVIDER_RESULTS:
        reasons.append("upstream-selected-query-limit-exceeded")
    if executed is not None and isinstance(raw_results, list) and executed != len(raw_results):
        reasons.append("upstream-executed-query-count-mismatch")
    if (
        unsupported_count is not None
        and isinstance(raw_unsupported, list)
        and unsupported_count != len(raw_unsupported)
    ):
        reasons.append("upstream-unsupported-query-count-mismatch")
    if error_count is not None and isinstance(raw_errors, list) and error_count != len(raw_errors):
        reasons.append("upstream-error-count-mismatch")
    if selected is not None and executed is not None and error_count is not None:
        if selected != executed + error_count:
            reasons.append("upstream-selected-query-accounting-mismatch")

    status = str(execution.get("status", ""))
    if error_count is not None:
        expected_status = "error" if error_count else "pass"
        if status != expected_status:
            reasons.append("upstream-status-error-count-mismatch")
    elif status not in {"pass", "error"}:
        reasons.append("upstream-status-invalid")

    network_performed = execution.get("network_performed")
    if not isinstance(network_performed, bool):
        reasons.append("upstream-network-state-invalid")
    elif selected is not None and network_performed is not bool(selected):
        reasons.append("upstream-network-selection-mismatch")
    return reasons


def _result_contract_reasons(result: Mapping[str, Any]) -> List[str]:
    reasons = []
    field = str(result.get("field", ""))
    target = str(result.get("target", ""))
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
    if not target:
        reasons.append("result-target-missing")
    elif not _TARGET.fullmatch(target):
        reasons.append("result-target-invalid")
    expected_operation = _EXPECTED_OPERATIONS.get(field)
    if expected_operation and str(result.get("operation", "")) != expected_operation:
        reasons.append("result-operation-does-not-match-field")
    candidates = result.get("candidates", [])
    if not isinstance(candidates, list):
        reasons.append("result-candidates-shape-invalid")
    else:
        if len(candidates) > MAX_PROVIDER_CANDIDATES_PER_RESULT:
            reasons.append("result-candidate-limit-exceeded")
        if result.get("candidate_count") != len(candidates):
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
    if str(candidate.get("provenance", "")) != "github-read-only-api":
        reasons.append("candidate-provenance-invalid")
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


def _source_reasons(candidate: Mapping[str, Any], target: str) -> List[str]:
    details = _details(candidate)
    reasons = []
    repository = str(details.get("repository", ""))
    commit_sha = str(details.get("commit_sha", ""))
    if details.get("exact_identity") is not True:
        reasons.append("source-exact-identity-missing")
    if not commit_sha:
        reasons.append("source-commit-sha-missing")
    elif not _GIT_OBJECT_ID.fullmatch(commit_sha):
        reasons.append("source-commit-sha-invalid")
    if not repository:
        reasons.append("source-repository-missing")
    elif repository != target:
        reasons.append("source-repository-target-mismatch")
    if repository and commit_sha:
        expected_ref = "github://{}@{}".format(repository, commit_sha)
        if str(candidate.get("ref", "")) != expected_ref:
            reasons.append("source-ref-identity-mismatch")
    return reasons


def _validation_reasons(candidate: Mapping[str, Any], target: str) -> List[str]:
    details = _details(candidate)
    reasons = []
    run_id = str(details.get("run_id", ""))
    head_sha = str(details.get("head_sha", ""))
    if str(details.get("conclusion", "")) != "success":
        reasons.append("validation-not-successful")
    if not run_id:
        reasons.append("validation-run-id-missing")
    if not head_sha:
        reasons.append("validation-head-sha-missing")
    elif not _GIT_OBJECT_ID.fullmatch(head_sha):
        reasons.append("validation-head-sha-invalid")
    if run_id:
        expected_ref = "github-actions://{}/runs/{}".format(target, run_id)
        if str(candidate.get("ref", "")) != expected_ref:
            reasons.append("validation-ref-identity-mismatch")
    return reasons


def _artifact_reasons(candidate: Mapping[str, Any], target: str) -> List[str]:
    details = _details(candidate)
    kind = str(candidate.get("kind", ""))
    reasons = []
    digest = str(details.get("digest", ""))
    if not digest:
        reasons.append("artifact-digest-missing")
    elif not _SHA256_DIGEST.fullmatch(digest):
        reasons.append("artifact-digest-invalid")
    if kind == "github-actions-artifact":
        artifact_id = str(details.get("artifact_id", ""))
        if details.get("expired") is not False:
            reasons.append("actions-artifact-expiry-state-invalid")
        if not artifact_id:
            reasons.append("actions-artifact-id-missing")
        else:
            expected_ref = "github-actions-artifact://{}/{}".format(
                target, artifact_id
            )
            if str(candidate.get("ref", "")) != expected_ref:
                reasons.append("actions-artifact-ref-identity-mismatch")
    elif kind == "github-release-asset":
        asset_id = str(details.get("asset_id", ""))
        if not asset_id:
            reasons.append("release-asset-id-missing")
        else:
            expected_ref = "github-release-asset://{}/{}".format(target, asset_id)
            if str(candidate.get("ref", "")) != expected_ref:
                reasons.append("release-asset-ref-identity-mismatch")
        if not str(details.get("release_id", "")):
            reasons.append("release-asset-release-id-missing")
        if not str(details.get("tag_name", "")):
            reasons.append("release-asset-tag-missing")
        if details.get("release_draft") is not False:
            reasons.append("release-asset-draft-state-invalid")
        if details.get("release_prerelease") is not False:
            reasons.append("release-asset-prerelease-state-invalid")
    return reasons


def _release_reasons(candidate: Mapping[str, Any], target: str) -> List[str]:
    details = _details(candidate)
    reasons = []
    release_id = str(details.get("release_id", ""))
    if details.get("meets_immutable_release_policy") is not True:
        reasons.append("immutable-release-policy-not-met")
    if details.get("immutable") is not True:
        reasons.append("release-not-immutable")
    if details.get("draft") is not False:
        reasons.append("release-draft-state-invalid")
    if details.get("prerelease") is not False:
        reasons.append("release-prerelease-state-invalid")
    if not release_id:
        reasons.append("release-id-missing")
    else:
        expected_ref = "github-release://{}/{}".format(target, release_id)
        if str(candidate.get("ref", "")) != expected_ref:
            reasons.append("release-ref-identity-mismatch")
    if not str(details.get("tag_name", "")):
        reasons.append("release-tag-missing")
    return reasons


def _field_reasons(
    field: str, candidate: Mapping[str, Any], target: str
) -> List[str]:
    kind = str(candidate.get("kind", ""))
    if field not in REVIEW_FIELDS:
        return ["unsupported-evidence-field"]
    if kind not in _EXPECTED_KINDS[field]:
        return ["candidate-kind-does-not-match-field"]
    if field == "source_refs":
        return _source_reasons(candidate, target)
    if field == "validation_refs":
        return _validation_reasons(candidate, target)
    if field == "artifact_refs":
        return _artifact_reasons(candidate, target)
    return _release_reasons(candidate, target)


def _qualification_row(
    *,
    result: Mapping[str, Any],
    candidate: Mapping[str, Any],
    upstream_reasons: Sequence[str],
    result_reasons: Sequence[str],
) -> Dict[str, Any]:
    field = str(result.get("field", ""))
    target = str(result.get("target", ""))
    reasons = list(upstream_reasons)
    reasons.extend(result_reasons)
    reasons.extend(_generic_reasons(candidate))
    reasons.extend(_field_reasons(field, candidate, target))
    reasons = list(dict.fromkeys(reasons))
    reviewable = not reasons
    return {
        "project_id": str(result.get("project_id", "")),
        "field": field,
        "provider": str(result.get("provider", "")),
        "operation": str(result.get("operation", "")),
        "target": target,
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
    source_error_count = raw_error_count if _is_nonnegative_int(raw_error_count) else 1
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
