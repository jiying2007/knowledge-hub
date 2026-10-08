"""Versioned packet consumption is scoped to a review cycle, never owner approval."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re

from .common import KnowledgeHubError, file_sha256, read_utf8_bounded
from .security import scan_secret_text


def load_state(path):
    entries, _, expected = load_consumption_state(path)
    return entries, expected


def load_consumption_state(path):
    from .review_events import _unique_object, validate_pending
    raw = read_utf8_bounded(path, 4 * 1024 * 1024, 'review state') if path.exists() else ''
    try:
        document = json.loads(raw, object_pairs_hook=_unique_object) if raw else {}
    except (ValueError, RecursionError) as exc:
        raise KnowledgeHubError('review consumption JSON is invalid') from exc
    if not isinstance(document, dict):
        raise KnowledgeHubError('review state must be an object')
    if 'schema_version' in document:
        if type(document['schema_version']) is not int or document['schema_version'] != 2:
            raise KnowledgeHubError('review state version is unsupported')
        entries = document.get('entries')
    else:
        entries = document
    pending = document.get('pending_events', []) if 'schema_version' in document else []
    validate_pending(pending)
    if not isinstance(entries, dict) or len(entries) > 5000:
        raise KnowledgeHubError('review state entries exceed the schema budget')
    for key, value in entries.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            raise KnowledgeHubError('review state entry is malformed')
        if value.get('decision') not in ('accepted', 'deferred', 'changes-requested'):
            raise KnowledgeHubError('review decision is invalid')
        for field in ('body_sha256', 'cycle_sha256'):
            if field in value and (not isinstance(value[field], str) or not re.fullmatch(r'[a-f0-9]{64}', value[field])):
                raise KnowledgeHubError('review state hash is invalid')
        for field in ('next_review_at', 'valid_until', 'reviewed_at'):
            date = value.get(field, '')
            if not isinstance(date, str):
                raise KnowledgeHubError('review state date must be a string')
            if date:
                dt.date.fromisoformat(date)
        seconds = value.get('review_seconds')
        if seconds is not None and (type(seconds) not in (int, float) or not 0 <= seconds <= 86400 or not math.isfinite(seconds)):
            raise KnowledgeHubError('review time must be finite and bounded')
    return entries, pending, hashlib.sha256(raw.encode()).hexdigest() if raw else ''


def cycle_sha256(root, item):
    fields = ('id', 'owner', 'status', 'review_after', 'evidence_refs', 'evidence_validation_status', 'source')
    value = {key:item.get(key) for key in fields}
    risk = root / 'registry/review-risk-policy.json'
    value['risk_policy_sha256'] = file_sha256(risk) if risk.exists() else ''
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate_identity_text(value, label, maximum=600):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or scan_secret_text(value):
        raise KnowledgeHubError(label + ' requires bounded sanitized explicit text')
    return value.strip()
