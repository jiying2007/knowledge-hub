import json
import shutil

import pytest

from tools.codex_assets.knowledge_hub import runtime_v3 as rv3
from tools.codex_assets.knowledge_hub import runtime_v3_governance as gov
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root


def _root(tmp_path):
    source = repository_root() / rv3.CONFIG_PATH
    target = tmp_path / rv3.CONFIG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    items = tmp_path / "registry/items.jsonl"
    items.parent.mkdir(parents=True, exist_ok=True)
    items.write_text("", encoding="utf-8")
    return tmp_path


def test_a2a_declared_but_uncataloged_capability_fails_closed(tmp_path, monkeypatch):
    def fake_profile(_root, agent_id):
        if agent_id == "target":
            return {"id": "target", "capabilities": ["ghost.capability"]}
        return {"id": agent_id, "capabilities": []}

    monkeypatch.setattr(gov, "agent_profile", fake_profile)
    monkeypatch.setattr(
        gov,
        "capability_catalog",
        lambda _root: {"knowledge.search": {"mode": "read"}},
    )

    result = gov.a2a_preflight(
        tmp_path,
        "manager",
        "target",
        "delegate unknown operation",
        ["ghost.capability"],
    )

    assert result["status"] == "needs-review"
    assert result["unknown_capabilities"] == ["ghost.capability"]
    assert result["unsupported_capabilities"] == ["ghost.capability"]
    assert result["delegation_executes_task"] is False
    assert result["human_review_required"] is True


def test_execution_receipt_rejects_historical_content_tamper(tmp_path):
    root = _root(tmp_path)
    gov.record_execution_receipt(
        root,
        "knowledge-steward",
        "audit knowledge",
        "report-only",
        ["item:a"],
    )
    ledger = root / ".cache/knowledge-hub/runtime-v3/execution-receipts.jsonl"
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    rows[0]["action"] = "tampered action"
    ledger.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows)
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(KnowledgeHubError, match="failed integrity check"):
        gov.record_execution_receipt(
            root,
            "knowledge-steward",
            "next action",
            "report-only",
            ["item:b"],
        )

    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 1


def test_execution_receipt_rejects_broken_previous_link(tmp_path):
    root = _root(tmp_path)
    gov.record_execution_receipt(
        root,
        "knowledge-steward",
        "first action",
        "report-only",
        ["item:a"],
    )
    gov.record_execution_receipt(
        root,
        "knowledge-steward",
        "second action",
        "report-only",
        ["item:b"],
    )
    ledger = root / ".cache/knowledge-hub/runtime-v3/execution-receipts.jsonl"
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    rows[1]["previous_receipt_sha256"] = "0" * 64
    ledger.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows)
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(KnowledgeHubError, match="invalid previous link"):
        gov.record_execution_receipt(
            root,
            "knowledge-steward",
            "third action",
            "report-only",
            ["item:c"],
        )

    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 2
