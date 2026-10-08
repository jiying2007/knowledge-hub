"""Bind delegated pytest to an actual completed parent run and its full inputs."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid

from .common import working_tree_signature, utc_timestamp, load_json, pretty_json, KnowledgeHubError
from .check_dependencies import dependency_fingerprints
from .private_io import atomic_private_write


UNIT_RECEIPT = '.tmp/engineering/unit-evidence.json'


def record_parent_unit(root, source_signature, kernel_signature, result):
    if result.get('status') != 'pass' or not result.get('attempts') or result['attempts'][-1].get('exit_code') != 0:
        raise KnowledgeHubError('parent unit run did not actually pass')
    if working_tree_signature(root) != source_signature:
        raise KnowledgeHubError('parent unit inputs changed during execution')
    result_digest = hashlib.sha256(json.dumps(result, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    row = {'schema_version':1, 'run_id':uuid.uuid4().hex, 'status':'pass', 'generated_at':utc_timestamp(),
           'source_signature':source_signature, 'test_set_sha256':kernel_signature,
           'result_sha256':result_digest, 'result':result}
    atomic_private_write(root / UNIT_RECEIPT, pretty_json(row) + '\n')
    return row


def verified_parent_unit(root):
    path = root / UNIT_RECEIPT
    if not path.is_file() or path.is_symlink():
        return None
    try:
        row = load_json(path, {})
        if not isinstance(row, dict) or row.get('schema_version') != 1 or row.get('status') != 'pass' or not row.get('run_id'):
            return None
        result = row.get('result', {})
        if not isinstance(result, dict) or result.get('status') != 'pass' or not result.get('attempts'):
            return None
        if result['attempts'][-1].get('exit_code') != 0 or '-m pytest -q' not in result.get('command', ''):
            return None
        actual = hashlib.sha256(json.dumps(result, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if actual != row.get('result_sha256'):
            return None
        age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(row['generated_at'].replace('Z', '+00:00'))
        if not 0 <= age.total_seconds() <= 86400 or row.get('source_signature') != working_tree_signature(root):
            return None
        if row.get('test_set_sha256') != dependency_fingerprints(root)['kernel']:
            return None
        return {key:row[key] for key in ('run_id', 'generated_at', 'source_signature', 'test_set_sha256', 'result_sha256')}
    except (KnowledgeHubError, OSError, ValueError, KeyError, TypeError, AttributeError):
        return None
