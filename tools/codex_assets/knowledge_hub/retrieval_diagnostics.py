"""Development-only query diagnosis; never treats reused examples as unseen tests."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from .common import KnowledgeHubError, registry_items
from .search import (SearchIndex, SearchFilters, search, query_terms, _score,
                     _filter_reason, _item_is_default_searchable, _term_variants,
                     _matched_query_terms,
                     SEARCH_AUTHORITY_CANDIDATE_LIMIT, SEARCH_MAX_QUERY_CHARS)
from .natural_query import normalize_question
from .query_scope import candidate_concepts


def _digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _identity(value):
    text = str(value)
    return text if len(text) <= 160 else 'sha256:' + _digest(text)


def _validate_development(dataset, measured):
    if dataset.get('dataset_role') == 'frozen-validation':
        raise KnowledgeHubError('development diagnosis requires a separate development dataset')
    cases, observed = dataset.get('cases', []), measured.get('cases', [])
    if not isinstance(cases, list) or not isinstance(observed, list) or max(len(cases), len(observed)) > 200:
        raise KnowledgeHubError('development diagnosis exceeds 200-case budget')
    definitions = {case['id']:case for case in cases}
    if len(definitions) != len(cases) or len({row['id'] for row in observed}) != len(observed):
        raise KnowledgeHubError('development diagnosis requires unique case IDs')
    for row in observed:
        if row['id'] not in definitions:
            raise KnowledgeHubError('development measurement has an unknown case ID')
        query = row.get('query', '')
        if not isinstance(query, str) or not query.strip() or len(query) > SEARCH_MAX_QUERY_CHARS:
            raise KnowledgeHubError('development query exceeds budget or is empty')
        definition = definitions[row['id']]
        if definition.get('query', query) != query:
            raise KnowledgeHubError('development measurement query differs from definition')
        for key in ('expected_ids', 'expected_paths'):
            if len(definition.get(key, [])) > 32:
                raise KnowledgeHubError('development expected identity exceeds 32-item budget')
    return definitions


def _expected_evidence(definition, query, index, items, result):
    ids, paths = set(definition.get('expected_ids', [])), set(definition.get('expected_paths', []))
    plan = index.concept_query(query)
    terms = list(plan.terms)
    lexical = index.candidates(query, candidate_limit=index.CANDIDATE_LIMIT, concept_plan=plan)
    authority = index.authority_candidates(query, SEARCH_AUTHORITY_CANDIDATE_LIMIT, concept_plan=plan)
    lanes: Dict[str, Dict[str, Any]] = {}
    for name, candidates in (('lexical', lexical), ('authority', authority)):
        for candidate in candidates:
            item = json.loads(candidate['item_json'])
            key = str(item.get('id', ''))
            if key in ids or item.get('path') in paths:
                lanes.setdefault(key, {'row':candidate, 'lanes':[]})['lanes'].append(name)
    ranks = {row.get('item_id'):rank for rank, row in enumerate(result['results'], 1)}
    evidence = []
    for item in items:
        key = str(item.get('id', ''))
        if key not in ids and item.get('path') not in paths:
            continue
        candidate, scored, filtered, matched_count = lanes.get(key), None, '', 0
        if candidate:
            row = candidate['row']
            effective = candidate_concepts(plan, item)
            effective_terms = list(effective.terms) if effective else []
            matched_count = len(_matched_query_terms(effective_terms, str(row['body']), item, exact=plan.enabled))
            filtered = _filter_reason(item, json.loads(row['physical_sources']), SearchFilters())
            if not filtered:
                scored = _score(str(row['path']), str(row['suffix']), str(row['body']), item,
                                str(row['indexed_title']), terms, query, concept_plan=plan)
        evidence.append({'item_id':_identity(key), 'path_sha256':_digest(str(item.get('path', ''))),
                         'default_corpus_eligible':_item_is_default_searchable(item),
                         'candidate_lanes':candidate['lanes'] if candidate else [],
                         'excluded_by':filtered, 'scoring_passed':scored is not None,
                         'matched_term_count':matched_count, 'query_term_count':len(terms),
                         'effective_query_term_count':len(effective_terms) if candidate else 0,
                         'score':scored[0] if scored else None,
                         'score_reasons':list(scored[1])[:16] if scored else [],
                         'returned_rank':ranks.get(key, 0)})
    return evidence[:64]


def _reason(case, evidence, available):
    if case['forbidden_hits']:
        return 'forbidden-authority-hit'
    if case['hit']:
        return 'expected-zero-result-confirmed' if case.get('expected_zero_hit') else 'expected-answer-retrieved'
    if case.get('expected_zero_hit'):
        return 'unexpected-nonzero-result'
    if case['rank']:
        return 'expected-answer-below-top-k'
    if not available:
        return 'stage-evidence-unavailable'
    if not evidence:
        return 'expected-identity-not-registered'
    if not any(row['default_corpus_eligible'] for row in evidence):
        return 'expected-excluded-from-default-corpus'
    if not any(row['candidate_lanes'] for row in evidence):
        return 'expected-not-in-bounded-candidate-pool'
    if all(row['excluded_by'] for row in evidence if row['candidate_lanes']):
        return 'expected-excluded-by-authority-filters'
    if not any(row['scoring_passed'] for row in evidence):
        return 'expected-rejected-by-scoring'
    return 'expected-scored-outside-return-window'


def _diagnostic_row(definition, case, index, items, root, top_k):
    query, normalized = case['query'], normalize_question(case['query'])
    result = search(root, query, limit=max(top_k, 10), search_index=index) if index else {}
    evidence = _expected_evidence(definition, query, index, items, result) if index else []
    trace = result.get('search_trace', {})
    terms = result.get('query_terms', query_terms(query))
    return {'case_id':_identity(case['id']), 'query_sha256':_digest(query),
            'query_class':_identity(definition.get('query_class', 'unclassified')),
            'reason':_reason(case, evidence, index is not None),
            'normalization_changed':normalized != query, 'normalized_query_sha256':_digest(normalized),
            'alias':{'method':('corpus-concepts-plus-existing-term-variants'
                              if trace.get('concept_query', {}).get('enabled') else 'existing-search-term-variants'),
                     'policy_changed':False,
                     'term_count':len(terms), 'term_sha256':[_digest(term) for term in terms[:64]],
                     'variant_sha256':[[_digest(value) for value in _term_variants(term)[:8]]
                                       for term in terms[:64]],
                     'expanded_term_count':sum(len(_term_variants(term)) > 1 for term in terms)},
            'candidate_pool':trace.get('candidate_pool', {}),
            'authority_filter_counts':result.get('filter_diagnostics', {}).get('by_reason', {}),
            'expected_stage_evidence':evidence, 'stage_evidence_available':index is not None,
            'top_k':top_k, 'rank':case['rank'],
            'returned_ids':[_identity(row.get('item_id', '')) for row in case['ranked'][:10]],
            'returned_ranking':[{'item_id':_identity(row.get('item_id', '')), 'rank':rank,
                                 'score':row.get('score', 0)} for rank, row in enumerate(case['ranked'][:10], 1)],
            'next_action':'按首次失败阶段核验开发证据；冻结后由独立评估者采集新验证集' if not case['hit'] else '保留为开发回归案例'}


def development_diagnostics(dataset, measured, *, root=None):
    definitions = _validate_development(dataset, measured)
    top_k = measured.get('top_k', 3)
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 100:
        raise KnowledgeHubError('development top-k exceeds budget')
    index = SearchIndex(root) if root is not None else None
    items = registry_items(root) if root is not None else []
    if index:
        index.ensure()
    rows = [_diagnostic_row(definitions[case['id']], case, index, items, root, top_k)
            for case in measured['cases']]
    return {'schema_version':2, 'dataset_role':'development-regression', 'used_for_tuning':True,
            'unseen_claim_allowed':False, 'production_qualification':False, 'report_only':True, 'rows':rows,
            'default_policy_changed':False,
            'fresh_validation_protocol':[
                '冻结代码、检索策略和开发案例身份后，由未参与调优的评估者采集新问题',
                '脱敏并明确expected、forbidden和问题类别；审查后冻结案例hash',
                '新验证集不得进入开发诊断；首次评估单列失败项和来源证据',
                '真实生产资格需真实交互样本和反馈，禁止用合成案例补足数量']}
