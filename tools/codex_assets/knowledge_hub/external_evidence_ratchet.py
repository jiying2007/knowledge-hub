"""Build a review-only canonical registry candidate from hosted external evidence receipts.

The builder deliberately never mutates the canonical registry.  It accepts only a
closure-ready validator receipt that is bound to a successful hosted intake artifact,
then emits a complete candidate registry plus a bounded proposal for human/PR review.
"""

from __future__ import annotations

import copy
import json
import pathlib
import re
from typing import Any, Dict, List, Mapping, Tuple

from .common import KnowledgeHubError, file_sha256, read_bytes_bounded, utc_timestamp
from .external_evidence import RECEIPT_SCHEMA, SUPPORTED_GAPS

REGISTRY_SCHEMA = 2
INTAKE_PROJECTION = "knowledge-hub-external-evidence-intake-v1"
HOST_BINDING_PROJECTION = "knowledge-hub-external-evidence-intake-host-binding-v1"
PROPOSAL_PROJECTION = "knowledge-hub-external-evidence-ratchet-proposal-v1"
MAX_JSON_BYTES = 4 * 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _object(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return dict(value)


def _text(value: Any, label: str, maximum: int = 4096) -> str:
    result = str(value).strip()
    if not result or len(result) > maximum:
        raise KnowledgeHubError("{} must be non-empty and bounded".format(label))
    return result


def _sha256(value: Any, label: str) -> str:
    result = str(value).strip().lower()
    if not SHA256_RE.fullmatch(result):
        raise KnowledgeHubError("{} must be lowercase SHA256".format(label))
    return result


def _git_sha(value: Any, label: str) -> str:
    result = str(value).strip().lower()
    if not GIT_SHA_RE.fullmatch(result):
        raise KnowledgeHubError("{} must be a lowercase 40-character git SHA".format(label))
    return result


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise KnowledgeHubError("{} must be a positive integer".format(label))
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise KnowledgeHubError("{} must be a positive integer".format(label)) from exc
    if result < 1:
        raise KnowledgeHubError("{} must be a positive integer".format(label))
    return result


def _load_json(path: pathlib.Path, label: str) -> Tuple[Dict[str, Any], str]:
    raw = read_bytes_bounded(path, MAX_JSON_BYTES, label)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("{} must be valid UTF-8 JSON".format(label)) from exc
    return _object(value, label), file_sha256(path)


def _dedupe_refs(values: List[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        item = _text(value, "evidence ref")
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def build_external_gap_ratchet_candidate(
    *,
    registry_path: pathlib.Path,
    closure_receipt_path: pathlib.Path,
    intake_receipt_path: pathlib.Path,
    host_binding_path: pathlib.Path,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    registry, registry_sha = _load_json(registry_path, "canonical registry")
    closure, closure_sha = _load_json(closure_receipt_path, "closure candidate receipt")
    intake, intake_sha = _load_json(intake_receipt_path, "intake receipt")
    binding, binding_sha = _load_json(host_binding_path, "intake host binding")

    if registry.get("schema_version") != REGISTRY_SCHEMA:
        raise KnowledgeHubError("canonical registry schema_version is unsupported")
    if closure.get("schema_version") != RECEIPT_SCHEMA:
        raise KnowledgeHubError("closure receipt schema_version is unsupported")
    if closure.get("status") != "pass" or closure.get("closure_ready") is not True:
        raise KnowledgeHubError("closure receipt is not closure-ready")
    gap_id = _text(closure.get("gap_id"), "gap id", 128)
    if gap_id not in SUPPORTED_GAPS:
        raise KnowledgeHubError("gap is not eligible for external evidence ratchet")
    source_revision = _git_sha(closure.get("source_revision"), "source revision")
    payload_sha = _sha256(closure.get("evidence_payload_sha256"), "evidence payload digest")
    for key in (
        "synthetic_evidence_accepted",
        "mock_evidence_accepted",
        "local_only_evidence_accepted",
        "canonical_write_performed",
    ):
        if closure.get(key) is not False:
            raise KnowledgeHubError("closure receipt {} must be false".format(key))

    if intake.get("schema_version") != 1 or intake.get("projection") != INTAKE_PROJECTION:
        raise KnowledgeHubError("intake receipt schema/projection is unsupported")
    if intake.get("status") != "pass" or intake.get("closure_candidate_only") is not True:
        raise KnowledgeHubError("intake receipt is not a passed closure candidate")
    if intake.get("canonical_write_performed") is not False:
        raise KnowledgeHubError("intake receipt must not report a canonical write")
    if intake.get("gap_id") != gap_id:
        raise KnowledgeHubError("intake and closure gap ids differ")
    if intake.get("source_revision") != source_revision:
        raise KnowledgeHubError("intake and closure source revisions differ")
    if intake.get("evidence_payload_sha256") != payload_sha:
        raise KnowledgeHubError("intake and closure evidence digests differ")
    if _sha256(intake.get("receipt_sha256"), "intake closure receipt digest") != closure_sha:
        raise KnowledgeHubError("intake receipt is not bound to the supplied closure receipt")

    source_provenance = _object(intake.get("source_provenance"), "source provenance")
    source_repository = _text(source_provenance.get("repository"), "source repository", 512)
    source_run_id = _positive_int(source_provenance.get("source_run_id"), "source run id")
    source_run_head = _git_sha(source_provenance.get("source_run_head_sha"), "source run head")
    source_artifact_id = _positive_int(source_provenance.get("artifact_id"), "source artifact id")
    source_artifact_digest = _text(source_provenance.get("artifact_digest"), "source artifact digest", 128)
    if not source_artifact_digest.startswith("sha256:"):
        raise KnowledgeHubError("source artifact digest must use sha256")
    _sha256(source_artifact_digest.split(":", 1)[1], "source artifact digest")

    if binding.get("schema_version") != 1 or binding.get("projection") != HOST_BINDING_PROJECTION:
        raise KnowledgeHubError("intake host binding schema/projection is unsupported")
    if binding.get("status") != "pass":
        raise KnowledgeHubError("intake host binding must pass")
    if binding.get("workflow_path") != ".github/workflows/external-evidence-intake.yml":
        raise KnowledgeHubError("host binding must originate from external-evidence-intake workflow")
    intake_run_id = _positive_int(binding.get("intake_run_id"), "intake run id")
    intake_run_head = _git_sha(binding.get("intake_run_head_sha"), "intake run head")
    intake_artifact_id = _positive_int(binding.get("artifact_id"), "intake artifact id")
    intake_artifact_digest = _text(binding.get("artifact_digest"), "intake artifact digest", 128)
    if not intake_artifact_digest.startswith("sha256:"):
        raise KnowledgeHubError("intake artifact digest must use sha256")
    _sha256(intake_artifact_digest.split(":", 1)[1], "intake artifact digest")
    if binding.get("intake_receipt_sha256") != intake_sha:
        raise KnowledgeHubError("host binding is not bound to the supplied intake receipt")
    if int(intake.get("intake_run_id", 0) or 0) != intake_run_id:
        raise KnowledgeHubError("host binding and intake receipt run ids differ")
    if intake.get("intake_revision") != intake_run_head:
        raise KnowledgeHubError("host binding and intake receipt revisions differ")

    gaps = registry.get("external_closure_gaps")
    if not isinstance(gaps, list):
        raise KnowledgeHubError("canonical registry external_closure_gaps must be a list")
    matches = [item for item in gaps if isinstance(item, Mapping) and item.get("id") == gap_id]
    if len(matches) != 1:
        raise KnowledgeHubError("canonical registry must contain exactly one requested gap")
    current_gap = dict(matches[0])
    if current_gap.get("required") is not True or current_gap.get("status") != "open":
        raise KnowledgeHubError("requested canonical gap must be required and open")
    if current_gap.get("evidence_refs") or current_gap.get("evidence"):
        raise KnowledgeHubError("open canonical gap already contains closure evidence")

    external_refs = closure.get("evidence_source_refs")
    if not isinstance(external_refs, list) or len(external_refs) < 1:
        raise KnowledgeHubError("closure receipt must retain external evidence source refs")
    hosted_refs = [
        "https://github.com/{}/actions/runs/{}".format(source_repository, source_run_id),
        "https://github.com/{}/actions/runs/{}/artifacts/{}".format(
            source_repository, source_run_id, source_artifact_id
        ),
        "https://github.com/{}/actions/runs/{}".format(source_repository, intake_run_id),
        "https://github.com/{}/actions/runs/{}/artifacts/{}".format(
            source_repository, intake_run_id, intake_artifact_id
        ),
    ]

    candidate = copy.deepcopy(registry)
    candidate_gaps = candidate["external_closure_gaps"]
    candidate_gap = next(item for item in candidate_gaps if item.get("id") == gap_id)
    candidate_gap["status"] = "closed"
    candidate_gap["reason"] = (
        "Real external evidence passed the strict validator and hosted intake chain; "
        "closure is bound to the retained source and intake artifacts."
    )
    candidate_gap["evidence_refs"] = _dedupe_refs(
        [str(item) for item in external_refs] + hosted_refs
    )
    candidate_gap["evidence"] = {
        "closure_scope": "{}-only".format(gap_id),
        "terminal_claimed": False,
        "previous_open_reason": str(current_gap.get("reason", "")),
        "source_revision": source_revision,
        "observed_at": _text(closure.get("observed_at"), "observed_at", 128),
        "evidence_payload_sha256": payload_sha,
        "validator_receipt_sha256": closure_sha,
        "intake_receipt_sha256": intake_sha,
        "host_binding_sha256": binding_sha,
        "source_run_head_sha": source_run_head,
        "source_run_id": source_run_id,
        "source_artifact_id": source_artifact_id,
        "source_artifact_digest": source_artifact_digest,
        "intake_run_head_sha": intake_run_head,
        "intake_run_id": intake_run_id,
        "intake_artifact_id": intake_artifact_id,
        "intake_artifact_digest": intake_artifact_digest,
        "synthetic_evidence_accepted": False,
        "mock_evidence_accepted": False,
        "local_only_evidence_accepted": False,
        "canonical_write_performed_by_evidence_chain": False,
    }

    candidate_bytes = (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    import hashlib

    candidate_sha = hashlib.sha256(candidate_bytes).hexdigest()
    proposal = {
        "schema_version": 1,
        "projection": PROPOSAL_PROJECTION,
        "status": "ready-for-reviewed-ratchet",
        "review_required": True,
        "canonical_write_performed": False,
        "gap_id": gap_id,
        "expected_registry_sha256": registry_sha,
        "candidate_registry_sha256": candidate_sha,
        "closure_receipt_sha256": closure_sha,
        "intake_receipt_sha256": intake_sha,
        "host_binding_sha256": binding_sha,
        "source_revision": source_revision,
        "intake_revision": intake_run_head,
        "generated_at": utc_timestamp(),
    }
    return candidate, proposal
