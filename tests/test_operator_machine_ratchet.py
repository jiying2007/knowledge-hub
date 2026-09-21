from __future__ import annotations

import hashlib
import pathlib
from unittest import mock

from tools.codex_assets.knowledge_hub.common import encode_jsonl, repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance
from tools.codex_assets.knowledge_hub.operator_machine_ratchet import (
    build_machine_ratchet_candidate,
)


FP = "sha256:" + "a" * 64


def _write_registry(root):
    registry = pathlib.Path(root) / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    path = registry / "items.jsonl"
    path.write_text('{"id":"base"}\n', encoding="utf-8")
    return path


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _route(root, candidate_content):
    before = _sha((pathlib.Path(root) / "registry/items.jsonl").read_bytes())
    after = _sha(candidate_content.encode("utf-8"))
    return {
        "projection": "knowledge-operator-auto-route-v1",
        "status": "ready-for-machine-ratchet",
        "read_only": True,
        "selection_is_authorization": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "ambiguous_target_count": 0,
        "machine_route": {
            "status": "ready-for-machine-ratchet",
            "selected_proposal_fingerprints": [FP],
            "patch_plan": {
                "registry_path": "registry/items.jsonl",
                "registry_before_sha256": before,
                "registry_after_sha256": after,
                "selected_proposal_fingerprints": [FP],
                "planned_write_count": 1,
                "planned_item_count": 1,
            },
        },
    }


def _materialized(field="source_refs"):
    items = [{"id": "candidate"}]
    rows = [
        {
            "item_id": "candidate",
            "project_id": "project-1",
            "changed_fields": [field],
            "selected_proposal_fingerprints": [FP],
        }
    ]
    return items, rows, []


def test_machine_ratchet_candidate_binds_exact_registry_bytes(tmp_path):
    _write_registry(tmp_path)
    items, rows, reasons = _materialized()
    candidate_content = encode_jsonl(items)
    route = _route(tmp_path, candidate_content)

    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet._selected_rows",
        return_value=([{"proposal_fingerprint": FP}], []),
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet._materialize",
        return_value=(items, rows, reasons),
    ):
        content, manifest = build_machine_ratchet_candidate(
            pathlib.Path(tmp_path),
            {},
            route,
        )

    assert content == candidate_content
    assert manifest["status"] == "ready-for-machine-ratchet"
    assert manifest["canonical_write_performed"] is False
    assert manifest["automatic_execution_enabled"] is False
    assert manifest["candidate_only"] is True
    assert manifest["registry_after_sha256"] == _sha(content.encode("utf-8"))
    assert manifest["candidate_sha256"] == manifest["registry_after_sha256"]
    assert manifest["selected_proposal_fingerprints"] == [FP]
    assert (
        validate_instance(
            repository_root(),
            "operator-machine-ratchet-candidate-v1",
            manifest,
        )["status"]
        == "pass"
    )


def test_machine_ratchet_candidate_rejects_field_outside_machine_allowlist(tmp_path):
    _write_registry(tmp_path)
    items, rows, reasons = _materialized(field="release_ref")
    candidate_content = encode_jsonl(items)
    route = _route(tmp_path, candidate_content)

    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet._selected_rows",
        return_value=([{"proposal_fingerprint": FP}], []),
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet._materialize",
        return_value=(items, rows, reasons),
    ):
        content, manifest = build_machine_ratchet_candidate(
            pathlib.Path(tmp_path),
            {},
            route,
        )

    assert content == ""
    assert manifest["status"] == "blocked"
    assert "machine-changed-field-outside-allowlist" in manifest["reason_codes"]


def test_machine_ratchet_candidate_rejects_stale_registry_precondition(tmp_path):
    path = _write_registry(tmp_path)
    items, rows, reasons = _materialized()
    candidate_content = encode_jsonl(items)
    route = _route(tmp_path, candidate_content)
    path.write_text('{"id":"drift"}\n', encoding="utf-8")

    with mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet._selected_rows",
        return_value=([{"proposal_fingerprint": FP}], []),
    ), mock.patch(
        "tools.codex_assets.knowledge_hub.operator_machine_ratchet._materialize",
        return_value=(items, rows, reasons),
    ):
        content, manifest = build_machine_ratchet_candidate(
            pathlib.Path(tmp_path),
            {},
            route,
        )

    assert content == ""
    assert manifest["status"] == "blocked"
    assert "machine-registry-before-sha256-mismatch" in manifest["reason_codes"]


def test_machine_ratchet_builder_is_in_mypy_surface():
    pyproject = pathlib.Path("pyproject.toml").read_text(encoding="utf-8")
    assert (
        '"tools/codex_assets/knowledge_hub/operator_machine_ratchet.py"'
        in pyproject
    )
