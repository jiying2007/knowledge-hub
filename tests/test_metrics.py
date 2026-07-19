import errno
import hashlib
import json

import pytest

from tools.codex_assets.knowledge_hub import metrics
from tools.codex_assets.knowledge_hub.metrics import (
    append_optional_telemetry,
    local_metrics,
    record_feedback,
)


def _interaction(
    query,
    kind="search",
    recorded_at="2026-07-13T00:00:00Z",
    latency_ms=120,
    result_ids=("item-a",),
    performance_contract=metrics.PERFORMANCE_CONTRACT,
    index_state="warm",
    index_ensure_ms=40,
):
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    row = {
        "schema_version": metrics.INTERACTIVE_TELEMETRY_SCHEMA_VERSION,
        "sample_kind": "interactive",
        "interaction_contract": metrics.INTERACTION_CONTRACT,
        "interaction_id": metrics.make_interaction_id(kind, query_hash, recorded_at),
        "retrieval_kind": kind,
        "recorded_at": recorded_at,
        "query_sha256": query_hash,
        "result_count": len(result_ids),
        "result_ids": list(result_ids),
        "latency_ms": latency_ms,
        "index_state": index_state,
        "stage_timing": {"index_ensure_ms": index_ensure_ms},
        "raw_query_stored": False,
    }
    if performance_contract:
        row["performance_contract"] = performance_contract
    return row


def test_interaction_ids_are_unique_for_same_query_and_second():
    query_hash = hashlib.sha256(b"same query").hexdigest()

    first = metrics.make_interaction_id("search", query_hash, "2026-07-13T00:00:00Z")
    second = metrics.make_interaction_id("search", query_hash, "2026-07-13T00:00:00Z")

    assert first != second


