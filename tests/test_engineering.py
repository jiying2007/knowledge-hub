import pathlib

from tools.codex_assets.knowledge_hub import engineering
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.engineering import evaluate_engineering_contract


def test_repository_engineering_contract_is_complete():
    payload = evaluate_engineering_contract(repository_root())

    assert payload["status"] == "pass"
    assert payload["python_support"]["minimum"] == ""
    assert payload["python_support"]["requires_python"] == ""
    assert payload["python_support"]["selection_policy"] == "capability-based"
    assert payload["python_support"]["ci_versions"] == [
        "3.8",
        "3.9",
        "3.10",
        "3.11",
        "3.12",
        "3.13",
        "3.14",
    ]
    assert payload["dependencies"]["runtime_direct"] == {
        "jsonschema": "4.23.0",
        "pyyaml": "6.0.3",
        "tomli": "2.4.1",
    }
    assert payload["dependencies"]["build_backend"] == {"setuptools": "83.0.0"}
    assert payload["locks"]["requirements-runtime.lock"]["hash_complete"] is True
    assert payload["locks"]["requirements-dev.lock"]["hash_complete"] is True
    assert payload["locks"]["requirements-runtime.lock"]["direct_version_mismatches"] == []
    assert payload["locks"]["requirements-dev.lock"]["direct_version_mismatches"] == []
    assert payload["ci"]["all_actions_sha_pinned"] is True
    assert payload["ci"]["least_privilege_permissions"] is True
    assert payload["ci"]["dangerous_pull_request_target"] is False
    assert payload["ci"]["all_run_steps_governed"] is True
    assert payload["recovery_workflow"]["quarterly_schedule"] is True
    assert payload["recovery_workflow"]["evidence_retention_days"] == 90
    assert payload["ci_transport"]["exact_wrapper_allowlist"] is True
    assert payload["ci_transport"]["runner_path_boundary"] is True
    assert payload["dependabot"]["ecosystems"] == ["github-actions", "pip"]


def test_coverage_omits_ephemeral_regression_fixture_from_any_restore_root():
    pyproject = engineering.tomllib.loads(
        (repository_root() / "pyproject.toml").read_text(encoding="utf-8")
    )
    expected = [
        "*/tools/codex_assets/knowledge_hub/regression_fixture_cli.py"
    ]

    assert pyproject["tool"]["coverage"]["run"]["omit"] == expected
    assert pyproject["tool"]["coverage"]["report"]["omit"] == expected


def test_engineering_contract_rejects_mutable_action_ref(tmp_path):
    _write_minimal_contract(tmp_path)
    workflow = tmp_path / ".github/workflows/quality.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd",
            "actions/checkout@v6",
        ),
        encoding="utf-8",
    )

    payload = evaluate_engineering_contract(tmp_path)

    assert payload["status"] == "fail"
    assert payload["ci"]["all_actions_sha_pinned"] is False
    assert any("full commit SHA" in error for error in payload["errors"])


def test_engineering_contract_rejects_unhashed_lock_entry(tmp_path):
    _write_minimal_contract(tmp_path)
    lock = tmp_path / "requirements-runtime.lock"
    lock.write_text("PyYAML==6.0.3\n", encoding="utf-8")

    payload = evaluate_engineering_contract(tmp_path)

    assert payload["status"] == "fail"
    assert payload["locks"]["requirements-runtime.lock"]["hash_complete"] is False


def test_engineering_quality_preserves_virtualenv_interpreter_symlink(tmp_path, monkeypatch):
    target = tmp_path / "python-base"
    target.write_text("base", encoding="utf-8")
    virtualenv_python = tmp_path / "venv" / "bin" / "python"
    virtualenv_python.parent.mkdir(parents=True)
    virtualenv_python.symlink_to(target)
    monkeypatch.setattr(engineering.sys, "executable", str(virtualenv_python))

    assert engineering._current_python_executable() == str(virtualenv_python)


