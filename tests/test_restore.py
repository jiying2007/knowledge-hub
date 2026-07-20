from tools.codex_assets.knowledge_hub import restore
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.schemas import validate_instance


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


def test_execution_environment_only_marks_remote_push_on_matching_github_head(
    monkeypatch,
):
    revision = "a" * 40
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "team/knowledge-hub")
    monkeypatch.setenv("GITHUB_SHA", revision)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("RUNNER_ENVIRONMENT", "github-hosted")

    payload = restore._execution_environment("head", revision)

    assert payload["remote_checkout_verified"] is True
    assert payload["remote_published_ref_verified"] is True
    assert payload["offsite_environment_verified"] is True
    assert restore._execution_environment("candidate", revision)[
        "remote_checkout_verified"
    ] is False


def test_restore_v2_schema_strictly_validates_execution_environment():
    revision = "a" * 40
    environment = {
        "provider": "local",
        "repository": "",
        "revision": "",
        "event": "",
        "runner_environment": "",
        "remote_checkout_verified": False,
        "remote_published_ref_verified": False,
        "offsite_environment_verified": False,
    }
    payload = {
        "schema_version": 2,
        "status": "pass",
        "source_mode": "candidate",
        "source_revision": revision,
        "candidate_signature": "b" * 64,
        "execution_environment": environment,
        "remote_checkout_verified": False,
        "remote_published_ref_verified": False,
        "offsite_environment_verified": False,
        "checks": {},
        "cache_included": False,
        "local_workspace_mapping_included": False,
    }

    assert validate_instance(
        repository_root(), "restore-drill-v2", payload
    )["status"] == "pass"

    invalid_provider = dict(payload)
    invalid_provider["execution_environment"] = dict(
        environment, provider="untrusted-runner"
    )
    assert validate_instance(
        repository_root(), "restore-drill-v2", invalid_provider
    )["status"] == "fail"

    unexpected_field = dict(payload)
    unexpected_field["execution_environment"] = dict(
        environment, compatibility_fallback=True
    )
    assert validate_instance(
        repository_root(), "restore-drill-v2", unexpected_field
    )["status"] == "fail"


def test_restore_snapshot_writes_only_the_selected_mode(tmp_path):
    payload = {"source_mode": "candidate", "status": "pass"}

    relative = restore._write_snapshot(tmp_path, payload)

    assert relative == ".cache/knowledge-hub/restore-drill-candidate.json"
    assert (tmp_path / relative).is_file()
    assert (tmp_path / relative).stat().st_mode & 0o777 == 0o600
    assert (tmp_path / ".cache/knowledge-hub").stat().st_mode & 0o777 == 0o700
    assert not list((tmp_path / ".cache/knowledge-hub").glob("*.tmp-*"))
    assert not (tmp_path / ".cache/knowledge-hub/restore-drill.json").exists()


def test_candidate_copy_is_hash_verified_and_bounded_to_declared_paths(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    restored = tmp_path / "restored"
    source.mkdir()
    restored.mkdir()
    (source / "nested").mkdir()
    (source / "nested/data.txt").write_text("payload\n", encoding="utf-8")
    monkeypatch.setattr(
        restore,
        "_candidate_paths",
        lambda _root: ["nested/data.txt"],
    )

    payload = restore._copy_candidate(source, restored)

    assert payload["missing"] == []
    assert payload["symlinks"] == []
    assert payload["copied"][0]["path"] == "nested/data.txt"
    assert (restored / "nested/data.txt").read_text(encoding="utf-8") == "payload\n"


def test_restore_rejects_unknown_source_mode(tmp_path):
    try:
        restore.run_restore_drill(tmp_path, "2026-07-13", source_mode="unknown")
    except restore.KnowledgeHubError as exc:
        assert "candidate or head" in str(exc)
    else:
        raise AssertionError("unknown restore source mode was accepted")


def test_restore_runtime_preserves_virtualenv_symlink_path(tmp_path, monkeypatch):
    target = tmp_path / "python-base"
    target.write_text("runtime", encoding="utf-8")
    runtime = tmp_path / "venv" / "bin" / "python"
    runtime.parent.mkdir(parents=True)
    runtime.symlink_to(target)
    monkeypatch.setattr(restore.sys, "executable", str(runtime))

    assert restore._restore_runtime() == str(runtime)
