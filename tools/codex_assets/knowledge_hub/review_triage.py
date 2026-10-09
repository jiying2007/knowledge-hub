"""Read-only evidence preparation; mechanical checks never renew human review."""

from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import pathlib
import itertools
import re

from .common import KnowledgeHubError, split_frontmatter, read_repository_bytes_bounded, resolve_inside
from .review_state import load_consumption_state
from .review_preparation import prepare_owner_preparation


MAX_ENTITIES = 5000
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024


class _EvidenceReader:
    def __init__(self, root):
        self.root = root
        self.total = 0
        self.results = {}
        self.overflow = False

    def read(self, relative):
        if relative in self.results:
            return self.results[relative]
        raw = self.confirm(relative)
        self.results[relative] = raw
        return raw

    def confirm(self, relative):
        path = resolve_inside(self.root, relative)
        if not path.is_file():
            raise KnowledgeHubError('evidence file is unavailable')
        remaining = MAX_TOTAL_BYTES - self.total
        if remaining <= 0:
            self.overflow = True
            raise KnowledgeHubError('review evidence total byte budget exceeded')
        maximum = min(MAX_FILE_BYTES, remaining)
        if path.stat().st_size > maximum:
            self.overflow = True
            raise KnowledgeHubError('review evidence byte budget exceeded')
        raw = read_repository_bytes_bounded(self.root, relative, maximum, 'review evidence')
        self.total += len(raw)
        return raw


def _reference(reader, value):
    if not isinstance(value, str):
        return {'status':'invalid', 'reference_sha256':''}
    digest = hashlib.sha256(value.encode()).hexdigest()
    row = {'reference_sha256':digest, 'reuse_scope':'provenance-only', 'semantic_verified':False}
    if value.startswith('rtk '):
        return dict(row, status='replay-command-not-executed')
    if '://' in value or value.startswith(('~', '/')):
        return dict(row, status='external-evidence-required')
    relative = value.split('#', 1)[0]
    try:
        present = resolve_inside(reader.root, relative).is_file()
    except (KnowledgeHubError, OSError, ValueError):
        present = False
    if not present:
        kind = _unresolved_reference_kind(value)
        if kind != 'local-path':
            return dict(row, status=kind)
    try:
        raw = reader.read(relative)
        return dict(row, status='local-hash-confirmed', path=relative,
                    sha256=hashlib.sha256(raw).hexdigest())
    except (KnowledgeHubError, OSError, ValueError):
        return dict(row, status='local-unavailable-or-over-budget')


def _unresolved_reference_kind(value):
    # These are textual provenance pointers, never parsed into executable argv.
    if re.match(r'^(?:tools|scripts)/[^\s]+\.(?:sh|py)\s+', value):
        return 'legacy-replay-not-executed'
    if (re.match(r'^[A-Za-z0-9_-]*(?:sha256|reason|note):', value)
            or re.match(r'^(?:原因|后续|说明|备注|等待)[：:\s]', value)):
        return 'metadata-note'
    relative = value.split('#', 1)[0]
    filename = r'[^\n\r]*\.(?:md|json|jsonl|yaml|yml|txt|csv|sh|py|toml|ini)'
    roots = r'(?:projects|domains|governance|sources|artifacts|notes|tools|scripts|registry|indexes|templates|inbox|tests|docs)'
    if (re.fullmatch(roots + '/' + filename, relative)
            or ('/' not in relative and re.fullmatch(filename, relative))):
        return 'local-path'
    return 'unknown-pointer'


def _body_evidence(reader, item):
    try:
        relative = item.get('path', '')
        raw = reader.read(relative)
        metadata, _ = split_frontmatter(raw.decode('utf-8'))
        # Parse the same bounded snapshot as its hash; confirm it is still live.
        after = reader.confirm(relative)
        if after != raw:
            raise KnowledgeHubError('review body changed during preparation')
        if type(metadata.get('review_after')) is dt.date:
            metadata['review_after'] = metadata['review_after'].isoformat()
        mirrored = all(metadata.get(field) == item.get(field)
                       for field in ('id', 'owner', 'status', 'review_after', 'path') if field in metadata)
        declared = item.get('human_review_content_sha256', '')
        actual = hashlib.sha256(raw).hexdigest()
        return {'status':'metadata-ready' if mirrored else 'metadata-mismatch', 'sha256':actual,
                'frontmatter_mirror':mirrored, 'prior_human_content_hash_matches':bool(declared and declared == actual),
                'human_review_renewed':False}
    except (KnowledgeHubError, OSError, ValueError, TypeError):
        return {'status':'body-unavailable-or-over-budget', 'human_review_renewed':False}


