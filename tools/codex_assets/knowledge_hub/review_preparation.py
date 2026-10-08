"""Metadata-only routing packets reuse triage; they never assign human signers."""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
from collections import Counter, defaultdict, deque

from .common import KnowledgeHubError
from .security import scan_secret_text

MAX_PACKET_BYTES = 48 * 1024
LANES = ('item-current', 'item-candidate', 'source-current', 'source-retired', 'owner-gate')
DECISIONS = dict(zip(LANES, ('current-applicability', 'candidate-scope-and-evidence',
    'current-source-authority', 'retired-provenance-boundary', 'real-owner-assignment')))


def _identity(value):
    if not isinstance(value, str) or not value.strip():
        return '<unassigned>'
    value = value.strip()
    if len(value) > 160 or scan_secret_text(value):
        return 'withheld-sha256:' + hashlib.sha256(value.encode()).hexdigest()
    return value


def _hash(value):
    return value if isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) else ''


def _path(value):
    if not isinstance(value, str) or len(value) > 512 or scan_secret_text(value):
        return ''
    path = pathlib.PurePosixPath(value)
    allowed = {'projects', 'domains', 'governance', 'registry', 'indexes', 'templates', 'docs', 'tools', 'scripts', 'artifacts'}
    return value if (not path.is_absolute() and path.parts and path.parts[0] in allowed
        and '..' not in path.parts and not any(part.startswith('.') or part == 'personal' for part in path.parts)
        and '\x00' not in value) else ''


def _lane(row):
    if row['entity_type'] == 'source':
        return 'source-retired' if row.get('source_evidence', {}).get('retired_provenance_only') is True else 'source-current'
    if row['entity_type'] == 'owner-gate':
        return 'owner-gate'
    return 'item-current' if row.get('status') == 'active' else 'item-candidate'


def _entity(row):
    lane, body = _lane(row), row.get('body_evidence', {})
    refs = row.get('references', [])
    value = {'entity_id':_identity(row.get('entity_id')), 'lane':lane, 'review_after':row.get('review_after', '')}
    if body:
        value['body'] = {'path':_path(row.get('body_path', '')), 'sha256':_hash(body.get('sha256')),
                         'status':body.get('status', 'not-applicable')}
    if refs:
        value['reference_status_counts'] = dict(Counter(ref.get('status', 'unknown') for ref in refs))
    if row.get('reference_overflow'):
        value['reference_overflow'] = True
    if row.get('source_evidence'):
        value['source'] = {key:val for key,val in row['source_evidence'].items()
            if key in {'hub_path_present', 'origin_status', 'retired_provenance_only', 'declared_check_present'}}
    return value


def _round_robin(rows):
    buckets = {lane:deque() for lane in LANES}
    for row in sorted(rows, key=lambda row:str(row.get('entity_id', ''))):
        buckets[_lane(row)].append(row)
    while any(buckets.values()):
        for lane in LANES:
            if buckets[lane]:
                yield buckets[lane].popleft()


def _serialized_bytes(result):
    return len(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def _update_counts(result):
    selected = Counter()
    packet_counts = Counter()
    for packet in result['packets']:
        selected[packet['declared_owner']] += len(packet['rows'])
        packet_counts[packet['declared_owner']] += 1
    result['selected_count'] = sum(selected.values())
    result['remaining_count'] = result['eligible_count'] - result['selected_count']
    result['overflow'] = result['remaining_count'] > 0
    for owner in result['owners']:
        owner['selected_count'] = selected[owner['declared_owner']]
        owner['remaining_count'] = owner['total_count'] - owner['selected_count']
        owner['packet_count'] = packet_counts[owner['declared_owner']]


def _select(result, groups):
    pending = deque((owner['declared_owner'], iter(_round_robin(groups[owner['declared_owner']])))
                    for owner in result['owners'])
    last = {}
    while pending and result['selected_count'] < result['total_limit']:
        owner, iterator = pending.popleft()
        row = next(iterator, None)
        if row is None:
            continue
        packet = last.get(owner)
        created = packet is None or len(packet['rows']) >= result['packet_size']
        if created:
            if len(result['packets']) >= 50:
                continue
            packet = {'declared_owner':owner, 'rows':[]}
            result['packets'].append(packet)
            last[owner] = packet
        packet['rows'].append(_entity(row))
        _update_counts(result)
        if _serialized_bytes(result) > result['maximum_bytes']:
            packet['rows'].pop()
            if created:
                result['packets'].pop()
            _update_counts(result)
            break
        pending.append((owner, iterator))


def prepare_owner_preparation(rows, *, owner_limit=12, packet_size=10, total_limit=100,
                              maximum_bytes=MAX_PACKET_BYTES):
    if (len(rows) > 5000 or any(type(value) is not int or not 1 <= value <= upper
            for value,upper in ((owner_limit, 50), (packet_size, 50), (total_limit, 500),
                                (maximum_bytes, 1024 * 1024)))):
        raise KnowledgeHubError('review preparation exceeds typed budget')
    eligible, excluded = [], 0
    for row in rows:
        if row.get('warning_equivalent') is not True and row.get('entity_type') != 'owner-gate':
            continue
        if row.get('visibility') == 'personal-local' or row.get('status') == 'personal':
            excluded += 1
            continue
        if row.get('entity_type') not in {'item', 'source', 'owner-gate'}:
            raise KnowledgeHubError('review preparation entity type is invalid')
        eligible.append(row)
    groups = defaultdict(list)
    for row in eligible:
        groups[_identity(row.get('owner'))].append(row)
    owners = []
    for owner in sorted(groups)[:owner_limit]:
        owners.append({'declared_owner':owner, 'assignment_status':'routing-declaration-only',
            'real_signer_confirmed':False, 'total_count':len(groups[owner]), 'selected_count':0,
            'remaining_count':len(groups[owner]), 'lane_counts':dict(Counter(_lane(row) for row in groups[owner])),
            'packet_count':0})
    result = {'schema_version':'knowledge-hub.review-preparation/v1', 'report_only':True, 'read_only':True,
        'eligible_count':len(eligible), 'privacy_excluded_count':excluded, 'owner_count':len(groups),
        'selected_count':0, 'remaining_count':len(eligible), 'overflow':bool(eligible),
        'maximum_bytes':maximum_bytes, 'owner_limit':owner_limit, 'packet_size':packet_size,
        'total_limit':total_limit, 'owners':owners, 'packets':[], 'owner_approval_performed':False,
        'review_dates_changed':False, 'selection_is_assignment':False, 'decision_kinds':DECISIONS,
        'machine_evidence_is_approval':False, 'retired_origin_probe_allowed':False,
        'reference_details_location':'evidence_triage.rows; dispatch only carries status counts'}
    _select(result, groups)
    if _serialized_bytes(result) > maximum_bytes:
        raise KnowledgeHubError('review preparation summary exceeds byte budget')
    return result
