import copy

from tools.codex_assets.knowledge_hub.common import load_json, repository_root
from tools.codex_assets.knowledge_hub.metrics import local_metrics
from tools.codex_assets.knowledge_hub.schema_subset import validate_contract_subset
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
        "restore-drill-v4",
        "agent-compliance-eval-v2",
        "product-policy-v1",
        "ai-operations-policy-v1",
        "contract-compatibility-v1",
        "review-risk-policy-v1",
        "durable-evidence-record-v1",
    }.issubset({row["id"] for row in result["contracts"]})
    assert "retrieval-result-v3" in {row["id"] for row in result["contracts"]}
    contract_ids = {row["id"] for row in result["contracts"]}
    assert "final-gate-product-v5" in contract_ids
    assert "status-contract-v2" in contract_ids
    assert {
        "restore-drill-v2",
        "restore-drill-v3",
        "final-gate-product-v4",
        "local-metrics-v4",
        "status-contract-v1",
    }.isdisjoint(contract_ids)


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


def test_local_metrics_v5_schema_accepts_current_contract_output():
    result = validate_instance(
        repository_root(),
        "local-metrics-v5",
        local_metrics(repository_root()),
    )

    assert result["status"] == "pass"


def test_retrieval_hot_path_validator_matches_full_draft_validator():
    root = repository_root()
    payload = {
        "schema_version": 3,
        "status": "pass",
        "query": "knowledge hub",
        "index": {"mode": "local-index", "fresh": True},
        "results": [
            {
                "id": "item-a",
                "path": "governance/item-a.md",
                "status": "reviewing",
                "score": 1.0,
                "why_selected": ["registry-backed"],
            }
        ],
        "pagination": {
            "offset": 0,
            "limit": 3,
            "returned": 1,
            "total": 1,
            "has_more": False,
            "next_cursor": "",
            "signature_bound": True,
        },
        "search_trace": {
            "schema_version": "knowledge-hub.search-trace.v1",
            "query_terms": ["knowledge", "hub"],
            "applied_filters": {},
            "candidate_pool": {"indexed": 1, "after_filters": 1, "returned": 1},
            "excluded_by_filters_total": 0,
            "excluded_by_filters": [],
            "excluded_truncated": False,
            "retry_queries": [],
        },
        "zero_hit": {},
        "timing": {
            "validation_ms": 1.0,
            "index_ensure_ms": 1.0,
            "candidate_query_ms": 1.0,
            "ranking_ms": 1.0,
            "total_ms": 4.0,
        },
    }

    assert validate_instance(root, "retrieval-result-v3", payload)["status"] == "pass"
    assert (
        validate_contract_subset(root, "retrieval-result-v3", payload)["status"]
        == "pass"
    )

    invalid_payloads = []
    missing_timing = copy.deepcopy(payload)
    missing_timing.pop("timing")
    invalid_payloads.append(missing_timing)
    boolean_version = copy.deepcopy(payload)
    boolean_version["schema_version"] = True
    invalid_payloads.append(boolean_version)
    extra_pagination = copy.deepcopy(payload)
    extra_pagination["pagination"]["removed_compatibility_field"] = True
    invalid_payloads.append(extra_pagination)
    excessive_limit = copy.deepcopy(payload)
    excessive_limit["pagination"]["limit"] = 101
    invalid_payloads.append(excessive_limit)
    invalid_reason = copy.deepcopy(payload)
    invalid_reason["results"][0]["why_selected"] = [1]
    invalid_payloads.append(invalid_reason)
    negative_timing = copy.deepcopy(payload)
    negative_timing["timing"]["total_ms"] = -1
    invalid_payloads.append(negative_timing)

    for invalid in invalid_payloads:
        assert (
            validate_instance(root, "retrieval-result-v3", invalid)["status"]
            == "fail"
        )
        assert (
            validate_contract_subset(root, "retrieval-result-v3", invalid)[
                "status"
            ]
            == "fail"
        )


def test_retrieval_hot_path_validator_rejects_unknown_schema_keyword(tmp_path):
    (tmp_path / "schemas").mkdir()
    (tmp_path / "schemas/catalog.json").write_text(
        '{"contracts":[{"id":"retrieval-result-v3",'
        '"schema":"schemas/retrieval-result.schema.json"}]}\n',
        encoding="utf-8",
    )
    (tmp_path / "schemas/retrieval-result.schema.json").write_text(
        '{"type":"object","unevaluatedProperties":false}\n',
        encoding="utf-8",
    )

    result = validate_contract_subset(tmp_path, "retrieval-result-v3", {})

    assert result["status"] == "fail"
    assert result["errors"] == [
        {
            "path": "$schema",
            "message": "unsupported schema keyword unevaluatedProperties",
        }
    ]


def test_product_v5_schema_rejects_removed_top_level_compatibility_fields():
    payload = {
        "schema_version": 5,
        "status": "needs-review",
        "terminal": False,
        "final_profile": "product",
        "maturity_axes": {
            "schema_version": 2,
            "platform": {
                "status": "pass",
                "independent_from_project_evidence": True,
            },
            "content": {"status": "needs-review"},
            "project_evidence": {"status": "needs-review"},
            "delivery": {
                "status": "needs-review",
                "local_delivery_complete": False,
                "remote_published": False,
                "offsite_restore_verified": False,
            },
            "adoption": {"status": "needs-review", "ready": False},
            "status": "needs-review",
            "terminal": False,
        },
        "platform_status": {"status": "pass", "hard_checks": {}},
        "content_readiness": {"status": "needs-review"},
        "retrieval_quality": {"status": "pass"},
        "operational_readiness": {"status": "pass"},
        "delivery_readiness": {
            "status": "needs-review",
            "local_delivery_complete": False,
            "remote_published": False,
            "offsite_restore_verified": False,
        },
    }

    assert (
        validate_instance(repository_root(), "final-gate-product-v5", payload)[
            "status"
        ]
        == "pass"
    )
    for removed in (
        "gate_status",
        "final_status",
        "overall_status",
        "platform_productization_complete",
        "summary",
    ):
        invalid = validate_instance(
            repository_root(),
            "final-gate-product-v5",
            {**payload, removed: "removed"},
        )
        assert invalid["status"] == "fail"
        assert any(
            "Additional properties are not allowed" in row["message"]
            for row in invalid["errors"]
        )


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


def test_ai_first_long_term_registry_contracts_are_valid():
    root = repository_root()
    for contract_id, relative in (
        ("ai-operations-policy-v1", "registry/ai-operations-policy.json"),
        ("contract-compatibility-v1", "registry/contract-compatibility.json"),
        ("review-risk-policy-v1", "registry/review-risk-policy.json"),
    ):
        payload = load_json(root / relative, {})
        assert validate_instance(root, contract_id, payload)["status"] == "pass"
