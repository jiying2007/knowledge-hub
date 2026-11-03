"""A maintenance caller can request bounded privacy cleanup, never arbitrary edits."""
import argparse
import datetime as dt
import json

import pytest

from tools.codex_assets.knowledge_hub import provider_maintenance as maintenance
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, render_markdown
from test_provider_maintenance import sample as _sample_fixture

sample = _sample_fixture


def occurrences(body, count):
    return [{'start': m.start(), 'end': m.end(), 'sha256': maintenance.sha(m.group().encode())}
            for m in list(maintenance.IPV4_LITERAL.finditer(body))[:count]]


def test_redaction_removes_only_explicit_reviewed_spans():
    # All addresses below are synthetic test data, not device endpoints.
    body = ('adb connect 192.168.20.42:5555\n10.1.2.3 172.16.0.9 172.31.9.8\n'
            '192.0.2.1 203.0.113.4 172.32.0.1 999.1.2.3 v10.1.2.3 1.2.3.4\n'
            'version=10.1.2.3 release/10.1.2.3/changelog 版本 10.1.2.3\n')
    after, count = maintenance.redact_private_network_addresses(body, occurrences(body, 4))
    assert count == 4
    assert after == ('adb connect <设备地址>:5555\n<设备地址> <设备地址> <设备地址>\n'
                     '192.0.2.1 203.0.113.4 172.32.0.1 999.1.2.3 v10.1.2.3 1.2.3.4\n'
                     'version=10.1.2.3 release/10.1.2.3/changelog 版本 10.1.2.3\n')


def test_redaction_is_explicit_hash_bound_and_does_not_copy_address_into_plan(sample):
    root, request, item = sample
    path = root / item['path']
    body = '# 现场记录\n\nadb connect 192.168.20.42:5555\n'
    path.write_text(render_markdown(item, body))
    entry = request['items'][0]
    entry.pop('target_path')
    entry['expected_sha256'] = maintenance.sha(path.read_bytes())
    # Default maintenance still preserves every body byte.
    _, _, writes, _ = maintenance.build_plan(root, request)
    assert '192.168.20.42' in writes[item['path']].decode()
    entry['redactions'] = [{'kind': 'private-network-addresses', 'occurrences': occurrences(body, 1)}]
    plan, _, writes, _ = maintenance.build_plan(root, request)
    assert '<设备地址>:5555' in writes[item['path']].decode()
    assert '192.168.20.42' not in json.dumps(plan)
    assert maintenance.sha(b'192.168.20.42') not in json.dumps(plan)
    assert plan['body_redactions'] == [{'item_id': item['id'], 'kind': 'private-network-addresses', 'redacted_count': 1}]
    current = json.loads(writes['registry/items.jsonl'].splitlines()[0])
    assert all(current.get(k) == item.get(k) for k in ('owner', 'status', 'source', 'review_after'))
    entry['expected_sha256'] = '0' * 64
    with pytest.raises(KnowledgeHubError, match='CONTENT_DRIFT'):
        maintenance.build_plan(root, request)


@pytest.mark.parametrize('value', ['private-network-addresses', ['arbitrary-body-edit'],
                                  ['private-network-addresses', 'private-network-addresses'], {'replace': 'body'}])
def test_unknown_or_malformed_redaction_never_writes(sample, value):
    root, request, item = sample
    request['items'][0]['redactions'] = value
    original = (root / item['path']).read_bytes()
    with pytest.raises(KnowledgeHubError, match='POLICY_DENIED'):
        maintenance.build_plan(root, request)
    assert (root / item['path']).read_bytes() == original


def test_redaction_cannot_target_active_content(sample):
    root, request, item = sample
    item['status'] = 'active'
    (root / 'registry/items.jsonl').write_text(json.dumps(item) + '\n')
    request['items'][0]['redactions'] = [{'kind': 'private-network-addresses',
                                         'occurrences': [{'start': 0, 'end': 8, 'sha256': 'a' * 64}]}]
    with pytest.raises(KnowledgeHubError, match='POLICY_DENIED'):
        maintenance.build_plan(root, request)


@pytest.mark.parametrize('failure', ['hash', 'overlap', 'negative', 'not-private', 'not-address'])
def test_redaction_rejects_invalid_content_bindings(failure):
    body = '10.1.2.3 10.1.2.3 192.0.2.1 not-an-ip'
    selected = occurrences(body, 2)
    if failure == 'hash':
        selected[0]['sha256'] = '0' * 64
    elif failure == 'overlap':
        selected[1] = dict(selected[0])
    elif failure == 'negative':
        selected[0]['start'] = -1
    else:
        literal = '192.0.2.1' if failure == 'not-private' else 'not-an-ip'
        selected = [{'start': body.index(literal), 'end': body.index(literal) + len(literal),
                     'sha256': maintenance.sha(literal.encode())}]
    with pytest.raises(KnowledgeHubError):
        maintenance.redact_private_network_addresses(body, selected)


