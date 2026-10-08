"""General Chinese syntax and comparison lanes, independent synthetic documents."""

import pytest

from tests.test_fifth_retrieval import _hub, _item
from tools.codex_assets.knowledge_hub.search import search, SearchFilters, SearchIndex


def test_long_instruction_is_not_an_unknown_named_subject(tmp_path):
    item = _item('format', '中文说明规范', '中文说明分开写结论、证据与风险。', status='active', kind='standard')
    root = _hub(tmp_path, [item])
    result = search(root, '要把一大段说明整理成中文材料，结论、证据和风险怎么分开写？')
    assert result['results'][0]['item_id'] == 'format'


def test_compound_noun_with_modal_character_is_not_destroyed(tmp_path):
    item = _item('outline', '写作字段规范', '材料的摘要字段应保存来源。', status='active', kind='standard')
    root = _hub(tmp_path, [item])
    result = search(root, '材料摘要字段必须怎样记录来源？')
    assert '摘要' in ''.join(result['query_terms'])
    assert result['results'][0]['item_id'] == 'outline'


def test_normative_negation_prefers_team_policy_over_observed_project_text(tmp_path):
    policy = _item('rule', '故障记录规范', '故障记录区分猜测与已确认原因，证据不足不能写成已确认。',
                   status='active', kind='standard')
    project = _item('incident', '设备故障记录', policy['summary_zh'], project='other', status='active', kind='runbook')
    root = _hub(tmp_path, [policy, project])
    result = search(root, '故障记录只有一个猜测，还不能复现，能直接写成已确认原因吗？')
    assert result['results'][0]['item_id'] == 'rule'
    assert result['search_trace']['concept_query']['polarity']


