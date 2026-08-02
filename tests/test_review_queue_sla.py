from __future__ import annotations

import json
import pathlib
import subprocess


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "tools/codex_assets/knowledge_hub/index_plan_cli.py"


def test_review_queue_packet_reports_sla_and_bounded_batch(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir()
    rows = []
    for item_id, review_after, domain in (
        ("overdue", "2026-07-01", "projects/a"),
        ("soon", "2026-08-05", "projects/a"),
        ("missing", "", "projects/b"),
    ):
        target = tmp_path / "projects" / item_id / "note.md"
        target.parent.mkdir(parents=True)
        target.write_text("# evidence\n")
        rows.append(
            {
                "id": item_id,
                "title": item_id,
                "kind": "validation",
                "domain": domain,
                "path": str(target.relative_to(tmp_path)),
                "status": "reviewing",
                "owner": "owner-a",
                "review_after": review_after,
                "generated_by_ai": True,
                "human_reviewed_by": "",
                "human_reviewed_at": "",
                "review_basis": "",
                "source": {"type": "manual"},
            }
        )
    (registry / "items.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    (registry / "sources.json").write_text('{"sources": []}\n')

    result = subprocess.run(
        [
            "rtk",
            "python3",
            str(SCRIPT),
            str(tmp_path),
            "--section",
            "review-queue",
            "--json",
            "--as-of",
            "2026-08-01",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode in {0, 1}
    payload = json.loads(result.stdout)["indexes"]["by_review_queue"]
    sla = payload["summary"]["review_sla"]
    assert sla["overdue_count"] == 1
    assert sla["due_within_7_days_count"] == 1
    assert sla["missing_date_count"] == 1
    assert payload["by_domain"]["projects/a"]["count"] == 2
    batch = payload["review_batch_packet"]["recommended_batch"]
    assert len(batch) <= 10
    assert {row["sla_status"] for row in batch} >= {
        "overdue",
        "due-within-7-days",
        "missing-date",
    }
    assert payload["review_batch_packet"]["read_only"] is True
