import datetime as dt
import json

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, file_sha256, load_jsonl
from tools.codex_assets.knowledge_hub.lifecycle import capture, transition
from tools.codex_assets.knowledge_hub.cli import _capture_summary, main as lifecycle_main
from tools.codex_assets.knowledge_hub.model import validate_item
from tools.codex_assets.knowledge_hub.obsidian_view import build_obsidian_views
from tools.codex_assets.knowledge_hub.review_attestation import (
    build_attestation_packet,
    generate_review_form,
)


def _jsonl(rows):
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)


def _root(tmp_path):
    (tmp_path / "registry").mkdir()
    (tmp_path / "indexes").mkdir()
    (tmp_path / "governance").mkdir()
    (tmp_path / "registry/items.jsonl").write_text("")
    (tmp_path / "registry/authorizations.jsonl").write_text("")
    (tmp_path / "registry/promotions.jsonl").write_text("")
    (tmp_path / "registry/projects.json").write_text('{"projects": []}\n')
    (tmp_path / "indexes/by-owner.md").write_text("# By Owner\n\n## leiwenjun\n")
    (tmp_path / "indexes/by-review-date.md").write_text("# By Review Date\n")
    (tmp_path / "indexes/by-status.md").write_text("# By Status\n")
    (tmp_path / "indexes/by-project.md").write_text("# By Project\n")
    (tmp_path / "indexes/by-topic.md").write_text("# By Topic\n")
    return tmp_path


def test_capture_apply_creates_reviewing_item_and_indexes(tmp_path):
    root = _root(tmp_path)
    source = tmp_path / "source.md"
    source.write_text("# 捕获样例\n\n这是待复核内容。\n")
    result = capture(
        root,
        source,
        "audit",
        "governance/captured.md",
        dt.date(2026, 7, 13),
        True,
        item_id="captured-20260713",
        tags=("capture",),
    )
    assert result["status"] == "applied"
    item = load_jsonl(root / "registry/items.jsonl")[0]
    assert item["status"] == "reviewing"
    assert item["manual_validation_pending"] is True
    assert "captured-20260713" in (root / "indexes/by-status.md").read_text()
    assert load_jsonl(root / "registry/lifecycle-events.jsonl")[0]["event_type"] == "capture"
    assert "indexes/obsidian/topics.md" in result["transaction"]["changed_paths"]
    assert "indexes/obsidian/reviewing.base" in result["transaction"]["changed_paths"]
    rebuilt = build_obsidian_views(root)
    assert rebuilt["content_mirror_drift_count"] == 0
    assert rebuilt["transaction"]["changed_count"] == 0


def test_capture_summary_json_is_bounded_and_omits_write_rows(tmp_path, capsys):
    root = _root(tmp_path)
    source = tmp_path / "source.md"
    source.write_text("# 捕获摘要\n")
    result = lifecycle_main(
        [
            "capture",
            "--root",
            str(root),
            "--source",
            str(source),
            "--kind",
            "audit",
            "--target",
            "governance/summary.md",
            "--id",
            "summary-20260801",
            "--summary-json",
        ]
    )
    output = capsys.readouterr().out.strip()
    payload = json.loads(output)
    assert result == 0
    assert len(output.encode("utf-8")) <= 2048
    assert payload["projection"] == "knowledge-capture-summary-v1"
    assert payload["transaction"]["changed_count"] > 0
    assert "writes" not in payload["transaction"]


def test_capture_summary_preserves_error_and_applied_write_count():
    error = _capture_summary(
        {"status": "error", "error": "invalid scope", "command": "capture", "dry_run": True}
    )
    applied = _capture_summary(
        {
            "status": "applied",
            "transaction": {"changed_paths": ["a"], "unchanged_paths": ["b", "c"]},
        }
    )
    assert error["error"] == "invalid scope"
    assert error["dry_run"] is True
    assert applied["transaction"]["write_count"] == 3


