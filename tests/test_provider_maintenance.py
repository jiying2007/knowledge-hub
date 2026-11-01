import argparse
import copy
import datetime as dt
import json
import shutil

import pytest

from tools.codex_assets.knowledge_hub import provider_maintenance as maintenance
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, load_markdown, load_jsonl, render_markdown, repository_root
from tools.codex_assets.knowledge_hub.content_quality import findings, overdue
from tools.codex_assets.knowledge_hub.context_support import _rank_item, _current_exclusion_reason
from tools.codex_assets.knowledge_hub.provider_context import authority_lanes


@pytest.fixture
def sample(tmp_path, monkeypatch):
    source = repository_root()
    root = tmp_path / 'hub'
    (root / 'registry').mkdir(parents=True)
    shutil.copytree(source / 'schemas', root / 'schemas')
    shutil.copytree(source / 'templates', root / 'templates')
    item = copy.deepcopy(next(x for x in load_jsonl(source / 'registry/items.jsonl')
                              if x['path'].startswith('projects/gros/validation/') and x['source']['type'] == 'manual'))
    item.update(id='note', path='projects/one/current/note.md', domain='projects/one', owner='test-owner')
    item.pop('human_review_content_sha256', None)
    item.pop('delegated_content_review', None)
    path = root / item['path']
    path.parent.mkdir(parents=True)
    path.write_text(render_markdown(item, '# 记录\n\n真实证据 commit abcdef；13ms。\n'))
    (root / 'registry/items.jsonl').write_text(json.dumps(item) + '\n')
    (root / 'registry/projects.json').write_text(json.dumps({'projects': [{'id': 'one'}, {'id': 'two'}]}))
    (root / 'registry/provider-operations.jsonl').write_text('')
    (root / 'registry/authorizations.jsonl').write_text('')
    (root / 'indexes').mkdir()
    (root / 'indexes/entry.md').write_text('[记录](../projects/one/current/note.md)\n')
    request = {'schema_version': 1, 'items': [{'item_id': 'note', 'expected_sha256': maintenance.sha(path.read_bytes()),
               'target_path': 'projects/two/archive/note.md', 'metadata': {'searchable': False, 'quality_flags': ['superseded-candidate']}}]}
    monkeypatch.setattr(maintenance, 'authorize', lambda *a, **kw: None)
    monkeypatch.setattr(maintenance, 'principal', lambda *a: 'test-user')
    monkeypatch.setattr(maintenance, 'policy', lambda *a: {'actions': ['assign']})
    from tools.codex_assets.knowledge_hub import provider_grants
    monkeypatch.setattr(provider_grants, 'attested_request', lambda *a: ('a' * 64, 'b' * 64))
    return root, request, item


def test_exact_plan_preserves_body_lifecycle_and_rewrites_references(sample, tmp_path):
    root, request, before = sample
    plan, _, writes, deletes = maintenance.build_plan(root, request)
    assert set(deletes) == {before['path']}
    assert b'projects/two/archive/note.md' in writes['indexes/entry.md']
    after = [json.loads(line) for line in writes['registry/items.jsonl'].splitlines()][0]
    for key in ('status', 'owner', 'review_after', 'promotion', 'source'):
        assert after.get(key) == before.get(key)
    request_file = tmp_path / 'plan.json'
    request_file.write_text(json.dumps(request))
    declaration = tmp_path / 'request.md'
    declaration.write_text('全部优化落地')
    authorization = {'actor': 'test-user', 'action': 'maintain-content', 'expected_hash': plan['expected_hash'],
                     'item_ids': ['note'], 'visibility_change': False}
    (root / 'registry/authorizations.jsonl').write_text(json.dumps({'authorization_id': 'approval',
        'scope': json.dumps(authorization), 'allowed_actions': ['automation-apply-with-review'],
        'authorized_at': str(dt.date.today()), 'expires_at': str(dt.date.today()), 'status': 'active'}) + '\n')
    args = argparse.Namespace(source=str(request_file), apply=True, authorization_id='approval',
           expected_content_sha256=plan['expected_hash'], declaration_file=str(declaration))
    receipt = maintenance.maintain(root, args)
    assert receipt['status'] == 'MAINTAINED' and receipt['persisted'] is True
    assert not (root / before['path']).exists()
    assert load_markdown(root / after['path'])[1] == '# 记录\n\n真实证据 commit abcdef；13ms。\n'
    assert receipt['owner_review_performed'] is False


@pytest.mark.parametrize('failure', ['owner', 'status', 'date', 'body', 'review_status', 'evidence_validation_status', 'traversal', 'collision', 'stale', 'symlink'])
def test_rejected_maintenance_never_writes(sample, failure):
    root, request, item = sample
    entry = request['items'][0]
    if failure in {'owner', 'status', 'date', 'body', 'review_status', 'evidence_validation_status'}:
        field = {'date': 'review_after'}.get(failure, failure)
        entry['metadata'][field] = 'invalid'
    elif failure == 'traversal':
        entry['target_path'] = 'projects/two/../../escape.md'
    elif failure == 'collision':
        path = root / entry['target_path']
        path.parent.mkdir(parents=True)
        path.write_text('existing')
    elif failure == 'stale':
        entry['expected_sha256'] = '0' * 64
    else:
        original = root / item['path']
        original.rename(original.with_suffix('.original'))
        original.symlink_to(original.with_suffix('.original'))
    snapshot = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
    with pytest.raises(KnowledgeHubError):
        maintenance.build_plan(root, request)
    assert all(p.read_bytes() == value for p, value in snapshot.items())


