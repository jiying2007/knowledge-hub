import hashlib
import json

import pytest

from tools.codex_assets.knowledge_hub.artifact_restore import run_artifact_restore_drill
from tools.codex_assets.knowledge_hub.artifact_restore_cli import main as artifact_restore_main
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _release(tmp_path):
    root = tmp_path / "release"
    (root / "bin").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "bin/tool").write_bytes(b"executable payload\n")
    (root / "docs/guide.md").write_text("# 使用说明\n")
    rows = [
        "{}  {}\n".format(_sha256(root / relative), relative)
        for relative in ("bin/tool", "docs/guide.md")
    ]
    (root / "SHA256SUMS.txt").write_text("".join(rows))
    return root


def test_artifact_restore_drill_detects_corruption_and_restores(tmp_path):
    release = _release(tmp_path)
    before = {path.relative_to(release).as_posix(): _sha256(path) for path in release.rglob("*") if path.is_file()}

    payload = run_artifact_restore_drill(release, "fixture://tool/v1")

    after = {path.relative_to(release).as_posix(): _sha256(path) for path in release.rglob("*") if path.is_file()}
    assert payload["status"] == "pass"
    assert payload["file_count"] == 2
    assert payload["phases"]["source_integrity"] is True
    assert payload["phases"]["negative_corruption_detection"] is True
    assert payload["phases"]["restore_integrity"] is True
    assert payload["phases"]["source_unchanged"] is True
    assert payload["temporary_cleanup"] is True
    assert before == after
    assert validate_instance(
        repository_root(), "artifact-restore-drill-v1", payload
    )["status"] == "pass"
    payload["authority_contract"] = dict(payload["authority_contract"])
    payload["authority_contract"]["source_written"] = True
    assert validate_instance(
        repository_root(), "artifact-restore-drill-v1", payload
    )["status"] == "fail"


def test_artifact_restore_drill_fails_before_copy_on_source_mismatch(tmp_path):
    release = _release(tmp_path)
    (release / "bin/tool").write_bytes(b"tampered\n")

    payload = run_artifact_restore_drill(release, "fixture://tool/v1")

    assert payload["status"] == "fail"
    assert payload["phases"]["source_integrity"] is False
    assert payload["phases"]["deployment_copy_integrity"] is False


def test_artifact_restore_drill_rejects_manifest_escape_and_symlink(tmp_path):
    release = _release(tmp_path)
    outside = tmp_path / "outside"
    outside.write_text("secret\n")
    (release / "SHA256SUMS.txt").write_text("{}  ../outside\n".format(_sha256(outside)))
    with pytest.raises(KnowledgeHubError, match="relative path"):
        run_artifact_restore_drill(release, "fixture://tool/v1")

    release = _release(tmp_path / "linked")
    link = release / "bin/link"
    link.symlink_to(outside)
    with (release / "SHA256SUMS.txt").open("a") as handle:
        handle.write("{}  bin/link\n".format(_sha256(outside)))
    with pytest.raises(KnowledgeHubError, match="symlink"):
        run_artifact_restore_drill(release, "fixture://tool/v1")


def test_artifact_restore_drill_rejects_control_characters(tmp_path):
    release = _release(tmp_path)
    with pytest.raises(KnowledgeHubError, match="source_label"):
        run_artifact_restore_drill(release, "fixture://tool\nsecret")

    (release / "SHA256SUMS.txt").write_text("{}  bad\x00path\n".format("a" * 64))
    with pytest.raises(KnowledgeHubError, match="invalid checksum path"):
        run_artifact_restore_drill(release, "fixture://tool/v1")


def test_artifact_restore_cli_resolves_relative_root_from_caller_cwd(
    tmp_path, monkeypatch, capsys
):
    _release(tmp_path)
    monkeypatch.setenv("KNOWLEDGE_CALLER_CWD", str(tmp_path))

    exit_code = artifact_restore_main(
        [
            "--release-root",
            "release",
            "--source-label",
            "fixture://tool/v1",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "pass"
    assert payload["source_label"] == "fixture://tool/v1"
