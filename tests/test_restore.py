import subprocess

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
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv(
        "GITHUB_WORKFLOW_REF",
        "team/knowledge-hub/.github/workflows/recovery-drill.yml@refs/heads/main",
    )
    monkeypatch.setenv("GITHUB_WORKFLOW_SHA", revision)
    monkeypatch.setenv("RUNNER_ENVIRONMENT", "github-hosted")

    payload = restore._execution_environment(
        "head",
        revision,
        "team/knowledge-hub",
    )

    assert payload["remote_checkout_verified"] is True
    assert payload["remote_published_ref_verified"] is True
    assert payload["offsite_environment_verified"] is True
    assert restore._execution_environment(
        "candidate",
        revision,
        "team/knowledge-hub",
    )[
        "remote_checkout_verified"
    ] is False


def test_restore_v4_schema_strictly_validates_execution_environment():
    revision = "a" * 40
    environment = {
        "provider": "local",
        "repository": "",
        "expected_repository": "team/knowledge-hub",
        "revision": "",
        "event": "",
        "ref": "",
        "runner_environment": "",
        "run_id": "",
        "run_attempt": "",
        "workflow_ref": "",
        "workflow_sha": "",
        "remote_checkout_verified": False,
        "remote_published_ref_verified": False,
        "offsite_environment_verified": False,
        "trust_contract": "github-hosted-matching-revision-current-run-v1",
    }
    environment["evidence_sha256"] = restore.execution_environment_evidence(
        "candidate",
        revision,
        expected_repository="team/knowledge-hub",
        environment={},
    )["evidence_sha256"]
    payload = {
        "schema_version": 4,
        "status": "pass",
        "source_mode": "candidate",
        "source_revision": revision,
        "candidate_signature": "b" * 64,
        "execution_environment": environment,
        "evidence_matches_current_execution": False,
        "remote_checkout_verified": False,
        "remote_published_ref_verified": False,
        "offsite_environment_verified": False,
        "checks": {},
        "cache_included": False,
        "local_workspace_mapping_included": False,
    }

    assert validate_instance(
        repository_root(), "restore-drill-v4", payload
    )["status"] == "pass"

    invalid_provider = dict(payload)
    invalid_provider["execution_environment"] = dict(
        environment, provider="untrusted-runner"
    )
    assert validate_instance(
        repository_root(), "restore-drill-v4", invalid_provider
    )["status"] == "fail"

    unexpected_field = dict(payload)
    unexpected_field["execution_environment"] = dict(
        environment, compatibility_fallback=True
    )
    assert validate_instance(
        repository_root(), "restore-drill-v4", unexpected_field
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


def test_restore_check_environment_rebinds_complexity_baseline_to_scratch_head(
    tmp_path,
):
    (tmp_path / "tracked.txt").write_text("payload\n", encoding="utf-8")
    subprocess.run(
        ["git", "init", "-q"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    subprocess.run(
        ["git", "add", "tracked.txt"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Knowledge Hub Restore Drill Test",
            "-c",
            "user.email=restore-test@localhost",
            "commit",
            "-qm",
            "scratch",
        ],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()

    env = restore._restore_check_environment(
        tmp_path,
        "/tmp/knowledge-hub-python",
    )

    assert env == {
        "KNOWLEDGE_PYTHON_RUNTIME": "/tmp/knowledge-hub-python",
        "KNOWLEDGE_COMPLEXITY_ENFORCE_BASELINE": "true",
        "KNOWLEDGE_COMPLEXITY_BASE_REF": head,
    }


def test_restore_runtime_preserves_virtualenv_symlink_path(tmp_path, monkeypatch):
    target = tmp_path / "python-base"
    target.write_text("runtime", encoding="utf-8")
    runtime = tmp_path / "venv" / "bin" / "python"
    runtime.parent.mkdir(parents=True)
    runtime.symlink_to(target)
    monkeypatch.setattr(restore.sys, "executable", str(runtime))

    assert restore._restore_runtime() == str(runtime)


def test_restore_check_retries_retrieval_and_preserves_attempts(
    tmp_path, monkeypatch
):
    results = iter(
        [
            {
                "command": "rtk retrieval",
                "exit_code": 1,
                "stdout": '{"status":"fail","failures":["p95"]}\n',
                "stderr": "",
                "duration_sec": 1.0,
            },
            {
                "command": "rtk retrieval",
                "exit_code": 0,
                "stdout": '{"status":"pass","failures":[]}\n',
                "stderr": "",
                "duration_sec": 0.8,
            },
        ]
    )
    monkeypatch.setattr(restore, "run_rtk", lambda *args, **kwargs: next(results))

    payload = restore._run_restore_check(
        tmp_path,
        ["bash", "tools/knowledge-retrieval-benchmark.sh", "--json"],
        {},
        max_attempts=2,
    )

    assert payload["status"] == "pass"
    assert payload["attempt_count"] == 2
    assert payload["recovered_after_retry"] is True
    assert payload["attempts"][0]["status"] == "fail"
    assert payload["attempts"][0]["stdout_tail"] == [
        '{"status":"fail","failures":["p95"]}'
    ]
    assert payload["attempts"][1]["status"] == "pass"


def test_restore_check_fails_when_retry_budget_is_exhausted(tmp_path, monkeypatch):
    monkeypatch.setattr(
        restore,
        "run_rtk",
        lambda *args, **kwargs: {
            "command": "rtk retrieval",
            "exit_code": 1,
            "stdout": '{"status":"fail"}\n',
            "stderr": "",
            "duration_sec": 1.0,
        },
    )

    payload = restore._run_restore_check(
        tmp_path,
        ["bash", "tools/knowledge-retrieval-benchmark.sh", "--json"],
        {},
        max_attempts=2,
    )

    assert payload["status"] == "fail"
    assert payload["attempt_count"] == 2
    assert payload["recovered_after_retry"] is False
    assert [attempt["status"] for attempt in payload["attempts"]] == [
        "fail",
        "fail",
    ]
