import datetime as dt

from tools.codex_assets.knowledge_hub.common import registry_items, repository_root
from tools.codex_assets.knowledge_hub.pcr02_validation import (
    MANAGED_END,
    MANAGED_START,
    TARGETS,
    _initialize_candidate_contract,
    _managed_section,
    harden_pcr02_validation,
)


def test_pcr02_validation_contract_is_idempotent_and_owner_safe():
    root = repository_root()
    payload = harden_pcr02_validation(root, dt.date(2026, 7, 13))
    assert payload["candidate_count"] == 3
    assert payload["transaction"]["changed_count"] == 0
    assert payload["reviewing_only"] is True
    assert payload["active_promotion"] is False
    rows = {row["id"]: row for row in registry_items(root) if row.get("id") in TARGETS}
    assert set(rows) == set(TARGETS)
    for row in rows.values():
        assert row["status"] == "reviewing"
        assert row["promotion"] == "none"
        assert row["decision_owner"] == "leiwenjun"
        assert row["decision_status"] == "accepted-boundary-evidence-pending"
        assert row["owner_attestation_ref"] == (
            "artifacts/manifests/knowledge-hub-pcr02-specialized-owner-attestation-20260716.md"
        )
        assert row["owner_decision"].startswith("accept-")
        assert row["manual_validation_pending"] is True
        assert set(row["evidence_readiness"].values()) >= {
            "accepted-boundary-evidence-pending",
            "pending-current-commit-and-artifact-identity",
            "pending-real-device-or-lab-evidence",
            "pending-release-and-rollback-evidence",
        }


def test_pcr02_contract_preserves_owner_evolution():
    contract = next(iter(TARGETS.values()))
    item = {
        "status": "active",
        "promotion": "active",
        "decision_owner": "display-owner",
        "decision_status": "accepted",
        "manual_validation_pending": False,
        "validation_refs": ["artifact://real-validation"],
        "evidence_readiness": {
            "owner": "ready",
            "source": "ready",
            "device": "ready",
            "release": "ready",
        },
    }
    result = _initialize_candidate_contract(
        item,
        contract,
        "projects/xcrz-sigmastar-demo/decisions/example.md",
        dt.date(2026, 7, 13),
    )
    for field in (
        "status",
        "promotion",
        "decision_owner",
        "decision_status",
        "manual_validation_pending",
        "evidence_readiness",
    ):
        assert result[field] == item[field]
    assert "artifact://real-validation" in result["validation_refs"]


def test_pcr02_existing_managed_section_is_not_rewritten():
    body = "{}\ncustom owner evidence\n### 证据落地契约\ncustom contract\n{}\n".format(
        MANAGED_START,
        MANAGED_END,
    )
    assert _managed_section(body, "replacement") == body
