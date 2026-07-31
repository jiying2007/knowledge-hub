import os
import pathlib
import shlex
import shutil
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


def test_runtime_selector_uses_lightweight_dependency_discovery():
    selector = (ROOT / "tools/ci/python-runtime.sh").read_text(encoding="utf-8")

    assert "importlib.util.find_spec" in selector
    assert "import sys, yaml, jsonschema" not in selector


def test_runtime_selector_reuses_validated_cache_for_public_modules(tmp_path):
    fixture_root = tmp_path / "repo"
    fixture_selector = fixture_root / "tools/ci/python-runtime.sh"
    fixture_selector.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "tools/ci/python-runtime.sh", fixture_selector)
    (fixture_root / "requirements-runtime.lock").write_text(
        "fixture lock\n",
        encoding="utf-8",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    trace = tmp_path / "rtk-trace"
    real_rtk = shutil.which("rtk")
    assert real_rtk
    fake_rtk = fake_bin / "rtk"
    fake_rtk.write_text(
        "#!/usr/bin/env bash\n"
        'printf "call\\n" >> "$RTK_TRACE_FILE"\n'
        f"exec {shlex.quote(real_rtk)} \"$@\"\n",
        encoding="utf-8",
    )
    fake_rtk.chmod(0o755)
    env = dict(os.environ)
    env["KNOWLEDGE_PYTHON_RUNTIME"] = sys.executable
    env["PYTHONPATH"] = str(ROOT)
    env["PATH"] = str(fake_bin) + os.pathsep + env["PATH"]
    env["RTK_TRACE_FILE"] = str(trace)
    command = [
        "bash",
        str(fixture_selector),
        "-m",
        "tools.codex_assets.knowledge_hub.search_cli",
        "--help",
    ]

    first = subprocess.run(
        command,
        cwd=str(fixture_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
        check=False,
    )

    assert first.returncode == 0, first.stderr
    cache = fixture_root / ".cache/knowledge-hub/python-runtime-selection-v1"
    assert cache.is_file()
    assert cache.read_text(encoding="utf-8").splitlines() == [
        sys.executable,
        "{}.{}".format(sys.version_info.major, sys.version_info.minor),
    ]

    trace.write_text("", encoding="utf-8")
    second = subprocess.run(
        command,
        cwd=str(fixture_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
        check=False,
    )

    assert second.returncode == 0, second.stderr
    assert trace.read_text(encoding="utf-8").splitlines() == ["call"]
