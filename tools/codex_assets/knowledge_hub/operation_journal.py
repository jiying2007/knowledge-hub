"""Bounded metadata-only stage records and public Provider reconciliation."""

from __future__ import annotations

import json
import re
import hashlib

from .common import KnowledgeHubError, read_utf8_bounded, pretty_json, utc_timestamp, run_rtk, parse_json_output
from .private_io import atomic_private_write

TRANSITIONS = {'planned':{'gated'}, 'gated':{'applied', 'unknown'},
               'applied':{'verified', 'unknown'}, 'unknown':set(), 'verified':set()}


def record_stage(root, digest, stage, identity):
    if not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise KnowledgeHubError('operation plan identity is invalid')
    path = root / '.tmp/governed-provider' / (digest + '.state.json')
    raw = read_utf8_bounded(path, 128 * 1024, 'operation state') if path.exists() else ''
    state = json.loads(raw) if raw else {'schema_version':1, 'plan_sha256':digest, 'identity':identity, 'events':[], 'attempt_generation':1}
    if not isinstance(state, dict) or state.get('schema_version') != 1 or state.get('plan_sha256') != digest:
        raise KnowledgeHubError('operation state schema or plan identity is invalid')
    if stage not in ('planned', 'gated', 'applied', 'verified', 'unknown'):
        raise KnowledgeHubError('operation stage is invalid')
    if state.get('identity') != identity or not isinstance(state.get('events'), list) or len(state['events']) >= 100:
        raise KnowledgeHubError('operation state conflicts or exceeds budget')
    if any(not isinstance(event, dict) or event.get('stage') not in ('planned', 'gated', 'applied', 'verified', 'unknown')
           or not isinstance(event.get('recorded_at'), str) for event in state['events']):
        raise KnowledgeHubError('operation event schema is invalid')
    _validate_history(state)
    previous = state.get('stage')
    if previous == stage:
        atomic_private_write(path, raw, expected_sha256=hashlib.sha256(raw.encode()).hexdigest())
        return False
    if (not previous and stage != 'planned') or (previous and stage not in TRANSITIONS.get(previous, set())):
        raise KnowledgeHubError('operation transition is invalid; unknown outcomes require reconciliation')
    state['events'].append({'stage':stage, 'recorded_at':utc_timestamp()})
    state['stage'] = stage
    atomic_private_write(path, pretty_json(state) + '\n', expected_sha256=hashlib.sha256(raw.encode()).hexdigest() if raw else '')
    return True


def _validate_history(state):
    generation = state.get('attempt_generation', 1)
    if type(generation) is not int or not 1 <= generation <= 100:
        raise KnowledgeHubError('operation attempt generation is invalid')
    previous = None
    for event in state['events']:
        current = event['stage']
        if ((previous is None and current != 'planned') or
                (previous is not None and current not in TRANSITIONS.get(previous, set()))):
            raise KnowledgeHubError('operation history transition is invalid')
        previous = current
    if state.get('stage') != previous:
        raise KnowledgeHubError('operation history does not match its current stage')


def reconcile_plan(root, policy_root, digest):
    if not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise KnowledgeHubError('reconciliation requires the exact plan hash')
    path = root / '.tmp/governed-provider' / (digest + '.json')
    raw = read_utf8_bounded(path, 128 * 1024, 'operation plan')
    import hashlib
    if hashlib.sha256(raw.encode()).hexdigest() != digest:
        raise KnowledgeHubError('operation plan bytes do not match identity')
    plan = json.loads(raw)
    receipt = plan['provider_plan']
    command = ['bash', str(policy_root / 'scripts/knowledge-provider.sh')]
    if plan['operation'] == 'archive':
        command += ['archive', '--project', plan['project'], '--reconcile-operation', receipt['operation_id'],
                    '--expected-content-sha256', receipt['content_sha256'], '--json']
    elif plan['operation'] == 'activity-capture':
        command += ['activity-capture', '--reconcile-receipt', receipt['receipt_id'], '--receipt-date', plan['receipt_date'],
                    '--expected-content-sha256', receipt['sha256'], '--json']
    else:
        raise KnowledgeHubError('operation type is unsupported')
    result = parse_json_output(run_rtk(root, command, timeout=60))
    return {'status':result['status'], 'plan_sha256':digest, 'read_only':True, 'reconciliation':result,
            'automatic_retry_performed':False}
