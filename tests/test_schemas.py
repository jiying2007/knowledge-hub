from tools.codex_assets.knowledge_hub.common import load_json, repository_root
from tools.codex_assets.knowledge_hub.metrics import local_metrics
from tools.codex_assets.knowledge_hub.schemas import validate_instance, validate_schema_catalog


def test_schema_catalog_resolves_all_contracts():
    result = validate_schema_catalog(repository_root())

    assert result["status"] == "pass"
    assert result["contract_count"] >= 26
    assert result["validated_count"] == result["contract_count"]
    assert result["authority_overlap"] == []
    assert result["instance_validation"]["status"] == "pass"
    assert result["instance_validation"]["instance_count"] > 400
    assert {
        "agent-contract-v1",
        "body-coverage-v2",
        "knowledge-map-v1",
        "agent-evidence-pack-v1",
        "agent-action-check-v1",
        "agent-review-policy-v1",
        "agent-proposal-route-v1",
        "agent-proposal-shadow-stats-v1",
        "raw-evidence-inspection-v1",
        "artifact-restore-drill-v1",
        "restore-drill-v2",
        "agent-compliance-eval-v2",
        "product-policy-v1",
    }.issubset({row["id"] for row in result["contracts"]})
    assert "retrieval-result-v3" in {row["id"] for row in result["contracts"]}
    assert "restore-drill-v1" not in {row["id"] for row in result["contracts"]}


def test_schema_catalog_exposes_only_strict_current_contracts():
    catalog = load_json(repository_root() / "schemas/catalog.json", {})

    assert catalog["schema_change_policy"].startswith("runtime accepts only")
    assert "migration_policy" not in catalog
    assert all(row.get("change_policy") == "strict-current-contract" for row in catalog["contracts"])
    assert all("compatibility" not in row for row in catalog["contracts"])


def test_schema_instance_validation_rejects_invalid_item():
    result = validate_instance(repository_root(), "registry-item-v1", {"id": "broken"})
    assert result["status"] == "fail"
    assert result["error_count"] > 0


def test_body_coverage_v2_requires_unregistered_only_inventory():
    payload = load_json(repository_root() / "registry/body-coverage.json", {})
    result = validate_instance(repository_root(), "body-coverage-v2", payload)

    assert result["status"] == "pass"

    payload["collections"][0].pop("inventory_scope")
    invalid = validate_instance(repository_root(), "body-coverage-v2", payload)

    assert invalid["status"] == "fail"
    assert any(
        row["path"] == "$.collections[0]" and "inventory_scope" in row["message"]
        for row in invalid["errors"]
    )


def test_local_metrics_v4_schema_accepts_current_contract_output():
    result = validate_instance(
        repository_root(),
        "local-metrics-v4",
        local_metrics(repository_root()),
    )

    assert result["status"] == "pass"


def test_project_readiness_schema_accepts_idempotent_apply():
    result = validate_instance(
        repository_root(),
        "project-readiness-v1",
        {
            "schema_version": 1,
            "status": "no-change",
            "project_count": 31,
            "slot_count": 31,
            "transaction": {"changed_count": 0},
        },
    )
    assert result["status"] == "pass"


def test_obsidian_view_schema_accepts_idempotent_apply():
    result = validate_instance(
        repository_root(),
        "obsidian-view-build-v1",
        {
            "schema_version": 1,
            "status": "no-change",
            "obsidian_runtime_status": "not-validated",
            "managed_document_count": 150,
            "content_mirror_drift_count": 0,
            "property_coverage": {},
            "transaction": {"changed_count": 0},
        },
    )
    assert result["status"] == "pass"