def test_engineering_snapshot_is_private_and_atomic(tmp_path):
    payload = {
        "status": "pass",
        "mode": "full",
        "candidate_integrity": {
            "unchanged": True,
            "before_signature": "sig",
            "after_signature": "sig",
        },
    }

    relative = engineering._write_engineering_snapshot(tmp_path, payload)
    path = tmp_path / relative

    assert relative == ".cache/knowledge-hub/engineering-quality.json"
    assert path.is_file()
    assert path.stat().st_mode & 0o777 == 0o600


def test_quality_command_retries_and_preserves_attempt_evidence(tmp_path, monkeypatch):
    results = iter(
        [
            {
                "command": "rtk regression",
                "exit_code": 1,
                "stdout": '{"status":"fail","failure_ids":["flaky-fixture"]}\n',
                "stderr": "",
                "duration_sec": 1.2,
            },
            {
                "command": "rtk regression",
                "exit_code": 0,
                "stdout": '{"status":"pass","failure_ids":[]}\n',
                "stderr": "",
                "duration_sec": 1.0,
            },
        ]
    )

    monkeypatch.setattr(engineering, "run_rtk", lambda *args, **kwargs: next(results))

    payload = engineering._run_quality_command(
        tmp_path,
        ("python", "-m", "regression"),
        10,
        max_attempts=2,
        retry_exit_codes=(1,),
    )

    assert payload["status"] == "pass"
    assert payload["attempt_count"] == 2
    assert payload["recovered_after_retry"] is True
    assert payload["attempts"][0]["status"] == "fail"
    assert payload["attempts"][0]["stdout_tail"] == [
        '{"status":"fail","failure_ids":["flaky-fixture"]}'
    ]
    assert payload["attempts"][1]["status"] == "pass"


def test_quality_command_fails_after_retry_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(
        engineering,
        "run_rtk",
        lambda *args, **kwargs: {
            "command": "rtk regression",
            "exit_code": 1,
            "stdout": '{"status":"fail"}\n',
            "stderr": "",
            "duration_sec": 1.0,
        },
    )

    payload = engineering._run_quality_command(
        tmp_path,
        ("python", "-m", "regression"),
        10,
        max_attempts=2,
        retry_exit_codes=(1,),
    )

    assert payload["status"] == "fail"
    assert payload["attempt_count"] == 2
    assert payload["recovered_after_retry"] is False
    assert [attempt["status"] for attempt in payload["attempts"]] == ["fail", "fail"]


def test_coverage_report_recollection_recovers_and_preserves_initial_evidence(tmp_path, monkeypatch):
    calls = []

    def fake_run(root, command, timeout, **kwargs):
        calls.append(tuple(command))
        return {
            "status": "pass",
            "command": " ".join(command),
            "duration_sec": 1.0,
            "stdout_tail": ["TOTAL 78%"],
            "stderr_tail": [],
        }

    monkeypatch.setattr(engineering, "_run_quality_command", fake_run)
    initial = {"status": "fail", "error": "first coverage report failed"}
    payload = engineering._recover_coverage_report(tmp_path, "python", initial)

    assert payload["status"] == "pass"
    assert payload["recovered_after_recollection"] is True
    assert payload["initial"] == initial
    assert payload["diagnostic"]["status"] == "pass"
    assert list(payload["recollection"]) == [
        "coverage_erase",
        "coverage",
        "full_regression",
        "coverage_combine",
        "coverage_report",
    ]
    assert calls[0] == ("python", "-m", "coverage", "report", "--fail-under=0")
    assert calls[-1] == ("python", "-m", "coverage", "report")


def test_coverage_report_recollection_remains_fail_closed(tmp_path, monkeypatch):
    def fake_run(root, command, timeout, **kwargs):
        if tuple(command) == ("python", "-m", "coverage", "report"):
            return {
                "status": "fail",
                "attempt_count": 1,
                "recovered_after_retry": False,
                "attempts": [{"attempt": 1, "status": "fail"}],
                "error": "coverage threshold still failed",
            }
        return {
            "status": "pass",
            "command": " ".join(command),
            "duration_sec": 1.0,
            "stdout_tail": [],
            "stderr_tail": [],
        }

    monkeypatch.setattr(engineering, "_run_quality_command", fake_run)
    payload = engineering._recover_coverage_report(
        tmp_path,
        "python",
        {"status": "fail", "error": "first coverage report failed"},
    )

    assert payload["status"] == "fail"
    assert payload["recovered_after_recollection"] is False
    assert payload["recollection"]["coverage_report"]["status"] == "fail"
    assert payload["error"] == "coverage report failed after one full recollection"


