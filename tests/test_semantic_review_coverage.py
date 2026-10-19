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
        "archive_directory_observed_count": 1,
        "rows": [
            {"id": "r1", "path": "docs/r1.md", "status": "reviewing", "lane": "P2-candidate-review",
             "body": {"status": "read", "sha256": SHA_A}, "signals": []},
            {"id": "a1", "path": "docs/a1.md", "status": "active", "lane": "P1-current-validity",
             "body": {"status": "read", "sha256": SHA_B}, "signals": []},
            {"id": "archive-dir", "path": "archive/", "status": "archived", "lane": "P3-historical-integrity",
             "body": {"status": "archive-directory-observed", "sha256": "",
                      "directory_identity_observed": True}, "signals": []},
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
    assert report["pending_body_claim_count"] == 1
    assert report["archive_directory_structural_count"] == 1
    assert report["reviewable_blob_count"] == 2
    assert report["body_unavailable_count"] == 0
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


def test_tracked_text_inventory_is_aggregate_and_directory_is_not_a_document():
    report = build_coverage(corpus(), [comment("r1"), comment("a1", SHA_B)], owner="jiying2007", tracked_paths=[
        "docs/r1.md", "docs/a1.md", "archive/history.md", "docs/other.txt",
        "personal/secret.md", "scripts/build.py", "README.md",
    ])
    assert report["registered_text_claims_complete"] is True
    assert report["status"] == "registered-text-claims-complete-scope-incomplete"
    assert report["pending_body_claim_count"] == 0
    inv = report["unregistered_tracked_text_inventory"]
    assert inv["tracked_text_count"] == 5
    assert inv["unregistered_total"] == 3
    assert inv["under_archive_directory_count"] == 1
    assert inv["unregistered_elsewhere_count"] == 2
    assert inv["private_path_candidates_skipped"] == 1
    assert "secret.md" not in json.dumps(report)
    assert "history.md" not in json.dumps(report)


def test_invalid_archive_status_and_inventory_fail_closed():
    data = corpus()
    data["rows"][2]["body"]["directory_identity_observed"] = False
    with pytest.raises(ValueError, match="unverified archive"):
        build_coverage(data, [], owner="jiying2007")
    data = corpus()
    with pytest.raises(ValueError, match="duplicate tracked path"):
        build_coverage(data, [], owner="jiying2007", tracked_paths=["docs/a.md", "docs/a.md"])
