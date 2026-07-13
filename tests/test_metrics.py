import json

from tools.codex_assets.knowledge_hub.metrics import local_metrics, record_feedback


def test_metrics_do_not_store_raw_queries(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    (cache / "search-telemetry.jsonl").write_text(
        json.dumps(
            {
                "recorded_at": "2026-07-13T00:00:00Z",
                "query_sha256": "abc",
                "result_count": 1,
                "latency_ms": 120,
                "raw_query_stored": False,
            }
        )
        + "\n"
    )

    recorded = record_feedback(tmp_path, "sensitive query body", "found", "item-a", "general")
    payload = local_metrics(tmp_path)
    stored = (cache / "retrieval-feedback.jsonl").read_text()

    assert recorded["raw_query_stored"] is False
    assert "sensitive query body" not in stored
    assert payload["privacy"]["raw_query_stored"] is False
    assert payload["usage"]["invocation_count"] == 0
    assert payload["usage"]["excluded_legacy_or_noninteractive_count"] == 1
    assert payload["adoption"]["ready"] is False


def test_metrics_only_count_interactive_v2_samples(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    (cache / "search-telemetry.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "schema_version": 2,
                        "sample_kind": "interactive",
                        "recorded_at": "2026-07-13T00:00:00Z",
                        "query_sha256": "interactive",
                        "result_count": 1,
                        "latency_ms": 120,
                        "raw_query_stored": False,
                    }
                ),
                json.dumps(
                    {
                        "schema_version": 2,
                        "sample_kind": "benchmark",
                        "recorded_at": "2026-07-13T00:00:01Z",
                        "query_sha256": "benchmark",
                        "result_count": 1,
                        "latency_ms": 900,
                        "raw_query_stored": False,
                    }
                ),
            ]
        )
        + "\n"
    )

    payload = local_metrics(tmp_path)

    assert payload["usage"]["invocation_count"] == 1
    assert payload["usage"]["excluded_legacy_or_noninteractive_count"] == 1
    assert payload["performance"]["search_p95_ms"] == 120
    assert payload["performance"]["status"] == "pass"
