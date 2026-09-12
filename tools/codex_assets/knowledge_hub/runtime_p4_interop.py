"""Provider-side P4 interoperability contracts for Knowledge Runtime.

This module does not move source-of-truth ownership into Knowledge Hub. It only
validates consumer identity, provider capability compatibility, A2A handoff
preflight, and optional local execution-receipt correlation.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError, load_json, load_jsonl
from .runtime_v3_contracts import (
    A2A_PROTOCOL_VERSION,
    MCP_PROTOCOL_VERSION,
    agent_profile,
    capability_catalog,
    config,
    require_capability,
)
from .runtime_v3_governance import _validate_receipt_chain, a2a_preflight

DEFAULT_CONSUMER = "digital-worker"
INTEGRATION_DIRECTORY = "registry/integrations"
P4_CONFIG_PATH = "registry/knowledge-runtime-p4.json"
MAX_IDENTIFIER_CHARS = 512
MAX_TASK_CHARS = 8192
MAX_CAPABILITIES = 32
MAX_EVIDENCE_IDS = 64
_CONSUMER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _bounded_text(value: Any, label: str, maximum: int) -> str:
    text = str(value).strip()
    if not text or len(text) > maximum:
        raise KnowledgeHubError("{} must be non-empty and bounded".format(label))
    return text


def _bounded_strings(
    values: Sequence[Any], *, label: str, maximum: int
) -> List[str]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise KnowledgeHubError("{} must be a sequence".format(label))
    if len(values) > maximum:
        raise KnowledgeHubError("{} exceeds {} values".format(label, maximum))
    result = []
    for value in values:
        result.append(_bounded_text(value, label, MAX_IDENTIFIER_CHARS))
    return result


def _consumer_name(value: str) -> str:
    consumer = str(value).strip()
    if not _CONSUMER_PATTERN.fullmatch(consumer):
        raise KnowledgeHubError("invalid integration consumer")
    return consumer


def p4_program(root: pathlib.Path) -> Dict[str, Any]:
    value = load_json(root / P4_CONFIG_PATH, None)
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("missing or invalid {}".format(P4_CONFIG_PATH))
    program = dict(value)
    if str(program.get("extends", "")) != "registry/knowledge-runtime-v3.json":
        raise KnowledgeHubError("P4 program must extend the governed v3 runtime")
    if not isinstance(program.get("consumer_contracts"), Sequence) or isinstance(
        program.get("consumer_contracts"), (str, bytes)
    ):
        raise KnowledgeHubError("P4 consumer_contracts must be a sequence")
    return program


def integration_contract(
    root: pathlib.Path, consumer: str = DEFAULT_CONSUMER
) -> Dict[str, Any]:
    consumer = _consumer_name(consumer)
    path = root / INTEGRATION_DIRECTORY / "{}.json".format(consumer)
    value = load_json(path, None)
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("missing integration contract: {}".format(consumer))
    contract = dict(value)
    if str(contract.get("consumer", "")) != consumer:
        raise KnowledgeHubError("integration consumer identity mismatch")
    if str(contract.get("provider", "")) != "knowledge-hub":
        raise KnowledgeHubError("integration provider identity mismatch")
    if not isinstance(contract.get("ssot"), Mapping):
        raise KnowledgeHubError("integration contract missing SSOT boundary")
    if not isinstance(contract.get("identity"), Mapping):
        raise KnowledgeHubError("integration contract missing identity contract")
    return contract


def _surface_paths(contract: Mapping[str, Any]) -> Dict[str, str]:
    surfaces: Dict[str, str] = {}
    for group_name in ("read_surfaces", "write_surfaces"):
        group = contract.get(group_name, {})
        if not isinstance(group, Mapping):
            raise KnowledgeHubError(
                "integration contract {} must be an object".format(group_name)
            )
        for name, path in group.items():
            surfaces["{}.{}".format(group_name, name)] = str(path)
    runtime_contract = contract.get("runtime_contract", {})
    if isinstance(runtime_contract, Mapping):
        entrypoint = str(runtime_contract.get("provider_entrypoint", "")).strip()
        if entrypoint:
            surfaces["runtime_contract.provider_entrypoint"] = entrypoint
    return surfaces


def _safe_surface_exists(root: pathlib.Path, relative: str) -> bool:
    pure = pathlib.PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        return False
    return (root / pathlib.Path(*pure.parts)).is_file()


def integration_readiness(
    root: pathlib.Path, consumer: str = DEFAULT_CONSUMER
) -> Dict[str, Any]:
    contract = integration_contract(root, consumer)
    program = p4_program(root)
    runtime_contract = contract.get("runtime_contract", {})
    if not isinstance(runtime_contract, Mapping):
        raise KnowledgeHubError("integration contract missing runtime_contract")
    required_capabilities = _bounded_strings(
        runtime_contract.get("required_provider_capabilities", []),
        label="required_provider_capabilities",
        maximum=MAX_CAPABILITIES,
    )
    catalog = capability_catalog(root)
    missing_capabilities = sorted(
        capability
        for capability in required_capabilities
        if capability not in catalog
    )
    surfaces = _surface_paths(contract)
    missing_surfaces = sorted(
        name for name, path in surfaces.items() if not _safe_surface_exists(root, path)
    )
    expected_protocols = runtime_contract.get("protocols", {})
    if not isinstance(expected_protocols, Mapping):
        raise KnowledgeHubError("integration protocols must be an object")
    runtime_protocols = config(root).get("protocols", {})
    if not isinstance(runtime_protocols, Mapping):
        raise KnowledgeHubError("runtime protocols must be an object")
    protocol_mismatches = sorted(
        protocol
        for protocol, expected in expected_protocols.items()
        if str(runtime_protocols.get(protocol, "")) != str(expected)
    )
    expected_contract_path = "{}/{}.json".format(INTEGRATION_DIRECTORY, consumer)
    consumer_contracts = {str(value) for value in program.get("consumer_contracts", [])}
    errors = []
    if expected_contract_path not in consumer_contracts:
        errors.append("consumer-contract-not-governed")
    if missing_capabilities:
        errors.append("missing-provider-capabilities")
    if missing_surfaces:
        errors.append("missing-provider-surfaces")
    if protocol_mismatches:
        errors.append("protocol-mismatch")
    return {
        "schema_version": "knowledge-hub.integration-readiness.v1",
        "status": "pass" if not errors else "needs-fix",
        "consumer": consumer,
        "provider": "knowledge-hub",
        "contract_version": str(contract.get("contract_version", "")),
        "program_status": str(program.get("status", "")),
        "required_provider_capabilities": required_capabilities,
        "missing_provider_capabilities": missing_capabilities,
        "missing_provider_surfaces": missing_surfaces,
        "protocol_mismatches": protocol_mismatches,
        "source_of_truth_policy": contract.get("source_of_truth_policy", ""),
        "direct_active_mutation": bool(
            contract.get("write_policy", {}).get("direct_active_mutation", False)
        )
        if isinstance(contract.get("write_policy"), Mapping)
        else False,
        "network_required": bool(runtime_contract.get("network_required", False)),
        "errors": errors,
    }


def _normalized_identity(
    contract: Mapping[str, Any], identity: Mapping[str, Any]
) -> Tuple[Dict[str, str], List[str]]:
    identity_contract = contract.get("identity", {})
    if not isinstance(identity_contract, Mapping):
        raise KnowledgeHubError("integration identity contract must be an object")
    required_inputs = _bounded_strings(
        identity_contract.get("required_inputs", []),
        label="identity required_inputs",
        maximum=16,
    )
    normalized: Dict[str, str] = {}
    missing = []
    for field in required_inputs:
        value = str(identity.get(field, "")).strip()
        if not value:
            missing.append(field)
            continue
        normalized[field] = _bounded_text(
            value, "identity {}".format(field), MAX_IDENTIFIER_CHARS
        )
    return normalized, sorted(missing)


def _requested_capability_risk(
    root: pathlib.Path, requested_capabilities: Sequence[str]
) -> Tuple[List[str], List[str], List[str]]:
    requested = sorted(
        set(
            _bounded_strings(
                requested_capabilities,
                label="requested_capabilities",
                maximum=MAX_CAPABILITIES,
            )
        )
    )
    catalog = capability_catalog(root)
    unknown = sorted(capability for capability in requested if capability not in catalog)
    high_risk = sorted(
        capability
        for capability in requested
        if capability in catalog
        and (
            bool(catalog[capability].get("requires_human_approval", False))
            or str(catalog[capability].get("mode", "")) == "write"
        )
    )
    return requested, unknown, high_risk


def _protocol_mismatches(mcp_version: str, a2a_version: str) -> List[str]:
    mismatches = []
    if mcp_version and mcp_version != MCP_PROTOCOL_VERSION:
        mismatches.append("mcp")
    if a2a_version and a2a_version != A2A_PROTOCOL_VERSION:
        mismatches.append("a2a")
    return mismatches


def consumer_handshake(
    root: pathlib.Path,
    consumer: str,
    agent_id: str,
    identity: Mapping[str, Any],
    requested_capabilities: Sequence[str] = (),
    *,
    mcp_version: str = "",
    a2a_version: str = "",
) -> Dict[str, Any]:
    require_capability(root, agent_id, "a2a.preflight")
    agent_profile(root, agent_id)
    contract = integration_contract(root, consumer)
    readiness = integration_readiness(root, consumer)
    normalized_identity, missing_identity = _normalized_identity(contract, identity)
    requested, unknown, high_risk = _requested_capability_risk(
        root, requested_capabilities
    )
    protocol_mismatches = _protocol_mismatches(mcp_version, a2a_version)
    blocked = bool(
        missing_identity
        or protocol_mismatches
        or readiness.get("status") != "pass"
    )
    needs_review = bool(unknown or high_risk)
    status = "blocked" if blocked else "needs-review" if needs_review else "ready"
    return {
        "schema_version": "knowledge-hub.integration-handshake.v1",
        "status": status,
        "consumer": consumer,
        "provider": "knowledge-hub",
        "agent_id": agent_id,
        "identity": normalized_identity,
        "missing_identity_fields": missing_identity,
        "requested_capabilities": requested,
        "unknown_capabilities": unknown,
        "high_risk_capabilities": high_risk,
        "protocols": {"mcp": MCP_PROTOCOL_VERSION, "a2a": A2A_PROTOCOL_VERSION},
        "protocol_mismatches": protocol_mismatches,
        "readiness": readiness,
        "human_review_required": needs_review,
        "task_execution_authorized": False,
        "canonical_write_permitted": False,
        "source_of_truth_policy": contract.get("source_of_truth_policy", ""),
        "ssot": contract.get("ssot", {}),
    }


def correlate_execution_receipt(
    root: pathlib.Path, receipt_sha256: str
) -> Dict[str, Any]:
    receipt_sha256 = str(receipt_sha256).strip()
    if not receipt_sha256:
        return {
            "status": "not-provided",
            "verified": False,
            "receipt_sha256": "",
        }
    if not _SHA256_PATTERN.fullmatch(receipt_sha256):
        raise KnowledgeHubError("execution receipt digest must be lowercase SHA256")
    path = (
        root
        / ".cache"
        / "knowledge-hub"
        / "runtime-v3"
        / "execution-receipts.jsonl"
    )
    if not path.exists():
        return {
            "status": "missing",
            "verified": False,
            "receipt_sha256": receipt_sha256,
        }
    ledger = load_jsonl(path, maximum_bytes=16 * 1024 * 1024)
    _validate_receipt_chain(ledger)
    match = next(
        (
            row
            for row in ledger
            if str(row.get("receipt_sha256", "")) == receipt_sha256
        ),
        None,
    )
    if not isinstance(match, Mapping):
        return {
            "status": "missing",
            "verified": False,
            "receipt_sha256": receipt_sha256,
        }
    action = str(match.get("action", ""))
    return {
        "status": "verified",
        "verified": True,
        "receipt_sha256": receipt_sha256,
        "agent_id": str(match.get("agent_id", "")),
        "verdict": str(match.get("verdict", "")),
        "action_sha256": hashlib.sha256(action.encode("utf-8")).hexdigest(),
    }


def _handoff_id(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "kh-handoff-{}".format(hashlib.sha256(encoded).hexdigest()[:24])


def _handoff_status(
    handshake: Mapping[str, Any],
    preflight: Mapping[str, Any],
    receipt: Mapping[str, Any],
    receipt_sha256: str,
) -> Tuple[str, bool]:
    if handshake.get("status") == "blocked":
        return "blocked", True
    needs_review = bool(
        handshake.get("status") == "needs-review"
        or preflight.get("status") != "pass"
        or (receipt_sha256 and not bool(receipt.get("verified", False)))
    )
    return ("needs-review" if needs_review else "ready"), needs_review


def _handoff_correlation(
    consumer: str,
    identity: Mapping[str, Any],
    from_agent: str,
    to_agent: str,
    task_sha256: str,
    requested: Sequence[str],
    evidence: Sequence[str],
    receipt_sha256: str,
) -> Dict[str, Any]:
    return {
        "consumer": consumer,
        "work_item_id": identity.get("work_item_id", ""),
        "run_id": identity.get("run_id", ""),
        "scope_ref": identity.get("scope_ref", ""),
        "from_agent": from_agent,
        "to_agent": to_agent,
        "task_sha256": task_sha256,
        "requested_capabilities": list(requested),
        "evidence_ids": list(evidence),
        "execution_receipt_sha256": receipt_sha256,
    }


def handoff_envelope(
    root: pathlib.Path,
    consumer: str,
    from_agent: str,
    to_agent: str,
    task: str,
    identity: Mapping[str, Any],
    requested_capabilities: Sequence[str],
    *,
    evidence_ids: Sequence[str] = (),
    execution_receipt_sha256: str = "",
    mcp_version: str = "",
    a2a_version: str = "",
) -> Dict[str, Any]:
    require_capability(root, from_agent, "a2a.preflight")
    task_text = _bounded_text(task, "handoff task", MAX_TASK_CHARS)
    task_sha256 = hashlib.sha256(task_text.encode("utf-8")).hexdigest()
    requested, _, _ = _requested_capability_risk(root, requested_capabilities)
    evidence = _bounded_strings(
        evidence_ids, label="evidence_ids", maximum=MAX_EVIDENCE_IDS
    )
    handshake = consumer_handshake(
        root, consumer, from_agent, identity, requested,
        mcp_version=mcp_version, a2a_version=a2a_version,
    )
    preflight = a2a_preflight(root, from_agent, to_agent, task_text, requested)
    receipt = correlate_execution_receipt(root, execution_receipt_sha256)
    normalized_identity = dict(handshake.get("identity", {}))
    correlation = _handoff_correlation(
        consumer, normalized_identity, from_agent, to_agent, task_sha256,
        requested, evidence, execution_receipt_sha256,
    )
    status, needs_review = _handoff_status(
        handshake, preflight, receipt, execution_receipt_sha256
    )
    contract = integration_contract(root, consumer)
    return {
        "schema_version": "knowledge-hub.agent-handoff.v1",
        "status": status,
        "handoff_id": _handoff_id(correlation),
        "consumer": consumer,
        "provider": "knowledge-hub",
        "identity": normalized_identity,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "task_sha256": task_sha256,
        "task_echoed": False,
        "requested_capabilities": requested,
        "evidence_ids": evidence,
        "execution_receipt": receipt,
        "handshake_status": handshake.get("status"),
        "a2a_preflight": preflight,
        "human_review_required": bool(
            needs_review or preflight.get("human_review_required", False)
        ),
        "handoff_executes_task": False,
        "canonical_write_permitted": False,
        "network_call_performed": False,
        "source_of_truth_policy": contract.get("source_of_truth_policy", ""),
        "consumer_work_item_ssot": True,
    }