def test_redaction_apply_preserves_protected_fields_and_invalidates_prior_review(sample, tmp_path):
    root, request, item = sample
    path = root / item['path']
    body = '# 现场记录\n\nadb connect 192.168.20.42:5555\n版本 10.1.2.3\n'
    path.write_text(render_markdown(item, body))
    before_sha = maintenance.sha(path.read_bytes())
    item.update(human_review_content_sha256=before_sha, human_review_decision='accept-as-review-record')
    (root / 'registry/items.jsonl').write_text(json.dumps(item) + '\n')
    entry = request['items'][0]
    entry.pop('target_path')
    entry.update(expected_sha256=before_sha,
                 redactions=[{'kind': 'private-network-addresses', 'occurrences': occurrences(body, 1)}])
    plan, _, _, _ = maintenance.build_plan(root, request)
    source = tmp_path / 'request.json'
    source.write_text(json.dumps(request))
    declaration = tmp_path / 'declaration.md'
    declaration.write_text('全部优化落地')
    scope = {'actor': 'test-user', 'action': 'maintain-content', 'expected_hash': plan['expected_hash'],
             'item_ids': [item['id']], 'visibility_change': False}
    (root / 'registry/authorizations.jsonl').write_text(json.dumps({
        'authorization_id': 'approved-redaction', 'scope': json.dumps(scope),
        'allowed_actions': ['automation-apply-with-review'], 'authorized_at': str(dt.date.today()),
        'expires_at': str(dt.date.today()), 'status': 'active'}) + '\n')
    args = argparse.Namespace(source=str(source), declaration_file=str(declaration), apply=True,
                              expected_content_sha256=plan['expected_hash'], authorization_id='approved-redaction')
    receipt = maintenance.maintain(root, args)
    assert receipt['status'] == 'MAINTAINED' and receipt['persisted'] is True
    assert '192.168.20.42' not in path.read_text()
    assert '<设备地址>:5555' in path.read_text() and '版本 10.1.2.3' in path.read_text()
    current = json.loads((root / 'registry/items.jsonl').read_text())
    assert all(current.get(k) == item.get(k) for k in ('status', 'owner', 'source', 'review_after', 'promotion'))
    assert current['human_review_decision'] == 'defer'
    manifest = (root / receipt['manifest_ref']).read_text()
    assert '192.168.20.42' not in manifest
    assert maintenance.sha(b'192.168.20.42') not in manifest
    assert json.loads(manifest)['prior_reviews'][0]['before_sha256'] == before_sha


def test_metadata_redaction_updates_exact_registry_and_frontmatter_text_only(sample):
    root, request, item = sample
    item['source']['from'] = 'synthetic endpoint 192.168.20.42'
    item['summary_zh'] = 'synthetic endpoint 192.168.20.42'
    item['evidence_refs'] = ['synthetic endpoint 192.168.20.42']
    path = root / item['path']
    path.write_text(render_markdown(item, '# 已脱敏正文\n'))
    (root / 'registry/items.jsonl').write_text(json.dumps(item) + '\n')
    selected = []
    for field in ('source.from', 'summary_zh', 'evidence_refs.0'):
        parent, key = maintenance.metadata_slot(item, field)
        selected += [dict(row, field=field) for row in occurrences(parent[key], 1)]
    entry = request['items'][0]
    entry.pop('target_path')
    entry.update(expected_sha256=maintenance.sha(path.read_bytes()),
                 redactions=[{'kind': 'private-network-addresses', 'occurrences': [],
                              'metadata_occurrences': selected}])
    plan, _, writes, _ = maintenance.build_plan(root, request)
    current = json.loads(writes['registry/items.jsonl'].splitlines()[0])
    assert current['source']['type'] == item['source']['type']
    assert current['source'].get('source_sha256') == item['source'].get('source_sha256')
    assert current['source']['from'] == 'synthetic endpoint <设备地址>'
    assert current['summary_zh'] == current['evidence_refs'][0] == 'synthetic endpoint <设备地址>'
    assert '192.168.20.42' not in writes[item['path']].decode()
    assert maintenance.sha(b'192.168.20.42') not in json.dumps(plan)
    assert plan['body_redactions'][0]['redacted_count'] == 3
    # A differing registry/frontmatter mirror cannot be laundered by redaction.
    item['summary_zh'] = 'different synthetic context 192.168.20.42'
    (root / 'registry/items.jsonl').write_text(json.dumps(item) + '\n')
    with pytest.raises(KnowledgeHubError, match='CONTENT_DRIFT'):
        maintenance.build_plan(root, request)


@pytest.mark.parametrize('field', ['owner', 'status', 'path', 'review_after', 'source.type',
                                  'source.source_sha256', '__class__', 'evidence_refs.-1'])
def test_metadata_redaction_cannot_change_identity_or_protected_source_fields(sample, field):
    root, request, _ = sample
    request['items'][0]['redactions'] = [{'kind': 'private-network-addresses', 'occurrences': [],
        'metadata_occurrences': [{'field': field, 'start': 0, 'end': 8, 'sha256': 'a' * 64}]}]
    with pytest.raises(KnowledgeHubError, match='POLICY_DENIED'):
        maintenance.build_plan(root, request)
