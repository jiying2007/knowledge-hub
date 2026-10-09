"""Query context may include shared norms; it never replaces explicit filters."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping, Optional

from .query_concepts import ConceptQuery
from .search_core import _domain_matches


def candidate_concepts(plan: ConceptQuery, item: Mapping[str, Any]) -> Optional[ConceptQuery]:
    if any(_domain_matches(str(item.get('domain', '')), domain) for domain in plan.excluded_project_domains):
        return None
    if not (plan.enabled or plan.enforce_constraints) or not plan.project_domains:
        return plan
    if any(_domain_matches(str(item.get('domain', '')), domain) for domain in plan.project_domains):
        return _projected_plan(plan, plan.project_terms) if plan.shared_policy_context and plan.project_terms else plan
    if (not plan.shared_policy_context or item.get('scope') != 'team-general'
            or item.get('kind') not in ('standard', 'architecture', 'runbook')
            or item.get('visibility') == 'personal-local' or item.get('searchable') is False):
        return None
    projected = _projected_plan(plan, plan.shared_terms) if plan.shared_terms else plan
    selected = [(term, weight) for term, weight in zip(projected.terms, projected.weights)
                if term not in plan.project_anchors]
    return replace(projected, terms=tuple(term for term, _ in selected), weights=tuple(weight for _, weight in selected),
                   anchors=tuple(term for term in projected.anchors if term not in plan.project_anchors),
                   project_anchors=(), project_domains=(), governance=True)


def _projected_plan(plan: ConceptQuery, terms) -> ConceptQuery:
    required = set(plan.global_anchors) | set(plan.lexical_constraints)
    selected = [(term, weight) for term, weight in zip(plan.terms, plan.weights) if term in terms or term in required]
    return replace(plan, terms=tuple(term for term, _ in selected), weights=tuple(weight for _, weight in selected),
                   anchors=tuple(term for term in plan.anchors if term in terms or term in required))