def test_capture_records_explicit_ai_provenance(tmp_path):
    root = _root(tmp_path)
    source = tmp_path / "source.md"
    source.write_text("# AI 审计候选\n\n这是待人工复核的 Codex 输出。\n")
    capture(
        root,
        source,
        "audit",
        "governance/ai-audit.md",
        dt.date(2026, 7, 13),
        True,
        item_id="ai-audit-20260713",
        generated_by_ai=True,
        ai_role="drafted",
        ai_model_or_tool="Codex",
        source_type="generated",
        source_from="current-session test fixture",
    )
    item = load_jsonl(root / "registry/items.jsonl")[0]
    assert item["generated_by_ai"] is True
    assert item["ai_role"] == "drafted"
    assert item["ai_model_or_tool"] == "Codex"
    assert item["ai_generated_at"] == "2026-07-13"
    assert item["source"]["type"] == "generated"
    assert item["source"]["from"] == "current-session test fixture"
    assert item["primary_language"] == "zh-CN"
    assert item["source_language"] == "zh-CN"
    assert item["translation_status"] == "not-required"
    assert item["terminology_status"] == "pending-review"
    body = (root / "governance/ai-audit.md").read_text()
    assert "generated_by_ai: true" in body
    assert "ai_role: drafted" in body
    assert "primary_language: zh-CN" in body
    assert "terminology_status: pending-review" in body


def test_capture_blank_language_metadata_uses_contract_defaults(tmp_path):
    root = _root(tmp_path)
    source = tmp_path / "source.md"
    source.write_text(
        "---\n"
        "title: 空语言元数据候选\n"
        "primary_language:\n"
        "source_language:\n"
        "translation_status:\n"
        "terminology_status:\n"
        "---\n\n"
        "这是待复核内容。\n"
    )

    capture(
        root,
        source,
        "audit",
        "governance/blank-language-metadata.md",
        dt.date(2026, 7, 26),
        True,
        item_id="blank-language-metadata-20260726",
    )

    item = load_jsonl(root / "registry/items.jsonl")[0]
    assert item["primary_language"] == "zh-CN"
    assert item["source_language"] == "zh-CN"
    assert item["translation_status"] == "not-required"
    assert item["terminology_status"] == "pending-review"
    body = (root / "governance/blank-language-metadata.md").read_text()
    assert "primary_language: zh-CN" in body
    assert "source_language: zh-CN" in body
    assert "translation_status: not-required" in body
    assert "terminology_status: pending-review" in body


def test_capture_external_temporary_source_records_hash_without_temporary_path(tmp_path):
    root = _root(tmp_path)
    source = tmp_path.parent / "{}-ephemeral-source.md".format(tmp_path.name)
    source.write_text("# 临时来源\n\n只保留内容哈希。\n")

    capture(
        root,
        source,
        "audit",
        "governance/ephemeral-source.md",
        dt.date(2026, 7, 19),
        True,
        item_id="ephemeral-source-20260719",
    )

    item = load_jsonl(root / "registry/items.jsonl")[0]
    assert item["source"]["type"] == "ephemeral-file-capture"
    assert item["source"]["from"].startswith("ephemeral-content-sha256:")
    assert item["source"]["temporary_source_retained"] is False
    assert "/tmp/" not in json.dumps(item["source"], ensure_ascii=False)


def test_reviewing_item_rejects_temporary_durable_metadata(tmp_path):
    root = _root(tmp_path)
    source = tmp_path / "source.md"
    source.write_text("# 临时证据门禁\n\n待复核。\n")
    capture(
        root,
        source,
        "audit",
        "governance/temp-evidence.md",
        dt.date(2026, 7, 19),
        True,
        item_id="temp-evidence-20260719",
    )
    item = load_jsonl(root / "registry/items.jsonl")[0]
    item["evidence_refs"] = ["/tmp/transient.log sha256=abc"]

    assert (
        "active/reviewing durable metadata must not reference temporary path: evidence_refs[0]"
        in validate_item(item)
    )


def test_capture_manifest_audit_creates_machine_companion(tmp_path):
    root = _root(tmp_path)
    source = tmp_path / "source.md"
    source.write_text("# 审计候选\n\n机器 companion 测试。\n")
    capture(
        root,
        source,
        "audit",
        "artifacts/manifests/audit.md",
        dt.date(2026, 7, 13),
        True,
        item_id="audit-20260713",
        generated_by_ai=True,
    )
    rows = load_jsonl(root / "artifacts/manifests/audit.jsonl")
    assert rows[0]["id"] == "audit-20260713"
    assert rows[0]["status"] == "reviewing"
    assert rows[0]["manual_validation_pending"] is True
    item = load_jsonl(root / "registry/items.jsonl")[0]
    assert "artifacts/manifests/audit.jsonl" in item["validation_refs"]


