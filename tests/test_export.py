import datetime as dt
import json

import pytest

from tools.codex_assets.knowledge_hub import export as export_module
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.export import apply_team_export, plan_team_export


def _row(item_id, path, status="active", visibility="team-internal"):
    return {
        "id": item_id,
        "title": item_id,
        "kind": "runbook",
        "domain": "embedded",
        "path": path,
        "status": status,
        "visibility": visibility,
        "owner": "owner",
        "review_after": "2026-10-13",
    }


def test_export_only_copies_active_team_canonical_markdown(tmp_path):
    (tmp_path / "registry").mkdir()
    active = _row("active", "domains/embedded/runbooks/active.md")
    reviewing = _row("reviewing", "domains/embedded/runbooks/reviewing.md", status="reviewing")
    for row in (active, reviewing):
        path = tmp_path / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# {}\n".format(row["id"]))
    (tmp_path / "registry/items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in (active, reviewing))
    )
    plan = plan_team_export(tmp_path)
    assert plan["status"] == "ready"
    assert plan["selected_count"] == 1
    output = tmp_path.parent / "export-output"
    result = apply_team_export(tmp_path, dt.date(2026, 7, 13), output)
    assert result["status"] == "exported"
    assert (output / active["path"]).is_file()
    assert not (output / reviewing["path"]).exists()
    assert (output / "manifest.json").is_file()
    assert (output / "registry/items.jsonl").is_file()
    assert (output / "indexes/team-index.md").is_file()
    assert (output / "EXPORT.md").is_file()
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["file_count"] == 4
    assert manifest["secret_scan"]["status"] == "pass"


def test_export_blocks_high_confidence_secret_pattern(tmp_path):
    (tmp_path / "registry").mkdir()
    item = _row("secret", "domains/embedded/runbooks/secret.md")
    path = tmp_path / item["path"]
    path.parent.mkdir(parents=True)
    path.write_text("-----BEGIN PRIVATE KEY-----\n")
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(item) + "\n")
    plan = plan_team_export(tmp_path)
    assert plan["status"] == "blocked"
    assert plan["errors"][0]["error"] == "high-confidence-secret-pattern"


def test_export_blocks_generic_password_assignment(tmp_path):
    (tmp_path / "registry").mkdir()
    item = _row("secret", "domains/embedded/runbooks/secret.md")
    path = tmp_path / item["path"]
    path.parent.mkdir(parents=True)
    path.write_text("password=correct-horse-battery-staple\n")
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(item) + "\n")
    assert plan_team_export(tmp_path)["status"] == "blocked"


def test_export_blocks_repository_file_symlink_even_when_target_is_text(tmp_path):
    (tmp_path / "registry").mkdir()
    item = _row("linked", "domains/embedded/runbooks/linked.md")
    outside = tmp_path.parent / "outside-export.md"
    outside.write_text("# outside export marker\n", encoding="utf-8")
    path = tmp_path / item["path"]
    path.parent.mkdir(parents=True)
    path.symlink_to(outside)
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(item) + "\n")

    plan = plan_team_export(tmp_path)

    assert plan["status"] == "blocked"
    assert plan["errors"][0]["error"] == "unsafe-symlink-or-root-escape"


def test_export_rejects_body_over_configured_byte_budget(monkeypatch, tmp_path):
    (tmp_path / "registry").mkdir()
    item = _row("large", "domains/embedded/runbooks/large.md")
    path = tmp_path / item["path"]
    path.parent.mkdir(parents=True)
    path.write_text("# body larger than test budget\n")
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(item) + "\n")
    monkeypatch.setattr(export_module, "EXPORT_MAX_FILE_BYTES", 16, raising=False)

    plan = plan_team_export(tmp_path)

    assert plan["status"] == "blocked"
    assert plan["errors"][0]["error"] == "body-byte-budget-exceeded"


def test_export_rewrites_links_to_excluded_content(tmp_path):
    (tmp_path / "registry").mkdir()
    active = _row("active", "domains/embedded/runbooks/active.md")
    reviewing = _row("reviewing", "domains/embedded/runbooks/reviewing.md", status="reviewing")
    active_path = tmp_path / active["path"]
    active_path.parent.mkdir(parents=True)
    active_path.write_text("# Active\n\n[pending](reviewing.md)\n")
    (tmp_path / reviewing["path"]).write_text("# Reviewing\n")
    (tmp_path / "registry/items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in (active, reviewing))
    )
    output = tmp_path.parent / "closed-export"
    result = apply_team_export(tmp_path, dt.date(2026, 7, 13), output)
    exported = (output / active["path"]).read_text()
    manifest = json.loads((output / "manifest.json").read_text())
    assert "[pending]" not in exported
    assert result["link_closure"]["status"] == "pass"
    assert manifest["schema_version"] == 2
    assert manifest["link_closure"]["rewrite_count"] == 1


def test_export_publish_failure_never_exposes_partial_destination(tmp_path, monkeypatch):
    (tmp_path / "registry").mkdir()
    item = _row("active", "domains/embedded/runbooks/active.md")
    path = tmp_path / item["path"]
    path.parent.mkdir(parents=True)
    path.write_text("# Active\n")
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(item) + "\n")
    output = tmp_path.parent / "atomic-export"

    def fail_replace(*_args, **_kwargs):
        raise OSError("injected publish failure")

    monkeypatch.setattr(export_module.os, "replace", fail_replace)
    with pytest.raises(KnowledgeHubError):
        apply_team_export(tmp_path, dt.date(2026, 7, 13), output)
    assert not output.exists()
    staging = list(output.parent.glob(output.name + ".staging-*"))
    assert len(staging) == 1
    assert (staging[0] / ".incomplete.json").is_file()


def test_export_output_tree_is_private(tmp_path):
    (tmp_path / "registry").mkdir()
    item = _row("active", "domains/embedded/runbooks/active.md")
    path = tmp_path / item["path"]
    path.parent.mkdir(parents=True)
    path.write_text("# Active\n")
    (tmp_path / "registry/items.jsonl").write_text(json.dumps(item) + "\n")
    output = tmp_path.parent / "private-export"

    apply_team_export(tmp_path, dt.date(2026, 7, 13), output)

    assert output.stat().st_mode & 0o777 == 0o700
    assert (output / item["path"]).stat().st_mode & 0o777 == 0o600
    assert (output / "manifest.json").stat().st_mode & 0o777 == 0o600
