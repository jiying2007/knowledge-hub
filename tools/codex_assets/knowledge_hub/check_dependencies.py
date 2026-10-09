"""Conservative dependency identities; final delivery still binds the exact tree."""

from __future__ import annotations

import hashlib
import json
import sys
import os
import importlib.metadata

from .common import file_sha256, working_tree_signature, utc_timestamp, load_json, pretty_json, KnowledgeHubError
from .private_io import atomic_private_write


def dependency_fingerprints(root):
    groups = {
        'kernel':('tools', 'tests', 'schemas', '.github'),
        'content':('registry', 'projects', 'domains', 'governance', 'notes', 'inbox', 'artifacts/manifests'),
        'views':('registry', 'indexes', 'projects', 'domains', 'governance', 'inbox', 'artifacts/manifests'),
        'retrieval':('registry', 'projects', 'domains', 'governance', 'notes', 'inbox', 'artifacts/manifests', 'tests/fixtures'),
    }
    result = {}
    for name, prefixes in groups.items():
        paths = set()
        for prefix in prefixes:
            directory = root / prefix
            if directory.exists():
                paths.update(path for path in directory.rglob('*') if path.is_file()
                             and not any(part in {'.tmp', '.cache', '__pycache__', '.pytest_cache'} for part in path.parts))
        paths.update(path for pattern in ('pyproject.toml', 'requirements*') for path in root.glob(pattern) if path.is_file())
        # Automatic discovery can prefer a newly added root configuration over
        # pyproject. Presence, removal and bytes must all invalidate code checks.
        for pattern in ('*.toml', '*.ini', '*.cfg', '*.yaml', '*.yml', '.bandit'):
            paths.update(path for path in root.glob(pattern) if path.is_file())
        if name == 'kernel':
            for suffix in ('*.py', '*.pyi'):
                paths.update(path for path in root.rglob(suffix) if path.is_file()
                             and not any(part in {'.git', '.tmp', '.cache', '__pycache__', '.pytest_cache',
                                                  'build', 'dist', '.venv', 'venv'} or part.endswith('.egg-info')
                                         for part in path.relative_to(root).parts))
        if name != 'kernel':
            paths.update((root / 'tools').rglob('*.py'))
            if (root / 'README.md').is_file():
                paths.add(root / 'README.md')
        digest = hashlib.sha256()
        for path in sorted(paths):
            digest.update((str(path.relative_to(root)) + '\0' + file_sha256(path) + '\n').encode())
        result[name] = digest.hexdigest()
    result['delivery'] = working_tree_signature(root)
    return result


def check_identity(name, command, fingerprints):
    # Pytest and full regression read live repository fixtures: keep the entire
    # delivery tree in their identity until their inputs are fully isolated.
    scope = 'kernel' if name in {'ruff_correctness', 'mypy', 'bandit', 'build'} else 'delivery'
    if name == 'retrieval_benchmark':
        scope = 'retrieval'
    elif name == 'knowledge_check':
        scope = 'views'
    payload = {'check':name, 'scope':scope, 'fingerprint':fingerprints[scope],
               'command':list(command), 'python':sys.version,
               'environment_sha256':hashlib.sha256(json.dumps({key:os.environ.get(key, '') for key in ('PATH', 'PYTHONPATH')}, sort_keys=True).encode()).hexdigest(),
               'installed_tools':{},
               'policy':'explicit-dependencies-v1'}
    for package in ('ruff', 'mypy', 'bandit', 'PyYAML', 'jsonschema', 'setuptools', 'pytest', 'coverage'):
        try:
            payload['installed_tools'][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            payload['installed_tools'][package] = 'not-installed'
    return payload, hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def cache_safe(root, name):
    """Imported plugins/extra stub search paths need an explicit dependency closure."""
    if name != 'mypy':
        return True
    if os.environ.get('MYPYPATH'):
        return False
    for filename in ('pyproject.toml', 'mypy.ini', '.mypy.ini', 'setup.cfg'):
        path = root / filename
        if path.exists():
            text = path.read_text(encoding='utf-8')
            import re
            if re.search(r'(?m)^\s*(plugins|mypy_path|files|modules|packages)\s*=', text):
                return False
    return True


def cached_check(root, name, identity):
    import datetime as dt
    path = root / '.cache/knowledge-hub/checks' / (name + '.json')
    try:
        row = load_json(path, {}) or {}
    except (KnowledgeHubError, OSError, ValueError):
        return None
    if not isinstance(row, dict) or row.get('identity') != identity or not isinstance(row.get('result'), dict) or row['result'].get('status') != 'pass':
        return None
    if row.get('result_sha256') != hashlib.sha256(json.dumps(row['result'], sort_keys=True, ensure_ascii=False).encode()).hexdigest():
        return None
    try:
        if not isinstance(row.get('generated_at'), str):
            return None
        age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(row['generated_at'].replace('Z', '+00:00'))
        if not 0 <= age.total_seconds() <= 86400:
            return None
    except (KeyError, ValueError, TypeError):
        return None
    return dict(row['result'], cache_reused=True, original_generated_at=row['generated_at'])


def store_check(root, name, identity, result):
    path = root / '.cache/knowledge-hub/checks' / (name + '.json')
    digest = hashlib.sha256(json.dumps(result, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    atomic_private_write(path, pretty_json({'identity':identity, 'generated_at':utc_timestamp(), 'result':result, 'result_sha256':digest}) + '\n')
