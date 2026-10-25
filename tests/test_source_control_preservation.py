"""Source control scaffolding preserves subsequent evidence and refuses aliases."""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from tools.codex_assets.knowledge_hub.source_control_files import materialize_source_file


ROOT = Path(__file__).resolve().parents[1]


def _fixture(tmp_path, source_id="example", coverage=True):
    (tmp_path / "registry").mkdir()
    (tmp_path / "registry/sources.json").write_text(json.dumps({"sources": [{
        "id": source_id, "role": "hub-runtime-input", "path": "sources/example",
        "authority": "runtime-input-provenance", "owner": "test-owner",
        "review_after": "2026-10-01", "status": "registered",
    }]}), encoding="utf-8")
    if coverage:
        folder = tmp_path / "artifacts/manifests"
        folder.mkdir(parents=True)
        (folder / "knowledge-hub-source-coverage-closeout-20260624.jsonl").write_text(
            json.dumps({"source_id": "example", "decision": "Historical plan only",
                        "status": "runtime-input-control", "checked_at": "2026-06-24"}) + "\n",
            encoding="utf-8",
        )
    return tmp_path


def _run(root, *args):
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    return subprocess.run(
        [sys.executable, "-m", "tools.codex_assets.knowledge_hub.source_control_cli",
         str(root), "--json", *args], cwd=ROOT, env=env,
        capture_output=True, text=True, timeout=15, check=False,
    )


def test_apply_creates_missing_and_preserves_manual_appendix(tmp_path):
    root = _fixture(tmp_path)
    directory = root / "sources/example"
    directory.mkdir(parents=True)
    target = directory / "coverage.md"
    original = "# Preserved evidence\n\n## 2026-07-18 manual validation\nNot a synthetic approval.\n"
    target.write_text(original, encoding="utf-8")
    before_stat = target.stat()
    run = _run(root, "--apply", "--as-of", "2026-10-22")
    assert run.returncode == 0, run.stderr
    report = json.loads(run.stdout)
    assert report["written_count"] == 3
    assert report["preserved_existing_count"] == 1
    assert report["existing_files_overwritten"] is False
    assert report["existing_content_validated"] is False
    assert target.read_text(encoding="utf-8") == original
    assert target.stat().st_mtime_ns == before_stat.st_mtime_ns
    assert len(list(directory.iterdir())) == 4


def test_repeated_apply_does_not_refresh_evidence_dates(tmp_path):
    root = _fixture(tmp_path)
    first = _run(root, "--apply", "--as-of", "2026-10-21")
    assert first.returncode == 0, first.stderr
    before = {p.name: p.read_bytes() for p in (root / "sources/example").iterdir()}
    second = _run(root, "--apply", "--as-of", "2026-10-22")
    assert second.returncode == 0, second.stderr
    report = json.loads(second.stdout)
    assert report["written_count"] == 0 and report["preserved_existing_count"] == 4
    assert before == {p.name: p.read_bytes() for p in (root / "sources/example").iterdir()}


def test_plan_creates_no_directory_or_file(tmp_path):
    root = _fixture(tmp_path)
    run = _run(root)
    assert run.returncode == 1
    assert json.loads(run.stdout)["missing_count"] == 4
    assert not (root / "sources").exists()


def test_missing_coverage_manifest_is_supported_without_fabricated_results(tmp_path):
    root = _fixture(tmp_path, coverage=False)
    run = _run(root)
    assert run.returncode == 1
    report = json.loads(run.stdout)
    assert report["coverage_manifest"] == "" and report["written_count"] == 0
    assert not (root / "sources").exists()


@pytest.mark.parametrize("source_id", ["../outside", "a/b", "/tmp/x", "a\\b", "a\n", True, 9, ""])
def test_invalid_source_ids_fail_before_any_creation(tmp_path, source_id):
    root = _fixture(tmp_path, source_id=source_id)
    run = _run(root, "--apply")
    assert run.returncode == 2
    assert "invalid-source-control-id" in run.stderr
    assert not (root / "sources").exists()


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("location", ["parent", "leaf", "dangling", "fifo", "directory"])
def test_symlink_and_nonregular_targets_are_never_followed(tmp_path, apply, location):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    canary = outside / "README.md"
    canary.write_text("DO_NOT_CHANGE", encoding="utf-8")
    source = root / "sources/example"
    if location == "parent":
        (root / "sources").symlink_to(outside, target_is_directory=True)
    else:
        source.mkdir(parents=True)
        target = source / "README.md"
        if location == "leaf":
            target.symlink_to(canary)
        elif location == "dangling":
            target.symlink_to(outside / "absent.md")
        elif location == "fifo":
            os.mkfifo(target)
        else:
            target.mkdir()
    with pytest.raises(ValueError):
        materialize_source_file(root, "example", "README.md", "replacement", apply=apply)
    assert canary.read_text(encoding="utf-8") == "DO_NOT_CHANGE"
    assert not (outside / "absent.md").exists()
    assert not (outside / "example").exists()


def test_concurrent_creators_do_not_clobber_existing_result(tmp_path):
    # Use the actual filesystem, not mocked path.exists/write_text behavior.
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(
            lambda value: materialize_source_file(tmp_path, "example", "README.md", value, apply=True),
            ["one", "two", "three", "four"],
        ))
    assert results.count("created") == 1
    assert results.count("preserved") == 3
    assert (tmp_path / "sources/example/README.md").read_text() in {"one", "two", "three", "four"}


@pytest.mark.parametrize("name", ["other.md", "../README.md", "/README.md", ""])
def test_only_fixed_control_filenames_can_be_created(tmp_path, name):
    with pytest.raises(ValueError):
        materialize_source_file(tmp_path, "example", name, "text", apply=True)
    assert list(tmp_path.iterdir()) == []
