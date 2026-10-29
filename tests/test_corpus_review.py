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




def test_full_corpus_optimization_covers_every_item_without_promotion(tmp_path):
    root = _fixture(tmp_path)
    before = (root / "registry/items.jsonl").read_bytes()
    result = build_corpus_review(root, dt.date(2026, 10, 17))
    plan = result["optimization_queue"]
    summary = result["optimization_summary"]
    assert plan["projection"] == "knowledge-hub.corpus-optimization/v1"
    assert plan["item_count"] == plan["accounted_for_count"] == 5
    assert plan["visible_count"] == 4
    assert plan["private_excluded_count"] == 1
    assert plan["coverage_complete"] is True
    assert plan["action_count"] + plan["no_change_count"] == 4
    assert plan["automatic_content_edits_enabled"] is False
    assert plan["canonical_write_performed"] is False
    assert plan["semantic_review_performed"] is False
    assert plan["owner_approval_performed"] is False
    assert all(row["proposal_only"] and not row["content_change_approved"]
               for row in plan["actions"])
    assert all(not row["item_id"].startswith("redacted-sha256:")
               for row in plan["actions"])
    assert "personal-a" not in json.dumps(plan)
    assert "notes/personal/alice" not in json.dumps(plan)
    by_id = {row["item_id"]: row for row in plan["actions"]}
    assert by_id["active-a"]["action"] == "machine-prepare-current-review"
    assert by_id["active-a"]["next_boundary"] == "owner-semantic-review"
    assert by_id["review-a"]["duplicate_candidate"] is True
    assert by_id["review-b"]["duplicate_candidate"] is True
    assert plan["duplicate_auto_merge_enabled"] is False
    assert "actions" not in summary
    assert summary["fingerprint"] == plan["fingerprint"]
    assert (root / "registry/items.jsonl").read_bytes() == before
    assert build_corpus_review(root, dt.date(2026, 10, 17))["optimization_queue"] == plan


def test_corpus_optimization_integrity_drift_has_machine_only_repair_proposal(tmp_path):
    root = _fixture(tmp_path)
    path = root / "projects/demo/validation/a.md"
    path.write_text("# missing frontmatter\\n", encoding="utf-8")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    actions = {row["item_id"]: row for row in report["optimization_queue"]["actions"]}
    assert actions["review-a"]["priority"] == "P0"
    assert actions["review-a"]["action"] == "machine-diagnose-integrity"
    assert actions["review-a"]["next_boundary"] == "governed-repair-review"
    assert actions["review-a"]["content_change_approved"] is False


def test_corpus_optimization_fails_closed_on_partial_report_or_private_leak(tmp_path):
    import copy
    import pytest
    from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
    from tools.codex_assets.knowledge_hub.corpus_optimization import build_corpus_optimization

    root = _fixture(tmp_path)
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    missing = copy.deepcopy(report)
    missing["rows"].pop()
    with pytest.raises(KnowledgeHubError, match="complete"):
        build_corpus_optimization(missing)
    leaked = copy.deepcopy(report)
    leaked["duplicates"]["same_domain_title"].append(["personal-a", "review-a"])
    with pytest.raises(KnowledgeHubError, match="duplicate"):
        build_corpus_optimization(leaked)
    unknown = copy.deepcopy(report)
    for row in unknown["rows"]:
        if row.get("id") == "review-a":
            row["signals"] = ["unregistered-contract-signal"]
            break
    actions = build_corpus_optimization(unknown)["actions"]
    action = next(row for row in actions if row["item_id"] == "review-a")
    assert action["action"] == "human-governance-review"
    assert action["priority"] == "P0"


def test_real_corpus_fixture_routes_declared_supersession_as_candidate_only(tmp_path):
    # Reuse existing bounded fixture: do not invent a second registry.
    from tools.codex_assets.knowledge_hub.corpus_review import build_corpus_review

    root = _fixture(tmp_path)
    older = root / "projects/demo/validation/a.md"
    newer = root / "projects/demo/validation/b.md"
    original_registry = (root / "registry/items.jsonl").read_bytes()
    text = newer.read_text(encoding="utf-8")
    assert text.startswith("---")
    newer.write_text(
        text.replace("---\n", "---\nsupersedes_candidate: review-a\n", 1),
        encoding="utf-8",
    )
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    by_id = {x["id"]: x for x in report["rows"] if x.get("id")}
    assert "superseded-candidate-provenance" in by_id["review-a"]["signals"]
    assert report["supersession_audit"]["candidate_history_count"] == 1
    queue = {x["item_id"]: x for x in report["optimization_queue"]["actions"]}
    assert queue["review-a"]["action"] == "machine-compare-supersession-lineage"
    assert queue["review-a"]["next_boundary"] == "owner-supersession-review"
    assert queue["review-a"]["content_change_approved"] is False
    assert older.read_bytes() and (root / "registry/items.jsonl").read_bytes() == original_registry


