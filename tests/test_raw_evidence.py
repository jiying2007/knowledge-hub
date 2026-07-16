import hashlib
import json

import pytest

from tools.codex_assets.knowledge_hub.raw_evidence import inspect_raw_evidence_ledger
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def _hash(event):
    payload = {key: value for key, value in event.items() if key != "content_hash"}
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _event(event_id, previous_hash, text):
    event = {
        "schema": "rawmem.event.v1",
        "event_id": event_id,
        "ts": "2026-07-16T00:00:00Z",
        "source": "codex",
        "event_type": "task_note",
        "project": "demo",
        "cwd": "/private/demo",
        "summary": text,
        "raw_text": text,
        "tags": [],
        "artifacts": [],
        "payload": {
            "redaction": {"count": 1},
            "capture_policy": {"schema_version": "rawmem.capture_policy.v1"},
        },
        "privacy": {"scope": "local_only", "review_required": True},
        "previous_hash": previous_hash,
    }
    event["content_hash"] = _hash(event)
    return event


def _ledger(tmp_path):
    first = _event("evt_1", None, "password=[REDACTED]")
    second = _event("evt_2", first["content_hash"], "safe observation")
    path = tmp_path / "events.jsonl"
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in (first, second))
    )
    return path


def test_raw_evidence_inspection_is_read_only_metadata_projection(tmp_path):
    path = _ledger(tmp_path)
    payload = inspect_raw_evidence_ledger(path)
    serialized = json.dumps(payload, ensure_ascii=False)

    assert payload["status"] == "pass"
    assert payload["chain_status"] == "verified"
    assert payload["ledger"]["event_count"] == 2
    assert payload["hub_route"]["eligible_for_text_ingest"] is False
    assert payload["privacy"]["content_echoed"] is False
    assert "safe observation" not in serialized
    assert "/private/demo" not in serialized
    assert not (tmp_path / "events.jsonl.lock").exists()
    assert not (tmp_path / "events.jsonl.state.json").exists()
    assert validate_instance(repository_root(), "raw-evidence-inspection-v1", payload)["status"] == "pass"


def test_raw_evidence_tamper_fails_closed_without_echoing_body(tmp_path):
    path = _ledger(tmp_path)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[1]["summary"] = "tampered body"
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))

    payload = inspect_raw_evidence_ledger(path)
    assert payload["status"] == "fail"
    assert payload["chain_status"] == "failed"
    assert any(row["code"] == "content_hash_mismatch" for row in payload["errors"])
    assert "tampered body" not in json.dumps(payload)


def test_raw_evidence_rejects_file_budget_and_bounds_line_processing(tmp_path):
    path = _ledger(tmp_path)
    with pytest.raises(KnowledgeHubError, match="ledger exceeds"):
        inspect_raw_evidence_ledger(path, max_bytes=1)

    payload = inspect_raw_evidence_ledger(path, max_line_bytes=32)
    assert payload["status"] == "fail"
    assert any(row["code"] == "line_too_large" for row in payload["errors"])
    assert payload["limits"]["max_line_bytes"] == 32


def test_raw_evidence_max_events_fails_closed(tmp_path):
    path = _ledger(tmp_path)
    payload = inspect_raw_evidence_ledger(path, max_events=1)
    assert payload["status"] == "fail"
    assert any(row["code"] == "event_limit_exceeded" for row in payload["errors"])
    assert payload["ledger"]["event_count"] == 1
