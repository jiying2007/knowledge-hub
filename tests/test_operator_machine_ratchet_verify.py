from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest import mock

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance
from tools.codex_assets.knowledge_hub.operator_machine_ratchet_verify import (
    verify_machine_evidence_ratchet,
)


MASTER = "a" * 40
HEAD = "b" * 40
RUN_ID = 123
RUN_ATTEMPT = 1
FP = "sha256:" + "c" * 64
REPOSITORY = "example/knowledge-hub"


def _write_json(path, payload):
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path, rows):
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract():
    return {
        "profile": "software-tool",
        "status": "pending",
        "source_refs": [],
        "validation_refs": [],
        "artifact_refs": [],
        "release_ref": None,
    }


def _item(contract=None):
    return {
        "id": "item-1",
        "project_id": "project-1",
        "path": "projects/project-1/validation/project-readiness.md",
        "owner": "owner-a",
        "evidence_contract": contract or _contract(),
    }


def _fixture(tmp_path):
    base_items = tmp_path / "base-items.jsonl"
    head_items = tmp_path / "head-items.jsonl"
    base_ledger = tmp_path / "base-ledger.jsonl"
    head_ledger = tmp_path / "head-ledger.jsonl"
    routing = tmp_path / "routing.json"
    candidate = tmp_path / "candidate.jsonl"
    manifest = tmp_path / "manifest.json"
    origin = tmp_path / "origin.json"

    base_contract = _contract()
    head_contract = _contract()
    head_contract["source_refs"] = [
        {
            "kind": "github-source-revision",
            "ref": "github://example/project@" + "1" * 40,
        }
    ]
    _write_jsonl(base_items, [_item(base_contract)])
    _write_jsonl(head_items, [_item(head_contract)])
    candidate.write_bytes(head_items.read_bytes())
    base_ledger.write_bytes(b"")

    route_payload = {
        "status": "ready-for-machine-ratchet",
        "machine_route": {
            "status": "ready-for-machine-ratchet",
            "selected_proposal_fingerprints": [FP],
        },
    }
    _write_json(routing, route_payload)
    manifest_payload = {
        "status": "ready-for-machine-ratchet",
        "selected_proposal_count": 1,
        "selected_proposal_fingerprints": [FP],
        "registry_before_sha256": _sha(base_items),
        "registry_after_sha256": _sha(head_items),
        "candidate_sha256": _sha(candidate),
    }
    _write_json(manifest, manifest_payload)

    observed_at = "2026-09-20T00:00:00Z"
    record = {
        "schema_version": 1,
        "event_id": "evidence-binding-{}-{}".format(RUN_ID, RUN_ATTEMPT),
        "event_type": "evidence-binding-ratchet",
        "source_revision": MASTER,
        "observed_at": observed_at,
        "evidence_refs": [
            "https://github.com/{}/actions/runs/{}".format(
                REPOSITORY, RUN_ID
            )
        ],
        "digests": {
            "routing_bundle": "sha256:" + _sha(routing),
            "machine_candidate": "sha256:" + _sha(candidate),
            "machine_manifest": "sha256:" + _sha(manifest),
        },
        "expires_at": None,
        "notes": "bounded machine evidence ratchet",
    }
    _write_jsonl(head_ledger, [record])
    _write_json(
        origin,
        {
            "id": RUN_ID,
            "run_attempt": RUN_ATTEMPT,
            "name": "ai-provider-discovery",
            "path": ".github/workflows/ai-provider-discovery.yml",
            "head_sha": MASTER,
            "head_branch": "master",
            "status": "completed",
            "conclusion": "success",
            "event": "workflow_run",
            "run_started_at": observed_at,
            "repository": {"full_name": REPOSITORY},
        },
    )
    return {
        "base_items": base_items,
        "head_items": head_items,
        "base_ledger": base_ledger,
        "head_ledger": head_ledger,
        "routing": routing,
        "candidate": candidate,
        "manifest": manifest,
        "origin": origin,
    }