def test_invalid_untrusted_declared_identity_is_not_exported(tmp_path):
    from tools.codex_assets.knowledge_hub.corpus_review import build_corpus_review

    root = _fixture(tmp_path)
    path = root / "projects/demo/validation/b.md"
    original = path.read_text(encoding="utf-8")
    path.write_text(
        original.replace("---\n", "---\nsupersedes_candidate: ../private\n", 1),
        encoding="utf-8",
    )
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    assert report["supersession_audit"]["blocking_signal_counts"] == {
        "supersession-declaration-invalid": 1
    }
    assert "../private" not in str(report)


def test_archived_plaintext_is_unbound_provenance_not_a_current_mirror(tmp_path):
    root = _fixture(tmp_path)
    path = root / "projects/demo/archive/a.md"
    registry = (root / "registry/items.jsonl").read_bytes()
    path.write_text("# Original historical evidence\n\nDo not synthesize YAML.\n",
                    encoding="utf-8")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in report["rows"] if x.get("id") == "arch-a")
    assert row["body"]["historical_plaintext_archive"] is True
    assert row["body"]["frontmatter_matches_registry"] is False
    assert "archive-plaintext-provenance-only" in row["signals"]
    assert "frontmatter-drift" not in row["signals"]
    assert row["lane"] == "P3-historical-integrity"
    action = next(x for x in report["optimization_queue"]["actions"]
                  if x["item_id"] == "arch-a")
    assert action["action"] == "machine-audit-archive-provenance"
    assert action["priority"] == "P3"
    assert action["content_change_approved"] is False
    assert report["canonical_write_performed"] is False
    assert report["semantic_review_performed"] is False
    assert (root / "registry/items.jsonl").read_bytes() == registry


def test_archived_declared_metadata_conflict_remains_integrity_p0(tmp_path):
    root = _fixture(tmp_path)
    archive = root / "projects/demo/archive/a.md"
    body = archive.read_text(encoding="utf-8")
    assert "status: archived" in body
    archive.write_text(body.replace("status: archived", "status: active", 1),
                       encoding="utf-8")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in report["rows"] if x.get("id") == "arch-a")
    assert row["body"]["historical_plaintext_archive"] is False
    assert "frontmatter-drift" in row["signals"]
    assert row["lane"] == "P0-integrity"


def test_partial_archive_metadata_and_current_plaintext_remain_p0(tmp_path):
    root = _fixture(tmp_path)
    archived = root / "projects/demo/archive/a.md"
    archived.write_text("---\nid: arch-a\n---\n\nIncomplete metadata\n",
                        encoding="utf-8")
    current = root / "projects/demo/current/a.md"
    current.write_text("# Current content without metadata\n", encoding="utf-8")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    for item_id in ("arch-a", "active-a"):
        row = next(x for x in report["rows"] if x.get("id") == item_id)
        assert row["body"]["historical_plaintext_archive"] is False
        assert "frontmatter-drift" in row["signals"]
        assert row["lane"] == "P0-integrity"


def test_non_markdown_historical_script_is_not_exempted(tmp_path):
    root = _fixture(tmp_path)
    script = root / "tools/history.sh"
    script.parent.mkdir(parents=True)
    script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    registry = root / "registry/items.jsonl"
    with registry.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "id": "legacy-script", "path": "tools/history.sh",
            "status": "archived", "owner": "team-core", "kind": "audit",
            "domain": "tools", "review_after": "2026-09-01"
        }) + "\n")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in report["rows"] if x.get("id") == "legacy-script")
    assert row["body"]["historical_plaintext_archive"] is False
    assert "frontmatter-drift" in row["signals"]
    assert row["lane"] == "P0-integrity"


