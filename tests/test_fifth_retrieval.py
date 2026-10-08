"""Corpus-derived questions tested outside the exposed development gold."""

import json
import sqlite3
import gc
import os

import pytest

from tools.codex_assets.knowledge_hub import query_concepts as concepts
from tools.codex_assets.knowledge_hub import search_query
from tools.codex_assets.knowledge_hub.retrieval_diagnostics import development_diagnostics
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.search import SearchIndex, SearchFilters, SearchBoundaryError, search, _score


def _item(key, title, summary, *, project='', status='reviewing', kind='decision', visibility='team-internal'):
    path = 'projects/' + project + '/current/' + key + '.md' if project else key + '.md'
    return dict(id=key, path=path, title=title, summary_zh=summary, tags=[], status=status, kind=kind,
                scope='project-specific' if project else 'team-general',
                domain='projects/' + project if project else 'governance', visibility=visibility, owner='maintainer')


def _hub(root, items, bodies=None, routes=None):
    (root/'registry').mkdir()
    for item in items:
        path = root/item['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# ' + item['title'] + '\n\n' + (bodies or {}).get(item['id'], item['summary_zh']))
    (root/'registry/items.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False)+'\n' for item in items))
    (root/'registry/sources.json').write_text('{"sources":[]}')
    (root/'registry/retired-sources.jsonl').write_text('')
    if routes:
        (root/'registry/project-routes.json').write_text(json.dumps(dict(routes=routes)))
    return root


def test_long_planning_question_keeps_ordinal_and_finds_corpus_concepts(tmp_path):
    answer = _item('foundation', '第三产品 ZEUS17 研发基础设施', '第三产品选型前准备代码规范、组件边界和测试模板。', project='zeus')
    unrelated = _item('daily', 'ZEUS17 日常记录', '本轮状态为 reviewing，尚未执行验收。', project='zeus')
    root = _hub(tmp_path, [answer, unrelated])
    query = 'ZEUS17 第三款产品硬件还没有定，代码规范和测试模板现在先做哪些？'
    result = search(root, query)
    assert result['results'][0]['item_id'] == 'foundation'
    assert result['results'][0]['status'] == 'reviewing'
    assert '第三产品' in result['query_terms'] and result['query'] == query
    assert result['search_trace']['concept_query']['polarity']


def test_long_distribution_question_uses_title_summary_and_technical_anchor(tmp_path):
    answer = _item('distribution', 'LUMEN42 私有工具分发', '团队成员通过运行包交付技能，实现源码不进入成员仓。', project='lumen')
    noise = _item('notice', 'LUMEN42 通告', '审查日志和本轮测试记录。', project='lumen')
    root = _hub(tmp_path, [answer, noise])
    result = search(root, 'LUMEN42 团队成员要用私有工具，怎么交付技能而不暴露实现源码？')
    assert result['results'][0]['item_id'] == 'distribution'
    assert '不' in result['search_trace']['concept_query']['polarity']


def test_status_and_directory_values_are_not_topic_evidence():
    noise = _item('noise', '日报', '工作记录', project='unrelated', status='reviewing')
    assert _score(noise['path'], '.md', '工作记录', noise, '', ['reviewing', 'current'], 'reviewing current') is None


def test_general_lifecycle_definition_wins_over_project_status_echo(tmp_path):
    definition = _item('policy', '生命周期与规则生效规范', '目录位置不改变 draft 状态，规则生效要求明确审批。',
                       status='active', kind='standard')
    project = _item('echo', '项目生命周期记录', '目录位置和规则生效说明。', project='other', status='active', kind='architecture')
    body = '项目决策还在 draft，放进 current 目录不代表规则生效。'
    root = _hub(tmp_path, [definition, project], dict(policy=body, echo=body))
    result = search(root, '项目决策还在 draft，放在 current 目录就能当生效规则吗？')
    assert result['results'][0]['item_id'] == 'policy'
    assert 'active-general-policy' in result['results'][0]['why_selected']


def test_new_runbook_question_finds_operational_content_not_analysis(tmp_path):
    guide = _item('guide', 'ORION51 内存快照采集使用指南', '设备准备、五类内存场景采集和数据完整性判读。', project='orion', kind='runbook')
    report = _item('report', 'ORION51 内存算法分析', '历史数据对照与算法分析。', project='orion', kind='validation')
    root = _hub(tmp_path, [guide, report], dict(guide='设备准备后采集五类内存场景，判断数据完整性。'))
    result = search(root, 'ORION51 要采集五类内存场景，设备上怎样准备和判断数据完整性？')
    assert result['results'][0]['item_id'] == 'guide'


def test_registered_project_alias_can_find_document_without_literal_project_name(tmp_path):
    guide = _item('guide', '采样工具完整使用指南', '设备准备、八类采样场景和数据判读。', project='component', kind='runbook')
    wrong = _item('wrong', 'VEGA73 采样指南', guide['summary_zh'], project='elsewhere', status='active')
    routes = [dict(group_id='vega73', aliases=['VEGA73'], domain_refs=['projects/device']),
              dict(group_id='vega73', aliases=['component'], domain_refs=['projects/component'])]
    root = _hub(tmp_path, [guide, wrong], routes=routes)
    result = search(root, 'VEGA73 设备上怎样准备八类采样场景和判断数据？')
    assert result['results'][0]['item_id'] == 'guide'
    assert all(row['domain'] != 'projects/elsewhere' for row in result['results'])


def test_wrong_project_body_mentions_do_not_override_registered_domain(tmp_path):
    right = _item('right', 'VEGA73 电源诊断', 'PB77 电源控制契约。', project='vega')
    wrong = _item('wrong', 'LYRA81 电源诊断', 'VEGA73 PB77 电源控制契约。', project='lyra', status='active')
    routes = [dict(group_id='vega', aliases=['VEGA73'], domain_refs=['projects/vega'])]
    root = _hub(tmp_path, [right, wrong], routes=routes)
    result = search(root, 'VEGA73 的 PB77 为什么不能控制电源？')
    assert result['results'][0]['item_id'] == 'right'
    assert all(row['item_id'] != 'wrong' for row in result['results'])


def test_registered_alias_is_not_dependent_on_uppercase_or_digits(tmp_path):
    right = _item('right', '固件校验诊断指南', '固件校验和故障诊断。', project='zephyr')
    wrong = _item('wrong', 'Zephyr 固件校验诊断指南', right['summary_zh'], project='other', status='active')
    routes = [dict(group_id='zephyr', aliases=['Zephyr'], domain_refs=['projects/zephyr'])]
    root = _hub(tmp_path, [right, wrong], routes=routes)
    result = search(root, 'Zephyr 固件校验为什么失败，怎样进行故障诊断？')
    assert result['results'][0]['item_id'] == 'right'
    assert all(row['item_id'] != 'wrong' for row in result['results'])


def test_declared_project_domain_includes_children_without_matching_prefix_lookalikes(tmp_path):
    child = _item('child', 'VEGA73 电源控制', 'PB77 电源控制和故障诊断。', project='vega/drivers')
    wrong = _item('wrong', child['title'], child['summary_zh'], project='vega-other', status='active')
    routes = [dict(aliases=['VEGA73'], group_id='vega', domain_refs=['projects/vega'])]
    root = _hub(tmp_path, [child, wrong], routes=routes)
    result = search(root, 'VEGA73 的 PB77 为什么不能控制电源？')
    assert result['results'][0]['item_id'] == 'child'
    assert all(row['item_id'] != 'wrong' for row in result['results'])


@pytest.mark.parametrize('query', ['陌生医院结算接口如何配置？', '请问陌生医院结算接口如何配置？',
                                   'UNKNOWN938 的接口为什么不能工作？'])
def test_unknown_subject_or_identifier_does_not_degrade_into_a_generic_answer(tmp_path, query):
    root = _hub(tmp_path, [_item('generic', '接口配置规范', '系统接口配置和生命周期门禁。', status='active', kind='standard')])
    result = search(root, query)
    assert not result['results']


def test_private_documents_and_explicit_filters_remain_excluded(tmp_path):
    public = _item('public', 'ORION51 固件校验', '固件校验和故障排查。', project='orion')
    private = _item('private', 'ORION51 固件校验详细结论', public['summary_zh'], project='orion', visibility='personal-local', status='active')
    root = _hub(tmp_path, [public, private])
    query = 'ORION51 固件校验为什么失败？'
    result = search(root, query)
    assert all(row['item_id'] != 'private' for row in result['results'])
    assert search(root, query, filters=SearchFilters(statuses=['active']))['results'] == []


def test_known_project_does_not_supply_an_unsupported_subject(tmp_path):
    root = _hub(tmp_path, [_item('generic', 'VEGA73 接口和阈值规范', '系统接口配置和阈值。', project='vega')])
    assert search(root, 'VEGA73 陌生医院接口和阈值怎么配置？')['results'] == []


def test_lexical_negation_compounds_and_technical_tokens_survive_extraction():
    vocabulary, count = concepts.corpus_lexicon([dict(title='非易失性 无线网络', summary_zh='非易失性存储器读取', tags=[])])
    plan = concepts.extract_concepts('AX19 的 /dev/flash0 非易失性存储器怎么读取，无线网络会受影响吗？', vocabulary, count)
    assert '/dev/flash0' in plan.terms and 'ax19' in plan.anchors
    assert '非易失性' in ''.join(plan.terms) and '无线网络' in ''.join(plan.terms)
    assert plan.lexical_constraints
    assert not concepts.exact_concept_match('pb77', 'pb770')


def test_title_nouns_containing_function_characters_are_not_destroyed(tmp_path):
    item = _item('summary', 'AX19 智能模块性能摘要', '智能模块性能摘要生成方法。', project='ax')
    root = _hub(tmp_path, [item])
    result = search(root, 'AX19 智能模块性能摘要怎么生成？')
    assert result['results'][0]['item_id'] == 'summary'
    terms = ''.join(result['query_terms'])
    assert '智能' in terms and '性能' in terms and '摘要' in terms


def test_fallback_and_sqlite_share_the_same_concepts(tmp_path, monkeypatch):
    root = _hub(tmp_path, [_item('guide', 'ORION51 第四产品研发基础设施', '第四产品代码规范和测试模板。', project='orion')])
    query = 'ORION51 第四款产品代码规范和测试模板现在先做哪些？'
    indexed = search(root, query)
    monkeypatch.setattr(SearchIndex, 'ensure', lambda *a, **kw:(_ for _ in ()).throw(sqlite3.DatabaseError('fixture')))
    scanned = search(root, query)
    assert indexed['query_terms'] == scanned['query_terms']
    assert [row['item_id'] for row in indexed['results']] == [row['item_id'] for row in scanned['results']]


def test_concept_metadata_budget_does_not_fall_back_to_unbounded_scan(tmp_path, monkeypatch):
    root = _hub(tmp_path, [_item('guide', 'ORION51 使用指南', '设备准备和采集。', project='orion')])
    index = SearchIndex(root)
    index.ensure()
    with sqlite3.connect(index.path) as connection:
        connection.execute('update documents set item_json=?', ('x'*(concepts.MAX_METADATA_BYTES+1),))
    monkeypatch.setattr(search_query, '_scan_candidates', lambda root:pytest.fail('resource failure must not scan'))
    with pytest.raises(SearchBoundaryError, match='corpus budget'):
        search(root, 'ORION51 设备怎样准备采集？', search_index=index)


def test_case_and_route_budgets_are_visible_errors(monkeypatch):
    monkeypatch.setattr(concepts, 'MAX_ITEMS', 1)
    with pytest.raises(KnowledgeHubError, match='item budget'):
        concepts.corpus_lexicon([{}, {}])
    with pytest.raises(KnowledgeHubError, match='route budget'):
        concepts.extract_concepts('AX19 怎样准备设备？', {}, 1, [{}]*1001)
    with pytest.raises(KnowledgeHubError, match='typed budget'):
        concepts.corpus_lexicon([dict(tags='not-a-list')])


def test_query_concept_budget_never_invokes_scan_fallback(tmp_path, monkeypatch):
    root = _hub(tmp_path, [_item('guide', 'Guide', 'sample')])
    monkeypatch.setattr(search_query, '_scan_candidates', lambda root:pytest.fail('query boundary must not scan'))
    with pytest.raises(SearchBoundaryError, match='64-term'):
        search(root, 'how ' + ' '.join('term' + str(i) for i in range(65)))


def test_idf_frequencies_come_from_topic_fields_not_status_attributes():
    vocabulary, _ = concepts.corpus_lexicon([dict(title='采集', summary_zh='sample', tags=[], status='reviewing')] * 3)
    assert vocabulary['sample'] == 3 and vocabulary['采集'] == 3
    assert 'reviewing' not in vocabulary


def test_cursor_binds_concept_route_scope_not_just_document_content(tmp_path):
    items = [_item('one', 'VEGA73 采集指南', '采集场景和设备准备。', project='one'),
             _item('two', 'VEGA73 采集指南', '采集场景和设备准备。', project='two')]
    routes = [dict(aliases=['VEGA73'], group_id='group', domain_refs=['projects/one', 'projects/two'])]
    root = _hub(tmp_path, items, routes=routes)
    query = 'VEGA73 设备怎样准备采集场景？'
    first = search(root, query, limit=1)
    assert first['pagination']['has_more']
    routes[0]['domain_refs'] = ['projects/one']
    (root/'registry/project-routes.json').write_text(json.dumps(dict(routes=routes)))
    with pytest.raises(KnowledgeHubError, match='cursor'):
        search(root, query, limit=1, cursor=first['pagination']['next_cursor'])


def test_stage_diagnostics_use_the_same_concept_policy_as_actual_search(tmp_path):
    root = _hub(tmp_path, [_item('foundation', 'ZEUS17 第三产品研发基础设施', '第三产品代码规范和测试模板。', project='zeus')])
    query = 'ZEUS17 第三款产品代码规范和测试模板现在先做哪些？'
    definition = dict(id='synthetic', query=query, expected_ids=['foundation'])
    result = search(root, query)
    measured = dict(definition, hit=True, rank=1, forbidden_hits=[], ranked=result['results'])
    report = development_diagnostics(dict(cases=[definition]), dict(cases=[measured]), root=root)
    row = report['rows'][0]
    assert row['expected_stage_evidence'][0]['scoring_passed'] is True
    assert row['expected_stage_evidence'][0]['query_term_count'] == len(result['query_terms'])
    assert row['alias']['method'] == 'corpus-concepts-plus-existing-term-variants'


def test_repeated_concept_plans_close_sqlite_handles_without_waiting_for_gc(tmp_path):
    root = _hub(tmp_path, [_item('guide', 'ORION51 场景采集', '场景采集和设备准备。', project='orion')])
    index = SearchIndex(root)
    index.ensure()
    gc.collect()
    before = len(os.listdir('/proc/self/fd'))
    gc.disable()
    try:
        for _ in range(25):
            index.concept_query('ORION51 场景采集设备怎样准备？')
        assert len(os.listdir('/proc/self/fd')) <= before + 1
    finally:
        gc.enable()


@pytest.mark.parametrize('name', ['UNKNOWNPROJECT', 'Unknownproject', 'unknownproject'])
@pytest.mark.parametrize('prefix', ['', '请问 ', '请帮我 ', '如何 ', 'Please ', 'How to configure '])
def test_unknown_ascii_project_subject_is_case_insensitive(tmp_path, name, prefix):
    root = _hub(tmp_path, [_item('generic', '接口配置故障诊断指南', '系统接口配置、参数设置和故障诊断。', status='active')])
    assert search(root, prefix + name + ' 接口配置为什么失败，如何设置参数和诊断故障？')['results'] == []


@pytest.mark.parametrize('query', ['how to configure interface parameters?', 'Configure interface parameters?',
                                   'Please configure interface parameters?', 'How should I configure interface parameters?',
                                   'interface parameters how to configure?', 'Interface parameters how to configure?'])
def test_ordinary_english_topics_and_unknown_action_words_are_not_all_entities(tmp_path, query):
    root = _hub(tmp_path, [_item('generic', 'Interface parameters guide', 'Interface parameters configuration.', status='active')])
    assert search(root, query)['results'][0]['item_id'] == 'generic'


def test_unknown_explicit_english_entity_cannot_use_topic_only_answer(tmp_path):
    root = _hub(tmp_path, [_item('generic', 'Interface parameters guide', 'Interface parameters configuration.', status='active')])
    assert search(root, 'How to configure project Unknownproject interface parameters?')['results'] == []


def test_real_frontmatter_does_not_count_status_or_directory_as_topic(tmp_path):
    item = _item('noise', '日报', '工作记录', project='unrelated', status='reviewing')
    body = '---\nid: noise\nstatus: reviewing\npath: projects/unrelated/current/noise.md\n---\n# 日报\n工作记录'
    root = _hub(tmp_path, [item], dict(noise=body))
    (root/item['path']).write_text(body)
    result = search(root, 'reviewing current 是什么？')
    assert result['results'] == [] and result['search_trace']['candidate_pool']['after_filters'] == 0


def test_real_prose_definition_remains_findable_and_preview_points_to_prose(tmp_path):
    item = _item('guide', '规则说明指南', '生命周期规则说明。', status='active', kind='standard')
    body = '---\nid: guide\nstatus: reviewing\npath: projects/unrelated/current/guide.md\n---\n# 规则说明\nreviewing 是候选状态，current 目录不改变状态资格。'
    root = _hub(tmp_path, [item], dict(guide=body))
    (root/item['path']).write_text(body)
    result = search(root, 'reviewing current 是什么？')
    assert result['results'][0]['item_id'] == 'guide'
    assert result['results'][0]['line'] == 7
    assert '候选状态' in result['results'][0]['preview']
    assert 'path:' not in result['results'][0]['preview']


@pytest.mark.parametrize('fallback', [False, True])
def test_frontmatter_topic_boundary_has_sqlite_scan_and_diagnostic_parity(tmp_path, monkeypatch, fallback):
    noise = _item('noise', '日报', '工作记录', project='unrelated', status='reviewing')
    guide = _item('guide', '规则说明', '生命周期定义。', status='active', kind='standard')
    header = '---\nstatus: reviewing\npath: projects/unrelated/current/noise.md\n---\n'
    root = _hub(tmp_path, [noise, guide], dict(noise=header+'工作记录', guide=header+'reviewing 状态不因 current 目录生效。'))
    (root/noise['path']).write_text(header+'工作记录')
    (root/guide['path']).write_text(header+'reviewing 状态不因 current 目录生效。')
    if fallback:
        monkeypatch.setattr(SearchIndex, 'ensure', lambda *a, **kw:(_ for _ in ()).throw(sqlite3.DatabaseError('fixture')))
    result = search(root, 'reviewing current 是什么？')
    assert [row['item_id'] for row in result['results']] == ['guide']
    assert result['results'][0]['query_coverage'] == 1


def test_path_field_never_returns_as_weighted_or_distinctive_topic_evidence(tmp_path):
    item = _item('ordinary', '接口说明', '接口配置指南。', project='unrelated', status='active')
    root = _hub(tmp_path, [item])
    assert search(root, 'current 接口是什么？')['results'] == []


def test_unknown_entity_and_frontmatter_negative_keep_explicit_filters(tmp_path, monkeypatch):
    item = _item('noise', '接口配置', '参数配置。', project='unrelated', status='reviewing')
    root = _hub(tmp_path, [item])
    query = 'Unknownproject 接口配置为什么失败，如何设置参数？'
    first = search(root, query, filters=SearchFilters(statuses=['reviewing']))
    assert first['results'] == []
    monkeypatch.setattr(SearchIndex, 'ensure', lambda *a, **kw:(_ for _ in ()).throw(sqlite3.DatabaseError('fixture')))
    assert search(root, query, filters=SearchFilters(statuses=['reviewing']))['results'] == []
