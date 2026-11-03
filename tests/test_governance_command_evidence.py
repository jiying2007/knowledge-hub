"""Adversarial checks for read-only, hash-bound historical command records."""

import copy
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess

import pytest
import yaml

from tools.codex_assets.knowledge_hub import governance_command_evidence as evidence


TODAY = dt.date(2026, 11, 1)
PATTERNS = [
    ('repo-relative-tool-command', 'rtk bash tools/'),
    ('short-knowledge-check-command', '`knowledge-check --dry-run'),
    ('bare-knowledge-check-command', 'knowledge-check --dry-run --json --diagnostics'),
    ('weak-validation-ref', 'validation_refs":["tools/knowledge-check.sh --dry-run'),
]


def archive_fixture(name='one', paragraph=None):
    ident = 'record-' + name
    relative = 'governance/product/validation/' + name + '.md'
    operation = hashlib.sha256(ident.encode()).hexdigest()
    subject = {'type': 'project', 'id': 'knowledge-hub'}
    item = {
        'id': ident, 'path': relative, 'kind': 'validation', 'status': 'reviewing',
        'visibility': 'team-internal', 'created_at': '2026-10-31',
        'source': {'type': 'provider-candidate-archive', 'from': 'operation:' + operation},
        'provider_operation_id': operation, 'subject_ref': subject,
        'created_subject_ref': subject, 'principal_id': 'test-principal',
    }
    body = '2026-10-31 历史验证记录。\n\n' + (paragraph or evidence.HISTORY_SENTENCE) + '\n\n后续说明。\n'
    proof = {
        'action': 'archive', 'operation_id': operation, 'item_id': ident,
        'before_content_sha256': None, 'created_subject_ref': copy.deepcopy(subject),
        'subject_ref': copy.deepcopy(subject), 'principal_id': 'test-principal',
    }
    return item, body, proof


def classified(item, body, proof, *, metadata=None, raw=None):
    if raw is None:
        text = '---\n' + yaml.safe_dump(metadata if metadata is not None else item, allow_unicode=True) + '---\n\n' + body
        raw = text.encode()
    proof = copy.deepcopy(proof)
    proof.setdefault('content_sha256', hashlib.sha256(raw).hexdigest())
    loaded = evidence.CommandEvidence(TODAY, {item['path']: [item]}, {item['id']: [proof]}, {item['id']: 1})
    return loaded.classify(item['path'], raw), raw, loaded


@pytest.mark.parametrize('name', ['one', 'another-unrelated-item'])
@pytest.mark.parametrize('declaration', ['', evidence.HISTORY_DECLARATION])
def test_distinct_bound_records_are_provenance_only(name, declaration):
    result, raw, _ = classified(*archive_fixture(name, evidence.HISTORY_SENTENCE + declaration))
    record = result['record']
    assert result['rejection_reason'] == ''
    assert record['item_id'] == 'record-' + name
    assert record['record_content_sha256'] == hashlib.sha256(raw).hexdigest()
    assert record['record_integrity_verified'] is True
    for key in ('execution_verified', 'derived_entry_executed', 'historical_cwd_known',
                'equivalence_verified', 'content_approval_performed'):
        assert record[key] is False
    assert record['original_argv'] == list(evidence.ORIGINAL_ARGV)
    assert record['derived_cwd_stable_argv'][2] == '~/knowledge-hub/tools/knowledge-source-check.sh'
    assert '历史等价性未验证' in record['note']
    assert evidence.instruction_occurrences(raw.decode(), PATTERNS, record) == []


@pytest.mark.parametrize('transform', [
    lambda text: text + '请运行上述命令',
    lambda text: '请执行以下命令\n' + text,
    lambda text: '[\n' + text + '\n](https://example.test)',
    lambda text: '![\n' + text + '\n](image.png)',
    lambda text: '```sh\n' + text + '\n```',
    lambda text: '~~~\n' + text + '\n~~~',
    lambda text: '<!--\n' + text + '\n-->',
    lambda text: '> ' + text,
    lambda text: '- ' + text,
    lambda text: '    ' + text,
    lambda text: text.replace('实际运行', '\\实际运行'),
    lambda text: text + '\n\n' + text,
    lambda text: text + '\n\n推荐 `rtk bash tools/knowledge-source-check.sh --scope current --json --strict`。',
    lambda text: text.replace('--strict', '--strict; touch /tmp/never-execute'),
    lambda text: text.replace('--strict', '--strict && echo unsafe'),
    lambda text: text.replace('--strict', '--unknown'),
])
def test_unknown_context_or_second_command_remains_finding(transform):
    item, _, proof = archive_fixture()
    body = '2026-10-31 历史验证记录。\n\n' + transform(evidence.HISTORY_SENTENCE) + '\n\n后续说明。\n'
    result, raw, _ = classified(item, body, proof)
    assert result['record'] is None
    assert result['rejection_reason'] in evidence.REJECTION_CODES
    assert evidence.instruction_occurrences(raw.decode(), PATTERNS, result['record'])