def test_archived_yaml_markers_with_crlf_or_bom_remain_p0(tmp_path):
    root = _fixture(tmp_path)
    archive = root / "projects/demo/archive/a.md"
    samples = (
        "---\r\nid: arch-a\r\nstatus: active\r\n---\r\nbody\r\n",
        "\ufeff---\nid: arch-a\nstatus: active\n---\nbody\n",
        "--- ambiguous historical separator\nbody\n",
    )
    for body in samples:
        archive.write_text(body, encoding="utf-8")
        report = build_corpus_review(root, dt.date(2026, 10, 17))
        row = next(r for r in report["rows"] if r.get("id") == "arch-a")
        assert row["body"]["status"] == "read"
        assert row["body"]["historical_plaintext_archive"] is False
        assert "frontmatter-drift" in row["signals"]
        assert row["lane"] == "P0-integrity"
        action = next(r for r in report["optimization_queue"]["actions"]
                      if r["item_id"] == "arch-a")
        assert action["priority"] == "P0"
        assert action["content_change_approved"] is False


def test_known_raw_templates_are_p0_when_registered_as_reviewing_content(tmp_path):
    """Trust the canonical body template, not a factual-looking Registry title."""
    from tools.codex_assets.knowledge_hub.common import split_frontmatter
    from tools.codex_assets.knowledge_hub.template_integrity import UNFILLED_TEMPLATE_BODY_SHA256

    repo = pathlib.Path(__file__).resolve().parents[1]
    variants = (
        ("debug-record", "templates/debug-record.md"),
        ("validation", "templates/validation-report.md"),
        ("decision", "templates/decision.md"),
    )
    for kind, template_path in variants:
        root = _fixture(tmp_path / kind)
        registry = root / "registry/items.jsonl"
        items = [json.loads(s) for s in registry.read_text(encoding="utf-8").splitlines()]
        entry = next(row for row in items if row["id"] == "review-a")
        entry["kind"] = kind
        registry.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in items),
            encoding="utf-8",
        )
        _, template_body = split_frontmatter(
            (repo / template_path).read_text(encoding="utf-8")
        )
        assert hashlib.sha256(template_body.strip().encode("utf-8")).hexdigest() == (
            UNFILLED_TEMPLATE_BODY_SHA256[kind]
        )
        page = root / entry["path"]
        original_meta, _ = split_frontmatter(page.read_text(encoding="utf-8"))
        original_meta["kind"] = kind
        page.write_text(render_markdown(original_meta, template_body),
                        encoding="utf-8")
        report = build_corpus_review(root, dt.date(2026, 10, 17))
        row = next(x for x in report["rows"] if x.get("id") == "review-a")
        assert row["body"]["frontmatter_matches_registry"] is True
        assert row["body"]["body_sha256"] == UNFILLED_TEMPLATE_BODY_SHA256[kind]
        assert "registered-unfilled-template" in row["signals"]
        assert row["lane"] == "P0-integrity"
        action = next(x for x in report["optimization_queue"]["actions"]
                      if x["item_id"] == "review-a")
        assert action["priority"] == "P0"
        assert action["action"] == "machine-diagnose-integrity"
        assert action["content_change_approved"] is False
        assert report["semantic_review_performed"] is False
        assert report["canonical_write_performed"] is False

        # A substantive edit is NOT exactly an unfilled canonical template.
        page.write_text(page.read_text(encoding="utf-8") +
                        "\n## Verified observation\nActual cited source differs.\n",
                        encoding="utf-8")
        changed = build_corpus_review(root, dt.date(2026, 10, 17))
        row = next(x for x in changed["rows"] if x.get("id") == "review-a")
        assert "registered-unfilled-template" not in row["signals"]
        assert row["lane"] != "P0-integrity"


def test_historical_archived_template_not_misclassified_as_current_p0(tmp_path):
    from tools.codex_assets.knowledge_hub.common import split_frontmatter

    root = _fixture(tmp_path)
    repo = pathlib.Path(__file__).resolve().parents[1]
    _, template = split_frontmatter((repo / "templates/debug-record.md").read_text(
        encoding="utf-8"
    ))
    page = root / "projects/demo/archive/a.md"
    metadata, _ = split_frontmatter(page.read_text(encoding="utf-8"))
    page.write_text(render_markdown(metadata, template), encoding="utf-8")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in report["rows"] if x.get("id") == "arch-a")
    assert "registered-unfilled-template" not in row["signals"]
    assert row["lane"] == "P3-historical-integrity"


