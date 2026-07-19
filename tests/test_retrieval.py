import json

from tools.codex_assets.knowledge_hub.common import project_rows, repository_root
from tools.codex_assets.knowledge_hub.context import TASK_TYPES
from tools.codex_assets.knowledge_hub import retrieval
from tools.codex_assets.knowledge_hub.retrieval import run_retrieval_benchmark


def test_known_answer_retrieval_meets_product_thresholds():
    payload = run_retrieval_benchmark(repository_root(), maximum_p95_ms=5000)
    assert payload["status"] == "pass"
    assert payload["case_count"] >= 20
    assert payload["route_case_count"] == len(project_rows(repository_root())) * len(TASK_TYPES) + 4
    assert payload["route_accuracy"] == 1.0
    assert payload["hit_rate"] >= 0.95
    assert payload["mrr"] >= 0.85


def test_retrieval_benchmark_rejects_p95_above_product_target(monkeypatch, tmp_path):
    cases = tmp_path / "cases.json"
    cases.write_text(
        json.dumps(
            {
                "cases": [
                    {"id": "slow", "query": "known", "expected_ids": ["known-id"]}
                ]
            }
        )
    )
    class FakeSearchIndex:
        def __init__(self, _root):
            pass

        def ensure(self):
            return {"state": "warm", "rebuilt": False, "updated": False}

    monkeypatch.setattr(retrieval, "SearchIndex", FakeSearchIndex)
    monkeypatch.setattr(
        retrieval,
        "search",
        lambda *_args, **_kwargs: {
            "results": [{"item_id": "known-id", "path": "known.md", "score": 1}],
            "latency_ms": 501,
        },
    )

    payload = run_retrieval_benchmark(tmp_path, cases_path=cases)

    assert payload["status"] == "fail"
    assert payload["latency_target_met"] is False
    assert payload["thresholds"]["maximum_p95_ms"] == 500


def test_retrieval_benchmark_prepares_index_before_warm_measurement(monkeypatch, tmp_path):
    cases = tmp_path / "cases.json"
    cases.write_text(
        json.dumps(
            {
                "cases": [
                    {"id": "known", "query": "known", "expected_ids": ["known-id"]}
                ]
            }
        )
    )
    events = []

    class FakeSearchIndex:
        def __init__(self, _root):
            pass

        def ensure(self):
            events.append("prepare")
            return {"state": "rebuilt", "rebuilt": True, "updated": False}

    def fake_search(*_args, **_kwargs):
        assert events == ["prepare"]
        return {
            "results": [{"item_id": "known-id", "path": "known.md", "score": 1}],
            "latency_ms": 10,
        }

    monkeypatch.setattr(retrieval, "SearchIndex", FakeSearchIndex)
    monkeypatch.setattr(retrieval, "search", fake_search)

    payload = run_retrieval_benchmark(tmp_path, cases_path=cases)

    assert payload["status"] == "pass"
    assert payload["measurement_profile"] == "warm-interactive"
    assert payload["index_preparation"]["state"] == "rebuilt"
    assert payload["index_preparation_target_met"] is True
    assert payload["latency_ms"]["total"] >= payload["latency_ms"]["measured_queries"]
