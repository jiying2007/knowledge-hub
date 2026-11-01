import pytest
import json

from tools.codex_assets.knowledge_hub.query_concepts import extract_concepts
from tools.codex_assets.knowledge_hub.search_ranking import is_historical_result


@pytest.mark.parametrize("status", ["reviewing", "draft"])
def test_candidate_storage_does_not_imply_historical_lifecycle(status):
    item = {"status": status, "promotion": "none", "source": {"type": "provider-candidate-archive"}}
    assert is_historical_result(item, "projects/p/archive/candidate.md") is False


@pytest.mark.parametrize("status", ["archived", "superseded", "rejected"])
def test_real_historical_lifecycle_remains_historical_everywhere(status):
    item = {"status": status, "promotion": "none", "source": {"type": "provider-candidate-archive"}}
    assert is_historical_result(item, "projects/p/archive/candidate.md") is True
    assert is_historical_result(item, "projects/p/current/candidate.md") is True


def test_legacy_archive_provenance_keeps_fallback_lane():
    assert (
        is_historical_result({"status": "reviewing", "source": {"type": "manual"}}, "projects/p/archive/old.md") is True
    )
    assert is_historical_result({"status": "reviewing", "source": None}, "projects/p/archive/old.md") is True


@pytest.mark.parametrize(
    "query", ["DEVWIRE WiFi当前SDIO频率位宽是什么", "DEVWIRE WiFi当前SDIO频率位宽是什么？", "ModuleX UART波特率是什么"]
)
def test_short_mixed_chinese_question_uses_concepts_without_punctuation(query):
    plan = extract_concepts(query, {"频率": 1, "位宽": 1, "波特率": 1, "当前": 1}, 10)
    assert plan.enabled is True
    assert "是什么" not in plan.terms
    assert "sdio" in plan.anchors or "uart" in plan.anchors


def test_plain_identifier_stays_literal_and_named_unknown_constraint_remains():
    assert extract_concepts("MBI_CVE_Filter", {}, 0).enabled is False
    plan = extract_concepts("UnknownChip UART波特率是什么", {"波特率": 1}, 10)
    assert plan.enabled and "unknownchip" in plan.anchors


def test_candidate_ranking_keeps_lifecycle_information_after_public_projection(tmp_path):
    from test_search import _search_root
    from tools.codex_assets.knowledge_hub.search import search, SearchFilters

    root = _search_root(tmp_path)
    items = [json.loads(line) for line in (root / "registry/items.jsonl").read_text().splitlines()]
    for ident, path, title, summary, source, status in [
        (
            "current",
            "projects/p1/current/generic.md",
            "模块配置",
            "模块波特率的当前参数说明",
            {"type": "manual"},
            "reviewing",
        ),
        (
            "candidate",
            "projects/p1/archive/specific.md",
            "模块波特率配置",
            "模块波特率参数说明",
            {"type": "provider-candidate-archive"},
            "reviewing",
        ),
        (
            "legacy",
            "projects/p1/archive/legacy.md",
            "模块波特率旧版",
            "模块波特率旧版说明",
            {"type": "manual"},
            "reviewing",
        ),
    ]:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text("# " + title + "\n\n" + summary)
        items.append(
            {
                "id": ident,
                "path": path,
                "title": title,
                "summary_zh": summary,
                "source": source,
                "status": status,
                "promotion": "none",
                "kind": "runbook",
                "domain": "projects/p1",
                "owner": "owner-a",
                "tags": [],
                "manual_validation_pending": True,
            }
        )
    (root / "registry/items.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items))
    result = search(root, "模块波特率", limit=10, filters=SearchFilters(domains=["projects/p1"]))
    ids = [r["id"] for r in result["results"]]
    assert ids[0] == "candidate"
    assert ids.index("current") < ids.index("legacy")
    candidate = result["results"][0]
    assert candidate["source"] == "knowledge-hub" and candidate["status"] == "reviewing"
    assert "historical-fallback-lane" not in candidate["why_selected"]
    assert candidate["manual_validation_pending"] is True


def test_heading_focus_cannot_override_stronger_answer_evidence():
    from tools.codex_assets.knowledge_hub.query_focus import focus_order

    topic = {
        "id": "topic",
        "item_id": "topic",
        "path": "current/topic.md",
        "score": 1100,
        "query_coverage": 0.67,
        "why_selected": ["literal-heading-focus"],
    }
    answer = {
        "id": "answer",
        "item_id": "answer",
        "path": "archive/answer.md",
        "score": 1800,
        "query_coverage": 1.0,
        "why_selected": [],
    }
    assert sorted([topic, answer], key=focus_order)[0]["id"] == "answer"
    topic["score"] = 1800
    topic["query_coverage"] = 1.0
    assert sorted([answer, topic], key=focus_order)[0]["id"] == "topic"


def test_question_only_validation_is_not_a_substitute_for_answer_metadata(tmp_path):
    from test_search import _search_root
    from tools.codex_assets.knowledge_hub.search import search, SearchFilters

    root = _search_root(tmp_path)
    query = "模块缓存大小如何设置"
    items = []
    for ident, path, title, summary, body, kind, source in [
        (
            "answer",
            "projects/p1/archive/answer.md",
            "模块缓存设置",
            "模块缓存大小通过配置接口设置。",
            "配置前须核验版本与参数范围。",
            "runbook",
            {"type": "provider-candidate-archive"},
        ),
        (
            "report",
            "projects/p1/validation/report.md",
            "检索验收记录",
            "记录失败样本，尚待修复。",
            query,
            "validation",
            {"type": "manual"},
        ),
    ]:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text("# " + title + "\n\n" + body)
        items.append(
            {
                "id": ident,
                "path": path,
                "title": title,
                "summary_zh": summary,
                "kind": kind,
                "source": source,
                "status": "reviewing",
                "promotion": "none",
                "domain": "projects/p1",
                "owner": "owner-a",
                "tags": [],
            }
        )
    (root / "registry/items.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items))
    assert search(root, query, filters=SearchFilters(domains=["projects/p1"]))["results"][0]["id"] == "answer"


def test_candidate_incidental_body_mention_remains_fallback(tmp_path):
    from test_search import _search_root
    from tools.codex_assets.knowledge_hub.search import search

    root = _search_root(tmp_path)
    rows = []
    for ident, path, title, summary, body, source, status in [
        (
            "legacy",
            "projects/p1/archive/legacy.md",
            "调试指南",
            "调试指南的历史步骤。",
            "历史调试指南",
            {"type": "manual"},
            "archived",
        ),
        (
            "catalog",
            "projects/p1/archive/catalog.md",
            "平台资料总目",
            "资料来源清单。",
            "其他来源中包含调试指南。",
            {"type": "provider-candidate-archive"},
            "reviewing",
        ),
    ]:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text("# " + title + "\n\n" + body)
        rows.append(
            {
                "id": ident,
                "path": path,
                "title": title,
                "summary_zh": summary,
                "source": source,
                "status": status,
                "promotion": "none",
                "kind": "runbook",
                "domain": "projects/p1",
                "owner": "owner-a",
                "tags": [],
            }
        )
    (root / "registry/items.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    result = search(root, "调试指南")
    assert result["results"][0]["id"] == "legacy"
    catalog = next(r for r in result["results"] if r["id"] == "catalog")
    assert "candidate-body-only-fallback" in catalog["why_selected"]
    assert catalog["status"] == "reviewing"