def test_unfilled_template_requires_matching_kind_and_current_lifecycle(tmp_path):
    from tools.codex_assets.knowledge_hub.common import split_frontmatter

    root = _fixture(tmp_path)
    repo = pathlib.Path(__file__).resolve().parents[1]
    _, canonical_body = split_frontmatter(
        (repo / "templates/debug-record.md").read_text(encoding="utf-8")
    )
    registry = root / "registry/items.jsonl"
    rows = [json.loads(line) for line in registry.read_text(encoding="utf-8").splitlines()]
    item = next(row for row in rows if row["id"] == "review-a")
    page = root / item["path"]
    original_meta, _ = split_frontmatter(page.read_text(encoding="utf-8"))

    variants = (
        ("validation", "reviewing", False),  # Wrong template kind
        ("debug-record", "draft", False),    # Unapproved authoring template
        ("debug-record", "archived", False), # Retired source retained
        ("debug-record", "active", True),    # Current published template is P0
    )
    for kind, status, should_alert in variants:
        item["kind"], item["status"] = kind, status
        registry.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
        metadata = dict(original_meta, kind=kind, status=status)
        page.write_text(render_markdown(metadata, canonical_body), encoding="utf-8")
        report = build_corpus_review(root, dt.date(2026, 10, 17))
        row = next(entry for entry in report["rows"] if entry.get("id") == "review-a")
        assert row["body"]["frontmatter_matches_registry"] is True
        has_signal = "registered-unfilled-template" in row["signals"]
        assert has_signal is should_alert
        assert (row["lane"] == "P0-integrity") is should_alert
        assert report["semantic_review_performed"] is False
        assert report["canonical_write_performed"] is False

