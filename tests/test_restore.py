import hashlib
import json
import os
import subprocess
import sys

import pytest

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


def _unit_target(root, *, passes=True):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'tests').mkdir()
    (root / 'tests/test_unit.py').write_text('def test_unit():\n    assert {}\n'.format(passes), encoding='utf-8')
    (root / 'README.md').write_text('restore fixture\n', encoding='utf-8')
    (root / '.gitignore').write_text('.tmp/\n.cache/\n.pytest_cache/\n__pycache__/\nignored_input.py\n', encoding='utf-8')
    subprocess.run(['rtk', 'git', 'init', '-q'], cwd=root, check=True, capture_output=True)
    return [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider']


def _unit_env():
    return {'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1', 'PYTHONDONTWRITEBYTECODE':'1',
            'KNOWLEDGE_FINAL_GATE_INNER_REGRESSION':'0'}


def test_successful_restored_unit_run_retains_actual_attempt_and_target_receipt(tmp_path):
    from tools.codex_assets.knowledge_hub.unit_evidence import UNIT_RECEIPT, verified_parent_unit
    from tools.codex_assets.knowledge_hub.check_dependencies import dependency_fingerprints

    command = _unit_target(tmp_path / 'restored')
    target = tmp_path / 'restored'
    source = restore.working_tree_signature(target)
    kernel = dependency_fingerprints(target)['kernel']
    result = restore._run_restored_unit_check(target, command, _unit_env())
    receipt = json.loads((target / UNIT_RECEIPT).read_text())
    assert result['status'] == 'pass' and result['attempt_count'] == 1
    assert receipt == result['parent_unit_evidence']
    assert receipt['source_signature'] == source and receipt['test_set_sha256'] == kernel
    actual = receipt['result']
    assert actual['attempts'][0]['exit_code'] == 0 and actual['attempts'][0]['status'] == 'pass'
    assert '-m pytest -q' in actual['command']
    assert receipt['result_sha256'] == hashlib.sha256(json.dumps(actual, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert verified_parent_unit(target)['run_id'] == receipt['run_id']
    assert not (tmp_path / UNIT_RECEIPT).exists()


@pytest.mark.parametrize('exit_kind', ['failed-pytest', 'exit77'])
def test_failed_or_delegated_restored_unit_never_records_pass(tmp_path, monkeypatch, exit_kind):
    from tools.codex_assets.knowledge_hub.unit_evidence import UNIT_RECEIPT

    command = _unit_target(tmp_path, passes=False)
    if exit_kind == 'exit77':
        command = [sys.executable, '-c', 'import sys; sys.exit(77)']
    def forbidden(*args, **kwargs):
        pytest.fail('failed or delegated unit cannot be attested')
    monkeypatch.setattr(restore, 'record_parent_unit', forbidden)
    result = restore._run_restored_unit_check(tmp_path, command, _unit_env())
    assert result['status'] == 'fail' and result['attempt_count'] == 1
    assert result['attempts'][0]['status'] == 'fail'
    assert not (tmp_path / UNIT_RECEIPT).exists()


@pytest.mark.parametrize('changed', ['source', 'ignored-kernel'])
def test_successful_runner_with_changed_inputs_cannot_write_pass_receipt(tmp_path, monkeypatch, changed):
    from tools.codex_assets.knowledge_hub.unit_evidence import UNIT_RECEIPT

    command = _unit_target(tmp_path)
    path = tmp_path / ('README.md' if changed == 'source' else 'ignored_input.py')
    path.write_text('before = 1\n', encoding='utf-8')
    source_before = restore.working_tree_signature(tmp_path)
    real_run = restore.run_rtk
    def mutate_after_actual_run(root, command, **kwargs):
        result = real_run(root, command, **kwargs)
        path.write_text('after = 2\n', encoding='utf-8')
        return result
    monkeypatch.setattr(restore, 'run_rtk', mutate_after_actual_run)
    result = restore._run_restored_unit_check(tmp_path, command, _unit_env())
    assert result['status'] == 'fail' and result['attempts'][0]['exit_code'] == 0
    assert 'inputs changed' in result['parent_unit_evidence_error']
    assert not (tmp_path / UNIT_RECEIPT).exists()
    if changed == 'ignored-kernel':
        assert restore.working_tree_signature(tmp_path) == source_before


def test_actual_timeout_cannot_register_restored_unit_pass(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub.bounded_process import run_bounded
    from tools.codex_assets.knowledge_hub.unit_evidence import UNIT_RECEIPT

    _unit_target(tmp_path)
    def timed_out(*args, **kwargs):
        return run_bounded([sys.executable, '-c', 'import time; time.sleep(2)'],
                           cwd=tmp_path, env=os.environ.copy(), timeout=.05)
    monkeypatch.setattr(restore, 'run_rtk', timed_out)
    with pytest.raises(subprocess.TimeoutExpired):
        restore._run_restored_unit_check(tmp_path, [sys.executable], _unit_env())
    assert not (tmp_path / UNIT_RECEIPT).exists()


def test_restored_parent_proof_is_rechecked_after_downstream_input_change(tmp_path):
    from tools.codex_assets.knowledge_hub.unit_evidence import verified_parent_unit

    command = _unit_target(tmp_path)
    result = restore._run_restored_unit_check(tmp_path, command, _unit_env())
    assert result['status'] == 'pass' and verified_parent_unit(tmp_path)
    (tmp_path / 'tests/test_unit.py').write_text('def test_changed():\n    assert False\n', encoding='utf-8')
    assert verified_parent_unit(tmp_path) is None


def test_restore_check_sequence_registers_target_proof_before_product_smoke(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub.unit_evidence import verified_parent_unit

    target = tmp_path / 'restored'
    command = _unit_target(target)
    monkeypatch.setattr(restore, '_restore_commands', lambda *args: {
        'unit_tests':command, 'product_gate_smoke':['fixture-smoke'],
    })
    actual_check = restore._run_restore_check
    def check_with_smoke(root, arguments, command_env, **kwargs):
        assert root == target
        if arguments == command:
            assert command_env['KNOWLEDGE_FINAL_GATE_INNER_REGRESSION'] == '0'
            return actual_check(root, arguments, command_env, **kwargs)
        assert command_env['KNOWLEDGE_FINAL_GATE_INNER_REGRESSION'] == '1'
        proof = verified_parent_unit(root)
        assert proof is not None
        return {'status':'pass', 'used_run_id':proof['run_id']}
    monkeypatch.setattr(restore, '_run_restore_check', check_with_smoke)
    checks = restore._run_restore_checks(target, '2026-10-09', _unit_env())
    assert checks['unit_tests']['status'] == checks['product_gate_smoke']['status'] == 'pass'
    assert checks['unit_tests']['parent_unit_evidence']['run_id'] == checks['product_gate_smoke']['used_run_id']
