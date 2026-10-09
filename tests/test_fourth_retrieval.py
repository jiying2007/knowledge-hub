"""General synthetic ranking and evaluator integrity regressions, never gold edits."""

import hashlib
import json

import pytest

from tools.codex_assets.knowledge_hub import retrieval
from tools.codex_assets.knowledge_hub import retrieval_holdout as holdout
from tools.codex_assets.knowledge_hub import retrieval_diagnostics as diagnosis
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.retrieval_metrics import validate_cases, ranking_summary
from tools.codex_assets.knowledge_hub.search import _score, query_terms


def _case(key):
    return dict(id=key, query=key, expected_ids=['answer'], forbidden_ids=['forbidden'])


def _measure(monkeypatch, tmp_path, cases, response):
    class Index:
        def __init__(self, _root):
            pass
        def ensure(self):
            return dict(state='warm', document_files=2)
    monkeypatch.setattr(retrieval, 'load_json', lambda *args:dict(cases=cases))
    monkeypatch.setattr(retrieval, 'registry_items', lambda root:[
        dict(id='answer', path='answer.md'), dict(id='forbidden', path='forbidden.md')])
    monkeypatch.setattr(retrieval, 'SearchIndex', Index)
    monkeypatch.setattr(retrieval, 'search', response)
    return retrieval.run_retrieval_benchmark(tmp_path, cases_path=tmp_path/'cases.json', enable_extended_probes=False)


def _result(forbidden=False):
    rows = [dict(item_id='answer', path='answer.md', score=2)]
    if forbidden:
        rows.append(dict(item_id='forbidden', path='forbidden.md', score=1))
    return dict(results=rows, latency_ms=1)


def test_single_forbidden_hit_cannot_be_diluted_by_aggregate_threshold(monkeypatch, tmp_path):
    payload = _measure(monkeypatch, tmp_path, [_case(str(i)) for i in range(20)],
                       lambda root, query, **kw:_result(query == '0'))
    assert payload['hit_rate'] == .95 and payload['mrr'] == 1
    assert payload['status'] == 'fail' and payload['integrity']['status'] == 'fail'
    assert payload['integrity']['forbidden_hit_count'] == 1


def test_zero_hit_failure_is_separate_from_answerable_ranking(monkeypatch, tmp_path):
    cases = [dict(id='zero', query='zero', expected_zero_hit=True)] + [_case(str(i)) for i in range(19)]
    payload = _measure(monkeypatch, tmp_path, cases, lambda *args, **kw:_result())
    assert payload['hit_rate'] == .95 and payload['ndcg_at_10'] == 1
    assert payload['status'] == 'fail' and payload['cases'][0]['ndcg_at_10'] is None
    assert payload['ranking_case_count'] == 19 and payload['zero_hit_accuracy'] == 0
    assert payload['integrity']['zero_hit_failure_count'] == 1
    zero = ranking_summary([payload['cases'][0]])
    assert not zero['ranking_metrics_applicable'] and zero['ranking_case_count'] == 0
    assert zero['ndcg_at_10'] == 0 and zero['zero_hit_accuracy'] == 0


def test_successful_negative_only_dataset_does_not_claim_ranking_quality(monkeypatch, tmp_path):
    payload = _measure(monkeypatch, tmp_path, [dict(id='zero', query='zero', expected_zero_hit=True)],
                       lambda *args, **kw:dict(results=[], latency_ms=1))
    assert payload['status'] == 'pass' and payload['zero_hit_accuracy'] == 1
    assert not payload['ranking_metrics_applicable'] and payload['mrr'] == payload['ndcg_at_10'] == 0
    assert payload['cases'][0]['ndcg_at_10'] is None
    summary = retrieval.retrieval_benchmark_summary(payload)
    assert summary['ranking_case_count'] == 0 and summary['zero_hit_accuracy'] == 1


def test_ndcg_deduplicates_id_and_path_even_for_unreturned_document():
    ranked = [dict(item_id='answer', path='answer.md')]
    assert retrieval._ndcg_at_10(ranked, {'answer':3}, {'answer.md':3}) == 1
    mapping = dict(answer='answer.md', other='other.md', alias='answer.md')
    double = retrieval._ndcg_at_10(ranked, {'answer':3, 'other':2}, {'answer.md':3, 'other.md':2}, mapping)
    single = retrieval._ndcg_at_10(ranked, {'answer':3, 'other':2}, {}, mapping)
    assert double == single and 0 < single < 1
    assert retrieval._ndcg_at_10(ranked, {'alias':3}, {}, mapping) == 1


def test_registry_identity_requires_id_and_path_from_the_same_item(monkeypatch, tmp_path):
    payload = _measure(monkeypatch, tmp_path, [_case('pair')], lambda *args, **kw:dict(
        results=[dict(item_id='answer', path='forbidden.md', score=2)], latency_ms=1))
    assert payload['status'] == 'fail' and payload['integrity']['unregistered_result_count'] == 1


def test_successful_zero_diagnostic_does_not_claim_an_answer_was_retrieved():
    case = dict(hit=True, expected_zero_hit=True, forbidden_hits=[], rank=0)
    assert diagnosis._reason(case, [], True) == 'expected-zero-result-confirmed'


