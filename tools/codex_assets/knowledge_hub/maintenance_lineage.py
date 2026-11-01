"""Resolve historical evidence targets through exact maintenance manifests.

This is evidence navigation only, never a workspace alias or owner approval.
"""
from .common import file_sha256, load_json, registry_items, resolve_inside


def historical_target(root, source):
    candidates = set()
    current = {row['id']: row for row in registry_items(root)}
    for path in (root / 'artifacts/manifests').glob('content-maintenance-*.json'):
        report = load_json(path)
        expected = report.get('deletes', {}).get(source)
        if (not expected or report.get('inputs', {}).get(source) != expected
                or report.get('active_promoted') is not False or report.get('owner_review_performed') is not False):
            continue
        for entry in report.get('request', {}).get('items', []):
            target = entry.get('target_path')
            item = current.get(entry.get('item_id'))
            if (not target or not item or item['path'] != target or entry.get('expected_sha256') != expected):
                continue
            file = resolve_inside(root, target)
            if file.is_file() and file_sha256(file) == report.get('result_writes', {}).get(target):
                candidates.add(target)
    return next(iter(candidates)) if len(candidates) == 1 else ''
