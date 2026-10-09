"""Bounded owner work packets keep current validity, candidates and history separate."""

from __future__ import annotations

from collections import defaultdict
import time
import hashlib
from typing import Any, Dict
import datetime as dt

from .common import KnowledgeHubError, file_sha256, load_markdown, resolve_inside, pretty_json
from .private_io import atomic_private_write, PrivateWriteUncertain
from .review_state import load_consumption_state, cycle_sha256, validate_identity_text
import math


def build_review_batches(rows, batch_size=10, owner_wip_limit=10, cold_days=30):
    if type(batch_size) is not int or not 1 <= batch_size <= 50 or len(rows) > 5000:
        raise KnowledgeHubError('review batch exceeds explicit budget')
    if type(owner_wip_limit) is not int or not 1 <= owner_wip_limit <= 50 or type(cold_days) is not int or not 1 <= cold_days <= 3650:
        raise KnowledgeHubError('review WIP or cold age exceeds budget')
    groups = defaultdict(list)
    for row in rows:
        status = row.get('status')
        lane = {'active':'current-validity', 'reviewing':'candidate-decision',
                'draft':'candidate-decision', 'archived':'historical-integrity',
                'superseded':'historical-integrity', 'rejected':'historical-integrity'}.get(status)
        if lane is None:
            continue
        owner = row.get('owner') or '<missing-owner>'
        overdue = max(0, -int(row.get('days_until_review', 0)))
        priority = {'current-validity':3000, 'candidate-decision':2000, 'historical-integrity':1000}[lane]
        priority += min(overdue, 365) + (1000 if row.get('review_class') != 'ordinary' else 0)
        cold = overdue >= cold_days
        priority += 365 if cold and lane == 'candidate-decision' else 0
        groups[owner].append({
            'item_id':row['item_id'], 'path':row['path'], 'status':status, 'lane':lane,
            'domain':row.get('domain', ''), 'review_after':row.get('review_after', ''),
            'priority':priority, 'overdue_days':overdue,
            'cold':cold, 'responsible_owner':owner,
            'next_action':{'current-validity':'核验当前适用性并补充周期证据',
                           'candidate-decision':'审查内容和证据后明确接受、延期或要求修改',
                           'historical-integrity':'核验历史引用和失效边界'}[lane],
            'machine_checks':['body-registry-mirror', 'references', 'duplicate-candidates', 'evidence-inventory'],
            'human_decision':'current-applicability' if lane == 'current-validity'
                             else 'content-and-evidence' if lane == 'candidate-decision' else 'historical-boundary',
        })
    if len(groups) > 100:
        raise KnowledgeHubError('review owner count exceeds budget')
    batches = []
    for owner, candidates in sorted(groups.items()):
        selected_limit = min(batch_size, owner_wip_limit)
        candidates.sort(key=lambda row:(-row['priority'], row['item_id']))
        lanes = defaultdict(list)
        for row in candidates:
            lanes[row['lane']].append(row)
        selected: list[Dict[str, Any]] = []
        while len(selected) < min(selected_limit, len(candidates)):
            for lane in ('current-validity', 'candidate-decision', 'historical-integrity'):
                if lanes[lane] and len(selected) < selected_limit:
                    selected.append(lanes[lane].pop(0))
        batches.append({'owner':owner, 'total_count':len(candidates),
                        'selected_count':len(selected),
                        'remaining_count':len(candidates) - len(selected),
                        'cold_count':sum(row['cold'] for row in candidates),
                        'wip_limit':owner_wip_limit, 'wip_limit_reached':len(candidates) > selected_limit,
                        'rows':selected,
                        'lane_selected_counts':{lane:sum(row['lane'] == lane for row in selected) for lane in lanes}})
    return {'schema_version':'knowledge-hub.review-batches/v1', 'report_only':True,
            'selection_is_authorization':False, 'semantic_decision_made':False,
            'batch_size':batch_size, 'owner_count':len(batches), 'batches':batches}


