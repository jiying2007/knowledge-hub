"""Public read-only content reconciliation; presence never implies owner approval."""

from __future__ import annotations

import re
import datetime as dt

from .common import KnowledgeHubError, registry_items, route_rows, resolve_inside, file_sha256, load_markdown, load_json
from .model import FRONTMATTER_MIRROR_FIELDS


def reconcile_archive(root, project, operation_id, expected_sha256=''):
    if not re.fullmatch(r'[a-f0-9]{64}', operation_id):
        raise KnowledgeHubError('reconciliation requires the exact operation identity')
    routes = [row for row in route_rows(root) if row.get('project_id') == project]
    if len(routes) != 1:
        raise KnowledgeHubError('reconciliation requires one explicit project route')
    item_id = 'provider-{}-{}'.format(project, operation_id[:24])
    item = next((row for row in registry_items(root) if row.get('id') == item_id), None)
    result = {'status':'NOT_FOUND', 'read_only':True, 'operation_id':operation_id, 'persisted':False,
              'content_verified':False, 'owner_review_performed':False, 'active_promoted':False}
    if item is None:
        return result
    bases = [routes[0].get(key, '') for key in ('validation_path', 'archive_path')]
    if (item.get('source', {}).get('type') != 'provider-candidate-archive'
            or 'operation:' + operation_id not in item.get('source', {}).get('from', '')
            or not any(base and item['path'].startswith(base + '/') for base in bases)):
        return dict(result, status='CONFLICT')
    target = resolve_inside(root, item['path'])
    if not target.is_file():
        return dict(result, status='CONFLICT')
    metadata, _ = load_markdown(target)
    actual = file_sha256(target)
    mirrors = all(metadata.get(key) == item.get(key) for key in FRONTMATTER_MIRROR_FIELDS if key in item)
    verified = bool(expected_sha256 and actual == expected_sha256 and mirrors)
    return dict(result, status='VERIFIED' if verified else 'PRESENT_UNVERIFIED', persisted=True,
                content_verified=verified, content_sha256=actual, item_id=item_id,
                candidate_status=item.get('status'), target=item['path'], durable_acknowledgement=False)


def reconcile_activity(root, receipt_id, receipt_date, expected_sha256=''):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+-]{0,159}', receipt_id):
        raise KnowledgeHubError('receipt identity is invalid')
    date = dt.date.fromisoformat(receipt_date).isoformat()
    relative = '.tmp/activity/receipts/{}/{}.json'.format(date, receipt_id)
    target = resolve_inside(root, relative)
    result = {'status':'NOT_FOUND', 'read_only':True, 'receipt_id':receipt_id, 'persisted':False, 'content_verified':False}
    if target.is_file():
        payload = load_json(target)
        if not isinstance(payload, dict) or payload.get('kind') != 'activity-session-receipt':
            return dict(result, status='CONFLICT')
        actual = file_sha256(target)
        verified = bool(expected_sha256 and actual == expected_sha256)
        return dict(result, status='VERIFIED' if verified else 'PRESENT_UNVERIFIED', persisted=True,
                    content_verified=verified, sha256=actual, durable_acknowledgement=False)
    return result
