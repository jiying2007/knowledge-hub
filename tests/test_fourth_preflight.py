"""Use the exact engineering interpreter in the real least-capability transport."""

import os
import pathlib
import shutil
import sys

from tools.codex_assets.knowledge_hub import engineering, engineering_preflight

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _contracts_and_transport(tmp_path, monkeypatch):
    directory = tmp_path / 'tools/ci'
    directory.mkdir(parents=True)
    shutil.copy2(ROOT / 'tools/ci/rtk', directory / 'rtk')
    monkeypatch.setattr(engineering, 'evaluate_engineering_contract', lambda root:{'status':'pass'})
    monkeypatch.setattr(engineering_preflight, 'validate_schema_catalog',
        lambda root:{'status':'pass', 'errors':[]})
    interpreter = pathlib.Path(sys.executable)
    monkeypatch.setenv('PATH', str(interpreter.parent) + os.pathsep + os.environ.get('PATH', ''))
    return interpreter


def test_real_ci_preflight_rejects_mismatched_absolute_interpreter(tmp_path, monkeypatch):
    _contracts_and_transport(tmp_path, monkeypatch)
    wrong = tmp_path / 'alien/python'
    wrong.parent.mkdir()
    wrong.write_text('#!/bin/sh\nexit 0\n')
    wrong.chmod(0o755)
    monkeypatch.setattr(sys, 'executable', str(wrong))
    result = engineering_preflight.preflight(tmp_path)
    assert result['status'] == result['transport']['status'] == 'fail'
    assert 'denied absolute python' in result['transport']['error']
    assert result['expensive_checks_started'] is False


def test_real_ci_preflight_accepts_matching_active_venv(tmp_path, monkeypatch):
    interpreter = _contracts_and_transport(tmp_path, monkeypatch)
    assert engineering._current_python_executable() == os.path.abspath(str(interpreter))
    result = engineering_preflight.preflight(tmp_path)
    assert result['status'] == result['transport']['status'] == 'pass'
    assert result['transport']['exit_code'] == 0
    assert result['expensive_checks_started'] is False
