import shutil

from tools.codex_assets.knowledge_hub.regression.copy_policy import ignored_fixture_names


def test_fixture_copy_preserves_source_and_never_follows_host_private_or_derived_paths(tmp_path):
    root = tmp_path / 'source'
    root.mkdir()
    (root / 'README.md').write_text('canonical source')
    for name in ['.aws', '.agents', '.ssh', '.gnupg', '.azure']:
        (root / name).symlink_to(tmp_path / 'missing-host-private-path', target_is_directory=True)
    for name in ['build', 'tool.egg-info', '.mypy_cache', '.ruff_cache']:
        (root / name).mkdir()
        (root / name / 'derived').write_text('derived')
    target = tmp_path / 'fixture'
    shutil.copytree(root, target, ignore=lambda directory, names: ignored_fixture_names(root, directory, names))
    assert sorted(path.name for path in target.iterdir()) == ['README.md']
    assert (target / 'README.md').read_text() == 'canonical source'


def test_fixture_vault_remains_a_separate_copy_and_nested_sources_are_preserved(tmp_path):
    root = tmp_path.resolve()
    assert ignored_fixture_names(root, root / 'artifacts', ['vault', 'manifests']) == {'vault'}
    assert ignored_fixture_names(root, root / 'projects', ['build', 'tool.egg-info', 'source']) == set()
