import json
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub import signed_attestation
from tools.codex_assets.knowledge_hub.attestation import PREDICATE_TYPE
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


def _write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def _evidence(
    root: Path,
    *,
    terminal_status="needs-review",
    terminal_value=False,
    terminal_blockers=None,
    product_status="needs-review",
    product_terminal=False,
):
    _write(
        root / ".cache/knowledge-hub/engineering-quality.json",
        {"status": "pass", "candidate_integrity": {"status": "pass"}},
    )
    _write(root / ".cache/knowledge-hub/compliance-eval.json", {"status": "pass"})
    _write(root / ".cache/knowledge-hub/restore-drill-head.json", {"status": "pass"})
    _write(
        root / ".cache/knowledge-hub/final-gate-product-full.json",
        {"status": product_status, "terminal": product_terminal},
    )
    if terminal_blockers is None:
        terminal_blockers = [] if terminal_value else ["external_closure"]
    _write(
        root / ".cache/knowledge-hub/terminal-closure.json",
        {
            "status": terminal_status,
            "terminal": terminal_value,
            "blockers": terminal_blockers,
        },
    )
    _write(
        root / ".cache/knowledge-hub/hosting-posture.json",
        {
            "status": "pass",
            "repository": "example/knowledge-hub",
            "source_revision": "a" * 40,
            "repository_private": True,
            "repository_visibility": "private",
            "default_branch": "master",
            "default_branch_protected": False,
        },
    )
    _write(root / ".tmp/engineering/knowledge-hub.cdx.json", {"bomFormat": "CycloneDX"})


def test_signed_materials_bind_quality_sbom_and_actual_terminal_verdict(monkeypatch, tmp_path):
    monkeypatch.setattr(signed_attestation, "utc_timestamp", lambda: "2026-09-14T00:00:00Z")
    _evidence(tmp_path)
    receipt = signed_attestation.build_signed_quality_materials(
        tmp_path,
        source_revision="a" * 40,
    )
    statement = json.loads(
        (tmp_path / ".cache/knowledge-hub/signed-attestation/quality-statement.json").read_text(
            encoding="utf-8"
        )
    )

    assert receipt["structural_verification"]["status"] == "pass"
    assert statement["predicateType"] == PREDICATE_TYPE
    assert statement["predicate"]["source_commit"] == "a" * 40
    assert statement["predicate"]["evidence_artifact_sha256"] == receipt["manifest_sha256"]
    assert statement["predicate"]["sbom_sha256"] == receipt["sbom_sha256"]
    assert statement["predicate"]["quality_gates"]["product_gate"] == "needs-review"
    assert statement["predicate"]["terminal_closure"]["status"] == "needs-review"
    assert statement["predicate"]["terminal_closure"]["terminal"] is False
    assert statement["predicate"]["terminal_closure"]["blockers"] == [
        "external_closure",
    ]


def test_evidence_mutation_changes_manifest_identity(monkeypatch, tmp_path):
    monkeypatch.setattr(signed_attestation, "utc_timestamp", lambda: "2026-09-14T00:00:00Z")
    _evidence(tmp_path)
    first = signed_attestation.build_signed_quality_materials(
        tmp_path,
        source_revision="b" * 40,
    )["manifest_sha256"]
    _write(
        tmp_path / ".cache/knowledge-hub/compliance-eval.json",
        {"status": "pass", "case_count": 53},
    )
    second = signed_attestation.build_signed_quality_materials(
        tmp_path,
        source_revision="b" * 40,
    )["manifest_sha256"]
    assert first != second


def test_signed_materials_reject_invalid_terminal_verdict(tmp_path):
    _evidence(tmp_path, terminal_status="closed")
    with pytest.raises(KnowledgeHubError, match="terminal closure verdict has invalid status"):
        signed_attestation.build_signed_quality_materials(
            tmp_path,
            source_revision="c" * 40,
        )


