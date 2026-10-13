"""Public activity receipt reconciliation, independent of candidate operations."""

import re
import datetime as dt

from .common import KnowledgeHubError, resolve_inside, file_sha256, load_json


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
