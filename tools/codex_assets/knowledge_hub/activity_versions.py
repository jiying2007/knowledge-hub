"""Resolve explicit fact revisions; unordered conflicting legacy facts stay unknown."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re

from .common import KnowledgeHubError


def version_fields(payload):
    result = {}
    if 'revision' in payload:
        value = payload['revision']
        if type(value) is not int or not 1 <= value <= 1000000:
            raise KnowledgeHubError('fact revision must be a positive bounded integer')
        result['revision'] = value
    if 'supersedes_sha256' in payload:
        value = payload['supersedes_sha256']
        if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
            raise KnowledgeHubError('fact supersedes hash is invalid')
        result['supersedes_sha256'] = value
    if result.get('revision', 1) > 1 and 'supersedes_sha256' not in result:
        raise KnowledgeHubError('fact revision after one requires supersedes_sha256')
    if 'observed_at' in payload:
        result['observed_at'] = parse_observed_at(payload['observed_at']).isoformat()
    return result


def parse_observed_at(value):
    if not isinstance(value, str) or len(value) > 80:
        raise KnowledgeHubError('observed_at must be a bounded timestamp')
    try:
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise KnowledgeHubError('observed_at is invalid') from exc
    if parsed.tzinfo is None:
        raise KnowledgeHubError('observed_at requires an explicit timezone')
    return parsed.astimezone(dt.timezone.utc)


def fact_sha256(item):
    value = {key:val for key,val in item.items() if key != 'source'}
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def resolve_facts(groups, knowledge_as_of=None):
    cutoff = parse_observed_at(knowledge_as_of) if knowledge_as_of else None
    selected, conflicts = [], []
    undated = 0
    for key, values in sorted(groups.items()):
        unique = {}
        for item in values:
            if cutoff:
                if not item.get('observed_at'):
                    undated += 1
                    continue
                if parse_observed_at(item['observed_at']) > cutoff:
                    continue
            unique[fact_sha256(item)] = item
        ordered = sorted(unique.values(), key=lambda item:item.get('revision', 0))
        if not ordered:
            continue
        first_revision = ordered[0].get('revision')
        anchored = first_revision in (None, 1)
        valid = len(ordered) == 1 and anchored
        if len(ordered) > 1:
            valid = anchored and all(item.get('revision') for item in ordered)
            for before, after in zip(ordered, ordered[1:]):
                valid = valid and after.get('revision', 0) == before.get('revision', 0) + 1
                valid = valid and after.get('supersedes_sha256') == fact_sha256(before)
                if before.get('observed_at') and after.get('observed_at'):
                    valid = valid and parse_observed_at(before['observed_at']) <= parse_observed_at(after['observed_at'])
        if valid:
            selected.append(ordered[-1])
        else:
            conflicts.append({'subject_id':key[0], 'project_id':key[1], 'item_id':key[2],
                              'fact_hashes':sorted(unique),
                              'activity_dates':sorted({item.get('activity_date', '') for item in ordered}),
                              'reason':'lineage-unknown' if not anchored else 'unordered-or-invalid-revisions'})
    return selected, conflicts, undated