def test_holdout_groups_do_not_mix_zero_hit_cases_into_ranking_means(monkeypatch, tmp_path):
    cases = [dict(_case('answer'), query_class='mixed'),
             dict(id='zero', query='zero', query_class='mixed', expected_zero_hit=True)]
    path = tmp_path/'cases.json'
    path.write_text(json.dumps(dict(cases=cases)))
    monkeypatch.setattr(holdout, 'working_tree_signature', lambda root:'stable')
    measured = dict(status='pass', cases=[
        dict(id='answer', hit=True, reciprocal_rank=1, ndcg_at_10=1, forbidden_hits=[]),
        dict(id='zero', hit=True, expected_zero_hit=True, reciprocal_rank=0, ndcg_at_10=None, forbidden_hits=[])],
        hit_rate=1, mrr=1, ndcg_at_10=1, authority_recall_at_3=1, integrity=dict(status='pass'))
    monkeypatch.setattr(holdout, 'run_retrieval_benchmark_serialized', lambda *args, **kw:measured)
    result = holdout.evaluate_holdout(tmp_path, path)
    group = result['by_query_class']['mixed']
    assert group['mrr'] == group['ndcg_at_10'] == group['zero_hit_accuracy'] == 1
    assert group['ranking_case_count'] == group['zero_hit_case_count'] == 1


@pytest.mark.parametrize('mutation', ['duplicate', 'boolean', 'empty', 'overlap', 'noexpectation',
                                       'ambiguouszero', 'wronglist', 'relevance', 'querybudget'])
def test_dataset_contract_is_checked_before_search(monkeypatch, tmp_path, mutation):
    cases = [_case('case')]
    if mutation == 'duplicate':
        cases *= 2
    elif mutation == 'boolean':
        cases[0]['expected_zero_hit'] = 'false'
    elif mutation == 'empty':
        cases = []
    elif mutation == 'overlap':
        cases[0]['forbidden_ids'] = ['answer']
    elif mutation == 'noexpectation':
        cases[0]['expected_ids'] = []
    elif mutation == 'ambiguouszero':
        cases[0]['expected_zero_hit'] = True
    elif mutation == 'wronglist':
        cases[0]['expected_ids'] = 'answer'
    elif mutation == 'relevance':
        cases[0]['relevance_ids'] = {'answer':True}
    else:
        cases[0]['query'] = 'q' * 4097
    def forbidden(*args, **kwargs):
        pytest.fail('invalid dataset must fail before search')
    with pytest.raises(KnowledgeHubError):
        _measure(monkeypatch, tmp_path, cases, forbidden)


def test_holdout_rejects_duplicate_frozen_cases_before_benchmark(monkeypatch, tmp_path):
    cases = [_case('one')] * 2
    digest = hashlib.sha256(json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    path = tmp_path/'cases.json'
    path.write_text(json.dumps(dict(cases=cases, dataset_role='frozen-validation', used_for_tuning=False,
                                    frozen_cases_sha256=digest)))
    monkeypatch.setattr(holdout, 'working_tree_signature', lambda root:'stable')
    monkeypatch.setattr(holdout, 'run_retrieval_benchmark_serialized', lambda *args, **kw:pytest.fail('must reject first'))
    with pytest.raises(KnowledgeHubError, match='unique'):
        holdout.evaluate_holdout(tmp_path, path)


@pytest.mark.parametrize('query,partial_title,answer_title', [
    ('固件升级失败', '固件升级指南', '故障排查'),
    ('传感器校准错误', '传感器校准指南', '设备诊断'),
    ('calibration reset', 'calibration reset guide', 'Hardware procedures'),
])
def test_complete_summary_has_a_visible_general_ranking_signal(query, partial_title, answer_title):
    base = dict(kind='architecture', status='active')
    answer = dict(base, id='answer', path='a.md', title=answer_title, summary_zh=query)
    noisy = dict(base, id='noise', path='b.md', title=partial_title)
    full = _score('a.md', '.md', '说明', answer, '', query_terms(query), query)
    partial = _score('b.md', '.md', '说明', noisy, '', query_terms(query), query)
    assert full is not None and partial is not None and 'exact-summary' in full[1]
    if any('\u4e00' <= char <= '\u9fff' for char in query):
        assert full[0] > partial[0]
    # Exact titles remain stronger evidence than the same phrase in a summary.
    exact_title = dict(base, id='title', path='c.md', title=query)
    exact = _score('c.md', '.md', '说明', exact_title, '', query_terms(query), query)
    assert exact is not None and exact[0] > full[0]


def test_generic_and_body_only_queries_do_not_gain_summary_bonus():
    for query, summary, body in [('validation', 'validation', ''), ('alpha', '', 'alpha')]:
        item = dict(id='item', path='a.md', title='reference', kind='architecture', status='active', summary_zh=summary)
        score = _score('a.md', '.md', body, item, '', query_terms(query), query)
        assert score is not None and 'exact-summary' not in score[1]


def test_case_count_has_an_explicit_budget():
    with pytest.raises(KnowledgeHubError, match='5000'):
        validate_cases(dict(cases=[_case(str(i)) for i in range(5001)]))