def _verify(tmp_path, paths):
    return verify_machine_evidence_ratchet(
        Path(tmp_path),
        base_items_path=paths["base_items"],
        head_items_path=paths["head_items"],
        base_ledger_path=paths["base_ledger"],
        head_ledger_path=paths["head_ledger"],
        routing_path=paths["routing"],
        candidate_path=paths["candidate"],
        manifest_path=paths["manifest"],
        origin_run_path=paths["origin"],
        repository=REPOSITORY,
        master_sha=MASTER,
        head_sha=HEAD,
    )


def _schema_pass(_root, _contract, _payload):
    return {"status": "pass", "errors": []}


def test_machine_evidence_ratchet_verifier_accepts_exact_append_only_chain(tmp_path):
    paths = _fixture(tmp_path)
    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet_verify."
        "validate_instance",
        side_effect=_schema_pass,
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet_verify."
        "evaluate_evidence_contract",
        return_value={"declared_status": "pending", "status": "pending"},
    ):
        result = _verify(tmp_path, paths)

    assert result["status"] == "pass"
    assert result["changed_item_ids"] == ["item-1"]
    assert result["changed_fields"] == ["source_refs"]
    assert result["origin_run_id"] == RUN_ID
    assert result["origin_run_attempt"] == RUN_ATTEMPT
    assert (
        validate_instance(
            repository_root(),
            "operator-machine-ratchet-verification-v1",
            result,
        )["status"]
        == "pass"
    )


def test_machine_evidence_ratchet_verifier_rejects_top_level_or_release_change(tmp_path):
    paths = _fixture(tmp_path)
    head_contract = _contract()
    head_contract["release_ref"] = {
        "kind": "github-release",
        "ref": "github-release://example/project/1",
    }
    changed = _item(head_contract)
    changed["owner"] = "different-owner"
    _write_jsonl(paths["head_items"], [changed])
    paths["candidate"].write_bytes(paths["head_items"].read_bytes())

    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet_verify."
        "validate_instance",
        side_effect=_schema_pass,
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet_verify."
        "evaluate_evidence_contract",
        return_value={"declared_status": "pending", "status": "pending"},
    ):
        with pytest.raises(KnowledgeHubError, match="outside evidence_contract"):
            _verify(tmp_path, paths)


def test_machine_evidence_ratchet_verifier_rejects_auto_ready_result(tmp_path):
    paths = _fixture(tmp_path)
    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet_verify."
        "validate_instance",
        side_effect=_schema_pass,
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet_verify."
        "evaluate_evidence_contract",
        return_value={"declared_status": "pending", "status": "ready"},
    ):
        with pytest.raises(KnowledgeHubError, match="auto-promote"):
            _verify(tmp_path, paths)


def test_machine_evidence_ratchet_verifier_rejects_origin_artifact_tamper(tmp_path):
    paths = _fixture(tmp_path)
    routing = json.loads(paths["routing"].read_text(encoding="utf-8"))
    routing["tampered"] = True
    _write_json(paths["routing"], routing)

    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet_verify."
        "validate_instance",
        side_effect=_schema_pass,
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet_verify."
        "evaluate_evidence_contract",
        return_value={"declared_status": "pending", "status": "pending"},
    ):
        with pytest.raises(KnowledgeHubError, match="artifact digest mismatch"):
            _verify(tmp_path, paths)


def test_machine_evidence_ratchet_verifier_rejects_multiple_ledger_appends(tmp_path):
    paths = _fixture(tmp_path)
    first = paths["head_ledger"].read_text(encoding="utf-8")
    paths["head_ledger"].write_text(first + first, encoding="utf-8")

    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet_verify."
        "validate_instance",
        side_effect=_schema_pass,
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet_verify."
        "evaluate_evidence_contract",
        return_value={"declared_status": "pending", "status": "pending"},
    ):
        with pytest.raises(KnowledgeHubError, match="exactly one durable record"):
            _verify(tmp_path, paths)
