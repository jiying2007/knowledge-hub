"""Verify a machine evidence ratchet without trusting pull-request code."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError
from .evidence import evaluate_evidence_contract
from .schemas import validate_instance

MACHINE_FIELDS = {"source_refs", "validation_refs", "artifact_refs"}
EVENT_RE = re.compile(r"^evidence-binding-([0-9]+)-([0-9]+)$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_json(path: pathlib.Path, label: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("{} is invalid JSON".format(label)) from exc
    if not isinstance(value, Mapping):
        raise KnowledgeHubError("{} must be an object".format(label))
    return dict(value)


def _load_jsonl(path: pathlib.Path, label: str) -> Tuple[bytes, List[Dict[str, Any]]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise KnowledgeHubError("{} is unavailable".format(label)) from exc
    rows: List[Dict[str, Any]] = []
    for number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise KnowledgeHubError(
                "{} line {} is invalid JSON".format(label, number)
            ) from exc
        if not isinstance(value, Mapping):
            raise KnowledgeHubError(
                "{} line {} must be an object".format(label, number)
            )
        rows.append(dict(value))
    return raw, rows


def _reference_key(value: object) -> Tuple[str, str]:
    if not isinstance(value, Mapping):
        return "", ""
    return str(value.get("kind", "")), str(value.get("ref", ""))


def _verify_reference_append(
    base: object,
    head: object,
    *,
    item_id: str,
    field: str,
) -> bool:
    if not isinstance(base, list) or not isinstance(head, list):
        raise KnowledgeHubError(
            "{} {} must remain list-valued".format(item_id, field)
        )
    if head[: len(base)] != base:
        raise KnowledgeHubError(
            "{} {} must preserve the exact canonical prefix".format(
                item_id, field
            )
        )
    appended = head[len(base) :]
    if not appended:
        return False
    for value in appended:
        if not isinstance(value, Mapping) or set(value) != {"kind", "ref"}:
            raise KnowledgeHubError(
                "{} {} appended reference shape is invalid".format(
                    item_id, field
                )
            )
        if not all(_reference_key(value)):
            raise KnowledgeHubError(
                "{} {} appended reference identity is empty".format(
                    item_id, field
                )
            )
    keys = [_reference_key(value) for value in head]
    if len(keys) != len(set(keys)):
        raise KnowledgeHubError(
            "{} {} contains duplicate evidence references".format(
                item_id, field
            )
        )
    return True


def _verify_head_contract_readiness(
    item_id: str,
    contract: Mapping[str, Any],
) -> None:
    evaluation = evaluate_evidence_contract(contract)
    if evaluation.get("declared_status") != "pending":
        raise KnowledgeHubError(
            "{} machine ratchet changed declared readiness".format(item_id)
        )
    if evaluation.get("status") == "ready":
        raise KnowledgeHubError(
            "{} machine ratchet would auto-promote evidence readiness".format(
                item_id
            )
        )


def _verify_items(
    base_rows: Sequence[Mapping[str, Any]],
    head_rows: Sequence[Mapping[str, Any]],
) -> Tuple[List[str], List[str]]:
    if len(base_rows) != len(head_rows):
        raise KnowledgeHubError("machine ratchet must not add or remove registry items")
    base_ids = [str(row.get("id", "")) for row in base_rows]
    head_ids = [str(row.get("id", "")) for row in head_rows]
    if not all(base_ids) or len(base_ids) != len(set(base_ids)):
        raise KnowledgeHubError("base registry item identity is invalid")
    if head_ids != base_ids:
        raise KnowledgeHubError("machine ratchet must preserve registry item order and identity")

    changed_items: List[str] = []
    changed_fields: List[str] = []
    for base_raw, head_raw in zip(base_rows, head_rows):
        base = dict(base_raw)
        head = dict(head_raw)
        if base == head:
            continue
        item_id = str(base["id"])
        base_contract = base.pop("evidence_contract", None)
        head_contract = head.pop("evidence_contract", None)
        if base != head:
            raise KnowledgeHubError(
                "{} changed outside evidence_contract".format(item_id)
            )
        if not isinstance(base_contract, Mapping) or not isinstance(
            head_contract, Mapping
        ):
            raise KnowledgeHubError(
                "{} evidence_contract is invalid".format(item_id)
            )
        if set(base_contract) != set(head_contract):
            raise KnowledgeHubError(
                "{} evidence_contract field set changed".format(item_id)
            )
        item_fields: List[str] = []
        for field in sorted(base_contract):
            before = base_contract.get(field)
            after = head_contract.get(field)
            if before == after:
                continue
            if field not in MACHINE_FIELDS:
                raise KnowledgeHubError(
                    "{} changed forbidden evidence field {}".format(
                        item_id, field
                    )
                )
            if not _verify_reference_append(
                before,
                after,
                item_id=item_id,
                field=field,
            ):
                raise KnowledgeHubError(
                    "{} {} changed without an append".format(item_id, field)
                )
            item_fields.append(field)
        if not item_fields:
            raise KnowledgeHubError(
                "{} changed without an allowed evidence append".format(item_id)
            )
        _verify_head_contract_readiness(item_id, head_contract)
        changed_items.append(item_id)
        changed_fields.extend(item_fields)
    if not changed_items:
        raise KnowledgeHubError("machine ratchet contains no canonical evidence change")
    return changed_items, sorted(set(changed_fields))


def _verify_ledger(
    root: pathlib.Path,
    base_raw: bytes,
    head_raw: bytes,
    *,
    repository: str,
    master_sha: str,
) -> Tuple[Dict[str, Any], int, int]:
    if base_raw and not base_raw.endswith(b"\n"):
        raise KnowledgeHubError("base durable ledger is not canonical JSONL")
    if not head_raw.startswith(base_raw):
        raise KnowledgeHubError("durable ledger must preserve the exact base prefix")
    tail = head_raw[len(base_raw) :]
    rows = [line for line in tail.splitlines() if line.strip()]
    if len(rows) != 1:
        raise KnowledgeHubError("machine ratchet must append exactly one durable record")
    try:
        record = json.loads(rows[0].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("appended durable record is invalid JSON") from exc
    if not isinstance(record, Mapping):
        raise KnowledgeHubError("appended durable record must be an object")
    record = dict(record)
    validation = validate_instance(root, "durable-evidence-record-v1", record)
    if validation.get("status") != "pass":
        raise KnowledgeHubError(
            "appended durable record violates schema: {}".format(
                validation.get("errors", [])
            )
        )
    if record.get("event_type") != "evidence-binding-ratchet":
        raise KnowledgeHubError("durable record type is not evidence-binding-ratchet")
    if record.get("source_revision") != master_sha:
        raise KnowledgeHubError("durable record source revision is not current master")
    match = EVENT_RE.fullmatch(str(record.get("event_id", "")))
    if match is None:
        raise KnowledgeHubError("durable event identity is invalid")
    run_id = int(match.group(1))
    run_attempt = int(match.group(2))
    expected_ref = "https://github.com/{}/actions/runs/{}".format(
        repository, run_id
    )
    if record.get("evidence_refs") != [expected_ref]:
        raise KnowledgeHubError("durable evidence reference is not exact")
    digests = record.get("digests", {})
    if not isinstance(digests, Mapping) or set(digests) != {
        "routing_bundle",
        "machine_candidate",
        "machine_manifest",
    }:
        raise KnowledgeHubError("durable evidence digest set is invalid")
    if any(not DIGEST_RE.fullmatch(str(value)) for value in digests.values()):
        raise KnowledgeHubError("durable evidence digest format is invalid")
    return record, run_id, run_attempt


def _verify_origin_run(
    run: Mapping[str, Any],
    record: Mapping[str, Any],
    *,
    repository: str,
    master_sha: str,
    run_id: int,
    run_attempt: int,
) -> None:
    expected = {
        "id": run_id,
        "run_attempt": run_attempt,
        "name": "ai-provider-discovery",
        "path": ".github/workflows/ai-provider-discovery.yml",
        "head_sha": master_sha,
        "head_branch": "master",
        "status": "completed",
        "conclusion": "success",
    }
    for field, value in expected.items():
        if run.get(field) != value:
            raise KnowledgeHubError(
                "origin run {} mismatch: expected={!r} observed={!r}".format(
                    field, value, run.get(field)
                )
            )
    if run.get("event") not in {"workflow_run", "schedule", "workflow_dispatch"}:
        raise KnowledgeHubError("origin run event is not trusted")
    repository_row = run.get("repository") or {}
    if not isinstance(repository_row, Mapping) or repository_row.get(
        "full_name"
    ) != repository:
        raise KnowledgeHubError("origin run repository identity mismatch")
    observed_at = str(run.get("run_started_at") or run.get("created_at") or "")
    if record.get("observed_at") != observed_at:
        raise KnowledgeHubError("durable observed_at does not match origin run")


def _verify_artifact(
    root: pathlib.Path,
    record: Mapping[str, Any],
    *,
    base_items_raw: bytes,
    head_items_raw: bytes,
    routing_path: pathlib.Path,
    candidate_path: pathlib.Path,
    manifest_path: pathlib.Path,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    routing = _load_json(routing_path, "routing bundle")
    manifest = _load_json(manifest_path, "machine candidate manifest")
    for contract_id, payload in (
        ("operator-auto-route-v1", routing),
        ("operator-machine-ratchet-candidate-v1", manifest),
    ):
        validation = validate_instance(root, contract_id, payload)
        if validation.get("status") != "pass":
            raise KnowledgeHubError(
                "{} validation failed: {}".format(
                    contract_id, validation.get("errors", [])
                )
            )
    candidate_raw = candidate_path.read_bytes()
    if candidate_raw != head_items_raw:
        raise KnowledgeHubError(
            "origin machine candidate bytes do not equal pull-request registry bytes"
        )
    base_sha = _sha256(base_items_raw)
    head_sha = _sha256(head_items_raw)
    if manifest.get("registry_before_sha256") != base_sha:
        raise KnowledgeHubError("machine manifest base registry digest mismatch")
    if manifest.get("registry_after_sha256") != head_sha:
        raise KnowledgeHubError("machine manifest head registry digest mismatch")
    if manifest.get("candidate_sha256") != head_sha:
        raise KnowledgeHubError("machine manifest candidate digest mismatch")
    machine_route = routing.get("machine_route", {})
    if not isinstance(machine_route, Mapping):
        raise KnowledgeHubError("routing machine subroute is invalid")
    if machine_route.get("status") != "ready-for-machine-ratchet":
        raise KnowledgeHubError("routing machine subroute is not ready")
    if manifest.get("selected_proposal_fingerprints") != machine_route.get(
        "selected_proposal_fingerprints"
    ):
        raise KnowledgeHubError("routing and machine manifest selection mismatch")

    digests = record["digests"]
    actual = {
        "routing_bundle": "sha256:" + _sha256(routing_path.read_bytes()),
        "machine_candidate": "sha256:" + _sha256(candidate_raw),
        "machine_manifest": "sha256:" + _sha256(manifest_path.read_bytes()),
    }
    if dict(digests) != actual:
        raise KnowledgeHubError("durable origin artifact digest mismatch")
    return routing, manifest


def verify_machine_evidence_ratchet(
    root: pathlib.Path,
    *,
    base_items_path: pathlib.Path,
    head_items_path: pathlib.Path,
    base_ledger_path: pathlib.Path,
    head_ledger_path: pathlib.Path,
    routing_path: pathlib.Path,
    candidate_path: pathlib.Path,
    manifest_path: pathlib.Path,
    origin_run_path: pathlib.Path,
    repository: str,
    master_sha: str,
    head_sha: str,
) -> Dict[str, Any]:
    """Verify exact PR semantics, durable provenance and origin artifacts."""

    root = pathlib.Path(root).resolve()
    if not SHA_RE.fullmatch(master_sha) or not SHA_RE.fullmatch(head_sha):
        raise KnowledgeHubError("master/head revisions must be lowercase git SHAs")
    base_items_raw, base_rows = _load_jsonl(base_items_path, "base registry")
    head_items_raw, head_rows = _load_jsonl(head_items_path, "head registry")
    base_ledger_raw, _ = _load_jsonl(base_ledger_path, "base durable ledger")
    head_ledger_raw, _ = _load_jsonl(head_ledger_path, "head durable ledger")

    changed_items, changed_fields = _verify_items(base_rows, head_rows)
    record, run_id, run_attempt = _verify_ledger(
        root,
        base_ledger_raw,
        head_ledger_raw,
        repository=repository,
        master_sha=master_sha,
    )
    origin_run = _load_json(origin_run_path, "origin run")
    _verify_origin_run(
        origin_run,
        record,
        repository=repository,
        master_sha=master_sha,
        run_id=run_id,
        run_attempt=run_attempt,
    )
    routing, manifest = _verify_artifact(
        root,
        record,
        base_items_raw=base_items_raw,
        head_items_raw=head_items_raw,
        routing_path=routing_path,
        candidate_path=candidate_path,
        manifest_path=manifest_path,
    )
    return {
        "schema_version": 1,
        "projection": "knowledge-operator-machine-ratchet-verification-v1",
        "status": "pass",
        "read_only": True,
        "canonical_write_performed": False,
        "repository": repository,
        "master_sha": master_sha,
        "head_sha": head_sha,
        "changed_item_count": len(changed_items),
        "changed_item_ids": changed_items,
        "changed_fields": changed_fields,
        "origin_run_id": run_id,
        "origin_run_attempt": run_attempt,
        "routing_status": routing.get("status", ""),
        "selected_proposal_count": manifest.get("selected_proposal_count", 0),
        "candidate_sha256": manifest.get("candidate_sha256", ""),
    }
