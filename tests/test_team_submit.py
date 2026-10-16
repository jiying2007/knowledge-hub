"""Prevent regression in Git candidate boundaries and deploy evidence checks."""
import datetime as dt
import hashlib
import pathlib
import subprocess

import pytest

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub import team_ci_gate, team_submit


def test_exact_quality_and_signed_runs_required():
    sha = "c" * 40
    good = {"workflow_runs": [
        {"name": "quality", "head_sha": sha, "head_branch": "master", "status": "completed", "conclusion": "success", "event": "push"},
        {"name": "signed-quality-attestation", "head_sha": sha, "head_branch": "master", "status": "completed",
         "conclusion": "success", "event": "workflow_run"},
        {"name": "quality", "head_sha": "d" * 40, "status": "completed",
         "conclusion": "failure", "event": "push"},
    ]}
    assert team_ci_gate.check_runs(good, sha)["status"] == "pass"
    for modified in [
        {"workflow_runs": good["workflow_runs"][:1]},
        {"workflow_runs": [{**good["workflow_runs"][0], "event": "pull_request"}, good["workflow_runs"][1]]},
        {"workflow_runs": [{**good["workflow_runs"][0], "head_sha": "d" * 40}, good["workflow_runs"][1]]},
        {"workflow_runs": [{**good["workflow_runs"][0], "head_branch": "feature"}, good["workflow_runs"][1]]},
        {"workflow_runs": [good["workflow_runs"][0], {**good["workflow_runs"][1], "event": "push"}]},
    ]:
        with pytest.raises(KnowledgeHubError, match="missing"):
            team_ci_gate.check_runs(modified, sha)


def test_submissions_require_public_source_and_safe_changes(tmp_path):
    source = tmp_path / "note.md"
    source.write_text("# 一次正常排障\n\n需要保存的验证结论。", encoding="utf-8")
    assert "排障" in team_submit._safe_source(source)
    source.write_text("password=supersecret123", encoding="utf-8")
    with pytest.raises(KnowledgeHubError):
        team_submit._safe_source(source)
    assert team_submit._permitted_change("projects/pcr02-ssc305/current/team-knowledge/a.md", "pcr02-ssc305")
    assert team_submit._permitted_change("registry/items.jsonl", "pcr02-ssc305")
    assert not team_submit._permitted_change("tools/evil.py", "pcr02-ssc305")
    assert not team_submit._permitted_change(".github/workflows/ci.yml", "pcr02-ssc305")
    assert not team_submit._permitted_change("projects/other/current/team-knowledge/a.md", "pcr02-ssc305")


def test_create_id_not_derived_from_ascii_slug(tmp_path, monkeypatch):
    source = tmp_path / "note.md"
    source.write_text("# 中文排障记录\n\n内容不同。", encoding="utf-8")
    root = tmp_path / "hub"
    root.mkdir()
    monkeypatch.setattr(team_submit, "_route", lambda r, p: "projects/pcr02-ssc305/current/team-knowledge")
    calls = []
    def fake_capture(root, staged, kind, target, today, apply, **kwargs):
        calls.append((staged.read_text(encoding="utf-8"), target, kwargs))
        return {"status": "planned", "target": target}
    monkeypatch.setattr(team_submit, "capture", fake_capture)
    today = dt.date(2026, 10, 16)
    team_submit.create_candidate(root, source, "pcr02-ssc305", "debug-record", today, apply=False)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
    assert calls[0][1].endswith("-20261016-" + digest + ".md")
    assert calls[0][2]["owner"] == "team-core"


def test_team_shell_scripts_are_parseable():
    base = pathlib.Path(__file__).resolve().parents[1] / "tools/team"
    for name in ("serve.sh", "deploy.sh", "backup.sh"):
        result = subprocess.run(["bash", "-n", str(base / name)], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, name


def test_reviewing_update_uses_real_cas_transaction(tmp_path, monkeypatch):
    """A real registry/body/index transaction is produced; Active stays immutable."""
    import json
    from tools.codex_assets.knowledge_hub.common import render_markdown
    root = tmp_path / "hub"
    (root / "registry").mkdir(parents=True)
    (root / "indexes").mkdir()
    relative = "projects/pcr02-ssc305/current/team-knowledge/test-note.md"
    target = root / relative
    target.parent.mkdir(parents=True)
    item = {
        "id": "pcr02-test-note", "title": "初始排障", "kind": "debug-record",
        "domain": "projects/pcr02-ssc305", "path": relative,
        "scope": "project-specific", "visibility": "team-internal",
        "status": "reviewing", "owner": "team-core",
        "source": {"type": "manual", "from": "test"},
        "review_after": "2027-01-01", "created_at": "2026-10-16",
        "updated_at": "2026-10-16", "promotion": "none",
        "review_status": "manual-entry-pending-review", "tags": ["debug-record"],
        "validation_refs": [relative], "evidence_refs": [relative],
        "summary_zh": "初始排障记录", "primary_language": "zh-CN",
        "source_language": "zh-CN", "translation_status": "not-required",
        "terminology_status": "pending-review", "manual_validation_pending": True,
        "human_reviewed_by": "old reviewer",
    }
    target.write_text(render_markdown(item, "# 旧版\n\n原始记录。"), encoding="utf-8")
    (root / "registry/items.jsonl").write_text(json.dumps(item, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / "registry/lifecycle-events.jsonl").write_text("", encoding="utf-8")
    for name in ("by-owner.md", "by-review-date.md", "by-status.md", "by-project.md", "by-topic.md"):
        (root / "indexes" / name).write_text("# Test\n", encoding="utf-8")
    monkeypatch.setattr(team_submit, "_route", lambda root, project:
                        "projects/pcr02-ssc305/current/team-knowledge")
    monkeypatch.setattr(team_submit, "stage_obsidian_views",
                        lambda *args, **kwargs: {"missing_files": [], "content_drifts": []})
    source = tmp_path / "revised.md"
    source.write_text("# 新版\n\n验证后的修订。", encoding="utf-8")
    old_sha = hashlib.sha256(target.read_bytes()).hexdigest()
    result = team_submit.update_candidate(
        root, item["id"], source, old_sha, dt.date(2026, 10, 16),
        apply=True, generated_by_ai=True,
    )
    assert result["status"] == "applied"
    assert "新版" in target.read_text(encoding="utf-8")
    after = json.loads((root / "registry/items.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert after["status"] == "reviewing"
    assert after["generated_by_ai"] is True
    assert "human_reviewed_by" not in after
    assert (root / "registry/lifecycle-events.jsonl").read_text(encoding="utf-8").strip()
    from jsonschema import Draft202012Validator
    schema_path = pathlib.Path(__file__).resolve().parents[1] / "schemas/lifecycle-event.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    event = json.loads((root / "registry/lifecycle-events.jsonl").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(event)
    assert event["event_type"] == "update"
    with pytest.raises(KnowledgeHubError, match="content SHA conflict"):
        team_submit.update_candidate(root, item["id"], source, old_sha, dt.date(2026, 10, 16), apply=True)
    after["status"] = "active"
    (root / "registry/items.jsonl").write_text(json.dumps(after, ensure_ascii=False) + "\n", encoding="utf-8")
    with pytest.raises(KnowledgeHubError, match="reviewing item"):
        team_submit.update_candidate(root, item["id"], source, old_sha, dt.date(2026, 10, 16), apply=True)