def _write_minimal_contract(root: pathlib.Path) -> None:
    (root / ".github/workflows").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        """[build-system]
requires = ["setuptools==83.0.0"]
build-backend = "setuptools.build_meta"

[project]
dependencies = [
  "PyYAML==6.0.3",
  "jsonschema==4.23.0",
  "tomli==2.4.1; python_version < '3.11'",
]
""",
        encoding="utf-8",
    )
    (root / "requirements-runtime.txt").write_text(
        "PyYAML==6.0.3\njsonschema==4.23.0\ntomli==2.4.1; python_version < '3.11'\n",
        encoding="utf-8",
    )
    (root / "requirements-dev.txt").write_text(
        "-r requirements-runtime.txt\npytest==9.1.1\nsetuptools==83.0.0\n",
        encoding="utf-8",
    )
    hashed = "package==1.0 --hash=sha256:" + "a" * 64 + "\n"
    (root / "requirements-runtime.lock").write_text(hashed, encoding="utf-8")
    (root / "requirements-dev.lock").write_text(hashed, encoding="utf-8")
    (root / ".github/workflows/quality.yml").write_text(
        """name: quality
on: [push, pull_request]
permissions:
  contents: read
jobs:
  runtime:
    strategy:
      matrix:
        python-version: ["3.8", "3.9"]
  test:
    timeout-minutes: 30
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13", "3.14"]
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd
        with: {persist-credentials: false}
      - uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405
      - run: tools/ci/rtk bash tools/ci/bootstrap-path.sh
      - run: rtk python -m pip install --require-hashes -r requirements-dev.lock
      - run: rtk python -m pytest
      - run: rtk bash tools/knowledge-check.sh --dry-run
      - run: rtk bash tools/knowledge-retrieval-benchmark.sh --json
      - run: rtk bash tools/knowledge-regression.sh --suite full --json
      - run: python -m pip_audit --require-hashes -r requirements-runtime.lock
""",
        encoding="utf-8",
    )
    (root / ".github/workflows/recovery-drill.yml").write_text(
        """name: quarterly-recovery-drill
on:
  schedule:
    - cron: "23 3 1 */3 *"
  workflow_dispatch:
permissions:
  contents: read
jobs:
  recover:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd
        with: {persist-credentials: false}
      - uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405
      - run: tools/ci/rtk bash tools/ci/bootstrap-path.sh
      - run: rtk python -m pip install --require-hashes -r requirements-dev.lock
      - run: rtk bash tools/knowledge-restore-drill.sh --source-mode head --summary-json
      - run: rtk bash tools/knowledge-final-gate.sh --final-profile product --summary-json
      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a
        with: {retention-days: 90}
""",
        encoding="utf-8",
    )
    (root / ".github/dependabot.yml").write_text(
        """version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule: {interval: monthly}
  - package-ecosystem: github-actions
    directory: /
    schedule: {interval: monthly}
""",
        encoding="utf-8",
    )
    (root / "tools/ci").mkdir(parents=True)
    (root / "tools/ci/rtk").write_text(
        "tools/ci/bootstrap-path.sh|tools/knowledge-check.sh|tools/knowledge-regression.sh|"
        "tools/knowledge-retrieval-benchmark.sh\n",
        encoding="utf-8",
    )
    (root / "tools/ci/bootstrap-path.sh").write_text(
        '"$RUNNER_TEMP"/_runner_file_commands/*\n'
        '! -f "$GITHUB_PATH"\n'
        '-L "$GITHUB_PATH"\n'
        '"$GITHUB_WORKSPACE/tools/ci"\n',
        encoding="utf-8",
    )