def prepare_review_batches(root, rows, items, batch_size=10, as_of=None):
    from .candidate_duplicates import duplicate_hints, duplicate_inventory

    started = time.monotonic()
    by_id = {item['id']:item for item in items}
    duplicate_rows = duplicate_inventory(root, items)
    state_status = 'pass'
    pending_count = None
    try:
        state, pending, _ = load_consumption_state(root / '.tmp/review-consumption/state.json')
        pending_count = len(pending)
        if pending:
            state_status = 'needs-review'
    except (KnowledgeHubError, ValueError, OSError):
        state, state_status = {}, 'needs-review'
    eligible = []
    today = as_of or dt.date.today()
    suppressed = 0
    for row in rows:
        previous = state.get(row['item_id'], {})
        try:
            digest = file_sha256(resolve_inside(root, row['path']))
        except (OSError, KnowledgeHubError):
            digest = ''
        same = bool(digest and previous.get('body_sha256') == digest
                    and previous.get('cycle_sha256') == cycle_sha256(root, by_id[row['item_id']]))
        deferred = previous.get('decision') == 'deferred' and previous.get('next_review_at', '') > today.isoformat()
        accepted = previous.get('decision') == 'accepted' and previous.get('valid_until', '') > today.isoformat()
        if same and (accepted or deferred):
            suppressed += 1
        else:
            eligible.append(row)
    packet = build_review_batches(eligible, batch_size)
    packet['consumed_or_deferred_count'] = suppressed
    packet['consumption_state_status'] = state_status
    packet['pending_event_count'] = pending_count
    packet['reopened_count'] = sum(row['item_id'] in state for row in eligible)
    for batch in packet['batches']:
        for row in batch['rows']:
            item = by_id[row['item_id']]
            checks: Dict[str, Any]
            try:
                target = resolve_inside(root, row['path'])
                metadata, body = load_markdown(target)
                mirror = all(metadata.get(key) == item.get(key) for key in ('id', 'owner', 'status', 'path'))
                checks = {'body':'present', 'mirror':'pass' if mirror else 'needs-fix',
                          'body_sha256':file_sha256(target)}
            except (OSError, KnowledgeHubError, ValueError):
                body = ''
                checks = {'body':'unavailable', 'mirror':'needs-fix'}
            hints = duplicate_hints(duplicate_rows, item.get('title', ''), item.get('summary_zh', ''), item.get('domain'), exclude_id=row['item_id'],
                                    body=body, scope=item.get('scope', ''), version=item.get('version', ''))
            checks['duplicate_candidates'] = hints
            checks['evidence_reference_count'] = len(item.get('evidence_refs', []))
            checks['reference_inventory'] = _reference_inventory(root, item.get('evidence_refs', []))
            checks['evidence_validation_status'] = item.get('evidence_validation_status', 'pending')
            checks['source_sha256'] = item.get('source', {}).get('source_sha256', '')
            row['machine_checks'] = checks
    packet['preparation_ms'] = round((time.monotonic() - started) * 1000, 2)
    packet['reviewer_time_measured'] = False
    durations = [value['review_seconds'] for value in state.values() if type(value.get('review_seconds')) in (int, float)]
    packet['consumption_metrics'] = {'recorded_count':len(state), 'timed_review_count':len(durations),
                                    'review_seconds_total':sum(durations), 'preparation_is_review_time':False,
                                    'decision_counts':{decision:sum(value.get('decision') == decision for value in state.values())
                                                       for decision in ('accepted', 'deferred', 'changes-requested')},
                                    'reopened_count':packet['reopened_count'], 'suppressed_count':suppressed}
    from .review_events import event_metrics
    packet['consumption_metrics']['measurement_scope'] = 'current-state-stock'
    packet['consumption_metrics']['throughput'] = event_metrics(root, today)
    if state_status != 'pass':
        packet['consumption_metrics']['throughput']['status'] = 'needs-review'
    packet['consumption_metrics']['throughput']['pending_event_count'] = pending_count
    return packet


