"""Full-corpus audit is reproducible and never grants content approval."""
import datetime as dt
import hashlib
import json
import pathlib

from tools.codex_assets.knowledge_hub.common import render_markdown, registry_items
from tools.codex_assets.knowledge_hub.corpus_review import build_corpus_review
from tools.codex_assets.knowledge_hub.corpus_review_cli import main as review_cli


def _fixture(tmp_path):
    root = tmp_path / "hub"
    (root / "registry").mkdir(parents=True)
    (root / "registry/review-risk-policy.json").write_text(json.dumps({
        "default_class": "ordinary",
        "classes": {"ordinary": {"ai_first_action": "auto-triage"}},
        "rules": [],
    }), encoding="utf-8")
    paths = [
        ("active-a", "active", "projects/demo/current/a.md", "工程经验", "2026-09-01"),
        ("review-a", "reviewing", "projects/demo/validation/a.md", "重复标题", "2026-12-01"),
        ("review-b", "reviewing", "projects/demo/validation/b.md", "重复标题", "2026-12-01"),
        ("arch-a", "archived", "projects/demo/archive/a.md", "历史排障", "2026-01-01"),
        ("personal-a", "personal", "notes/personal/alice/a.md", "私人笔记", "2026-10-01"),
    ]
    entries = []
    for item_id, status, relative, title, due in paths:
        row = {
            "id": item_id, "title": title, "kind": "debug-record",
            "status": status, "domain": "projects/demo" if status != "personal" else "notes",
            "path": relative, "owner": "team-core", "review_after": due,
            "visibility": "personal-local" if status == "personal" else "team-internal",
            "tags": ["engineering"], "summary_zh": title + "的证据摘要",
            "evidence_refs": [relative], "validation_refs": [relative],
        }
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_markdown(row, "# 正文\n\n证据内容。\n"), encoding="utf-8")
        entries.append(row)
    (root / "registry/items.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in entries) + "\n",
        encoding="utf-8",
    )
    return root


def test_full_registry_coverage_without_lifecycle_mutation(tmp_path):
    root = _fixture(tmp_path)
    before = (root / "registry/items.jsonl").read_bytes()
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    assert report["item_count"] == report["accounted_for_count"] == 5
    assert report["private_excluded_count"] == 1
    assert report["machine_attempted_count"] == 4
    assert report["machine_checked_count"] == 4
    assert report["machine_failed_count"] == 0
    assert report["status_counts"]["active"] == 1
    assert report["signal_counts"]["active-review-overdue"] == 1
    assert report["signal_counts"]["historical-review-overdue"] == 1
    assert report["duplicates"]["same_domain_title"] == [["review-a", "review-b"]]
    assert report["semantic_review_performed"] is False
    assert report["canonical_write_performed"] is False
    assert report["owner_approval_performed"] is False
    assert before == (root / "registry/items.jsonl").read_bytes()
    assert "私人笔记" not in json.dumps(report, ensure_ascii=False)
    assert "personal-a" not in json.dumps(report, ensure_ascii=False)
    assert report["report_sha256"] == build_corpus_review(root, dt.date(2026, 10, 17))["report_sha256"]


def test_corrupted_body_reports_attention_without_auto_accept(tmp_path):
    root = _fixture(tmp_path)
    file = root / "projects/demo/validation/a.md"
    file.write_text("# 没有 Frontmatter\n\n内容。\n", encoding="utf-8")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in report["rows"] if x["id"] == "review-a")
    assert "frontmatter-drift" in row["signals"]
    assert row["lane"] == "P0-integrity"
    assert row["semantic_review_performed"] is False
    assert row["review_proof"]["ai_closed"] == "not-verified"


