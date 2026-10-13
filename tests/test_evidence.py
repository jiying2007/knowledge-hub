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


def _ready_aggregate_contract(*members):
    contract = new_evidence_contract("aggregate-group", members)
    contract.update(
        {
            "status": "ready",
            "owner_ref": _ref("owner-decision", "decision://aggregate-owner"),
        }
    )
    return contract


def test_aggregate_self_membership_is_not_a_readiness_dependency():
    contract = _ready_aggregate_contract("x5-rdk")
    result = evaluate_evidence_contract(
        contract,
        ready_member_ids=[],
        current_project_id="x5-rdk",
    )
    assert result["status"] == "ready"
    assert result["missing_fields"] == []


def test_aggregate_self_and_ready_real_member_are_ready():
    contract = _ready_aggregate_contract("mcu", "gd32l235")
    result = evaluate_evidence_contract(
        contract,
        ready_member_ids=["gd32l235"],
        current_project_id="mcu",
    )
    assert result["status"] == "ready"
    assert result["missing_fields"] == []


def test_aggregate_missing_real_member_remains_fail_closed():
    contract = _ready_aggregate_contract("mcu", "gd32l235")
    result = evaluate_evidence_contract(
        contract,
        ready_member_ids=[],
        current_project_id="mcu",
    )
    assert result["status"] == "pending"
    assert "member_project_ids" in result["missing_fields"]
    assert "status" in result["invalid_fields"]


def test_aggregate_without_current_project_keeps_legacy_member_check():
    contract = _ready_aggregate_contract("x5-rdk")
    result = evaluate_evidence_contract(contract, ready_member_ids=[])
    assert result["status"] == "pending"
    assert "member_project_ids" in result["missing_fields"]


def test_aggregate_diagnostics_distinguish_empty_list_from_pending_members():
    empty = evaluate_evidence_contract(_ready_aggregate_contract())
    pending = evaluate_evidence_contract(
        _ready_aggregate_contract("mcu", "ready", "pending", "unknown"),
        ready_member_ids=["ready", "unrelated"], current_project_id="mcu",
    )
    assert empty["member_diagnostics"]["status"] == "missing-members"
    assert empty["member_diagnostics"]["registered_member_ids"] == []
    assert pending["status"] == "pending"
    assert "member_project_ids" in pending["missing_fields"]
    assert pending["member_diagnostics"] == {
        "status": "member-evidence-pending",
        "registered_member_ids": ["mcu", "pending", "ready", "unknown"],
        "dependency_member_ids": ["pending", "ready", "unknown"],
        "ready_member_ids": ["ready"],
        "pending_member_ids": ["pending", "unknown"],
    }


def test_member_readiness_does_not_override_pending_declaration_or_owner():
    contract = _ready_aggregate_contract("mcu", "ready")
    contract["status"] = "pending"
    result = evaluate_evidence_contract(contract, ["ready"], "mcu")
    assert result["member_diagnostics"]["status"] == "members-ready"
    assert result["status"] == "pending"
    contract["status"] = "ready"
    contract["owner_ref"] = None
    result = evaluate_evidence_contract(contract, ["ready"], "mcu")
    assert result["member_diagnostics"]["status"] == "members-ready"
    assert result["status"] == "pending"
    assert "owner_ref" in result["missing_fields"]


def test_self_only_diagnostics_have_no_pending_dependency():
    result = evaluate_evidence_contract(_ready_aggregate_contract("self"), [], "self")
    assert result["status"] == "ready"
    assert result["member_diagnostics"]["dependency_member_ids"] == []
    assert result["member_diagnostics"]["pending_member_ids"] == []
