"""Validate one externally supplied real observation for hosted evidence intake.

The workflow transport is intentionally narrow: the observation arrives through one
GitHub Actions secret, is schema-validated and semantically projected by the existing
strict pilot validator, and is then written only to a non-canonical artifact path.
This module never invents production/provider fields and never changes lifecycle or
canonical registry state.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import pathlib
import re
from typing import Any, Dict, Mapping, Sequence, Tuple

from .common import (
    KnowledgeHubError,
    ensure_private_directory_tree,
    ensure_private_file,
    repository_root,
    resolve_inside,
)
from .pilot_evidence import build_pilot_evidence
from .schemas import validate_instance

SECRET_ENV = "KNOWLEDGE_REAL_OBSERVATION_B64"
MAX_ENCODED_BYTES = 128 * 1024
MAX_DECODED_BYTES = 96 * 1024
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
CANONICAL_REGISTRY = "registry/knowledge-platform-p5-p10.json"


def _load_policy(root: pathlib.Path) -> Dict[str, Any]:
    path = root / "registry/ai-operations-policy.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("AI operations policy is unavailable or invalid") from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("AI operations policy must be an object")
    return dict(value)


def _contract_for_gap(root: pathlib.Path, gap_id: str) -> Tuple[str, str]:
    policy = _load_policy(root)
    external = policy.get("external_evidence")
    if not isinstance(external, Mapping):
        raise KnowledgeHubError("external evidence policy must be an object")
    supported = external.get("supported_gaps")
    contracts = external.get("observation_contracts")
    allowlists = external.get("observation_source_workflow_allowlist")
    if not isinstance(supported, list) or gap_id not in supported:
        raise KnowledgeHubError("real observation gap is not supported")
    if not isinstance(contracts, Mapping) or not isinstance(allowlists, Mapping):
        raise KnowledgeHubError("real observation registration policy is invalid")
    contract_id = str(contracts.get(gap_id) or "")
    workflows = allowlists.get(gap_id)
    if not contract_id or not isinstance(workflows, list) or len(workflows) != 1:
        raise KnowledgeHubError("real observation gap must have exactly one registered workflow")
    workflow_path = str(workflows[0] or "")
    prefix = str(external.get("observation_source_workflow_prefix") or "")
    if not prefix or not workflow_path.startswith(prefix):
        raise KnowledgeHubError("real observation workflow is outside the reserved namespace")
    if not (root / workflow_path).is_file():
        raise KnowledgeHubError("registered real observation workflow is unavailable")
    return contract_id, workflow_path


def _decode_observation(encoded: str) -> Dict[str, Any]:
    if not isinstance(encoded, str) or not encoded.strip():
        raise KnowledgeHubError("real observation secret is not configured")
    try:
        encoded_bytes = encoded.strip().encode("ascii")
    except UnicodeEncodeError as exc:
        raise KnowledgeHubError("real observation secret must be base64 ASCII") from exc
    if len(encoded_bytes) > MAX_ENCODED_BYTES:
        raise KnowledgeHubError("real observation secret exceeds encoded byte budget")
    try:
        raw = base64.b64decode(encoded_bytes, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise KnowledgeHubError("real observation secret is invalid base64") from exc
    if not raw or len(raw) > MAX_DECODED_BYTES:
        raise KnowledgeHubError("real observation payload exceeds decoded byte budget")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("real observation payload is invalid JSON") from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("real observation payload must be an object")
    return dict(value)


def prepare_real_observation(
    root: pathlib.Path,
    *,
    encoded: str,
    expected_gap: str,
    source_revision: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    source_revision = str(source_revision or "").strip().lower()
    if not GIT_SHA_RE.fullmatch(source_revision):
        raise KnowledgeHubError("source revision must be a lowercase 40-character git SHA")
    contract_id, workflow_path = _contract_for_gap(root, expected_gap)
    observation = _decode_observation(encoded)
    if observation.get("gap_id") != expected_gap:
        raise KnowledgeHubError("real observation gap does not match expected gap")
    if str(observation.get("source_revision") or "").lower() != source_revision:
        raise KnowledgeHubError("real observation source revision does not match workflow run")
    validation = validate_instance(root, contract_id, observation)
    if validation.get("status") != "pass":
        raise KnowledgeHubError(
            "real observation schema validation failed: {}".format(
                validation.get("errors", [])
            )
        )

    # Reuse the strict semantic projection without retaining the projected
    # closure evidence here. This rejects underfilled/synthetic/unsafe payloads
    # before the observation artifact can become a trusted source run.
    build_pilot_evidence(observation, expected_gap=expected_gap)

    canonical = json.dumps(
        observation,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    receipt = {
        "schema_version": 1,
        "projection": "knowledge-hub-real-observation-ingress-v1",
        "status": "pass",
        "gap_id": expected_gap,
        "contract_id": contract_id,
        "source_revision": source_revision,
        "source_workflow_path": workflow_path,
        "observed_at": str(observation.get("observed_at") or ""),
        "observation_sha256": hashlib.sha256(canonical).hexdigest(),
        "input_transport": "github-actions-secret-base64",
        "raw_observation_logged": False,
        "canonical_write_performed": False,
        "owner_decision_generated": False,
    }
    return observation, receipt


def _write_json(root: pathlib.Path, relative: str, payload: Mapping[str, Any]) -> None:
    path = resolve_inside(root, relative)
    if path == resolve_inside(root, CANONICAL_REGISTRY):
        raise KnowledgeHubError("real observation ingress must never write canonical registry")
    ensure_private_directory_tree(root, path.parent)
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    ensure_private_file(path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="")
    parser.add_argument("--expected-gap", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--receipt-output", required=True)
    return parser


def main(argv: Sequence[str] = ()) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv else None)
    try:
        root = repository_root(args.root)
        observation, receipt = prepare_real_observation(
            root,
            encoded=os.environ.get(SECRET_ENV, ""),
            expected_gap=args.expected_gap,
            source_revision=args.source_revision,
        )
        _write_json(root, args.output, observation)
        _write_json(root, args.receipt_output, receipt)
    except (KnowledgeHubError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(receipt, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