def record_consumption(root, item_id, decision, reviewer, evidence_ref, body_sha256, *,
                       next_review_at='', review_seconds=None, review_event_id='', apply=False):
    """Record packet consumption only; this never changes lifecycle or owner gates."""
    from .common import registry_items
    reviewer = validate_identity_text(reviewer, 'reviewer', 160)
    evidence_ref = validate_identity_text(evidence_ref, 'evidence reference')
    if not isinstance(review_event_id, str):
        raise KnowledgeHubError('review event identity must be a string')
    if review_event_id:
        review_event_id = validate_identity_text(review_event_id, 'review event identity', 160)
    if not isinstance(decision, str) or decision not in {'accepted', 'deferred', 'changes-requested'}:
        raise KnowledgeHubError('consumption requires decision, explicit reviewer and evidence')
    item = next((row for row in registry_items(root) if row['id'] == item_id), None)
    if item is None or file_sha256(resolve_inside(root, item['path'])) != body_sha256:
        raise KnowledgeHubError('consumption body identity is stale or unknown')
    if review_seconds is not None and (type(review_seconds) not in (int, float) or not 0 <= review_seconds <= 86400 or not math.isfinite(review_seconds)):
        raise KnowledgeHubError('review duration is invalid')
    path = root / '.tmp/review-consumption/state.json'
    state, pending, expected = _load_consumption(path)
    if len(state) >= 5000 and item_id not in state:
        raise KnowledgeHubError('review consumption state is malformed or exceeds budget')
    today = dt.date.today()
    expiry = today + dt.timedelta(days=30)
    review_after = item.get('review_after', '')
    if review_after:
        next_cycle = dt.date.fromisoformat(review_after)
        if today < next_cycle < expiry:
            expiry = next_cycle
    consumption = {'decision':decision, 'reviewer':reviewer, 'evidence_ref':evidence_ref,
                      'body_sha256':body_sha256, 'next_review_at':next_review_at,
                      'cycle_sha256':cycle_sha256(root, item), 'reviewed_at':today.isoformat(),
                      'valid_until':expiry.isoformat(),
                      'review_seconds':review_seconds, 'lifecycle_mutation':False, 'owner_gate_mutation':False}
    from .review_events import prepare_event
    event, replay = prepare_event(root, item_id, consumption, review_event_id, pending)
    if not replay:
        if decision == 'deferred' and (not next_review_at or dt.date.fromisoformat(next_review_at) <= today):
            raise KnowledgeHubError('deferred consumption requires a future next_review_at')
        state[item_id] = dict(consumption, event_id=event['event_id'])
        pending.append(event)
    result = {'status':'planned', 'applied':False, 'event_id':event['event_id'],
              'history_status':'not-written', 'stock_changed':not replay,
              'semantic_owner_approval':False, 'consumption':state.get(item_id, consumption)}
    if apply:
        result.update(_apply_consumption(root, path, state, pending, expected, event))
    return result


def _load_consumption(path):
    return load_consumption_state(path)


def _write_consumption(path, state, pending, expected):
    from .review_events import validate_pending
    validate_pending(pending)
    content = pretty_json({'schema_version':2, 'entries':state, 'pending_events':pending}) + '\n'
    if len(content.encode()) > 4 * 1024 * 1024:
        raise KnowledgeHubError('review consumption exceeds byte budget')
    atomic_private_write(path, content, expected_sha256=expected)


def _ack_event(path, event_id):
    for attempt in range(3):
        state, pending, expected = _load_consumption(path)
        remaining = [event for event in pending if event['event_id'] != event_id]
        if len(remaining) == len(pending):
            return
        try:
            _write_consumption(path, state, remaining, expected)
            return
        except PrivateWriteUncertain:
            raise
        except KnowledgeHubError as exc:
            if str(exc) != 'private write expected hash conflict' or attempt == 2:
                raise


def _apply_consumption(root, path, state, pending, expected, event):
    from .review_events import append_prepared_event
    is_pending = any(row['event_id'] == event['event_id'] for row in pending)
    if is_pending:
        try:
            _write_consumption(path, state, pending, expected)
        except PrivateWriteUncertain:
            return {'status':'needs-recovery-review', 'applied':None, 'state_status':'durability-unknown',
                    'history_status':'not-written', 'pending_status':'needs-review', 'stock_changed':None}
    result = {'status':'recorded', 'applied':True, 'state_status':'confirmed', 'pending_status':'clear'}
    try:
        result['history_status'] = append_prepared_event(root, event)
    except (KnowledgeHubError, OSError, ValueError, TypeError):
        result.update(history_status='needs-review', pending_status='needs-review')
        return result
    if is_pending:
        try:
            _ack_event(path, event['event_id'])
        except (KnowledgeHubError, OSError, ValueError, TypeError):
            result['pending_status'] = 'needs-review'
    return result


def _reference_inventory(root, refs):
    inventory = []
    for value in refs[:64]:
        ref = str(value)
        kind, status = 'external-pointer', 'needs-external-evidence'
        if ref.startswith('rtk '):
            kind, status = 'replay-command', 'not-executed-by-triage'
        elif '://' not in ref and not ref.startswith(('~', '/')):
            kind = 'local-reference'
            try:
                status = 'present' if resolve_inside(root, ref.split('#', 1)[0]).is_file() else 'missing'
            except KnowledgeHubError:
                status = 'invalid'
        inventory.append({'reference_sha256':hashlib.sha256(ref.encode()).hexdigest(),
                          'kind':kind, 'status':status})
    return inventory
