import os
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]


def _wrappers():
    return sorted((ROOT / "tools").glob("knowledge-*.sh"))


def test_all_public_wrappers_anchor_repository_cwd():
    wrappers = _wrappers()
    assert wrappers
    for wrapper in wrappers:
        text = wrapper.read_text(encoding="utf-8")
        assert 'ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"' in text
        assert '\ncd "$ROOT"\nexport PYTHONPATH=' in text
        assert 'exec "$ROOT/tools/ci/python-runtime.sh" -m ' in text


def test_wrapper_ignores_colliding_tools_package(tmp_path):
    collision = tmp_path / "tools" / "codex_assets"
    collision.mkdir(parents=True)
    (tmp_path / "tools" / "__init__.py").write_text("", encoding="utf-8")
    (collision / "__init__.py").write_text("", encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tmp_path)
    result = subprocess.run(
        ["bash", str(ROOT / "tools/knowledge-search.sh"), "--help"],
        cwd=str(tmp_path),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--rebuild-index" in result.stdout


def test_runtime_selector_accepts_absolute_injected_interpreter():
    env = dict(os.environ)
    env["KNOWLEDGE_PYTHON_RUNTIME"] = sys.executable
    result = subprocess.run(
        ["bash", str(ROOT / "tools/ci/python-runtime.sh"), "--version"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("Python 3.")


def test_runtime_selector_rejects_relative_injected_interpreter():
    env = dict(os.environ)
    env["KNOWLEDGE_PYTHON_RUNTIME"] = "python3"
    result = subprocess.run(
        ["bash", str(ROOT / "tools/ci/python-runtime.sh"), "--version"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
        check=False,
    )

    assert result.returncode == 69
    assert "must be an absolute interpreter path" in result.stderr
