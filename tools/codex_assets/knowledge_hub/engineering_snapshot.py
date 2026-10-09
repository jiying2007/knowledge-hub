"""Capture a reviewed dirty tree under a short lock; verify it without blocking intake."""

from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile
import subprocess

from .common import run_rtk, parse_json_output, working_tree_signature, file_sha256, resolve_inside, KnowledgeHubError
from .store import RepositoryTransaction
from .private_io import atomic_private_write
from .snapshot_routing import bind_snapshot_route


def capture_snapshot(root, destination):
    destination = pathlib.Path(destination).resolve()
    if destination.exists():
        raise KnowledgeHubError('snapshot target must be new')
    try:
        destination.relative_to(root.resolve())
    except ValueError:
        pass
    else:
        raise KnowledgeHubError('snapshot must be outside the live repository')
    with RepositoryTransaction(root, 'engineering-snapshot-capture')._lock():
        signature = working_tree_signature(root)
        paths = run_rtk(root, ['git', '-c', 'core.quotePath=false', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'])['stdout'].split('\0')
        head = run_rtk(root, ['git', 'rev-parse', 'HEAD'])['stdout'].strip()
        run_rtk(root, ['git', 'clone', '--no-hardlinks', '--no-checkout', str(root), str(destination)], timeout=60)
        destination.chmod(0o700)
        run_rtk(destination, ['git', 'read-tree', head])
        manifest = []
        for relative in sorted(set(path for path in paths if path)):
            source = resolve_inside(root, relative)
            if not source.exists():
                manifest.append({'path':relative, 'missing':True})
                continue
            if not source.is_file():
                raise KnowledgeHubError('snapshot input is not a regular file')
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            digest = file_sha256(source)
            if digest != file_sha256(target):
                raise KnowledgeHubError('snapshot input changed while copying')
            manifest.append({'path':relative, 'sha256':digest, 'size':source.stat().st_size})
        if working_tree_signature(root) != signature or working_tree_signature(destination) != signature:
            raise KnowledgeHubError('snapshot identity does not match the captured tree')
        # Host-local routing configuration is declared separately and never
        # promoted as source/project evidence or copied into release artifacts.
        host_inputs = []
        for relative in ('local/workspaces.json', 'local/activity-report.json'):
            source = root / relative
            if source.is_file() and not source.is_symlink():
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                target.chmod(0o600)
                digest = file_sha256(source)
                if digest != file_sha256(target):
                    raise KnowledgeHubError('snapshot host input changed while copying')
                host_inputs.append({'path':relative, 'sha256':digest})
        routing = bind_snapshot_route(root, destination, head)
        if working_tree_signature(root) != signature or working_tree_signature(destination) != signature:
            raise KnowledgeHubError('snapshot identity changed during host binding')
    return {'source_signature':signature, 'head':head, 'inputs':manifest, 'host_inputs':host_inputs,
            'snapshot_routing':routing,
            'dirty_overlay_included':True, 'writer_lock_released_before_tests':True}


def run_snapshot_engineering(root, sbom_output=None):
    from .engineering import _write_engineering_snapshot
    from .engineering_preflight import preflight
    checked = preflight(root, verify_capabilities=True)
    if checked['status'] != 'pass':
        return {'status':'fail', 'phase':'preflight', 'preflight':checked,
                'contract':checked['contract'], 'environment':checked['environment'], 'checks':{},
                'errors':['engineering preflight failed'], 'failure_class':'preflight',
                'expensive_checks_started':False, 'automatic_retry_performed':False}
    with tempfile.TemporaryDirectory(prefix='kh-engineering-snapshot-') as temporary:
        snapshot = pathlib.Path(temporary) / 'repo'
        identity = capture_snapshot(root, snapshot)
        try:
            result = run_rtk(snapshot, [sys.executable, '-m', 'tools.codex_assets.knowledge_hub.engineering_cli',
                                      '--mode', 'full', '--in-place', '--json'], timeout=3600, accepted_exit_codes=(0, 1),
                             extra_env={'PYTHONPATH':str(snapshot), 'KNOWLEDGE_ENGINEERING_SNAPSHOT':'1'})
            payload = parse_json_output(result)
        except (KnowledgeHubError, OSError, subprocess.TimeoutExpired) as error:
            payload = {'status':'fail', 'errors':[str(error)], 'failure_class':'transport-or-invalid-output',
                       'automatic_retry_performed':False,
                       'candidate_integrity':{'after_signature':working_tree_signature(snapshot)}}
        if payload.get('candidate_integrity', {}).get('after_signature') != identity['source_signature']:
            raise KnowledgeHubError('engineering result lost its snapshot binding')
        if payload.get('status') != 'pass':
            from .snapshot_retention import retain_failure
            payload['failure_replay'] = retain_failure(root, snapshot, identity, payload)
        dist = resolve_inside(root, '.tmp/engineering/dist')
        dist.mkdir(parents=True, exist_ok=True)
        for artifact in (snapshot / '.tmp/engineering/dist').glob('*'):
            if artifact.is_symlink() or not artifact.is_file():
                raise KnowledgeHubError('engineering artifact must be a regular non-symlink file')
            target = resolve_inside(root, str((dist / artifact.name).relative_to(root)))
            if target.is_symlink():
                raise KnowledgeHubError('engineering artifact target must not be a symlink')
            shutil.copy2(artifact, target)
        sbom = snapshot / '.tmp/engineering/knowledge-hub.cdx.json'
        if sbom.is_file():
            destination = pathlib.Path(sbom_output) if sbom_output else root / '.tmp/engineering/knowledge-hub.cdx.json'
            try:
                destination.resolve().relative_to(root.resolve())
            except ValueError as exc:
                raise KnowledgeHubError('SBOM output must stay inside the live repository') from exc
            atomic_private_write(destination, sbom.read_text(encoding='utf-8'))
        current = working_tree_signature(root)
        host_matches = all(file_sha256(root / row['path']) == row['sha256'] for row in identity['host_inputs'])
        payload['source_snapshot'] = dict(identity, inputs_count=len(identity['inputs']), live_source_signature=current,
                                          live_host_inputs_match=host_matches,
                                          live_matches_snapshot=current == identity['source_signature'] and host_matches)
        payload['source_snapshot'].pop('inputs')
        atomic_private_write(root / '.tmp/engineering/source-snapshot-manifest.json', json.dumps(identity, sort_keys=True, indent=2)+'\n')
        _write_engineering_snapshot(root, payload)
        return payload
