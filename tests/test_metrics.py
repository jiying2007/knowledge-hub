import errno
import json

import pytest

from tools.codex_assets.knowledge_hub import metrics
from tools.codex_assets.knowledge_hub.metrics import (
    append_optional_telemetry,
    local_metrics,
    record_feedback,
)


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