def test_search_exclusion_and_overdue_authority_are_consistent():
    item = {'id': 'x', 'path': 'projects/p/current/x.md', 'status': 'active', 'kind': 'decision',
            'visibility': 'team-internal', 'review_after': '2000-01-01', 'manual_validation_pending': False}
    assert overdue(item)
    assert _current_exclusion_reason(item) == 'review-overdue'
    assert authority_lanes([{'items': [item]}])['historical'] == ['x']
    item['searchable'] = False
    assert _rank_item(item, ['x'], 'source', set(), set(), False) == (0, [])


def test_template_body_gate_requires_explicit_quarantine(sample):
    root, _, item = sample
    _, body = load_markdown(root / 'templates/validation-report.md')
    (root / item['path']).write_text(render_markdown(item, body))
    assert findings(root, [item]) == ['template-body:' + item['path']]
    item['searchable'] = False
    assert findings(root, [item]) == []


@pytest.mark.parametrize('failure', [None, 'narrative', 'credential', 'source'])
def test_active_navigation_is_exact_and_never_transfers_approval(sample, failure):
    root, request, old = sample
    active = copy.deepcopy(old)
    active.update(id='active-reference', path='projects/one/current/reference.md', status='active')
    active.update(content_review_status='accepted', evidence_validation_status='verified')
    active['related'] = [old['path']]
    if failure == 'credential':
        active['human_review_content_sha256'] = 'a' * 64
    if failure == 'source':
        active['source'] = {'type': 'manual', 'from': old['path']}
    body = '# 规范\n\n引用：`' + old['path'] + '`\n'
    if failure == 'narrative':
        body += '历史运行目录是 ' + old['path'] + '。\n'
    text = render_markdown(active, body)
    (root / active['path']).write_text(text)
    rows = load_jsonl(root / 'registry/items.jsonl') + [active]
    (root / 'registry/items.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rows))
    if failure:
        with pytest.raises(KnowledgeHubError, match='ACTIVE_REVIEW'):
            maintenance.build_plan(root, request)
    else:
        plan, _, writes, _ = maintenance.build_plan(root, request)
        assert writes[active['path']].decode() == text.replace(old['path'], request['items'][0]['target_path'])
        assert plan['navigation_updates'][0]['item_id'] == active['id']


def test_team_maintenance_never_reads_or_rewrites_personal_bodies(sample, monkeypatch):
    root, request, old = sample
    private = copy.deepcopy(old)
    private.update(id='personal-note', path='notes/personal/private.md', visibility='personal-local',
                   domain='personal', status='personal')
    file = root / private['path']
    file.parent.mkdir(parents=True)
    file.write_text('private content referencing ' + old['path'])
    rows = load_jsonl(root / 'registry/items.jsonl') + [private]
    (root / 'registry/items.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rows))
    original_read = type(file).read_bytes
    original_text = type(file).read_text
    def reject_private(path, *args, **kwargs):
        assert path != file, 'private body was read'
        return original_read(path, *args, **kwargs)
    def reject_private_text(path, *args, **kwargs):
        assert path != file, 'private body was read'
        return original_text(path, *args, **kwargs)
    monkeypatch.setattr(type(file), 'read_bytes', reject_private)
    monkeypatch.setattr(type(file), 'read_text', reject_private_text)
    plan, inputs, writes, _ = maintenance.build_plan(root, request)
    assert private['path'] not in inputs and private['path'] not in writes


def test_historical_owner_target_is_only_resolved_by_exact_output(sample):
    root, request, old = sample
    from tools.codex_assets.knowledge_hub.maintenance_lineage import historical_target
    plan, _, writes, _ = maintenance.build_plan(root, request)
    target = request['items'][0]['target_path']
    file = root / target
    file.parent.mkdir(parents=True)
    file.write_bytes(writes[target])
    (root / 'registry/items.jsonl').write_bytes(writes['registry/items.jsonl'])
    directory = root / 'artifacts/manifests'
    directory.mkdir(parents=True)
    (directory / ('content-maintenance-' + plan['expected_hash'] + '.json')).write_text(json.dumps(plan))
    assert historical_target(root, old['path']) == target
    file.write_text('changed')
    assert historical_target(root, old['path']) == ''


def test_explicit_private_project_entry_is_rejected_before_read(sample, monkeypatch):
    root, request, item = sample
    item['visibility'] = 'personal-local'
    (root / 'registry/items.jsonl').write_text(json.dumps(item) + '\n')
    original = type(root).read_bytes
    def guarded(path, *args, **kwargs):
        assert path != root / item['path'], 'explicit private body was read'
        return original(path, *args, **kwargs)
    monkeypatch.setattr(type(root), 'read_bytes', guarded)
    with pytest.raises(KnowledgeHubError, match='POLICY_DENIED'):
        maintenance.build_plan(root, request)
