import datetime as dt
import json
import pathlib
import subprocess

import pytest

from tools.codex_assets.knowledge_hub.activity import (
    build_facts,
    capture_activity,
    capture_item,
    collect_work_items,
    generate_report,
    normalize_item,
    record_item,
    report_period,
)
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


def _hub(root: pathlib.Path, *, configured: bool = True) -> pathlib.Path:
    (root / "registry").mkdir(parents=True)
    (root / "registry/items.jsonl").write_text("", encoding="utf-8")
    (root / "local").mkdir()
    (root / "local/workspaces.json").write_text(json.dumps({"workspaces": []}), encoding="utf-8")
    if configured:
        (root / "local/activity-report.json").write_text(
            json.dumps({
                "schema_version": 2,
                "enabled": True,
                "subject_id": "developer-a",
                "display_name": "开发者A",
                "default_scope": "personal",
                "timezone": "Asia/Hong_Kong",
                "receipt_persistence": True,
                "retention_days": 45,
                "repositories": [],
            }), encoding="utf-8",
        )
    return root


def _item(**overrides):
    payload = {
        "schema_version": 2,
        "kind": "work-activity-item",
        "item_id": "item-1",
        "subject_id": "developer-a",
        "project_id": "sample",
        "activity_date": "2026-08-21",
        "title": "完成活动报告 v2",
        "status": "done",
        "verification": "verified",
        "outcomes": ["完成硬切"],
        "evidence_refs": ["validation:test-1"],
        "blockers": [],
        "next_actions": ["运行全量门禁"],
        "raw_content_stored": False,
    }
    payload.update(overrides)
    return payload


def test_periods_are_explicit_and_week_starts_monday():
    assert report_period("daily", dt.date(2026, 8, 21)) == (dt.date(2026, 8, 21), dt.date(2026, 8, 21))
    assert report_period("weekly", dt.date(2026, 8, 21)) == (dt.date(2026, 8, 17), dt.date(2026, 8, 21))
    assert report_period("custom", dt.date(2026, 8, 21), dt.date(2026, 8, 1), dt.date(2026, 8, 9)) == (
        dt.date(2026, 8, 1), dt.date(2026, 8, 9)
    )
    with pytest.raises(KnowledgeHubError):
        report_period("custom", dt.date(2026, 8, 21))


def test_v2_item_requires_identity_privacy_and_verified_evidence():
    normalized = normalize_item(_item(), source_kind="test", source_ref="case")
    assert normalized["subject_id"] == "developer-a"
    assert normalized["raw_content_stored"] is False
    with pytest.raises(KnowledgeHubError):
        normalize_item(_item(subject_id=""), source_kind="test", source_ref="case")
    with pytest.raises(KnowledgeHubError):
        normalize_item(_item(evidence_refs=[]), source_kind="test", source_ref="case")
    with pytest.raises(KnowledgeHubError):
        normalize_item(_item(raw_content_stored=True), source_kind="test", source_ref="case")


def test_explicit_item_overrides_receipt_by_stable_identity(tmp_path):
    root = _hub(tmp_path / "hub")
    receipt_dir = root / ".tmp/activity/receipts/2026-08-21"
    receipt_dir.mkdir(parents=True)
    receipt_dir.joinpath("receipt.json").write_text(
        json.dumps({
            "schema_version": 2,
            "kind": "activity-session-receipt",
            "work_items": [_item(title="回执标题", verification="reported", evidence_refs=[])],
            "raw_content_stored": False,
        }), encoding="utf-8",
    )
    item_dir = root / ".tmp/activity/items/2026-08-21"
    item_dir.mkdir(parents=True)
    item_dir.joinpath("item-1.json").write_text(json.dumps(_item(title="显式事项标题")), encoding="utf-8")
    rows, coverage = collect_work_items(root, dt.date(2026, 8, 17), dt.date(2026, 8, 21), subject_id="developer-a")
    assert len(rows) == 1
    assert rows[0]["title"] == "显式事项标题"
    assert rows[0]["source"]["kind"] == "explicit-item"
    assert coverage["receipt_count"] == 1


def test_personal_scope_never_collects_git_or_infers_identity(tmp_path):
    root = _hub(tmp_path / "hub")
    facts = build_facts(
        root, period="weekly", scope="personal", as_of=dt.date(2026, 8, 21),
        start=None, end=None, subject_id="", project_id="", codex_root=tmp_path / "codex", detail="normal",
    )
    assert facts["status"] == "pass"
    assert facts["subject"]["id"] == "developer-a"
    assert facts["git_activity"] == []
    assert facts["registry_activity"] == []
    assert facts["privacy"]["identity_inferred_from_git"] is False
    assert any("record" in warning for warning in facts["warnings"])


def test_personal_scope_without_subject_fails_closed(tmp_path):
    root = _hub(tmp_path / "hub", configured=False)
    facts = build_facts(
        root, period="daily", scope="personal", as_of=dt.date(2026, 8, 21),
        start=None, end=None, subject_id="", project_id="", codex_root=tmp_path / "codex", detail="normal",
    )
    assert facts["status"] == "needs-input"
    assert any("subject_id" in warning for warning in facts["warnings"])


