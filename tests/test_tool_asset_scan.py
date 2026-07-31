import json
import subprocess
from pathlib import Path

from tools.codex_assets.knowledge_hub.cli import main as shared_cli_main
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.tool_asset_scan import scan_tool_assets


def _run(repo: Path, *args: str):
    subprocess.run(["rtk", *args], cwd=repo, check=True, capture_output=True, text=True)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "source-repo"
    repo.mkdir()
    _run(repo, "git", "init", "-q")
    _run(repo, "git", "config", "user.name", "Tool Asset Test")
    _run(repo, "git", "config", "user.email", "tool-asset@example.invalid")
    (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
    _run(repo, "git", "add", "README.md")
    _run(repo, "git", "commit", "-qm", "fixture")
    return repo


def _validation():
    return {
        "unit_tests": "not-run",
        "cli_help": "not-run",
        "dry_run": "not-run",
        "non_repo_cwd": "not-run",
    }


def test_session_scan_reports_no_candidate_without_tool_changes(tmp_path):
    repo = _repo(tmp_path)
    output = repo / "tmp/session/hub-candidate.md"

    payload = scan_tool_assets(
        repository_root(), repo, output, _validation(), source_repo="xcrz-sigmastar-demo"
    )

    assert payload["status"] == "pass"
    assert payload["eligible_count"] == 0
    assert payload["hub_candidate_generated"] is False
    assert payload["archive_conclusion"] == "本次无可归档工具资产"
    assert not output.exists()


def test_session_scan_generates_dirty_hash_bound_candidate(tmp_path):
    repo = _repo(tmp_path)
    source = repo / "codex_assets/tools/session_helper.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        '"""Reusable session helper."""\n'
        "import argparse\n"
        "parser = argparse.ArgumentParser()\n"
        'parser.add_argument("--dry-run", action="store_true")\n',
        encoding="utf-8",
    )
    output = repo / "tmp/session/hub-candidate.md"

    payload = scan_tool_assets(
        repository_root(), repo, output, _validation(), source_repo="xcrz-sigmastar-demo"
    )

    assert payload["hub_candidate_generated"] is True
    assert payload["source_worktree_dirty"] is True
    assert payload["selected"]["path"] == "codex_assets/tools/session_helper.py"
    text = output.read_text(encoding="utf-8")
    assert "source_identity_verified: true" in text
    assert "source_worktree_dirty: true" in text
    assert payload["selected"]["sha256"] in text


def test_session_scan_rejects_sensitive_candidate(tmp_path):
    repo = _repo(tmp_path)
    source = repo / "tools/sensitive_helper.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        '"""Unsafe helper."""\npassword="real-secret-value"\n# --help --dry-run\n',
        encoding="utf-8",
    )

    payload = scan_tool_assets(
        repository_root(),
        repo,
        repo / "tmp/session/hub-candidate.md",
        _validation(),
        source_repo="xcrz-sigmastar-demo",
        minimum_score=0,
    )

    assert payload["hub_candidate_generated"] is False
    assert payload["inspected"][0]["reason"] == "sanitization-failed"
    assert "credential-assignment" in payload["inspected"][0]["secret_rules"]


def test_capture_scan_can_chain_hub_dry_run(tmp_path, capsys):
    repo = _repo(tmp_path)
    source = repo / "codex_assets/session_helper.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        '"""Reusable session helper."""\n'
        "import argparse\n"
        "parser = argparse.ArgumentParser()\n"
        'parser.add_argument("--dry-run", action="store_true")\n',
        encoding="utf-8",
    )
    output = repo / "tmp/session/hub-candidate.md"

    exit_code = shared_cli_main(
        [
            "capture",
            "--scan-tool-assets",
            "--repo-root",
            str(repo),
            "--hub-candidate-out",
            str(output),
            "--source-repo",
            "xcrz-sigmastar-demo",
            "--session-path",
            "codex_assets/session_helper.py",
            "--hub-dry-run",
            "--as-of",
            "2026-07-31",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["hub_candidate_generated"] is True
    assert payload["hub_plan"]["status"] == "planned"
    assert payload["hub_plan"]["active_promotion"] is False
