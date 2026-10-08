"""Private failure replay source; host configuration stays outside retention."""

from __future__ import annotations

import json
import pathlib
import shutil
import tempfile
import re

from .common import resolve_inside, ensure_private_directory_tree, file_sha256, KnowledgeHubError, read_utf8_bounded, working_tree_signature, run_rtk
from .private_io import atomic_private_write


def retain_failure(root, snapshot, identity, payload):
    base = resolve_inside(root, '.tmp/engineering/failure-snapshots')
    ensure_private_directory_tree(root, base)
    destination = pathlib.Path(tempfile.mkdtemp(prefix=identity['source_signature'][:16] + '-', dir=str(base)))
    shutil.copytree(snapshot / '.git', destination / '.git')
    for row in identity['inputs']:
        if row.get('missing'):
            continue
        source = resolve_inside(snapshot, row['path'])
        target = destination / row['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if file_sha256(target) != row['sha256']:
            raise KnowledgeHubError('failure replay input identity mismatch')
    manifest = dict(identity, schema_version=1, host_configuration_retained=False, replay_requires_host_configuration=True,
                    retention_mode='report-only', retention_days=30)
    atomic_private_write(destination / '.tmp/replay-manifest.json', json.dumps(manifest, sort_keys=True, indent=2) + '\n')
    atomic_private_write(destination / '.tmp/failure-report.json', json.dumps(payload, sort_keys=True, indent=2) + '\n')
    return {'path':str(destination.relative_to(root)), 'source_signature':identity['source_signature'],
            'host_configuration_retained':False, 'replay_requires_host_configuration':True, 'retention_mode':'report-only'}


def replay_failure(root, relative):
    if not relative.startswith('.tmp/engineering/failure-snapshots/'):
        raise KnowledgeHubError('replay requires a governed failure snapshot path')
    snapshot = resolve_inside(root, relative)
    try:
        manifest = json.loads(read_utf8_bounded(snapshot / '.tmp/replay-manifest.json', 4 * 1024 * 1024, 'replay manifest'))
    except (ValueError, OSError) as error:
        raise KnowledgeHubError('replay manifest is invalid') from error
    _validate_replay(snapshot, manifest)
    # Never attach host bytes or test outputs to the retained source fixture.
    with tempfile.TemporaryDirectory(prefix='kh-engineering-replay-') as temporary:
        execution = pathlib.Path(temporary) / 'repo'
        shutil.copytree(snapshot, execution)
        _bind_replay_host(root, execution, manifest)
        from .snapshot_routing import bind_snapshot_route
        routing = bind_snapshot_route(execution, execution, manifest['head'])
        expected = manifest.get('snapshot_routing')
        if not isinstance(expected, dict) or any(routing.get(key) != expected.get(key)
                for key in ('status', 'source_remote_key', 'repo_id', 'workspace_ref')):
            raise KnowledgeHubError('replay routing identity is invalid')
        from .engineering import run_engineering_quality
        payload = run_engineering_quality(execution)
    payload['replayed_source_signature'] = manifest['source_signature']
    payload['live_source_certified'] = False
    return payload


def _validate_replay(snapshot, manifest):
    if (not isinstance(manifest, dict) or manifest.get('schema_version') != 1
            or manifest.get('host_configuration_retained') is not False
            or not isinstance(manifest.get('inputs'), list)
            or not isinstance(manifest.get('host_inputs'), list)):
        raise KnowledgeHubError('replay manifest schema is invalid')
    if working_tree_signature(snapshot) != manifest.get('source_signature'):
        raise KnowledgeHubError('replay source identity is invalid')
    head = run_rtk(snapshot, ['git', 'rev-parse', 'HEAD'])['stdout'].strip()
    if head != manifest.get('head'):
        raise KnowledgeHubError('replay HEAD identity is invalid')
    seen = set()
    for row in manifest['inputs']:
        if not isinstance(row, dict) or not isinstance(row.get('path'), str) or row['path'] in seen:
            raise KnowledgeHubError('replay input manifest is invalid')
        seen.add(row['path'])
        source = resolve_inside(snapshot, row['path'])
        if row.get('missing') is True:
            valid = not source.exists()
        else:
            valid = source.is_file() and file_sha256(source) == row.get('sha256') and source.stat().st_size == row.get('size')
        if not valid:
            raise KnowledgeHubError('replay input identity is invalid')


def _bind_replay_host(root, execution, manifest):
    seen = set()
    for row in manifest['host_inputs']:
        if (not isinstance(row, dict) or row.get('path') not in ('local/workspaces.json', 'local/activity-report.json')
                or row['path'] in seen or not isinstance(row.get('sha256'), str)
                or not re.fullmatch('[0-9a-f]{64}', row['sha256'])):
            raise KnowledgeHubError('replay host input manifest is invalid')
        seen.add(row['path'])
        source = resolve_inside(root, row['path'])
        if not source.is_file() or file_sha256(source) != row['sha256']:
            raise KnowledgeHubError('replay requires the original host configuration identity')
        target = resolve_inside(execution, row['path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        target.chmod(0o600)
        if file_sha256(target) != row['sha256']:
            raise KnowledgeHubError('replay host input changed while copying')
