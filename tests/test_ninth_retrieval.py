"""Question admission and authority ordering without production answer IDs."""

import pytest

from tests.test_fifth_retrieval import _hub, _item
from tools.codex_assets.knowledge_hub.search import search


def test_location_question_keeps_architecture_above_unrelated_standards(tmp_path):
    architecture = _item('root', 'Lattice 控制面架构', 'Lattice registry owner 和统一控制面入口。',
                         status='active', kind='architecture')
    standard = _item('standard', 'Lattice 提交规范', 'Lattice owner 提交采用统一字段。',
                     status='active', kind='standard')
    root = _hub(tmp_path, [architecture, standard])
    result = search(root, 'Lattice 的 registry、owner 和统一控制面在哪里说明？')
    assert result['results'][0]['item_id'] == 'root'


def test_location_question_keeps_specific_guide_above_general_policy(tmp_path):
    guide = _item('guide', 'Atlas Properties owner 导航', 'Atlas Properties owner 导航的权威位置。',
                  status='reviewing', kind='runbook')
    policy = _item('policy', '统一 owner 控制面', 'owner 的权威位置由统一控制面登记。',
                   status='active', kind='standard')
    root = _hub(tmp_path, [guide, policy])
    assert search(root, 'Atlas Properties 的 owner 导航权威位置在哪里？')['results'][0]['item_id'] == 'guide'


def test_leading_read_action_is_not_a_required_unknown_subject(tmp_path):
    guide = _item('navigation', 'Atlas 链接导航', 'Atlas 知识的链接和关系支持导航。', kind='runbook')
    root = _hub(tmp_path, [guide])
    result = search(root, '如何在 Atlas 查看知识的链接和关系？')
    assert result['results'][0]['item_id'] == 'navigation'
    assert '查看' not in result['query_terms']


def test_read_action_does_not_erase_a_registered_alias(tmp_path):
    guide = _item('guide', '知识链接导航', '知识链接导航保存关系。', project='island', kind='runbook')
    root = _hub(tmp_path, [guide], routes=[dict(aliases=['查看岛项目'], domain_refs=['projects/island'])])
    assert search(root, '查看岛项目 知识链接怎样导航？')['results'][0]['item_id'] == 'guide'


def test_multilingual_unit_inside_modifier_phrase_keeps_qualifier(tmp_path):
    from tools.codex_assets.knowledge_hub.query_concepts import extract_concepts
    plan = extract_concepts('LYRA82 正式发布真实性怎样核验？',
                            {'正式发布': 1, '正式': 2, '发布': 3, '真实性': 1, '核验': 2}, 4)
    assert '正式' in plan.terms and '发布' in plan.terms
    assert '正式发布' not in plan.terms


def test_multilingual_compound_split_preserves_exact_registered_identity():
    from tools.codex_assets.knowledge_hub.query_concepts import concept_units
    assert concept_units('正式发布', {'正式发布': 0, '正式': 1}) == ('正式发布',)
    assert concept_units('反向链接', {'反向': 1}) == ('反向链接',)


@pytest.mark.parametrize('prefix', ['如何查看', '怎样查阅', '请问浏览'])
def test_read_action_after_question_scaffold_is_not_a_subject(tmp_path, prefix):
    guide = _item('guide', '知识链接导航', '知识的链接和关系支持导航。', kind='runbook')
    root = _hub(tmp_path, [guide])
    assert search(root, prefix + '知识的链接和关系？')['results'][0]['item_id'] == 'guide'


def test_browser_noun_is_preserved_in_questions_and_corpus():
    from tools.codex_assets.knowledge_hub.query_concepts import clean_segments
    assert clean_segments('浏览器缓存', question=True) == ['浏览器缓存']
    assert clean_segments('查看参数') == ['查看参数']


@pytest.mark.parametrize('prefix', ['如何查看 ', '怎样查阅 ', '请问浏览 '])
def test_separate_read_action_before_latin_topic_is_not_a_subject(tmp_path, prefix):
    guide = _item('guide', 'Atlas 链接导航', 'Atlas 链接和关系支持导航。', kind='runbook')
    root = _hub(tmp_path, [guide])
    result = search(root, prefix + 'Atlas 链接和关系？')
    assert result['results'][0]['item_id'] == 'guide'
    assert not {'查看', '查阅', '浏览'}.intersection(result['query_terms'])


def test_curated_synonym_is_not_split_into_an_unknown_subject(tmp_path):
    guide = _item('guide', 'Atlas Backlinks', 'Atlas Backlinks 支持知识权威边界说明。', kind='runbook')
    root = _hub(tmp_path, [guide])
    result = search(root, 'Atlas 的反向链接能决定知识权威性吗？')
    assert result['results'][0]['item_id'] == 'guide'
    assert '反向链接' in result['query_terms']
    assert '反向' not in result['query_terms']


@pytest.mark.parametrize('name', ['排障项目', '知识图谱项目', '反向链接设备'])
def test_curated_topic_prefix_does_not_erase_an_unknown_chinese_entity(tmp_path, name):
    guide = _item('guide', 'Atlas Backlinks Graph', 'Atlas Backlinks Graph 知识权威边界说明。', kind='runbook')
    root = _hub(tmp_path, [guide])
    assert search(root, name + ' 的 Atlas 知识权威边界如何说明？')['results'] == []


@pytest.mark.parametrize('text', ['owner', 'coowner', 'owner2', 'owner_gate', 'x-owner',
                                  '知识owner边界', 'owners and owner', '无匹配内容' * 1000])
def test_literal_prefilter_preserves_regex_boundaries(text):
    import re
    from tools.codex_assets.knowledge_hub.query_matching import ConceptMatcher
    from tools.codex_assets.knowledge_hub.search_core import _term_variants
    expected = any(re.search(r'(?<![a-z0-9])' + re.escape(word) + r'(?![a-z0-9])', text) is not None
                   for word in _term_variants('owner'))
    assert ConceptMatcher(('owner',))('owner', text) is expected