def test_comparison_projects_independent_topics_to_their_lanes(tmp_path):
    shared = _item('policy', '团队记录写法规范', '团队记录写法区分结论和证据。', status='active', kind='standard')
    local = _item('sampling', 'ORBIT62 热点线程采样', 'ORBIT62 热点线程采样使用调度计数。', project='orbit', kind='runbook')
    root = _hub(tmp_path, [shared, local], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    result = search(root, '团队记录写法和 ORBIT62 热点线程采样步骤是一份规则吗，分别应该查什么？')
    assert {row['item_id'] for row in result['results']} == {'policy', 'sampling'}


@pytest.mark.parametrize('subject', ['星环浮岛项目', '一个星环浮岛项目', 'Marindale', 'Unknownproject', 'SPECTROMETER883'])
def test_unknown_subjects_cannot_be_replaced_with_generic_policy(tmp_path, subject):
    item = _item('rule', '团队材料记录规范', '材料记录保存结论、证据、风险与来源。', status='active', kind='standard')
    root = _hub(tmp_path, [item])
    assert search(root, subject + ' 材料记录必须保存哪些证据和来源？')['results'] == []


def test_normative_intent_prioritizes_standard_over_observation_echo(tmp_path):
    query = '材料记录必须包含结论和证据吗？'
    standard = _item('standard', '材料记录规范', '材料记录包含结论和证据。', status='active', kind='standard')
    observation = _item('observation', query, query, project='elsewhere', status='active', kind='validation')
    root = _hub(tmp_path, [standard, observation])
    assert search(root, query)['results'][0]['item_id'] == 'standard'


def test_comparison_steps_prepare_both_policy_and_runbook(tmp_path):
    policy = _item('policy', '团队记录写法规范', '团队记录写法区分结论和证据。', status='active', kind='standard')
    guide = _item('guide', 'ORBIT62 热点线程采样', 'ORBIT62 热点线程采样使用调度计数。', project='orbit', kind='runbook')
    decision = _item('aaa', 'ORBIT62 热点线程采样步骤规则', 'ORBIT62 热点线程采样步骤规则采用调度计数。', project='orbit', kind='decision')
    root = _hub(tmp_path, [policy, guide, decision], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    result = search(root, '团队记录写法和 ORBIT62 热点线程采样步骤是一份规则吗，分别应该查什么？')
    assert {row['item_id'] for row in result['results'][:2]} == {'policy', 'guide'}


@pytest.mark.parametrize('alias', ['只有岛项目', '第三个岛项目', '整理成岛项目'])
def test_registered_chinese_alias_is_preserved_before_question_grammar(tmp_path, alias):
    item = _item('guide', '配置参数记录规范', '配置参数记录保存结论和证据。', project='island', kind='runbook')
    root = _hub(tmp_path, [item], routes=[dict(aliases=[alias], domain_refs=['projects/island'])])
    result = search(root, alias + ' 配置参数记录必须保存哪些结论和证据？')
    assert result['results'][0]['item_id'] == 'guide'
    assert alias in result['search_trace']['concept_query']['anchors']


@pytest.mark.parametrize('query', ['请问必须应该怎样？', '请帮我应该如何？'])
def test_no_effective_topic_stays_zero_instead_of_legacy_fuzzy_fallback(tmp_path, query):
    root = _hub(tmp_path, [_item('policy', '记录规范', '必须应该记录内容。', status='active', kind='standard')])
    assert search(root, query)['results'] == []


def test_technical_shared_memory_does_not_become_shared_policy_comparison(tmp_path):
    item = _item('ipc', 'ORBIT62 视频音频共享内存契约', '视频与音频共享内存订阅使用统一缓冲区。', project='orbit', kind='architecture')
    root = _hub(tmp_path, [item], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    index = SearchIndex(root)
    index.ensure()
    plan = index.concept_query('ORBIT62 视频和音频怎样通过共享内存订阅？')
    assert plan.shared_terms == plan.project_terms == ()
    assert search(root, 'ORBIT62 视频和音频怎样通过共享内存订阅？', search_index=index)['results'][0]['item_id'] == 'ipc'


@pytest.mark.parametrize('filters', [SearchFilters(domains=['projects/orbit']), SearchFilters(owners=['absent']),
                                    SearchFilters(statuses=['reviewing'])])
def test_intent_and_projection_never_relax_explicit_filters(tmp_path, filters):
    policy = _item('policy', '团队记录写法规范', '团队记录写法区分结论和证据。', status='active', kind='standard')
    guide = _item('guide', 'ORBIT62 热点线程采样', 'ORBIT62 热点线程采样使用调度计数。', project='orbit', kind='runbook')
    root = _hub(tmp_path, [policy, guide], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    result = search(root, '团队记录写法和 ORBIT62 热点线程采样步骤是一份规则吗，分别应该查什么？', filters=filters)
    assert all(row['item_id'] != 'policy' for row in result['results'])


@pytest.mark.parametrize('entity', ['星环浮岛项目', '一个星环浮岛项目', '星环浮岛设备', 'Unknownproject', 'Unknown883'])
def test_named_unknown_operands_stay_global_across_projected_lanes(tmp_path, entity):
    policy = _item('policy', '团队记录写法规范', '团队记录写法区分结论和证据。', status='active', kind='standard')
    guide = _item('guide', 'ORBIT62 热点线程采样', 'ORBIT62 热点线程采样使用调度计数。', project='orbit', kind='runbook')
    root = _hub(tmp_path, [policy, guide], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    query = '团队记录写法和 ORBIT62 versus ' + entity + ' 热点线程采样步骤怎样分别查？'
    assert search(root, query)['results'] == []


def test_route_alias_preclassification_does_not_expand_vocabulary_budget(monkeypatch):
    from tools.codex_assets.knowledge_hub import query_concepts
    from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
    monkeypatch.setattr(query_concepts, 'MAX_VOCABULARY', 2)
    with pytest.raises(KnowledgeHubError, match='vocabulary exceeds budget'):
        query_concepts.extract_concepts('AX19 怎样记录材料？', {'记录':1, '材料':1}, 2,
            [dict(aliases=['AX19'], domain_refs=['projects/ax'])])


def test_technical_shared_memory_cannot_admit_competing_team_standard(tmp_path):
    ipc = _item('ipc', 'HELIX47 视频音频共享内存契约', '视频音频通过共享内存订阅。', project='helix', kind='architecture')
    norm = _item('norm', '视频音频共享内存订阅规范', '视频音频通过共享内存订阅。', status='active', kind='standard')
    root = _hub(tmp_path, [ipc, norm], routes=[dict(aliases=['HELIX47'], domain_refs=['projects/helix'])])
    result = search(root, 'HELIX47 视频和音频怎样通过共享内存订阅？')
    assert [row['item_id'] for row in result['results']] == ['ipc']


@pytest.mark.parametrize('entity', ['GNOSTER', 'device gnoster', 'project Gnoster', 'board gnoster'])
def test_corpus_known_named_operand_is_not_a_registered_entity(tmp_path, entity):
    policy = _item('policy', '团队记录写法规范', '团队记录写法区分结论和证据。', status='active', kind='standard')
    guide = _item('guide', 'ORBIT62 热点线程采样', 'ORBIT62 热点线程采样使用调度计数。', project='orbit', kind='runbook')
    noise = _item('noise', 'GNOSTER 材料', 'gnoster 存在于词表，不构成项目登记。', project='elsewhere')
    root = _hub(tmp_path, [policy, guide, noise], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    result = search(root, '团队记录写法和 ORBIT62 ' + entity + ' 热点线程采样步骤怎样分别查？')
    assert result['results'] == []


@pytest.mark.parametrize('connector', [' versus ', ' vs ', ' against ', ' and ', ' or ', ', '])
def test_known_explicit_entity_constraint_survives_comparison_lists(tmp_path, connector):
    policy = _item('policy', '团队记录写法规范', '团队记录写法区分结论和证据。', status='active', kind='standard')
    guide = _item('guide', 'ORBIT62 热点线程采样', 'ORBIT62 热点线程采样使用调度计数。', project='orbit', kind='runbook')
    noise = _item('noise', 'GNOSTER 材料', 'gnoster 是词表内容，不是登记项目。', project='elsewhere')
    root = _hub(tmp_path, [policy, guide, noise], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    query = '团队记录写法和 ORBIT62 versus 热点线程采样' + connector + 'GNOSTER 应怎样分别查？'
    assert search(root, query)['results'] == []


def test_known_entity_requires_literal_evidence_on_both_comparison_lanes(tmp_path):
    policy = _item('policy', '团队 GNOSTER 记录写法规范', 'GNOSTER 团队记录写法区分结论和证据。', status='active', kind='standard')
    guide = _item('guide', 'ORBIT62 GNOSTER 热点线程采样', 'ORBIT62 GNOSTER 热点线程采样使用调度计数。', project='orbit', kind='runbook')
    root = _hub(tmp_path, [policy, guide], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    query = '团队记录写法和 ORBIT62 GNOSTER 热点线程采样步骤怎样分别查？'
    assert {row['item_id'] for row in search(root, query)['results']} == {'policy', 'guide'}


@pytest.mark.parametrize('entity', ['GNOSTER', 'Gnoster', 'gnoster'])
@pytest.mark.parametrize('pair', ['HELIX47 versus {entity}', '{entity} versus HELIX47',
                                 'compare HELIX47 with {entity}', 'between HELIX47 and {entity}'])
def test_named_comparand_role_is_casefolded_even_when_corpus_known(tmp_path, entity, pair):
    policy = _item('policy', '团队记录写法规范', '团队记录写法区分结论和证据。', status='active', kind='standard')
    guide = _item('guide', 'HELIX47 热点线程采样', 'HELIX47 热点线程采样使用调度计数。', project='helix', kind='runbook')
    noise = _item('noise', 'GNOSTER 材料', 'gnoster 是普通词表内容。', project='elsewhere')
    root = _hub(tmp_path, [policy, guide, noise], routes=[dict(aliases=['HELIX47'], domain_refs=['projects/helix'])])
    query = '团队记录写法和 ' + pair.format(entity=entity) + ' 热点线程采样步骤怎样分别查？'
    assert search(root, query)['results'] == []


@pytest.mark.parametrize('query', ['How compare configuration with deployment?',
    'How compare configuration with deployment for HELIX47?',
    'HELIX47 versus shared general procedure, how should we compare?',
    'shared general procedure versus HELIX47, how should we compare?'])
def test_comparand_roles_preserve_ordinary_or_marked_normative_topics(query):
    from tools.codex_assets.knowledge_hub.query_concepts import extract_concepts
    plan = extract_concepts(query, {'configuration':3, 'deployment':4, 'procedure':2}, 5,
        [dict(aliases=['HELIX47'], domain_refs=['projects/helix'])])
    assert not set(plan.global_anchors).intersection({'configuration', 'deployment', 'procedure'})
    assert not set(plan.global_anchors).intersection({'shared', 'general', 'common', 'team', 'normative'})
