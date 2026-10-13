import datetime as dt
import hashlib
import json
import subprocess

import pytest

from tools.codex_assets.knowledge_hub import review_automation as automation
from tools.codex_assets.knowledge_hub import review_triage
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError

DAY = dt.date(2026, 10, 10)


@pytest.fixture
def inventory(tmp_path, monkeypatch):
    registry = tmp_path / 'registry'
    registry.mkdir()
    (registry / 'review-risk-policy.json').write_text(json.dumps(
        {'default_class': 'ordinary', 'classes': {'ordinary': {}}, 'rules': []}))
    folder = tmp_path / 'projects/example/validation'
    folder.mkdir(parents=True)
    body = folder / 'candidate.md'
    body.write_text('---\nid: candidate\npath: projects/example/validation/candidate.md\n'
                    'status: reviewing\nowner: declared\nreview_after: 2026-10-01\n---\n候选结论\n')
    proof = folder / 'proof.json'
    proof.write_text('{"status":"pass","synthetic":true}')
    item = dict(id='candidate', path='projects/example/validation/candidate.md', owner='declared',
                status='reviewing', kind='validation', domain='projects/example',
                review_after='2026-10-01', evidence_refs=['projects/example/validation/proof.json'],
                validation_refs=[])
    (registry / 'items.jsonl').write_text(json.dumps(item) + '\n')
    rows = [dict(item_id='candidate', review_after='2026-10-01', review_class='ordinary')]
    readiness = {'rows': [{'project_id': 'example', 'evidence_status': 'contract-evidence-pending',
                          'evidence_contract': {'missing_fields': ['real_device_evidence'], 'invalid_fields': []}}]}
    monkeypatch.setattr(automation, 'working_tree_signature', lambda root: 'a' * 64)
    monkeypatch.setattr(automation, '_readiness', lambda root: readiness)
    return tmp_path, [item], rows, readiness


def test_preparation_and_replay_do_not_approve_synthetic_proof(inventory):
    root, items, rows, readiness = inventory
    before = (root / 'registry/items.jsonl').read_bytes()
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    assert plan['status'] == 'prepared' and plan['content_selected'] == 1
    assert plan['binding']['content'][0]['semantic_verified'] is False
    assert plan['binding']['projects'][0]['automatic_qualification'] is False
    assert plan['automatically_closed_count'] == 0
    assert automation.verify_automation_plan(root, plan, DAY)['status'] == 'pass'
    assert (root / 'registry/items.jsonl').read_bytes() == before


@pytest.mark.parametrize('target', ['candidate.md', 'proof.json'])
def test_same_source_signature_does_not_hide_body_or_proof_changes(inventory, target):
    root, items, rows, readiness = inventory
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    (root / 'projects/example/validation' / target).write_text('changed')
    with pytest.raises(KnowledgeHubError, match='changed'):
        automation.verify_automation_plan(root, plan, DAY)


def test_private_and_command_references_are_never_read_or_executed(inventory, monkeypatch):
    root, items, rows, readiness = inventory
    items[0]['evidence_refs'] = ['../../.ssh/key', 'rtk bash evil.sh; touch stolen', '.aws/secret']
    (root / 'registry/items.jsonl').write_text(json.dumps(items[0]) + '\n')
    calls = []
    monkeypatch.setattr(automation, '_reference', lambda *a: calls.append(a))
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    assert calls == [] and plan['machine_check']['executed'] is False
    assert plan['binding']['content'][0]['lane'] == 'evidence-needed'
    assert 'evil.sh' not in json.dumps(plan)


def test_personal_inventory_excluded_from_content_and_project_discovery(inventory):
    root, items, rows, readiness = inventory
    items[0]['visibility'] = 'personal-local'
    (root / 'registry/items.jsonl').write_text(json.dumps(items[0]) + '\n')
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    assert plan['content_selected'] == 0
    assert plan['binding']['projects'][0]['candidate_count'] == 0