@pytest.mark.parametrize(('field', 'value'), [
    ('status', 'active'), ('visibility', 'private'), ('kind', 'runbook'),
    ('created_at', '2026-11-01'), ('created_at', '2026-11-02'),
    ('source', {'type': 'provider-candidate-archive', 'from': 'operation:wrong'}),
    ('subject_ref', {'type': 'personal', 'id': 'someone'}),
])
def test_typed_identity_and_date_restrictions(field, value):
    item, body, proof = archive_fixture()
    item[field] = value
    assert classified(item, body, proof)[0]['record'] is None


@pytest.mark.parametrize('change', ['extra', 'missing', 'different'])
def test_protected_frontmatter_fields_match_symmetrically(change):
    item, body, proof = archive_fixture()
    metadata = copy.deepcopy(item)
    if change == 'extra':
        field = next(key for key in evidence.PROTECTED_FIELDS if key not in item)
        metadata[field] = 'unbound-value'
    elif change == 'missing':
        metadata.pop('principal_id')
    else:
        metadata['principal_id'] = 'different-principal'
    result = classified(item, body, proof, metadata=metadata)[0]
    assert result['rejection_reason'] == 'frontmatter-identity-mismatch'


@pytest.mark.parametrize('mutation', ['hash', 'subject', 'created', 'principal', 'archive', 'before'])
def test_initial_and_latest_proof_binding(mutation):
    item, body, proof = archive_fixture()
    changes = {
        'hash': ('content_sha256', '0' * 64),
        'subject': ('subject_ref', {'type': 'project', 'id': 'other'}),
        'created': ('created_subject_ref', {'type': 'project', 'id': 'other'}),
        'principal': ('principal_id', 'other'), 'archive': ('action', 'metadata'),
        'before': ('before_content_sha256', '1' * 64),
    }
    key, value = changes[mutation]
    proof[key] = value
    assert classified(item, body, proof)[0]['record'] is None


def test_same_raw_snapshot_tamper_and_duplicate_registry_refused():
    result, raw, loaded = classified(*archive_fixture())
    assert result['record']
    relative = result['record']['path']
    assert loaded.classify(relative, raw + b'changed')['record'] is None
    loaded.id_counts['record-one'] = 2
    assert loaded.classify(relative, raw)['rejection_reason'] == 'registry-id-not-unique'
    loaded.id_counts['record-one'] = 1
    loaded.by_path[relative] *= 2
    assert loaded.classify(relative, raw)['rejection_reason'] == 'registry-path-not-unique'


def test_date_in_body_must_match_record():
    item, body, proof = archive_fixture()
    assert classified(item, body.replace('2026-10-31', '2026-10-30'), proof)[0]['record'] is None


def test_all_original_patterns_and_repeated_occurrences_are_retained():
    text = '\n'.join(needle for _, needle in PATTERNS)
    findings = evidence.instruction_occurrences(text, PATTERNS)
    assert {row['pattern_id'] for row in findings} == {name for name, _ in PATTERNS}
    repeated = 'rtk bash tools/one.sh ; rtk bash tools/two.sh'
    rows = evidence.instruction_occurrences(repeated, PATTERNS)
    assert len(rows) == 2
    assert rows[0]['offset'] != rows[1]['offset']
    assert all(row['line'] == 1 for row in rows)


def test_stable_entry_does_not_hide_bare_command_on_same_line():
    text = 'rtk bash ~/knowledge-hub/tools/knowledge-check.sh ; rtk bash tools/unsafe.sh'
    rows = evidence.instruction_occurrences(text, PATTERNS)
    assert len(rows) == 1
    assert rows[0]['offset'] == text.index('rtk bash tools/')


def test_only_exact_proof_span_is_skipped():
    result, raw, _ = classified(*archive_fixture())
    text = raw.decode() + '\nrtk bash tools/another.sh\n'
    rows = evidence.instruction_occurrences(text, PATTERNS, result['record'])
    assert len(rows) == 1
    assert rows[0]['offset'] == text.index('rtk bash tools/another.sh')


