"""Read-only classification of hash-bound reported commands, never execution proof."""

from __future__ import annotations

import datetime as dt
import hashlib
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .common import (DEFAULT_MARKDOWN_MAX_BYTES, KnowledgeHubError, load_jsonl,
                     normalize_relpath, split_frontmatter)
from .model import FRONTMATTER_MIRROR_FIELDS
from .provider_operations import operations
from .provider_subjects import item_subject

ORIGINAL_ARGV = ('rtk', 'bash', 'tools/knowledge-source-check.sh', '--scope', 'current', '--json', '--strict')
ORIGINAL_COMMAND = ' '.join(ORIGINAL_ARGV)
RELATIVE_NEEDLE = 'rtk bash tools/'
HISTORY = re.compile(r'^实际运行 `(?P<command>' + re.escape(ORIGINAL_COMMAND) + r')`，结果 (?P<result>pass)。', re.M)
HISTORY_SENTENCE = '实际运行 `' + ORIGINAL_COMMAND + '`，结果 pass。'
# A deliberately finite grammar, not a natural-language instruction detector.
# Unknown suffixes remain findings even when their Provider record is intact.
HISTORY_DECLARATION = (
    '逐项确认 Hub source 控制目录存在，已登记 origin 存在，并阅读现行 source-policy 和 registry 中的 '
    'role、authority、source_strategy、write_policy。控制文件逐项计算 SHA256；未读取、复制或导出原始 '
    'memory、history、session 正文，未修改任何 origin。'
)
HISTORY_PARAGRAPHS = frozenset({HISTORY_SENTENCE, HISTORY_SENTENCE + HISTORY_DECLARATION})
PROTECTED_FIELDS = set(FRONTMATTER_MIRROR_FIELDS) | {
    'subject_ref', 'created_subject_ref', 'principal_id', 'provider_operation_id', 'source', 'created_at',
}
REJECTION_CODES = frozenset({
    'registry-path-not-unique', 'not-typed-public-history', 'archive-identity-unbound',
    'current-proof-unbound', 'proof-history-discontinuous', 'unsupported-markdown-context',
    'history-occurrence-not-single', 'mixed-history-and-instruction',
    'full-document-occurrence-not-single', 'history-input-budget', 'registry-id-not-unique',
    'frontmatter-identity-mismatch', 'historical-date-unbound', 'provider-proof-unavailable',
    'invalid-history-input',
})


def _refuse(reason: str) -> Dict[str, Any]:
    return {'record': None, 'rejection_reason': reason if reason in REJECTION_CODES else 'invalid-history-input'}


