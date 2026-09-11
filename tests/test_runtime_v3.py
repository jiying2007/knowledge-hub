import json
import shutil

import pytest

from tools.codex_assets.knowledge_hub import runtime_v3 as rv3
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root


def _root(tmp_path):
    source = repository_root() / rv3.CONFIG_PATH
    target = tmp_path / rv3.CONFIG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    rows = [
        {
            "id": "active-fact",
            "title": "UART timestamp synchronization",
            "kind": "project-current",
            "domain": "projects/demo",
            "path": "projects/demo/current/uart.md",
            "visibility": "team-internal",
            "status": "active",
            "owner": "owner-a",
            "summary_zh": "UART 时间戳同步已经启用。",
            "tags": ["uart", "timestamp"],
            "updated_at": "2026-09-01",
            "review_after": "2026-12-01",
            "evidence_refs": ["evidence:a"],
            "agent_contract": {
                "schema_version": 1,
                "role": "assertion",
                "force": "advisory",
                "relations": {"related_to": ["reviewing-note"]},
            },
        },
        {
            "id": "reviewing-note",
            "title": "Serial clock candidate",
            "kind": "debug-record",
            "domain": "projects/demo",
            "path": "projects/demo/archive/serial.md",
            "visibility": "team-internal",
            "status": "reviewing",
            "owner": "owner-a",
            "summary_zh": "串口时钟候选排障结论。",
            "tags": ["serial", "clock"],
            "updated_at": "2026-08-01",
            "review_after": "2026-10-01",
            "evidence_refs": ["evidence:b"],
        },
        {
            "id": "expired-fact",
            "title": "Expired protocol",
            "kind": "project-current",
            "domain": "projects/demo",
            "path": "projects/demo/current/expired.md",
            "visibility": "team-internal",
            "status": "active",
            "owner": "owner-a",
            "summary_zh": "已经失效的协议。",
            "tags": ["protocol"],
            "valid_to": "2026-01-01",
            "updated_at": "2025-01-01",
            "review_after": "2025-02-01",
            "evidence_refs": ["evidence:c"],
        },
        {
            "id": "personal-note",
            "title": "Personal UART note",
            "kind": "personal-note",
            "domain": "notes",
            "path": "notes/personal/uart.md",
            "visibility": "personal-local",
            "status": "personal",
            "owner": "owner-a",
            "summary_zh": "个人串口笔记。",
            "tags": ["uart"],
        },
    ]
    for row in rows:
        path = tmp_path / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# {}\n\n{}\n".format(row["title"], row["summary_zh"]), encoding="utf-8")
    (tmp_path / "registry/items.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    return tmp_path


def test_hybrid_search_respects_temporal_visibility_and_authority(tmp_path, monkeypatch):
    root = _root(tmp_path)
    monkeypatch.setattr(rv3, "SearchIndex", lambda root: object())
    monkeypatch.setattr(
        rv3,
        "search",
        lambda *args, **kwargs: {
            "results": [
                {"id": "active-fact", "item_id": "active-fact", "score": 10, "why_selected": ["title"]},
                {"id": "expired-fact", "item_id": "expired-fact", "score": 9, "why_selected": ["title"]},
            ]
        },
    )
    result = rv3.hybrid_search(
        root,
        "UART timestamp",
        knowledge_scopes=("projects",),
        as_of="2026-09-11",
    )
    ids = [row["id"] for row in result["results"]]
    assert "active-fact" in ids
    assert "expired-fact" not in ids
    assert "personal-note" not in ids
    assert result["authority_contract"]["derived_ranking_is_authority"] is False
    row = next(item for item in result["results"] if item["id"] == "active-fact")
    assert row["score_components"]["authority"] == 1.0


def test_context_graph_is_derived(tmp_path):
    graph = rv3.context_graph(_root(tmp_path), ["active-fact"], hops=1)
    assert graph["authoritative"] is False
    assert graph["edges"] == [
        {"source_id": "active-fact", "relation": "related_to", "target_id": "reviewing-note"}
    ]


def test_context_compiler_keeps_evidence_authority(tmp_path, monkeypatch):
    root = _root(tmp_path)
    monkeypatch.setattr(
        rv3,
        "hybrid_search",
        lambda *args, **kwargs: {"results": [{"id": "active-fact"}]},
    )
    monkeypatch.setattr(
        rv3,
        "build_evidence_pack",
        lambda *args, **kwargs: {"must": [], "context": [{"id": "active-fact"}]},
    )
    result = rv3.compile_context(root, "UART", agent_id="embedded-expert")
    assert result["agent"]["id"] == "embedded-expert"
    assert result["authority_contract"]["evidence_pack_controls_constraints"] is True
    assert result["authority_contract"]["graph_can_promote_lifecycle"] is False


def test_agent_capability_unknown_agent_fails_closed(tmp_path):
    with pytest.raises(KnowledgeHubError, match="unknown agent"):
        rv3.require_capability(_root(tmp_path), "ghost", "knowledge.search")


def test_memory_candidate_never_writes_canonical():
    candidate = rv3.memory_candidate(
        "embedded-expert", "semantic", "稳定工程结论。", ["item:a"]
    )
    assert candidate["durable"] is True
    assert candidate["canonical_write_permitted"] is False
    assert candidate["target"] == "reviewing"


def test_feedback_and_adaptive_retrieval_are_local_and_shadow(tmp_path):
    root = _root(tmp_path)
    for index in range(10):
        result = rv3.record_feedback(
            root,
            "knowledge-steward",
            "sensitive query {}".format(index),
            "missing" if index < 3 else "accepted",
        )
        assert result["record"]["raw_query_stored"] is False
        assert "sensitive query" not in json.dumps(result["record"])
    proposal = rv3.adaptive_retrieval_proposal(root)
    assert proposal["status"] == "proposal"
    assert proposal["auto_apply"] is False
    assert proposal["proposed_weights"]["semantic"] > proposal["current_weights"]["semantic"]


def test_api_local_write_disabled_by_default(tmp_path):
    with pytest.raises(KnowledgeHubError, match="local write API is disabled"):
        rv3.api_dispatch(
            _root(tmp_path),
            "feedback",
            {"query": "q", "outcome": "accepted"},
            agent_id="knowledge-steward",
        )


def test_mcp_is_read_only_and_reports_current_protocol(tmp_path):
    root = _root(tmp_path)
    tools = rv3.handle_mcp_request(
        root, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    )
    assert {tool["name"] for tool in tools["result"]["tools"]} == {
        "knowledge_search",
        "knowledge_context",
        "knowledge_evidence_pack",
        "knowledge_action_check",
    }
    init = rv3.handle_mcp_request(
        root, {"jsonrpc": "2.0", "id": 2, "method": "initialize"}
    )
    assert init["result"]["protocolVersion"] == "2026-07-28"
    assert init["result"]["stateless"] is True


def test_a2a_high_risk_delegation_is_fail_closed(tmp_path):
    root = _root(tmp_path)
    card = rv3.agent_card(root, "release-expert")
    assert card["protocol_version"] == "1.0.0"
    assert card["canonical_write_permitted"] is False
    preflight = rv3.a2a_preflight(
        root,
        "manager-agent",
        "release-expert",
        "publish release",
        ["release.publish"],
    )
    assert preflight["status"] == "needs-review"
    assert preflight["delegation_executes_task"] is False


def test_steward_and_p3_improvement_never_auto_apply(tmp_path):
    root = _root(tmp_path)
    audit = rv3.steward_audit(root, as_of="2026-09-11")
    assert audit["report_only"] is True
    assert audit["canonical_write_performed"] is False
    assert "expired-fact" in [row["id"] for row in audit["stale_active"]]
    plan = rv3.improvement_plan(root, as_of="2026-09-11")
    assert plan["guards"]["auto_apply"] is False
    assert plan["guards"]["auto_promote_active"] is False
    assert plan["guards"]["owner_decision_bypass"] is False


def test_receipt_and_observability_are_non_authoritative(tmp_path):
    root = _root(tmp_path)
    receipt = rv3.execution_receipt(
        "knowledge-steward", "audit", "report-only", ["active-fact"]
    )
    assert receipt["canonical_state_changed"] is False
    projection = rv3.trace_projection(root, "embedded-expert", "knowledge.context", "secret")
    assert projection["event"]["raw_query_stored"] is False
    assert "secret" not in json.dumps(projection)
    assert projection["network_export_performed"] is False


def test_runtime_health_declares_derived_planes_non_authoritative(tmp_path):
    health = rv3.runtime_health(_root(tmp_path))
    assert health["status"] == "pass"
    assert health["authority"]["derived_planes_are_authoritative"] is False
