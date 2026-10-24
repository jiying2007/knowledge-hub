"""Archived code/config is provenance, never current Markdown approval."""
import datetime as dt
import hashlib
import json

import pytest

from tools.codex_assets.knowledge_hub import corpus_review as corpus


@pytest.mark.parametrize("path,data,expected", [
    ("tools/a.sh", b"#!/bin/bash\necho test\n", True),
    ("tools/a.sh", b"#!/usr/bin/env bash\nexit 0\n", True),
    ("registry/a.json", b'{"version":1}\n', True),
    ("registry/a.json", b"[]\n", True),
    ("registry/a.json", b"{bad", False),
    ("registry/a.json", b"42\n", False),
    ("registry/a.json", b"\xff", False),
    ("projects/a.sh", b"#!/bin/bash\n", False),
    ("tools/a.txt", b"#!/bin/bash\n", False),
    ("tools/a.sh.md", b"#!/bin/bash\n", False),
    ("tools/a.sh", b"---\nstatus: active\n---\n", False),
    ("tools/a.sh", b"\xef\xbb\xbf---\n", False),
    ("tools/a.sh", b"", False),
    ("tools/../projects/a.sh", b"#!/bin/bash\n", False),
    ("tools//a.sh", b"#!/bin/bash\n", False),
    ("./tools/a.sh", b"#!/bin/bash\n", False),
    ("tools/a\\b.sh", b"#!/bin/bash\n", False),
    ("registry/a\n.json", b"{}", False),
])
def test_classifier_is_narrow(path, data, expected):
    item = {"kind": "audit", "status": "archived"}
    assert corpus._archived_non_markdown_asset(item, path, data) is expected


@pytest.mark.parametrize("status,kind", [
    ("active", "audit"), ("reviewing", "audit"), ("draft", "audit"),
    ("archived", "decision"), ("archived", "debug-record"),
])
def test_classifier_does_not_exempt_current_or_unrelated_kinds(status, kind):
    assert not corpus._archived_non_markdown_asset(
        {"status": status, "kind": kind}, "registry/a.json", b"{}\n",
    )


def _fixture(tmp_path, path="tools/example.sh", data=b"#!/bin/bash\nexit 0\n", status="archived"):
    root = tmp_path / "hub"
    (root / "registry").mkdir(parents=True)
    (root / "registry/review-risk-policy.json").write_text(json.dumps({
        "default_class": "ordinary",
        "classes": {"ordinary": {"ai_first_action": "auto-triage"}}, "rules": [],
    }), encoding="utf-8")
    row = {
        "id": "archived-audit", "title": "Archived audit asset", "kind": "audit",
        "status": status, "domain": "governance", "path": path, "owner": "team-core",
        "review_after": "2026-01-01", "visibility": "team-internal",
        "evidence_refs": [path, "governance/missing-reference.md"], "validation_refs": [],
    }
    (root / "registry/items.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return root, row, target


@pytest.mark.parametrize("path,data", [
    ("tools/example.sh", b"#!/usr/bin/env bash\nexit 0\n"),
    ("registry/example.json", b'{"routes":[]}\n'),
])
def test_full_report_preserves_hash_missing_refs_and_authority(tmp_path, monkeypatch, path, data):
    root, item, _ = _fixture(tmp_path, path, data)
    before = (root / "registry/items.jsonl").read_bytes()
    # Force a synthetic secret finding; classification must not hide it.
    monkeypatch.setattr(corpus, "scan_secret_text", lambda text: ["synthetic-finding"])
    report = corpus.build_corpus_review(root, dt.date(2026, 10, 20))
    row = report["rows"][0]
    assert row["id"] == item["id"]
    assert row["body"]["sha256"] == hashlib.sha256(data).hexdigest()
    assert row["body"]["bytes"] == len(data)
    assert row["body"]["frontmatter_matches_registry"] is False
    assert row["body"]["historical_non_markdown_asset"] is True
    assert "frontmatter-drift" not in row["signals"]
    assert set(row["signals"]) >= {
        "archive-plaintext-provenance-only", "local-reference-missing",
        "historical-review-overdue", "secret-pattern-requires-triage",
    }
    assert row["lane"] == "P3-historical-integrity"
    action = report["optimization_queue"]["actions"][0]
    assert action["priority"] == "P0"
    assert action["action"] == "human-security-review"
    assert row["semantic_review_performed"] is False
    assert report["machine_checked_count"] == 1
    assert report["semantic_review_performed"] is False
    assert report["owner_approval_performed"] is False
    assert report["active_promoted"] is False
    assert report["canonical_write_performed"] is False
    assert before == (root / "registry/items.jsonl").read_bytes()


@pytest.mark.parametrize("status", ["active", "reviewing", "draft"])
def test_full_report_current_assets_still_fail_frontmatter_contract(tmp_path, status):
    root, _, _ = _fixture(tmp_path, status=status)
    row = corpus.build_corpus_review(root, dt.date(2026, 10, 20))["rows"][0]
    assert "frontmatter-drift" in row["signals"]
    assert row["lane"] == "P0-integrity"


@pytest.mark.parametrize("data", [None, b"\xff"])
def test_missing_or_non_utf8_asset_remains_failed(tmp_path, data):
    root, _, target = _fixture(tmp_path)
    if data is None:
        target.unlink()
    else:
        target.write_bytes(data)
    report = corpus.build_corpus_review(root, dt.date(2026, 10, 20))
    assert report["machine_checked_count"] == 0
    assert report["machine_failed_count"] == 1
    assert "body-unavailable-or-invalid" in report["rows"][0]["signals"]
    assert report["rows"][0]["lane"] == "P0-integrity"


@pytest.mark.parametrize("key,value", [("status", "personal"), ("visibility", "personal-local")])
def test_private_asset_classification_never_reads_the_body(tmp_path, monkeypatch, key, value):
    root, row, _ = _fixture(tmp_path)
    row[key] = value
    (root / "registry/items.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")

    def forbidden(*args, **kwargs):
        pytest.fail("personal body must not be read")

    monkeypatch.setattr(corpus, "read_repository_bytes_bounded", forbidden)
    report = corpus.build_corpus_review(root, dt.date(2026, 10, 20))
    assert report["private_excluded_count"] == 1
    assert report["machine_attempted_count"] == 0
    assert row["path"] not in json.dumps(report)
    assert row["id"] not in json.dumps(report)


def test_full_report_missing_reference_still_routes_to_evidence_review(tmp_path):
    root, _, _ = _fixture(tmp_path)
    report = corpus.build_corpus_review(root, dt.date(2026, 10, 20))
    action = report["optimization_queue"]["actions"][0]
    assert action["priority"] == "P1"
    assert action["action"] == "machine-discover-references"
    assert action["next_boundary"] == "governed-evidence-review"
    assert action["content_change_approved"] is False
