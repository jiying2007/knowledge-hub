import datetime as dt
import json
import os
import pathlib
import subprocess

from tools.codex_assets.knowledge_hub.activity_report import (
    build_activity_facts,
    collect_memory_cues,
    collect_registry_activity,
    collect_session_receipts,
    generate_activity_report,
    report_period,
)


def _hub(root: pathlib.Path) -> pathlib.Path:
    (root / "registry").mkdir(parents=True)
    (root / "registry/items.jsonl").write_text("", encoding="utf-8")
    (root / "local").mkdir()
    (root / "local/workspaces.json").write_text(
        json.dumps({"workspaces": []}),
        encoding="utf-8",
    )
    return root


def _git_repository(path: pathlib.Path, committed_at: str, subject: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.invalid"], check=True)
    (path / "README.md").write_text(subject + "\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
    environment = dict(os.environ)
    environment.update({"GIT_AUTHOR_DATE": committed_at, "GIT_COMMITTER_DATE": committed_at})
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", subject], check=True, env=environment)


def test_report_period_uses_monday_to_as_of_for_weekly():
    start, end = report_period("weekly", dt.date(2026, 8, 7))

    assert start == dt.date(2026, 8, 3)
    assert end == dt.date(2026, 8, 7)
    assert report_period("daily", end) == (end, end)


def test_registry_activity_uses_created_and_updated_dates_and_redacts_secrets(tmp_path):
    root = _hub(tmp_path / "hub")
    rows = [
        {
            "id": "current",
            "title": "Current",
            "summary_zh": "token=abcdefghijklmnopqrstuvwxyz0123456789",
            "domain": "projects/sample",
            "kind": "validation",
            "status": "reviewing",
            "path": "projects/sample/validation/current.md",
            "created_at": "2026-08-01",
        },
        {
            "id": "updated",
            "title": "Updated",
            "summary_zh": "updated this week",
            "domain": "projects/sample",
            "kind": "decision",
            "status": "reviewing",
            "path": "projects/sample/decisions/updated.md",
            "created_at": "2026-07-01",
            "updated_at": "2026-08-02",
        },
        {"id": "old", "title": "Old", "created_at": "2026-07-01"},
    ]
    (root / "registry/items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    selected = collect_registry_activity(root, dt.date(2026, 8, 1), dt.date(2026, 8, 2))

    assert [row["id"] for row in selected] == ["current", "updated"]
    assert selected[0]["summary_zh"].startswith("[已脱敏")
    assert selected[1]["activity_dates"] == ["2026-08-02"]


def test_memory_cues_exclude_raw_memory_and_keep_project_context(tmp_path):
    memory = tmp_path / "memories"
    (memory / "rollout_summaries").mkdir(parents=True)
    (memory / "projects").mkdir()
    (memory / "raw_memories.md").write_text("# raw secret history\n", encoding="utf-8")
    (memory / "rollout_summaries/2026-08-02T10-00-00-test.md").write_text(
        "thread_id: hidden\n# Completed PCR02 validation\nraw body must not be copied\n",
        encoding="utf-8",
    )
    (memory / "projects/gd32l235.md").write_text("# GD32L235 stable context\n", encoding="utf-8")

    cues, metadata = collect_memory_cues(
        memory,
        dt.date(2026, 8, 2),
        dt.date(2026, 8, 2),
        ["projects-gd32l235"],
    )

    assert {row["path"] for row in cues} == {
        "projects/gd32l235.md",
        "rollout_summaries/2026-08-02T10-00-00-test.md",
    }
    assert all("raw body" not in json.dumps(row) for row in cues)
    assert metadata["excluded_raw_memory"] is True


def test_session_receipts_are_bounded_redacted_and_period_filtered(tmp_path):
    root = _hub(tmp_path / "hub")
    receipts = root / ".tmp/session-receipts/2026-08-02"
    receipts.mkdir(parents=True)
    valid = {
        "schema_version": 1,
        "kind": "codex-session-receipt",
        "project": "sample",
        "period_date": "2026-08-02",
        "goal": "完成自动报告",
        "outcomes": ["日报首跑通过"],
        "validation": ["pytest pass"],
        "risks": [],
        "next_actions": ["人工复核"],
        "artifacts": [str(tmp_path / "private/report.md")],
        "completion_status": "complete",
        "raw_content_stored": False,
    }
    (receipts / "valid.json").write_text(json.dumps(valid), encoding="utf-8")
    (receipts / "raw.json").write_text(
        json.dumps({**valid, "raw_content_stored": True}),
        encoding="utf-8",
    )
    (receipts / "old.json").write_text(
        json.dumps({**valid, "period_date": "2026-07-01"}),
        encoding="utf-8",
    )

    selected, metadata = collect_session_receipts(root, dt.date(2026, 8, 2), dt.date(2026, 8, 2))

    assert len(selected) == 1
    assert selected[0]["receipt_id"] == "valid"
    assert selected[0]["artifacts"] == ["[本地工件路径已省略]"]
    assert selected[0]["raw_content_stored"] is False
    assert metadata["invalid_count"] == 2


def test_activity_facts_combine_registry_git_and_memory_without_local_paths(tmp_path):
    root = _hub(tmp_path / "hub")
    codex = tmp_path / "codex"
    memory = tmp_path / "memories"
    (memory / "rollout_summaries").mkdir(parents=True)
    _git_repository(root, "2026-08-02T08:00:00+08:00", "feat: hub activity")
    _git_repository(codex, "2026-08-02T09:00:00+08:00", "feat: codex activity")
    (memory / "rollout_summaries/2026-08-02T10-00-00-test.md").write_text(
        "# Codex rollout summary\n",
        encoding="utf-8",
    )
    (root / "registry/items.jsonl").write_text(
        json.dumps(
            {
                "id": "sample",
                "title": "Sample validation",
                "summary_zh": "验证通过",
                "domain": "projects/sample",
                "kind": "validation",
                "status": "reviewing",
                "path": "projects/sample/validation/sample.md",
                "created_at": "2026-08-02",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    facts = build_activity_facts(root, "daily", dt.date(2026, 8, 2), codex, memory)

    assert facts["summary"]["registry_item_count"] == 1
    assert facts["summary"]["git_commit_count"] == 2
    assert facts["summary"]["session_receipt_count"] == 0
    assert facts["summary"]["memory_cue_count"] == 1
    encoded = json.dumps(facts, ensure_ascii=False)
    assert str(tmp_path) not in encoded
    assert facts["privacy"]["raw_sessions_stored"] is False


def test_generate_report_writes_hash_bound_markdown_and_json(tmp_path):
    root = _hub(tmp_path / "hub")
    codex = tmp_path / "missing-codex"
    memory = tmp_path / "missing-memory"
    output = root / ".tmp/reports"

    receipt = generate_activity_report(
        root,
        "weekly",
        dt.date(2026, 8, 7),
        codex,
        memory,
        output,
    )

    report_path = pathlib.Path(receipt["report_path"])
    facts_path = pathlib.Path(receipt["facts_path"])
    assert report_path.is_file()
    assert facts_path.is_file()
    assert report_path.name == "2026-W32-2026-08-07.md"
    assert "report-only" in report_path.read_text(encoding="utf-8")
    assert json.loads(facts_path.read_text(encoding="utf-8"))["report_kind"] == "weekly"


def test_systemd_units_use_expected_cadence_and_read_only_boundary():
    root = pathlib.Path(__file__).resolve().parents[1]
    daily_timer = (root / "tools/systemd/knowledge-activity-daily.timer").read_text(encoding="utf-8")
    weekly_timer = (root / "tools/systemd/knowledge-activity-weekly.timer").read_text(encoding="utf-8")
    daily_service = (root / "tools/systemd/knowledge-activity-daily.service").read_text(encoding="utf-8")
    weekly_service = (root / "tools/systemd/knowledge-activity-weekly.service").read_text(encoding="utf-8")

    assert "OnCalendar=*-*-* 20:30:00 Asia/Hong_Kong" in daily_timer
    assert "OnCalendar=Fri *-*-* 20:45:00 Asia/Hong_Kong" in weekly_timer
    for service in (daily_service, weekly_service):
        assert "Environment=PATH=%h/.local/bin:/usr/local/bin:/usr/bin:/bin" in service
        assert "ProtectSystem=strict" in service
        assert "ProtectHome=read-only" in service
        assert "RestrictAddressFamilies=AF_UNIX" in service
        assert "ReadWritePaths=%h/knowledge-hub/.tmp/reports" in service
        assert "--summary-json" in service
