import datetime as dt
import json
import pathlib

import pytest

from tools.codex_assets.knowledge_hub.authorization import load_review_form
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, file_sha256, load_jsonl
from tools.codex_assets.knowledge_hub.lifecycle import capture, transition
from tools.codex_assets.knowledge_hub.review_attestation import (
    build_attestation_packet,
    generate_review_form,
)
from tools.codex_assets.knowledge_hub.schemas import validate_instance


TODAY = dt.date(2026, 7, 14)
ITEM_ID = "attestation-fixture-20260714"
ITEM_PATH = "governance/attestation-fixture.md"


def _jsonl(rows):
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)


def _root(tmp_path):
    (tmp_path / "registry").mkdir()
    (tmp_path / "indexes").mkdir()
    (tmp_path / "governance").mkdir()
    (tmp_path / "registry/items.jsonl").write_text("")
    (tmp_path / "registry/authorizations.jsonl").write_text("")
    (tmp_path / "registry/promotions.jsonl").write_text("")
    (tmp_path / "registry/projects.json").write_text('{"projects": []}\n')
    (tmp_path / "indexes/by-owner.md").write_text("# By Owner\n\n## leiwenjun\n")
    (tmp_path / "indexes/by-review-date.md").write_text("# By Review Date\n")
    (tmp_path / "indexes/by-status.md").write_text("# By Status\n")
    (tmp_path / "indexes/by-project.md").write_text("# By Project\n")
    (tmp_path / "indexes/by-topic.md").write_text("# By Topic\n")
    source = tmp_path / "source.md"
    source.write_text("# Attestation fixture\n\nExact body under review.\n")
    capture(
        tmp_path,
        source,
        "audit",
        ITEM_PATH,
        TODAY,
        True,
        item_id=ITEM_ID,
    )
    return tmp_path


def _statement(packet, mode, reviewer="leiwenjun"):
    return packet["content_review_attestation"]["response_templates"][mode].replace("<reviewer>", reviewer)


def _generate(root, mode="human-reviewed", apply=True, output="artifacts/manifests/review.local.jsonl"):
    packet = build_attestation_packet(root, ITEM_ID, "archived", TODAY)
    result = generate_review_form(
        root,
        ITEM_ID,
        "archived",
        TODAY,
        packet["item"]["content_sha256"],
        mode,
        "leiwenjun",
        "current-session:user-message-42",
        _statement(packet, mode),
        output,
        apply,
        True,
    )
    return packet, result, root / output


def test_packet_separates_execution_authorization_from_content_review(tmp_path):
    root = _root(tmp_path)
    packet = build_attestation_packet(root, ITEM_ID, "archived", TODAY)

    assert packet["status"] == "awaiting-human-decision"
    assert packet["read_only"] is True
    assert packet["execution_authorization"]["separate_gate"] is True
    assert packet["execution_authorization"]["required_for_form_generation"] is False
    assert packet["content_review_attestation"]["manual_json_editing_required"] is False
    assert set(packet["content_review_attestation"]["allowed_modes"]) == {
        "human-reviewed",
        "human-directed-delegation",
    }
    assert packet["item"]["content_sha256"] in _statement(packet, "human-reviewed")

    blocked = transition(root, ITEM_ID, "archived", TODAY, False)
    assert blocked["gates"]["execution_authorization"]["status"] == "blocked"
    assert blocked["gates"]["content_review_attestation"]["status"] == "blocked"
    assert blocked["gates"]["content_review_attestation"]["manual_json_editing_required"] is False
    assert "knowledge-review-attest.sh packet" in blocked["gates"]["content_review_attestation"]["packet_command"]


def test_direct_human_attestation_form_is_generated_and_idempotent(tmp_path):
    root = _root(tmp_path)
    packet, result, form_path = _generate(root)

    assert result["status"] == "applied"
    form = load_review_form(form_path, ITEM_ID)
    assert form["form_kind"] == "content-review-attestation"
    assert form["reviewed_by"] == "leiwenjun"
    assert form["attestation_mode"] == "human-reviewed"
    assert form["content_sha256"] == packet["item"]["content_sha256"]
    assert "authorization_id" not in form
    assert form["execution_authorization_embedded"] is False
    schema_root = root / "schema-root"
    schema_root.mkdir()
    (schema_root / "schemas").mkdir()
    source_root = pathlib.Path(__file__).resolve().parents[1]
    (schema_root / "schemas/catalog.json").write_text((source_root / "schemas/catalog.json").read_text())
    for path in (source_root / "schemas").glob("*.schema.json"):
        (schema_root / "schemas" / path.name).write_text(path.read_text())
    assert validate_instance(schema_root, "review-attestation-v1", form)["status"] == "pass"

    _, repeated, _ = _generate(root)
    assert repeated["status"] == "no-change"


def test_delegated_decision_uses_explicit_delegation_identity(tmp_path):
    root = _root(tmp_path)
    _, _, form_path = _generate(root, mode="human-directed-delegation")
    form = load_review_form(form_path, ITEM_ID)

    assert form["attested_by"] == "leiwenjun"
    assert form["reviewed_by"] == "leiwenjun-via-codex-delegation"
    assert "direct content review not asserted" in form["review_basis"]


