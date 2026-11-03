"""Disposable capture preserves the exact source candidate across staged deletes."""

import pathlib

import pytest

from tools.codex_assets.knowledge_hub.common import run_rtk, working_tree_signature
from tools.codex_assets.knowledge_hub.engineering_snapshot import capture_snapshot


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / 'source'
    root.mkdir()
    run_rtk(root, ['git', 'init'])
    (root / '.gitignore').write_text('.tmp/\nlocal/\n')
    for path in ('staged.txt', 'unstaged.txt', 'rename.txt', '-literal space.txt', 'keep.txt'):
        (root / path).write_text(path + '\n')
    run_rtk(root, ['git', 'add', '.'])
    run_rtk(root, ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                   'commit', '-m', 'fixture'])
    return root


def capture_unchanged_source(root, destination):
    index = (root / '.git/index').read_bytes()
    signature = working_tree_signature(root)
    identity = capture_snapshot(root, destination)
    assert (root / '.git/index').read_bytes() == index
    assert working_tree_signature(root) == working_tree_signature(destination) == signature
    assert identity['source_signature'] == signature
    return identity


def cached_paths(root):
    return set(run_rtk(root, ['git', 'ls-files', '-z', '--cached'])['stdout'].split('\0')) - {''}


def test_staged_deletion_removes_only_disposable_head_index_entry(repository, tmp_path):
    run_rtk(repository, ['git', 'rm', '--', 'staged.txt', '-literal space.txt'])
    destination = tmp_path / 'snapshot'
    identity = capture_unchanged_source(repository, destination)
    assert {'staged.txt', '-literal space.txt'}.isdisjoint(cached_paths(destination))
    assert not (destination / 'staged.txt').exists()
    assert not (destination / '-literal space.txt').exists()
    assert {'staged.txt', '-literal space.txt'}.isdisjoint(row['path'] for row in identity['inputs'])
    assert (destination / 'keep.txt').read_bytes() == (repository / 'keep.txt').read_bytes()


def test_unstaged_deletion_preserves_missing_manifest_and_index_entry(repository, tmp_path):
    (repository / 'unstaged.txt').unlink()
    destination = tmp_path / 'snapshot'
    identity = capture_unchanged_source(repository, destination)
    assert 'unstaged.txt' in cached_paths(destination)
    assert {'path': 'unstaged.txt', 'missing': True} in identity['inputs']
    assert not (destination / 'unstaged.txt').exists()


def test_rename_new_files_and_mixed_deletions_capture_exact_candidate(repository, tmp_path):
    run_rtk(repository, ['git', 'mv', '--', 'rename.txt', 'renamed space.txt'])
    run_rtk(repository, ['git', 'rm', '--', 'staged.txt'])
    (repository / 'unstaged.txt').unlink()
    (repository / 'added.txt').write_text('staged new file\n')
    run_rtk(repository, ['git', 'add', '--', 'added.txt'])
    (repository / 'untracked.txt').write_text('untracked new file\n')
    destination = tmp_path / 'snapshot'
    identity = capture_unchanged_source(repository, destination)
    assert {'rename.txt', 'staged.txt'}.isdisjoint(cached_paths(destination))
    assert {'path': 'unstaged.txt', 'missing': True} in identity['inputs']
    for path in ('renamed space.txt', 'added.txt', 'untracked.txt', 'keep.txt'):
        assert (destination / path).read_bytes() == (repository / path).read_bytes()


def test_capture_still_rejects_source_mutation(repository, tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import engineering_snapshot
    from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
    copy = engineering_snapshot.shutil.copy2

    def change_source(source, destination):
        result = copy(source, destination)
        if pathlib.Path(source).name == 'keep.txt':
            pathlib.Path(source).write_text('changed while capture ran\n')
        return result

    monkeypatch.setattr(engineering_snapshot.shutil, 'copy2', change_source)
    with pytest.raises(KnowledgeHubError, match='changed while copying'):
        capture_snapshot(repository, tmp_path / 'snapshot')
