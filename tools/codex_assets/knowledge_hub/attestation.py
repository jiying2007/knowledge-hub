"""P10 deterministic in-toto/SLSA-style evidence attestations."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Mapping, Sequence

from .common import KnowledgeHubError, utc_timestamp

STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://knowledge-hub.local/attestation/quality/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TERMINAL_STATUSES = {"pass", "needs-review", "needs-fix", "blocked"}
PASSING_QUALITY_STATUSES = {"pass", "success"}
PRODUCT_EVIDENCE_STATUSES = {"pass", "success", "needs-review"}


def _sha256(value: str, label: str) -> str:
    value = str(value).strip().lower()
    if not SHA256_RE.fullmatch(value):
        raise KnowledgeHubError("{} must be lowercase SHA256".format(label))
    return value


def _terminal_closure(
    *,
    status: str,
    terminal: Any,
    digest: str,
    blockers: Sequence[str],
) -> Dict[str, Any]:
    if status not in TERMINAL_STATUSES:
        raise KnowledgeHubError("terminal closure status is invalid")
    if not isinstance(terminal, bool):
        raise KnowledgeHubError("terminal closure terminal must be boolean")
    if isinstance(blockers, (str, bytes)) or len(blockers) > 32:
        raise KnowledgeHubError("terminal closure blockers are invalid")
    blocker_rows = [str(value).strip() for value in blockers]
    if any(not value or len(value) > 256 for value in blocker_rows):
        raise KnowledgeHubError("terminal closure blocker is invalid")
    return {
        "status": status,
        "terminal": terminal,
        "sha256": _sha256(digest, "terminal closure digest"),
        "blockers": blocker_rows,
    }


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
    terminal_closure_status: str = "",
    terminal_closure_terminal: Any = None,
    terminal_closure_sha256: str = "",
    terminal_closure_blockers: Sequence[str] = (),
) -> Dict[str, Any]:
    if not subject_name or len(subject_name) > 1024:
        raise KnowledgeHubError("attestation subject name must be non-empty and bounded")
    statuses = {
        "engineering": engineering_status,
        "compliance": compliance_status,
        "restore": restore_status,
        "product_gate": product_gate_status,
    }
    if any(
        statuses[key] not in PASSING_QUALITY_STATUSES
        for key in ("engineering", "compliance", "restore")
    ):
        raise KnowledgeHubError("quality attestation requires passing quality evidence")
    if product_gate_status not in PRODUCT_EVIDENCE_STATUSES:
        raise KnowledgeHubError("quality attestation product evidence status is invalid")
    terminal_requested = any(
        [
            terminal_closure_status,
            terminal_closure_terminal is not None,
            terminal_closure_sha256,
            bool(terminal_closure_blockers),
        ]
    )
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
    if terminal_requested:
        predicate["terminal_closure"] = _terminal_closure(
            status=terminal_closure_status,
            terminal=terminal_closure_terminal,
            digest=terminal_closure_sha256,
            blockers=terminal_closure_blockers,
        )
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
        product_gate_status = ""
        if not isinstance(gates, Mapping):
            failures.append("quality-gates")
        else:
            required_gates = {"engineering", "compliance", "restore", "product_gate"}
            if set(gates) != required_gates:
                failures.append("quality-gates")
            elif any(
                str(gates.get(key, "")) not in PASSING_QUALITY_STATUSES
                for key in ("engineering", "compliance", "restore")
            ):
                failures.append("quality-gate-not-pass")
            product_gate_status = str(gates.get("product_gate", ""))
            if product_gate_status not in PRODUCT_EVIDENCE_STATUSES:
                failures.append("product-gate-status")
        artifact_digest = str(predicate.get("evidence_artifact_sha256", ""))
        if not SHA256_RE.fullmatch(artifact_digest):
            failures.append("artifact-digest")
        terminal = predicate.get("terminal_closure")
        if terminal is not None:
            if not isinstance(terminal, Mapping):
                failures.append("terminal-closure-object")
            else:
                if str(terminal.get("status", "")) not in TERMINAL_STATUSES:
                    failures.append("terminal-closure-status")
                if not isinstance(terminal.get("terminal"), bool):
                    failures.append("terminal-closure-terminal")
                if not SHA256_RE.fullmatch(str(terminal.get("sha256", ""))):
                    failures.append("terminal-closure-digest")
                blockers = terminal.get("blockers", [])
                if not isinstance(blockers, list) or any(
                    not isinstance(value, str) or not value for value in blockers
                ):
                    failures.append("terminal-closure-blockers")
    return {
        "schema_version": "knowledge-hub.attestation-verdict.v1",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "statement_sha256": statement_digest(statement),
    }
