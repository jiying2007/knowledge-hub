import copy

import pytest

from tests import test_review_automation as fixtures
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.review_automation import build_automation_plan
from tools.codex_assets.knowledge_hub.review_semantic import (
    RESULT_SCHEMA, prepare_semantic_task, validate_semantic_result,
)

DAY = fixtures.DAY


@pytest.fixture
def inventory(tmp_path, monkeypatch):
    import json
    value = fixtures.inventory.__wrapped__(tmp_path, monkeypatch)
    root, items, _, _ = value
    items[0]['visibility'] = 'team-internal'
    (root / 'registry/items.jsonl').write_text(json.dumps(items[0]) + '\n')
    return value


def packet(inventory):
    root, items, rows, readiness = inventory
    plan = build_automation_plan(root, items, rows, readiness, DAY)
    task = prepare_semantic_task(root, plan, DAY)
    result = {'schema_version': RESULT_SCHEMA, 'task_sha256': task['task_sha256'],
              'evaluator': {'tool': 'test-only', 'model': 'synthetic', 'invocation_ref': 'fixture'},
              'rows': [{'item_id': 'candidate', 'confirmation_sha256': task['rows'][0]['confirmation_sha256'],
                        'verdict': 'proposal', 'findings': [{'anchor': '候选结论', 'issue_zh': '缺少适用范围',
                        'replacement': '仅供测试的候选结论', 'basis_zh': '此正文未限定范围',
                        'confidence': 'medium', 'confirm_zh': '需负责人确认适用范围'}]}]}
    return root, plan, task, result


def test_concrete_proposal_is_bound_but_never_approved(inventory):
    root, plan, task, result = packet(inventory)
    before = (root / 'registry/items.jsonl').read_bytes()
    report = validate_semantic_result(root, plan, result, DAY)
    assert report['metrics']['proposed'] == 1 and report['metrics']['closed'] == 0
    assert not task['model_executed'] and not report['evaluator_identity_verified']
    assert not report['execution_authorized'] and not report['semantic_correctness_verified']
    assert (root / 'registry/items.jsonl').read_bytes() == before


@pytest.mark.parametrize('change', ['digest', 'missing', 'duplicate', 'anchor', 'approval', 'provenance', 'field'])
def test_forged_or_incomplete_response_rejected(inventory, change):
    root, plan, _, result = packet(inventory)
    value = copy.deepcopy(result)
    if change == 'digest':
        value['task_sha256'] = 'f' * 64
    elif change == 'missing':
        value['rows'] = []
    elif change == 'duplicate':
        value['rows'] *= 2
    elif change == 'anchor':
        value['rows'][0]['findings'][0]['anchor'] = '不存在的原文'
    elif change == 'approval':
        value['rows'][0]['verdict'] = 'accepted'
    elif change == 'provenance':
        value['evaluator']['invocation_ref'] = ''
    else:
        value['rows'][0]['findings'][0]['owner_decision'] = 'accepted'
    with pytest.raises(KnowledgeHubError):
        validate_semantic_result(root, plan, value, DAY)


def test_changed_reference_invalidates_response(inventory):
    root, plan, _, result = packet(inventory)
    (root / 'projects/example/validation/proof.json').write_text('{"changed":true}')
    with pytest.raises(KnowledgeHubError, match='changed'):
        validate_semantic_result(root, plan, result, DAY)


def test_sensitive_body_is_withheld_without_exposing_content(inventory):
    root, items, rows, readiness = inventory
    body = root / items[0]['path']
    body.write_text(body.read_text() + '\npassword=very-sensitive-password\n')
    plan = build_automation_plan(root, items, rows, readiness, DAY)
    task = prepare_semantic_task(root, plan, DAY)
    assert not task['rows'] and len(task['blocked']) == 1
    assert 'very-sensitive' not in str(task)


def test_replacement_on_no_change_cannot_pass(inventory):
    root, plan, _, result = packet(inventory)
    result['rows'][0]['verdict'] = 'no-change'
    with pytest.raises(KnowledgeHubError, match='replacement'):
        validate_semantic_result(root, plan, result, DAY)


@pytest.mark.parametrize('verdict', [[], {}, True, None])
def test_invalid_verdict_type_is_controlled_failure(inventory, verdict):
    root, plan, _, result = packet(inventory)
    result['rows'][0]['verdict'] = verdict
    with pytest.raises(KnowledgeHubError, match='approve'):
        validate_semantic_result(root, plan, result, DAY)


def test_extra_approval_claim_cannot_be_imported(inventory):
    root, plan, _, result = packet(inventory)
    result['owner_approved'] = True
    with pytest.raises(KnowledgeHubError, match='binding'):
        validate_semantic_result(root, plan, result, DAY)


def test_personal_reference_never_exported(inventory):
    import json
    root, items, rows, readiness = inventory
    private = dict(items[0], id='private', visibility='personal-local',
                   path='projects/example/validation/private.md')
    (root / private['path']).write_text('个人想法，不得进入团队包')
    items[0]['evidence_refs'] = [private['path']]
    items.append(private)
    (root / 'registry/items.jsonl').write_text(''.join(json.dumps(item) + '\n' for item in items))
    plan = build_automation_plan(root, items, rows, readiness, DAY)
    task = prepare_semantic_task(root, plan, DAY)
    assert len(task['rows']) == 1 and task['rows'][0]['references'] == []
    assert '个人想法' not in str(task)


@pytest.mark.parametrize('review_status', [
    'pending-owner-review', 'needs-owner-resolution', 'owner-intake-ready',
    'source-identity-match', 'embedded-knowledge-owner-review-required',
    'blocked-pending-owner-review', 'blocked-pending-owner-status-decision',
    'blocked-personal-local', 'blocked-pending-archive-metadata',
])
def test_owner_gated_body_not_copied(inventory, review_status):
    import json
    root, items, rows, readiness = inventory
    items[0]['review_status'] = review_status
    (root / 'registry/items.jsonl').write_text(json.dumps(items[0]) + '\n')
    plan = build_automation_plan(root, items, rows, readiness, DAY)
    task = prepare_semantic_task(root, plan, DAY)
    assert not task['rows'] and task['blocked']


def test_oversized_body_withheld_without_partial_text(inventory):
    root, items, rows, readiness = inventory
    body = root / items[0]['path']
    body.write_text(body.read_text() + 'x' * (33 * 1024))
    plan = build_automation_plan(root, items, rows, readiness, DAY)
    task = prepare_semantic_task(root, plan, DAY)
    assert not task['rows'] and task['blocked']


def test_drift_during_export_rejected(inventory, monkeypatch):
    from tools.codex_assets.knowledge_hub import review_semantic as semantic
    root, items, rows, readiness = inventory
    plan = build_automation_plan(root, items, rows, readiness, DAY)
    original = semantic._bounded
    def drift(value):
        if isinstance(value, list) and value:
            (root / items[0]['path']).write_text('changed during export')
        original(value)
    monkeypatch.setattr(semantic, '_bounded', drift)
    with pytest.raises(KnowledgeHubError, match='changed'):
        prepare_semantic_task(root, plan, DAY)


def test_total_budget_cannot_certify_partial_task(inventory, monkeypatch):
    from tools.codex_assets.knowledge_hub import review_semantic as semantic
    root, items, rows, readiness = inventory
    plan = build_automation_plan(root, items, rows, readiness, DAY)
    monkeypatch.setattr(semantic, 'MAX_BYTES', 5)
    with pytest.raises(KnowledgeHubError, match='budget'):
        prepare_semantic_task(root, plan, DAY)
