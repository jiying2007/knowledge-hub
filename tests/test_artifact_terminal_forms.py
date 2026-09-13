import json

from tools.codex_assets.knowledge_hub.artifact_terminal_forms import (
    COVERAGE_MODE,
    HISTORICAL_EXCEPTION_FORM,
    REGISTRY_CONTRACT,
    evaluate_legacy_artifact_terminal_forms,
    legacy_reference_snapshot,
)
from tools.codex_assets.knowledge_hub.common import repository_root


def _write_legacy_row(root, *, sha256="a" * 64):
    manifests = root / "artifacts/manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    row = {
        "id": "legacy-a",
        "artifact_uri": "artifact://legacy/a.bin",
        "sha256": sha256,
        "size": 12,
    }
    (manifests / "legacy.jsonl").write_text(
        json.dumps(row, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_registry(root, snapshot):
    registry = root / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "contract": REGISTRY_CONTRACT,
        "status": "active",
        "coverage": {
            "terminal_form": HISTORICAL_EXCEPTION_FORM,
            "coverage_mode": COVERAGE_MODE,
            "scope": "artifacts/manifests/**/*.jsonl",
            "source_revision": "test-fixture",
            "legacy_reference_count": snapshot["legacy_reference_count"],
            "legacy_reference_set_sha256": snapshot["legacy_reference_set_sha256"],
            "owner": "test-owner",
            "reason": "freeze the exact synthetic historical reference set",
            "automatic_delete": False,
        },
    }
    (registry / "legacy-artifact-terminal-forms.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def test_exact_historical_reference_set_is_accepted(tmp_path):
    _write_legacy_row(tmp_path)
    snapshot = legacy_reference_snapshot(tmp_path)
    _write_registry(tmp_path, snapshot)

    report = evaluate_legacy_artifact_terminal_forms(tmp_path)

    assert report["status"] == "pass"
    assert report["legacy_reference_count"] == 1
    assert report["accepted_legacy_reference_count"] == 1
    assert report["unaccepted_legacy_reference_count"] == 0
    assert report["count_matches"] is True
    assert report["digest_matches"] is True


def test_historical_reference_mutation_fails_closed(tmp_path):
    _write_legacy_row(tmp_path)
    snapshot = legacy_reference_snapshot(tmp_path)
    _write_registry(tmp_path, snapshot)
    _write_legacy_row(tmp_path, sha256="b" * 64)

    report = evaluate_legacy_artifact_terminal_forms(tmp_path)

    assert report["status"] == "fail"
    assert report["legacy_reference_count"] == 1
    assert report["accepted_legacy_reference_count"] == 0
    assert report["unaccepted_legacy_reference_count"] == 1
    assert report["count_matches"] is True
    assert report["digest_matches"] is False


def test_repository_legacy_artifact_refs_have_machine_terminal_form():
    report = evaluate_legacy_artifact_terminal_forms(repository_root())

    assert report["status"] == "pass", json.dumps(
        report,
        ensure_ascii=False,
        sort_keys=True,
    )
    assert report["legacy_reference_count"] == 315
    assert report["accepted_legacy_reference_count"] == 315
    assert report["unaccepted_legacy_reference_count"] == 0
