import os
import pathlib
import subprocess
import sys


def test_default_gate_diagnostic_probe():
    if os.environ.get("KNOWLEDGE_FINAL_GATE_INNER_REGRESSION") == "1":
        return
    root = pathlib.Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.codex_assets.knowledge_hub.regression_cli",
            str(root),
            "--suite",
            "full",
            "--test",
            "test_final_gate_default_regression_path",
            "--summary-json",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, (
        completed.stdout[-12000:] + "\nSTDERR:\n" + completed.stderr[-4000:]
    )
