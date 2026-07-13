from tools.codex_assets.knowledge_hub import restore


def test_candidate_paths_exclude_tracked_deletions(monkeypatch, tmp_path):
    def fake_run_rtk(_root, command, **_kwargs):
        if "--deleted" in command:
            return {"stdout": "removed.sh\0"}
        return {"stdout": "kept.md\0removed.sh\0new.md\0"}

    monkeypatch.setattr(restore, "run_rtk", fake_run_rtk)

    assert restore._candidate_paths(tmp_path) == ["kept.md", "new.md"]


def test_restore_snapshot_modes_are_separate(tmp_path):
    assert restore._snapshot_path(tmp_path, "candidate").name == "restore-drill-candidate.json"
    assert restore._snapshot_path(tmp_path, "head").name == "restore-drill-head.json"


def test_restore_rejects_unknown_source_mode(tmp_path):
    try:
        restore.run_restore_drill(tmp_path, "2026-07-13", source_mode="unknown")
    except restore.KnowledgeHubError as exc:
        assert "candidate or head" in str(exc)
    else:
        raise AssertionError("unknown restore source mode was accepted")
