"""Unit boundary tests: real corpus functions with file/parser ports mocked."""
import datetime as dt
import hashlib
import json

import pytest

from tools.codex_assets.knowledge_hub import corpus_review as corpus


def _review():
    return {"human": "absent", "ai": "absent", "ai_closed": "not-verified",
            "ai_snapshot": {"item_sha256_match": None, "content_sha256_match": None,
                            "request_proof": "absent", "state": "absent"}}


@pytest.mark.parametrize("plain", [False, True])
def test_marker_is_p0_even_with_mirrored_fields_or_plain_archive(monkeypatch, tmp_path, plain):
    item = {"id": "synthetic-history", "path": "history.md", "status": "archived",
            "owner": "team-core", "kind": "decision", "review_after": "2026-10-20"}
    marker = "…2200 tokens truncated…"
    text = marker if plain else "---\nreview_status: delegated" + marker + "\n---\nBody.\n"
    raw = text.encode("utf-8")
    monkeypatch.setattr(corpus, "read_repository_bytes_bounded", lambda *_: raw)
    monkeypatch.setattr(corpus, "split_frontmatter", lambda _: ({}, text) if plain else (item, "Body."))
    monkeypatch.setattr(corpus, "scan_secret_text", lambda _: [])
    before = dict(item)
    doc = corpus._document(tmp_path, item)
    assert doc["status"] == "read"
    assert doc["sha256"] == hashlib.sha256(raw).hexdigest()
    assert doc["persisted_tool_truncation"] is True
    assert doc["frontmatter_matches_registry"] is not plain
    flags = corpus._signals(item, doc, {"status": "checked", "missing": 0}, _review(), dt.date(2026, 10, 20))
    assert "persisted-tool-truncation-marker" in flags
    assert corpus._lane(item, flags, "ordinary") == "P0-integrity"
    assert marker not in json.dumps(doc, ensure_ascii=False)
    assert item == before  # Classification does not repair/reapprove the record.


def test_clean_archive_is_not_declared_truncated(monkeypatch, tmp_path):
    item = {"id": "historical", "path": "history.md", "status": "archived",
            "owner": "team-core", "kind": "decision", "review_after": "2026-10-20"}
    monkeypatch.setattr(corpus, "read_repository_bytes_bounded", lambda *_: b"Body.")
    monkeypatch.setattr(corpus, "split_frontmatter", lambda _: ({}, "Body."))
    monkeypatch.setattr(corpus, "scan_secret_text", lambda _: [])
    doc = corpus._document(tmp_path, item)
    assert doc["persisted_tool_truncation"] is False
    flags = corpus._signals(item, doc, {"status": "checked", "missing": 0}, _review(), dt.date(2026, 10, 20))
    assert "persisted-tool-truncation-marker" not in flags
    assert corpus._lane(item, flags, "ordinary") == "P3-historical-integrity"


@pytest.mark.parametrize("privacy", [{"status": "personal"}, {"visibility": "personal-local"}])
def test_existing_private_exclusion_precedes_body_reader_and_detector(monkeypatch, tmp_path, privacy):
    def forbidden(*_):
        raise AssertionError("private body must not be inspected")
    monkeypatch.setattr(corpus, "_document", forbidden)
    monkeypatch.setattr(corpus, "_archive_directory", forbidden)
    monkeypatch.setattr(corpus, "has_persisted_tool_truncation", forbidden)
    row = corpus._item_row(tmp_path, dict(id="synthetic-private", **privacy), dt.date(2026, 10, 20), {}, {})
    assert row["lane"] == "personal-excluded"
    assert row["machine_checked"] is False
    assert "body" not in row and "path" not in row
