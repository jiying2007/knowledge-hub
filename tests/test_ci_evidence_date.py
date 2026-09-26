"""Keep producer/consumer as-of dates identical across UTC midnight."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/quality.yml"
RESTORE_STEP = "Verify remote checkout in an offsite runner"
PRODUCT_STEP = "Assess product readiness (non-terminal)"


def _steps():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["engineering"]["steps"]


def test_date_is_frozen_before_evidence_and_consumed_explicitly():
    steps = _steps()
    names = [step["name"] for step in steps]
    freeze = names.index("Freeze evidence evaluation date")
    assert freeze < names.index("Run full engineering gate")
    assert sum("date -u +%F" in step.get("run", "") for step in steps) == 1
    for name in (RESTORE_STEP, PRODUCT_STEP):
        command = steps[names.index(name)]["run"]
        assert '--as-of "${KNOWLEDGE_CI_AS_OF:?}"' in command
        assert "date " not in command


@pytest.mark.parametrize("frozen,later", [
    ("2026-09-24", "2026-09-25"), ("2026-12-31", "2027-01-01"),
])
def test_actual_shell_commands_reuse_the_date_after_midnight(tmp_path, frozen, later):
    steps = {step["name"]: step for step in _steps()}
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    date = bin_dir / "date"
    date.write_text('#!/bin/sh\ntest "$1" = -u && test "$2" = +%F || exit 5\nprintf "%s\\n" "$FAKE_DATE"\n', encoding="utf-8")
    date.chmod(0o755)
    capture = bin_dir / "rtk"
    capture.write_text(
        "#!" + sys.executable + "\nimport json,os,sys\n"
        "with open(os.environ['CAPTURE'], 'a', encoding='utf-8') as f:\n"
        "    f.write(json.dumps(sys.argv[1:]) + '\\n')\n",
        encoding="utf-8",
    )
    capture.chmod(0o755)
    env_file, output = tmp_path / "env", tmp_path / "calls.jsonl"
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"],
               GITHUB_ENV=str(env_file), FAKE_DATE=frozen, CAPTURE=str(output))
    subprocess.run(["bash", "-eu", "-c", steps["Freeze evidence evaluation date"]["run"]],
                   check=True, env=env, timeout=5)
    key, value = env_file.read_text(encoding="utf-8").strip().split("=", 1)
    assert (key, value) == ("KNOWLEDGE_CI_AS_OF", frozen)
    env.update({key: value, "FAKE_DATE": later})
    for name in (RESTORE_STEP, PRODUCT_STEP):
        subprocess.run(["bash", "-eu", "-c", steps[name]["run"]], check=True, env=env, timeout=5)
    calls = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(calls) == 2
    assert [call[call.index("--as-of") + 1] for call in calls] == [frozen, frozen]


@pytest.mark.parametrize("name", [RESTORE_STEP, PRODUCT_STEP])
def test_missing_frozen_date_fails_before_running_any_consumer(tmp_path, name):
    env = dict(os.environ)
    env.pop("KNOWLEDGE_CI_AS_OF", None)
    command = next(step["run"] for step in _steps() if step["name"] == name)
    result = subprocess.run(["bash", "-eu", "-c", command], env=env,
                            capture_output=True, text=True, timeout=5)
    assert result.returncode != 0
    assert "KNOWLEDGE_CI_AS_OF" in result.stderr
