"""Scoring evidence gates extracted without changing arithmetic or order."""

import math
import re
from .query_concepts import FIELD_VALUES, exact_concept_match
from .search_core import CJK_PATTERN, GENERIC_QUERY_TERMS


def select_distinctive_terms(terms):
    return [
        term
        for term in terms
        if term not in GENERIC_QUERY_TERMS
        and (
            len(term) >= 3
            or len("".join(CJK_PATTERN.findall(term))) >= 2
        )
    ]


def concept_evidence_score(concept_plan, natural, terms, matches, full_document,
                           topic_document, metadata_fields, evidence_text, item):
    score, reasons = 0, []
    if concept_plan and (concept_plan.enabled or concept_plan.enforce_constraints):
        if any(not exact_concept_match(term, full_document, normalized=True)
               for term in concept_plan.anchors if term not in concept_plan.project_anchors):
            return None
        if (not concept_plan.project_domains and terms and terms[0] in concept_plan.anchors
                and re.search(r'\d', terms[0]) and not exact_concept_match(terms[0], metadata_fields, normalized=True)):
            return None
        if any(not exact_concept_match(term, full_document, normalized=True)
               for term in concept_plan.lexical_constraints):
            return None
        if concept_plan.subject and not exact_concept_match(concept_plan.subject, full_document, normalized=True):
            return None
    if natural and concept_plan:
        total_weight = sum(concept_plan.weights) or 1
        matched_weight = sum(weight for term, weight in zip(terms, concept_plan.weights)
                             if matches(term, topic_document if term in FIELD_VALUES else full_document))
        if matched_weight / total_weight < .5:
            return None
        score += int(240 * matched_weight / total_weight)
        reasons.append('concept-idf-document')
        metadata_weight = sum(weight for term, weight in zip(terms, concept_plan.weights)
                              if matches(term, evidence_text(term)))
        score += int(240 * metadata_weight / total_weight)
        reasons.append('concept-idf-metadata')
        if (concept_plan.governance and item.get('scope') == 'team-general'
                and item.get('status') == 'active' and item.get('kind') in ('architecture', 'standard', 'runbook')):
            score += 220
            reasons.append('active-general-policy')
    return score, reasons


def distinctive_evidence_score(distinctive_terms, matches, evidence_text, body_haystack,
                               normalized_query, topic_fields):
    score, reasons = 0, []
    matched_distinctive_anywhere = [
        term
        for term in distinctive_terms
        if matches(term, evidence_text(term)) or matches(term, body_haystack)
    ]
    matched_distinctive_metadata = [
        term for term in distinctive_terms if matches(term, evidence_text(term))
    ]
    exact_query_match = bool(
        normalized_query
        and (
            normalized_query in topic_fields
            or normalized_query in body_haystack
        )
    )
    if len(distinctive_terms) >= 2 and not exact_query_match:
        minimum_distinctive = (
            2
            if len(distinctive_terms) == 2
            else max(2, int(math.ceil(len(distinctive_terms) * 0.5)))
        )
        field_definition = all(term in FIELD_VALUES and matches(term, body_haystack) for term in distinctive_terms)
        if (
            len(matched_distinctive_anywhere) < minimum_distinctive
            or (not matched_distinctive_metadata and not field_definition)
        ):
            return None
    distinctive_hits = [term for term in distinctive_terms if matches(term, evidence_text(term))]
    if distinctive_hits:
        score += min(480, sum(min(180, 45 + (12 * len(term))) for term in distinctive_hits))
        reasons.append("distinctive-metadata:{}".format(len(distinctive_hits)))
    body_only_hits = [
        term
        for term in distinctive_terms
        if matches(term, body_haystack) and not matches(term, evidence_text(term))
    ]
    if body_only_hits:
        score -= min(120, len(body_only_hits) * 30)
        reasons.append("body-only-distinctive-penalty")
    return score, reasons
