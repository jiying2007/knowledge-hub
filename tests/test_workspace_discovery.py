import json
import pathlib

from tools.codex_assets.knowledge_hub.workspace_discovery import discover_workspaces


def _repository(path: pathlib.Path, remote: str, head: str = "a" * 40) -> None:
    git_dir = path / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "refs/heads").mkdir(parents=True)
    (git_dir / "config").write_text(
        '[remote "origin"]\n\turl = {}\n'.format(remote),
        encoding="utf-8",
    )
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="ascii")
    (git_dir / "refs/heads/main").write_text(head + "\n", encoding="ascii")


def _hub(path: pathlib.Path) -> pathlib.Path:
    (path / "registry").mkdir(parents=True)
    (path / "registry/items.jsonl").write_text("", encoding="utf-8")
    (path / "registry/repositories.json").write_text(
        json.dumps(
            {
                "repositories": [
                    {
                        "repo_id": "sample",
                        "project_id": "sample",
                        "remote_key": "team/sample",
                        "workspace_ref": "workspace://sample",
                        "lifecycle": "first-party",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def test_discovery_matches_remote_and_extracts_local_source_evidence(tmp_path):
    hub = _hub(tmp_path / "hub")
    source = tmp_path / "work/sample"
    _repository(source, "git@example.invalid:team/sample.git")
    (source / "README.md").write_text("sample\n", encoding="utf-8")
    (source / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")

    payload = discover_workspaces(hub, [tmp_path / "work"], maximum_depth=4)

    assert payload["matched_remote_count"] == 1
    assert payload["unmatched_remote_count"] == 0
    row = payload["workspaces"][0]
    assert row["path"] == str(source)
    assert row["source_evidence"]["readme_entries"] == ["README.md"]
    assert row["source_evidence"]["build_entries"] == ["pyproject.toml"]
    assert row["source_evidence"]["git_head"] == "a" * 40
    assert payload["transaction"]["changed_paths"] == ["local/workspaces.json"]


def test_discovery_prefers_work_path_and_reports_alternates(tmp_path):
    hub = _hub(tmp_path / "hub")
    release = tmp_path / "sample_release"
    working = tmp_path / "work/sample"
    _repository(release, "https://example.invalid/team/sample.git")
    _repository(working, "ssh://git@example.invalid/team/sample.git")

    payload = discover_workspaces(hub, [tmp_path], maximum_depth=4)

    row = payload["workspaces"][0]
    assert row["path"] == str(working)
    assert row["alternate_count"] == 1
    assert row["alternate_paths"] == [str(release)]
    assert payload["duplicate_remote_keys"] == ["team/sample"]


def test_discovery_apply_is_transactional_and_idempotent(tmp_path):
    hub = _hub(tmp_path / "hub")
    source = tmp_path / "work/sample"
    _repository(source, "git@example.invalid:team/sample.git")

    first = discover_workspaces(hub, [tmp_path / "work"], maximum_depth=4, apply=True)
    second = discover_workspaces(hub, [tmp_path / "work"], maximum_depth=4, apply=True)

    assert first["status"] == "applied"
    assert second["status"] == "no-change"
    local = json.loads((hub / "local/workspaces.json").read_text(encoding="utf-8"))
    assert local["tracked"] is False
    assert local["workspaces"][0]["remote_key"] == "team/sample"