def test_load_reads_once_and_classification_never_executes_or_writes(tmp_path, monkeypatch):
    item, body, proof = archive_fixture()
    _, raw, _ = classified(item, body, proof)
    proof['content_sha256'] = hashlib.sha256(raw).hexdigest()
    registry = tmp_path / 'registry'
    registry.mkdir()
    registry_file = registry / 'items.jsonl'
    registry_file.write_text(json.dumps(item) + '\n')
    document = tmp_path / item['path']
    document.parent.mkdir(parents=True)
    document.write_bytes(raw)
    before = (registry_file.read_bytes(), document.read_bytes())
    calls = []

    def read_operations(root):
        calls.append(root)
        return [proof]

    def forbidden(*args, **kwargs):
        pytest.fail('classification must never execute commands')

    monkeypatch.setattr(evidence, 'operations', read_operations)
    monkeypatch.setattr(subprocess, 'run', forbidden)
    monkeypatch.setattr(os, 'system', forbidden)
    loaded = evidence.load_evidence(tmp_path, TODAY)
    assert loaded.classify(item['path'], raw)['record']
    assert loaded.classify(item['path'], raw)['record']
    assert calls == [tmp_path]
    assert before == (registry_file.read_bytes(), document.read_bytes())


def test_proof_load_failure_fails_closed(tmp_path, monkeypatch):
    registry = tmp_path / 'registry'
    registry.mkdir()
    (registry / 'items.jsonl').write_text('')

    def invalid_operations(root):
        raise ValueError('untrusted diagnostic must not escape')

    monkeypatch.setattr(evidence, 'operations', invalid_operations)
    result = evidence.load_evidence(tmp_path, TODAY).classify('unknown.md', b'')
    assert result == {'record': None, 'rejection_reason': 'provider-proof-unavailable'}


@pytest.mark.parametrize('mutation', ['before', 'created', 'subject', 'action'])
def test_discontinuous_latest_operation_is_refused(mutation):
    result, raw, loaded = classified(*archive_fixture())
    latest = copy.deepcopy(loaded.by_item['record-one'][0])
    latest.update(action='metadata', operation_id='b' * 64,
                  before_content_sha256=latest['content_sha256'])
    changes = {
        'before': ('before_content_sha256', '0' * 64),
        'created': ('created_subject_ref', {'type': 'project', 'id': 'other'}),
        'subject': ('subject_ref', {'type': 'project', 'id': 'other'}),
        'action': ('action', 'archive'),
    }
    key, value = changes[mutation]
    latest[key] = value
    loaded.by_item['record-one'].append(latest)
    assert loaded.classify(result['record']['path'], raw)['record'] is None


def test_empty_proof_history_and_invalid_input_are_refused():
    result, raw, loaded = classified(*archive_fixture())
    relative = result['record']['path']
    loaded.by_item.clear()
    assert loaded.classify(relative, raw)['record'] is None
    assert loaded.classify(relative, b'\xff')['record'] is None
    assert loaded.classify(relative, 'not bytes')['rejection_reason'] == 'history-input-budget'
    assert loaded.classify(relative, b'x' * (evidence.DEFAULT_MARKDOWN_MAX_BYTES + 1))['record'] is None


@pytest.mark.parametrize('ledger_error', ['', 'duplicate', 'schema-invalid'])
def test_real_provider_ledger_validation_without_mocking(tmp_path, ledger_error):
    source_root = pathlib.Path(__file__).resolve().parents[1]
    shutil.copytree(source_root / 'schemas', tmp_path / 'schemas')
    registry = tmp_path / 'registry'
    registry.mkdir()
    item, body, proof = archive_fixture('real-schema')
    _, raw, _ = classified(item, body, proof)
    proof.update(schema_version=4, request_sha256=proof['operation_id'],
                 content_sha256=hashlib.sha256(raw).hexdigest(), transaction_id='test-transaction',
                 verification_basis={'kind': 'transaction', 'proof_ref': 'test-transaction'})
    rows = [proof]
    if ledger_error == 'duplicate':
        rows.append(copy.deepcopy(proof))
    elif ledger_error == 'schema-invalid':
        proof['action'] = 'execute-shell'
    (registry / 'items.jsonl').write_text(json.dumps(item) + '\n')
    ledger = registry / 'provider-operations.jsonl'
    ledger.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    before = ledger.read_bytes()
    loaded = evidence.load_evidence(tmp_path, TODAY)
    result = loaded.classify(item['path'], raw)
    if ledger_error:
        assert result['rejection_reason'] == 'provider-proof-unavailable'
    else:
        assert result['record']['record_integrity_verified'] is True
    assert ledger.read_bytes() == before