def test_canonical_codex_route_discovered_without_personal_or_other_domain(inventory):
    root, items, rows, readiness = inventory
    (root / 'registry/projects.json').write_text(json.dumps(
        {'projects': [{'id': 'codex', 'domain': 'domains/codex'}]}))
    items[0]['domain'] = 'codex'
    items.extend([dict(items[0], id='personal', visibility='personal-local'),
                  dict(items[0], id='other-domain', domain='projects/codex')])
    (root / 'registry/items.jsonl').write_text(
        '\n'.join(json.dumps(item) for item in items) + '\n')
    readiness['rows'][0]['project_id'] = 'codex'
    before = (root / 'registry/items.jsonl').read_bytes()
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    discovery = plan['binding']['projects'][0]
    assert discovery['candidate_count'] == 1
    assert [row['item_id'] for row in discovery['candidates']] == ['candidate']
    assert discovery['automatic_qualification'] is False
    assert automation.verify_automation_plan(root, plan, DAY)['status'] == 'pass'
    assert (root / 'registry/items.jsonl').read_bytes() == before
    (root / 'registry/projects.json').write_text(json.dumps(
        {'projects': [{'id': 'codex', 'domain': 'projects/codex'}]}))
    with pytest.raises(KnowledgeHubError, match='project inventory'):
        automation.verify_automation_plan(root, plan, DAY)


def test_canonical_route_material_count_controls_project_priority(inventory):
    root, items, rows, readiness = inventory
    (root / 'registry/projects.json').write_text(json.dumps(
        {'projects': [{'id': 'codex', 'domain': 'domains/codex'},
                      {'id': 'aaa', 'domain': 'projects/aaa'}]}))
    items[0]['domain'] = 'codex'
    (root / 'registry/items.jsonl').write_text(json.dumps(items[0]) + '\n')
    readiness['rows'][0]['project_id'] = 'codex'
    readiness['rows'].append(dict(readiness['rows'][0], project_id='aaa'))
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY, project_limit=1)
    assert plan['binding']['projects'][0]['project_id'] == 'codex'
    assert plan['project_pending_total'] == 2


def test_review_cycle_changes_invalidate_confirmation(inventory):
    root, items, rows, readiness = inventory
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    items[0]['owner'] = 'another-owner'
    (root / 'registry/items.jsonl').write_text(json.dumps(items[0]) + '\n')
    with pytest.raises(KnowledgeHubError, match='changed'):
        automation.verify_automation_plan(root, plan, DAY)


def test_local_mapping_drift_is_not_hidden_by_git_signature(inventory):
    root, items, rows, readiness = inventory
    (root / 'local').mkdir()
    mapping = root / 'local/workspaces.json'
    mapping.write_text('{}')
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    mapping.write_text('{"workspaces":[]}')
    with pytest.raises(KnowledgeHubError, match='local mapping'):
        automation.verify_automation_plan(root, plan, DAY)


def test_budget_exhaustion_is_partial_not_prepared(inventory, monkeypatch):
    root, items, rows, readiness = inventory
    monkeypatch.setattr(review_triage, 'MAX_TOTAL_BYTES', 1)
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    assert plan['status'] == 'needs-fix' and plan['evidence_byte_overflow']
    with pytest.raises(KnowledgeHubError, match='incomplete'):
        automation.verify_automation_plan(root, plan, DAY)


@pytest.mark.parametrize('stdout,code', [('{}', 0), ('{"status":"pass","errors":[]}', 1),
                                       ('{"status":"fail","errors":[]}', 0),
                                       ('{"status":"pass","errors":[],"warnings":1}', 0)])
def test_machine_failure_or_ambiguous_output_cannot_pass(inventory, monkeypatch, stdout, code):
    root, items, rows, readiness = inventory
    monkeypatch.setattr(automation, 'run_bounded', lambda command, **kw:
                        (subprocess.CompletedProcess(command, code, stdout, ''), False))
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY, run_machine_checks=True)
    assert plan['status'] == 'needs-fix'
    assert plan['machine_check']['argv'] == list(automation.MACHINE_COMMAND) + ['--as-of', DAY.isoformat()]


def test_fixed_check_timeout_is_failed_without_arbitrary_retry(inventory, monkeypatch):
    root, items, rows, readiness = inventory
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 60)
    monkeypatch.setattr(automation, 'run_bounded', timeout)
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY, run_machine_checks=True)
    assert plan['status'] == 'needs-fix' and plan['machine_check']['failure_kind'] == 'TimeoutExpired'


