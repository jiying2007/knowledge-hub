"""Build a non-canonical machine-ratchet candidate from hosted real evidence.

The builder never mutates the canonical registry. Real-world observation remains an
external boundary; once strict validation and hosted provenance are satisfied, the
canonical gap closure is a deterministic low-risk ratchet candidate.
"""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import re
from typing import Any, Dict, List, Mapping, Tuple

from .common import KnowledgeHubError, file_sha256, read_bytes_bounded
from .external_evidence import RECEIPT_SCHEMA, SUPPORTED_GAPS

REGISTRY_SCHEMA = 2
INTAKE_PROJECTION = "knowledge-hub-external-evidence-intake-v1"
HOST_BINDING_PROJECTION = "knowledge-hub-external-evidence-intake-host-binding-v1"
PROPOSAL_PROJECTION = "knowledge-hub-external-evidence-ratchet-proposal-v2"
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


def _validate_closure(closure: Mapping[str, Any], closure_sha: str) -> Dict[str, Any]:
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
    refs = closure.get("evidence_source_refs")
    if not isinstance(refs, list) or not refs:
        raise KnowledgeHubError("closure receipt must retain external evidence source refs")
    return {
        "gap_id": gap_id,
        "source_revision": source_revision,
        "payload_sha": payload_sha,
        "closure_sha": closure_sha,
        "observed_at": _text(closure.get("observed_at"), "observed_at", 128),
        "external_refs": [_text(item, "evidence ref") for item in refs],
    }


def _validate_source_provenance(
    value: Any,
    label: str,
) -> Dict[str, Any]:
    provenance = _object(value, label)
    if provenance.get("source_run_head_branch") != "master":
        raise KnowledgeHubError(
            "{} must originate from master".format(label)
        )
    if provenance.get("source_run_event") not in {
        "workflow_dispatch",
        "schedule",
    }:
        raise KnowledgeHubError(
            "{} event is not trusted".format(label)
        )
    workflow_path = _text(
        provenance.get("source_workflow_path"),
        "{} workflow path".format(label),
        512,
    )
    if (
        not workflow_path.startswith(".github/workflows/")
        or not workflow_path.endswith(".yml")
    ):
        raise KnowledgeHubError(
            "{} workflow path is invalid".format(label)
        )
    artifact_digest = _text(
        provenance.get("artifact_digest"),
        "{} artifact digest".format(label),
        128,
    )
    if not artifact_digest.startswith("sha256:"):
        raise KnowledgeHubError(
            "{} artifact digest must use sha256".format(label)
        )
    _sha256(
        artifact_digest.split(":", 1)[1],
        "{} artifact digest".format(label),
    )
    return {
        "repository": _text(
            provenance.get("repository"),
            "{} repository".format(label),
            512,
        ),
        "run_id": _positive_int(
            provenance.get("source_run_id"),
            "{} run id".format(label),
        ),
        "run_attempt": _positive_int(
            provenance.get("source_run_attempt"),
            "{} run attempt".format(label),
        ),
        "run_head": _git_sha(
            provenance.get("source_run_head_sha"),
            "{} run head".format(label),
        ),
        "run_event": str(provenance.get("source_run_event")),
        "workflow_path": workflow_path,
        "artifact_id": _positive_int(
            provenance.get("artifact_id"),
            "{} artifact id".format(label),
        ),
        "artifact_name": _text(
            provenance.get("artifact_name"),
            "{} artifact name".format(label),
            512,
        ),
        "artifact_digest": artifact_digest,
    }


def _validate_intake_links(
    intake: Mapping[str, Any],
    closure_context: Mapping[str, Any],
) -> None:
    if (
        intake.get("schema_version") != 1
        or intake.get("projection") != INTAKE_PROJECTION
    ):
        raise KnowledgeHubError(
            "intake receipt schema/projection is unsupported"
        )
    if (
        intake.get("status") != "pass"
        or intake.get("closure_candidate_only") is not True
    ):
        raise KnowledgeHubError(
            "intake receipt is not a passed closure candidate"
        )
    if intake.get("canonical_write_performed") is not False:
        raise KnowledgeHubError(
            "intake receipt must not report a canonical write"
        )
    if intake.get("gap_id") != closure_context["gap_id"]:
        raise KnowledgeHubError("intake and closure gap ids differ")
    if intake.get("source_revision") != closure_context["source_revision"]:
        raise KnowledgeHubError(
            "intake and closure source revisions differ"
        )
    if (
        intake.get("evidence_payload_sha256")
        != closure_context["payload_sha"]
    ):
        raise KnowledgeHubError(
            "intake and closure evidence digests differ"
        )
    if (
        _sha256(
            intake.get("receipt_sha256"),
            "intake closure receipt digest",
        )
        != closure_context["closure_sha"]
    ):
        raise KnowledgeHubError(
            "intake receipt is not bound to the supplied closure receipt"
        )


