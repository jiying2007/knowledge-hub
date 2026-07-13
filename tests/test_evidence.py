from tools.codex_assets.knowledge_hub.evidence import (
    evaluate_evidence_contract,
    new_evidence_contract,
)


def _ref(kind, value):
    return {"kind": kind, "ref": value}


def test_empty_embedded_contract_stays_pending():
    contract = new_evidence_contract("embedded-target")
    result = evaluate_evidence_contract(contract)
    assert result["status"] == "pending"
    assert set(result["missing_fields"]) == {
        "owner_ref",
        "source_refs",
        "validation_refs",
        "artifact_refs",
        "device_refs",
        "release_ref",
        "rollback_ref",
    }


def test_ready_status_cannot_bypass_missing_real_evidence():
    contract = new_evidence_contract("software-tool")
    contract["status"] = "ready"
    result = evaluate_evidence_contract(contract)
    assert result["status"] == "pending"
    assert "status" in result["invalid_fields"]


def test_complete_software_contract_is_ready():
    contract = new_evidence_contract("software-tool")
    contract.update(
        {
            "status": "ready",
            "owner_ref": _ref("owner-decision", "decision://1"),
            "source_refs": [_ref("git-commit", "0123456789abcdef")],
            "validation_refs": [_ref("test-report", "artifact://tests")],
            "artifact_refs": [_ref("sha256", "abc")],
            "release_ref": _ref("release", "release://1"),
            "rollback_ref": _ref("rollback", "artifact://rollback"),
        }
    )
    assert evaluate_evidence_contract(contract)["status"] == "ready"
