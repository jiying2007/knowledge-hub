import os
import pathlib
import shutil
import subprocess

from tools.codex_assets.knowledge_hub.common import repository_root


ROOT = repository_root()
RTK = ROOT / "tools/ci/rtk"


def test_ci_transport_accepts_exact_resolved_allowlisted_python():
    python = shutil.which("python3")
    assert python
    resolved = os.path.realpath(python)

    result = subprocess.run(
        [str(RTK), resolved, "-c", "print('runtime-ok')"],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "runtime-ok"


def test_ci_transport_rejects_unrelated_absolute_command():
    echo = shutil.which("echo") or "/bin/echo"
    result = subprocess.run(
        [str(RTK), os.path.realpath(echo), "not-allowed"],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
        check=False,
    )

    assert result.returncode == 64
    assert "denied command" in result.stderr


def test_ci_transport_allows_registered_path_audit_wrapper():
    result = subprocess.run(
        [str(RTK), "bash", "tools/knowledge-path-audit.sh", "--help"],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
        check=False,
    )

    assert result.returncode == 0, result.stderr
