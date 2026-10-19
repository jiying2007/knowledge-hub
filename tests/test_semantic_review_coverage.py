import json

import pytest

from tools.codex_assets.knowledge_hub.semantic_review_coverage import build_coverage, main

SHA_A = "a" * 64
SHA_B = "b" * 64
HEAD = "c" * 40


def corpus():
    return {
        "schema_version": "knowledge-hub.corpus-review/v1", "source_revision": HEAD,
        "report_sha256": SHA_B, "item_count": 4, "accounted_for_count": 4,
        "canonical_write_performed": False, "private_excluded_count": 1,
        "rows": [
            {"id": "r1", "status": "reviewing", "lane": "P2-candidate-review",
             "body": {"status": "read", "sha256": SHA_A}, "signals": []},
            {"id": "a1", "status": "active", "lane": "P1-current-validity",
             "body": {"status": "read", "sha256": SHA_B}, "signals": []},
            {"id": "archive-dir", "status": "archived", "lane": "P3-historical-integrity",
             "body": {"status": "archive-directory-observed", "sha256": ""}, "signals": []},
            {"id": "redacted-sha256:private", "status": "personal", "lane": "personal-excluded",
             "body": None},
        ],
    }


def comment(id_, sha=SHA_A, user="jiying2007", marker=True):
    return {"user": {"login": user}, "body": (
        "semantic_review_performed=true\n" if marker else "Metadata only\n"
    ) + "| Registry ID | SHA | result |\n| -- | -- | -- |\n| `{}` | `{}` | needs-evidence |\n".format(id_, sha)}


def test_count_exact_and_privacy():
    report = build_coverage(corpus(), [comment("r1")], owner="jiying2007")
    assert report["registry_item_count"] == 4
    assert report["private_excluded_count"] == 1
    assert report["non_private_count"] == 3
    assert report["current_body_claim_count"] == 1
    assert report["pending_body_claim_count"] == 2
    assert report["body_unavailable_count"] == 1
    assert report["machine_semantic_verification_performed"] is False
    assert "redacted-sha256:private" not in json.dumps(report)


def test_stale_and_spoofed_receipts_do_not_count():
    report = build_coverage(corpus(), [
        comment("r1", SHA_B), comment("a1", SHA_B, user="someone-else"),
        comment("a1", SHA_B, marker=False)
    ], owner="jiying2007")
    assert report["current_body_claim_count"] == 0
    assert report["stale_body_claim_count"] == 1
    assert report["untrusted_issue_comment_count"] == 1
    assert report["next_review_queue"][0]["status"] == "active"
    assert any(x["reason"] == "stale-claim" for x in report["next_review_queue"])


def test_old_and_current_receipts_resolve_at_exact_hash():
    result = build_coverage(corpus(), [
        comment("r1", SHA_B), comment("r1", SHA_A)
    ], owner="jiying2007")
    assert result["current_body_claim_count"] == 1
    assert result["stale_body_claim_count"] == 0


def test_fail_closed_on_incomplete_or_malicious_corpus():
    data = corpus()
    data["rows"][0]["id"] = data["rows"][1]["id"]
    with pytest.raises(ValueError, match="duplicated"):
        build_coverage(data, [], owner="jiying2007")
    data = corpus()
    data["private_excluded_count"] = 0
    with pytest.raises(ValueError, match="private exclusion"):
        build_coverage(data, [], owner="jiying2007")
    data = corpus()
    data["source_revision"] = "unknown"
    with pytest.raises(ValueError, match="source revision"):
        build_coverage(data, [], owner="jiying2007")


def test_reject_oversized_comments():
    x = comment("r1")
    x["body"] += "a" * 70000
    with pytest.raises(ValueError, match="oversized"):
        build_coverage(corpus(), [x], owner="jiying2007")


def test_cli_writes_report_only(tmp_path):
    source = tmp_path / "corpus.json"
    journal = tmp_path / "comments.jsonl"
    output = tmp_path / "coverage.json"
    source.write_text(json.dumps(corpus()), encoding="utf-8")
    journal.write_text(json.dumps(comment("r1")) + "\n", encoding="utf-8")
    rc = main(["--corpus", str(source), "--comments-jsonl", str(journal), "--output", str(output)])
    assert rc == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["current_body_claim_count"] == 1
    assert data["canonical_write_performed"] is False
