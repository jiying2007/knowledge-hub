"""Bound legacy evaluation cases and distinguish ranking from abstention."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

from .common import KnowledgeHubError

MAX_EVALUATION_CASES = 5000
MAX_IDENTITIES_PER_CASE = 32


def validate_cases(payload: Any) -> List[Dict[str, Any]]:
    if not isinstance(payload, Mapping):
        raise KnowledgeHubError('retrieval dataset must be an object')
    cases = payload.get('cases')
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_EVALUATION_CASES:
        raise KnowledgeHubError('retrieval dataset must contain 1-5000 cases')
    seen = set()
    for case in cases:
        if not isinstance(case, Mapping):
            raise KnowledgeHubError('retrieval case must be an object')
        for key in ('id', 'query'):
            value = case.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > 4096:
                raise KnowledgeHubError('retrieval case {} must be a bounded non-empty string'.format(key))
        if case['id'] in seen:
            raise KnowledgeHubError('retrieval dataset requires unique case IDs')
        seen.add(case['id'])
        for key in ('expected_ids', 'expected_paths', 'forbidden_ids', 'forbidden_paths'):
            values = case.get(key, [])
            if (not isinstance(values, list) or len(values) > MAX_IDENTITIES_PER_CASE
                    or any(not isinstance(value, str) or not value.strip() or len(value) > 4096 for value in values)
                    or len(set(values)) != len(values)):
                raise KnowledgeHubError('retrieval {} must contain at most 32 unique bounded identities'.format(key))
        for key in ('expected_zero_hit', 'authority_case'):
            if key in case and type(case[key]) is not bool:
                raise KnowledgeHubError('retrieval {} must be a boolean'.format(key))
        answerable = bool(case.get('expected_ids') or case.get('expected_paths'))
        if answerable == bool(case.get('expected_zero_hit', False)):
            raise KnowledgeHubError('retrieval case requires either expected identity or expected_zero_hit')
        for expected, forbidden in (('expected_ids', 'forbidden_ids'), ('expected_paths', 'forbidden_paths')):
            if set(case.get(expected, [])).intersection(case.get(forbidden, [])):
                raise KnowledgeHubError('retrieval expected and forbidden identities overlap')
        for key in ('relevance_ids', 'relevance_paths'):
            values = case.get(key, {})
            if (not isinstance(values, Mapping) or len(values) > MAX_IDENTITIES_PER_CASE
                    or any(not isinstance(identity, str) or not identity.strip() or len(identity) > 4096
                           or type(value) is not int or not 0 <= value <= 3 for identity, value in values.items())):
                raise KnowledgeHubError('retrieval relevance must map bounded identities to integer grades 0-3')
    return [dict(case) for case in cases]


def ranking_summary(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    ranked = [row for row in rows if not row.get('expected_zero_hit', False)]
    zero = [row for row in rows if row.get('expected_zero_hit', False)]
    return {
        'ranking_case_count': len(ranked),
        'ranking_metrics_applicable': bool(ranked),
        'mrr': sum(row['reciprocal_rank'] for row in ranked) / len(ranked) if ranked else 0.0,
        'ndcg_at_10': sum(row['ndcg_at_10'] for row in ranked) / len(ranked) if ranked else 0.0,
        'zero_hit_case_count': len(zero),
        'zero_hit_success_count': sum(bool(row['hit']) for row in zero),
        'zero_hit_accuracy': sum(bool(row['hit']) for row in zero) / len(zero) if zero else None,
        'zero_hit_failure_count': sum(not row['hit'] for row in zero),
    }