def test_promote_requires_authorization_and_review_form(tmp_path):
    root = _root(tmp_path)
    source = tmp_path / "source.md"
    source.write_text("# 捕获样例\n\n待复核。\n")
    capture(
        root,
        source,
        "audit",
        "governance/captured.md",
        dt.date(2026, 7, 13),
        True,
        item_id="captured-20260713",
        tags=("capture",),
    )
    result = transition(root, "captured-20260713", "active", dt.date(2026, 7, 13), False)
    assert result["status"] == "blocked"
    assert "authorization_id is required" in result["gate_errors"]
    with pytest.raises(KnowledgeHubError):
        transition(root, "captured-20260713", "active", dt.date(2026, 7, 13), True)


def test_promote_consumes_scoped_authorization(tmp_path):
    root = _root(tmp_path)
    source = tmp_path / "source.md"
    source.write_text("# 捕获样例\n\n待复核。\n")
    capture(
        root,
        source,
        "audit",
        "governance/captured.md",
        dt.date(2026, 7, 13),
        True,
        item_id="captured-20260713",
        tags=("capture",),
    )
    auth_id = "auth-captured-active"
    authorization = {
        "authorization_id": auth_id,
        "authorized_by": "owner-a",
        "authorized_at": "2026-07-13",
        "scope": "active promotion for captured-20260713 only",
        "allowed_actions": ["active-promotion"],
        "expires_at": "2026-07-14",
        "evidence_refs": ["review.json"],
        "rollback_path": "restore pre-transaction files",
        "validation_commands": ["rtk bash tools/knowledge-check.sh --dry-run"],
        "status": "active",
    }
    (root / "registry/authorizations.jsonl").write_text(_jsonl([authorization]))
    packet = build_attestation_packet(
        root,
        "captured-20260713",
        "active",
        dt.date(2026, 7, 13),
    )
    statement = packet["content_review_attestation"]["response_templates"]["human-reviewed"].replace(
        "<reviewer>", "owner-a"
    )
    review_output = "artifacts/manifests/captured-active.local.jsonl"
    generate_review_form(
        root,
        "captured-20260713",
        "active",
        dt.date(2026, 7, 13),
        packet["item"]["content_sha256"],
        "human-reviewed",
        "owner-a",
        "test:owner-a-active-confirmation",
        statement,
        review_output,
        True,
        True,
    )
    review_path = root / review_output
    body_hash = file_sha256(root / "governance/captured.md")
    result = transition(
        root,
        "captured-20260713",
        "active",
        dt.date(2026, 7, 13),
        True,
        authorization_id=auth_id,
        review_form=review_path,
        expected_item_sha256=body_hash,
    )
    assert result["status"] == "applied"
    assert load_jsonl(root / "registry/items.jsonl")[0]["status"] == "active"
    assert load_jsonl(root / "registry/authorizations.jsonl")[0]["status"] == "used"
    assert load_jsonl(root / "registry/promotions.jsonl")[0]["target_item"] == "captured-20260713"
    events = load_jsonl(root / "registry/lifecycle-events.jsonl")
    assert [row["event_type"] for row in events] == ["capture", "promote"]
    assert "indexes/obsidian/active-knowledge.base" in result["transaction"]["unchanged_paths"]
    rebuilt = build_obsidian_views(root)
    assert rebuilt["content_mirror_drift_count"] == 0
    assert rebuilt["transaction"]["changed_count"] == 0


def test_removed_coupled_review_form_is_rejected(tmp_path):
    root = _root(tmp_path)
    source = tmp_path / "source.md"
    source.write_text("# 捕获样例\n\n待复核。\n")
    capture(
        root,
        source,
        "audit",
        "governance/captured.md",
        dt.date(2026, 7, 13),
        True,
        item_id="captured-20260713",
    )
    review_path = root / "review.json"
    review_path.write_text(
        json.dumps(
            {
                "item_id": "captured-20260713",
                "reviewed_by": "owner-a",
                "reviewed_at": "2026-07-13",
                "review_decision": "accept-active",
                "review_basis": "removed coupled form",
                "validation_refs": ["governance/captured.md"],
                "authorization_id": "auth-captured-active",
            }
        )
    )

    result = transition(
        root,
        "captured-20260713",
        "active",
        dt.date(2026, 7, 13),
        False,
        authorization_id="auth-captured-active",
        review_form=review_path,
    )

    assert any("content-review-attestation is required" in error for error in result["gate_errors"])
