from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance, validate_schema_catalog


def test_schema_catalog_resolves_all_contracts():
    result = validate_schema_catalog(repository_root())

    assert result["status"] == "pass"
    assert result["contract_count"] == 15
    assert result["validated_count"] == result["contract_count"]
    assert result["authority_overlap"] == []
    assert result["instance_validation"]["status"] == "pass"
    assert result["instance_validation"]["instance_count"] > 400


def test_schema_instance_validation_rejects_invalid_item():
    result = validate_instance(repository_root(), "registry-item-v1", {"id": "broken"})
    assert result["status"] == "fail"
    assert result["error_count"] > 0


def test_project_readiness_schema_accepts_idempotent_apply():
    result = validate_instance(
        repository_root(),
        "project-readiness-v1",
        {
            "schema_version": 1,
            "status": "no-change",
            "project_count": 30,
            "slot_count": 120,
            "transaction": {"changed_count": 0},
        },
    )
    assert result["status"] == "pass"