def test_unreadable_body_is_counted_as_attempted_not_verified(tmp_path):
    root = _fixture(tmp_path)
    (root / "projects/demo/validation/a.md").unlink()
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    assert report["item_count"] == report["accounted_for_count"] == 5
    assert report["private_excluded_count"] == 1
    assert report["machine_attempted_count"] == 4
    assert report["machine_checked_count"] == 3
    assert report["machine_failed_count"] == 1
    assert report["machine_attempted_count"] == (
        report["machine_checked_count"] + report["machine_failed_count"]
    )
    broken = next(row for row in report["rows"] if row["id"] == "review-a")
    assert broken["machine_checked"] is False
    assert broken["lane"] == "P0-integrity"
    assert "body-unavailable-or-invalid" in broken["signals"]
    assert report["semantic_review_performed"] is False


def _add_archive_directory(root):
    relative = "projects/demo/archive/corpus"
    path = root / relative
    path.mkdir(parents=True)
    (path / "retained.md").write_text("# historical file\n", encoding="utf-8")
    entry = {
        "id": "archive-directory", "path": relative, "kind": "project-archive",
        "domain": "projects/demo", "owner": "team-core",
        "status": "archived", "visibility": "team-internal",
        "source": {"type": "retired-source-provenance", "source_id": "old"},
        "promotion": "none", "review_status": "archive-corpus-materialized",
        "tags": ["historical-corpus", "archive-only"],
        "review_after": "2026-09-01", "validation_refs": [relative],
    }
    with (root / "registry/items.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def test_archive_directory_is_structural_identity_not_body_review(tmp_path):
    root = _fixture(tmp_path)
    target = _add_archive_directory(root)
    before = (root / "registry/items.jsonl").read_bytes()
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    assert report["item_count"] == 6
    assert report["private_excluded_count"] == 1
    assert report["machine_attempted_count"] == 5
    assert report["machine_checked_count"] == 4
    assert report["archive_directory_observed_count"] == 1
    assert report["machine_failed_count"] == 0
    row = next(x for x in report["rows"] if x["id"] == "archive-directory")
    assert row["archive_directory_observed"] is True
    assert row["machine_checked"] is False
    assert row["body"]["status"] == "archive-directory-observed"
    assert row["body"]["contents_verified"] is False
    assert row["body"]["frontmatter_matches_registry"] is None
    assert row["references"]["missing"] == 0
    assert "archive-directory-identity-only" in row["signals"]
    assert "historical-review-overdue" in row["signals"]
    assert "body-unavailable-or-invalid" not in row["signals"]
    assert row["lane"] == "P3-historical-integrity"
    assert (root / "registry/items.jsonl").read_bytes() == before
    (target / "retained.md").unlink()
    target.rmdir()
    broken = build_corpus_review(root, dt.date(2026, 10, 17))
    assert broken["archive_directory_observed_count"] == 0
    assert broken["machine_failed_count"] == 1
    missing = next(x for x in broken["rows"] if x["id"] == "archive-directory")
    assert missing["lane"] == "P0-integrity"
    assert "body-unavailable-or-invalid" in missing["signals"]
    target.symlink_to(root / "notes/personal", target_is_directory=True)
    linked = build_corpus_review(root, dt.date(2026, 10, 17))
    assert linked["archive_directory_observed_count"] == 0
    assert linked["machine_failed_count"] == 1
    assert next(x for x in linked["rows"] if x["id"] == "archive-directory")["lane"] == "P0-integrity"


def test_archive_directory_must_be_nonempty_and_explicitly_archived(tmp_path):
    root = _fixture(tmp_path)
    target = _add_archive_directory(root)
    (target / "retained.md").unlink()
    empty = build_corpus_review(root, dt.date(2026, 10, 17))
    assert empty["archive_directory_observed_count"] == 0
    assert empty["machine_failed_count"] == 1
    (target / "retained.md").write_text("historical", encoding="utf-8")
    registry_path = root / "registry/items.jsonl"
    lines = registry_path.read_text(encoding="utf-8").splitlines()
    archive = json.loads(lines[-1])
    archive["status"] = "active"
    lines[-1] = json.dumps(archive, ensure_ascii=False)
    registry_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    invalid = build_corpus_review(root, dt.date(2026, 10, 17))
    assert invalid["archive_directory_observed_count"] == 0
    assert invalid["machine_failed_count"] == 1
    assert next(x for x in invalid["rows"] if x["id"] == "archive-directory")["lane"] == "P0-integrity"


def test_report_uses_ignored_location_only(tmp_path):
    root = _fixture(tmp_path)
    assert review_cli(["--root", str(root), "--as-of", "2026-10-17",
                       "--output", ".tmp/knowledge-hub/review.json"]) == 0
    result = root / ".tmp/knowledge-hub/review.json"
    payload = json.loads(result.read_text(encoding="utf-8"))
    assert payload["item_count"] == 5
    assert len(payload["report_sha256"]) == 64
    assert review_cli(["--root", str(root), "--as-of", "2026-10-17",
                       "--output", "../../outside.json"]) == 1


def test_real_repository_full_coverage():
    root = pathlib.Path(__file__).resolve().parents[1]
    as_of = dt.date(2026, 10, 17)
    old_hash = hashlib.sha256((root / "registry/items.jsonl").read_bytes()).hexdigest()
    report = build_corpus_review(root, as_of)
    assert report["item_count"] == len(registry_items(root))
    assert report["item_count"] >= 700
    assert report["accounted_for_count"] == report["item_count"]
    assert report["private_excluded_count"] >= 1
    # A real repository may contain unreadable or historical bodies. Preserve
    # findings as P0 rather than silently counting failures as scanned PASS.
    assert report["machine_attempted_count"] == report["accounted_for_count"] - report["private_excluded_count"]
    assert report["machine_attempted_count"] == (
        report["machine_checked_count"]
        + report["archive_directory_observed_count"]
        + report["machine_failed_count"]
    )
    directories = [row for row in report["rows"] if row.get("archive_directory_observed")]
    assert report["archive_directory_observed_count"] == len(directories)
    assert all(row["status"] == "archived" for row in directories)
    assert all(row["body"]["contents_verified"] is False for row in directories)
    failures = [
        row for row in report["rows"]
        if row["lane"] != "personal-excluded"
        and not row["machine_checked"]
        and not row.get("archive_directory_observed")
    ]
    assert len(failures) == report["machine_failed_count"]
    assert all(row["lane"] == "P0-integrity" for row in failures)
    assert all("body-unavailable-or-invalid" in row["signals"] for row in failures)
    assert report["status_counts"]["reviewing"] >= 300
    assert len(report["rows"]) == report["item_count"]
    assert hashlib.sha256((root / "registry/items.jsonl").read_bytes()).hexdigest() == old_hash
    assert report["active_promoted"] is False
    assert report["canonical_write_performed"] is False


def _install_unverified_ai_history(root):
    """Create an authentic-shape fixture, not a human approval."""
    from tools.codex_assets.knowledge_hub.delegated_content_review import (
        FIELD, SCHEMA, content_digest, expected_record, item_digest,
    )

    registry = root / "registry/items.jsonl"
    items = [json.loads(line) for line in registry.read_text(encoding="utf-8").splitlines()]
    item = next(row for row in items if row["id"] == "review-a")
    item["generated_by_ai"] = True
    entry = {
        "id": item["id"], "path": item["path"], "owner": item["owner"],
        "item_sha256": item_digest(item),
        "content_sha256": content_digest(root, item["path"]),
        "decision": "accept-as-review-record",
        "basis": "Fixture only; this is not independent human or product review.",
    }
    auth = {
        "schema_version": SCHEMA, "authorization_id": "historical-review-test",
        "authorized_by": "team-core", "authorized_at": "2026-10-10",
        "thread_id": "00000000-0000-0000-0000-000000000001",
        "authorization_statement": "historical fixture",
        "authorization_evidence_sha256": "a" * 64,
        "executor": "Codex", "scope": "ordinary-reviewing-content-only",
        "independent_review_sha256": "b" * 64,
        "entries": [entry],
        "request_proof": {
            "state": "unverified", "request_sha256": None,
            "intake_attestation_sha256": None, "actor_identity_verified": False,
        },
    }
    item[FIELD] = expected_record(auth, entry)
    registry.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in items),
        encoding="utf-8",
    )
    (root / "registry/owners.json").write_text(
        json.dumps({"owners": [{"id": "team-core"}]}), encoding="utf-8",
    )
    (root / "registry/ai-content-review-authorizations.jsonl").write_text(
        json.dumps(auth, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    return item


def test_historical_ai_review_snapshot_drift_is_independently_visible(tmp_path):
    root = _fixture(tmp_path)
    target = _install_unverified_ai_history(root)
    body_path = root / target["path"]
    original = body_path.read_bytes()
    registry_path = root / "registry/items.jsonl"
    original_registry = registry_path.read_bytes()

    baseline = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in baseline["rows"] if x["id"] == "review-a")
    snapshot = row["review_proof"]["ai_snapshot"]
    assert snapshot["state"] == "request-unverified"
    assert snapshot["item_sha256_match"] is True
    assert snapshot["content_sha256_match"] is True
    assert snapshot["request_proof"] == "unverified"
    assert "ai-review-request-proof-unverified" in row["signals"]
    assert row["review_proof"]["ai_closed"] == "not-verified"
    assert baseline["canonical_write_performed"] is False

    body_path.write_bytes(original + b"\nbody changed after historical review\n")
    changed_body = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in changed_body["rows"] if x["id"] == "review-a")
    assert row["review_proof"]["ai_snapshot"]["content_sha256_match"] is False
    assert row["review_proof"]["ai_snapshot"]["item_sha256_match"] is True
    assert "ai-review-content-drift" in row["signals"]
    assert row["review_proof"]["ai_closed"] == "not-verified"

    body_path.write_bytes(original)
    items = [json.loads(line) for line in original_registry.decode("utf-8").splitlines()]
    next(row for row in items if row["id"] == "review-a")["updated_at"] = "2026-10-17"
    registry_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in items),
        encoding="utf-8",
    )
    changed_item = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in changed_item["rows"] if x["id"] == "review-a")
    assert row["review_proof"]["ai_snapshot"]["item_sha256_match"] is False
    assert row["review_proof"]["ai_snapshot"]["content_sha256_match"] is True
    assert "ai-review-item-identity-drift" in row["signals"]
    assert row["review_proof"]["ai_closed"] == "not-verified"


