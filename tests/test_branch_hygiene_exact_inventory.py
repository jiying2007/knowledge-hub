"""Branch hygiene must distinguish an absent ref from a moved live ref."""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess

import pytest
import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/branch-hygiene.yml"
EXPECTED_SHA = "c" * 40


def _retirement_script() -> str:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["retire"]["steps"]
    return next(step["run"] for step in steps if step.get("name") == "Retire exact registered candidates")


@pytest.mark.parametrize(
    ("scenario", "expected_success", "delete_expected"),
    (
        ("absent", True, False),
        ("moved", False, False),
        ("non-exact", False, False),
        ("api-error", False, False),
        ("exact", True, True),
    ),
)
def test_retirement_uses_exact_branch_inventory(
    tmp_path: pathlib.Path,
    scenario: str,
    expected_success: bool,
    delete_expected: bool,
) -> None:
    if not shutil.which("bash") or not shutil.which("jq"):
        pytest.skip("requires bash and jq")

    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "branch-lifecycle.json").write_text(
        json.dumps({"retirement_candidates": [
            {"branch": "archive/candidate", "expected_head": EXPECTED_SHA}
        ]}),
        encoding="utf-8",
    )
    bindir = tmp_path / "bin"
    bindir.mkdir()
    fake = bindir / "gh"
    fake.write_text(
        """#!/usr/bin/env python3
import json
import os
import pathlib
import sys

args = sys.argv[1:]
scenario = os.environ["MOCK_SCENARIO"]
if "DELETE" in args:
    pathlib.Path(os.environ["MOCK_DELETE_LOG"]).write_text("DELETE", encoding="utf-8")
elif "--paginate" in args:
    if scenario == "api-error":
        sys.exit(22)
    print("master\\t" + "a" * 40)
    if scenario in {"moved", "non-exact", "exact"}:
        print("archive/candidate\\t" + ("b" if scenario == "moved" else "c") * 40)
elif "api" in args and any("/git/ref/heads/" in value for value in args):
    if scenario == "non-exact":
        print("[]")
    else:
        print(json.dumps({
            "ref": "refs/heads/archive/candidate",
            "object": {"sha": "c" * 40},
        }))
elif "pr" in args and "list" in args:
    print("0")
else:
    sys.exit(23)
""",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    deleted = tmp_path / "deletion.log"
    env = {
        **os.environ,
        "PATH": str(bindir) + os.pathsep + os.environ.get("PATH", ""),
        "GITHUB_REPOSITORY": "jiying2007/knowledge-hub",
        "MOCK_SCENARIO": scenario,
        "MOCK_DELETE_LOG": str(deleted),
    }
    result = subprocess.run(
        ["bash", "-c", _retirement_script()],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    assert (result.returncode == 0) is expected_success, result.stdout + result.stderr
    assert deleted.exists() is delete_expected
    if scenario == "absent":
        assert "already absent: archive/candidate" in result.stdout
