"""Provider plan -> runtime gate -> frozen input -> persistence -> hash readback."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import subprocess

from .common import KnowledgeHubError, parse_json_output, run_rtk, file_sha256, resolve_inside
from .private_io import atomic_private_write, private_execution_lock
from .operation_journal import record_stage, reconcile_plan


class PersistenceUnverified(KnowledgeHubError):
    """An apply was invoked; do not report a false no-write guarantee."""


def _apply_and_verify(root, args, planned, identity_keys):
    try:
        result = parse_json_output(run_rtk(root, args + ['--apply'], timeout=60))
        if not isinstance(result.get('status'), str):
            raise KnowledgeHubError('Provider result status type is invalid')
        successful = (result.get('status') in {'ARCHIVED', 'ALREADY_ARCHIVED'} and result.get('persisted') is True
                      if 'archive' in args else result.get('status') == 'pass' and result.get('applied') is True)
        if not successful or any(not isinstance(result.get(key), str) or result.get(key) != planned.get(key) for key in identity_keys):
            raise KnowledgeHubError('Provider outcome does not match the approved identity')
        if not isinstance(result.get('target'), str):
            raise KnowledgeHubError('Provider result target type is invalid')
        target = pathlib.Path(result['target'])
        relative = str(target.relative_to(root)) if target.is_absolute() else str(target)
        expected = result[identity_keys[1]]
        if file_sha256(resolve_inside(root, relative)) != expected:
            raise KnowledgeHubError('persisted Provider output readback mismatch')
        return result
    except (KnowledgeHubError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        raise PersistenceUnverified(str(exc)) from exc


def execute_provider(root, policy_root, thread_id, operation, source, *, project='', kind='validation', apply=False):
    if not thread_id or thread_id != os.environ.get('CODEX_THREAD_ID'):
        raise KnowledgeHubError('must use the actual current thread id')
    if operation not in {'archive', 'activity-capture'}:
        raise KnowledgeHubError('unsupported governed Provider operation')
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 256 * 1024:
        raise KnowledgeHubError('source must be a bounded non-symlink file')
    source = source.resolve()
    raw = source.read_bytes()
    source_digest = hashlib.sha256(raw).hexdigest()
    provider = policy_root / 'scripts/knowledge-provider.sh'
    with tempfile.TemporaryDirectory(prefix='kh-governed-provider-') as directory:
        frozen = pathlib.Path(directory) / source.name
        frozen.write_bytes(raw)
        args = ['bash', str(provider), operation]
        if operation == 'archive':
            if not project:
                raise KnowledgeHubError('archive requires an explicit project')
            args += ['--project', project, '--source', str(frozen), '--kind', kind, '--sanitized']
        else:
            args += ['--input', str(frozen)]
        args += ['--json']
        planned = parse_json_output(run_rtk(root, args, timeout=60))
        if not isinstance(planned.get('status'), str) or planned['status'] not in {'PLANNED', 'ALREADY_ARCHIVED', 'pass'}:
            raise KnowledgeHubError('Provider did not produce an acceptable dry-run')
        identity_keys = ('operation_id', 'content_sha256') if operation == 'archive' else ('receipt_id', 'sha256')
        if any(not isinstance(planned.get(key), str) or not planned[key] for key in identity_keys):
            raise KnowledgeHubError('Provider dry-run identity fields are invalid')
        plan = {'operation':operation, 'source_sha256':source_digest, 'thread_id':thread_id,
                'provider_plan':planned, 'source_frozen':True, 'project':project,
                'receipt_date':json.loads(raw).get('session_date', '') if operation == 'activity-capture' else ''}
        plan_text = json.dumps(plan, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(plan_text.encode()).hexdigest()
        if not apply:
            return {'status':'planned', 'applied':False, 'plan':plan, 'plan_sha256':digest}
        lock = root / '.tmp/governed-provider' / (digest + '.execution.lock')
        with private_execution_lock(lock):
            return _execute_provider_plan(root, policy_root, thread_id, source, source_digest,
                                          args, planned, identity_keys, plan_text, digest)


def _execute_provider_plan(root, policy_root, thread_id, source, source_digest,
                           args, planned, identity_keys, plan_text, digest):
    policy = [sys.executable, '-m', 'tools.codex_assets', 'execution-policy', '--thread-id', thread_id]
    policy_env = {'PYTHONPATH':str(policy_root)}
    atomic_private_write(root / '.tmp/governed-provider' / (digest + '.json'), plan_text, immutable=True)
    identity = {key:planned[key] for key in identity_keys}
    record_stage(root, digest, 'planned', identity)
    evidence_id = 'provider-plan-' + digest[:24]
    for suffix in (['evidence', '--evidence-id', evidence_id, '--sha256', digest],
                   ['artifact', '--artifact-type', 'plan', '--evidence-id', evidence_id],
                   ['artifact', '--artifact-type', 'dry-run', '--evidence-id', evidence_id]):
        run_rtk(policy_root, policy + suffix, timeout=30, extra_env=policy_env)
    gate = parse_json_output(run_rtk(policy_root, policy + ['gate', '--event', 'apply'], timeout=30, extra_env=policy_env))
    if gate.get('status') != 'pass' or gate.get('gate_allowed') is not True:
        raise KnowledgeHubError('apply gate denied; Provider apply was not invoked')
    if file_sha256(source) != source_digest:
        raise KnowledgeHubError('source changed after planning; replan required')
    record_stage(root, digest, 'gated', identity)
    try:
        result = _apply_and_verify(root, args, planned, identity_keys)
    except PersistenceUnverified as error:
        error.plan_sha256 = digest
        error.operation_identity = identity
        try:
            record_stage(root, digest, 'unknown', identity)
        except (KnowledgeHubError, OSError, ValueError, TypeError):
            pass
        try:
            error.reconciliation = reconcile_plan(root, policy_root, digest)
        except (KnowledgeHubError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
            error.reconciliation = {'status':'unavailable', 'read_only':True}
        raise
    journal_status = 'pass'
    try:
        record_stage(root, digest, 'applied', identity)
        record_stage(root, digest, 'verified', identity)
    except (KnowledgeHubError, OSError, ValueError, TypeError):
        journal_status = 'needs-review'
    return {'status':'pass', 'applied':True, 'plan_sha256':digest,
            'readback_verified':True, 'receipt':result, 'runtime_gate':gate, 'journal_status':journal_status}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(pathlib.Path(__file__).resolve().parents[3]))
    parser.add_argument('--policy-root', default=str(pathlib.Path.home() / 'codex'))
    parser.add_argument('--thread-id', default=os.environ.get('CODEX_THREAD_ID', ''))
    parser.add_argument('--operation', choices=('archive', 'activity-capture'), default='archive')
    parser.add_argument('--source', default='')
    parser.add_argument('--reconcile-plan', default='')
    parser.add_argument('--project', default='')
    parser.add_argument('--kind', default='validation')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.reconcile_plan:
            if args.apply:
                raise KnowledgeHubError('reconcile-plan is read-only')
            payload = reconcile_plan(pathlib.Path(args.root).resolve(), pathlib.Path(args.policy_root).resolve(), args.reconcile_plan)
        else:
            payload = execute_provider(pathlib.Path(args.root).resolve(), pathlib.Path(args.policy_root).resolve(),
                                   args.thread_id, args.operation, pathlib.Path(args.source),
                                   project=args.project, kind=args.kind, apply=args.apply)
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    except (KnowledgeHubError, OSError, ValueError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({'status':'needs-recovery-review' if isinstance(exc, PersistenceUnverified) else 'blocked',
                          'error':str(exc), 'applied':None if isinstance(exc, PersistenceUnverified) else False,
                          'plan_sha256':getattr(exc, 'plan_sha256', ''),
                          'reconciliation':getattr(exc, 'reconciliation', None),
                          'operation_identity':getattr(exc, 'operation_identity', {})}, ensure_ascii=False))
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
