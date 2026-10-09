"""Development stages are observable without changing retrieval authority."""

import hashlib
import json

import pytest

from tools.codex_assets.knowledge_hub import retrieval_diagnostics as diagnosis
from tools.codex_assets.knowledge_hub import retrieval_holdout as holdout
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError


def _hub(root):
    (root / 'registry').mkdir()
    rows = []
    for key, title, enabled in [('answer', 'uniqueanswer', True), ('noise', 'noise', True),
                                ('blocked', 'blockedword', False)]:
        path = key + '.md'
        (root / path).write_text('# ' + title + '\n\nPRIVATE RAW BODY sentinel\n')
        rows.append(dict(id=key, path=path, title=title, kind='architecture',
                         status='active', domain='root', searchable=enabled, tags=[title]))
    (root / 'registry/items.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
    (root / 'registry/sources.json').write_text('{"sources":[]}')
    (root / 'registry/retired-sources.jsonl').write_text('')


def _case(key, query, expected, rank=0, hit=False):
    definition = dict(id=key, query=query, expected_ids=[expected])
    measured = dict(definition, rank=rank, hit=hit, forbidden_hits=[], ranked=[])
    return definition, measured


def test_real_stages_distinguish_recall_authority_identity_and_ranking(tmp_path):
    _hub(tmp_path)
    pairs = [_case('missing', 'noise', 'absent'), _case('blocked', 'blockedword', 'blocked'),
             _case('recall', 'noise', 'answer'), _case('rank', 'uniqueanswer', 'answer', rank=2),
             _case('scoring', 'uniqueanswer absentword', 'answer')]
    report = diagnosis.development_diagnostics({'cases':[pair[0] for pair in pairs]},
               {'cases':[pair[1] for pair in pairs], 'top_k':1}, root=tmp_path)
    assert [row['reason'] for row in report['rows']] == [
        'expected-identity-not-registered', 'expected-excluded-from-default-corpus',
        'expected-not-in-bounded-candidate-pool', 'expected-answer-below-top-k',
        'expected-rejected-by-scoring']
    stage = report['rows'][3]['expected_stage_evidence'][0]
    assert stage['candidate_lanes'] and stage['scoring_passed'] and stage['returned_rank'] == 1
    serialized = json.dumps(report)
    assert 'PRIVATE RAW BODY' not in serialized and 'uniqueanswer' not in serialized
    assert report['rows'][3]['candidate_pool']['returned'] == 1
    rejected = report['rows'][4]['expected_stage_evidence'][0]
    assert rejected['matched_term_count'] == 1 and rejected['query_term_count'] == 2
    assert not report['production_qualification'] and not report['default_policy_changed']


def test_scoring_filter_and_outside_window_are_separate():
    case = dict(hit=False, rank=0, forbidden_hits=[])
    stage = dict(default_corpus_eligible=True, candidate_lanes=['lexical'],
                 excluded_by='', scoring_passed=False)
    assert diagnosis._reason(case, [stage], True) == 'expected-rejected-by-scoring'
    stage['excluded_by'] = 'status'
    assert diagnosis._reason(case, [stage], True) == 'expected-excluded-by-authority-filters'
    stage.update(excluded_by='', scoring_passed=True)
    assert diagnosis._reason(case, [stage], True) == 'expected-scored-outside-return-window'
    assert diagnosis._reason(case, [], False) == 'stage-evidence-unavailable'
    case['expected_zero_hit'] = True
    assert diagnosis._reason(case, [], True) == 'unexpected-nonzero-result'


@pytest.mark.parametrize('mutation,match', [
    ('query', 'query differs'), ('unknown', 'unknown case'), ('duplicate', 'unique'),
    ('budget', '200-case'), ('expected', '32-item'), ('longquery', 'query exceeds')])
def test_input_budget_and_measurement_identity(mutation, match):
    definition, measured = _case('case', 'answer', 'answer')
    dataset, payload = {'cases':[definition]}, {'cases':[measured]}
    if mutation == 'query':
        measured['query'] = 'different'
    elif mutation == 'unknown':
        measured['id'] = 'unknown'
    elif mutation == 'duplicate':
        payload['cases'] *= 2
    elif mutation == 'budget':
        payload['cases'] *= 201
    elif mutation == 'expected':
        definition['expected_ids'] = ['id'] * 33
    else:
        measured['query'] = 'q' * (diagnosis.SEARCH_MAX_QUERY_CHARS + 1)
    with pytest.raises(KnowledgeHubError, match=match):
        diagnosis.development_diagnostics(dataset, payload)


def test_frozen_diagnosis_rejected_before_retrieval_or_shadow(tmp_path, monkeypatch):
    cases = [dict(id='frozen', query='untuned', expected_ids=['answer'])]
    digest = hashlib.sha256(json.dumps(cases, ensure_ascii=False, sort_keys=True,
                                      separators=(',', ':')).encode()).hexdigest()
    path = tmp_path / 'frozen.json'
    path.write_text(json.dumps(dict(dataset_role='frozen-validation', used_for_tuning=False,
                                    frozen_cases_sha256=digest, cases=cases)))
    before = path.read_bytes()
    monkeypatch.setattr(holdout, 'working_tree_signature', lambda root:'stable')
    def forbidden(*args, **kwargs):
        pytest.fail('frozen diagnosis must not start evaluator')
    monkeypatch.setattr(holdout, 'run_retrieval_benchmark_serialized', forbidden)
    with pytest.raises(KnowledgeHubError, match='frozen validation'):
        holdout.evaluate_holdout(tmp_path, path, diagnose=True)
    assert path.read_bytes() == before


def test_bounded_output_and_summary_preserves_top_k():
    definition, measured = _case('case', 'answer', 'answer', hit=True, rank=1)
    measured['ranked'] = [dict(item_id='x' * 1000, score=1)] * 100
    report = diagnosis.development_diagnostics({'cases':[definition]}, {'cases':[measured]})
    assert len(report['rows'][0]['returned_ids']) == 10
    assert len(report['rows'][0]['returned_ids'][0]) < 100
    from tools.codex_assets.knowledge_hub.retrieval import retrieval_benchmark_summary
    assert retrieval_benchmark_summary({'top_k':1, 'thresholds':{'minimum_hit_rate':0.5}})['top_k'] == 1