def test_metrics_do_not_store_raw_queries(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    (cache / "search-telemetry.jsonl").write_text(
        json.dumps(_interaction("sensitive query body"))
        + "\n"
        + json.dumps({"recorded_at": "2026-07-12T00:00:00Z", "latency_ms": 999})
        + "\n"
    )

    recorded = record_feedback(tmp_path, "sensitive query body", "found", "item-a", "general")
    payload = local_metrics(tmp_path)
    stored = (cache / "retrieval-feedback.jsonl").read_text()

    assert recorded["raw_query_stored"] is False
    assert "sensitive query body" not in stored
    assert payload["privacy"]["raw_query_stored"] is False
    assert payload["schema_version"] == 4
    assert payload["usage"]["invocation_count"] == 1
    assert payload["usage"]["excluded_historical_or_noninteractive_count"] == 1
    assert payload["retrieval"]["feedback_count"] == 1
    assert payload["performance"]["status"] == "pending"
    assert payload["adoption"]["ready"] is False


def test_metrics_only_count_current_contract_interactive_samples(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    (cache / "search-telemetry.jsonl").write_text(
        "\n".join(
            [
                json.dumps(_interaction("current")),
                json.dumps(
                    {
                        "schema_version": 2,
                        "sample_kind": "interactive",
                        "recorded_at": "2026-07-13T00:00:01Z",
                        "query_sha256": "historical",
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
    assert payload["usage"]["excluded_historical_or_noninteractive_count"] == 1
    assert payload["performance"]["search_p95_ms"] == 120
    assert payload["performance"]["status"] == "pending"


def test_metrics_keep_usage_but_exclude_stale_performance_contract(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    rows = [
        _interaction("current-performance"),
        _interaction(
            "historical-performance",
            recorded_at="2026-07-13T00:00:01Z",
            latency_ms=9999,
            performance_contract="knowledge-retrieval-performance-v1",
        ),
    ]
    (cache / "search-telemetry.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows)
    )

    payload = local_metrics(tmp_path)

    assert payload["usage"]["invocation_count"] == 2
    assert payload["performance"]["search_sample_count"] == 1
    assert payload["performance"]["search_p95_ms"] == 120
    assert payload["performance"]["excluded_stale_contract_sample_count"] == 1
    assert payload["measurement_contract"]["performance_contract"] == metrics.PERFORMANCE_CONTRACT


def test_metrics_separate_index_preparation_from_warm_interactive_sla(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    search_rows = [
        _interaction(
            "search-{}".format(index),
            recorded_at="2026-07-13T00:00:{:02d}Z".format(index),
        )
        for index in range(metrics.MINIMUM_PERFORMANCE_SAMPLE_COUNT)
    ]
    context_rows = [
        _interaction(
            "context-{}".format(index),
            kind="context",
            recorded_at="2026-07-13T00:01:{:02d}Z".format(index),
            latency_ms=240,
        )
        for index in range(metrics.MINIMUM_PERFORMANCE_SAMPLE_COUNT)
    ]
    search_rows.append(
        _interaction(
            "search-rebuild",
            recorded_at="2026-07-13T00:02:00Z",
            latency_ms=4700,
            index_state="rebuilt",
            index_ensure_ms=4500,
        )
    )
    context_rows.append(
        _interaction(
            "context-rebuild",
            kind="context",
            recorded_at="2026-07-13T00:02:01Z",
            latency_ms=4800,
            index_state="rebuilt",
            index_ensure_ms=4600,
        )
    )
    (cache / "search-telemetry.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in search_rows)
    )
    (cache / "context-telemetry.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in context_rows)
    )

    payload = local_metrics(tmp_path)

    assert payload["performance"]["status"] == "pass"
    assert payload["performance"]["search_p95_ms"] == 120
    assert payload["performance"]["context_p95_ms"] == 240
    assert payload["performance"]["index_preparation"]["status"] == "pass"
    assert payload["performance"]["index_preparation"]["search_p95_ms"] == 4500
    assert payload["performance"]["end_to_end_observed"]["search_p95_ms"] == 4700
    assert payload["performance"]["excluded_non_warm_sample_count"] == 2


def test_metrics_fail_when_index_preparation_exceeds_bound(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    rebuilt = _interaction(
        "slow-rebuild",
        latency_ms=6200,
        index_state="rebuilt",
        index_ensure_ms=6000,
    )
    (cache / "search-telemetry.jsonl").write_text(json.dumps(rebuilt) + "\n")

    payload = local_metrics(tmp_path)

    assert payload["performance"]["evaluable"] is False
    assert payload["performance"]["index_preparation"]["status"] == "fail"
    assert payload["performance"]["status"] == "fail"


def test_metrics_require_enough_current_search_and_context_samples(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    search_rows = [
        _interaction("search-{}".format(index), recorded_at="2026-07-13T00:00:{:02d}Z".format(index))
        for index in range(metrics.MINIMUM_PERFORMANCE_SAMPLE_COUNT)
    ]
    context_rows = [
        _interaction(
            "context-{}".format(index),
            kind="context",
            recorded_at="2026-07-13T00:01:{:02d}Z".format(index),
            latency_ms=240,
        )
        for index in range(metrics.MINIMUM_PERFORMANCE_SAMPLE_COUNT)
    ]
    (cache / "search-telemetry.jsonl").write_text("".join(json.dumps(row) + "\n" for row in search_rows))
    (cache / "context-telemetry.jsonl").write_text("".join(json.dumps(row) + "\n" for row in context_rows))

    payload = local_metrics(tmp_path)

    assert payload["performance"]["evaluable"] is True
    assert payload["performance"]["status"] == "pass"
    assert payload["adoption"]["ready"] is False


def test_feedback_requires_a_matching_result_and_is_unique(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    interaction = _interaction("bound query")
    (cache / "search-telemetry.jsonl").write_text(json.dumps(interaction) + "\n")

    with pytest.raises(ValueError, match="selected_id"):
        record_feedback(tmp_path, "bound query", "found", "item-missing")

    recorded = record_feedback(tmp_path, "bound query", "found", "item-a")
    assert recorded["record"]["interaction_id"] == interaction["interaction_id"]

    with pytest.raises(ValueError, match="already exists"):
        record_feedback(tmp_path, "bound query", "found", "item-a")

    with pytest.raises(ValueError, match="does not accept selected_id"):
        record_feedback(tmp_path, "bound query", "not-found", "item-a")


def test_metrics_only_count_feedback_bound_to_observed_result(tmp_path):
    cache = tmp_path / ".cache/knowledge-hub"
    cache.mkdir(parents=True)
    first_interaction = _interaction("first query", result_ids=("item-a",))
    second_interaction = _interaction("second query", result_ids=("item-b",))
    (cache / "search-telemetry.jsonl").write_text(
        json.dumps(first_interaction) + "\n" + json.dumps(second_interaction) + "\n"
    )
    recorded = record_feedback(tmp_path, "first query", "found", "item-a")["record"]
    duplicate = dict(recorded)
    invalid_selected = dict(recorded)
    invalid_selected.update(
        {
            "interaction_id": second_interaction["interaction_id"],
            "query_sha256": second_interaction["query_sha256"],
            "selected_id": "item-missing",
        }
    )
    unbound = dict(recorded)
    unbound["interaction_id"] = "f" * 64
    with (cache / "retrieval-feedback.jsonl").open("a") as handle:
        for row in (duplicate, invalid_selected, unbound):
            handle.write(json.dumps(row) + "\n")

    payload = local_metrics(tmp_path)

    assert payload["retrieval"]["feedback_count"] == 1
    assert payload["retrieval"]["excluded_unbound_or_historical_feedback_count"] == 3


def test_feedback_rejects_unobserved_query(tmp_path):
    with pytest.raises(ValueError, match="matching current-contract"):
        record_feedback(tmp_path, "never observed", "not-found")


def test_optional_telemetry_degrades_on_read_only_storage(monkeypatch, tmp_path):
    def deny_write(path, row):
        raise PermissionError(errno.EROFS, "read-only filesystem")

    monkeypatch.setenv("KNOWLEDGE_TELEMETRY", "1")
    monkeypatch.setattr(metrics, "_append_locked", deny_write)

    result = append_optional_telemetry(
        tmp_path / ".cache/knowledge-hub/search-telemetry.jsonl",
        {"query_sha256": "abc"},
    )

    assert result == {
        "status": "degraded",
        "recorded": False,
        "non_blocking": True,
        "reason": "read-only-or-permission-denied",
        "error_code": "EROFS",
    }


def test_optional_telemetry_does_not_hide_programming_errors(monkeypatch, tmp_path):
    def broken_writer(path, row):
        raise RuntimeError("unexpected telemetry bug")

    monkeypatch.setenv("KNOWLEDGE_TELEMETRY", "1")
    monkeypatch.setattr(metrics, "_append_locked", broken_writer)

    with pytest.raises(RuntimeError, match="unexpected telemetry bug"):
        append_optional_telemetry(
            tmp_path / ".cache/knowledge-hub/search-telemetry.jsonl",
            {"query_sha256": "abc"},
        )


def test_optional_telemetry_reports_explicit_disable(monkeypatch, tmp_path):
    cli_disabled = append_optional_telemetry(tmp_path / "unused.jsonl", {}, enabled=False)
    monkeypatch.setenv("KNOWLEDGE_TELEMETRY", "off")
    environment_disabled = append_optional_telemetry(tmp_path / "unused.jsonl", {})

    assert cli_disabled["status"] == "disabled"
    assert cli_disabled["reason"] == "cli-disabled"
    assert environment_disabled["status"] == "disabled"
    assert environment_disabled["reason"] == "environment-disabled"
