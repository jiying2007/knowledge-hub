"""Bounded metadata-only review events; throughput is not current-state stock."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re

from .common import KnowledgeHubError, read_utf8_bounded, utc_timestamp, pretty_json
from .private_io import atomic_private_write, PrivateWriteUncertain
from .review_state import validate_identity_text

_FIELDS = {'event_id', 'item_id', 'decision', 'body_sha256', 'cycle_sha256',
           'review_seconds', 'reviewed_at', 'recorded_at'}
_FINGERPRINTS = {'reviewer_sha256', 'evidence_sha256'}
_CYCLE_DATES = {'next_review_at', 'valid_until'}
_DECISIONS = ('accepted', 'deferred', 'changes-requested')


def _validate_event(row):
    if not isinstance(row, dict) or set(row) not in (_FIELDS, _FIELDS | _FINGERPRINTS | _CYCLE_DATES):
        raise KnowledgeHubError('review event fields are invalid')
    validate_identity_text(row['item_id'], 'event item identity', 160)
    if row['decision'] not in _DECISIONS:
        raise KnowledgeHubError('review event decision is invalid')
    for field in ('event_id', 'body_sha256', 'cycle_sha256') + tuple(_FINGERPRINTS & set(row)):
        if not isinstance(row[field], str) or not re.fullmatch(r'[a-f0-9]{64}', row[field]):
            raise KnowledgeHubError('review event hash is invalid')
    date = row['reviewed_at']
    if not isinstance(date, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
        raise KnowledgeHubError('review event date is invalid')
    dt.date.fromisoformat(date)
    for field in _CYCLE_DATES & set(row):
        value = row[field]
        if not isinstance(value, str) or (value and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value)):
            raise KnowledgeHubError('review event cycle date is invalid')
        if value:
            dt.date.fromisoformat(value)
    stamp = row['recorded_at']
    if not isinstance(stamp, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', stamp):
        raise KnowledgeHubError('review event timestamp is invalid')
    dt.datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%SZ')
    seconds = row['review_seconds']
    if seconds is not None and (type(seconds) not in (int, float)
                               or not 0 <= seconds <= 86400 or not math.isfinite(seconds)):
        raise KnowledgeHubError('review event duration is invalid')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise KnowledgeHubError('review event history has duplicate JSON fields')
        result[key] = value
    return result


def _load_events(path):
    raw = read_utf8_bounded(path, 4 * 1024 * 1024, 'review event history') if path.exists() else ''
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object) if raw else {'schema_version':1, 'events':[]}
    except (ValueError, RecursionError) as exc:
        raise KnowledgeHubError('review event history JSON is invalid') from exc
    if (not isinstance(value, dict) or set(value) != {'schema_version', 'events'}
            or type(value['schema_version']) is not int or value['schema_version'] != 1
            or not isinstance(value['events'], list) or len(value['events']) > 5000):
        raise KnowledgeHubError('review event history schema is invalid')
    seen = set()
    for row in value['events']:
        _validate_event(row)
        if row['event_id'] in seen:
            raise KnowledgeHubError('review event history contains duplicate identities')
        seen.add(row['event_id'])
    return value, hashlib.sha256(raw.encode()).hexdigest() if raw else ''


def _make_event(item_id, consumption, review_event_id):
    if not isinstance(review_event_id, str):
        raise KnowledgeHubError('review event identity must be a string')
    event = {key:consumption[key] for key in ('decision', 'body_sha256', 'cycle_sha256',
                                            'review_seconds', 'reviewed_at')}
    event.update(item_id=item_id, recorded_at=utc_timestamp())
    event.update({key:consumption[key] for key in _CYCLE_DATES})
    for source, target in (('reviewer', 'reviewer_sha256'), ('evidence_ref', 'evidence_sha256')):
        value = validate_identity_text(consumption[source], source)
        event[target] = hashlib.sha256(value.encode()).hexdigest()
    if review_event_id:
        identity = validate_identity_text(review_event_id, 'review event identity', 160)
        identity = json.dumps([item_id, identity], ensure_ascii=False)
    else:
        identity = json.dumps(dict(event, recorded_at=''), sort_keys=True, ensure_ascii=False)
    event['event_id'] = hashlib.sha256(identity.encode()).hexdigest()
    _validate_event(event)
    return event


def validate_event_identity(root, item_id, consumption, review_event_id=''):
    """Reject known event conflicts before the current-state write is attempted."""
    event = _make_event(item_id, consumption, review_event_id)
    value, _ = _load_events(root / '.tmp/review-consumption/events.json')
    previous = next((row for row in value['events'] if row['event_id'] == event['event_id']), None)
    if previous is not None and dict(previous, recorded_at='') != dict(event, recorded_at=''):
        raise KnowledgeHubError('review event identity has conflicting metadata')
    return event['event_id']


def append_event(root, item_id, consumption, review_event_id=''):
    """Retry one call idempotently; distinct identical reviews need explicit identity."""
    event = _make_event(item_id, consumption, review_event_id)
    return append_prepared_event(root, event)


def append_prepared_event(root, event):
    """Flush an original event from the state outbox without rebuilding its dates."""
    _validate_event(event)
    path = root / '.tmp/review-consumption/events.json'
    for attempt in range(3):
        value, expected = _load_events(path)
        previous = next((row for row in value['events'] if row['event_id'] == event['event_id']), None)
        if previous is not None:
            if dict(previous, recorded_at='') != dict(event, recorded_at=''):
                raise KnowledgeHubError('review event identity has conflicting metadata')
        if previous is None and len(value['events']) >= 5000:
            raise KnowledgeHubError('review event history exceeds budget; rotate explicitly')
        if previous is None:
            value['events'].append(event)
        content = pretty_json(value) + '\n'
        if len(content.encode()) > 4 * 1024 * 1024:
            raise KnowledgeHubError('review event history exceeds byte budget')
        try:
            atomic_private_write(path, content, expected_sha256=expected)
            return 'already-recorded' if previous is not None else 'recorded'
        except PrivateWriteUncertain:
            raise
        except KnowledgeHubError as exc:
            if str(exc) != 'private write expected hash conflict' or attempt == 2:
                raise
    raise KnowledgeHubError('review event retry budget exhausted')


def prepare_event(root, item_id, consumption, review_event_id, pending):
    event = _make_event(item_id, consumption, review_event_id)
    history, _ = _load_events(root / '.tmp/review-consumption/events.json')
    previous = next((row for row in history['events'] + pending if row['event_id'] == event['event_id']), None)
    if previous is not None:
        ignored = {'recorded_at', 'reviewed_at', 'valid_until'} if review_event_id else {'recorded_at'}
        if {k:v for k,v in previous.items() if k not in ignored} != {k:v for k,v in event.items() if k not in ignored}:
            raise KnowledgeHubError('review event identity has conflicting metadata')
        return previous, True
    return event, False


def validate_pending(events):
    if not isinstance(events, list) or len(events) > 5000:
        raise KnowledgeHubError('pending review events exceed schema budget')
    seen = set()
    for event in events:
        _validate_event(event)
        if event['event_id'] in seen:
            raise KnowledgeHubError('pending review events contain duplicate identities')
        seen.add(event['event_id'])


def event_metrics(root, as_of):
    try:
        if type(as_of) is not dt.date:
            raise KnowledgeHubError('review metrics require a date')
        value, _ = _load_events(root / '.tmp/review-consumption/events.json')
        start = (as_of - dt.timedelta(days=29)).isoformat()
        recent = [row for row in value['events'] if start <= row['reviewed_at'] <= as_of.isoformat()]
        durations = [row['review_seconds'] for row in recent if row['review_seconds'] is not None]
        return {'status':'pass', 'measurement_scope':'review-event-throughput',
                'window_days':30, 'window_start':start, 'window_end':as_of.isoformat(),
                'history_available':(root / '.tmp/review-consumption/events.json').exists(),
                'coverage':'recorded-events-only',
                'event_count':len(recent), 'distinct_items':len({row['item_id'] for row in recent}),
                'timed_review_count':len(durations), 'untimed_review_count':len(recent) - len(durations),
                'review_seconds_total':sum(durations), 'preparation_is_review_time':False,
                'decision_counts':{key:sum(row['decision'] == key for row in recent) for key in _DECISIONS},
                'owner_approval':False}
    except (OSError, ValueError, KeyError, TypeError, OverflowError, KnowledgeHubError):
        return {'status':'needs-review', 'measurement_scope':'review-event-throughput',
                'event_count':None, 'review_seconds_total':None, 'owner_approval':False}