def _validate_intake(
    intake: Mapping[str, Any],
    intake_sha: str,
    closure_context: Mapping[str, Any],
) -> Dict[str, Any]:
    _validate_intake_links(intake, closure_context)
    source = _validate_source_provenance(
        intake.get("source_provenance"),
        "source provenance",
    )
    root = _validate_source_provenance(
        intake.get("root_observation_provenance"),
        "root observation provenance",
    )
    if root["repository"] != source["repository"]:
        raise KnowledgeHubError(
            "root observation repository differs from hosted source repository"
        )
    if root["run_head"] != closure_context["source_revision"]:
        raise KnowledgeHubError(
            "root observation revision does not match strict evidence source revision"
        )

    return {
        "intake_sha": intake_sha,
        "repository": source["repository"],
        "source_run_id": source["run_id"],
        "source_run_attempt": source["run_attempt"],
        "source_run_head": source["run_head"],
        "source_run_head_branch": "master",
        "source_run_event": source["run_event"],
        "source_workflow_path": source["workflow_path"],
        "source_artifact_id": source["artifact_id"],
        "source_artifact_name": source["artifact_name"],
        "source_artifact_digest": source["artifact_digest"],
        "root_repository": root["repository"],
        "root_source_run_id": root["run_id"],
        "root_source_run_attempt": root["run_attempt"],
        "root_source_run_head": root["run_head"],
        "root_source_run_event": root["run_event"],
        "root_source_workflow_path": root["workflow_path"],
        "root_source_artifact_id": root["artifact_id"],
        "root_source_artifact_name": root["artifact_name"],
        "root_source_artifact_digest": root["artifact_digest"],
        "intake_run_id": _positive_int(
            intake.get("intake_run_id"),
            "intake run id",
        ),
        "intake_revision": _git_sha(
            intake.get("intake_revision"),
            "intake revision",
        ),
    }

def _validate_binding(
    binding: Mapping[str, Any], binding_sha: str, intake_context: Mapping[str, Any]
) -> Dict[str, Any]:
    if binding.get("schema_version") != 1 or binding.get("projection") != HOST_BINDING_PROJECTION:
        raise KnowledgeHubError("intake host binding schema/projection is unsupported")
    if binding.get("status") != "pass":
        raise KnowledgeHubError("intake host binding must pass")
    if binding.get("workflow_path") != ".github/workflows/external-evidence-intake.yml":
        raise KnowledgeHubError("host binding must originate from external-evidence-intake workflow")
    repository = _text(binding.get("repository"), "intake repository", 512)
    if repository != intake_context["repository"]:
        raise KnowledgeHubError("source and intake repositories differ")
    run_id = _positive_int(binding.get("intake_run_id"), "intake run id")
    run_head = _git_sha(binding.get("intake_run_head_sha"), "intake run head")
    if run_id != intake_context["intake_run_id"]:
        raise KnowledgeHubError("host binding and intake receipt run ids differ")
    if run_head != intake_context["intake_revision"]:
        raise KnowledgeHubError("host binding and intake receipt revisions differ")
    if binding.get("intake_receipt_sha256") != intake_context["intake_sha"]:
        raise KnowledgeHubError("host binding is not bound to the supplied intake receipt")
    artifact_digest = _text(binding.get("artifact_digest"), "intake artifact digest", 128)
    if not artifact_digest.startswith("sha256:"):
        raise KnowledgeHubError("intake artifact digest must use sha256")
    _sha256(artifact_digest.split(":", 1)[1], "intake artifact digest")
    return {
        "binding_sha": binding_sha,
        "intake_run_id": run_id,
        "intake_run_head": run_head,
        "intake_artifact_id": _positive_int(binding.get("artifact_id"), "intake artifact id"),
        "intake_artifact_digest": artifact_digest,
    }


def _find_open_gap(registry: Mapping[str, Any], gap_id: str) -> Dict[str, Any]:
    if registry.get("schema_version") != REGISTRY_SCHEMA:
        raise KnowledgeHubError("canonical registry schema_version is unsupported")
    gaps = registry.get("external_closure_gaps")
    if not isinstance(gaps, list):
        raise KnowledgeHubError("canonical registry external_closure_gaps must be a list")
    matches = [item for item in gaps if isinstance(item, Mapping) and item.get("id") == gap_id]
    if len(matches) != 1:
        raise KnowledgeHubError("canonical registry must contain exactly one requested gap")
    gap = dict(matches[0])
    if gap.get("required") is not True or gap.get("status") != "open":
        raise KnowledgeHubError("requested canonical gap must be required and open")
    if gap.get("evidence_refs") or gap.get("evidence"):
        raise KnowledgeHubError("open canonical gap already contains closure evidence")
    return gap