def test_capture_dry_run_then_apply_and_generate_hash_bound_report(tmp_path):
    root = _hub(tmp_path / "hub")
    source = tmp_path / "item.json"
    source.write_text(json.dumps(_item()), encoding="utf-8")
    dry = capture_item(root, source, apply=False)
    assert dry["applied"] is False
    assert not (root / ".tmp/activity/items/2026-08-21/item-1.json").exists()
    applied = capture_item(root, source, apply=True)
    assert applied["applied"] is True
    receipt = generate_report(
        root, period="weekly", scope="personal", as_of=dt.date(2026, 8, 21),
        start=None, end=None, subject_id="", project_id="", codex_root=tmp_path / "codex",
        detail="normal", output_root=root / ".tmp/activity", write=True,
    )
    report_path = pathlib.Path(receipt["report_path"])
    facts_path = pathlib.Path(receipt["facts_path"])
    assert receipt["status"] == "pass"
    assert report_path.is_file() and facts_path.is_file()
    assert "已完成" in report_path.read_text(encoding="utf-8")
    assert json.loads(facts_path.read_text(encoding="utf-8"))["schema_version"] == 2


def test_capture_session_receipt_persists_under_hub_and_is_collectable(tmp_path):
    root = _hub(tmp_path / "hub")
    source = tmp_path / "activity-session-receipt-session-123.json"
    source.write_text(json.dumps({
        "schema_version": 2,
        "kind": "activity-session-receipt",
        "session_date": "2026-08-21",
        "work_items": [_item()],
        "raw_content_stored": False,
    }), encoding="utf-8")
    dry = capture_activity(root, source, apply=False)
    assert dry["applied"] is False
    assert dry["target"] == ""
    applied = capture_activity(root, source, apply=True)
    target = pathlib.Path(applied["target"])
    assert target == root / ".tmp/activity/receipts/2026-08-21/session-123.json"
    assert target.is_file()
    rows, coverage = collect_work_items(
        root, dt.date(2026, 8, 21), dt.date(2026, 8, 21), subject_id="developer-a"
    )
    assert len(rows) == 1
    assert coverage["receipt_count"] == 1


def test_capture_session_receipt_fails_closed_without_persistence_authorization(tmp_path):
    root = _hub(tmp_path / "hub")
    config_path = root / "local/activity-report.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["receipt_persistence"] = False
    config_path.write_text(json.dumps(config), encoding="utf-8")
    source = tmp_path / "receipt.json"
    source.write_text(json.dumps({
        "schema_version": 2,
        "kind": "activity-session-receipt",
        "session_date": "2026-08-21",
        "work_items": [_item()],
        "raw_content_stored": False,
    }), encoding="utf-8")
    with pytest.raises(KnowledgeHubError, match="receipt persistence requires"):
        capture_activity(root, source, apply=True)


def test_record_avoids_hand_authored_json_and_preserves_v2_gates(tmp_path):
    root = _hub(tmp_path / "hub")
    dry = record_item(
        root, title="整理周报流程", activity_date=dt.date(2026, 8, 21), subject_id="", project_id="knowledge-hub",
        item_id="", status="done", verification="reported", outcomes=["提供一行记录入口"], evidence_refs=[],
        blockers=[], next_actions=[], apply=False,
    )
    assert dry["applied"] is False
    applied = record_item(
        root, title="整理周报流程", activity_date=dt.date(2026, 8, 21), subject_id="", project_id="knowledge-hub",
        item_id="", status="done", verification="reported", outcomes=["提供一行记录入口"], evidence_refs=[],
        blockers=[], next_actions=[], apply=True,
    )
    target = pathlib.Path(applied["target"])
    assert target.is_file()
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["subject_id"] == "developer-a"
    assert payload["raw_content_stored"] is False
    facts = build_facts(
        root, period="weekly", scope="personal", as_of=dt.date(2026, 8, 21), start=None, end=None,
        subject_id="", project_id="", codex_root=tmp_path / "codex", detail="normal",
    )
    assert facts["summary"]["done_pending_verification"] == 1


def test_legacy_receipts_are_diagnosed_but_never_collected(tmp_path):
    root = _hub(tmp_path / "hub")
    legacy = root / ".tmp/session-receipts/2026-08-21"
    legacy.mkdir(parents=True)
    legacy.joinpath("legacy.json").write_text('{"schema_version": 1}', encoding="utf-8")
    facts = build_facts(
        root, period="weekly", scope="personal", as_of=dt.date(2026, 8, 21), start=None, end=None,
        subject_id="", project_id="", codex_root=tmp_path / "codex", detail="normal",
    )
    assert facts["summary"]["item_count"] == 0
    assert facts["source_coverage"]["work_items"]["legacy_receipt_file_count"] == 1
    assert any("旧目录回执" in warning for warning in facts["warnings"])


def test_cli_has_dedicated_subcommands_and_old_flags_are_rejected():
    root = pathlib.Path(__file__).resolve().parents[1]
    help_result = subprocess.run(
        ["bash", str(root / "tools/knowledge-activity.sh"), "--help"],
        cwd="/tmp", capture_output=True, text=True, check=False,
    )
    assert help_result.returncode == 0
    assert "{report,capture,record,validate,coverage}" in help_result.stdout
    old = subprocess.run(
        ["bash", str(root / "tools/knowledge-metrics.sh"), "--activity-report", "daily"],
        cwd="/tmp", capture_output=True, text=True, check=False,
    )
    assert old.returncode != 0


def test_systemd_units_use_v2_cli_and_report_only_boundary():
    root = pathlib.Path(__file__).resolve().parents[1]
    daily = (root / "tools/systemd/knowledge-activity-daily.service").read_text(encoding="utf-8")
    weekly = (root / "tools/systemd/knowledge-activity-weekly.service").read_text(encoding="utf-8")
    assert "knowledge-activity.sh report --period daily" in daily
    assert "knowledge-activity.sh report --period weekly" in weekly
    for service in (daily, weekly):
        assert "--scope personal" in service
        assert "ProtectSystem=strict" in service
        assert "RestrictAddressFamilies=AF_UNIX" in service
        assert "ReadWritePaths=%h/knowledge-hub/.tmp/activity" in service