def test_rejected_target_maps_to_reject_decision(tmp_path):
    root = _root(tmp_path)
    packet = build_attestation_packet(root, ITEM_ID, "rejected", TODAY)
    output = "artifacts/manifests/rejected.local.jsonl"
    generate_review_form(
        root,
        ITEM_ID,
        "rejected",
        TODAY,
        packet["item"]["content_sha256"],
        "human-directed-delegation",
        "leiwenjun",
        "current-session:user-message-46",
        _statement(packet, "human-directed-delegation"),
        output,
        True,
        True,
    )

    form = load_review_form(root / output, ITEM_ID)
    assert form["target_status"] == "rejected"
    assert form["review_decision"] == "reject"


def test_active_promotion_rejects_delegated_decision(tmp_path):
    root = _root(tmp_path)
    packet = build_attestation_packet(root, ITEM_ID, "active", TODAY)
    assert packet["content_review_attestation"]["allowed_modes"] == ["human-reviewed"]

    direct_statement = _statement(packet, "human-reviewed")
    delegated_statement = direct_statement.replace("leiwenjun", "leiwenjun-via-codex-delegation")
    with pytest.raises(KnowledgeHubError, match="active promotion requires direct"):
        generate_review_form(
            root,
            ITEM_ID,
            "active",
            TODAY,
            packet["item"]["content_sha256"],
            "human-directed-delegation",
            "leiwenjun",
            "current-session:user-message-43",
            delegated_statement,
            "artifacts/manifests/active.local.jsonl",
            True,
            True,
        )


def test_generation_rejects_generic_confirmation_and_hash_drift(tmp_path):
    root = _root(tmp_path)
    packet = build_attestation_packet(root, ITEM_ID, "archived", TODAY)

    with pytest.raises(KnowledgeHubError, match="exact review packet"):
        generate_review_form(
            root,
            ITEM_ID,
            "archived",
            TODAY,
            packet["item"]["content_sha256"],
            "human-reviewed",
            "leiwenjun",
            "current-session:user-message-44",
            "同意归档",
            "artifacts/manifests/generic.local.jsonl",
            True,
            True,
        )

    with pytest.raises(KnowledgeHubError, match="expected item SHA256"):
        generate_review_form(
            root,
            ITEM_ID,
            "archived",
            TODAY,
            "0" * 64,
            "human-reviewed",
            "leiwenjun",
            "current-session:user-message-44",
            _statement(packet, "human-reviewed"),
            "artifacts/manifests/drift.local.jsonl",
            True,
            True,
        )


def test_transition_rejects_form_after_body_changes(tmp_path):
    root = _root(tmp_path)
    packet, _, form_path = _generate(root)
    body_path = root / ITEM_PATH
    body_path.write_text(body_path.read_text() + "\nChanged after attestation.\n")

    result = transition(
        root,
        ITEM_ID,
        "archived",
        TODAY,
        False,
        review_form=form_path,
        expected_item_sha256=file_sha256(body_path),
    )
    assert result["gates"]["content_review_attestation"]["status"] == "blocked"
    assert any("SHA256 does not match" in error for error in result["gate_errors"])
    assert packet["item"]["content_sha256"] != file_sha256(body_path)


def test_loader_rejects_tampered_generated_review_basis(tmp_path):
    root = _root(tmp_path)
    _, _, form_path = _generate(root)
    form = json.loads(form_path.read_text())
    form["review_basis"] = "tampered owner decision"
    form_path.write_text(json.dumps(form, ensure_ascii=False) + "\n")

    with pytest.raises(KnowledgeHubError, match="review_basis does not match"):
        load_review_form(form_path, ITEM_ID)


def test_generated_form_does_not_replace_execution_authorization(tmp_path):
    root = _root(tmp_path)
    packet, _, form_path = _generate(root)

    without_authorization = transition(
        root,
        ITEM_ID,
        "archived",
        TODAY,
        False,
        review_form=form_path,
        expected_item_sha256=packet["item"]["content_sha256"],
    )
    assert without_authorization["gates"]["content_review_attestation"]["status"] == "pass"
    assert without_authorization["gates"]["execution_authorization"]["status"] == "blocked"

    auth_id = "auth-attestation-fixture-archive"
    authorization = {
        "authorization_id": auth_id,
        "authorized_by": "leiwenjun",
        "authorized_at": TODAY.isoformat(),
        "scope": "archive {} at {} only".format(ITEM_ID, ITEM_PATH),
        "allowed_actions": ["automation-apply-with-review"],
        "expires_at": "2026-07-15",
        "evidence_refs": ["current-session:user-message-45"],
        "rollback_path": "restore transaction backups",
        "validation_commands": ["rtk bash tools/knowledge-check.sh --dry-run"],
        "status": "active",
    }
    (root / "registry/authorizations.jsonl").write_text(_jsonl([authorization]))
    applied = transition(
        root,
        ITEM_ID,
        "archived",
        TODAY,
        True,
        authorization_id=auth_id,
        review_form=form_path,
        expected_item_sha256=file_sha256(root / ITEM_PATH),
    )

    assert applied["status"] == "applied"
    item = load_jsonl(root / "registry/items.jsonl")[0]
    assert item["status"] == "archived"
    assert item["review_attestation_mode"] == "human-reviewed"
    assert load_jsonl(root / "registry/authorizations.jsonl")[0]["status"] == "used"
    event = load_jsonl(root / "registry/lifecycle-events.jsonl")[-1]
    assert event["authorization_id"] == auth_id
    assert event["review_attestation_id"] == item["review_attestation_id"]
    assert event["review_attestation_statement_sha256"] == item["review_attestation_statement_sha256"]
    assert event["review_confirmation_token"] == item["review_confirmation_token"]
