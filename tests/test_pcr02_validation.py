import datetime as dt
import hashlib
import json
import pytest

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
        "projects/gros/decisions/example.md",
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


@pytest.mark.parametrize('variant', ['valid', 'no-manifest', 'wrong-before', 'claimed-new-owner-review'])
def test_normalized_owner_packet_requires_historical_lineage(tmp_path, monkeypatch, variant):
    from tools.codex_assets.knowledge_hub import pcr02_validation as validation
    from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
    packet = tmp_path / validation.OWNER_PACKET_PATH
    packet.parent.mkdir(parents=True)
    packet.write_text('normalized repository identity; unchanged technical boundary')
    current = hashlib.sha256(packet.read_bytes()).hexdigest()
    monkeypatch.setattr(validation, 'OWNER_PACKET_SHA256', current)
    attestation = tmp_path / validation.OWNER_ATTESTATION_REF
    original_statement = 'Historical owner statement binds ' + validation.OWNER_PACKET_SOURCE_SHA256
    attestation.write_text(original_statement)
    manifest = {'protocol': 'project-migration/v1', 'active_promoted': False,
                'owner_review_performed': variant == 'claimed-new-owner-review',
                'before_writes': {validation.OWNER_PACKET_PATH: '0' * 64 if variant == 'wrong-before' else validation.OWNER_PACKET_SOURCE_SHA256},
                'result_writes': {validation.OWNER_PACKET_PATH: current}}
    if variant != 'no-manifest':
        (packet.parent / 'project-migration-test.json').write_text(json.dumps(manifest))
    if variant == 'valid':
        validation._require_owner_packet(tmp_path)
    else:
        with pytest.raises(KnowledgeHubError, match='migration lineage is missing'):
            validation._require_owner_packet(tmp_path)
    assert attestation.read_text() == original_statement
