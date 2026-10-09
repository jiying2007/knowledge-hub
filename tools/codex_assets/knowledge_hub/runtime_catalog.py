"""Metadata-only retention inventory. No new artifact category is deleted here."""

from __future__ import annotations

import datetime as dt
import json
from collections import deque

from .common import KnowledgeHubError, read_utf8_bounded, resolve_inside


SCOPES = {
    'activity-receipts':('.tmp/activity/receipts', 365),
    'activity-history':('.tmp/activity/receipt-history', 365),
    'activity-items':('.tmp/activity/items', 365),
    'review-consumption':('.tmp/review-consumption', 365),
    'engineering-evidence':('.tmp/engineering', 30),
    'governed-provider':('.tmp/governed-provider', 365),
    'query-traces':('.cache/knowledge-hub', 30),
}


def runtime_catalog(root, today, maximum_files=5000, maximum_bytes=256 * 1024 * 1024):
    if type(maximum_files) is not int or not 1 <= maximum_files <= 10000:
        raise KnowledgeHubError('runtime inventory exceeds budget')
    if type(maximum_bytes) is not int or not 1 <= maximum_bytes <= 1024 * 1024 * 1024:
        raise KnowledgeHubError('runtime inventory byte budget is invalid')
    rows, errors, categories = [], [], {}
    overflow, examined, total_bytes = False, 0, 0
    pending = deque()
    order = ['governed-provider'] + [name for name in SCOPES if name != 'governed-provider']
    for category in order:
        relative, retention = SCOPES[category]
        directory = root / relative
        categories[category] = {'examined':0, 'files':0, 'bytes':0, 'unknown':0, 'scan_complete':False}
        if directory.is_symlink():
            errors.append(category + ':symlink-directory')
            continue
        if not directory.is_dir():
            categories[category]['scan_complete'] = True
        else:
            pending.append((category, retention, iter(directory.rglob('*'))))
    while pending:
        category, retention, iterator = pending.popleft()
        try:
            path = next(iterator)
        except StopIteration:
            categories[category]['scan_complete'] = True
            continue
        if examined >= maximum_files:
            overflow = True
            break
        examined += 1
        categories[category]['examined'] += 1
        pending.append((category, retention, iterator))
        if path.is_dir() and not path.is_symlink():
            continue
        try:
            row = _entry(root, path, category, retention, today)
            total_bytes += row['size_bytes']
            if total_bytes > maximum_bytes:
                overflow = True
                break
            rows.append(row)
            categories[category]['files'] += 1
            categories[category]['bytes'] += row['size_bytes']
            if row['protected_reason'] == 'unknown-operation-state':
                categories[category]['unknown'] += 1
        except (OSError, KnowledgeHubError, ValueError):
            errors.append(category + ':unreadable-or-invalid')
            categories[category]['unknown'] += 1
    return {'schema_version':1, 'status':'needs-review' if errors or overflow else 'pass',
            'report_only':True, 'deletion_authorized':False, 'overflow':overflow, 'file_count':len(rows),
            'total_bytes':total_bytes, 'examined_count':examined, 'maximum_files':maximum_files,
            'maximum_bytes':maximum_bytes, 'rows':rows, 'errors':errors, 'categories':categories,
            'policy':'Retain authoritative facts; protect pending/unknown operations; review expired artifacts before deletion.'}


def _entry(root, path, category, retention, today):
    resolve_inside(root, str(path.relative_to(root)))
    if not path.is_file() or path.is_symlink():
        raise KnowledgeHubError('non-regular runtime input')
    stat = path.stat()
    age = max(0, (today - dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc).date()).days)
    return {'path':str(path.relative_to(root)), 'category':category, 'size_bytes':stat.st_size,
            'age_days':age, 'retention_days':retention, 'protected_reason':_protection(category, path),
            'retention_due':age >= retention, 'action':'report-only'}


def _protection(category, path):
    if category == 'governed-provider':
        state_path = path if path.name.endswith('.state.json') else path.with_suffix('.state.json')
        try:
            state = json.loads(read_utf8_bounded(state_path, 128 * 1024, 'operation state'))
            stage = state.get('stage') if isinstance(state, dict) else None
            return 'pending-or-unknown-operation' if stage != 'verified' else 'verified-operation-provenance'
        except (OSError, KnowledgeHubError, ValueError):
            return 'unknown-operation-state'
    return {'activity-receipts':'authoritative-activity-facts', 'activity-history':'revision-provenance',
            'activity-items':'authoritative-activity-facts', 'review-consumption':'cycle-state',
            'engineering-evidence':'source-bound-evidence', 'query-traces':'privacy-retention-review'}[category]