def _rewrite_test_frontmatter_field(path, key, value=None):
    """Modify only one explicit YAML mirror in a temporary test fixture."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    assert lines[0].strip() == "---"
    end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    positions = [i for i, line in enumerate(lines[1:end], 1)
                 if line.startswith(key + ":")]
    assert len(positions) == 1
    i = positions[0]
    if value is None:
        lines.pop(i)
    else:
        lines[i] = "{}: {}\n".format(key, value)
    path.write_text("".join(lines), encoding="utf-8")


def test_archived_legacy_path_omission_is_not_false_p0(tmp_path):
    root = _fixture(tmp_path)
    file = root / "projects/demo/archive/a.md"
    _rewrite_test_frontmatter_field(file, "path")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in report["rows"] if x["id"] == "arch-a")
    assert row["body"]["frontmatter_matches_registry"] is True
    assert "frontmatter-drift" not in row["signals"]
    assert row["lane"] == "P3-historical-integrity"
    assert report["canonical_write_performed"] is False
    assert report["semantic_review_performed"] is False


def test_archived_explicit_wrong_path_remains_p0(tmp_path):
    root = _fixture(tmp_path)
    file = root / "projects/demo/archive/a.md"
    _rewrite_test_frontmatter_field(file, "path", "projects/demo/archive/wrong.md")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in report["rows"] if x["id"] == "arch-a")
    assert row["body"]["frontmatter_matches_registry"] is False
    assert "frontmatter-drift" in row["signals"]
    assert row["lane"] == "P0-integrity"


def test_archived_path_omission_cannot_hide_other_missing_identity(tmp_path):
    root = _fixture(tmp_path)
    file = root / "projects/demo/archive/a.md"
    _rewrite_test_frontmatter_field(file, "path")
    _rewrite_test_frontmatter_field(file, "kind")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in report["rows"] if x["id"] == "arch-a")
    assert row["body"]["frontmatter_matches_registry"] is False
    assert "frontmatter-drift" in row["signals"]
    assert row["lane"] == "P0-integrity"


def test_current_and_reviewing_path_omission_still_block(tmp_path):
    root = _fixture(tmp_path)
    for _item_id, relative in (
        ("active-a", "projects/demo/current/a.md"),
        ("review-a", "projects/demo/validation/a.md"),
    ):
        _rewrite_test_frontmatter_field(root / relative, "path")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    for item_id in ("active-a", "review-a"):
        row = next(x for x in report["rows"] if x["id"] == item_id)
        assert row["body"]["frontmatter_matches_registry"] is False
        assert "frontmatter-drift" in row["signals"]
        assert row["lane"] == "P0-integrity"


def test_archived_path_omission_does_not_hide_status_mismatch(tmp_path):
    root = _fixture(tmp_path)
    file = root / "projects/demo/archive/a.md"
    _rewrite_test_frontmatter_field(file, "path")
    _rewrite_test_frontmatter_field(file, "status", "active")
    report = build_corpus_review(root, dt.date(2026, 10, 17))
    row = next(x for x in report["rows"] if x["id"] == "arch-a")
    assert row["body"]["frontmatter_matches_registry"] is False
    assert "frontmatter-drift" in row["signals"]
    assert row["lane"] == "P0-integrity"

def test_real_archived_path_omissions_and_reviewing_drift_stay_separate():
    from tools.codex_assets.knowledge_hub import corpus_review

    root = pathlib.Path(__file__).resolve().parents[1]
    items = {row["id"]: row for row in registry_items(root)}
    archived_path_only = (
        "codex-archive-phased-migration-removal-20260709",
        "codex-archive-migration-preflight-20260709",
        "codex-archive-removal-preflight-20260710",
        "codex-archive-extract-first-preflight-20260710",
        "codex-openai-local-runtime-boundary-20260524",
        "codex-token-efficiency-roadmap-coverage-20260710",
        "codex-archive-memory-curation-file-level-audit-20260710",
        "codex-adk-hardcut-source-to-live-audit-20260710",
        "codex-knowledge-hub-final-hardcut-tombstone-audit-20260710",
    )
    for item_id in archived_path_only:
        item = items[item_id]
        assert item["status"] == "archived"
        result = corpus_review._document(root, item)
        assert result["status"] == "read"
        assert result["frontmatter_matches_registry"] is True

    for item_id in (
        "pcr02-evt2-hardware-pdf-reference-index-20260711",
        "pcr02-evt2-mcu-soc-contract-index-20260711",
        "pcr02-owner-ready-validation-paths-20260713",
    ):
        item = items[item_id]
        assert item["status"] == "reviewing"
        result = corpus_review._document(root, item)
        assert result["status"] == "read"
        assert result["frontmatter_matches_registry"] is False

def test_shell_command_reference_checks_script_but_does_not_run(tmp_path):
    from tools.codex_assets.knowledge_hub import corpus_review

    root = _fixture(tmp_path)
    tool = root / "tools/check-ref.sh"
    tool.parent.mkdir(parents=True, exist_ok=True)
    tool.write_text("#!/bin/sh\ntouch {} \n".format(root / "executed.txt"),
                    encoding="utf-8")
    item = {"evidence_refs": [], "validation_refs": [
        "tools/check-ref.sh --dry-run --json"
    ]}
    result = corpus_review._local_refs(root, item)
    assert result == {"status": "checked", "missing": 0, "checked": 1}
    assert not (root / "executed.txt").exists()

    tool.unlink()
    missing = corpus_review._local_refs(root, item)
    assert missing == {"status": "checked", "missing": 1, "checked": 1}
    assert not (root / "executed.txt").exists()


def test_script_command_normalization_does_not_hide_ordinary_path_misses(tmp_path):
    from tools.codex_assets.knowledge_hub import corpus_review

    root = _fixture(tmp_path)
    path = root / "tools/report with spaces.sh"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("historical fixture", encoding="utf-8")
    item = {"validation_refs": [
        "tools/report with spaces.sh",
        "tools/missing.sh",
        "projects/demo/validation/missing.md",
    ]}
    assert corpus_review._local_refs(root, item) == {
        "status": "checked", "missing": 2, "checked": 3,
    }


def test_registered_schema_command_ref_is_structurally_present_not_executed():
    from tools.codex_assets.knowledge_hub import corpus_review

    root = pathlib.Path(__file__).resolve().parents[1]
    item = next(x for x in registry_items(root)
                if x["id"] == "knowledge-hub-registry-schema-readability-extension")
    result = corpus_review._local_refs(root, item)
    assert result["status"] == "checked"
    assert result["checked"] >= 3
    assert result["missing"] == 0
