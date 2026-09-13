"""Machine-verifiable terminal forms for historical artifact references."""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any, Dict, List, Mapping

from .artifact_governance import (
    IMMUTABLE_ARTIFACT_REF_SCHEMA,
    validate_immutable_artifact_ref,
)
from .common import KnowledgeHubError, load_jsonl

DEFAULT_REGISTRY = "registry/legacy-artifact-terminal-forms.json"
REGISTRY_CONTRACT = "knowledge-hub-legacy-artifact-terminal-forms-v1"
HISTORICAL_EXCEPTION_FORM = "immutable-historical-exception-with-owner-and-reason"
COVERAGE_MODE = "exact-reference-set-sha256"


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _is_legacy_artifact_ref(row: Mapping[str, Any]) -> bool:
    return bool(
        (row.get("uri") or row.get("artifact_uri"))
        and (row.get("sha256") or row.get("source_sha256"))
        and row.get("size") is not None
        and row.get("schema_version") != IMMUTABLE_ARTIFACT_REF_SCHEMA
    )


def _reference_fingerprint(relative_path: str, row: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        {"path": relative_path, "row": dict(row)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def legacy_reference_snapshot(root: pathlib.Path) -> Dict[str, Any]:
    """Return an exact, order-independent snapshot of every legacy artifact ref."""

    fingerprints: List[str] = []
    sample: List[Dict[str, Any]] = []
    strict_valid_count = 0
    strict_invalid: List[Dict[str, Any]] = []
    manifests = root / "artifacts/manifests"
    for path in sorted(manifests.rglob("*.jsonl")) if manifests.exists() else []:
        relative = str(path.relative_to(root))
        for line_no, row in enumerate(load_jsonl(path), 1):
            if not isinstance(row, Mapping):
                continue
            if row.get("schema_version") == IMMUTABLE_ARTIFACT_REF_SCHEMA:
                errors = validate_immutable_artifact_ref(row)
                if errors:
                    strict_invalid.append(
                        {
                            "path": relative,
                            "line": line_no,
                            "id": str(row.get("id", "")),
                            "errors": errors,
                        }
                    )
                else:
                    strict_valid_count += 1
                continue
            if not _is_legacy_artifact_ref(row):
                continue
            fingerprint = _reference_fingerprint(relative, row)
            fingerprints.append(fingerprint)
            if len(sample) < 20:
                sample.append(
                    {
                        "path": relative,
                        "line": line_no,
                        "id": str(row.get("id", "")),
                        "fingerprint": fingerprint,
                    }
                )
    ordered = sorted(fingerprints)
    set_digest = hashlib.sha256("\n".join(ordered).encode("utf-8")).hexdigest()
    return {
        "legacy_reference_count": len(ordered),
        "legacy_reference_set_sha256": set_digest,
        "legacy_reference_sample": sample,
        "strict_v1_reference_count": strict_valid_count,
        "strict_v1_invalid_count": len(strict_invalid),
        "strict_v1_invalid_sample": strict_invalid[:20],
    }


def _load_registry(root: pathlib.Path, registry_path: str) -> Dict[str, Any]:
    path = root / registry_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("legacy artifact terminal-form registry is unavailable or invalid") from exc
    if not isinstance(payload, Mapping):
        raise KnowledgeHubError("legacy artifact terminal-form registry must be an object")
    return dict(payload)


def evaluate_legacy_artifact_terminal_forms(
    root: pathlib.Path,
    *,
    registry_path: str = DEFAULT_REGISTRY,
) -> Dict[str, Any]:
    """Fail closed unless every legacy reference is covered by an exact frozen set."""

    snapshot = legacy_reference_snapshot(root)
    errors: List[str] = []
    try:
        registry = _load_registry(root, registry_path)
    except KnowledgeHubError as exc:
        registry = {}
        errors.append(str(exc))

    if registry.get("schema_version") != 1:
        errors.append("terminal-form registry schema_version must be 1")
    if registry.get("contract") != REGISTRY_CONTRACT:
        errors.append("terminal-form registry contract mismatch")
    coverage = registry.get("coverage", {})
    if not isinstance(coverage, Mapping):
        coverage = {}
        errors.append("terminal-form registry coverage must be an object")

    owner = str(coverage.get("owner", "")).strip()
    reason = str(coverage.get("reason", "")).strip()
    terminal_form = str(coverage.get("terminal_form", "")).strip()
    coverage_mode = str(coverage.get("coverage_mode", "")).strip()
    expected_count = int(coverage.get("legacy_reference_count", -1) or 0)
    expected_digest = str(coverage.get("legacy_reference_set_sha256", "")).strip()
    actual_count = int(snapshot["legacy_reference_count"])
    actual_digest = str(snapshot["legacy_reference_set_sha256"])

    if terminal_form != HISTORICAL_EXCEPTION_FORM:
        errors.append("historical exception terminal_form mismatch")
    if coverage_mode != COVERAGE_MODE:
        errors.append("historical exception coverage_mode mismatch")
    if not owner:
        errors.append("historical exception owner is required")
    if not reason:
        errors.append("historical exception reason is required")
    if len(expected_digest) != 64 or any(
        character not in "0123456789abcdef" for character in expected_digest
    ):
        errors.append("historical exception set sha256 is invalid")
    if expected_count < 0:
        errors.append("historical exception count must be non-negative")

    count_matches = expected_count == actual_count
    digest_matches = expected_digest == actual_digest
    strict_refs_valid = int(snapshot["strict_v1_invalid_count"]) == 0
    accepted = not errors and count_matches and digest_matches and strict_refs_valid
    accepted_legacy_count = actual_count if accepted else 0
    unaccepted_legacy_count = actual_count - accepted_legacy_count

    return {
        "schema_version": 1,
        "contract": REGISTRY_CONTRACT,
        "status": "pass" if accepted else "fail",
        "registry": registry_path,
        "terminal_form": terminal_form,
        "coverage_mode": coverage_mode,
        "owner": owner,
        "reason": reason,
        "legacy_reference_count": actual_count,
        "legacy_reference_set_sha256": actual_digest,
        "expected_legacy_reference_count": expected_count,
        "expected_legacy_reference_set_sha256": expected_digest,
        "count_matches": count_matches,
        "digest_matches": digest_matches,
        "accepted_legacy_reference_count": accepted_legacy_count,
        "unaccepted_legacy_reference_count": unaccepted_legacy_count,
        "strict_v1_reference_count": snapshot["strict_v1_reference_count"],
        "strict_v1_invalid_count": snapshot["strict_v1_invalid_count"],
        "legacy_reference_sample": snapshot["legacy_reference_sample"],
        "strict_v1_invalid_sample": snapshot["strict_v1_invalid_sample"],
        "errors": errors,
    }