def _hosted_refs(repository: str, intake: Mapping[str, Any], binding: Mapping[str, Any]) -> List[str]:
    return [
        "https://github.com/{}/actions/runs/{}".format(repository, intake["source_run_id"]),
        "https://github.com/{}/actions/runs/{}/artifacts/{}".format(
            repository, intake["source_run_id"], intake["source_artifact_id"]
        ),
        "https://github.com/{}/actions/runs/{}".format(repository, binding["intake_run_id"]),
        "https://github.com/{}/actions/runs/{}/artifacts/{}".format(
            repository, binding["intake_run_id"], binding["intake_artifact_id"]
        ),
    ]


def _build_candidate(
    registry: Mapping[str, Any], current_gap: Mapping[str, Any], closure: Mapping[str, Any],
    intake: Mapping[str, Any], binding: Mapping[str, Any]
) -> Dict[str, Any]:
    candidate = copy.deepcopy(dict(registry))
    gap_id = closure["gap_id"]
    gaps = candidate["external_closure_gaps"]
    candidate_gap = next(item for item in gaps if item.get("id") == gap_id)
    candidate_gap["status"] = "closed"
    candidate_gap["reason"] = (
        "Real external evidence passed the strict validator and hosted intake chain; "
        "closure is bound to the retained source and intake artifacts."
    )
    refs = list(closure["external_refs"]) + _hosted_refs(intake["repository"], intake, binding)
    candidate_gap["evidence_refs"] = _dedupe_refs(refs)
    candidate_gap["evidence"] = {
        "closure_scope": "{}-only".format(gap_id),
        "terminal_claimed": False,
        "previous_open_reason": str(current_gap.get("reason", "")),
        "source_revision": closure["source_revision"],
        "observed_at": closure["observed_at"],
        "evidence_payload_sha256": closure["payload_sha"],
        "validator_receipt_sha256": closure["closure_sha"],
        "intake_receipt_sha256": intake["intake_sha"],
        "host_binding_sha256": binding["binding_sha"],
        "source_run_head_sha": intake["source_run_head"],
        "source_run_id": intake["source_run_id"],
        "source_run_attempt": intake["source_run_attempt"],
        "source_artifact_id": intake["source_artifact_id"],
        "source_artifact_digest": intake["source_artifact_digest"],
        "root_source_repository": intake["root_repository"],
        "root_source_run_head_sha": intake["root_source_run_head"],
        "root_source_run_id": intake["root_source_run_id"],
        "root_source_run_attempt": intake["root_source_run_attempt"],
        "root_source_workflow_path": intake["root_source_workflow_path"],
        "root_source_artifact_id": intake["root_source_artifact_id"],
        "root_source_artifact_digest": intake["root_source_artifact_digest"],
        "intake_run_head_sha": binding["intake_run_head"],
        "intake_run_id": binding["intake_run_id"],
        "intake_artifact_id": binding["intake_artifact_id"],
        "intake_artifact_digest": binding["intake_artifact_digest"],
        "synthetic_evidence_accepted": False,
        "mock_evidence_accepted": False,
        "local_only_evidence_accepted": False,
        "canonical_write_performed_by_evidence_chain": False,
    }
    return candidate


def build_external_gap_ratchet_candidate(
    *, registry_path: pathlib.Path, closure_receipt_path: pathlib.Path,
    intake_receipt_path: pathlib.Path, host_binding_path: pathlib.Path
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    registry, registry_sha = _load_json(registry_path, "canonical registry")
    closure_raw, closure_sha = _load_json(closure_receipt_path, "closure candidate receipt")
    intake_raw, intake_sha = _load_json(intake_receipt_path, "intake receipt")
    binding_raw, binding_sha = _load_json(host_binding_path, "intake host binding")
    closure = _validate_closure(closure_raw, closure_sha)
    intake = _validate_intake(intake_raw, intake_sha, closure)
    binding = _validate_binding(binding_raw, binding_sha, intake)
    current_gap = _find_open_gap(registry, closure["gap_id"])
    candidate = _build_candidate(registry, current_gap, closure, intake, binding)
    candidate_bytes = (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    proposal = {
        "schema_version": 1,
        "projection": PROPOSAL_PROJECTION,
        "status": "ready-for-machine-ratchet",
        "authorization_class": "autonomous-low-risk-ratchet",
        "review_required": False,
        "canonical_write_performed": False,
        "gap_id": closure["gap_id"],
        "expected_registry_sha256": registry_sha,
        "candidate_registry_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "closure_receipt_sha256": closure_sha,
        "intake_receipt_sha256": intake_sha,
        "host_binding_sha256": binding_sha,
        "source_revision": closure["source_revision"],
        "intake_revision": binding["intake_run_head"],
        "generated_at": closure["observed_at"],
    }
    return candidate, proposal
