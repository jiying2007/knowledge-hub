"""Bounded machine preparation and replay; human decisions remain explicit."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
from collections import Counter

from .bounded_process import run_bounded
from .common import KnowledgeHubError, project_rows, registry_items, working_tree_signature
from .project_readiness import _item_domain
from .review_preparation import _path
from .review_risk import classify_review_risk, load_review_risk_policy
from .review_state import cycle_sha256, load_consumption_state
from .review_triage import _EvidenceReader, _body_evidence, _reference
from .security import scan_secret_text

SCHEMA = 'knowledge-hub.autonomous-review-plan/v1'
MAX_DISCOVERY_ITEMS = 40
MAX_PLAN_BYTES = 2 * 1024 * 1024
MACHINE_COMMAND = ('rtk', 'bash', 'tools/knowledge-check.sh', '--dry-run', '--json')


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def _visible(item):
    return (item.get('visibility') != 'personal-local' and item.get('status') != 'personal'
            and bool(_path(item.get('path', ''))))


def _safe_identity(value):
    if not isinstance(value, str) or not value or len(value) > 160 or scan_secret_text(value):
        raise KnowledgeHubError('automation identity is invalid or sensitive')
    return value


def _references(reader, item):
    refs = list(dict.fromkeys(item.get('evidence_refs', []) + item.get('validation_refs', [])))
    rows = []
    for value in refs[:16]:
        relative = value.split('#', 1)[0] if isinstance(value, str) else ''
        if not _path(relative):
            # Text commands, private paths and external pointers are never opened/executed.
            rows.append({'status': 'external-or-nonlocal-not-executed',
                         'reference_sha256': _digest(value), 'semantic_verified': False})
        else:
            rows.append(_reference(reader, value))
    return rows, len(refs) > 16


def _prepare_content(root, reader, item, policy):
    body = _body_evidence(reader, item)
    refs, overflow = _references(reader, item)
    risk = classify_review_risk(policy, item['path'])['review_class']
    local = sum(ref['status'] == 'local-hash-confirmed' for ref in refs)
    issues = [ref['status'] for ref in refs if ref['status'] != 'local-hash-confirmed']
    if body['status'] != 'metadata-ready':
        lane = 'repair-required'
    elif overflow or issues or not refs:
        lane = 'evidence-needed'
    elif risk != 'ordinary' or item.get('kind') in ('standard', 'architecture', 'decision'):
        lane = 'detailed-human-review'
    else:
        lane = 'brief-human-confirmation'
    binding = {'item_id': _safe_identity(item['id']), 'path': item['path'],
               'body_sha256': body.get('sha256', ''), 'cycle_sha256': cycle_sha256(root, item),
               'references': refs, 'reference_overflow': overflow}
    return dict(binding, lane=lane, risk=risk, body_status=body['status'],
                local_reference_count=local, semantic_verified=False,
                confirmation_sha256=_digest(binding),
                proposed_action_zh={
                    'repair-required': '修复正文与registry不一致或不可读取问题后重新生成包',
                    'evidence-needed': '补充缺失证据或核验外部来源，再重新生成确认包',
                    'detailed-human-review': '复核适用性、依据及权威状态；AI检查不构成内容签收',
                    'brief-human-confirmation': '机器身份检查通过；真实负责人确认当前适用性与内容决定',
                }[lane],
                execution_route={'wrapper': 'tools/knowledge-review-after.sh',
                                 'option': '--consume-item', 'requires_explicit_decision': True,
                                 'lifecycle_wrapper': 'tools/knowledge-review-attest.sh',
                                 'active_requires_human_review': True})


def _project_domain(root, project_id):
    for registered in project_rows(root):
        if registered.get('id') == project_id:
            return _item_domain(registered)
    return 'projects/' + project_id


def _discover_project(reader, project, items, offset=0):
    if type(offset) is not int or not 0 <= offset <= 5000:
        raise KnowledgeHubError('project discovery offset exceeds budget')
    project_id = _safe_identity(project['project_id'])
    domain = _project_domain(reader.root, project_id)
    candidates = sorted((item for item in items if _visible(item)
                         and item.get('domain') == domain),
                        key=lambda item: (item.get('kind') != 'validation', item['id']))
    discovered = []
    for item in candidates[offset:offset + MAX_DISCOVERY_ITEMS]:
        body = _body_evidence(reader, item)
        refs, overflow = _references(reader, item)
        discovered.append({'item_id': _safe_identity(item['id']), 'path': item['path'],
                           'body_sha256': body.get('sha256', ''),
                           'body_status': body['status'], 'references': refs,
                           'reference_overflow': overflow,
                           'binding_scope': 'candidate-provenance-only'})
    contract = project['evidence_contract']
    return {'project_id': project_id, 'canonical_evidence_status': project['evidence_status'],
            'missing_fields': contract.get('missing_fields', []),
            'invalid_fields': contract.get('invalid_fields', []),
            'discovery_scope': 'registered-hub-items-and-declared-local-references',
            'candidates': discovered, 'candidate_count': len(candidates),
            'discovery_offset': offset, 'discovery_next_offset': offset + len(discovered),
            'discovery_overflow': offset + len(discovered) < len(candidates),
            'automatic_qualification': False,
            'next_action_zh': '将现有候选与缺失字段逐项核对；hash存在不证明测试结论或真实环境资格',
            'external_execution_authorized': False}


def _machine_check(root, as_of):
    command = list(MACHINE_COMMAND) + ['--as-of', as_of.isoformat()]
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        result, overflow = run_bounded(command, cwd=str(root), env=dict(os.environ),
                                       timeout=60, output_limit=2 * 1024 * 1024)
        payload = json.loads(result.stdout) if not overflow else {}
        if not isinstance(payload, dict):
            payload = {}
        warnings = payload.get('warnings')
        passed = (result.returncode == 0 and not overflow
                  and payload.get('status') == 'pass' and payload.get('errors') == []
                  and isinstance(warnings, list))
        return {'status': 'pass' if passed else 'fail', 'executed': True,
                'argv': command, 'started_at': started, 'exit_code': result.returncode,
                'output_sha256': _digest({'stdout': result.stdout, 'stderr': result.stderr}),
                'output_overflow': overflow, 'warnings_count': len(warnings) if isinstance(warnings, list) else None,
                'semantic_approval': False}
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {'status': 'fail', 'executed': True, 'argv': command,
                'started_at': started, 'failure_kind': type(exc).__name__, 'semantic_approval': False}


def _local_binding(root, reader):
    result = {}
    for relative in ('local/workspaces.json', '.tmp/review-consumption/state.json'):
        path = root / relative
        result[relative] = hashlib.sha256(reader.confirm(relative)).hexdigest() if path.exists() else ''
    return result


def _readiness(root):
    from .product_gate_support import _project_readiness
    return _project_readiness(root)


def _pending_content(root, reader, rows, by_id, as_of):
    state, outbox, _ = load_consumption_state(root / '.tmp/review-consumption/state.json')
    if outbox:
        raise KnowledgeHubError('review consumption outbox is pending; reconcile before preparation')
    eligible, suppressed = [], 0
    for row in rows:
        item = by_id[row['item_id']]
        if not _visible(item):
            continue
        prior = state.get(item['id'], {})
        expiry = prior.get('next_review_at') if prior.get('decision') == 'deferred' else prior.get('valid_until')
        if prior.get('decision') in ('accepted', 'deferred') and expiry and expiry > as_of.isoformat():
            body = _body_evidence(reader, item)
            if (body.get('sha256') == prior.get('body_sha256')
                    and cycle_sha256(root, item) == prior.get('cycle_sha256')):
                suppressed += 1
                continue
        eligible.append(row)
    return sorted(eligible, key=lambda row: (row.get('review_class') == 'ordinary',
                                           row['review_after'], row['item_id'])), suppressed


def build_automation_plan(root, items, item_rows, readiness, as_of, *, content_limit=10,
                          project_limit=2, content_offset=0, project_offset=0,
                          discovery_offset=0, run_machine_checks=False):
    """Prepare bounded batches; no owner, lifecycle or canonical evidence writes."""
    values = ((content_limit, 500), (project_limit, 100), (content_offset, 5000),
              (project_offset, 100), (discovery_offset, 5000))
    if any(type(v) is not int or not 0 <= v <= cap for v, cap in values):
        raise KnowledgeHubError('automation selection exceeds explicit budgets')
    if not content_limit or not project_limit or type(as_of) is not dt.date:
        raise KnowledgeHubError('automation needs nonempty limits and a date')
    if len(items) > 5000 or len(item_rows) > 5000:
        raise KnowledgeHubError('automation inventory exceeds budget')
    before = working_tree_signature(root)
    reader = _EvidenceReader(root)
    local_before = _local_binding(root, reader)
    if _digest(registry_items(root)) != _digest(items):
        raise KnowledgeHubError('automation registry input changed before preparation')
    readiness = _readiness(root) if readiness is None else readiness
    if len(readiness['rows']) > 100:
        raise KnowledgeHubError('automation project inventory exceeds budget')
    policy = load_review_risk_policy(root)
    by_id = {item['id']: item for item in items}
    selected, suppressed = _pending_content(root, reader, item_rows, by_id, as_of)
    counts = Counter(item.get('domain') for item in items if _visible(item))
    pending = sorted((row for row in readiness['rows'] if row['evidence_status'] != 'ready'),
                     key=lambda row: (-counts[_project_domain(root, row['project_id'])], row['project_id']))
    content = [_prepare_content(root, reader, by_id[row['item_id']], policy)
               for row in selected[content_offset:content_offset + content_limit]]
    projects = [_discover_project(reader, row, items, discovery_offset)
                for row in pending[project_offset:project_offset + project_limit]]
    binding = {'as_of': as_of.isoformat(), 'source_signature': before,
               'content': content, 'projects': projects, 'local_inputs': _local_binding(root, reader)}
    machine = _machine_check(root, as_of) if run_machine_checks else {'status': 'not-run', 'executed': False}
    local_after = _local_binding(root, reader)
    after = working_tree_signature(root)
    complete = not reader.overflow and before == after and local_before == local_after == binding['local_inputs']
    result = {'schema_version': SCHEMA, 'status': 'prepared' if complete else 'needs-fix',
              'read_only': True, 'report_only': True, 'binding': binding,
              'plan_sha256': _digest(binding), 'source_unchanged': before == after,
              'preparation_complete': complete, 'evidence_bytes_read': reader.total,
              'evidence_byte_overflow': reader.overflow, 'machine_check': machine,
              'content_total': len(selected), 'project_pending_total': len(pending),
              'consumed_or_deferred_count': suppressed,
              'content_selected': len(content), 'project_selected': len(projects),
              'content_next_offset': content_offset + len(content),
              'project_next_offset': project_offset + len(projects),
              'lane_counts': dict(Counter(row['lane'] for row in content)),
              'metrics_scope': 'machine-preparation-not-human-review-time',
              'owner_decision_generated': False, 'review_dates_changed': False,
              'active_promoted': False, 'automatically_closed_count': 0}
    if machine['status'] == 'fail':
        result['status'] = 'needs-fix'
    if len(json.dumps(result, ensure_ascii=False).encode()) > MAX_PLAN_BYTES:
        raise KnowledgeHubError('automation serialized plan exceeds budget; reduce batch limits')
    return result


def verify_automation_plan(root, plan, as_of):
    """Reconfirm the exact selected inputs before any separately authorized action."""
    if not isinstance(plan, dict) or plan.get('schema_version') != SCHEMA:
        raise KnowledgeHubError('unsupported automation plan')
    binding = plan.get('binding', {})
    if not isinstance(binding, dict) or _digest(binding) != plan.get('plan_sha256'):
        raise KnowledgeHubError('automation plan digest mismatch')
    if (plan.get('status') != 'prepared' or plan.get('preparation_complete') is not True
            or binding.get('as_of') != as_of.isoformat()):
        raise KnowledgeHubError('automation plan incomplete, failed or expired')
    if binding.get('source_signature') != working_tree_signature(root):
        raise KnowledgeHubError('automation source signature changed')
    reader = _EvidenceReader(root)
    if _local_binding(root, reader) != binding.get('local_inputs'):
        raise KnowledgeHubError('automation local mapping or review state changed')
    current = {item['id']: item for item in registry_items(root)}
    rows = binding.get('content', [])
    projects = binding.get('projects', [])
    if not isinstance(rows, list) or not isinstance(projects, list) or len(rows) > 500 or len(projects) > 100:
        raise KnowledgeHubError('automation plan selection invalid')
    policy = load_review_risk_policy(root)
    readiness = {row['project_id']: row for row in _readiness(root)['rows']}
    for row, field in [(row, 'item_id') for row in rows] + [(row, 'project_id') for row in projects]:
        if not isinstance(row, dict):
            raise KnowledgeHubError('automation selection row invalid')
        _safe_identity(row.get(field))
    if (len({row['item_id'] for row in rows}) != len(rows)
            or len({row['project_id'] for row in projects}) != len(projects)):
        raise KnowledgeHubError('automation duplicate or invalid selection identities')
    for row in rows:
        if not isinstance(row, dict):
            raise KnowledgeHubError('automation content row invalid')
        item = current.get(row.get('item_id'))
        if not item or not _visible(item) or _prepare_content(root, reader, item, policy) != row:
            raise KnowledgeHubError('automation content or evidence changed')
    for project in projects:
        if not isinstance(project, dict) or not isinstance(project.get('candidates'), list) or len(project['candidates']) > MAX_DISCOVERY_ITEMS:
            raise KnowledgeHubError('automation project row invalid')
        canonical = readiness.get(project.get('project_id'))
        if (not canonical or canonical['evidence_status'] == 'ready'
                or _discover_project(reader, canonical, list(current.values()),
                                     project.get('discovery_offset')) != project):
            raise KnowledgeHubError('automation project inventory or evidence changed')
    if (reader.overflow or working_tree_signature(root) != binding['source_signature']
            or _local_binding(root, reader) != binding['local_inputs']):
        raise KnowledgeHubError('automation replay incomplete or inputs drifted')
    return {'status': 'pass', 'read_only': True, 'plan_sha256': plan['plan_sha256'],
            'execution_authorized': False, 'owner_approval_performed': False,
            'content_verified': len(rows), 'projects_verified': len(projects)}
