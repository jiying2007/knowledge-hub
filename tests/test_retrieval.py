import json

from tools.codex_assets.knowledge_hub.common import project_rows, repository_root
from tools.codex_assets.knowledge_hub.context import TASK_TYPES
from tools.codex_assets.knowledge_hub import retrieval
from tools.codex_assets.knowledge_hub.retrieval import run_retrieval_benchmark


def test_known_answer_retrieval_meets_functional_product_thresholds():
    # Wall-clock thresholds belong to the serialized standalone benchmark and
    # engineering/product gates.  Unit tests can run concurrently (and under
    # coverage), so they validate the same authority/integrity corpus without
    # turning shared-runner contention into a functional failure.
    payload = run_retrieval_benchmark(
        repository_root(),
        enable_extended_probes=False,
        enforce_performance_thresholds=False,
    )
    assert payload["status"] == "pass"
    assert payload["case_count"] >= 20
    assert payload["route_case_count"] == len(project_rows(repository_root())) * len(TASK_TYPES) + 4
    assert payload["route_accuracy"] == 1.0
    assert payload["hit_rate"] >= 0.95
    assert payload["mrr"] >= 0.85
    assert payload["ndcg_at_10"] >= 0.90
    assert payload["authority_recall_at_3"] == 1.0
    assert payload["performance_thresholds_enforced"] is False
    integrity = payload["integrity"]
    assert integrity["status"] == "pass"
    for field in (
        "unregistered_result_count",
        "control_result_count",
        "duplicate_result_count",
        "compatibility_hit_count",
        "internal_endpoint_exposure_count",
    ):
        assert integrity[field] == 0


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
    functional_payload = run_retrieval_benchmark(
        tmp_path,
        cases_path=cases,
        enforce_performance_thresholds=False,
    )

    assert payload["status"] == "fail"
    assert payload["latency_target_met"] is False
    assert payload["thresholds"]["maximum_p95_ms"] == 500
    assert functional_payload["status"] == "pass"
    assert functional_payload["latency_target_met"] is False
    assert functional_payload["performance_target_met"] is True
    assert functional_payload["performance_thresholds_enforced"] is False


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


def test_retrieval_benchmark_rejects_forbidden_default_search_result(monkeypatch, tmp_path):
    cases = tmp_path / "cases.json"
    cases.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "authority-boundary",
                        "query": "known",
                        "expected_ids": ["known-id"],
                        "forbidden_ids": ["legacy-id"],
                    }
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
            "results": [
                {"item_id": "known-id", "path": "known.md", "score": 2},
                {"item_id": "legacy-id", "path": "legacy.md", "score": 1},
            ],
            "latency_ms": 10,
        },
    )

    payload = run_retrieval_benchmark(tmp_path, cases_path=cases)

    assert payload["status"] == "fail"
    assert payload["failures"][0]["rank"] == 1
    assert payload["failures"][0]["forbidden_hits"][0]["item_id"] == "legacy-id"
