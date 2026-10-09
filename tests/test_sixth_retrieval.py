"""Shared/project comparisons and query-local work reuse, using synthetic evidence."""

import sqlite3

import pytest

from tools.codex_assets.knowledge_hub.search import SearchIndex, SearchFilters, search
from tests.test_fifth_retrieval import _hub, _item


def _comparison_hub(root):
    shared = _item('shared', 'TRACE77 团队通用调试流程', '团队通用流程和项目特有命令应分开，TRACE77 排障使用共享诊断步骤。',
                   status='active', kind='runbook')
    project = _item('local', 'AURORA18 TRACE77 项目特有命令', '项目特有命令和路径属于本项目，团队通用流程另外维护。',
                    project='aurora', kind='runbook')
    wrong = _item('other', 'NOVA29 TRACE77 调试流程', shared['summary_zh'], project='nova', status='active', kind='runbook')
    private = _item('personal', shared['title'], shared['summary_zh'], status='active', kind='runbook', visibility='personal-local')
    routes = [dict(aliases=['AURORA18'], group_id='aurora', domain_refs=['projects/aurora'])]
    return _hub(root, [shared, project, wrong, private], routes=routes)


def test_comparison_finds_shared_policy_and_registered_project_context(tmp_path):
    root = _comparison_hub(tmp_path)
    result = search(root, 'AURORA18 TRACE77 项目特有命令与团队通用调试流程应怎样分开？')
    ids = [row['item_id'] for row in result['results']]
    assert 'shared' in ids and 'local' in ids
    assert 'other' not in ids and 'personal' not in ids


def test_project_specific_question_keeps_project_scope(tmp_path):
    root = _comparison_hub(tmp_path)
    result = search(root, 'AURORA18 TRACE77 项目特有命令怎样使用？')
    assert [row['item_id'] for row in result['results']] == ['local']


@pytest.mark.parametrize('filters', [SearchFilters(domains=['projects/aurora']), SearchFilters(owners=['absent']),
                                    SearchFilters(statuses=['reviewing'])])
def test_comparison_never_relaxes_explicit_filters(tmp_path, filters):
    root = _comparison_hub(tmp_path)
    result = search(root, 'AURORA18 TRACE77 项目特有命令与团队通用调试流程应怎样分开？', filters=filters)
    assert all(row['item_id'] != 'shared' for row in result['results'])


@pytest.mark.parametrize('name', ['Unknownproject', 'unknownproject', 'UNKNOWNPROJECT', 'UNKNOWN938'])
def test_shared_comparison_cannot_launder_unknown_entities(tmp_path, name):
    root = _comparison_hub(tmp_path)
    assert search(root, '请问 ' + name + ' TRACE77 项目命令与团队通用调试流程怎样分开？')['results'] == []


def test_comparison_sqlite_and_scan_parity(tmp_path, monkeypatch):
    root = _comparison_hub(tmp_path)
    query = 'AURORA18 TRACE77 项目特有命令与团队通用调试流程怎样分开？'
    indexed = search(root, query)
    monkeypatch.setattr(SearchIndex, 'ensure', lambda *a, **kw:(_ for _ in ()).throw(sqlite3.DatabaseError('fixture')))
    scanned = search(root, query)
    assert [row['item_id'] for row in indexed['results']] == [row['item_id'] for row in scanned['results']]


def test_candidate_lanes_preserve_separate_lane_union(tmp_path):
    root = _comparison_hub(tmp_path)
    index = SearchIndex(root)
    index.ensure()
    query = 'AURORA18 TRACE77 项目命令与团队通用流程比较'
    plan = index.concept_query(query)
    authority = index.authority_candidates(query, 2, plan)
    lexical = index.candidates(query, 2, plan)
    expected = list(dict.fromkeys(row['doc_key'] for row in authority + lexical))
    combined, count = index.candidate_lanes(query, 2, 2, plan)
    assert [row['doc_key'] for row in combined] == expected
    assert count == len(authority)


def test_search_uses_one_body_lane_load(tmp_path, monkeypatch):
    root = _comparison_hub(tmp_path)
    index = SearchIndex(root)
    monkeypatch.setattr(index, 'candidates', lambda *a, **kw:pytest.fail('duplicate lexical payload read'))
    monkeypatch.setattr(index, 'authority_candidates', lambda *a, **kw:pytest.fail('duplicate authority payload read'))
    assert search(root, 'AURORA18 TRACE77 团队通用与项目命令比较', search_index=index)['results']


@pytest.mark.parametrize('comparison', [
    'AURORA18 versus Unknownproject', 'AURORA18 vs unknownproject',
    'AURORA18 against UNKNOWNPROJECT', 'compare AURORA18 with Unknownproject',
    'compare AURORA18 to unknownproject', '比较 AURORA18 与 Unknownproject',
    'AURORA18 versus the project Unknownproject', 'compare Unknownproject with AURORA18',
    'between AURORA18 and unknownproject', 'AURORA18 against unknownproject',
])
def test_unknown_comparison_operand_cannot_enter_shared_lane(tmp_path, comparison):
    root = _comparison_hub(tmp_path)
    query = comparison + ' TRACE77 团队通用调试流程和项目特有命令应怎样分开？'
    assert search(root, query)['results'] == []


@pytest.mark.parametrize('comparison', ['AURORA18 versus TRACE77', 'compare AURORA18 with TRACE77',
                                      '比较 AURORA18 与 TRACE77'])
def test_known_comparison_operands_preserve_shared_policy(tmp_path, comparison):
    root = _comparison_hub(tmp_path)
    result = search(root, comparison + ' 团队通用调试流程和项目特有命令应怎样分开？')
    assert 'shared' in [row['item_id'] for row in result['results']]


def test_comparison_preserves_corpus_known_ordinary_english_topics():
    from tools.codex_assets.knowledge_hub.query_concepts import extract_concepts
    plan = extract_concepts('How should we compare configuration with deployment?',
                            {'configuration':3, 'deployment':4}, 5)
    assert plan.enabled and plan.anchors == ()


@pytest.mark.parametrize('operator', ['versus', 'vs', 'against', 'compare-with', 'between-and', '中文比较'])
@pytest.mark.parametrize('joiner', [' and ', ' or ', ', ', '，', ' 与 ', ' 和 '])
def test_comparison_lists_keep_unknown_operand_constraints(tmp_path, operator, joiner):
    root = _comparison_hub(tmp_path)
    prefixes = {'compare-with':'compare AURORA18 with TRACE77', 'between-and':'between AURORA18 and TRACE77',
                '中文比较':'比较 AURORA18 与 TRACE77'}
    prefix = prefixes.get(operator, 'AURORA18 ' + operator + ' TRACE77')
    query = prefix + joiner + 'Unknownproject 团队通用调试流程和项目特有命令应怎样分开？'
    assert search(root, query)['results'] == []


@pytest.mark.parametrize('joiner', [' and ', ' or ', ', ', '，', ' 与 ', ' 和 '])
def test_comparison_lists_keep_known_topics_and_stop_at_clause_boundary(joiner):
    from tools.codex_assets.knowledge_hub.query_concepts import extract_concepts
    vocabulary = {'configuration':3, 'deployment':4, 'diagnostics':2}
    query = 'How compare configuration with deployment' + joiner + 'diagnostics?'
    assert extract_concepts(query, vocabulary, 5).anchors == ()
    separate = 'How compare configuration with deployment; and caution?'
    assert 'caution' not in extract_concepts(separate, vocabulary, 5).anchors