def _typed_item(relative: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(items) != 1:
        raise KnowledgeHubError('registry-path-not-unique')
    item = items[0]
    if (normalize_relpath(relative) != relative or not relative.startswith('governance/product/validation/')
            or not relative.endswith('.md') or item.get('path') != relative
            or item.get('kind') != 'validation' or item.get('status') != 'reviewing'
            or item.get('visibility') not in {'team-internal', 'public'}
            or item.get('source', {}).get('type') != 'provider-candidate-archive'):
        raise KnowledgeHubError('not-typed-public-history')
    return item


def _bound_proof(item: Dict[str, Any], history: List[Dict[str, Any]], raw_hash: str) -> Dict[str, Any]:
    archive_id = item.get('provider_operation_id')
    if (not isinstance(archive_id, str) or re.fullmatch(r'[a-f0-9]{64}', archive_id) is None
            or item.get('source', {}).get('from') != 'operation:' + archive_id
            or not history or history[0]['action'] != 'archive'
            or history[0]['operation_id'] != archive_id
            or history[0]['before_content_sha256'] is not None):
        raise KnowledgeHubError('archive-identity-unbound')
    initial, latest = history[0], history[-1]
    created = item.get('created_subject_ref')
    target = item_subject(item)
    if (not target or target['type'] in {'personal', 'unassigned'} or not created
            or initial['created_subject_ref'] != created or initial['subject_ref'] != created
            or initial['principal_id'] != item.get('principal_id')
            or latest['subject_ref'] != target or latest['content_sha256'] != raw_hash):
        raise KnowledgeHubError('current-proof-unbound')
    previous = initial
    for row in history[1:]:
        if (row['action'] not in {'metadata', 'assign'} or row['created_subject_ref'] != created
                or row['before_content_sha256'] != previous['content_sha256']
                or row['action'] == 'metadata' and row['subject_ref'] != previous['subject_ref']):
            raise KnowledgeHubError('proof-history-discontinuous')
        previous = row
    return latest


def _history_span(body: str) -> re.Match[str]:
    # Unknown containers are rejected rather than stripped or guessed away.
    if (any(token in body for token in ('\\', '<', '>', '```', '~~~', '[', ']'))
            or body.count('`') != 2
            or re.search(r'(?m)^(?:[ \t]+|[-+*] |\d+[.)]\s)', body)):
        raise KnowledgeHubError('unsupported-markdown-context')
    matches = list(HISTORY.finditer(body))
    if len(matches) != 1 or body.count(RELATIVE_NEEDLE) != 1:
        raise KnowledgeHubError('history-occurrence-not-single')
    match = matches[0]
    line_end = body.find('\n', match.start())
    line_end = len(body) if line_end < 0 else line_end
    line = body[match.start():line_end]
    before = body[:match.start()]
    after = body[line_end:]
    if (line not in HISTORY_PARAGRAPHS or before and not before.endswith('\n\n')
            or after not in {'', '\n'} and not after.startswith('\n\n')):
        raise KnowledgeHubError('mixed-history-and-instruction')
    return match


def _record(item: Dict[str, Any], text: str, body: str, latest: Dict[str, Any],
            raw_hash: str, recorded: dt.date, match: re.Match[str]) -> Dict[str, Any]:
    start = len(text) - len(body) + match.start('command')
    end = len(text) - len(body) + match.end('command')
    if text.count(RELATIVE_NEEDLE) != 1 or text[start:end] != ORIGINAL_COMMAND:
        raise KnowledgeHubError('full-document-occurrence-not-single')
    derived = list(ORIGINAL_ARGV)
    derived[2] = '~/knowledge-hub/' + derived[2]
    return {
        'classification': 'historical-execution-provenance', 'item_id': item['id'], 'path': item['path'],
        'line': text.count('\n', 0, start) + 1, 'span': {'start': start, 'end': end},
        'record_content_sha256': raw_hash, 'archive_operation_id': item['provider_operation_id'],
        'latest_operation_id': latest['operation_id'], 'subject_ref': latest['subject_ref'],
        'recorded_date': recorded.isoformat(), 'original_argv': list(ORIGINAL_ARGV),
        'reported_result': match.group('result'), 'derived_cwd_stable_argv': derived,
        'derived_command': ' '.join(derived), 'record_integrity_verified': True,
        'execution_verified': False, 'derived_entry_executed': False, 'historical_cwd_known': False,
        'equivalence_verified': False, 'content_approval_performed': False,
        'note': '当前Hub契约的cwd稳定参考入口，历史等价性未验证；本次未新增执行。',
    }


@dataclass
class CommandEvidence:
    today: dt.date
    by_path: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    by_item: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    id_counts: Dict[str, int] = field(default_factory=dict)
    load_failure: str = ''

    def classify(self, relative: str, raw: bytes) -> Dict[str, Any]:
        if self.load_failure:
            return _refuse(self.load_failure)
        try:
            return self._classify(relative, raw)
        except KnowledgeHubError as error:
            return _refuse(str(error))
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
            return _refuse('invalid-history-input')

    def _classify(self, relative: str, raw: bytes) -> Dict[str, Any]:
        if not isinstance(raw, bytes) or len(raw) > DEFAULT_MARKDOWN_MAX_BYTES:
            raise KnowledgeHubError('history-input-budget')
        item = _typed_item(relative, self.by_path.get(relative, []))
        if self.id_counts.get(item['id']) != 1:
            raise KnowledgeHubError('registry-id-not-unique')
        text = raw.decode('utf-8')
        metadata, body = split_frontmatter(text)
        if not metadata or any(
                (key in metadata) != (key in item) or metadata.get(key) != item.get(key)
                for key in PROTECTED_FIELDS):
            raise KnowledgeHubError('frontmatter-identity-mismatch')
        raw_hash = hashlib.sha256(raw).hexdigest()
        latest = _bound_proof(item, self.by_item.get(item['id'], []), raw_hash)
        recorded = dt.date.fromisoformat(item['created_at'])
        date_match = re.match(r'^(\d{4}-\d{2}-\d{2})\s', body)
        if not date_match or dt.date.fromisoformat(date_match.group(1)) != recorded or recorded >= self.today:
            raise KnowledgeHubError('historical-date-unbound')
        match = _history_span(body)
        return {'record': _record(item, text, body, latest, raw_hash, recorded, match), 'rejection_reason': ''}


def load_evidence(root: pathlib.Path, today: dt.date) -> CommandEvidence:
    """Validate bounded Provider history once per scanner batch; never write or run commands."""
    result = CommandEvidence(today)
    try:
        if type(today) is not dt.date:
            raise KnowledgeHubError('invalid-scanner-date')
        items = load_jsonl(root / 'registry/items.jsonl')
        rows = operations(root)
        for item in items:
            result.by_path.setdefault(item.get('path', ''), []).append(item)
            ident = item.get('id', '')
            result.id_counts[ident] = result.id_counts.get(ident, 0) + 1
        for row in rows:
            result.by_item.setdefault(row['item_id'], []).append(row)
    except (KnowledgeHubError, OSError, ValueError, TypeError, KeyError):
        return CommandEvidence(today, load_failure='provider-proof-unavailable')
    return result


def instruction_occurrences(text: str, patterns: List[Tuple[str, str]], record: Any = None) -> List[Dict[str, Any]]:
    """Retain every original pattern occurrence outside the one proven command span."""
    findings = []
    span = record['span'] if record else None
    for pattern_id, needle in patterns:
        offset = 0
        while True:
            start = text.find(needle, offset)
            if start < 0:
                break
            end = start + len(needle)
            offset = end
            if span and span['start'] <= start and end <= span['end']:
                continue
            line_start = text.rfind('\n', 0, start) + 1
            line_end = text.find('\n', end)
            line_end = len(text) if line_end < 0 else line_end
            findings.append({'pattern_id': pattern_id, 'line': text.count('\n', 0, start) + 1,
                             'sample': text[line_start:line_end].strip()[:240], 'offset': start})
    return sorted(findings, key=lambda row: (row['offset'], row['pattern_id']))
