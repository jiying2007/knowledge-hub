import argparse
import copy
import datetime as dt
import json
import shutil

import pytest

from tools.codex_assets.knowledge_hub import provider_review_schedule as schedule
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, load_jsonl, load_markdown, render_markdown, repository_root
from tools.codex_assets.knowledge_hub.content_quality import overdue
from tools.codex_assets.knowledge_hub.provider_context import authority_lanes
from tools.codex_assets.knowledge_hub.provider_operations import operations, verify_current_item
from tools.codex_assets.knowledge_hub.provider_subjects import digest

THREAD = '11111111-1111-1111-1111-111111111111'


@pytest.fixture
def case(tmp_path, monkeypatch):
    source, root = repository_root(), tmp_path / 'hub'
    (root / 'registry').mkdir(parents=True)
    (root / 'indexes').mkdir()
    (root / 'local').mkdir()
    shutil.copytree(source / 'schemas', root / 'schemas')
    item = copy.deepcopy(next(x for x in load_jsonl(source / 'registry/items.jsonl')
                              if x['path'].startswith('projects/gros/validation/') and x['source']['type'] == 'manual'))
    item.pop('delegated_content_review', None)
    item.update(id='note', path='projects/one/current/note.md', domain='projects/one', owner='alice',
                status='active', content_review_status='accepted', evidence_validation_status='verified',
                manual_validation_pending=False, review_after='2000-01-01', human_review_content_sha256='a' * 64,
                human_review_decision='accept', human_reviewed_by='previous-owner', human_reviewed_at='2000-01-01')
    item.pop('subject_ref', None)
    file = root / item['path']
    file.parent.mkdir(parents=True)
    body = '# 真实记录\n\n结论仍须设备证据，不能替代产品放行。\n'
    file.write_text(render_markdown(item, body))
    metadata, body = load_markdown(file)
    tomorrow = (dt.date.today() + dt.timedelta(days=7)).isoformat()
    fields = dict(review_after=tomorrow, updated_at=dt.date.today().isoformat(), manual_validation_pending=True,
                  content_review_status='accepted', review_status='periodic-review-scheduled-pending-content')
    metadata.update(fields, human_review_decision='defer')
    entry = dict(item_id='note', path=item['path'], owner='alice', status='active',
                 before_sha256=schedule.sha(file.read_bytes()), after_sha256=schedule.sha(render_markdown(metadata, body).encode()),
                 before_review_after=item['review_after'], after_review_after=tomorrow, planned_metadata=fields,
                 body_text_unchanged=True, prior_bound_review_will_defer=True)
    proposal = dict(schema_version=schedule.PROPOSAL, as_of=dt.date.today().isoformat(),
                    execution_state='not-applied', decision_required='owner-review-period-rescheduling-only',
                    content_approval_performed=False, human_review_performed=False, item_count=1,
                    owner_counts={'alice': 1}, date_counts={tomorrow: 1}, entries=[entry])
    proposal['proposal_sha256'] = digest(proposal)
    proposal['confirmation_token'] = 'KH-SCHEDULE-' + proposal['proposal_sha256'][:24].upper()
    packet = copy.deepcopy(item)
    packet.update(id='packet', path='projects/one/archive/packet.md', status='reviewing',
                  source={'type': 'provider-candidate-archive', 'from': 'operation:test', 'source_sha256': 'b' * 64})
    packet_file = root / packet['path']
    packet_file.parent.mkdir(parents=True)
    packet_file.write_text(render_markdown(packet, '# 决定包\n\n' + proposal['proposal_sha256'] + '\n' + proposal['confirmation_token']))
    confirmation = dict(schema_version='knowledge-owner-cycle-confirmation/v1',
                        confirmation_token=proposal['confirmation_token'], confirmed_by='alice', authorized_owners=['alice'],
                        decision_statement='确认周期安排 ' + proposal['confirmation_token'] + '；批准包中1条的日期与 pending/defer 处理，保留内容、证据及责任待办。',
                        identity_statement='负责人身份：alice；权限范围：所有周期复核；',
                        source_ref='codex-thread:' + THREAD + '/user-confirmation-and-identity',
                        decision_packet_id='packet', decision_packet_sha256=schedule.sha(packet_file.read_bytes()),
                        execution_authorized=True, content_approval_performed=False)
    request = dict(schema_version=schedule.APPLICATION, proposal=proposal, owner_confirmation=confirmation)
    rows = []
    for index, row in enumerate((item, packet)):
        rows.append(dict(schema_version=4, operation_id=str(index + 1) * 64, request_sha256=str(index + 1) * 64,
                         action='archive', item_id=row['id'], created_subject_ref={'type': 'project', 'id': 'one'},
                         subject_ref={'type': 'project', 'id': 'one'}, content_sha256=schedule.sha((root / row['path']).read_bytes()),
                         before_content_sha256=None, transaction_id=None, principal_id='test-user',
                         verification_basis={'kind': 'accepted-current', 'proof_ref': 'test'}))
    (root / 'registry/items.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in (item, packet)))
    (root / 'registry/provider-operations.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rows))
    for name in ('registry/authorizations.jsonl', 'registry/provider-subject-policy.json', 'registry/owners.json', 'local/provider-principal.json'):
        (root / name).write_text('')
    for name in schedule.CORE_INDEXES:
        (root / name).write_text('# index\n')
    monkeypatch.setattr(schedule, 'authorize', lambda *a, **kw: None)
    monkeypatch.setattr(schedule, 'principal', lambda *a: 'test-user')
    monkeypatch.setattr(schedule, 'policy', lambda *a: {'actions': ['assign']})
    monkeypatch.setenv('CODEX_THREAD_ID', THREAD)
    from tools.codex_assets.knowledge_hub import provider_grants
    monkeypatch.setattr(provider_grants, 'attested_request', lambda *a: ('c' * 64, 'd' * 64))
    return root, request, item, body


@pytest.mark.parametrize('renewal', [None, '', 'renewal.md'])
def test_explicit_renewal_forwarded_for_authorization_and_schedule(case, tmp_path, monkeypatch, renewal):
    from tools.codex_assets.knowledge_hub import provider_grants
    root, request, _, _ = case
    declaration = tmp_path / 'execution.md'
    declaration.write_text('全部优化落地')
    calls = []

    def attested(*args):
        calls.append(args)
        return 'c' * 64, 'd' * 64

    monkeypatch.setattr(provider_grants, 'attested_request', attested)
    args = argparse.Namespace(apply=False, expected_content_sha256='', declaration_file=str(declaration))
    if renewal is not None:
        args.renewal_request_file = str(tmp_path / renewal) if renewal else ''
    grant_request = dict(request, schema_version=schedule.AUTHORIZATION)
    grant = schedule.record_authorization(root, args, grant_request)
    assert calls == []
    args.apply, args.expected_content_sha256 = True, grant['expected_hash']
    schedule.record_authorization(root, args, grant_request)
    plan = schedule.build_plan(root, request, THREAD)[0]
    args.expected_content_sha256, args.authorization_id = plan['expected_hash'], grant['authorization_id']
    receipt = schedule.schedule(root, args, request)
    expected = (declaration.read_text(), declaration)
    if renewal:
        expected += (args.renewal_request_file,)
    assert calls == [expected, expected]
    assert receipt['persisted'] is True and receipt['owner_review_performed'] is False


@pytest.mark.parametrize('stage', ['authorization', 'schedule'])
def test_execution_attestation_failure_still_blocks_owner_cycle(case, tmp_path, monkeypatch, stage):
    from tools.codex_assets.knowledge_hub import provider_grants
    root, request, item, _ = case
    declaration = tmp_path / 'execution.md'
    declaration.write_text('全部优化落地')
    args = argparse.Namespace(apply=False, expected_content_sha256='', declaration_file=str(declaration))
    grant_request = dict(request, schema_version=schedule.AUTHORIZATION)
    grant = schedule.record_authorization(root, args, grant_request)
    args.apply, args.expected_content_sha256 = True, grant['expected_hash']
    if stage == 'schedule':
        schedule.record_authorization(root, args, grant_request)
        args.expected_content_sha256 = schedule.build_plan(root, request, THREAD)[0]['expected_hash']
        args.authorization_id = grant['authorization_id']
    before = (root / item['path']).read_bytes()
    authorization_before = (root / 'registry/authorizations.jsonl').read_bytes()

    def unattested(*args):
        assert len(args) == 2
        raise KnowledgeHubError('DECLARATION_UNATTESTED')

    monkeypatch.setattr(provider_grants, 'attested_request', unattested)
    with pytest.raises(KnowledgeHubError, match='DECLARATION_UNATTESTED'):
        if stage == 'authorization':
            schedule.record_authorization(root, args, grant_request)
        else:
            schedule.schedule(root, args, request)
    assert (root / item['path']).read_bytes() == before
    assert (root / 'registry/authorizations.jsonl').read_bytes() == authorization_before


def test_exact_cycle_apply_preserves_body_identity_and_invalidates_old_binding(case, tmp_path):
    root, request, before, body = case
    plan, inputs, writes = schedule.build_plan(root, request, THREAD)
    assert plan['maintenance_kind'] == 'owner-review-cycle-only'
    declaration = tmp_path / 'execution.md'
    declaration.write_text('全部优化落地')
    grant_request = dict(request, schema_version=schedule.AUTHORIZATION)
    grant_args = argparse.Namespace(apply=False, expected_content_sha256='', declaration_file=str(declaration))
    grant_plan = schedule.record_authorization(root, grant_args, grant_request)
    # Grant persistence cannot change any knowledge body or review date.
    before_bytes = (root / before['path']).read_bytes()
    grant_args.apply, grant_args.expected_content_sha256 = True, grant_plan['expected_hash']
    schedule.record_authorization(root, grant_args, grant_request)
    assert (root / before['path']).read_bytes() == before_bytes
    assert schedule.build_plan(root, request, THREAD)[0]['expected_hash'] == plan['expected_hash']
    args = argparse.Namespace(apply=True, expected_content_sha256=plan['expected_hash'], declaration_file=str(declaration),
                              authorization_id=grant_plan['authorization_id'])
    receipt = schedule.schedule(root, args, request)
    assert receipt['status'] == 'MAINTAINED' and receipt['persisted'] is True
    after = next(x for x in load_jsonl(root / 'registry/items.jsonl') if x['id'] == before['id'])
    metadata, actual_body = load_markdown(root / before['path'])
    assert actual_body == body
    for key in ('status', 'owner', 'source', 'evidence_validation_status', 'human_reviewed_by', 'human_reviewed_at', 'human_review_content_sha256'):
        assert after[key] == before[key]
    assert after['content_review_status'] == 'accepted'
    assert after['human_review_decision'] == 'defer' and after['manual_validation_pending'] is True
    assert not authority_lanes([{'items': [after]}])['authoritative']
    assert not overdue(after)
    assert overdue(after, dt.date.fromisoformat(after['review_after']) + dt.timedelta(days=1))
    ledger = operations(root)
    assert len(ledger) == 3
    verify_current_item(root, after, ledger)
    assert ledger[-1]['before_content_sha256'] == request['proposal']['entries'][0]['before_sha256']
    authorization = load_jsonl(root / 'registry/authorizations.jsonl')[0]
    assert authorization['status'] == 'used'
    scope = json.loads(authorization['scope'])
    assert scope['action'] == 'schedule-review' and scope['proposal_sha256'] == request['proposal']['proposal_sha256']
    assert str(after['review_after']) in (root / 'indexes/by-review-date.md').read_text()
    manifest = json.loads((root / receipt['manifest_ref']).read_text())
    assert manifest['owner_cycle_decision']['human_identity_independently_verified'] is False
    assert manifest['content_approval_performed'] is False
    # The consumed exact before hashes reject blind replay without a second write.
    snapshot = (root / 'registry/provider-operations.jsonl').read_bytes()
    with pytest.raises(KnowledgeHubError):
        schedule.schedule(root, args, request)
    assert (root / 'registry/provider-operations.jsonl').read_bytes() == snapshot


@pytest.mark.parametrize('failure', ['token', 'identity-placeholder', 'identity-machine', 'owners', 'thread',
                                  'statement', 'no-execution', 'packet-hash', 'before-hash', 'owner',
                                  'unapproved-after', 'active-pending', 'manual-false', 'date-past',
                                  'defer-omitted', 'body-hash', 'extra-field', 'path-symlink'])
def test_refuses_unapproved_or_drifted_cycle_without_writes(case, failure):
    root, request, item, _ = case
    p, c = request['proposal'], request['owner_confirmation']
    entry = p['entries'][0]
    if failure == 'token':
        c['confirmation_token'] = 'KH-SCHEDULE-WRONG'
    elif failure == 'identity-placeholder':
        c['confirmed_by'] = '<identity>'
    elif failure == 'identity-machine':
        c['confirmed_by'] = 'Codex'
    elif failure == 'owners':
        c['authorized_owners'] = ['other']
    elif failure == 'thread':
        c['source_ref'] = 'codex-thread:other'
    elif failure == 'statement':
        c['decision_statement'] = '全部优化落地'
    elif failure == 'no-execution':
        c['execution_authorized'] = False
    elif failure == 'packet-hash':
        c['decision_packet_sha256'] = '0' * 64
    elif failure == 'before-hash':
        entry['before_sha256'] = '0' * 64
    elif failure == 'owner':
        entry['owner'] = 'other'
    elif failure == 'unapproved-after':
        entry['after_review_after'] = '2099-01-01'
    elif failure == 'active-pending':
        entry['planned_metadata']['content_review_status'] = 'pending'
    elif failure == 'manual-false':
        entry['planned_metadata']['manual_validation_pending'] = False
    elif failure == 'date-past':
        entry['after_review_after'] = '2000-01-01'
    elif failure == 'defer-omitted':
        entry['prior_bound_review_will_defer'] = False
    elif failure == 'body-hash':
        entry['after_sha256'] = '0' * 64
    elif failure == 'extra-field':
        entry['planned_metadata']['source'] = {'type': 'manual'}
    else:
        file = root / item['path']
        file.rename(file.with_suffix('.original'))
        file.symlink_to(file.with_suffix('.original'))
    snapshot = {str(x.relative_to(root)): x.read_bytes() for x in root.rglob('*') if x.is_file()}
    with pytest.raises(KnowledgeHubError):
        schedule.build_plan(root, request, THREAD)
    assert snapshot == {str(x.relative_to(root)): x.read_bytes() for x in root.rglob('*') if x.is_file()}


def test_generic_maintenance_still_rejects_review_date_and_active_items(case):
    from tools.codex_assets.knowledge_hub.provider_maintenance import build_plan
    root, request, item, _ = case
    (root / 'registry/projects.json').write_text('{"projects": [{"id": "one"}]}')
    with pytest.raises(KnowledgeHubError, match='POLICY_DENIED'):
        build_plan(root, {'schema_version': 1, 'items': [
            {'item_id': item['id'], 'expected_sha256': request['proposal']['entries'][0]['before_sha256'],
             'metadata': {'review_after': '2099-01-01'}}]})


def rebind_fixture_packet(root, request):
    """Simulate another explicitly approved packet, reaching inner validations."""
    p, c = request['proposal'], request['owner_confirmation']
    old_hash, old_token = p['proposal_sha256'], p['confirmation_token']
    p['proposal_sha256'] = digest({k: v for k, v in p.items() if k not in {'proposal_sha256', 'confirmation_token'}})
    p['confirmation_token'] = 'KH-SCHEDULE-' + p['proposal_sha256'][:24].upper()
    c['confirmation_token'] = p['confirmation_token']
    c['decision_statement'] = c['decision_statement'].replace(old_token, p['confirmation_token'])
    packet = next(x for x in load_jsonl(root / 'registry/items.jsonl') if x['id'] == 'packet')
    file = root / packet['path']
    file.write_text(file.read_text().replace(old_hash, p['proposal_sha256']).replace(old_token, p['confirmation_token']))
    c['decision_packet_sha256'] = schedule.sha(file.read_bytes())
    ledger = load_jsonl(root / 'registry/provider-operations.jsonl')
    ledger[1]['content_sha256'] = c['decision_packet_sha256']
    (root / 'registry/provider-operations.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in ledger))


@pytest.mark.parametrize('failure,reason', [
    ('before-hash', 'CONTENT_DRIFT'), ('active-pending', 'POLICY_DENIED'),
    ('manual-false', 'POLICY_DENIED'), ('date-past', 'POLICY_DENIED'),
    ('defer-omitted', 'POLICY_DENIED'), ('after-body', 'CONTENT_DRIFT'),
    ('extra-source', 'POLICY_DENIED'), ('delegated-proof', 'POLICY_DENIED')])
def test_inner_guards_even_with_rehashed_owner_packet(case, failure, reason):
    root, request, item, _ = case
    entry = request['proposal']['entries'][0]
    if failure == 'before-hash':
        entry['before_sha256'] = '0' * 64
    elif failure == 'active-pending':
        entry['planned_metadata']['content_review_status'] = 'pending'
    elif failure == 'manual-false':
        entry['planned_metadata']['manual_validation_pending'] = False
    elif failure == 'date-past':
        entry['after_review_after'] = '2000-01-01'
    elif failure == 'defer-omitted':
        entry['prior_bound_review_will_defer'] = False
    elif failure == 'after-body':
        entry['after_sha256'] = '0' * 64
    elif failure == 'extra-source':
        entry['planned_metadata']['source'] = {'type': 'manual'}
    else:
        rows = load_jsonl(root / 'registry/items.jsonl')
        from tools.codex_assets.knowledge_hub.delegated_content_review import FIELD
        rows[0][FIELD] = {'stale': 'credential-must-be-rejected'}
        (root / 'registry/items.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rows))
    rebind_fixture_packet(root, request)
    snapshot = {str(x.relative_to(root)): x.read_bytes() for x in root.rglob('*') if x.is_file()}
    with pytest.raises(KnowledgeHubError, match=reason):
        schedule.build_plan(root, request, THREAD)
    assert snapshot == {str(x.relative_to(root)): x.read_bytes() for x in root.rglob('*') if x.is_file()}


def test_no_implicit_execution_authorization(case, tmp_path):
    root, request, _, _ = case
    plan = schedule.build_plan(root, request, THREAD)[0]
    args = argparse.Namespace(apply=True, expected_content_sha256=plan['expected_hash'], declaration_file='', authorization_id='')
    with pytest.raises(KnowledgeHubError, match='AUTHORIZATION_REQUIRED'):
        schedule.schedule(root, args, request)
    args.authorization_id = plan['authorization_ref']
    with pytest.raises(KnowledgeHubError, match='authorization_id must resolve'):
        schedule.schedule(root, args, request)
    assert (root / 'registry/authorizations.jsonl').read_bytes() == b''


@pytest.mark.parametrize('personal', [True, False])
def test_packet_access_checked_before_read(case, monkeypatch, personal):
    root, request, _, _ = case
    rows = load_jsonl(root / 'registry/items.jsonl')
    packet_path = root / rows[1]['path']
    if personal:
        rows[1]['visibility'] = 'personal-local'
        (root / 'registry/items.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rows))
    else:
        def denied(*a, **kw):
            raise KnowledgeHubError('VISIBILITY_DENIED')
        monkeypatch.setattr(schedule, 'authorize', denied)
    original = type(root).read_bytes
    def guarded(path, *a, **kw):
        assert path != packet_path, 'unauthorized packet was read'
        return original(path, *a, **kw)
    monkeypatch.setattr(type(root), 'read_bytes', guarded)
    with pytest.raises(KnowledgeHubError, match='VISIBILITY_DENIED'):
        schedule.build_plan(root, request, THREAD)


def test_transaction_failure_rolls_back_cycle_and_keeps_grant_active(case, tmp_path, monkeypatch):
    root, request, item, _ = case
    plan = schedule.build_plan(root, request, THREAD)[0]
    declaration = tmp_path / 'execution.md'
    declaration.write_text('全部优化落地')
    grant_request = dict(request, schema_version=schedule.AUTHORIZATION)
    grant_args = argparse.Namespace(apply=False, expected_content_sha256='', declaration_file=str(declaration))
    grant_plan = schedule.record_authorization(root, grant_args, grant_request)
    grant_args.apply, grant_args.expected_content_sha256 = True, grant_plan['expected_hash']
    schedule.record_authorization(root, grant_args, grant_request)
    snapshot = {str(x.relative_to(root)): x.read_bytes() for x in root.rglob('*') if x.is_file() and '.tmp' not in x.parts}
    from tools.codex_assets.knowledge_hub import store
    replace, failed = store.os.replace, []
    def failing_replace(src, dst):
        if str(dst) == str(root / item['path']) and not failed:
            failed.append(True)
            raise OSError('injected-failure')
        return replace(src, dst)
    monkeypatch.setattr(store.os, 'replace', failing_replace)
    args = argparse.Namespace(apply=True, expected_content_sha256=plan['expected_hash'], declaration_file=str(declaration),
                              authorization_id=grant_plan['authorization_id'])
    with pytest.raises(KnowledgeHubError, match='rolled-back'):
        schedule.schedule(root, args, request)
    assert failed
    assert snapshot == {str(x.relative_to(root)): x.read_bytes() for x in root.rglob('*') if x.is_file() and '.tmp' not in x.parts}
    assert load_jsonl(root / 'registry/authorizations.jsonl')[0]['status'] == 'active'
