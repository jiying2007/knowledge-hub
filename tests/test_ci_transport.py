import os
import shutil
import subprocess

from tools.codex_assets.knowledge_hub.common import repository_root


ROOT = repository_root()
RTK = ROOT / "tools/ci/rtk"


def _run(*args, extra_env=None):
    environment = os.environ.copy()
    if extra_env:
        environment.update(extra_env)
    return subprocess.run(
        [str(RTK), *args],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
        check=False,
        env=environment,
    )


def test_ci_transport_accepts_exact_resolved_allowlisted_python():
    python = shutil.which("python3")
    assert python
    resolved = os.path.realpath(python)

    result = _run(resolved, "-c", "print('runtime-ok')")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "runtime-ok"


def test_ci_transport_rejects_unrelated_absolute_command():
    echo = shutil.which("echo") or "/bin/echo"
    result = _run(os.path.realpath(echo), "not-allowed")

    assert result.returncode == 64
    assert "denied command" in result.stderr


def test_ci_transport_allows_registered_path_audit_wrapper():
    result = _run("bash", "tools/knowledge-path-audit.sh", "--help")

    assert result.returncode == 0, result.stderr


def test_ci_transport_allows_governed_runtime_selector():
    result = _run(
        "bash",
        "tools/ci/python-runtime.sh",
        "-c",
        "print('selector-ok')",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "selector-ok"


def test_ci_transport_rejects_unregistered_internal_ci_wrapper():
    result = _run("bash", "tools/ci/not-registered.sh", "--help")

    assert result.returncode == 64
    assert "denied wrapper: tools/ci/not-registered.sh" in result.stderr


def test_ci_transport_allows_bounded_read_only_directory_probe():
    result = _run("bash", "-lc", "test -d tools/codex_assets/knowledge_hub")

    assert result.returncode == 0, result.stderr


def test_ci_transport_rejects_generic_bash_lc():
    result = _run("bash", "-lc", "echo should-not-run")

    assert result.returncode == 64
    assert "denied bash -lc command" in result.stderr
    assert "should-not-run" not in result.stdout


def test_ci_transport_rejects_final_gate_shell_injection():
    command = (
        "KNOWLEDGE_FINAL_GATE_INNER_REGRESSION=1 "
        "rtk bash tools/knowledge-final-gate.sh --json ; echo injected"
    )
    result = _run("bash", "-lc", command)

    assert result.returncode == 64
    assert "denied unsafe final-gate regression arguments" in result.stderr
    assert "injected" not in result.stdout


def test_ci_transport_skips_only_recursive_final_gate_pytest():
    result = _run(
        "python3",
        "-m",
        "pytest",
        "-q",
        extra_env={"KNOWLEDGE_FINAL_GATE_INNER_REGRESSION": "1"},
    )

    assert result.returncode == 0, result.stderr
    assert "nested final-gate pytest skipped" in result.stdout