def test_ai_review_summary_is_hash_bound_report_only(tmp_path):
    from tools.codex_assets.knowledge_hub.corpus_review_cli import _summary

    root = _fixture(tmp_path)
    item = _install_unverified_ai_history(root)
    as_of = dt.date(2026, 10, 17)
    first = build_corpus_review(root, as_of)
    historical = first["ai_review_audit"]
    assert historical["historical_record_count"] == 1
    assert historical["request_unverified_count"] == 1
    assert historical["exact_snapshot_count"] == 1
    assert historical["item_identity_drift_count"] == 0
    assert historical["body_content_drift_count"] == 0
    assert historical["state_counts"] == {"request-unverified": 1}
    assert historical["historical_proof_promoted"] is False
    assert historical["semantic_approval_performed"] is False
    assert _summary(first)["ai_review_audit"] == historical

    document = root / item["path"]
    document.write_bytes(document.read_bytes() + b"\ndrift\n")
    drifted = build_corpus_review(root, as_of)["ai_review_audit"]
    assert drifted["historical_record_count"] == 1
    assert drifted["request_unverified_count"] == 1
    assert drifted["exact_snapshot_count"] == 0
    assert drifted["body_content_drift_count"] == 1
    assert drifted["item_identity_drift_count"] == 0
    assert drifted["state_counts"] == {"snapshot-drift": 1}
    assert drifted["semantic_approval_performed"] is False


