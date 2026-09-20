import json
from pathlib import Path

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.observation_source_readiness import (
    build_observation_source_readiness,
)
from tools.codex_assets.knowledge_hub.schemas import validate_instance


GAPS = (
    "connector-provider-pilot",
    "production-retrieval-eval",
    "memory-lifecycle-pilot",
    "real-adoption-evidence",
)


def _write(root: Path, allowlists, statuses=None):
    registry = root / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    (registry / "ai-operations-policy.json").write_text(
        json.dumps(
            {
                "external_evidence": {
                    "supported_gaps": list(GAPS),
                    "observation_source_workflow_allowlist": allowlists,
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    statuses = statuses or {gap: "open" for gap in GAPS}
    (registry / "knowledge-platform-p5-p10.json").write_text(
        json.dumps(
            {
                "external_closure_gaps": [
                    {
                        "id": gap,
                        "status": statuses.get(gap, "open"),
                    }
                    for gap in GAPS
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _empty_allowlists():
    return {gap: [] for gap in GAPS}


def test_observation_source_readiness_reports_unregistered_real_sources(tmp_path):
    _write(tmp_path, _empty_allowlists())

    report = build_observation_source_readiness(tmp_path)

    assert report["status"] == "needs-registration"
    assert report["unregistered_count"] == 4
    assert report["registered_open_count"] == 0
    assert report["canonical_write_performed"] is False
    assert report["owner_decision_generated"] is False
    assert all(
        row["next_action"] == "register-real-observation-workflow"
        for row in report["rows"]
    )
    assert all(row["row_fingerprint"].startswith("sha256:") for row in report["rows"])


def test_observation_source_readiness_is_deterministic_and_tracker_scoped(tmp_path):
    allowlists = _empty_allowlists()
    allowlists["connector-provider-pilot"] = [
        ".github/workflows/connector-real-observation.yml"
    ]
    _write(tmp_path, allowlists)

    first = build_observation_source_readiness(tmp_path)
    second = build_observation_source_readiness(tmp_path)

    assert first == second
    assert first["status"] == "needs-registration"
    connector = next(
        row
        for row in first["rows"]
        if row["gap_id"] == "connector-provider-pilot"
    )
    assert connector["status"] == "registered"
    assert connector["next_action"] == "produce-real-observation"
    assert first["connector_tracker_fingerprint"].startswith("sha256:")
    assert first["production_tracker_fingerprint"].startswith("sha256:")


def test_observation_source_readiness_ignores_registration_after_gap_closed(tmp_path):
    allowlists = _empty_allowlists()
    statuses = {gap: "closed" for gap in GAPS}
    _write(tmp_path, allowlists, statuses=statuses)

    report = build_observation_source_readiness(tmp_path)

    assert report["status"] == "closed"
    assert report["unregistered_count"] == 0
    assert all(row["status"] == "closed" for row in report["rows"])
    assert all(row["next_action"] == "none" for row in report["rows"])


def test_observation_source_readiness_matches_catalog_contract(tmp_path):
    _write(tmp_path, _empty_allowlists())
    report = build_observation_source_readiness(tmp_path)

    result = validate_instance(
        repository_root(),
        "observation-source-readiness-v1",
        report,
    )

    assert result["status"] == "pass", result["errors"]