def _source_evidence(root, source):
    relative = source.get('path', '')
    try:
        hub_present = resolve_inside(root, relative).exists()
    except (KnowledgeHubError, OSError, ValueError, TypeError):
        hub_present = False
    retired = source.get('status') == 'retired' or source.get('ledger_status') == 'retired'
    origin = source.get('origin_path', '')
    origin_status = 'retired-provenance-not-probed' if retired else 'not-declared'
    if not retired and isinstance(origin, str) and origin:
        if '://' in origin:
            origin_status = 'external-evidence-required'
        else:
            path = pathlib.Path(origin).expanduser()
            origin_status = 'present' if (path if path.is_absolute() else root / path).exists() else 'unavailable'
    return {'hub_path_present':hub_present, 'origin_status':origin_status,
            'retired_provenance_only':retired, 'source_check_executed':False,
            'declared_check_present':bool(source.get('check')), 'authority_verified':False}


def _cache_inventory(reader, as_of):
    try:
        base = resolve_inside(reader.root, '.cache/knowledge-hub/checks')
    except (KnowledgeHubError, OSError, ValueError):
        return {'status':'needs-review', 'rows':[], 'overflow':False}
    paths = sorted(itertools.islice(base.glob('*.json'), 33))
    rows = []
    for path in paths[:32]:
        relative = str(path.relative_to(reader.root))
        row = {'name':path.name, 'reuse_allowed':False, 'binding_status':'not-verified'}
        try:
            raw = reader.read(relative)
            value = json.loads(raw)
            stamp = dt.datetime.fromisoformat(value['generated_at'].replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                raise ValueError('cache timestamp lacks timezone')
            cutoff = dt.datetime.combine(as_of, dt.time.min, dt.timezone.utc)
            age = (cutoff - stamp).total_seconds()
            # Same calendar day is not evidence of exact current age/identity.
            status = 'expired' if age > 86400 else ('future-or-current-day-unconfirmed' if age < 0 else 'age-only-unconfirmed')
            result = value.get('result')
            if not isinstance(result, dict):
                raise ValueError('cache result is invalid')
            digest = hashlib.sha256(json.dumps(result, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if digest != value.get('result_sha256'):
                status = 'invalid-result-hash'
            row.update(status=status, sha256=hashlib.sha256(raw).hexdigest(), generated_at=value['generated_at'])
        except (KnowledgeHubError, OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
            row['status'] = 'invalid-or-unavailable'
        rows.append(row)
    return {'status':'report-only', 'rows':rows, 'overflow':len(paths) > 32,
            'age_reference_utc':as_of.isoformat() + 'T00:00:00Z', 'date_only_reference':True,
            'expired_count':sum(row['status'] == 'expired' for row in rows), 'reuse_authorized':False}


def _prepare_item(reader, item, row, state, as_of):
    evidence = _body_evidence(reader, item)
    previous = state.get(row['item_id'], {})
    expiry = previous.get('next_review_at') if previous.get('decision') == 'deferred' else previous.get('valid_until')
    cache_expired = bool(expiry and expiry <= as_of.isoformat())
    references = list(dict.fromkeys(item.get('evidence_refs', []) + item.get('validation_refs', [])))
    refs = [_reference(reader, value) for value in references[:16]]
    flags = [evidence['status']]
    if row['days_until_review'] < 0:
        flags.append('owner-semantic-review-due' if item.get('status') in ('active', 'reviewing') else 'historical-boundary-review-due')
    if not item.get('owner') or item.get('owner') in ('team-core', 'pcr02-registry-owner'):
        flags.append('real-owner-assignment-required')
    if cache_expired:
        flags.append('expired-review-cache')
    if any(ref['status'] == 'external-evidence-required' for ref in refs):
        flags.append('external-evidence-required')
    if not references:
        flags.append('evidence-not-linked')
    if any(ref['status'] == 'local-unavailable-or-over-budget' for ref in refs):
        flags.append('local-evidence-unavailable')
    if any(ref['status'] == 'unknown-pointer' for ref in refs):
        flags.append('evidence-pointer-unresolved')
    warning = row['days_until_review'] < 0 and item.get('status') in ('active', 'reviewing')
    return {'entity_type':'item', 'entity_id':item['id'], 'owner':item.get('owner', ''),
            'body_path':item.get('path', ''), 'visibility':item.get('visibility', ''),
            'status':item.get('status'), 'review_after':item.get('review_after'), 'warning_equivalent':warning,
            'classifications':flags, 'body_evidence':evidence, 'references':refs,
            'reference_overflow':len(references) > 16, 'automatic_closure_allowed':False,
            'owner_approval_performed':False, 'semantic_revalidation_required':True,
            'metadata_action':{'cwd':'repository-root', 'argv':['rtk', 'bash', 'tools/knowledge-check.sh',
                               '--dry-run', '--explain', item['id'], '--json'], 'executed':False},
            'human_action_zh':'核验当前适用性与外部证据；仅由真实负责人决定是否续期，不以 hash 相同自动接受。'}


def _prepare_source(root, reader, source, as_of):
    try:
        due = dt.date.fromisoformat(source.get('review_after', '')) < as_of
    except (ValueError, TypeError):
        due = False
    if not due:
        return None
    evidence = _source_evidence(root, source)
    flags = ['source-semantic-review-due']
    if not evidence['hub_path_present'] or evidence['origin_status'] == 'unavailable':
        flags.append('source-path-unavailable')
    if evidence['retired_provenance_only']:
        flags.append('retired-provenance-review')
    refs = [_reference(reader, value) for value in source.get('evidence_refs', [])[:16]]
    return {'entity_type':'source', 'entity_id':source['id'], 'owner':source.get('owner', ''),
            'review_after':source.get('review_after', ''),
            'status':source.get('status'), 'warning_equivalent':True, 'classifications':flags,
            'source_evidence':evidence, 'references':refs, 'automatic_closure_allowed':False,
            'source_action':{'cwd':'repository-root', 'argv':['rtk', 'bash', 'tools/knowledge-check.sh',
                            '--sources-only', '--dry-run', '--json'], 'executed':False},
            'human_action_zh':'确认当前来源或历史 provenance 边界；退役来源不恢复为当前入口，不刷新日期假复核。'}


def prepare_review_triage(root, item_rows, items, sources, owner_gates, as_of, *, detail_limit=100, packet_size=10):
    if type(as_of) is not dt.date or type(detail_limit) is not int or not 1 <= detail_limit <= 500:
        raise KnowledgeHubError('review triage requires a date and 1-500 detail limit')
    if max(len(items), len(item_rows), len(sources), len(owner_gates)) > MAX_ENTITIES:
        raise KnowledgeHubError('review triage entity budget exceeded')
    by_id = {item['id']:item for item in items}
    reader = _EvidenceReader(root)
    try:
        state, pending, _ = load_consumption_state(root / '.tmp/review-consumption/state.json')
        state_status = 'needs-review' if pending else 'pass'
    except (KnowledgeHubError, OSError, ValueError, TypeError):
        state, state_status = {}, 'needs-review'
    rows = []
    warning_counts: collections.Counter[str] = collections.Counter()
    classifications: collections.Counter[str] = collections.Counter()
    for row in item_rows:
        prepared = _prepare_item(reader, by_id[row['item_id']], row, state, as_of)
        warning_counts['stale_items'] += int(prepared['warning_equivalent'])
        classifications.update(prepared['classifications'])
        rows.append(prepared)
    for source in sources:
        prepared = _prepare_source(root, reader, source, as_of)
        if prepared is None:
            continue
        classifications.update(prepared['classifications'])
        warning_counts['stale_sources'] += 1
        rows.append(prepared)
    for gate in owner_gates:
        classifications['owner-gate-open'] += 1
        rows.append({'entity_type':'owner-gate', 'entity_id':gate.get('worksheet_id', ''),
                     'owner':gate.get('owner', gate.get('owner_required', '')),
                     'warning_equivalent':False, 'classifications':['owner-gate-open', 'real-owner-assignment-required'],
                     'automatic_closure_allowed':False, 'owner_approval_performed':False,
                     'human_action_zh':'分派真实签收人并取得明确内容复核；routing owner 不充当 reviewed_by。'})
    caches = _cache_inventory(reader, as_of)
    rows.sort(key=lambda row:(not row['warning_equivalent'], row['entity_type'], row['entity_id']))
    return {'schema_version':'knowledge-hub.review-triage/v1', 'status':'report-only', 'report_only':True,
            'read_only':True, 'as_of':as_of.isoformat(), 'warning_counts':dict(warning_counts),
            'warning_equivalent_count':sum(warning_counts.values()), 'classifications':dict(classifications),
            'entity_count':len(rows), 'rows':rows[:detail_limit], 'detail_limit':detail_limit,
            'detail_overflow':len(rows) > detail_limit, 'review_state_status':state_status,
            'metadata_ready_count':classifications['metadata-ready'], 'evidence_bytes_read':reader.total,
            'evidence_byte_overflow':reader.overflow,
            'maximum_evidence_bytes':MAX_TOTAL_BYTES, 'runtime_check_cache':caches,
            'owner_preparation':prepare_owner_preparation(rows, total_limit=detail_limit, packet_size=packet_size),
            'automatically_closed_warning_count':0, 'owner_decision_generated':False,
            'review_dates_changed':False, 'active_promoted':False,
            'policy_zh':'仅复用真实正文和本地引用的 hash 及既有 evidence；机械通过不续期、不签收、不关闭 warning 或 owner gate。'}
