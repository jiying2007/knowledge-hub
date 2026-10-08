"""Syntax, scope-specific concepts and nonredundant authoritative results."""

from tests.test_fifth_retrieval import _hub, _item
from tools.codex_assets.knowledge_hub.search import search
import pytest
import sqlite3
from tools.codex_assets.knowledge_hub.search import SearchIndex, SearchFilters


def test_indefinite_discovery_and_disposal_grammar_is_not_a_subject(tmp_path):
    rule = _item('rule', '外部材料使用规范', '外部材料需复核来源和证据，不允许复制观点进入团队规则。', status='active', kind='standard')
    root = _hub(tmp_path, [rule])
    result = search(root, '找到一份外部材料，能把观点整段复制进团队规则立即使用吗，使用前应检查什么？')
    assert result['results'][0]['item_id'] == 'rule'


def test_project_technical_subject_does_not_constrain_general_clause(tmp_path):
    policy = _item('policy', '团队 TOOL77 工具入口规范', '团队 TOOL77 工具入口规定权限和证据。', status='active', kind='standard')
    guide = _item('guide', 'ORBIT62 CRAFT99 应用构建方案', 'CRAFT99 应用构建交付 SDK 工具包。', project='orbit')
    root = _hub(tmp_path, [policy, guide], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    result = search(root, '团队 TOOL77 工具入口规范和 ORBIT62 CRAFT99 应用构建，是同一种职责吗，SDK 工具包该查哪层资料？')
    assert {r['item_id'] for r in result['results'][:2]} == {'policy', 'guide'}


def test_literal_focus_beats_peripheral_question_echo(tmp_path):
    query = 'SIGNAL v7 规范允许普通请求改变权限吗？'
    focus = _item('focus', 'SIGNAL 平面规范 v7', 'SIGNAL v7 规范不允许普通请求改变权限。', kind='decision')
    peripheral = _item('peripheral', '其他架构 SIGNAL v7 规范', query, kind='decision')
    root = _hub(tmp_path, [focus, peripheral])
    assert search(root, query)['results'][0]['item_id'] == 'focus'


def test_current_policy_form_beats_experimental_echo_for_default_question(tmp_path):
    query = 'ORBIT62 LOW、HIGH 哪个是默认，配置模式能运行中随时改吗？'
    policy = _item('policy', 'ORBIT62 配置模式当前决策', 'LOW HIGH 默认配置模式在初始化固定，配置模式不能运行中随时改。', project='orbit')
    experiment = _item('experiment', 'ORBIT62 LOW HIGH 配置模式实验', query, project='orbit')
    root = _hub(tmp_path, [policy, experiment], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    assert search(root, query)['results'][0]['item_id'] == 'policy'


def test_explicit_normative_clause_without_team_prefix_keeps_both_layers(tmp_path):
    policy = _item('policy', '材料使用规则', '材料使用规则检查证据和复核。', status='active', kind='standard')
    guide = _item('guide', 'ORBIT62 THREAD88 硬切架构', 'THREAD88 硬切架构划定设备范围。', project='orbit', kind='architecture')
    root = _hub(tmp_path, [policy, guide], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    result = search(root, '材料使用规则和 ORBIT62 THREAD88 硬切架构，能不区分范围就当所有项目的默认要求吗？')
    assert {r['item_id'] for r in result['results'][:2]} == {'policy', 'guide'}


@pytest.mark.parametrize('name', ['ASTERON', 'Asteron', 'asteron'])
def test_scoped_topic_association_never_registers_explicit_entity(tmp_path, name):
    policy = _item('policy', '团队工具入口规范', '团队工具入口规定权限和证据。', status='active', kind='standard')
    guide = _item('guide', 'ORBIT62 ASTERON 工具示例', 'ASTERON 是工具主题而非登记实体。', project='orbit')
    root = _hub(tmp_path, [policy, guide], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    query = '团队工具入口规范和 ORBIT62 versus ' + name + ' 应怎样分别查？'
    result = search(root, query)
    assert [row['item_id'] for row in result['results']] == ['guide']
    index = SearchIndex(root)
    index.ensure()
    plan = index.concept_query(query)
    assert name.lower() in plan.global_anchors and name.lower() not in plan.project_anchors


def test_role_projection_scan_parity_and_filters(tmp_path, monkeypatch):
    policy = _item('policy', '团队工具入口规范', '团队工具入口规定权限和证据。', status='active', kind='standard')
    guide = _item('guide', 'ORBIT62 CRAFT99 应用构建方案', 'CRAFT99 应用构建交付 SDK 工具包。', project='orbit')
    root = _hub(tmp_path, [policy, guide], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    query = '团队工具入口规范和 ORBIT62 CRAFT99 应用构建，应该怎样分别查？'
    indexed = search(root, query)
    assert all(row['item_id'] != 'policy' for row in search(root, query, filters=SearchFilters(domains=['projects/orbit']))['results'])
    monkeypatch.setattr(SearchIndex, 'ensure', lambda *a, **kw:(_ for _ in ()).throw(sqlite3.DatabaseError('fixture')))
    assert [r['item_id'] for r in search(root, query)['results']] == [r['item_id'] for r in indexed['results']]


@pytest.mark.parametrize('name', ['CRAFT99', 'Craft99', 'craft99'])
@pytest.mark.parametrize('head', ['项目', '设备', '产品', '板卡', '仓库'])
@pytest.mark.parametrize('position', ['suffix', 'prefix'])
def test_explicit_chinese_entity_head_precedes_scoped_technical_topic(tmp_path, name, head, position):
    policy = _item('policy', '团队 TOOL77 工具入口规范', '团队 TOOL77 工具入口规定权限和证据。', status='active', kind='standard')
    guide = _item('guide', 'ORBIT62 CRAFT99 应用构建方案', 'CRAFT99 应用构建交付 SDK 工具包。', project='orbit')
    root = _hub(tmp_path, [policy, guide], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/orbit'])])
    entity = name + head if position == 'suffix' else head + name
    query = '团队 TOOL77 工具入口规范和 ORBIT62 ' + entity + '应用构建，是同一种职责吗？'
    result = search(root, query)
    assert all(row['item_id'] != 'policy' for row in result['results'])
    index = SearchIndex(root)
    index.ensure()
    plan = index.concept_query(query)
    assert name.lower() in plan.global_anchors and name.lower() not in plan.project_anchors


@pytest.mark.parametrize('alias', ['星环项目', '只有银河能源研究所项目', '第三个岛设备'])
def test_registered_alias_containing_chinese_entity_head_keeps_route(tmp_path, alias):
    guide = _item('guide', '配置参数记录规范', '配置参数记录保存结论和证据。', project='island', kind='runbook')
    root = _hub(tmp_path, [guide], routes=[dict(aliases=[alias], domain_refs=['projects/island'])])
    result = search(root, alias + ' 配置参数记录必须保存哪些结论和证据？')
    assert [row['item_id'] for row in result['results']] == ['guide']
    index = SearchIndex(root)
    index.ensure()
    plan = index.concept_query(alias + ' 配置参数记录必须保存哪些结论和证据？')
    assert alias in plan.project_anchors and alias not in plan.global_anchors


@pytest.mark.parametrize('head', ['项目', '设备', '产品', '板卡', '仓库'])
def test_prefix_chinese_entity_head_is_not_itself_unknown_subject(tmp_path, head):
    guide = _item('guide', '配置参数记录规范', '配置参数记录保存结论和证据。', project='island', kind='runbook')
    root = _hub(tmp_path, [guide], routes=[dict(aliases=['ORBIT62'], domain_refs=['projects/island'])])
    assert [row['item_id'] for row in search(root, head + 'ORBIT62 配置参数记录必须保存哪些结论和证据？')['results']] == ['guide']


def _signed_hub(root):
    one = _item('one', 'ORBIT17 flash guard SPI 发布记录', 'flash guard SPI 发布记录与Owner刷新决策。', project='orbit')
    two = _item('two', 'PULSE28 flash guard SPI 发布记录', one['summary_zh'], project='pulse')
    return _hub(root, [one, two], routes=[dict(aliases=['ORBIT17'], domain_refs=['projects/orbit']),
                                        dict(aliases=['PULSE28'], domain_refs=['projects/pulse'])])


@pytest.mark.parametrize('ending', ['', '.', '。', '?', '？'])
@pytest.mark.parametrize('subject', ['project:unregistered-iris-473', '项目 NebulaMCU321',
                                   'NebulaMCU321芯片项目', '设备NebulaMCU321', 'project NebulaMCU321'])
def test_explicit_unknown_subject_is_always_on_outside_natural_gate(tmp_path, ending, subject):
    root = _signed_hub(tmp_path)
    result = search(root, subject + ' 请给我 flash guard SPI 发布记录' + ending)
    assert result['results'] == []
    assert result['search_trace']['concept_query']['hard_constraints_enabled'] is True


@pytest.mark.parametrize('ending', ['', '.', '。', '?', '？'])
@pytest.mark.parametrize('head', ['project:ORBIT17', 'ORBIT17芯片项目', '项目ORBIT17'])
def test_explicit_known_subject_and_negative_route_do_not_depend_on_question_mark(tmp_path, ending, head):
    root = _signed_hub(tmp_path)
    result = search(root, head + ' flash guard SPI 发布记录，排除PULSE28' + ending)
    assert [row['domain'] for row in result['results']] == ['projects/orbit']
    trace = result['search_trace']['concept_query']
    assert 'pulse28' not in trace['anchors'] and trace['excluded_project_anchors'] == ['pulse28']
    assert trace['excluded_project_domains'] == ['projects/pulse']


def test_plain_keywords_keep_legacy_matching_and_technical_compounds_are_not_route_negation(tmp_path):
    root = _signed_hub(tmp_path)
    plain = search(root, 'flash guard')
    assert plain['results'] and plain['search_trace']['concept_query']['enabled'] is False
    assert plain['search_trace']['concept_query']['hard_constraints_enabled'] is False
    index = SearchIndex(root)
    index.ensure()
    plan = index.concept_query('ORBIT17 无线与非易失性发布记录怎样查询？')
    assert not plan.excluded_project_anchors and plan.project_anchors == ('orbit17',)


def test_constraint_trace_instance_schema_and_scan_parity(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub.schemas import validate_instance
    from tools.codex_assets.knowledge_hub.common import repository_root
    root = _signed_hub(tmp_path)
    query = 'project:ORBIT17 flash guard SPI 发布记录，排除PULSE28。'
    indexed = search(root, query)
    assert validate_instance(repository_root(), 'retrieval-result-v3', indexed)['status'] == 'pass'
    trace = indexed['search_trace']['concept_query']
    assert type(trace['hard_constraints_enabled']) is bool
    assert all(isinstance(value, str) for key in ('excluded_project_anchors', 'excluded_project_domains') for value in trace[key])
    monkeypatch.setattr(SearchIndex, 'ensure', lambda *a, **kw:(_ for _ in ()).throw(sqlite3.DatabaseError('fixture')))
    assert [row['item_id'] for row in search(root, query)['results']] == [row['item_id'] for row in indexed['results']]


def test_hard_boundary_name_and_negative_domain_budgets_are_bounded():
    from tools.codex_assets.knowledge_hub.query_boundaries import boundaries
    from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
    with pytest.raises(KnowledgeHubError, match='boundaries exceed budget'):
        boundaries(' '.join('project:NAME' + str(i) for i in range(65)), {})
    aliases = {'orbit17':{'projects/domain' + str(i) for i in range(65)}}
    with pytest.raises(KnowledgeHubError, match='boundaries exceed budget'):
        boundaries('flash guard 排除ORBIT17。', aliases)


@pytest.mark.parametrize('ending', ['', '.', '。', '?', '？'])
@pytest.mark.parametrize('forms', [
    ('排除项目ORBIT17', ['orbit17']), ('exclude project:ORBIT17', ['orbit17']),
    ('不要ORBIT17项目和PULSE28项目', ['orbit17', 'pulse28']),
    ('排除项目ORBIT17和项目PULSE28', ['orbit17', 'pulse28']),
    ('except project ORBIT17 and device PULSE28', ['orbit17', 'pulse28']),
    ('排除ORBIT17芯片项目以及PULSE28主板设备', ['orbit17', 'pulse28']),
])
def test_signed_subject_uses_identical_lexemes_for_heads_and_lists(tmp_path, ending, forms):
    root = _signed_hub(tmp_path)
    cue, names = forms
    result = search(root, 'flash guard ' + cue + ending)
    trace = result['search_trace']['concept_query']
    assert trace['excluded_project_anchors'] == names
    assert not set(names).intersection(trace['anchors'])
    assert trace['global_entity_constraints'] == []
    assert {row['domain'] for row in result['results']} == ({'projects/pulse'} if names == ['orbit17'] else set())


def test_cjk_actions_are_not_entity_class_descriptors():
    from tools.codex_assets.knowledge_hub.query_language import chinese_named_constraints
    assert 'guard' not in chinese_named_constraints('flash guard 排除项目ORBIT17', (), ())
    assert 'guard' not in chinese_named_constraints('flash guard 查询项目ORBIT17', (), ())
    assert chinese_named_constraints('CRAFT99芯片项目', (), ()) == ('craft99',)
