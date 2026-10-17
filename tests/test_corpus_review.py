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
    assert report["machine_checked_count"] == 4
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
    assert report["machine_checked_count"] == report["accounted_for_count"] - report["private_excluded_count"]
    assert report["status_counts"]["reviewing"] >= 300
    assert len(report["rows"]) == report["item_count"]
    assert hashlib.sha256((root / "registry/items.jsonl").read_bytes()).hexdigest() == old_hash
    assert report["active_promoted"] is False
    assert report["canonical_write_performed"] is False
