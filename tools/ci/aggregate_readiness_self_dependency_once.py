from pathlib import Path


def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit("unexpected {}".format(label))
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


evidence_path = Path("tools/codex_assets/knowledge_hub/evidence.py")
replace_once(
    evidence_path,
    """def evaluate_evidence_contract(\n    contract: Mapping[str, Any],\n    ready_member_ids: Sequence[str] = (),\n) -> Dict[str, Any]:""",
    """def evaluate_evidence_contract(\n    contract: Mapping[str, Any],\n    ready_member_ids: Sequence[str] = (),\n    current_project_id: str = \"\",\n) -> Dict[str, Any]:""",
    "evidence evaluator signature",
)
replace_once(
    evidence_path,
    """    ready_members = set(str(value) for value in ready_member_ids)\n    missing: List[str] = []""",
    """    ready_members = set(str(value) for value in ready_member_ids)\n    current_project = str(current_project_id).strip()\n    missing: List[str] = []""",
    "ready member setup",
)
replace_once(
    evidence_path,
    """        if field == \"member_project_ids\":\n            members = {str(row) for row in value or []}\n            if not members:\n                missing.append(field)\n            elif not members.issubset(ready_members):\n                missing.append(field)\n            continue""",
    """        if field == \"member_project_ids\":\n            members = {str(row) for row in value or []}\n            dependency_members = (\n                members - {current_project} if current_project else members\n            )\n            if not members:\n                missing.append(field)\n            elif not dependency_members.issubset(ready_members):\n                missing.append(field)\n            continue""",
    "aggregate member evaluation block",
)

support_path = Path("tools/codex_assets/knowledge_hub/product_gate_support.py")
replace_once(
    support_path,
    """        evaluation = evaluate_evidence_contract(\n            validation_item.get(\"evidence_contract\", {}),\n            ready_member_ids=sorted(ready_project_ids),\n        )""",
    """        evaluation = evaluate_evidence_contract(\n            validation_item.get(\"evidence_contract\", {}),\n            ready_member_ids=sorted(ready_project_ids),\n            current_project_id=project_id,\n        )""",
    "aggregate second-pass evaluator call",
)

tests_path = Path("tests/test_evidence.py")
text = tests_path.read_text(encoding="utf-8")
if "_ready_aggregate_contract" in text:
    raise SystemExit("aggregate regression tests already present")
addition = '''


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
'''
tests_path.write_text(text.rstrip() + addition + "\n", encoding="utf-8")
