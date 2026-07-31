import json
import subprocess
from pathlib import Path

from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.tool_asset_session import (
    close_tool_asset_session,
    start_tool_asset_session,
)


TOOL_TEXT = (
    '"""Reusable session helper."""\n'
    "import argparse\n"
    "import json\n"
    "parser = argparse.ArgumentParser()\n"
    'parser.add_argument("--dry-run", action="store_true")\n'
    'parser.add_argument("--json", action="store_true")\n'
)


def _run(repo: Path, *args: str):
    subprocess.run(["rtk", *args], cwd=repo, check=True, capture_output=True, text=True)


def _repo(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir()
    _run(repo, "git", "init", "-q")
    _run(repo, "git", "config", "user.name", "Tool Session Test")
    _run(repo, "git", "config", "user.email", "tool-session@example.invalid")
    (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
    _run(repo, "git", "add", "README.md")
    _run(repo, "git", "commit", "-qm", "fixture")
    return repo


def _validation():
    return {
        "unit_tests": "pass",
        "cli_help": "pass",
        "dry_run": "pass",
        "non_repo_cwd": "pass",
    }


def test_session_baseline_is_metadata_only_and_private(tmp_path):
    repo = _repo(tmp_path, "baseline-repo")
    state = repo / ".tmp/tool-assets/session.json"

    payload = start_tool_asset_session(
        repository_root(), repo, state, source_repo="xcrz-sigmastar-demo", session_id="session-one"
    )
    saved = json.loads(state.read_text(encoding="utf-8"))

    assert payload["status"] == "pass"
    assert saved["privacy"]["raw_session_stored"] is False
    assert saved["privacy"]["command_arguments_stored"] is False
    assert saved["privacy"]["environment_stored"] is False
    assert "prompt" not in saved
    assert state.stat().st_mode & 0o777 == 0o600


def test_two_sessions_promote_local_observation_to_ready(tmp_path):
    repo = _repo(tmp_path, "repeat-repo")
    ledger = tmp_path / "observations.jsonl"
    tool = repo / "codex_assets/session_helper.py"
    tool.parent.mkdir(parents=True)

    state1 = repo / ".tmp/tool-assets/session-1.json"
    start_tool_asset_session(
        repository_root(), repo, state1, source_repo="xcrz-sigmastar-demo", session_id="session-one"
    )
    tool.write_text(TOOL_TEXT, encoding="utf-8")
    first = close_tool_asset_session(
        repository_root(),
        repo,
        state1,
        repo / "tmp/tool-assets/candidate-1.md",
        ledger,
        _validation(),
    )
    assert first["hub_candidate_ready"] is False
    assert first["observation_appended_count"] == 1

    _run(repo, "git", "add", "codex_assets/session_helper.py")
    _run(repo, "git", "commit", "-qm", "add helper")
    state2 = repo / ".tmp/tool-assets/session-2.json"
    start_tool_asset_session(
        repository_root(), repo, state2, source_repo="xcrz-sigmastar-demo", session_id="session-two"
    )
    second = close_tool_asset_session(
        repository_root(),
        repo,
        state2,
        repo / "tmp/tool-assets/candidate-2.md",
        ledger,
        _validation(),
        used_paths=["codex_assets/session_helper.py"],
    )

    aggregate = next(iter(second["aggregates"].values()))
    assert second["changes"]["codex_assets/session_helper.py"] == "used-unchanged-in-session"
    assert aggregate["distinct_session_count"] == 2
    assert aggregate["distinct_project_count"] == 1
    assert aggregate["hub_candidate_ready"] is True
    assert aggregate["recommendation"] == "keep-project-tool"
    assert "recommendation: keep-project-tool" in (repo / "tmp/tool-assets/candidate-2.md").read_text(
        encoding="utf-8"
    )


def test_three_sessions_across_projects_recommend_global_codex(tmp_path):
    ledger = tmp_path / "cross-project-observations.jsonl"
    signatures = []
    cases = (
        ("repo-a", "xcrz-sigmastar-demo", "session-a"),
        ("repo-b", "xcrz-sigmastar-demo", "session-b"),
        ("repo-c", "pcr02-ssc305", "session-c"),
    )
    last = None
    for repo_name, source_repo, session_id in cases:
        repo = _repo(tmp_path, repo_name)
        state = repo / ".tmp/tool-assets/session.json"
        start_tool_asset_session(
            repository_root(), repo, state, source_repo=source_repo, session_id=session_id
        )
        tool = repo / "codex_assets/session_helper.py"
        tool.parent.mkdir(parents=True)
        tool.write_text(TOOL_TEXT, encoding="utf-8")
        last = close_tool_asset_session(
            repository_root(),
            repo,
            state,
            repo / "tmp/tool-assets/candidate.md",
            ledger,
            _validation(),
        )
        signatures.extend(last["aggregates"].keys())

    assert last is not None
    aggregate = last["aggregates"][signatures[-1]]
    assert aggregate["distinct_session_count"] == 3
    assert aggregate["distinct_project_count"] == 2
    assert aggregate["hub_candidate_ready"] is True
    assert aggregate["recommendation"] == "recommend-global-codex"
    assert "recommendation: recommend-global-codex" in (
        tmp_path / "repo-c/tmp/tool-assets/candidate.md"
    ).read_text(encoding="utf-8")


def test_observation_ledger_is_idempotent_and_hash_chained(tmp_path):
    repo = _repo(tmp_path, "ledger-repo")
    state = repo / ".tmp/tool-assets/session.json"
    ledger = tmp_path / "ledger.jsonl"
    start_tool_asset_session(
        repository_root(), repo, state, source_repo="xcrz-sigmastar-demo", session_id="stable-session"
    )
    tool = repo / "tools/session_helper.py"
    tool.parent.mkdir(parents=True)
    tool.write_text(TOOL_TEXT, encoding="utf-8")

    first = close_tool_asset_session(
        repository_root(), repo, state, repo / "tmp/candidate.md", ledger, _validation()
    )
    second = close_tool_asset_session(
        repository_root(), repo, state, repo / "tmp/candidate.md", ledger, _validation()
    )
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]

    assert first["observation_appended_count"] == 1
    assert second["observation_appended_count"] == 0
    assert len(rows) == 1
    assert rows[0]["previous_hash"] is None
    assert len(rows[0]["content_hash"]) == 64
