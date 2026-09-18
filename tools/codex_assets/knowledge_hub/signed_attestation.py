"""Build and verify bounded materials for hosted signed quality attestations."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any, Dict, Mapping

from .attestation import PREDICATE_TYPE, quality_attestation, statement_digest, verify_quality_attestation
from .common import KnowledgeHubError, utc_timestamp
from .quality_evidence_binding import verify_quality_evidence_binding

SOURCE_RE = re.compile(r"^[0-9a-f]{40}$")
DEFAULT_OUTPUT = ".cache/knowledge-hub/signed-attestation"
EVIDENCE_PATHS = {
    "engineering": ".cache/knowledge-hub/engineering-quality.json",
    "compliance": ".cache/knowledge-hub/compliance-eval.json",
    "restore": ".cache/knowledge-hub/restore-drill-head.json",
    "product": ".cache/knowledge-hub/final-gate-product-full.json",
    "quality_binding": ".cache/knowledge-hub/quality-evidence-binding.json",
    "terminal": ".cache/knowledge-hub/terminal-closure.json",
    "hosting": ".cache/knowledge-hub/hosting-posture.json",
    "sbom": ".tmp/engineering/knowledge-hub.cdx.json",
}
MAX_BUNDLE_BYTES = 16 * 1024 * 1024


def _load_object(path: pathlib.Path, label: str) -> Dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise KnowledgeHubError("{} evidence is unavailable".format(label))
    if path.stat().st_size > 16 * 1024 * 1024:
        raise KnowledgeHubError("{} evidence exceeds byte budget".format(label))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("{} evidence is invalid JSON".format(label)) from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} evidence must be an object".format(label))
    return dict(value)


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_write(path: pathlib.Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def _status(payload: Mapping[str, Any], label: str) -> str:
    status = str(payload.get("status", "")).strip()
    if status not in {"pass", "success"}:
        raise KnowledgeHubError("{} evidence is not passing".format(label))
    return status


def _product_status(payload: Mapping[str, Any]) -> str:
    status = str(payload.get("status", "")).strip()
    if status not in {"pass", "success", "needs-review"}:
        raise KnowledgeHubError("product evidence has invalid status")
    if status == "needs-review" and payload.get("terminal") is not False:
        raise KnowledgeHubError("nonterminal product evidence must declare terminal=false")
    return status


def build_signed_quality_materials(
    root: pathlib.Path,
    *,
    source_revision: str,
    output_relative: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    if not SOURCE_RE.fullmatch(source_revision):
        raise KnowledgeHubError("source revision must be a lowercase 40-character git SHA")
    root = pathlib.Path(root).resolve()
    output = (root / output_relative).resolve()
    try:
        output.relative_to(root)
    except ValueError as exc:
        raise KnowledgeHubError("signed attestation output must stay inside repository") from exc

    objects = {
        key: _load_object(root / relative, key)
        for key, relative in EVIDENCE_PATHS.items()
        if key != "sbom"
    }
    sbom_path = root / EVIDENCE_PATHS["sbom"]
    if not sbom_path.is_file() or sbom_path.is_symlink():
        raise KnowledgeHubError("sbom evidence is unavailable")

    verify_quality_evidence_binding(
        root,
        objects["quality_binding"],
        source_revision=source_revision,
    )

    if str(objects["hosting"].get("source_revision", "")).lower() != source_revision:
        raise KnowledgeHubError("hosting posture source revision mismatch")

    statuses = {
        "engineering": _status(objects["engineering"], "engineering"),
        "compliance": _status(objects["compliance"], "compliance"),
        "restore": _status(objects["restore"], "restore"),
        "product": _product_status(objects["product"]),
        "hosting": _status(objects["hosting"], "hosting"),
    }
    terminal = objects["terminal"]
    terminal_status = str(terminal.get("status", "")).strip()
    terminal_value = terminal.get("terminal")
    blockers = terminal.get("blockers", [])
    if terminal_status not in {"pass", "needs-review", "needs-fix", "blocked"}:
        raise KnowledgeHubError("terminal closure verdict has invalid status")
    if not isinstance(terminal_value, bool):
        raise KnowledgeHubError("terminal closure verdict must include boolean terminal")
    if not isinstance(blockers, list):
        raise KnowledgeHubError("terminal closure blockers must be a list")
    evidence_rows = []
    for key, relative in EVIDENCE_PATHS.items():
        path = root / relative
        evidence_rows.append(
            {
                "id": key,
                "path": relative,
                "sha256": _sha256(path),
                "size": path.stat().st_size,
            }
        )
    manifest = {
        "schema_version": "knowledge-hub.signed-quality-evidence.v1",
        "source_revision": source_revision,
        "generated_at": utc_timestamp(),
        "evidence": evidence_rows,
        "canonical_write": False,
    }
    manifest_path = output / "quality-evidence-manifest.json"
    _canonical_write(manifest_path, manifest)
    manifest_sha = _sha256(manifest_path)
    terminal_sha = next(row["sha256"] for row in evidence_rows if row["id"] == "terminal")
    sbom_sha = next(row["sha256"] for row in evidence_rows if row["id"] == "sbom")

    statement = quality_attestation(
        subject_name="quality-evidence-manifest.json",
        subject_sha256=manifest_sha,
        source_commit=source_revision,
        evidence_artifact_sha256=manifest_sha,
        engineering_status=statuses["engineering"],
        compliance_status=statuses["compliance"],
        restore_status=statuses["restore"],
        product_gate_status=statuses["product"],
        sbom_sha256=sbom_sha,
        terminal_closure_status=terminal_status,
        terminal_closure_terminal=terminal_value,
        terminal_closure_sha256=terminal_sha,
        terminal_closure_blockers=[str(value) for value in blockers],
    )
    structural = verify_quality_attestation(statement, expected_subject_sha256=manifest_sha)
    if structural["status"] != "pass":
        raise KnowledgeHubError("generated quality statement failed structural verification")
    statement_path = output / "quality-statement.json"
    predicate_path = output / "quality-predicate.json"
    _canonical_write(statement_path, statement)
    _canonical_write(predicate_path, statement["predicate"])
    receipt = {
        "schema_version": "knowledge-hub.signed-attestation-materials.v1",
        "source_revision": source_revision,
        "manifest_path": str(manifest_path.relative_to(root)),
        "manifest_sha256": manifest_sha,
        "statement_path": str(statement_path.relative_to(root)),
        "statement_sha256": statement_digest(statement),
        "predicate_path": str(predicate_path.relative_to(root)),
        "predicate_type": PREDICATE_TYPE,
        "sbom_sha256": sbom_sha,
        "terminal_closure": dict(statement["predicate"]["terminal_closure"]),
        "quality_gates": dict(statement["predicate"]["quality_gates"]),
        "structural_verification": structural,
    }
    receipt_path = output / "materials-receipt.json"
    _canonical_write(receipt_path, receipt)
    return receipt


def verify_hosted_attestation(
    root: pathlib.Path,
    *,
    verification_path: pathlib.Path,
    source_revision: str,
    source_ref: str,
    signer_workflow: str,
    signer_source_revision: str,
    bundle_path: pathlib.Path,
    attestation_id: str,
    attestation_url: str,
    output_relative: str = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    if not SOURCE_RE.fullmatch(str(signer_source_revision).lower()):
        raise KnowledgeHubError(
            "signer source revision must be a lowercase 40-character git SHA"
        )
    root = pathlib.Path(root).resolve()
    output = root / output_relative
    materials = _load_object(output / "materials-receipt.json", "materials receipt")
    value = json.loads(verification_path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not value:
        raise KnowledgeHubError("hosted attestation verification returned no verified attestations")
    expected_manifest = str(materials.get("manifest_sha256", ""))
    expected_sbom = str(materials.get("sbom_sha256", ""))
    expected_terminal = materials.get("terminal_closure", {})
    matched = None
    for row in value:
        if not isinstance(row, Mapping):
            continue
        verification = row.get("verificationResult", {})
        if not isinstance(verification, Mapping):
            continue
        statement = verification.get("statement", {})
        if not isinstance(statement, Mapping) or statement.get("predicateType") != PREDICATE_TYPE:
            continue
        subjects = statement.get("subject", [])
        if not isinstance(subjects, list) or not subjects or not isinstance(subjects[0], Mapping):
            continue
        digest = subjects[0].get("digest", {})
        if not isinstance(digest, Mapping) or digest.get("sha256") != expected_manifest:
            continue
        predicate = statement.get("predicate", {})
        if not isinstance(predicate, Mapping):
            continue
        if str(predicate.get("source_commit", "")) != source_revision:
            continue
        if str(predicate.get("evidence_artifact_sha256", "")) != expected_manifest:
            continue
        if str(predicate.get("sbom_sha256", "")) != expected_sbom:
            continue
        if predicate.get("terminal_closure") != expected_terminal:
            continue
        signature = verification.get("signature", {})
        timestamps = verification.get("verifiedTimestamps", [])
        if not isinstance(signature, Mapping) or not signature.get("certificate"):
            continue
        if not isinstance(timestamps, list) or not timestamps:
            continue
        matched = row
        break
    if matched is None:
        raise KnowledgeHubError("verified hosted attestation does not match local quality materials")
    if not bundle_path.is_file() or bundle_path.is_symlink():
        raise KnowledgeHubError("signed attestation bundle is unavailable")
    if bundle_path.stat().st_size > MAX_BUNDLE_BYTES:
        raise KnowledgeHubError("signed attestation bundle exceeds byte budget")
    retained_bundle = output / "sigstore-bundle.json"
    retained_bundle.write_bytes(bundle_path.read_bytes())
    receipt = {
        "schema_version": "knowledge-hub.hosted-signed-attestation.v1",
        "status": "pass",
        "source_revision": source_revision,
        "source_ref": source_ref,
        "signer_workflow": signer_workflow,
        "signer_source_revision": str(signer_source_revision).lower(),
        "predicate_type": PREDICATE_TYPE,
        "manifest_sha256": expected_manifest,
        "sbom_sha256": expected_sbom,
        "terminal_closure": expected_terminal,
        "attestation_id": str(attestation_id),
        "attestation_url": str(attestation_url),
        "bundle_path": str(retained_bundle.relative_to(root)),
        "bundle_sha256": _sha256(retained_bundle),
        "verification_sha256": _sha256(verification_path),
        "sigstore_identity_verified": True,
        "private_key_used": False,
        "self_hosted_runner_allowed": False,
        "generated_at": utc_timestamp(),
    }
    _canonical_write(output / "hosted-verification-receipt.json", receipt)
    return receipt
