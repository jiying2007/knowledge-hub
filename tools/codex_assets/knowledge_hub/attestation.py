"""P10 deterministic in-toto/SLSA-style evidence attestations."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Mapping

from .common import KnowledgeHubError, utc_timestamp

STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://knowledge-hub.local/attestation/quality/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256(value: str, label: str) -> str:
    value = str(value).strip().lower()
    if not SHA256_RE.fullmatch(value):
        raise KnowledgeHubError("{} must be lowercase SHA256".format(label))
    return value


def quality_attestation(
    *,
    subject_name: str,
    subject_sha256: str,
    source_commit: str,
    evidence_artifact_sha256: str,
    engineering_status: str,
    compliance_status: str,
    restore_status: str,
    product_gate_status: str,
    sbom_sha256: str = "",
) -> Dict[str, Any]:
    if not subject_name or len(subject_name) > 1024:
        raise KnowledgeHubError("attestation subject name must be non-empty and bounded")
    statuses = {
        "engineering": engineering_status,
        "compliance": compliance_status,
        "restore": restore_status,
        "product_gate": product_gate_status,
    }
    if any(value not in {"success", "pass"} for value in statuses.values()):
        raise KnowledgeHubError("quality attestation requires passing terminal evidence")
    predicate: Dict[str, Any] = {
        "source_commit": str(source_commit),
        "evidence_artifact_sha256": _sha256(
            evidence_artifact_sha256, "evidence artifact digest"
        ),
        "quality_gates": statuses,
        "generated_at": utc_timestamp(),
        "canonical_write": False,
    }
    if sbom_sha256:
        predicate["sbom_sha256"] = _sha256(sbom_sha256, "SBOM digest")
    return {
        "_type": STATEMENT_TYPE,
        "subject": [
            {
                "name": subject_name,
                "digest": {"sha256": _sha256(subject_sha256, "subject digest")},
            }
        ],
        "predicateType": PREDICATE_TYPE,
        "predicate": predicate,
    }


def statement_digest(statement: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(statement),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def verify_quality_attestation(
    statement: Mapping[str, Any],
    *,
    expected_subject_sha256: str = "",
) -> Dict[str, Any]:
    failures = []
    if statement.get("_type") != STATEMENT_TYPE:
        failures.append("statement-type")
    if statement.get("predicateType") != PREDICATE_TYPE:
        failures.append("predicate-type")
    subjects = statement.get("subject", [])
    if not isinstance(subjects, list) or len(subjects) != 1:
        failures.append("subject-count")
        subject_digest = ""
    else:
        digest = subjects[0].get("digest", {}) if isinstance(subjects[0], Mapping) else {}
        subject_digest = str(digest.get("sha256", "")) if isinstance(digest, Mapping) else ""
        if not SHA256_RE.fullmatch(subject_digest):
            failures.append("subject-digest")
    if expected_subject_sha256 and subject_digest != expected_subject_sha256:
        failures.append("subject-mismatch")
    predicate = statement.get("predicate", {})
    if not isinstance(predicate, Mapping):
        failures.append("predicate-object")
    else:
        gates = predicate.get("quality_gates", {})
        if not isinstance(gates, Mapping):
            failures.append("quality-gates")
        elif any(str(value) not in {"success", "pass"} for value in gates.values()):
            failures.append("quality-gate-not-pass")
        artifact_digest = str(predicate.get("evidence_artifact_sha256", ""))
        if not SHA256_RE.fullmatch(artifact_digest):
            failures.append("artifact-digest")
    return {
        "schema_version": "knowledge-hub.attestation-verdict.v1",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "statement_sha256": statement_digest(statement),
    }