def test_same_day_replay_stable_and_next_day_expired(inventory):
    root, items, rows, readiness = inventory
    first = automation.build_automation_plan(root, items, rows, readiness, DAY)
    second = automation.build_automation_plan(root, items, rows, readiness, DAY)
    assert first['plan_sha256'] == second['plan_sha256']
    with pytest.raises(KnowledgeHubError, match='expired'):
        automation.verify_automation_plan(root, first, DAY + dt.timedelta(days=1))


def test_consumed_unchanged_cycle_suppressed_and_changed_body_reopened(inventory):
    root, items, rows, readiness = inventory
    item = items[0]
    state = root / '.tmp/review-consumption'
    state.mkdir(parents=True)
    prior = {'candidate': {'decision': 'accepted', 'valid_until': '2026-11-01',
                          'body_sha256': hashlib.sha256((root / item['path']).read_bytes()).hexdigest(),
                          'cycle_sha256': automation.cycle_sha256(root, item)}}
    (state / 'state.json').write_text(json.dumps(prior))
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    assert plan['content_selected'] == 0 and plan['consumed_or_deferred_count'] == 1
    (root / item['path']).write_text('changed')
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    assert plan['content_selected'] == 1 and plan['consumed_or_deferred_count'] == 0


@pytest.mark.parametrize('kwargs', [{'content_limit': True}, {'project_limit': 101},
                                    {'content_offset': -1}, {'content_limit': 0}])
def test_invalid_budgets_fail_closed(inventory, kwargs):
    root, items, rows, readiness = inventory
    with pytest.raises(KnowledgeHubError):
        automation.build_automation_plan(root, items, rows, readiness, DAY, **kwargs)


@pytest.mark.parametrize('change', [{'project_id': 'unknown'}, {'canonical_evidence_status': 'ready'},
                                   {'missing_fields': []}, {'candidates': []}])
def test_redigested_forged_project_summary_is_not_canonical(inventory, change):
    root, items, rows, readiness = inventory
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    plan['binding']['projects'][0].update(change)
    plan['plan_sha256'] = automation._digest(plan['binding'])
    with pytest.raises(KnowledgeHubError, match='project inventory'):
        automation.verify_automation_plan(root, plan, DAY)


def test_local_input_changes_during_generation_are_not_bound_as_prepared(inventory, monkeypatch):
    root, items, rows, readiness = inventory
    (root / 'local').mkdir()
    mapping = root / 'local/workspaces.json'
    mapping.write_text('{}')
    def observe(root):
        mapping.write_text('{"workspaces":[]}')
        return readiness
    monkeypatch.setattr(automation, '_readiness', observe)
    plan = automation.build_automation_plan(root, items, rows, None, DAY)
    assert plan['status'] == 'needs-fix' and not plan['preparation_complete']


def test_serialized_output_budget_cannot_emit_unreplayable_prepared_plan(inventory, monkeypatch):
    root, items, rows, readiness = inventory
    monkeypatch.setattr(automation, 'MAX_PLAN_BYTES', 100)
    with pytest.raises(KnowledgeHubError, match='serialized plan'):
        automation.build_automation_plan(root, items, rows, readiness, DAY)


@pytest.mark.parametrize('collection,field,bad', [('content', 'item_id', []),
                                                 ('projects', 'project_id', {})])
def test_malformed_selection_identity_is_structured_error(inventory, collection, field, bad):
    root, items, rows, readiness = inventory
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY)
    plan['binding'][collection][0][field] = bad
    plan['plan_sha256'] = automation._digest(plan['binding'])
    with pytest.raises(KnowledgeHubError, match='identity'):
        automation.verify_automation_plan(root, plan, DAY)


def test_local_input_drift_during_machine_check_cannot_claim_complete(inventory, monkeypatch):
    root, items, rows, readiness = inventory
    (root / 'local').mkdir()
    mapping = root / 'local/workspaces.json'
    mapping.write_text('{}')
    def check(*args):
        mapping.write_text('{"workspaces":[]}')
        return {'status': 'pass', 'executed': True}
    monkeypatch.setattr(automation, '_machine_check', check)
    plan = automation.build_automation_plan(root, items, rows, readiness, DAY, run_machine_checks=True)
    assert plan['status'] == 'needs-fix' and not plan['preparation_complete']