def test_signed_materials_allow_repository_terminal_with_nonterminal_product(tmp_path):
    _evidence(
        tmp_path,
        terminal_status="pass",
        terminal_value=True,
        terminal_blockers=[],
        product_status="needs-review",
        product_terminal=False,
    )
    receipt = signed_attestation.build_signed_quality_materials(
        tmp_path,
        source_revision="c" * 40,
    )

    assert receipt["terminal_closure"]["status"] == "pass"
    assert receipt["terminal_closure"]["terminal"] is True
    assert receipt["quality_gates"]["product_gate"] == "needs-review"


def test_signed_materials_reject_failed_product_evidence(tmp_path):
    _evidence(tmp_path, product_status="needs-fix")
    with pytest.raises(KnowledgeHubError, match="product evidence has invalid status"):
        signed_attestation.build_signed_quality_materials(
            tmp_path,
            source_revision="c" * 40,
        )


def test_hosted_verification_must_match_signed_local_materials(monkeypatch, tmp_path):
    monkeypatch.setattr(signed_attestation, "utc_timestamp", lambda: "2026-09-14T00:00:00Z")
    _evidence(tmp_path)
    receipt = signed_attestation.build_signed_quality_materials(
        tmp_path,
        source_revision="d" * 40,
    )
    statement = json.loads(
        (tmp_path / ".cache/knowledge-hub/signed-attestation/quality-statement.json").read_text(
            encoding="utf-8"
        )
    )
    verification = [
        {
            "verificationResult": {
                "statement": statement,
                "signature": {"certificate": {"subject": "github-actions-oidc"}},
                "verifiedTimestamps": [{"timestamp": "2026-09-14T00:00:01Z"}],
            }
        }
    ]
    verification_path = tmp_path / "verification.json"
    verification_path.write_text(json.dumps(verification), encoding="utf-8")
    bundle = tmp_path / "bundle.json"
    bundle.write_text("{}\n", encoding="utf-8")

    hosted = signed_attestation.verify_hosted_attestation(
        tmp_path,
        verification_path=verification_path,
        source_revision="d" * 40,
        source_ref="refs/heads/master",
        signer_workflow="jiying2007/knowledge-hub/.github/workflows/signed-quality-attestation.yml",
        bundle_path=bundle,
        attestation_id="1234",
        attestation_url="https://github.com/jiying2007/knowledge-hub/attestations/1234",
    )
    assert hosted["status"] == "pass"
    assert hosted["manifest_sha256"] == receipt["manifest_sha256"]
    assert hosted["sigstore_identity_verified"] is True
    assert hosted["private_key_used"] is False


def test_hosted_verification_rejects_predicate_drift(monkeypatch, tmp_path):
    monkeypatch.setattr(signed_attestation, "utc_timestamp", lambda: "2026-09-14T00:00:00Z")
    _evidence(tmp_path)
    signed_attestation.build_signed_quality_materials(tmp_path, source_revision="e" * 40)
    statement = json.loads(
        (tmp_path / ".cache/knowledge-hub/signed-attestation/quality-statement.json").read_text(
            encoding="utf-8"
        )
    )
    statement["predicate"]["source_commit"] = "f" * 40
    verification_path = tmp_path / "verification.json"
    verification_path.write_text(
        json.dumps(
            [
                {
                    "verificationResult": {
                        "statement": statement,
                        "signature": {"certificate": {"subject": "github-actions-oidc"}},
                        "verifiedTimestamps": [{"timestamp": "2026-09-14T00:00:01Z"}],
                    }
                }
            ]
        ),
        encoding="utf-8",
    )
    bundle = tmp_path / "bundle.json"
    bundle.write_text("{}\n", encoding="utf-8")
    with pytest.raises(KnowledgeHubError, match="does not match local quality materials"):
        signed_attestation.verify_hosted_attestation(
            tmp_path,
            verification_path=verification_path,
            source_revision="e" * 40,
            source_ref="refs/heads/master",
            signer_workflow="jiying2007/knowledge-hub/.github/workflows/signed-quality-attestation.yml",
            bundle_path=bundle,
            attestation_id="1234",
            attestation_url="https://github.com/jiying2007/knowledge-hub/attestations/1234",
        )
