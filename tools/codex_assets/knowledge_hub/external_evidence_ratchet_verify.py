"""Verify an external-evidence ratchet without trusting pull-request code."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any, Dict, Mapping, Tuple

from .common import KnowledgeHubError
from .external_evidence_ratchet import build_external_gap_ratchet_candidate
from .schemas import validate_instance

EVENT_RE = re.compile(
    r"^external-evidence-"
    r"(connector-provider-pilot|production-retrieval-eval|memory-lifecycle-pilot|real-adoption-evidence)-"
    r"([0-9]+)-([0-9]+)$"
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_json(path: pathlib.Path, label: str) -> Tuple[Dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("{} is invalid JSON".format(label)) from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return dict(value), raw


def _ledger_record(
    root: pathlib.Path,
    base_path: pathlib.Path,
    head_path: pathlib.Path,
) -> Tuple[Dict[str, Any], str, int, int]:
    base = base_path.read_bytes()
    head = head_path.read_bytes()
    if base and not base.endswith(b"\n"):
        raise KnowledgeHubError("base durable ledger is not canonical JSONL")
    if not head.startswith(base):
        raise KnowledgeHubError("durable ledger must preserve exact base prefix")
    rows = [line for line in head[len(base) :].splitlines() if line.strip()]
    if len(rows) != 1:
        raise KnowledgeHubError("external ratchet must append exactly one durable record")
    try:
        record = json.loads(rows[0].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("external durable record is invalid JSON") from exc
    if not isinstance(record, Mapping):
        raise KnowledgeHubError("external durable record must be an object")
    record = dict(record)
    validation = validate_instance(root, "durable-evidence-record-v1", record)
    if validation.get("status") != "pass":
        raise KnowledgeHubError(
            "external durable record violates schema: {}".format(
                validation.get("errors", [])
            )
        )
    if record.get("event_type") != "external-evidence-ratchet":
        raise KnowledgeHubError("durable record type is not external-evidence-ratchet")
    match = EVENT_RE.fullmatch(str(record.get("event_id", "")))
    if match is None:
        raise KnowledgeHubError("external durable event identity is invalid")
    return record, match.group(1), int(match.group(2)), int(match.group(3))


def _verify_origin_run(
    run: Mapping[str, Any],
    *,
    repository: str,
    master_sha: str,
    run_id: int,
    run_attempt: int,
) -> None:
    expected = {
        "id": run_id,
        "run_attempt": run_attempt,
        "name": "external-evidence-ratchet-candidate",
        "path": ".github/workflows/external-evidence-ratchet-candidate.yml",
        "head_sha": master_sha,
        "head_branch": "master",
        "status": "completed",
        "conclusion": "success",
    }
    for field, value in expected.items():
        if run.get(field) != value:
            raise KnowledgeHubError(
                "origin ratchet run {} mismatch expected={!r} observed={!r}".format(
                    field, value, run.get(field)
                )
            )
    if run.get("event") not in {"workflow_run", "workflow_dispatch"}:
        raise KnowledgeHubError("origin ratchet event is not trusted")
    repo = run.get("repository") or {}
    if not isinstance(repo, Mapping) or repo.get("full_name") != repository:
        raise KnowledgeHubError("origin ratchet repository identity mismatch")


def _expected_candidate_bytes(candidate: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(dict(candidate), ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def _verify_digests(
    record: Mapping[str, Any],
    *,
    head_registry_raw: bytes,
    proposal_raw: bytes,
    binding_raw: bytes,
    closure_raw: bytes,
    intake_raw: bytes,
) -> None:
    expected = {
        "candidate_registry": "sha256:" + _sha256(head_registry_raw),
        "ratchet_proposal": "sha256:" + _sha256(proposal_raw),
        "host_binding": "sha256:" + _sha256(binding_raw),
        "closure_receipt": "sha256:" + _sha256(closure_raw),
        "intake_receipt": "sha256:" + _sha256(intake_raw),
    }
    if record.get("digests") != expected:
        raise KnowledgeHubError("external durable digest set does not match origin receipts")


def _validate_origin_contracts(
    root: pathlib.Path,
    *,
    closure: Mapping[str, Any],
    intake: Mapping[str, Any],
    binding: Mapping[str, Any],
    proposal: Mapping[str, Any],
) -> None:
    for contract_id, payload in (
        ("external-evidence-receipt-v1", closure),
        ("external-evidence-intake-receipt-v1", intake),
        ("external-evidence-intake-host-binding-v1", binding),
        ("external-evidence-ratchet-proposal-v2", proposal),
    ):
        result = validate_instance(root, contract_id, payload)
        if result.get("status") != "pass":
            raise KnowledgeHubError(
                "{} validation failed: {}".format(
                    contract_id,
                    result.get("errors", []),
                )
            )


def _replay_candidate(
    root: pathlib.Path,
    *,
    base_registry_path: pathlib.Path,
    head_registry_path: pathlib.Path,
    closure_receipt_path: pathlib.Path,
    intake_receipt_path: pathlib.Path,
    host_binding_path: pathlib.Path,
    proposal_path: pathlib.Path,
    gap_id: str,
    record: Mapping[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], bytes]:
    origin_proposal, proposal_raw = _load_json(proposal_path, "origin proposal")
    binding, binding_raw = _load_json(host_binding_path, "host binding")
    closure, closure_raw = _load_json(closure_receipt_path, "closure receipt")
    intake, intake_raw = _load_json(intake_receipt_path, "intake receipt")
    _validate_origin_contracts(
        root,
        closure=closure,
        intake=intake,
        binding=binding,
        proposal=origin_proposal,
    )

    candidate, proposal = build_external_gap_ratchet_candidate(
        registry_path=base_registry_path,
        closure_receipt_path=closure_receipt_path,
        intake_receipt_path=intake_receipt_path,
        host_binding_path=host_binding_path,
    )
    if proposal.get("gap_id") != gap_id:
        raise KnowledgeHubError("durable event gap does not match replayed proposal")
    if proposal.get("status") != "ready-for-machine-ratchet":
        raise KnowledgeHubError("replayed external proposal is not machine-ready")
    if proposal.get("review_required") is not False:
        raise KnowledgeHubError(
            "replayed external proposal unexpectedly requires review"
        )
    if origin_proposal != proposal:
        raise KnowledgeHubError("origin proposal does not equal trusted replay")

    head_raw = head_registry_path.read_bytes()
    if head_raw != _expected_candidate_bytes(candidate):
        raise KnowledgeHubError(
            "PR registry bytes do not equal replayed external candidate"
        )
    _verify_digests(
        record,
        head_registry_raw=head_raw,
        proposal_raw=proposal_raw,
        binding_raw=binding_raw,
        closure_raw=closure_raw,
        intake_raw=intake_raw,
    )
    return candidate, proposal, head_raw


def _verify_candidate_gap(
    candidate: Mapping[str, Any],
    proposal: Mapping[str, Any],
    record: Mapping[str, Any],
    gap_id: str,
) -> None:
    gaps = [
        row
        for row in candidate.get("external_closure_gaps", [])
        if isinstance(row, Mapping) and row.get("id") == gap_id
    ]
    if len(gaps) != 1 or gaps[0].get("status") != "closed":
        raise KnowledgeHubError(
            "replayed external candidate does not close selected gap"
        )
    if record.get("evidence_refs") != gaps[0].get("evidence_refs"):
        raise KnowledgeHubError(
            "durable evidence refs differ from canonical gap refs"
        )
    if record.get("observed_at") != proposal.get("generated_at"):
        raise KnowledgeHubError(
            "durable observed_at differs from strict evidence time"
        )


def verify_external_evidence_ratchet(
    root: pathlib.Path,
    *,
    base_registry_path: pathlib.Path,
    head_registry_path: pathlib.Path,
    base_ledger_path: pathlib.Path,
    head_ledger_path: pathlib.Path,
    closure_receipt_path: pathlib.Path,
    intake_receipt_path: pathlib.Path,
    host_binding_path: pathlib.Path,
    proposal_path: pathlib.Path,
    origin_run_path: pathlib.Path,
    repository: str,
    master_sha: str,
    head_sha: str,
) -> Dict[str, Any]:
    """Replay strict evidence projection and verify exact canonical transition."""

    root = pathlib.Path(root).resolve()
    if not SHA_RE.fullmatch(master_sha) or not SHA_RE.fullmatch(head_sha):
        raise KnowledgeHubError("master/head revisions must be lowercase git SHAs")

    record, gap_id, run_id, run_attempt = _ledger_record(
        root, base_ledger_path, head_ledger_path
    )
    if record.get("source_revision") != master_sha:
        raise KnowledgeHubError(
            "external durable source revision is not current master"
        )

    candidate, proposal, head_raw = _replay_candidate(
        root,
        base_registry_path=base_registry_path,
        head_registry_path=head_registry_path,
        closure_receipt_path=closure_receipt_path,
        intake_receipt_path=intake_receipt_path,
        host_binding_path=host_binding_path,
        proposal_path=proposal_path,
        gap_id=gap_id,
        record=record,
    )
    _verify_candidate_gap(candidate, proposal, record, gap_id)

    origin_run, _ = _load_json(origin_run_path, "origin ratchet run")
    _verify_origin_run(
        origin_run,
        repository=repository,
        master_sha=master_sha,
        run_id=run_id,
        run_attempt=run_attempt,
    )
    return {
        "schema_version": 1,
        "projection": "knowledge-hub-external-evidence-ratchet-verification-v1",
        "status": "pass",
        "read_only": True,
        "canonical_write_performed": False,
        "repository": repository,
        "master_sha": master_sha,
        "head_sha": head_sha,
        "gap_id": gap_id,
        "candidate_registry_sha256": _sha256(head_raw),
        "origin_run_id": run_id,
        "origin_run_attempt": run_attempt,
        "evidence_observed_at": proposal["generated_at"],
    }
