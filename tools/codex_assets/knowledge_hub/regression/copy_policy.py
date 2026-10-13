"""Keep local credentials, runtime assets and derived state out of fixtures."""

import pathlib


def ignored_fixture_names(root, directory, names):
    ignored = set(names).intersection({'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'})
    current = pathlib.Path(directory).resolve()
    if current == root:
        ignored.update(set(names).intersection({'.git', '.tmp', '.codex', '.cache', '.agents',
                                               '.aws', '.ssh', '.gnupg', '.azure', 'build'}))
        ignored.update(name for name in names if name.endswith('.egg-info'))
    if current == root / 'artifacts':
        ignored.add('vault')
    return ignored
